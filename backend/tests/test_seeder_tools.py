"""Tests for seeder tools — direct tool function calls with real DB session."""

from sqlalchemy.orm import Session

from backend.models import Campaign, Consumer, Simulation, Website
from backend.tools.seeder_tools import (
    create_campaigns,
    create_consumers,
    create_websites,
    set_session_factory,
)


def _make_sim(db: Session) -> Simulation:
    sim = Simulation(scenario="test")
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


class TestCreateConsumers:
    def test_inserts_consumers(self, db_session: Session, db_session_factory):
        set_session_factory(db_session_factory)
        sim = _make_sim(db_session)

        consumers_data = [
            {
                "name": "Alice",
                "age": 25,
                "gender": "female",
                "income_level": "high",
                "interests": ["tech", "gaming"],
                "intent": "browsing",
                "mood": "curious",
                "openness_to_ads": 4,
                "location": "NYC",
            },
            {
                "name": "Bob",
                "age": 40,
                "gender": "male",
                "income_level": "medium",
                "interests": ["sports"],
                "intent": "ready to buy",
                "mood": "relaxed",
                "openness_to_ads": 2,
                "location": "LA",
            },
        ]

        result = create_consumers._tool_func(
            simulation_id=sim.id, consumers=consumers_data
        )
        assert "Created 2 consumers" in result

        rows = db_session.query(Consumer).filter_by(simulation_id=sim.id).all()
        assert len(rows) == 2
        names = {r.name for r in rows}
        assert names == {"Alice", "Bob"}
        by_name = {r.name: r for r in rows}
        assert by_name["Alice"].mood == "curious"
        assert by_name["Alice"].openness_to_ads == 4
        assert by_name["Bob"].mood == "relaxed"
        assert by_name["Bob"].openness_to_ads == 2

    def test_defaults_when_fields_omitted(self, db_session: Session, db_session_factory):
        set_session_factory(db_session_factory)
        sim = _make_sim(db_session)

        consumers_data = [
            {
                "name": "Charlie",
                "age": 30,
                "gender": "male",
                "income_level": "low",
                "interests": ["cooking"],
                "intent": "browsing",
                "location": "Denver",
            },
        ]

        result = create_consumers._tool_func(
            simulation_id=sim.id, consumers=consumers_data
        )
        assert "Created 1 consumers" in result

        row = db_session.query(Consumer).filter_by(simulation_id=sim.id).first()
        assert row.mood == "neutral"
        assert row.openness_to_ads == 3


class TestCreateWebsites:
    def test_inserts_websites(self, db_session: Session, db_session_factory):
        set_session_factory(db_session_factory)
        sim = _make_sim(db_session)

        websites_data = [
            {
                "name": "TechCrunch",
                "page_context": "article about AI startups",
                "ad_placement": "banner",
                "category": "tech",
            },
        ]

        result = create_websites._tool_func(
            simulation_id=sim.id, websites=websites_data
        )
        assert "Created 1 websites" in result

        rows = db_session.query(Website).filter_by(simulation_id=sim.id).all()
        assert len(rows) == 1
        assert rows[0].name == "TechCrunch"


class TestCreateCampaigns:
    def test_inserts_campaigns(self, db_session: Session, db_session_factory):
        set_session_factory(db_session_factory)
        sim = _make_sim(db_session)

        campaigns_data = [
            {
                "campaign_name": "Nike Reach",
                "product_description": "Running shoes for everyone",
                "creative": "Every finish line starts with a single step — lace up",
                "goal": "reach",
                "total_budget": 1000.0,
            },
            {
                "campaign_name": "Adidas Quality",
                "product_description": "Premium trainers",
                "creative": "73% of athletes chose comfort over hype — here's why",
                "goal": "quality",
                "total_budget": 500.0,
            },
        ]

        result = create_campaigns._tool_func(
            simulation_id=sim.id, campaigns=campaigns_data
        )
        assert "Created 2 campaigns" in result

        rows = db_session.query(Campaign).filter_by(simulation_id=sim.id).all()
        assert len(rows) == 2
        for row in rows:
            assert row.remaining_budget == row.total_budget
