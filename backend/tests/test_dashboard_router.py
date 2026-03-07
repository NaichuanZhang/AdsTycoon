"""Tests for dashboard router."""

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
    camp1 = Campaign(
        simulation_id=sim.id, campaign_name="Nike", product_description="Shoes",
        goal="reach", total_budget=100.0, remaining_budget=90.0,
    )
    camp2 = Campaign(
        simulation_id=sim.id, campaign_name="Adidas", product_description="Trainers",
        goal="quality", total_budget=50.0, remaining_budget=50.0,
    )
    db.add_all([consumer, website, camp1, camp2])
    db.commit()
    db.refresh(consumer)
    db.refresh(website)
    db.refresh(camp1)

    auction = Auction(
        simulation_id=sim.id, consumer_id=consumer.id, website_id=website.id,
        winning_campaign_id=camp1.id, winning_bid=5.0, consumer_feedback="like",
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    bid1 = Bid(auction_id=auction.id, campaign_id=camp1.id, bid_amount=5.0, reasoning="match")
    bid2 = Bid(auction_id=auction.id, campaign_id=camp2.id, bid_amount=3.0, reasoning="low")
    db.add_all([bid1, bid2])
    db.commit()

    return sim


class TestDashboard:
    def test_dashboard_stats(self, client, db_session):
        sim = _populate(db_session)
        resp = client.get(f"/api/simulations/{sim.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_auctions"] == 1
        assert data["total_bids"] == 2
        assert data["avg_winning_bid"] == 5.0
        assert data["likes"] == 1
        assert data["dislikes"] == 0
        assert data["like_ratio"] == 100.0
        assert data["total_budget_spent"] == 10.0  # 100 - 90 = 10
        assert len(data["campaigns"]) == 2

    def test_empty_dashboard(self, client, db_session):
        sim = Simulation(scenario="empty")
        db_session.add(sim)
        db_session.commit()
        db_session.refresh(sim)

        resp = client.get(f"/api/simulations/{sim.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_auctions"] == 0

    def test_not_found(self, client):
        resp = client.get("/api/simulations/nonexistent/dashboard")
        assert resp.status_code == 404
