from datetime import datetime

from pydantic import BaseModel, Field


# --- Simulation ---


class SimulationCreate(BaseModel):
    scenario: str = Field(..., min_length=1)
    num_consumers: int = Field(default=20, ge=1, le=100)
    num_websites: int = Field(default=10, ge=1, le=50)
    num_campaigns: int = Field(default=4, ge=1, le=20)
    num_rounds: int = Field(default=3, ge=1, le=50)


class SimulationResponse(BaseModel):
    id: str
    scenario: str
    status: str
    created_at: datetime
    num_rounds: int = 3
    consumer_count: int = 0
    website_count: int = 0
    campaign_count: int = 0
    auction_count: int = 0

    model_config = {"from_attributes": True}


class SimulationListResponse(BaseModel):
    id: str
    scenario: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Run ---


class RunRequest(BaseModel):
    rounds: int = Field(default=1, ge=1, le=100)


# --- Consumer ---


class ConsumerResponse(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    income_level: str
    interests: list[str]
    intent: str
    mood: str
    openness_to_ads: int
    location: str

    model_config = {"from_attributes": True}


# --- Website ---


class WebsiteResponse(BaseModel):
    id: str
    name: str
    page_context: str
    ad_placement: str
    category: str

    model_config = {"from_attributes": True}


# --- Campaign ---


class CampaignResponse(BaseModel):
    id: str
    campaign_name: str
    product_description: str
    creative: str
    goal: str
    total_budget: float
    remaining_budget: float

    model_config = {"from_attributes": True}


class CampaignStats(BaseModel):
    total_bids: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_bid: float = 0.0
    likes: int = 0
    dislikes: int = 0
    budget_spent: float = 0.0


class CampaignDetailResponse(CampaignResponse):
    stats: CampaignStats = CampaignStats()


class CampaignInsightsResponse(BaseModel):
    campaign_id: str
    summary: str
    suggestions: list[str]


# --- Bid ---


class BidResponse(BaseModel):
    id: str
    campaign_id: str
    campaign_name: str = ""
    bid_amount: float
    reasoning: str

    model_config = {"from_attributes": True}


# --- Auction ---


class AuctionResponse(BaseModel):
    id: str
    consumer: ConsumerResponse
    website: WebsiteResponse
    winning_campaign_id: str | None = None
    winning_bid: float | None = None
    consumer_feedback: str | None = None
    created_at: datetime
    bids: list[BidResponse] = []

    model_config = {"from_attributes": True}


class AuctionListResponse(BaseModel):
    id: str
    winning_campaign_id: str | None = None
    winning_bid: float | None = None
    consumer_feedback: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Dashboard ---


class DashboardResponse(BaseModel):
    total_auctions: int = 0
    total_bids: int = 0
    avg_winning_bid: float = 0.0
    likes: int = 0
    dislikes: int = 0
    like_ratio: float = 0.0
    total_budget_spent: float = 0.0
    campaigns: list[CampaignResponse] = []
