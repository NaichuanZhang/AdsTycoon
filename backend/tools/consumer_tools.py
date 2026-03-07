"""Strands tools for the Consumer Feedback Agent."""

import logging

from strands import tool

from backend.models import Auction

logger = logging.getLogger("bid_exchange.consumer_tools")

_db_session = None


def set_db_session(session):
    global _db_session
    _db_session = session


def _get_db():
    if _db_session is None:
        raise RuntimeError("DB session not set. Call set_db_session() first.")
    return _db_session


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
    db = _get_db()

    if feedback not in ("like", "dislike"):
        return f"Invalid feedback '{feedback}'. Must be 'like' or 'dislike'."

    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        return f"Auction {auction_id} not found"

    try:
        auction.consumer_feedback = feedback
        db.commit()
    except Exception as e:
        logger.exception("Failed to submit feedback")
        db.rollback()
        return f"Error submitting feedback: {e}"

    return f"Feedback '{feedback}' recorded for auction {auction_id}. Reason: {reasoning}"
