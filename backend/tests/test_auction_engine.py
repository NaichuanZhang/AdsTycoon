"""Tests for auction engine with mocked agents."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from backend.models import Auction, Bid, Campaign, Consumer, Simulation, Website
from backend.services.auction_engine import reset_simulation, run_single_auction


def _setup_simulation(db: Session):
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
    camp1 = Campaign(
        simulation_id=sim.id, campaign_name="Nike", product_description="Shoes",
        creative="Every finish line starts with a single step",
        goal="reach", total_budget=100.0, remaining_budget=100.0,
    )
    camp2 = Campaign(
        simulation_id=sim.id, campaign_name="Adidas", product_description="Trainers",
        creative="73% of athletes chose comfort over hype",
        goal="quality", total_budget=50.0, remaining_budget=50.0,
    )
    db.add_all([consumer, website, camp1, camp2])
    db.commit()
    db.refresh(sim)
    return sim, camp1, camp2


def _mock_campaign_agent(campaign_id, auction_id, consumer_profile, website_context, db_session):
    """Simulate a campaign placing a bid."""
    import uuid
    camp = db_session.query(Campaign).filter_by(id=campaign_id).first()
    bid_amount = 5.0 if camp.goal == "reach" else 10.0
    bid = Bid(
        id=str(uuid.uuid4()),
        auction_id=auction_id,
        campaign_id=campaign_id,
        bid_amount=bid_amount,
        reasoning=f"Test bid for {camp.campaign_name}",
    )
    db_session.add(bid)
    db_session.commit()


def _mock_consumer_agent(auction_id, consumer_profile, website_context, ad_description, db_session):
    """Simulate consumer feedback."""
    auction = db_session.query(Auction).filter_by(id=auction_id).first()
    auction.consumer_feedback = "like"
    db_session.commit()


class TestRunSingleAuction:
    @patch("backend.services.auction_engine.run_consumer_agent", side_effect=_mock_consumer_agent)
    @patch("backend.services.auction_engine.run_campaign_agent", side_effect=_mock_campaign_agent)
    def test_auction_selects_highest_bid(self, mock_camp, mock_cons, db_session):
        sim, camp1, camp2 = _setup_simulation(db_session)

        auction = run_single_auction(db_session, sim.id)

        assert auction.winning_campaign_id == camp2.id  # quality bids $10 > reach $5
        assert auction.winning_bid == 10.0
        assert auction.consumer_feedback == "like"
        assert len(auction.bids) == 2

    @patch("backend.services.auction_engine.run_consumer_agent", side_effect=_mock_consumer_agent)
    @patch("backend.services.auction_engine.run_campaign_agent", side_effect=_mock_campaign_agent)
    def test_budget_deducted(self, mock_camp, mock_cons, db_session):
        sim, camp1, camp2 = _setup_simulation(db_session)

        run_single_auction(db_session, sim.id)

        db_session.refresh(camp2)
        assert camp2.remaining_budget == 40.0  # 50 - 10

    def test_no_data_raises(self, db_session):
        sim = Simulation(scenario="empty")
        db_session.add(sim)
        db_session.commit()
        db_session.refresh(sim)

        with pytest.raises(ValueError, match="must have consumers"):
            run_single_auction(db_session, sim.id)


class TestResetSimulation:
    @patch("backend.services.auction_engine.run_consumer_agent", side_effect=_mock_consumer_agent)
    @patch("backend.services.auction_engine.run_campaign_agent", side_effect=_mock_campaign_agent)
    def test_reset_clears_auctions_and_restores_budgets(self, mock_camp, mock_cons, db_session):
        sim, camp1, camp2 = _setup_simulation(db_session)

        run_single_auction(db_session, sim.id)
        assert db_session.query(Auction).filter_by(simulation_id=sim.id).count() == 1

        reset_simulation(db_session, sim.id)

        assert db_session.query(Auction).filter_by(simulation_id=sim.id).count() == 0
        db_session.refresh(camp1)
        db_session.refresh(camp2)
        assert camp1.remaining_budget == 100.0
        assert camp2.remaining_budget == 50.0
