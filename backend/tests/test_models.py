from sqlalchemy.orm import Session

from backend.models import Auction, Bid, Campaign, Consumer, Simulation, Website


def _make_simulation(db: Session, scenario: str = "test scenario") -> Simulation:
    sim = Simulation(scenario=scenario)
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


def _make_consumer(db: Session, sim_id: str) -> Consumer:
    c = Consumer(
        simulation_id=sim_id,
        name="Alice",
        age=25,
        gender="female",
        income_level="medium",
        interests=["tech", "sports"],
        intent="browsing",
        mood="curious",
        openness_to_ads=4,
        location="NYC",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_website(db: Session, sim_id: str) -> Website:
    w = Website(
        simulation_id=sim_id,
        name="TechCrunch",
        page_context="article about AI",
        ad_placement="banner",
        category="tech",
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def _make_campaign(db: Session, sim_id: str) -> Campaign:
    camp = Campaign(
        simulation_id=sim_id,
        campaign_name="Nike Reach",
        product_description="Running shoes ad",
        creative="Every finish line starts with a single step — lace up",
        goal="reach",
        total_budget=1000.0,
        remaining_budget=1000.0,
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)
    return camp


class TestSimulationModel:
    def test_create_simulation(self, db_session: Session):
        sim = _make_simulation(db_session)
        assert sim.id is not None
        assert sim.scenario == "test scenario"
        assert sim.status == "created"
        assert sim.created_at is not None

    def test_simulation_query(self, db_session: Session):
        _make_simulation(db_session, "scenario A")
        _make_simulation(db_session, "scenario B")
        sims = db_session.query(Simulation).all()
        assert len(sims) == 2

    def test_simulation_default_num_rounds(self, db_session: Session):
        sim = _make_simulation(db_session)
        assert sim.num_rounds == 3

    def test_simulation_custom_num_rounds(self, db_session: Session):
        sim = Simulation(scenario="test", num_rounds=10)
        db_session.add(sim)
        db_session.commit()
        db_session.refresh(sim)
        assert sim.num_rounds == 10


class TestConsumerModel:
    def test_create_consumer(self, db_session: Session):
        sim = _make_simulation(db_session)
        c = _make_consumer(db_session, sim.id)
        assert c.id is not None
        assert c.simulation_id == sim.id
        assert c.interests == ["tech", "sports"]
        assert c.mood == "curious"
        assert c.openness_to_ads == 4

    def test_consumer_defaults(self, db_session: Session):
        sim = _make_simulation(db_session)
        c = Consumer(
            simulation_id=sim.id,
            name="Default User",
            age=30,
            gender="male",
            income_level="medium",
            interests=["reading"],
            intent="browsing",
            location="Chicago",
        )
        db_session.add(c)
        db_session.commit()
        db_session.refresh(c)
        assert c.mood == "neutral"
        assert c.openness_to_ads == 3

    def test_consumer_relationship(self, db_session: Session):
        sim = _make_simulation(db_session)
        _make_consumer(db_session, sim.id)
        db_session.refresh(sim)
        assert len(sim.consumers) == 1
        assert sim.consumers[0].name == "Alice"


class TestWebsiteModel:
    def test_create_website(self, db_session: Session):
        sim = _make_simulation(db_session)
        w = _make_website(db_session, sim.id)
        assert w.id is not None
        assert w.category == "tech"

    def test_website_relationship(self, db_session: Session):
        sim = _make_simulation(db_session)
        _make_website(db_session, sim.id)
        db_session.refresh(sim)
        assert len(sim.websites) == 1


class TestCampaignModel:
    def test_create_campaign(self, db_session: Session):
        sim = _make_simulation(db_session)
        camp = _make_campaign(db_session, sim.id)
        assert camp.id is not None
        assert camp.remaining_budget == 1000.0

    def test_campaign_relationship(self, db_session: Session):
        sim = _make_simulation(db_session)
        _make_campaign(db_session, sim.id)
        db_session.refresh(sim)
        assert len(sim.campaigns) == 1


class TestAuctionAndBidModels:
    def test_create_auction_with_bids(self, db_session: Session):
        sim = _make_simulation(db_session)
        consumer = _make_consumer(db_session, sim.id)
        website = _make_website(db_session, sim.id)
        campaign = _make_campaign(db_session, sim.id)

        auction = Auction(
            simulation_id=sim.id,
            consumer_id=consumer.id,
            website_id=website.id,
            winning_campaign_id=campaign.id,
            winning_bid=5.50,
            consumer_feedback="like",
        )
        db_session.add(auction)
        db_session.commit()
        db_session.refresh(auction)

        assert auction.id is not None
        assert auction.winning_bid == 5.50
        assert auction.consumer is not None
        assert auction.website is not None

        bid = Bid(
            auction_id=auction.id,
            campaign_id=campaign.id,
            bid_amount=5.50,
            reasoning="Good match for target audience",
        )
        db_session.add(bid)
        db_session.commit()
        db_session.refresh(auction)

        assert len(auction.bids) == 1
        assert auction.bids[0].bid_amount == 5.50

    def test_auction_null_winner(self, db_session: Session):
        sim = _make_simulation(db_session)
        consumer = _make_consumer(db_session, sim.id)
        website = _make_website(db_session, sim.id)

        auction = Auction(
            simulation_id=sim.id,
            consumer_id=consumer.id,
            website_id=website.id,
        )
        db_session.add(auction)
        db_session.commit()
        db_session.refresh(auction)

        assert auction.winning_campaign_id is None
        assert auction.winning_bid is None
        assert auction.consumer_feedback is None
