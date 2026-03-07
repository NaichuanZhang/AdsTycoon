import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    scenario: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="created")
    num_consumers: Mapped[int] = mapped_column(Integer, default=20)
    num_websites: Mapped[int] = mapped_column(Integer, default=10)
    num_campaigns: Mapped[int] = mapped_column(Integer, default=4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    consumers: Mapped[list["Consumer"]] = relationship(back_populates="simulation")
    websites: Mapped[list["Website"]] = relationship(back_populates="simulation")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="simulation")
    auctions: Mapped[list["Auction"]] = relationship(back_populates="simulation")


class Consumer(Base):
    __tablename__ = "consumers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    income_level: Mapped[str] = mapped_column(String, nullable=False)
    interests: Mapped[list] = mapped_column(JSON, nullable=False)
    intent: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)

    simulation: Mapped["Simulation"] = relationship(back_populates="consumers")


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    page_context: Mapped[str] = mapped_column(String, nullable=False)
    ad_placement: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

    simulation: Mapped["Simulation"] = relationship(back_populates="websites")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id"), nullable=False)
    campaign_name: Mapped[str] = mapped_column(String, nullable=False)
    product_description: Mapped[str] = mapped_column(String, nullable=False)
    goal: Mapped[str] = mapped_column(String, nullable=False)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False)
    remaining_budget: Mapped[float] = mapped_column(Float, nullable=False)

    simulation: Mapped["Simulation"] = relationship(back_populates="campaigns")
    bids: Mapped[list["Bid"]] = relationship(back_populates="campaign")


class Auction(Base):
    __tablename__ = "auctions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulations.id"), nullable=False)
    consumer_id: Mapped[str] = mapped_column(ForeignKey("consumers.id"), nullable=False)
    website_id: Mapped[str] = mapped_column(ForeignKey("websites.id"), nullable=False)
    winning_campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True
    )
    winning_bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    consumer_feedback: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    simulation: Mapped["Simulation"] = relationship(back_populates="auctions")
    consumer: Mapped["Consumer"] = relationship()
    website: Mapped["Website"] = relationship()
    winning_campaign: Mapped["Campaign | None"] = relationship()
    bids: Mapped[list["Bid"]] = relationship(back_populates="auction")


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    auction_id: Mapped[str] = mapped_column(ForeignKey("auctions.id"), nullable=False)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), nullable=False)
    bid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(String, nullable=False)

    auction: Mapped["Auction"] = relationship(back_populates="bids")
    campaign: Mapped["Campaign"] = relationship()
