"""Seeding Agent — interprets a scenario prompt and generates simulation data."""

from strands import Agent

from backend.agents import create_bedrock_model
from backend.tools.seeder_tools import (
    create_campaigns,
    create_consumers,
    create_websites,
    set_db_session,
)

SYSTEM_PROMPT = """You are a simulation data generator for an advertising exchange.

Given a scenario description, you must create realistic, diverse data by calling the provided tools.

## Consumer Rules
- Create consumers with DIVERSE demographics — not all matching the target audience.
- Include off-target consumers (different ages, interests, locations) for realistic noise.

## Website Rules
- **Category diversity:** Pick 3-4 categories relevant to the scenario and distribute websites
  roughly evenly across them. Do NOT hardcode categories — derive them from the scenario.
  Some websites should match the campaign themes, others should be unrelated for realistic noise.
- **Website names:** Use realistic, diverse names similar to actual US-based websites
  (e.g., "Vogue", "Car and Driver", "Zillow", "TechCrunch", "ESPN"). Include a mix of
  well-known and lesser-known site names. Each name must be unique.
- **Page context:** Each website must have a realistic page context that logically aligns with
  its category (e.g., "article about summer fashion trends", "review of new electric cars",
  "guide to buying a home"). Page context describes the content the user is viewing,
  agnostic to potential ads.
- **Ad placement distribution:** Use "banner", "sidebar", and "interstitial" — distribute them
  roughly evenly across websites.

## Campaign Rules
- Create campaigns that follow the scenario's strategy requirements.
- If the scenario mentions "reach vs quality", create campaigns with both goals.

## General Rules
- All data should feel realistic — real-sounding names, plausible demographics, actual website names.
- You MUST call all three tools: create_consumers, create_websites, create_campaigns.
- Do NOT explain your reasoning at length. Just call the tools with the data.
"""


def run_seeder(
    simulation_id: str,
    scenario: str,
    num_consumers: int,
    num_websites: int,
    num_campaigns: int,
    db_session,
) -> None:
    set_db_session(db_session)

    model = create_bedrock_model()
    agent = Agent(
        model=model,
        tools=[create_consumers, create_websites, create_campaigns],
        system_prompt=SYSTEM_PROMPT,
    )

    prompt = (
        f"Simulation ID: {simulation_id}\n"
        f"Scenario: {scenario}\n"
        f"Generate exactly {num_consumers} consumers, {num_websites} websites, "
        f"and {num_campaigns} campaigns.\n"
        f"Call the tools now."
    )

    agent(prompt)
