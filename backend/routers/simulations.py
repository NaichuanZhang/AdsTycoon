from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agents.seeder import run_seeder
from backend.database import get_db
from backend.models import Simulation
from backend.schemas import (
    AuctionListResponse,
    RunRequest,
    SimulationCreate,
    SimulationListResponse,
    SimulationResponse,
)
from backend.services.auction_engine import reset_simulation, run_auction_rounds

router = APIRouter(prefix="/api/simulations", tags=["simulations"])


@router.post("", response_model=SimulationResponse, status_code=201)
def create_simulation(payload: SimulationCreate, db: Session = Depends(get_db)):
    sim = Simulation(
        scenario=payload.scenario,
        status="created",
        num_consumers=payload.num_consumers,
        num_websites=payload.num_websites,
        num_campaigns=payload.num_campaigns,
        num_rounds=payload.num_rounds,
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return _sim_to_response(sim)


@router.post("/{sim_id}/seed", response_model=SimulationResponse)
def seed_simulation(sim_id: str, db: Session = Depends(get_db)):
    """Trigger seeding synchronously (non-streaming fallback)."""
    sim = _get_sim_or_404(sim_id, db)

    run_seeder(
        simulation_id=sim.id,
        scenario=sim.scenario,
        num_consumers=sim.num_consumers,
        num_websites=sim.num_websites,
        num_campaigns=sim.num_campaigns,
        num_rounds=sim.num_rounds,
        db_session=db,
    )

    sim.status = "seeded"
    db.commit()
    db.refresh(sim)
    return _sim_to_response(sim)


@router.get("", response_model=list[SimulationListResponse])
def list_simulations(db: Session = Depends(get_db)):
    sims = db.query(Simulation).order_by(Simulation.created_at.desc()).all()
    return sims


@router.get("/{sim_id}", response_model=SimulationResponse)
def get_simulation(sim_id: str, db: Session = Depends(get_db)):
    sim = _get_sim_or_404(sim_id, db)
    return _sim_to_response(sim)


def _get_sim_or_404(sim_id: str, db: Session) -> Simulation:
    sim = db.query(Simulation).filter(Simulation.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


@router.post("/{sim_id}/run", response_model=list[AuctionListResponse])
def run_simulation(sim_id: str, payload: RunRequest = RunRequest(), db: Session = Depends(get_db)):
    sim = _get_sim_or_404(sim_id, db)
    sim.status = "running"
    db.commit()

    auctions = run_auction_rounds(db, sim_id, payload.rounds)

    sim.status = "completed"
    db.commit()

    return auctions


@router.post("/{sim_id}/reset", status_code=200)
def reset_sim(sim_id: str, db: Session = Depends(get_db)):
    sim = _get_sim_or_404(sim_id, db)
    reset_simulation(db, sim_id)
    sim.status = "seeded"
    db.commit()
    return {"message": "Simulation reset successfully"}


def _sim_to_response(sim: Simulation) -> SimulationResponse:
    return SimulationResponse(
        id=sim.id,
        scenario=sim.scenario,
        status=sim.status,
        created_at=sim.created_at,
        num_rounds=sim.num_rounds,
        consumer_count=len(sim.consumers),
        website_count=len(sim.websites),
        campaign_count=len(sim.campaigns),
        auction_count=len(sim.auctions),
    )
