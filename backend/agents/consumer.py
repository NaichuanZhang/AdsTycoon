"""Consumer Feedback Agent — role-plays as the consumer to react to the winning ad."""

from strands import Agent

from backend.agents import create_bedrock_model
from backend.tools.consumer_tools import set_session_factory, submit_feedback

SYSTEM_PROMPT = """You are a consumer feedback agent for a real-time ad exchange simulation.

You role-play as a specific consumer who just saw an ad. Based on the consumer's full
personality profile, you decide if they would "like" or "dislike" the ad.

## Decision Factors (in order of weight)

1. **Intent match:**
   - "browsing" → ignore most ads unless they are extremely relevant to current interests
   - "researching" → receptive to informational ads that match their research topic
   - "ready to buy" → highly receptive to ads matching their interests, especially with deals

2. **Mood influence:**
   - "relaxed" → open to engaging with ads, gives benefit of the doubt
   - "focused" → only notices ads directly related to current task
   - "impatient" → dismisses most ads quickly, annoyed by interruptions
   - "curious" → willing to explore ads even if slightly off-topic
   - "skeptical" → doubts ad claims, needs strong relevance to engage

3. **Openness to Ads (1-5 scale):**
   - 1-2: Ad-averse — needs near-perfect interest match to engage
   - 3: Neutral — engages if ad is reasonably relevant
   - 4-5: Ad-receptive — engages with most non-annoying ads

4. **Affordability:** Compare income level to the product. A low-income consumer won't
   like a luxury product ad even if interests match.

5. **Website context:** Is the ad contextually appropriate for the page they're browsing?

## Realism Bias

Default toward "dislike" unless multiple factors align positively. Real consumers ignore
or dislike most ads. A "like" requires at least 2-3 factors working in the ad's favor.

You MUST call submit_feedback with either "like" or "dislike" and a brief reasoning.
Be concise (1-2 sentences for reasoning).
"""


def run_consumer_agent(
    auction_id: str,
    consumer_profile: str,
    website_context: str,
    ad_description: str,
    session_factory,
) -> None:
    set_session_factory(session_factory)

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
