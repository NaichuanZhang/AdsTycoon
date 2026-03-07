from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Auction, Simulation
from backend.schemas import AuctionListResponse, AuctionResponse, BidResponse, ConsumerResponse, WebsiteResponse

router = APIRouter(prefix="/api/simulations/{sim_id}/auctions", tags=["auctions"])


@router.get("", response_model=list[AuctionListResponse])
def list_auctions(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    auctions = (
        db.query(Auction)
        .filter_by(simulation_id=sim_id)
        .order_by(Auction.created_at.desc())
        .all()
    )
    return auctions


@router.get("/{auction_id}", response_model=AuctionResponse)
def get_auction(sim_id: str, auction_id: str, db: Session = Depends(get_db)):
    auction = (
        db.query(Auction)
        .filter_by(id=auction_id, simulation_id=sim_id)
        .first()
    )
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    return AuctionResponse(
        id=auction.id,
        consumer=ConsumerResponse.model_validate(auction.consumer),
        website=WebsiteResponse.model_validate(auction.website),
        winning_campaign_id=auction.winning_campaign_id,
        winning_bid=auction.winning_bid,
        consumer_feedback=auction.consumer_feedback,
        created_at=auction.created_at,
        bids=[
            BidResponse(
                id=b.id,
                campaign_id=b.campaign_id,
                campaign_name=b.campaign.campaign_name if b.campaign else "",
                bid_amount=b.bid_amount,
                reasoning=b.reasoning,
            )
            for b in auction.bids
        ],
    )
