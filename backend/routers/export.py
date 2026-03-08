"""Export endpoints — Google Sheets via Composio."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Auction, Campaign, Simulation
from backend.services.sheets_export import export_to_sheets

router = APIRouter(prefix="/api/simulations/{sim_id}/export", tags=["export"])


@router.post("/google-sheets")
def export_google_sheets(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    campaigns = db.query(Campaign).filter_by(simulation_id=sim_id).all()
    if not campaigns:
        raise HTTPException(status_code=400, detail="No campaigns to export")

    rows = []
    for camp in campaigns:
        wins = (
            db.query(Auction)
            .filter_by(simulation_id=sim_id, winning_campaign_id=camp.id)
            .count()
        )
        likes = (
            db.query(Auction)
            .filter_by(
                simulation_id=sim_id,
                winning_campaign_id=camp.id,
                consumer_feedback="like",
            )
            .count()
        )
        spent = camp.total_budget - camp.remaining_budget
        rows.append({
            "Campaign": camp.campaign_name,
            "Goal": camp.goal,
            "Total Budget": round(camp.total_budget, 2),
            "Budget Spent": round(spent, 2),
            "Remaining Budget": round(camp.remaining_budget, 2),
            "Wins": wins,
            "Likes": likes,
        })

    try:
        result = export_to_sheets(
            title=f"AdsTycoon — {sim.scenario}",
            rows=rows,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return result
