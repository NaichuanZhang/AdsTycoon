"""
Connect Google Sheets via Composio OAuth.

The `composio add googlesheets` CLI uses deprecated v2 endpoints.
This script uses the Python SDK's initiate_connection() which hits v3 and works.

Usage:
    uv run python scripts/connect_sheets.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    api_key = os.getenv("COMPOSIO_API_KEY", "")
    entity_id = os.getenv("COMPOSIO_ENTITY_ID", "default")

    if not api_key:
        print("Error: COMPOSIO_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    # Import here so missing dep gives a clear error, not an import traceback
    from composio import ComposioToolSet

    toolset = ComposioToolSet(api_key=api_key, entity_id=entity_id)

    print("Initiating Google Sheets OAuth connection...")
    result = toolset.initiate_connection(app="GOOGLESHEETS")

    redirect_url = result.redirectUrl
    if not redirect_url:
        print("Error: No redirect URL returned. Connection may already exist.")
        sys.exit(1)

    print(f"\nOpen this URL to connect Google Sheets:\n\n  {redirect_url}\n")
    print("Waiting for authorization (timeout: 120s)...")

    result.wait_until_active(timeout=120)
    print("Connected! Google Sheets is now linked to your Composio account.")


if __name__ == "__main__":
    main()
