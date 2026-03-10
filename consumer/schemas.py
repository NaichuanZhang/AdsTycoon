"""Pydantic schemas for the consumer module.

Defines data models for consumer personas, website contexts, browsing intents,
ad information, and consumer reactions to ads.
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Gender(str, Enum):
    """Consumer gender categories."""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"


class IncomeLevel(str, Enum):
    """Consumer income level brackets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConsumerPersona(BaseModel):
    """Consumer demographic profile loaded from the database.

    Maps directly to the `consumers` table schema.

    Attributes:
        id: Unique consumer identifier.
        name: Consumer's display name.
        age: Consumer's age in years.
        gender: Consumer's gender.
        income_level: Household income bracket.
        interests: List of interest categories (e.g., ["sports", "tech"]).
        location: Geographic location string.
    """

    id: UUID
    name: str
    age: int
    gender: str
    income_level: IncomeLevel
    interests: list[str]
    location: str


class WebsiteContext(BaseModel):
    """Website/page context where the ad slot is being served.

    Maps to the `websites` table schema. Passed to generate_intent()
    so the consumer's browsing intent is influenced by the page they're on.

    Attributes:
        website_id: Unique site identifier.
        name: Website name (e.g., "TechCrunch", "ESPN").
        page_context: Description of the page content.
        category: Site category (e.g., sports, tech, finance).
        ad_placement: Where on the page the ad appears.
    """

    website_id: UUID
    name: str
    page_context: str
    category: str
    ad_placement: str


class BrowsingIntent(BaseModel):
    """LLM-generated browsing intent for a consumer.

    Represents why the consumer is on the page right now,
    derived from their persona and the website context.

    Attributes:
        primary_intent: The main thing the consumer is looking for.
        mood: The consumer's current emotional state.
        openness_to_ads: How receptive the consumer is to advertising
            right now, on a scale of 1 (annoyed) to 5 (actively seeking).
    """

    primary_intent: str = Field(
        description=(
            "The main thing the consumer is browsing for right now, "
            "written in first person (e.g., 'I am looking for new running shoes')"
        ),
    )
    mood: str = Field(
        description=(
            "The consumer's current emotional state in one word "
            "(e.g., 'excited', 'bored', 'focused', 'curious')"
        ),
    )
    openness_to_ads: int = Field(
        ge=1,
        le=5,
        description=(
            "How receptive the consumer is to seeing ads right now. "
            "1 = very annoyed by ads, 5 = actively seeking product recommendations"
        ),
    )


class AdInfo(BaseModel):
    """Information about an ad shown to the consumer.

    Populated from the winning campaign data. The consumer does not
    need to know bid amounts or budgets — only the creative.

    Attributes:
        campaign_id: The campaign this ad belongs to.
        advertiser_name: Name of the advertiser.
        product_description: The ad creative/copy shown to the consumer.
    """

    campaign_id: UUID
    advertiser_name: str
    product_description: str


class ConsumerAction(str, Enum):
    """Possible consumer actions in response to an ad."""

    LIKE = "like"
    DISLIKE = "dislike"
    IGNORE = "ignore"


class ConsumerReaction(BaseModel):
    """LLM-generated consumer reaction to an ad.

    Structured output from the react() method, representing the
    consumer's feedback after seeing an ad.

    Attributes:
        action: The consumer's action (like, dislike, or ignore).
        sentiment_score: Numeric sentiment from -1.0 (very negative)
            to 1.0 (very positive).
        rationale: Free-text explanation of why the consumer reacted this way.
        relevance_score: How relevant the ad felt to the consumer's
            current intent, from 0.0 (irrelevant) to 1.0 (perfectly targeted).
    """

    action: ConsumerAction = Field(
        description=(
            "The consumer's action: 'like' if the ad resonates, "
            "'dislike' if it is off-putting, 'ignore' if it is irrelevant"
        ),
    )
    sentiment_score: float = Field(
        ge=-1.0,
        le=1.0,
        description=(
            "How the consumer feels about the ad. "
            "-1.0 = very negative, 0.0 = neutral, 1.0 = very positive"
        ),
    )
    rationale: str = Field(
        description=(
            "A 1-2 sentence explanation in first person of why the consumer "
            "reacted this way, considering their persona, intent, and the ad content"
        ),
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How relevant the ad is to the consumer's current browsing intent. "
            "0.0 = completely irrelevant, 1.0 = perfectly targeted"
        ),
    )
