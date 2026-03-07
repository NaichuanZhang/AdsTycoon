import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine
from backend.exceptions import BidExchangeError, bid_exchange_error_handler
from backend.routers import auctions, campaigns, dashboard, simulations
from backend.routers import stream

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bid_exchange")


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Bid Exchange API started")
    yield


app = FastAPI(title="Bid Exchange", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(BidExchangeError, bid_exchange_error_handler)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(simulations.router)
app.include_router(auctions.router)
app.include_router(campaigns.router)
app.include_router(dashboard.router)
app.include_router(stream.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


# Static files mount MUST be last — it catches all unmatched routes
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
