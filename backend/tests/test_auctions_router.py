"""Tests for auctions router."""

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
        goal="reach", total_budget=100.0, remaining_budget=95.0,
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

    return sim, auction


class TestListAuctions:
    def test_list(self, client, db_session):
        sim, _ = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/auctions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["winning_bid"] == 5.0

    def test_not_found_sim(self, client):
        resp = client.get("/api/simulations/nonexistent/auctions")
        assert resp.status_code == 404


class TestGetAuction:
    def test_detail(self, client, db_session):
        sim, auction = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/auctions/{auction.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["consumer"]["name"] == "Alice"
        assert data["website"]["name"] == "TechCrunch"
        assert len(data["bids"]) == 1
        assert data["bids"][0]["campaign_name"] == "Nike"

    def test_not_found(self, client, db_session):
        sim, _ = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/auctions/nonexistent")
        assert resp.status_code == 404
