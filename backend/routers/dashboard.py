from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Auction, Bid, Campaign, Simulation
from backend.schemas import CampaignResponse, DashboardResponse

router = APIRouter(prefix="/api/simulations/{sim_id}/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    auctions = db.query(Auction).filter_by(simulation_id=sim_id).all()
    total_auctions = len(auctions)

    total_bids = db.query(Bid).join(Auction).filter(Auction.simulation_id == sim_id).count()

    winning_auctions = [a for a in auctions if a.winning_bid is not None]
    avg_winning_bid = (
        sum(a.winning_bid for a in winning_auctions) / len(winning_auctions)
        if winning_auctions
        else 0.0
    )

    likes = sum(1 for a in auctions if a.consumer_feedback == "like")
    dislikes = sum(1 for a in auctions if a.consumer_feedback == "dislike")
    feedback_total = likes + dislikes
    like_ratio = (likes / feedback_total * 100) if feedback_total > 0 else 0.0

    campaigns = db.query(Campaign).filter_by(simulation_id=sim_id).all()
    total_budget_spent = sum(c.total_budget - c.remaining_budget for c in campaigns)

    return DashboardResponse(
        total_auctions=total_auctions,
        total_bids=total_bids,
        avg_winning_bid=avg_winning_bid,
        likes=likes,
        dislikes=dislikes,
        like_ratio=like_ratio,
        total_budget_spent=total_budget_spent,
        campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
    )
