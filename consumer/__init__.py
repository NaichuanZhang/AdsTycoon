"""Consumer agent module for the AdsTycoon simulation.

Provides the Consumer class and associated schemas for simulating
consumer behavior in the ad bidding auction loop.
"""

from .agent import Consumer, map_action_to_db_feedback
from .schemas import (
    AdInfo,
    BrowsingIntent,
    ConsumerAction,
    ConsumerPersona,
    ConsumerReaction,
    Gender,
    IncomeLevel,
    WebsiteContext,
)

__all__ = [
    "AdInfo",
    "BrowsingIntent",
    "Consumer",
    "ConsumerAction",
    "ConsumerPersona",
    "ConsumerReaction",
    "Gender",
    "IncomeLevel",
    "WebsiteContext",
    "map_action_to_db_feedback",
]
