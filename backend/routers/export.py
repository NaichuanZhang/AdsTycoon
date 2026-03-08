"""Export endpoints — Google Sheets via Composio."""

import logging

from composio import ComposioToolSet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.config import COMPOSIO_API_KEY, COMPOSIO_ENTITY_ID
from backend.database import get_db
from backend.models import Auction, Campaign, Simulation
from backend.services.sheets_export import export_to_sheets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simulations", tags=["export"])


@router.get("/export/google-sheets/status")
def google_sheets_status():
    """Check if a Google Sheets account is connected via Composio."""
    if not COMPOSIO_API_KEY:
        return {"connected": False, "reason": "COMPOSIO_API_KEY not configured"}

    try:
        toolset = ComposioToolSet(
            api_key=COMPOSIO_API_KEY, entity_id=COMPOSIO_ENTITY_ID,
        )
        connections = toolset.get_connected_accounts()
        active = any(
            getattr(c, "appName", "").upper() == "GOOGLESHEETS"
            and getattr(c, "status", "").upper() == "ACTIVE"
            for c in connections
        )
        return {"connected": active}
    except Exception:
        logger.exception("Failed to check Google Sheets connection status")
        return {"connected": False, "reason": "Failed to query Composio"}


@router.post("/{sim_id}/export/google-sheets")
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
