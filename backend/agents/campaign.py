"""Campaign Agent — decides whether/how much to bid on an impression."""

from strands import Agent

from backend.agents import create_bedrock_model
from backend.tools.campaign_tools import get_campaign, set_db_session, submit_bid

SYSTEM_PROMPT = """You are a campaign bidding agent for a real-time ad exchange.

You represent ONE advertising campaign. For each auction, you decide whether to bid and how much.

Your behavior depends on the campaign's goal:
- "reach" goal: Bid on most impressions. Bid LOW to stretch your budget across many impressions.
  Typical bids: $0.50 - $3.00. Skip only if the audience is completely irrelevant.
- "quality" goal: Bid SELECTIVELY. Only bid on high-relevance impressions. Bid HIGHER when you do.
  Typical bids: $3.00 - $15.00. Skip if the consumer doesn't match your target well.

Process:
1. First call get_campaign to check your remaining budget and campaign details.
2. Analyze the consumer profile and website context.
3. If you decide to bid, call submit_bid with your bid amount and reasoning.
4. If you decide NOT to bid, just say "SKIP" and explain why.

Rules:
- NEVER bid more than your remaining budget.
- Keep bids realistic ($0.50 - $20.00 range).
- Be concise in your reasoning (1-2 sentences).
"""


def run_campaign_agent(
    campaign_id: str,
    auction_id: str,
    consumer_profile: str,
    website_context: str,
    db_session,
) -> None:
    set_db_session(db_session)

    model = create_bedrock_model()
    agent = Agent(
        model=model,
        tools=[get_campaign, submit_bid],
        system_prompt=SYSTEM_PROMPT,
    )

    prompt = (
        f"Campaign ID: {campaign_id}\n"
        f"Auction ID: {auction_id}\n\n"
        f"Consumer Profile:\n{consumer_profile}\n\n"
        f"Website Context:\n{website_context}\n\n"
        f"Decide whether to bid and how much. Call the tools now."
    )

    agent(prompt)
