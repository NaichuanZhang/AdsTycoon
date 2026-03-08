"""Insights Agent — analyzes campaign performance and generates suggestions."""

import json

from strands import Agent

from backend.agents import create_bedrock_model
from backend.tools.insights_tools import (
    get_campaign_auctions,
    get_campaign_stats,
    set_session_factory,
)

SYSTEM_PROMPT = """You are a campaign performance analyst for an advertising exchange.

Analyze a campaign's auction history and stats, then provide insights.

Process:
1. Call get_campaign_stats to get aggregated metrics.
2. Call get_campaign_auctions to see detailed auction history.
3. Generate a concise summary and 2-4 actionable suggestions.

Your final response MUST be valid JSON with this exact format:
{
  "summary": "Brief performance summary (2-3 sentences)",
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}

Be specific and actionable in your suggestions. Reference actual numbers from the stats.
"""


def run_insights_agent(campaign_id: str, session_factory) -> dict:
    set_session_factory(session_factory)

    model = create_bedrock_model()
    agent = Agent(
        model=model,
        tools=[get_campaign_auctions, get_campaign_stats],
        system_prompt=SYSTEM_PROMPT,
    )

    result = agent(f"Analyze campaign {campaign_id} and return JSON insights.")
    response_text = str(result)

    try:
        start = response_text.index("{")
        end = response_text.rindex("}") + 1
        return json.loads(response_text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {
            "summary": response_text[:500],
            "suggestions": ["Unable to parse structured insights. Raw response provided."],
        }
