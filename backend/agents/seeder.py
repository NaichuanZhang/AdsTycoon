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

Rules:
1. Create consumers with DIVERSE demographics — not all matching the target audience.
   Include off-target consumers (different ages, interests, locations) for realistic noise.
2. Create websites with a MIX of relevant and irrelevant contexts.
   Some should match the campaign themes, others should be unrelated.
3. Create campaigns that follow the scenario's strategy requirements.
   If the scenario mentions "reach vs quality", create campaigns with both goals.
4. All data should feel realistic — real-sounding names, plausible demographics, actual website names.
5. You MUST call all three tools: create_consumers, create_websites, create_campaigns.
6. Do NOT explain your reasoning at length. Just call the tools with the data.
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
