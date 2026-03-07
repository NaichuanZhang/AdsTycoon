"""Strands tools for the Seeding Agent.

Each tool receives data from the LLM and inserts rows into the DB.
The DB session is set via set_db_session() before each agent invocation.
"""

import logging
import uuid

from strands import tool

from backend.models import Campaign, Consumer, Website

logger = logging.getLogger("bid_exchange.seeder_tools")

_db_session = None


def set_db_session(session):
    global _db_session
    _db_session = session


def _get_db():
    if _db_session is None:
        raise RuntimeError("DB session not set. Call set_db_session() first.")
    return _db_session


@tool
def create_consumers(simulation_id: str, consumers: list[dict]) -> str:
    """Create consumer profiles for a simulation.

    Args:
        simulation_id: The simulation UUID to attach consumers to.
        consumers: List of consumer dicts, each with keys:
            name (str), age (int), gender (str), income_level (str: low/medium/high),
            interests (list[str]), intent (str: browsing/researching/ready to buy),
            location (str).

    Returns:
        A confirmation message with the count of consumers created.
    """
    db = _get_db()
    existing = db.query(Consumer).filter_by(simulation_id=simulation_id).count()
    if existing > 0:
        return f"Simulation {simulation_id} already has {existing} consumers, skipping."

    try:
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
    db = _get_db()
    existing = db.query(Website).filter_by(simulation_id=simulation_id).count()
    if existing > 0:
        return f"Simulation {simulation_id} already has {existing} websites, skipping."

    try:
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


@tool
def create_campaigns(simulation_id: str, campaigns: list[dict]) -> str:
    """Create advertising campaigns for a simulation.

    Args:
        simulation_id: The simulation UUID to attach campaigns to.
        campaigns: List of campaign dicts, each with keys:
            campaign_name (str), product_description (str),
            goal (str: reach/quality), total_budget (float).

    Returns:
        A confirmation message with the count of campaigns created.
    """
    db = _get_db()
    existing = db.query(Campaign).filter_by(simulation_id=simulation_id).count()
    if existing > 0:
        return f"Simulation {simulation_id} already has {existing} campaigns, skipping."

    try:
        created = 0
        for camp in campaigns:
            budget = camp["total_budget"]
            campaign = Campaign(
                id=str(uuid.uuid4()),
                simulation_id=simulation_id,
                campaign_name=camp["campaign_name"],
                product_description=camp["product_description"],
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
