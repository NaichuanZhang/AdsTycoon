"""SSE streaming endpoints — pipe agent events to the browser in real-time."""

import asyncio
import json
import logging
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from strands import Agent

from backend.agents import create_bedrock_model
from backend.agents.campaign import SYSTEM_PROMPT as CAMPAIGN_SYSTEM_PROMPT
from backend.agents.consumer import SYSTEM_PROMPT as CONSUMER_SYSTEM_PROMPT
from backend.agents.insights import SYSTEM_PROMPT as INSIGHTS_SYSTEM_PROMPT
from backend.agents.seeder import SYSTEM_PROMPT as SEEDER_SYSTEM_PROMPT
from backend.agents.seeder import build_seeder_prompt
from backend.database import SessionLocal
from backend.models import Auction, Campaign, Consumer, Simulation, Website
from backend.tools.campaign_tools import get_campaign, submit_bid
from backend.tools.campaign_tools import set_session_factory as set_campaign_factory
from backend.tools.consumer_tools import submit_feedback
from backend.tools.consumer_tools import set_session_factory as set_consumer_factory
from backend.tools.insights_tools import get_campaign_auctions, get_campaign_stats
from backend.tools.insights_tools import set_session_factory as set_insights_factory
from backend.tools.seeder_tools import create_campaigns, create_consumers, create_websites
from backend.tools.seeder_tools import set_session_factory as set_seeder_factory

logger = logging.getLogger("bid_exchange.stream")

router = APIRouter(prefix="/api/simulations/{sim_id}/stream", tags=["streaming"])


def _sse(event_type: str, data: dict) -> str:
    payload = json.dumps({"type": event_type, **data})
    return f"data: {payload}\n\n"


def _get_sim(sim_id: str, db: Session) -> Simulation:
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


async def _stream_agent(agent: Agent, prompt: str):
    """Iterate over agent.stream_async() and yield formatted SSE events."""
    stream = agent.stream_async(prompt)
    async for event in stream:
        if "data" in event:
            text = event["data"]
            if text:
                yield _sse("text", {"content": str(text)})
        elif "current_tool_use" in event:
            tool_info = event["current_tool_use"]
            tool_name = tool_info.get("name", "")
            if tool_name:
                yield _sse("tool_call", {
                    "tool": tool_name,
                    "input": tool_info.get("input", {}),
                })


async def _stream_agent_full(agent: Agent, prompt: str):
    """Stream agent events and also capture tool results."""
    stream = agent.stream_async(prompt)
    current_tool = None
    async for event in stream:
        if "data" in event:
            text = event["data"]
            if text:
                yield _sse("text", {"content": str(text)})
        elif "current_tool_use" in event:
            tool_info = event["current_tool_use"]
            tool_name = tool_info.get("name", "")
            if tool_name and tool_name != current_tool:
                current_tool = tool_name
                yield _sse("tool_call", {
                    "tool": tool_name,
                    "input": tool_info.get("input", {}),
                })


@router.get("/seed")
async def stream_seed(sim_id: str):
    """SSE endpoint: streams seeder agent progress."""
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=sim_id).first()
        if not sim:
            raise HTTPException(status_code=404, detail="Simulation not found")

        set_seeder_factory(SessionLocal)
        model = create_bedrock_model()
        agent = Agent(
            model=model,
            tools=[create_consumers, create_websites, create_campaigns],
            system_prompt=SEEDER_SYSTEM_PROMPT,
            callback_handler=None,
        )

        prompt = build_seeder_prompt(
            sim.id, sim.scenario, sim.num_consumers, sim.num_websites,
            sim.num_campaigns, sim.num_rounds,
        )

        async def generate():
            try:
                yield _sse("status", {"message": "Seeding simulation..."})
                async for chunk in _stream_agent_full(agent, prompt):
                    yield chunk
                sim.status = "seeded"
                db.commit()
                yield _sse("done", {"message": "Seeding complete"})
            except Exception as e:
                logger.exception("Seeding stream error")
                db.rollback()
                yield _sse("error", {"message": str(e)})
            finally:
                db.close()

        return StreamingResponse(generate(), media_type="text/event-stream")
    except HTTPException:
        db.close()
        raise
    except Exception:
        db.close()
        raise


def _consumer_profile_text(consumer: Consumer) -> str:
    return (
        f"Name: {consumer.name}\n"
        f"Age: {consumer.age}, Gender: {consumer.gender}\n"
        f"Income: {consumer.income_level}\n"
        f"Interests: {', '.join(consumer.interests)}\n"
        f"Intent: {consumer.intent}\n"
        f"Mood: {consumer.mood}\n"
        f"Openness to Ads: {consumer.openness_to_ads}/5\n"
        f"Location: {consumer.location}"
    )


def _website_context_text(website: Website) -> str:
    return (
        f"Website: {website.name}\n"
        f"Page: {website.page_context}\n"
        f"Ad Placement: {website.ad_placement}\n"
        f"Category: {website.category}"
    )


