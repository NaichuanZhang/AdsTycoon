"""Tests for simulations router with mocked seeder agent."""

from unittest.mock import patch

from sqlalchemy.orm import Session

from backend.models import Campaign, Consumer, Simulation, Website


def _seed_manually(db: Session, sim_id: str):
    """Manually seed data instead of calling the real AI agent."""
    db.add(Consumer(
        simulation_id=sim_id, name="Alice", age=25, gender="female",
        income_level="high", interests=["tech"], intent="browsing", location="NYC",
    ))
    db.add(Website(
        simulation_id=sim_id, name="TechCrunch", page_context="AI article",
        ad_placement="banner", category="tech",
    ))
    db.add(Campaign(
        simulation_id=sim_id, campaign_name="Nike", product_description="Shoes",
        goal="reach", total_budget=1000.0, remaining_budget=1000.0,
    ))
    db.commit()


class TestCreateSimulation:
    def test_create_simulation_returns_201(self, client, db_session):
        resp = client.post("/api/simulations", json={
            "scenario": "sports brands targeting young males",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["scenario"] == "sports brands targeting young males"
        assert data["status"] == "created"
        assert data["consumer_count"] == 0
        assert data["website_count"] == 0
        assert data["campaign_count"] == 0

    @patch("backend.routers.simulations.run_seeder")
    def test_seed_simulation(self, mock_seeder, client, db_session):
        mock_seeder.side_effect = lambda simulation_id, scenario, num_consumers, num_websites, num_campaigns, db_session: _seed_manually(db_session, simulation_id)

        sim = Simulation(scenario="test seed", status="created")
        db_session.add(sim)
        db_session.commit()
        db_session.refresh(sim)

        resp = client.post(f"/api/simulations/{sim.id}/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "seeded"
        assert data["consumer_count"] == 1


class TestListSimulations:
    def test_list_empty(self, client):
        resp = client.get("/api/simulations")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, client, db_session):
        sim = Simulation(scenario="test")
        db_session.add(sim)
        db_session.commit()

        resp = client.get("/api/simulations")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetSimulation:
    def test_get_existing(self, client, db_session):
        sim = Simulation(scenario="test")
        db_session.add(sim)
        db_session.commit()
        db_session.refresh(sim)

        resp = client.get(f"/api/simulations/{sim.id}")
        assert resp.status_code == 200
        assert resp.json()["scenario"] == "test"

    def test_get_not_found(self, client):
        resp = client.get("/api/simulations/nonexistent")
        assert resp.status_code == 404
