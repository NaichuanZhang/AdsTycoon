"""Tests for consumer schema validation and enum constraints.

Covers: ConsumerPersona, WebsiteContext, BrowsingIntent, AdInfo,
ConsumerAction, ConsumerReaction — valid construction, invalid inputs,
boundary values, and enum membership.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from consumer.schemas import (
    AdInfo,
    BrowsingIntent,
    ConsumerAction,
    ConsumerPersona,
    ConsumerReaction,
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


@pytest.fixture
def sample_reaction() -> ConsumerReaction:
    return ConsumerReaction(
        action=ConsumerAction.LIKE,
        sentiment_score=0.7,
        rationale="This is exactly what I was looking for — great brand and matches my budget.",
        relevance_score=0.9,
    )


# --- ConsumerPersona ---


class TestConsumerPersona:
    def test_valid_persona(self, sample_persona: ConsumerPersona):
        assert sample_persona.name == "Alice"
        assert sample_persona.age == 28
        assert sample_persona.income_level == IncomeLevel.MEDIUM
        assert len(sample_persona.interests) == 3

    def test_invalid_income_level(self):
        with pytest.raises(ValidationError):
            ConsumerPersona(
                id=uuid4(),
                name="Bob",
                age=35,
                gender="male",
                income_level="ultra_rich",
                interests=["golf"],
                location="NYC",
            )

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            ConsumerPersona(
                id=uuid4(),
                name="Bob",
                age=35,
                gender="male",
                income_level=IncomeLevel.HIGH,
                # missing interests and location
            )


# --- WebsiteContext ---


class TestWebsiteContext:
    def test_valid_website(self, sample_website: WebsiteContext):
        assert sample_website.name == "TechCrunch"
        assert sample_website.category == "tech"
        assert sample_website.ad_placement == "sidebar"


# --- BrowsingIntent ---


class TestBrowsingIntent:
    def test_valid_intent(self, sample_intent: BrowsingIntent):
        assert sample_intent.openness_to_ads == 4
        assert sample_intent.mood == "curious"

    def test_openness_too_low(self):
        with pytest.raises(ValidationError):
            BrowsingIntent(
                primary_intent="just browsing",
                mood="bored",
                openness_to_ads=0,
            )

    def test_openness_too_high(self):
        with pytest.raises(ValidationError):
            BrowsingIntent(
                primary_intent="just browsing",
                mood="bored",
                openness_to_ads=6,
            )

    def test_openness_boundary_values(self):
        low = BrowsingIntent(primary_intent="x", mood="x", openness_to_ads=1)
        high = BrowsingIntent(primary_intent="x", mood="x", openness_to_ads=5)
        assert low.openness_to_ads == 1
        assert high.openness_to_ads == 5


# --- AdInfo ---


class TestAdInfo:
    def test_valid_ad(self, sample_ad: AdInfo):
        assert sample_ad.advertiser_name == "Sony"


# --- ConsumerAction ---


class TestConsumerAction:
    def test_enum_values(self):
        assert ConsumerAction.LIKE.value == "like"
        assert ConsumerAction.DISLIKE.value == "dislike"
        assert ConsumerAction.IGNORE.value == "ignore"

    def test_enum_count(self):
        assert len(ConsumerAction) == 3


# --- ConsumerReaction ---


class TestConsumerReaction:
    def test_valid_reaction(self, sample_reaction: ConsumerReaction):
        assert sample_reaction.action == ConsumerAction.LIKE
        assert sample_reaction.sentiment_score == 0.7
        assert sample_reaction.relevance_score == 0.9

    def test_sentiment_too_low(self):
        with pytest.raises(ValidationError):
            ConsumerReaction(
                action=ConsumerAction.DISLIKE,
                sentiment_score=-1.5,
                rationale="terrible",
                relevance_score=0.1,
            )

    def test_sentiment_too_high(self):
        with pytest.raises(ValidationError):
            ConsumerReaction(
                action=ConsumerAction.LIKE,
                sentiment_score=1.5,
                rationale="amazing",
                relevance_score=0.9,
            )

    def test_relevance_out_of_range(self):
        with pytest.raises(ValidationError):
            ConsumerReaction(
                action=ConsumerAction.IGNORE,
                sentiment_score=0.0,
                rationale="whatever",
                relevance_score=1.5,
            )

    def test_boundary_values(self):
        reaction = ConsumerReaction(
            action=ConsumerAction.DISLIKE,
            sentiment_score=-1.0,
            rationale="worst ad ever",
            relevance_score=0.0,
        )
        assert reaction.sentiment_score == -1.0
        assert reaction.relevance_score == 0.0
