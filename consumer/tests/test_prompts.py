"""Tests for consumer prompt template formatting.

Verifies that all prompt templates accept their expected placeholders
and produce correctly interpolated strings.
"""

from uuid import uuid4

import pytest

from consumer.prompts import (
    CONSUMER_SYSTEM_PROMPT,
    GENERATE_INTENT_PROMPT,
    REACT_TO_AD_PROMPT,
)
from consumer.schemas import (
    AdInfo,
    BrowsingIntent,
    ConsumerPersona,
    IncomeLevel,
    WebsiteContext,
)


# --- Fixtures ---


@pytest.fixture
def sample_persona() -> ConsumerPersona:
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
def sample_website() -> WebsiteContext:
    return WebsiteContext(
        website_id=uuid4(),
        name="TechCrunch",
        page_context="article about the latest noise-cancelling headphones",
        category="tech",
        ad_placement="sidebar",
    )


@pytest.fixture
def sample_ad() -> AdInfo:
    return AdInfo(
        campaign_id=uuid4(),
        advertiser_name="Sony",
        product_description="Sony WH-1000XM6 — premium noise-cancelling headphones, $349",
    )


@pytest.fixture
def sample_intent() -> BrowsingIntent:
    return BrowsingIntent(
        primary_intent="I am researching noise-cancelling headphones for my commute",
        mood="curious",
        openness_to_ads=4,
    )


# --- Prompt Template Tests ---


class TestPromptTemplates:
    def test_system_prompt_formats(self, sample_persona: ConsumerPersona):
        result = CONSUMER_SYSTEM_PROMPT.format(
            name=sample_persona.name,
            age=sample_persona.age,
            gender=sample_persona.gender,
            income_level=sample_persona.income_level.value,
            interests=", ".join(sample_persona.interests),
            location=sample_persona.location,
        )
        assert "Alice" in result
        assert "28" in result
        assert "fitness, tech, cooking" in result
        assert "San Francisco" in result
        assert "medium" in result

    def test_generate_intent_prompt_formats(self, sample_website: WebsiteContext):
        result = GENERATE_INTENT_PROMPT.format(
            website_name=sample_website.name,
            website_category=sample_website.category,
            page_context=sample_website.page_context,
        )
        assert "TechCrunch" in result
        assert "tech" in result
        assert "noise-cancelling headphones" in result

    def test_react_prompt_formats(self, sample_ad: AdInfo, sample_intent: BrowsingIntent):
        result = REACT_TO_AD_PROMPT.format(
            intent=sample_intent.primary_intent,
            mood=sample_intent.mood,
            openness_to_ads=sample_intent.openness_to_ads,
            advertiser_name=sample_ad.advertiser_name,
            product_description=sample_ad.product_description,
        )
        assert "Sony" in result
        assert "curious" in result
        assert "4/5" in result
        assert "noise-cancelling headphones" in result
