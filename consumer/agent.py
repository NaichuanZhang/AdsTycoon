"""Consumer agent for the ad bidding simulation.

Wraps a Strands Agent to simulate a consumer who generates browsing
intent and reacts to advertisements based on their persona.
"""

import logging

from strands import Agent
from strands.models.anthropic import AnthropicModel

from .prompts import CONSUMER_SYSTEM_PROMPT, GENERATE_INTENT_PROMPT, REACT_TO_AD_PROMPT
from .schemas import (
    AdInfo,
    BrowsingIntent,
    ConsumerAction,
    ConsumerPersona,
    ConsumerReaction,
    WebsiteContext,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ID = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 1024


class Consumer:
    """Simulated consumer agent powered by an LLM.

    Wraps a Strands Agent with a persona-specific system prompt to simulate
    realistic consumer behavior in the ad bidding auction loop.

    The Consumer is used in two stages of the auction:
    - Stage 1: generate_intent(website) -- why is this consumer on the page?
    - Stage 4: react(ad, intent) -- how does the consumer respond to the winning ad?

    One Consumer instance is created per auction cycle and discarded after.

    Example:
        ```python
        consumer = Consumer(persona=persona)
        intent = consumer.generate_intent(website=website_ctx)
        reaction = consumer.react(ad=ad_info, intent=intent)
        ```
    """

    def __init__(
        self,
        persona: ConsumerPersona,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """Initialize the consumer agent with a persona.

        Args:
            persona: Consumer demographic profile from the database.
            model_id: Anthropic model ID to use. Defaults to Haiku.
            max_tokens: Maximum tokens for LLM responses.
        """
        self.persona = persona

        system_prompt = CONSUMER_SYSTEM_PROMPT.format(
            name=persona.name,
            age=persona.age,
            gender=persona.gender,
            income_level=persona.income_level.value,
            interests=", ".join(persona.interests),
            location=persona.location,
        )

        model = AnthropicModel(
            model_id=model_id,
            max_tokens=max_tokens,
        )

        self._agent = Agent(
            model=model,
            system_prompt=system_prompt,
            callback_handler=None,
        )

    def generate_intent(self, website: WebsiteContext) -> BrowsingIntent:
        """Generate a realistic browsing intent based on persona and website context.

        Uses the LLM to simulate why this consumer is currently on the page,
        what they are looking for, and their current mood.

        Args:
            website: The website/page context the consumer is browsing.

        Returns:
            BrowsingIntent with primary_intent, mood, and openness_to_ads.
        """
        logger.info(
            "consumer=%s | generating intent for website=%s",
            self.persona.name,
            website.name,
        )

        prompt = GENERATE_INTENT_PROMPT.format(
            website_name=website.name,
            website_category=website.category,
            page_context=website.page_context,
        )

        result = self._agent(prompt, structured_output_model=BrowsingIntent)
        intent = result.structured_output

        logger.info(
            "consumer=%s | intent=%s | mood=%s | openness=%d",
            self.persona.name,
            intent.primary_intent,
            intent.mood,
            intent.openness_to_ads,
        )
        return intent

    def react(self, ad: AdInfo, intent: BrowsingIntent) -> ConsumerReaction:
        """React to an advertisement based on persona and current intent.

        Evaluates the winning ad from the auction and produces a structured
        reaction including action (like/dislike/ignore), sentiment score,
        relevance score, and rationale.

        Args:
            ad: Information about the advertisement shown to the consumer.
            intent: The consumer's current browsing intent (from generate_intent).

        Returns:
            ConsumerReaction with action, sentiment_score, rationale,
            and relevance_score.
        """
        logger.info(
            "consumer=%s | reacting to ad from %s",
            self.persona.name,
            ad.advertiser_name,
        )

        prompt = REACT_TO_AD_PROMPT.format(
            intent=intent.primary_intent,
            mood=intent.mood,
            openness_to_ads=intent.openness_to_ads,
            advertiser_name=ad.advertiser_name,
            product_description=ad.product_description,
        )

        result = self._agent(prompt, structured_output_model=ConsumerReaction)
        reaction = result.structured_output

        logger.info(
            "consumer=%s | action=%s | sentiment=%.2f | relevance=%.2f",
            self.persona.name,
            reaction.action.value,
            reaction.sentiment_score,
            reaction.relevance_score,
        )
        return reaction


def map_action_to_db_feedback(action: ConsumerAction) -> str | None:
    """Map a ConsumerAction to the database feedback format.

    The `auctions.consumer_feedback` column stores "like"/"dislike"/null.
    The consumer agent outputs "like"/"dislike"/"ignore". This function
    bridges the two.

    Args:
        action: The consumer's action from the reaction.

    Returns:
        "like", "dislike", or None (for ignore).
    """
    if action == ConsumerAction.IGNORE:
        return None
    return action.value
