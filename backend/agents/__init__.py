import boto3
from strands.models.bedrock import BedrockModel

from backend.config import AWS_PROFILE, AWS_REGION, BEDROCK_MODEL_ID


def create_bedrock_model() -> BedrockModel:
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return BedrockModel(model_id=BEDROCK_MODEL_ID, boto_session=session)
