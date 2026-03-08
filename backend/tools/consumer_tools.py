"""Strands tools for the Consumer Feedback Agent.

A session factory is set via set_session_factory() before each agent invocation.
Each tool creates its own session to avoid corruption from parallel tool calls.
"""

import logging

from strands import tool

from backend.models import Auction

logger = logging.getLogger("bid_exchange.consumer_tools")

_session_factory = None


def set_session_factory(factory):
    global _session_factory
    _session_factory = factory


def _new_db():
    if _session_factory is None:
        raise RuntimeError("Session factory not set. Call set_session_factory() first.")
    return _session_factory()


@tool
def submit_feedback(auction_id: str, feedback: str, reasoning: str) -> str:
    """Submit consumer feedback for a won auction.

    Args:
        auction_id: The auction UUID.
        feedback: Either "like" or "dislike".
        reasoning: Explanation for the feedback.

    Returns:
        Confirmation message.
    """
    db = _new_db()
    try:
        if feedback not in ("like", "dislike"):
            return f"Invalid feedback '{feedback}'. Must be 'like' or 'dislike'."

        auction = db.query(Auction).filter(Auction.id == auction_id).first()
        if not auction:
            return f"Auction {auction_id} not found"

        auction.consumer_feedback = feedback
        db.commit()
        return f"Feedback '{feedback}' recorded for auction {auction_id}. Reason: {reasoning}"
    except Exception as e:
        logger.exception("Failed to submit feedback")
        db.rollback()
        return f"Error submitting feedback: {e}"
    finally:
        db.close()
