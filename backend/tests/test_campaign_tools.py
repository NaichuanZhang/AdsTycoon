"""Tests for campaign tools."""

from sqlalchemy.orm import Session

from backend.models import Auction, Bid, Campaign, Consumer, Simulation, Website
from backend.tools.campaign_tools import get_campaign, set_db_session, submit_bid


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
        creative="Just do it — every step counts",
        goal="reach", total_budget=100.0, remaining_budget=100.0,
    )
    db.add_all([consumer, website, campaign])
    db.commit()
    db.refresh(consumer)
    db.refresh(website)
    db.refresh(campaign)

    auction = Auction(
        simulation_id=sim.id, consumer_id=consumer.id, website_id=website.id,
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    return sim, consumer, website, campaign, auction


class TestGetCampaign:
    def test_returns_campaign_details(self, db_session):
        set_db_session(db_session)
        _, _, _, campaign, _ = _setup_auction(db_session)
        result = get_campaign._tool_func(campaign_id=campaign.id)
        assert "Nike" in result
        assert "$100.00" in result

    def test_not_found(self, db_session):
        set_db_session(db_session)
        result = get_campaign._tool_func(campaign_id="nonexistent")
        assert "not found" in result


class TestSubmitBid:
    def test_valid_bid(self, db_session):
        set_db_session(db_session)
        _, _, _, campaign, auction = _setup_auction(db_session)
        result = submit_bid._tool_func(
            auction_id=auction.id, campaign_id=campaign.id,
            bid_amount=5.0, reasoning="Good match",
        )
        assert "Bid of $5.00" in result

        bids = db_session.query(Bid).filter_by(auction_id=auction.id).all()
        assert len(bids) == 1
        assert bids[0].bid_amount == 5.0

    def test_bid_exceeds_budget(self, db_session):
        set_db_session(db_session)
        _, _, _, campaign, auction = _setup_auction(db_session)
        result = submit_bid._tool_func(
            auction_id=auction.id, campaign_id=campaign.id,
            bid_amount=200.0, reasoning="Too much",
        )
        assert "exceeds remaining budget" in result

        bids = db_session.query(Bid).filter_by(auction_id=auction.id).all()
        assert len(bids) == 0

    def test_negative_bid_rejected(self, db_session):
        set_db_session(db_session)
        _, _, _, campaign, auction = _setup_auction(db_session)
        result = submit_bid._tool_func(
            auction_id=auction.id, campaign_id=campaign.id,
            bid_amount=-1.0, reasoning="Negative",
        )
        assert "must be positive" in result
