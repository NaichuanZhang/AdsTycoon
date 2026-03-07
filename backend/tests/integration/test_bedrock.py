"""Integration test for Bedrock + Strands connectivity.

Requires AWS credentials via 'tokenmaster' profile.
Skip with: pytest -m 'not integration'
"""

import pytest

from backend.config import AWS_PROFILE, AWS_REGION, BEDROCK_MODEL_ID


@pytest.mark.integration
def test_bedrock_strands_agent_responds():
    """Verify Strands Agent + BedrockModel returns a response."""
    import boto3
    from strands import Agent
    from strands.models.bedrock import BedrockModel

    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        boto_session=session,
    )

    agent = Agent(
        model=model,
        system_prompt="You are a helpful assistant. Reply concisely.",
    )

    result = agent("Say hello in exactly 3 words.")
    response_text = str(result)

    assert len(response_text) > 0, "Agent returned an empty response"
