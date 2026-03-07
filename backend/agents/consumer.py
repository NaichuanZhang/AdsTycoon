"""Consumer Feedback Agent — role-plays as the consumer to react to the winning ad."""

from strands import Agent

from backend.agents import create_bedrock_model
from backend.tools.consumer_tools import set_db_session, submit_feedback

SYSTEM_PROMPT = """You are a consumer feedback agent for a real-time ad exchange simulation.

You role-play as a specific consumer who just saw an ad. Based on the consumer's persona,
interests, intent, and the ad shown, you decide if they would "like" or "dislike" the ad.

Consider:
- Does the ad match the consumer's interests?
- Is the ad relevant to the website context they're browsing?
- Does the consumer's intent (browsing/researching/ready to buy) make them receptive?
- Would a real person with this demographic find the ad appealing or annoying?

You MUST call submit_feedback with either "like" or "dislike" and a brief reasoning.
Be concise (1-2 sentences for reasoning).
"""


def run_consumer_agent(
    auction_id: str,
    consumer_profile: str,
    website_context: str,
    ad_description: str,
    db_session,
) -> None:
    set_db_session(db_session)

    model = create_bedrock_model()
    agent = Agent(
        model=model,
        tools=[submit_feedback],
        system_prompt=SYSTEM_PROMPT,
    )

    prompt = (
        f"Auction ID: {auction_id}\n\n"
        f"You are this consumer:\n{consumer_profile}\n\n"
        f"You are browsing:\n{website_context}\n\n"
        f"You were shown this ad:\n{ad_description}\n\n"
        f"React to this ad. Call submit_feedback now."
    )

    agent(prompt)
