"""Tests for insights tools."""

from sqlalchemy.orm import Session

from backend.models import Auction, Bid, Campaign, Consumer, Simulation, Website
from backend.tools.insights_tools import (
    get_campaign_auctions,
    get_campaign_stats,
    set_db_session,
)


def _populate(db: Session):
    sim = Simulation(scenario="test")
    db.add(sim)
    db.commit()
    db.refresh(sim)

    consumer = Consumer(
        simulation_id=sim.id, name="Alice", age=25, gender="female",
        income_level="high", interests=["tech"], intent="browsing",
        mood="curious", openness_to_ads=4, location="NYC",
    )
    website = Website(
        simulation_id=sim.id, name="TechCrunch", page_context="AI article",
        ad_placement="banner", category="tech",
    )
    campaign = Campaign(
        simulation_id=sim.id, campaign_name="Nike", product_description="Shoes",
        creative="Just do it — every step counts",
        goal="reach", total_budget=100.0, remaining_budget=90.0,
    )
    db.add_all([consumer, website, campaign])
    db.commit()
    db.refresh(consumer)
    db.refresh(website)
    db.refresh(campaign)

    auction = Auction(
        simulation_id=sim.id, consumer_id=consumer.id, website_id=website.id,
        winning_campaign_id=campaign.id, winning_bid=5.0, consumer_feedback="like",
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    bid = Bid(
        auction_id=auction.id, campaign_id=campaign.id,
        bid_amount=5.0, reasoning="Good match",
    )
    db.add(bid)
    db.commit()

    return campaign


class TestGetCampaignAuctions:
    def test_returns_history(self, db_session):
        set_db_session(db_session)
        campaign = _populate(db_session)
        result = get_campaign_auctions._tool_func(campaign_id=campaign.id)
        assert "1 bids" in result
        assert "WON" in result
        assert "$5.00" in result

    def test_no_history(self, db_session):
        set_db_session(db_session)
        sim = Simulation(scenario="test")
        db_session.add(sim)
        db_session.commit()
        db_session.refresh(sim)
        camp = Campaign(
            simulation_id=sim.id, campaign_name="Empty", product_description="None",
            creative="No creative yet",
            goal="reach", total_budget=100.0, remaining_budget=100.0,
        )
        db_session.add(camp)
        db_session.commit()
        db_session.refresh(camp)
        result = get_campaign_auctions._tool_func(campaign_id=camp.id)
        assert "No auction history" in result


class TestGetCampaignStats:
    def test_returns_stats(self, db_session):
        set_db_session(db_session)
        campaign = _populate(db_session)
        result = get_campaign_stats._tool_func(campaign_id=campaign.id)
        assert "Nike" in result
        assert "Wins: 1" in result
        assert "Likes: 1" in result
        assert "$5.00" in result

    def test_not_found(self, db_session):
        set_db_session(db_session)
        result = get_campaign_stats._tool_func(campaign_id="nonexistent")
        assert "not found" in result
