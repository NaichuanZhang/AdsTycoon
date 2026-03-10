"""Integration tests for the consumer module with real LLM calls.

These tests instantiate a Consumer with a Strands Agent backed by
Anthropic's Sonnet model, call generate_intent() and react(), and
validate the structured output end-to-end.

Requires ANTHROPIC_API_KEY to be set in the environment or in .env file.
Run with: uv run pytest consumer/tests/test_integration.py -v -s
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from consumer.agent import Consumer, map_action_to_db_feedback
from consumer.schemas import (
    AdInfo,
    BrowsingIntent,
    ConsumerAction,
    ConsumerPersona,
    ConsumerReaction,
    IncomeLevel,
    WebsiteContext,
)

# Load ANTHROPIC_API_KEY from .env if not already in environment
if not os.environ.get("ANTHROPIC_API_KEY"):
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

INTEGRATION_MODEL_ID = os.environ.get("INTEGRATION_MODEL_ID", "claude-sonnet-4-6")

LOG_DIR = Path(__file__).resolve().parent / "logs"
_run_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"integration_{_run_ts}.jsonl"

SKIP_REASON = "ANTHROPIC_API_KEY not set — skipping integration tests"
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason=SKIP_REASON),
]


def _log_result(test_name: str, **data: object) -> None:
    """Append a JSON line to the integration log file."""
    LOG_DIR.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test": test_name,
        "model": INTEGRATION_MODEL_ID,
        **data,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# --- Fixtures ---


@pytest.fixture
def persona() -> ConsumerPersona:
    return ConsumerPersona(
        id=uuid4(),
        name="Alice",
        age=28,
        gender="female",
        income_level=IncomeLevel.MEDIUM,
        interests=["fitness", "tech", "cooking"],
        location="San Francisco, CA",
    )


@pytest.fixture
def website() -> WebsiteContext:
    return WebsiteContext(
        website_id=uuid4(),
        name="TechCrunch",
        page_context="article about the latest noise-cancelling headphones",
        category="tech",
        ad_placement="sidebar",
    )


@pytest.fixture
def relevant_ad() -> AdInfo:
    return AdInfo(
        campaign_id=uuid4(),
        advertiser_name="Sony",
        product_description="Sony WH-1000XM6 — premium noise-cancelling headphones, $349",
    )


# --- Integration Tests ---


class TestGenerateIntent:
    def test_returns_valid_browsing_intent(
        self,
        persona: ConsumerPersona,
        website: WebsiteContext,
    ):
        """Consumer.generate_intent() should return a well-formed BrowsingIntent."""
        consumer = Consumer(persona=persona, model_id=INTEGRATION_MODEL_ID)
        intent = consumer.generate_intent(website=website)

        assert isinstance(intent, BrowsingIntent)
        assert len(intent.primary_intent) > 0
        assert len(intent.mood) > 0
        assert 1 <= intent.openness_to_ads <= 5

        print(f"\n  Intent: {intent.primary_intent}")
        print(f"  Mood: {intent.mood}")
        print(f"  Openness: {intent.openness_to_ads}/5")

        _log_result(
            "test_returns_valid_browsing_intent",
            persona=persona.model_dump(),
            website=website.model_dump(),
            intent=intent.model_dump(),
        )


class TestReactToAd:
    def test_returns_valid_reaction(
        self,
        persona: ConsumerPersona,
        website: WebsiteContext,
        relevant_ad: AdInfo,
    ):
        """Consumer.react() should return a well-formed ConsumerReaction."""
        consumer = Consumer(persona=persona, model_id=INTEGRATION_MODEL_ID)
        intent = consumer.generate_intent(website=website)
        reaction = consumer.react(ad=relevant_ad, intent=intent)

        assert isinstance(reaction, ConsumerReaction)
        assert reaction.action in ConsumerAction
        assert -1.0 <= reaction.sentiment_score <= 1.0
        assert 0.0 <= reaction.relevance_score <= 1.0
        assert len(reaction.rationale) > 0

        print(f"\n  Action: {reaction.action.value}")
        print(f"  Sentiment: {reaction.sentiment_score:.2f}")
        print(f"  Relevance: {reaction.relevance_score:.2f}")
        print(f"  Rationale: {reaction.rationale}")

        _log_result(
            "test_returns_valid_reaction",
            persona=persona.model_dump(),
            website=website.model_dump(),
            ad=relevant_ad.model_dump(),
            intent=intent.model_dump(),
            reaction=reaction.model_dump(),
        )


class TestFullAuctionFlow:
    def test_end_to_end_with_db_mapping(
        self,
        persona: ConsumerPersona,
        website: WebsiteContext,
        relevant_ad: AdInfo,
    ):
        """Full flow: generate_intent → react → map_action_to_db_feedback."""
        consumer = Consumer(persona=persona, model_id=INTEGRATION_MODEL_ID)

        # Stage 1: Generate intent
        intent = consumer.generate_intent(website=website)
        assert isinstance(intent, BrowsingIntent)

        # Stage 4: React to winning ad
        reaction = consumer.react(ad=relevant_ad, intent=intent)
        assert isinstance(reaction, ConsumerReaction)

        # Stage 8: Map to DB feedback
        db_feedback = map_action_to_db_feedback(reaction.action)
        assert db_feedback in ("like", "dislike", None)

        print(f"\n  Intent: {intent.primary_intent}")
        print(f"  Action: {reaction.action.value} → DB: {db_feedback}")
        print(f"  Sentiment: {reaction.sentiment_score:.2f}")
        print(f"  Relevance: {reaction.relevance_score:.2f}")
        print(f"  Rationale: {reaction.rationale}")

        _log_result(
            "test_end_to_end_with_db_mapping",
            persona=persona.model_dump(),
            website=website.model_dump(),
            ad=relevant_ad.model_dump(),
            intent=intent.model_dump(),
            reaction=reaction.model_dump(),
            db_feedback=db_feedback,
        )
