"""
Integration tests for Composio Google Sheets export.

Requires COMPOSIO_API_KEY env var and a connected Google Sheets account.
Run with: uv run pytest -m integration -k composio -v
"""

import os

import pytest

from backend.services.sheets_export import export_to_sheets


@pytest.mark.integration
class TestComposioGoogleSheets:
    """Validate Composio connectivity and Google Sheets operations."""

    def test_export_creates_spreadsheet_with_data(self):
        """Create a test spreadsheet via Composio and verify the response."""
        if not os.getenv("COMPOSIO_API_KEY"):
            pytest.skip("COMPOSIO_API_KEY not set")

        title = "AdsTycoon Integration Test"
        rows = [
            {
                "Campaign": "Test Campaign A",
                "Goal": "reach",
                "Total Budget": 1000.0,
                "Remaining Budget": 250.0,
                "Budget Spent": 750.0,
            },
            {
                "Campaign": "Test Campaign B",
                "Goal": "quality",
                "Total Budget": 500.0,
                "Remaining Budget": 100.0,
                "Budget Spent": 400.0,
            },
        ]

        result = export_to_sheets(title, rows)

        assert result["spreadsheet_id"], "Expected a spreadsheet_id in response"
        assert result["spreadsheet_url"], "Expected a spreadsheet_url in response"
        assert "docs.google.com/spreadsheets" in result["spreadsheet_url"]
