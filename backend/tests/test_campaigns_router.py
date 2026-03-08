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


def _make_sim(db: Session) -> Simulation:
    sim = Simulation(scenario="test")
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


def _make_campaign(db: Session, sim: Simulation, **overrides) -> Campaign:
    defaults = dict(
        simulation_id=sim.id,
        campaign_name="Nike",
        product_description="Shoes",
        creative="Just do it — every step counts",
        goal="reach",
        total_budget=100.0,
        remaining_budget=100.0,
    )
    defaults.update(overrides)
    campaign = Campaign(**defaults)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


class TestUpdateCampaign:
    def _url(self, sim_id: str, campaign_id: str) -> str:
        return f"/api/simulations/{sim_id}/campaigns/{campaign_id}"

    def test_update_single_field(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim)
        resp = client.put(self._url(sim.id, campaign.id), json={"campaign_name": "Adidas"})
        assert resp.status_code == 200
        assert resp.json()["campaign_name"] == "Adidas"

    def test_update_all_fields(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim)
        payload = {
            "campaign_name": "Adidas",
            "product_description": "Running shoes",
            "creative": "Impossible is nothing",
            "goal": "quality",
            "total_budget": 200.0,
        }
        resp = client.put(self._url(sim.id, campaign.id), json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["campaign_name"] == "Adidas"
        assert data["product_description"] == "Running shoes"
        assert data["creative"] == "Impossible is nothing"
        assert data["goal"] == "quality"
        assert data["total_budget"] == 200.0
        assert data["remaining_budget"] == 200.0

    def test_update_budget_syncs_remaining(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim, remaining_budget=50.0)
        resp = client.put(self._url(sim.id, campaign.id), json={"total_budget": 300.0})
        assert resp.status_code == 200
        assert resp.json()["remaining_budget"] == 300.0

    def test_update_budget_must_be_positive(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim)
        assert client.put(self._url(sim.id, campaign.id), json={"total_budget": 0}).status_code == 422
        assert client.put(self._url(sim.id, campaign.id), json={"total_budget": -5}).status_code == 422

    def test_update_goal_valid_values(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim)
        assert client.put(self._url(sim.id, campaign.id), json={"goal": "quality"}).status_code == 200
        assert client.put(self._url(sim.id, campaign.id), json={"goal": "invalid"}).status_code == 422

    def test_update_empty_name_rejected(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim)
        assert client.put(self._url(sim.id, campaign.id), json={"campaign_name": ""}).status_code == 422

    def test_update_campaign_not_found(self, client, db_session):
        sim = _make_sim(db_session)
        resp = client.put(self._url(sim.id, "nonexistent"), json={"campaign_name": "X"})
        assert resp.status_code == 404

    def test_update_sim_not_found(self, client, db_session):
        resp = client.put(self._url("nonexistent", "nonexistent"), json={"campaign_name": "X"})
        assert resp.status_code == 404

    def test_partial_update_preserves_other_fields(self, client, db_session):
        sim = _make_sim(db_session)
        campaign = _make_campaign(db_session, sim)
        resp = client.put(self._url(sim.id, campaign.id), json={"campaign_name": "Puma"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["campaign_name"] == "Puma"
        assert data["product_description"] == "Shoes"
        assert data["creative"] == "Just do it — every step counts"
        assert data["goal"] == "reach"
        assert data["total_budget"] == 100.0


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
