"""Strands tools for the Seeding Agent.

Each tool receives data from the LLM and inserts rows into the DB.
A session factory is set via set_session_factory() before each agent invocation.
Each tool creates its own session to avoid corruption from parallel tool calls.
"""

import logging
import uuid

from strands import tool

from backend.models import Campaign, Consumer, Website

logger = logging.getLogger("bid_exchange.seeder_tools")

_session_factory = None


def set_session_factory(factory):
    global _session_factory
    _session_factory = factory


def _new_db():
    if _session_factory is None:
        raise RuntimeError("Session factory not set. Call set_session_factory() first.")
    return _session_factory()


@tool
def create_consumers(simulation_id: str, consumers: list[dict]) -> str:
    """Create consumer profiles for a simulation.

    Args:
        simulation_id: The simulation UUID to attach consumers to.
        consumers: List of consumer dicts, each with keys:
            name (str), age (int), gender (str), income_level (str: low/medium/high),
            interests (list[str]), intent (str: browsing/researching/ready to buy),
            mood (str: relaxed/focused/impatient/curious/skeptical),
            openness_to_ads (int: 1-5), location (str).

    Returns:
        A confirmation message with the count of consumers created.
    """
    db = _new_db()
    try:
        existing = db.query(Consumer).filter_by(simulation_id=simulation_id).count()
        if existing > 0:
            return f"Simulation {simulation_id} already has {existing} consumers, skipping."

        created = 0
        for c in consumers:
            consumer = Consumer(
                id=str(uuid.uuid4()),
                simulation_id=simulation_id,
                name=c["name"],
                age=c["age"],
                gender=c["gender"],
                income_level=c["income_level"],
                interests=c["interests"],
                intent=c["intent"],
                mood=c.get("mood", "neutral"),
                openness_to_ads=c.get("openness_to_ads", 3),
                location=c["location"],
            )
            db.add(consumer)
            created += 1
        db.commit()
        return f"Created {created} consumers for simulation {simulation_id}"
    except Exception as e:
        logger.exception("Failed to create consumers")
        db.rollback()
        return f"Error creating consumers: {e}"
    finally:
        db.close()


@tool
def create_websites(simulation_id: str, websites: list[dict]) -> str:
    """Create website contexts for a simulation.

    Args:
        simulation_id: The simulation UUID to attach websites to.
        websites: List of website dicts, each with keys:
            name (str), page_context (str), ad_placement (str: banner/sidebar/interstitial),
            category (str).

    Returns:
        A confirmation message with the count of websites created.
    """
    db = _new_db()
    try:
        existing = db.query(Website).filter_by(simulation_id=simulation_id).count()
        if existing > 0:
            return f"Simulation {simulation_id} already has {existing} websites, skipping."

        created = 0
        for w in websites:
            website = Website(
                id=str(uuid.uuid4()),
                simulation_id=simulation_id,
                name=w["name"],
                page_context=w["page_context"],
                ad_placement=w["ad_placement"],
                category=w["category"],
            )
            db.add(website)
            created += 1
        db.commit()
        return f"Created {created} websites for simulation {simulation_id}"
    except Exception as e:
        logger.exception("Failed to create websites")
        db.rollback()
        return f"Error creating websites: {e}"
    finally:
        db.close()


@tool
def create_campaigns(simulation_id: str, campaigns: list[dict]) -> str:
    """Create advertising campaigns for a simulation.

    Args:
        simulation_id: The simulation UUID to attach campaigns to.
        campaigns: List of campaign dicts, each with keys:
            campaign_name (str), product_description (str),
            creative (str: marketing creative concept),
            goal (str: reach/quality), total_budget (float).

    Returns:
        A confirmation message with the count of campaigns created.
    """
    db = _new_db()
    try:
        existing = db.query(Campaign).filter_by(simulation_id=simulation_id).count()
        if existing > 0:
            return f"Simulation {simulation_id} already has {existing} campaigns, skipping."

        created = 0
        for camp in campaigns:
            budget = camp["total_budget"]
            campaign = Campaign(
                id=str(uuid.uuid4()),
                simulation_id=simulation_id,
                campaign_name=camp["campaign_name"],
                product_description=camp["product_description"],
                creative=camp["creative"],
                goal=camp["goal"],
                total_budget=budget,
                remaining_budget=budget,
            )
            db.add(campaign)
            created += 1
        db.commit()
        return f"Created {created} campaigns for simulation {simulation_id}"
    except Exception as e:
        logger.exception("Failed to create campaigns")
        db.rollback()
        return f"Error creating campaigns: {e}"
    finally:
        db.close()
