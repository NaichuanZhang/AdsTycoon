"""Strands tools for the Insights Agent."""

from strands import tool

from backend.models import Auction, Bid, Campaign

_db_session = None


def set_db_session(session):
    global _db_session
    _db_session = session


def _get_db():
    if _db_session is None:
        raise RuntimeError("DB session not set. Call set_db_session() first.")
    return _db_session


@tool
def get_campaign_auctions(campaign_id: str) -> str:
    """Get all auctions where this campaign participated.

    Args:
        campaign_id: The campaign UUID.

    Returns:
        Formatted string with auction history.
    """
    db = _get_db()
    bids = db.query(Bid).filter_by(campaign_id=campaign_id).all()

    if not bids:
        return f"No auction history for campaign {campaign_id}"

    lines = [f"Auction history for campaign {campaign_id} ({len(bids)} bids):"]
    for bid in bids:
        auction = db.query(Auction).filter_by(id=bid.auction_id).first()
        won = auction and auction.winning_campaign_id == campaign_id
        feedback = auction.consumer_feedback if auction else "N/A"
        lines.append(
            f"  - Auction {bid.auction_id}: bid ${bid.bid_amount:.2f}, "
            f"{'WON' if won else 'LOST'}, feedback: {feedback}"
        )

    return "\n".join(lines)


@tool
def get_campaign_stats(campaign_id: str) -> str:
    """Get aggregated stats for a campaign.

    Args:
        campaign_id: The campaign UUID.

    Returns:
        Formatted string with win rate, avg bid, feedback ratio.
    """
    db = _get_db()
    campaign = db.query(Campaign).filter_by(id=campaign_id).first()
    if not campaign:
        return f"Campaign {campaign_id} not found"

    bids = db.query(Bid).filter_by(campaign_id=campaign_id).all()
    total_bids = len(bids)

    if total_bids == 0:
        return (
            f"Campaign: {campaign.campaign_name}\n"
            f"No bids placed yet."
        )

    wins = 0
    likes = 0
    dislikes = 0
    total_bid_amount = 0.0

    for bid in bids:
        total_bid_amount += bid.bid_amount
        auction = db.query(Auction).filter_by(id=bid.auction_id).first()
        if auction and auction.winning_campaign_id == campaign_id:
            wins += 1
            if auction.consumer_feedback == "like":
                likes += 1
            elif auction.consumer_feedback == "dislike":
                dislikes += 1

    win_rate = (wins / total_bids * 100) if total_bids > 0 else 0
    avg_bid = total_bid_amount / total_bids if total_bids > 0 else 0
    budget_spent = campaign.total_budget - campaign.remaining_budget

    return (
        f"Campaign: {campaign.campaign_name}\n"
        f"Goal: {campaign.goal}\n"
        f"Total Bids: {total_bids}\n"
        f"Wins: {wins} ({win_rate:.1f}%)\n"
        f"Avg Bid: ${avg_bid:.2f}\n"
        f"Likes: {likes}, Dislikes: {dislikes}\n"
        f"Budget: ${budget_spent:.2f} spent of ${campaign.total_budget:.2f}"
    )
