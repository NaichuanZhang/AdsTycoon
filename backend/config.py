import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bid_exchange.db")

AWS_PROFILE = os.getenv("AWS_PROFILE", "tokenmaster")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
)
