"""Tests for seeder prompt construction and budget scaling."""

from backend.agents.seeder import SYSTEM_PROMPT, build_seeder_prompt


class TestBuildSeederPrompt:
    def test_prompt_includes_num_rounds(self):
        prompt = build_seeder_prompt("sim-1", "test scenario", 20, 10, 4, 10)
        assert "10" in prompt
        assert "Number of auction rounds: 10" in prompt

    def test_prompt_includes_budget_guidance(self):
        prompt = build_seeder_prompt("sim-1", "test", 20, 10, 4, 10)
        assert "$" in prompt
        assert "Reach campaigns" in prompt
        assert "Quality campaigns" in prompt

    def test_budget_guidance_scales_with_rounds(self):
        prompt_3 = build_seeder_prompt("sim-1", "test", 20, 10, 4, 3)
        prompt_30 = build_seeder_prompt("sim-1", "test", 20, 10, 4, 30)
        # 30 rounds should have higher budget ranges than 3 rounds
        assert prompt_3 != prompt_30

    def test_prompt_includes_simulation_id(self):
        prompt = build_seeder_prompt("abc-123", "test", 20, 10, 4, 5)
        assert "abc-123" in prompt

    def test_prompt_includes_scenario(self):
        prompt = build_seeder_prompt("sim-1", "luxury watches", 20, 10, 4, 5)
        assert "luxury watches" in prompt

    def test_prompt_includes_counts(self):
        prompt = build_seeder_prompt("sim-1", "test", 25, 12, 6, 5)
        assert "25 consumers" in prompt
        assert "12 websites" in prompt
        assert "6 campaigns" in prompt


class TestSeederSystemPrompt:
    def test_system_prompt_mentions_budget_rules(self):
        assert "budget" in SYSTEM_PROMPT.lower()
        assert "rounds" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_reach_and_quality(self):
        assert "reach" in SYSTEM_PROMPT.lower()
        assert "quality" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_personality_traits(self):
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "mood" in prompt_lower
        assert "openness_to_ads" in prompt_lower
        assert "browsing" in prompt_lower
        assert "researching" in prompt_lower
        assert "ready to buy" in prompt_lower

    def test_system_prompt_mentions_creative_rules(self):
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "creative" in prompt_lower
        assert "hook" in prompt_lower
        assert "myth busting" in prompt_lower
