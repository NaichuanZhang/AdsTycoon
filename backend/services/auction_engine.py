"""Auction engine — orchestrates the bidding pipeline."""

import random

from sqlalchemy.orm import Session

from backend.agents.campaign import run_campaign_agent
from backend.agents.consumer import run_consumer_agent
from backend.database import SessionLocal
from backend.models import Auction, Bid, Campaign, Consumer, Website


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


def run_single_auction(db: Session, simulation_id: str) -> Auction:
    consumers = db.query(Consumer).filter_by(simulation_id=simulation_id).all()
    websites = db.query(Website).filter_by(simulation_id=simulation_id).all()
    campaigns = db.query(Campaign).filter_by(simulation_id=simulation_id).all()

    if not consumers or not websites or not campaigns:
        raise ValueError("Simulation must have consumers, websites, and campaigns")

    consumer = random.choice(consumers)
    website = random.choice(websites)

    auction = Auction(
        simulation_id=simulation_id,
        consumer_id=consumer.id,
        website_id=website.id,
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    consumer_text = _consumer_profile_text(consumer)
    website_text = _website_context_text(website)

    eligible_campaigns = [c for c in campaigns if c.remaining_budget > 0]

    for camp in eligible_campaigns:
        run_campaign_agent(
            campaign_id=camp.id,
            auction_id=auction.id,
            consumer_profile=consumer_text,
            website_context=website_text,
            session_factory=SessionLocal,
        )

    db.refresh(auction)

    if auction.bids:
        winning_bid = max(auction.bids, key=lambda b: b.bid_amount)
        auction.winning_campaign_id = winning_bid.campaign_id
        auction.winning_bid = winning_bid.bid_amount

        winner_campaign = db.query(Campaign).filter_by(id=winning_bid.campaign_id).first()
        if winner_campaign:
            winner_campaign.remaining_budget -= winning_bid.bid_amount
            db.commit()

            run_consumer_agent(
                auction_id=auction.id,
                consumer_profile=consumer_text,
                website_context=website_text,
                ad_description=winner_campaign.creative,
                session_factory=SessionLocal,
            )

    db.commit()
    db.refresh(auction)
    return auction


def run_auction_rounds(db: Session, simulation_id: str, rounds: int) -> list[Auction]:
    results = []
    for _ in range(rounds):
        auction = run_single_auction(db, simulation_id)
        results.append(auction)
    return results


def reset_simulation(db: Session, simulation_id: str) -> None:
    auctions = db.query(Auction).filter_by(simulation_id=simulation_id).all()
    for auction in auctions:
        db.query(Bid).filter_by(auction_id=auction.id).delete()
    db.query(Auction).filter_by(simulation_id=simulation_id).delete()

    campaigns = db.query(Campaign).filter_by(simulation_id=simulation_id).all()
    for camp in campaigns:
        camp.remaining_budget = camp.total_budget

    db.commit()
