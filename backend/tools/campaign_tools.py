"""Strands tools for the Campaign Agent."""

import logging
import uuid

from strands import tool

from backend.models import Bid, Campaign

logger = logging.getLogger("bid_exchange.campaign_tools")

_db_session = None


def set_db_session(session):
    global _db_session
    _db_session = session


def _get_db():
    if _db_session is None:
        raise RuntimeError("DB session not set. Call set_db_session() first.")
    return _db_session


@tool
def get_campaign(campaign_id: str) -> str:
    """Get campaign details including remaining budget.

    Args:
        campaign_id: The campaign UUID.

    Returns:
        Campaign details as a formatted string.
    """
    db = _get_db()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return f"Campaign {campaign_id} not found"

    return (
        f"Campaign: {campaign.campaign_name}\n"
        f"Product: {campaign.product_description}\n"
        f"Creative: {campaign.creative}\n"
        f"Goal: {campaign.goal}\n"
        f"Total Budget: ${campaign.total_budget:.2f}\n"
        f"Remaining Budget: ${campaign.remaining_budget:.2f}"
    )


@tool
def submit_bid(auction_id: str, campaign_id: str, bid_amount: float, reasoning: str) -> str:
    """Place a bid on an auction for a campaign.

    Args:
        auction_id: The auction UUID.
        campaign_id: The campaign UUID.
        bid_amount: The dollar amount to bid. Must not exceed remaining budget.
        reasoning: Explanation for the bid decision.

    Returns:
        Confirmation or rejection message.
    """
    db = _get_db()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return f"Campaign {campaign_id} not found"

    if bid_amount <= 0:
        return f"Bid amount must be positive. Got: {bid_amount}"

    if bid_amount > campaign.remaining_budget:
        return (
            f"Bid ${bid_amount:.2f} exceeds remaining budget "
            f"${campaign.remaining_budget:.2f}. Bid rejected."
        )

    bid = Bid(
        id=str(uuid.uuid4()),
        auction_id=auction_id,
        campaign_id=campaign_id,
        bid_amount=bid_amount,
        reasoning=reasoning,
    )
    try:
        db.add(bid)
        db.commit()
    except Exception as e:
        logger.exception("Failed to submit bid")
        db.rollback()
        return f"Error submitting bid: {e}"

    return f"Bid of ${bid_amount:.2f} placed for campaign {campaign.campaign_name}"
