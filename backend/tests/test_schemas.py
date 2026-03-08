import pytest
from pydantic import ValidationError

from backend.schemas import (
    CampaignResponse,
    ConsumerResponse,
    RunRequest,
    SimulationCreate,
    SimulationResponse,
)


class TestSimulationCreate:
    def test_valid_minimal(self):
        s = SimulationCreate(scenario="test")
        assert s.scenario == "test"
        assert s.num_consumers == 20
        assert s.num_websites == 10
        assert s.num_campaigns == 4

    def test_valid_custom_counts(self):
        s = SimulationCreate(
            scenario="sports brands",
            num_consumers=50,
            num_websites=20,
            num_campaigns=8,
        )
        assert s.num_consumers == 50

    def test_empty_scenario_rejected(self):
        with pytest.raises(ValidationError):
            SimulationCreate(scenario="")

    def test_negative_counts_rejected(self):
        with pytest.raises(ValidationError):
            SimulationCreate(scenario="test", num_consumers=-1)

    def test_too_many_consumers_rejected(self):
        with pytest.raises(ValidationError):
            SimulationCreate(scenario="test", num_consumers=200)

    def test_default_num_rounds(self):
        s = SimulationCreate(scenario="test")
        assert s.num_rounds == 3

    def test_custom_num_rounds(self):
        s = SimulationCreate(scenario="test", num_rounds=10)
        assert s.num_rounds == 10

    def test_zero_rounds_rejected(self):
        with pytest.raises(ValidationError):
            SimulationCreate(scenario="test", num_rounds=0)

    def test_over_50_rounds_rejected(self):
        with pytest.raises(ValidationError):
            SimulationCreate(scenario="test", num_rounds=51)


class TestRunRequest:
    def test_default_rounds(self):
        r = RunRequest()
        assert r.rounds == 1

    def test_custom_rounds(self):
        r = RunRequest(rounds=10)
        assert r.rounds == 10

    def test_zero_rounds_rejected(self):
        with pytest.raises(ValidationError):
            RunRequest(rounds=0)


class TestConsumerResponse:
    def test_from_dict(self):
        c = ConsumerResponse(
            id="abc",
            name="Alice",
            age=25,
            gender="female",
            income_level="high",
            interests=["tech"],
            intent="browsing",
            mood="curious",
            openness_to_ads=4,
            location="NYC",
        )
        assert c.name == "Alice"
        assert c.mood == "curious"
        assert c.openness_to_ads == 4


class TestSimulationResponse:
    def test_response_includes_num_rounds(self):
        resp = SimulationResponse(
            id="abc", scenario="test", status="created",
            created_at="2026-01-01T00:00:00", num_rounds=10,
        )
        assert resp.num_rounds == 10

    def test_response_default_num_rounds(self):
        resp = SimulationResponse(
            id="abc", scenario="test", status="created",
            created_at="2026-01-01T00:00:00",
        )
        assert resp.num_rounds == 3


class TestCampaignResponse:
    def test_from_dict(self):
        c = CampaignResponse(
            id="abc",
            campaign_name="Nike",
            product_description="Shoes",
            creative="Just do it — every step counts",
            goal="reach",
            total_budget=1000.0,
            remaining_budget=800.0,
        )
        assert c.remaining_budget == 800.0
