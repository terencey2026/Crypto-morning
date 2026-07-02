"""
Web Generator - Save daily briefing as JSON for the web dashboard
=================================================================
Saves each day's briefing as a dated JSON file and maintains an
index.json for the frontend to enumerate available dates.
"""

import json
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import WEB_DATA_DIR, TIMEZONE


def save_daily_briefing(briefing: dict) -> str:
    """
    Save the daily briefing as a JSON file and update the index.

    Creates:
      - docs/data/YYYY-MM-DD.json  (daily snapshot)
      - docs/data/latest.json       (copy of today's data)
      - docs/data/index.json        (updated date index)

    Args:
        briefing: Full briefing data dict.

    Returns:
        Absolute path to the saved daily JSON file.
    """
    os.makedirs(WEB_DATA_DIR, exist_ok=True)

    date_str = briefing.get(
        "date",
        datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d"),
    )

    # ── Save daily file ──
    daily_path = os.path.join(WEB_DATA_DIR, f"{date_str}.json")
    _write_json(daily_path, briefing)
    logger.info(f"Saved daily briefing → {daily_path}")

    # ── Save as latest.json ──
    latest_path = os.path.join(WEB_DATA_DIR, "latest.json")
    _write_json(latest_path, briefing)

    # ── Update index.json ──
    _update_index(date_str)

    return daily_path


def _write_json(path: str, data: dict) -> None:
    """Write dict as formatted JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _update_index(new_date: str) -> None:
    """Add date to index.json and keep sorted reverse-chronologically."""
    index_path = os.path.join(WEB_DATA_DIR, "index.json")

    # Load existing index
    index = {"dates": [], "latest": ""}
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing index.json, creating new: {e}")
            index = {"dates": [], "latest": ""}

    # Add new date if not already present
    if new_date not in index.get("dates", []):
        index.setdefault("dates", []).insert(0, new_date)
        # Keep sorted reverse-chronologically
        index["dates"].sort(reverse=True)

    index["latest"] = new_date

    _write_json(index_path, index)
    logger.info(f"Updated index.json — total {len(index['dates'])} dates archived")