@router.get("/run")
async def stream_run(sim_id: str, rounds: int = Query(default=None, ge=1, le=50)):
    """SSE endpoint: streams the full auction pipeline round by round."""
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=sim_id).first()
        if not sim:
            raise HTTPException(status_code=404, detail="Simulation not found")

        consumers = db.query(Consumer).filter_by(simulation_id=sim_id).all()
        websites = db.query(Website).filter_by(simulation_id=sim_id).all()
        campaigns = db.query(Campaign).filter_by(simulation_id=sim_id).all()

        if not consumers or not websites or not campaigns:
            raise HTTPException(status_code=400, detail="Simulation must be seeded first")

        effective_rounds = rounds if rounds is not None else sim.num_rounds

        async def generate():
            try:
                sim.status = "running"
                db.commit()

                for round_num in range(1, effective_rounds + 1):
                    consumer = random.choice(consumers)
                    website = random.choice(websites)

                    auction = Auction(
                        simulation_id=sim_id,
                        consumer_id=consumer.id,
                        website_id=website.id,
                    )
                    db.add(auction)
                    db.commit()
                    db.refresh(auction)

                    yield _sse("auction_start", {
                        "round": round_num,
                        "total_rounds": effective_rounds,
                        "auction_id": auction.id,
                        "consumer": consumer.name,
                        "website": website.name,
                    })

                    consumer_text = _consumer_profile_text(consumer)
                    website_text = _website_context_text(website)

                    eligible = [c for c in campaigns if c.remaining_budget > 0]

                    for camp in eligible:
                        yield _sse("campaign_turn", {
                            "campaign": camp.campaign_name,
                            "campaign_id": camp.id,
                            "goal": camp.goal,
                            "remaining_budget": round(camp.remaining_budget, 2),
                        })

                        set_campaign_factory(SessionLocal)
                        model = create_bedrock_model()
                        camp_agent = Agent(
                            model=model,
                            tools=[get_campaign, submit_bid],
                            system_prompt=CAMPAIGN_SYSTEM_PROMPT,
                            callback_handler=None,
                        )

                        camp_prompt = (
                            f"Campaign ID: {camp.id}\n"
                            f"Auction ID: {auction.id}\n\n"
                            f"Consumer Profile:\n{consumer_text}\n\n"
                            f"Website Context:\n{website_text}\n\n"
                            f"Decide whether to bid and how much. Call the tools now."
                        )

                        async for chunk in _stream_agent_full(camp_agent, camp_prompt):
                            yield chunk

                    db.refresh(auction)

                    if auction.bids:
                        winning_bid = max(auction.bids, key=lambda b: b.bid_amount)
                        auction.winning_campaign_id = winning_bid.campaign_id
                        auction.winning_bid = winning_bid.bid_amount

                        winner_campaign = db.query(Campaign).filter_by(id=winning_bid.campaign_id).first()
                        if winner_campaign:
                            winner_campaign.remaining_budget -= winning_bid.bid_amount
                            db.commit()

                            yield _sse("auction_winner", {
                                "campaign": winner_campaign.campaign_name,
                                "bid": round(winning_bid.bid_amount, 2),
                                "reasoning": winning_bid.reasoning,
                            })

                            set_consumer_factory(SessionLocal)
                            consumer_model = create_bedrock_model()
                            consumer_agent = Agent(
                                model=consumer_model,
                                tools=[submit_feedback],
                                system_prompt=CONSUMER_SYSTEM_PROMPT,
                                callback_handler=None,
                            )

                            feedback_prompt = (
                                f"Auction ID: {auction.id}\n\n"
                                f"You are this consumer:\n{consumer_text}\n\n"
                                f"You are browsing:\n{website_text}\n\n"
                                f"You were shown this ad:\n{winner_campaign.product_description}\n\n"
                                f"React to this ad. Call submit_feedback now."
                            )

                            async for chunk in _stream_agent_full(consumer_agent, feedback_prompt):
                                yield chunk

                    db.commit()
                    db.refresh(auction)

                    yield _sse("auction_end", {
                        "round": round_num,
                        "auction_id": auction.id,
                        "winner": auction.winning_campaign.campaign_name if auction.winning_campaign else None,
                        "winning_bid": round(auction.winning_bid, 2) if auction.winning_bid else None,
                        "feedback": auction.consumer_feedback,
                    })

                sim.status = "completed"
                db.commit()
                yield _sse("done", {"message": f"Completed {effective_rounds} auction rounds"})

            except Exception as e:
                logger.exception("Auction stream error")
                db.rollback()
                yield _sse("error", {"message": str(e)})
            finally:
                db.close()

        return StreamingResponse(generate(), media_type="text/event-stream")
    except HTTPException:
        db.close()
        raise
    except Exception:
        db.close()
        raise


@router.get("/insights/{campaign_id}")
async def stream_insights(sim_id: str, campaign_id: str):
    """SSE endpoint: streams insights agent analysis."""
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter_by(id=campaign_id, simulation_id=sim_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        set_insights_factory(SessionLocal)
        model = create_bedrock_model()
        agent = Agent(
            model=model,
            tools=[get_campaign_auctions, get_campaign_stats],
            system_prompt=INSIGHTS_SYSTEM_PROMPT,
            callback_handler=None,
        )

        async def generate():
            try:
                yield _sse("status", {"message": f"Analyzing {campaign.campaign_name}..."})
                async for chunk in _stream_agent_full(agent, f"Analyze campaign {campaign_id} and return JSON insights."):
                    yield chunk
                yield _sse("done", {"message": "Analysis complete"})
            except Exception as e:
                logger.exception("Insights stream error")
                db.rollback()
                yield _sse("error", {"message": str(e)})
            finally:
                db.close()

        return StreamingResponse(generate(), media_type="text/event-stream")
    except HTTPException:
        db.close()
        raise
    except Exception:
        db.close()
        raise
