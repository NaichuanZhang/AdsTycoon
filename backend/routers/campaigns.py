from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agents.insights import run_insights_agent
from backend.database import get_db
from backend.models import Auction, Bid, Campaign, Simulation
from backend.schemas import (
    CampaignDetailResponse,
    CampaignInsightsResponse,
    CampaignResponse,
    CampaignStats,
)

router = APIRouter(prefix="/api/simulations/{sim_id}/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return db.query(Campaign).filter_by(simulation_id=sim_id).all()


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign(sim_id: str, campaign_id: str, db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign)
        .filter_by(id=campaign_id, simulation_id=sim_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    stats = _compute_stats(db, campaign)
    return CampaignDetailResponse(
        id=campaign.id,
        campaign_name=campaign.campaign_name,
        product_description=campaign.product_description,
        creative=campaign.creative,
        goal=campaign.goal,
        total_budget=campaign.total_budget,
        remaining_budget=campaign.remaining_budget,
        stats=stats,
    )


@router.get("/{campaign_id}/insights", response_model=CampaignInsightsResponse)
def get_campaign_insights(sim_id: str, campaign_id: str, db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign)
        .filter_by(id=campaign_id, simulation_id=sim_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    result = run_insights_agent(campaign_id, db)
    return CampaignInsightsResponse(
        campaign_id=campaign_id,
        summary=result.get("summary", ""),
        suggestions=result.get("suggestions", []),
    )


def _compute_stats(db: Session, campaign: Campaign) -> CampaignStats:
    bids = db.query(Bid).filter_by(campaign_id=campaign.id).all()
    total_bids = len(bids)

    if total_bids == 0:
        return CampaignStats()

    wins = 0
    likes = 0
    dislikes = 0
    total_amount = 0.0

    for bid in bids:
        total_amount += bid.bid_amount
        auction = db.query(Auction).filter_by(id=bid.auction_id).first()
        if auction and auction.winning_campaign_id == campaign.id:
            wins += 1
            if auction.consumer_feedback == "like":
                likes += 1
            elif auction.consumer_feedback == "dislike":
                dislikes += 1

    return CampaignStats(
        total_bids=total_bids,
        wins=wins,
        losses=total_bids - wins,
        win_rate=(wins / total_bids * 100) if total_bids > 0 else 0,
        avg_bid=total_amount / total_bids,
        likes=likes,
        dislikes=dislikes,
        budget_spent=campaign.total_budget - campaign.remaining_budget,
    )
