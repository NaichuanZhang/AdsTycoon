"""Tests for consumer feedback tools."""

from sqlalchemy.orm import Session

from backend.models import Auction, Campaign, Consumer, Simulation, Website
from backend.tools.consumer_tools import set_db_session, submit_feedback


def _setup_auction(db: Session):
    sim = Simulation(scenario="test")
    db.add(sim)
    db.commit()
    db.refresh(sim)

    consumer = Consumer(
        simulation_id=sim.id, name="Alice", age=25, gender="female",
        income_level="high", interests=["tech"], intent="browsing", location="NYC",
    )
    website = Website(
        simulation_id=sim.id, name="TechCrunch", page_context="AI article",
        ad_placement="banner", category="tech",
    )
    campaign = Campaign(
        simulation_id=sim.id, campaign_name="Nike", product_description="Shoes",
        goal="reach", total_budget=100.0, remaining_budget=100.0,
    )
    db.add_all([consumer, website, campaign])
    db.commit()
    db.refresh(consumer)
    db.refresh(website)
    db.refresh(campaign)

    auction = Auction(
        simulation_id=sim.id, consumer_id=consumer.id, website_id=website.id,
        winning_campaign_id=campaign.id, winning_bid=5.0,
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    return auction


class TestSubmitFeedback:
    def test_like(self, db_session):
        set_db_session(db_session)
        auction = _setup_auction(db_session)
        result = submit_feedback._tool_func(
            auction_id=auction.id, feedback="like", reasoning="Relevant ad",
        )
        assert "like" in result
        db_session.refresh(auction)
        assert auction.consumer_feedback == "like"

    def test_dislike(self, db_session):
        set_db_session(db_session)
        auction = _setup_auction(db_session)
        result = submit_feedback._tool_func(
            auction_id=auction.id, feedback="dislike", reasoning="Irrelevant",
        )
        assert "dislike" in result
        db_session.refresh(auction)
        assert auction.consumer_feedback == "dislike"

    def test_invalid_feedback(self, db_session):
        set_db_session(db_session)
        auction = _setup_auction(db_session)
        result = submit_feedback._tool_func(
            auction_id=auction.id, feedback="meh", reasoning="Whatever",
        )
        assert "Invalid feedback" in result
        db_session.refresh(auction)
        assert auction.consumer_feedback is None
