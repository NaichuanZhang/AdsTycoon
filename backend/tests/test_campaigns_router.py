"""Tests for campaigns router."""

from unittest.mock import patch

from sqlalchemy.orm import Session

from backend.models import Auction, Bid, Campaign, Consumer, Simulation, Website


def _populate(db: Session):
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

    return sim, campaign


class TestListCampaigns:
    def test_list(self, client, db_session):
        sim, _ = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/campaigns")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["campaign_name"] == "Nike"


class TestGetCampaign:
    def test_detail_with_stats(self, client, db_session):
        sim, campaign = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/campaigns/{campaign.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_bids"] == 1
        assert data["stats"]["wins"] == 1
        assert data["stats"]["likes"] == 1

    def test_not_found(self, client, db_session):
        sim, _ = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/campaigns/nonexistent")
        assert resp.status_code == 404


class TestCampaignInsights:
    @patch("backend.routers.campaigns.run_insights_agent")
    def test_insights(self, mock_insights, client, db_session):
        sim, campaign = _populate(db_session)
        mock_insights.return_value = {
            "summary": "Campaign performing well",
            "suggestions": ["Increase budget", "Target more users"],
        }
        resp = client.get(f"/api/simulations/{sim.id}/campaigns/{campaign.id}/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == "Campaign performing well"
        assert len(data["suggestions"]) == 2
