"""
Google Sheets export via Composio.

Uses GOOGLESHEETS_SHEET_FROM_JSON to create a spreadsheet and populate it
with campaign data in a single API call.
"""

import logging

from composio import ComposioToolSet

from backend.config import COMPOSIO_API_KEY, COMPOSIO_ENTITY_ID

logger = logging.getLogger(__name__)


def export_to_sheets(
    title: str, rows: list[dict],
) -> dict[str, str]:
    """Create a Google Sheet and populate it with rows.

    Args:
        title: Spreadsheet title.
        rows: List of dicts — keys become column headers.

    Returns:
        {"spreadsheet_id": ..., "spreadsheet_url": ...}

    Raises:
        RuntimeError: If Composio action fails.
    """
    toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY, entity_id=COMPOSIO_ENTITY_ID)

    response = toolset.execute_action(
        action="GOOGLESHEETS_SHEET_FROM_JSON",
        params={
            "title": title,
            "sheet_name": "Campaign Results",
            "sheet_json": rows,
        },
    )

    if not response.get("successful", False):
        error_msg = response.get("error", "Unknown Composio error")
        logger.error("Sheets export failed: %s", error_msg)
        raise RuntimeError(f"Google Sheets export failed: {error_msg}")

    data = response.get("data", {})
    spreadsheet_id = data.get("spreadsheetId", "")
    spreadsheet_url = data.get(
        "spreadsheetUrl",
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}" if spreadsheet_id else "",
    )

    logger.info("Exported to Google Sheet: %s", spreadsheet_url)
    return {"spreadsheet_id": spreadsheet_id, "spreadsheet_url": spreadsheet_url}
