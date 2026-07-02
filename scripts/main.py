"""
Crypto Morning Briefing - Main Orchestrator
============================================
Runs the full pipeline:
  1. Fetch crypto prices (CoinGecko)
  2. Fetch stock prices (Yahoo Finance)
  3. Fetch news (CryptoPanic)
  4. AI analysis (Gemini + Google Search)
  5. Push to Feishu
  6. Save for web dashboard

Usage:
    python scripts/main.py
"""

import logging
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Ensure scripts directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TIMEZONE
from data_fetcher import fetch_crypto_prices, fetch_stock_prices
from news_fetcher import fetch_crypto_news
from ai_analyzer import generate_analysis
from feishu_sender import send_briefing
from web_generator import save_daily_briefing

# ── Logging Setup ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("crypto-briefing")


def main() -> int:
    """Run the full morning briefing pipeline. Returns 0 on success, 1 on critical failure."""

    now = datetime.now(ZoneInfo(TIMEZONE))
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    logger.info("=" * 60)
    logger.info("  Crypto Morning Briefing Pipeline")
    logger.info(f"  {now.strftime('%Y-%m-%d %H:%M:%S')} ({weekday_names[now.weekday()]})")
    logger.info("=" * 60)

    errors = []

    # ── Step 1: Fetch Crypto Prices ──────────────────────────────────────
    logger.info("[1/6] Fetching crypto prices from CoinGecko...")
    try:
        crypto_data = fetch_crypto_prices()
    except Exception as e:
        logger.error(f"Crypto fetch crashed: {e}")
        crypto_data = []
        errors.append("crypto_fetch")
    logger.info(f"       → {len(crypto_data)} tokens")

    # ── Step 2: Fetch Stock Prices ───────────────────────────────────────
    logger.info("[2/6] Fetching stock prices from Yahoo Finance...")
    try:
        stock_data = fetch_stock_prices()
    except Exception as e:
        logger.error(f"Stock fetch crashed: {e}")
        stock_data = {"primary": [], "secondary_alerts": []}
        errors.append("stock_fetch")
    logger.info(
        f"       → {len(stock_data.get('primary', []))} primary, "
        f"{len(stock_data.get('secondary_alerts', []))} secondary alerts"
    )

    # ── Step 3: Fetch News ───────────────────────────────────────────────
    logger.info("[3/6] Fetching crypto news from CryptoPanic...")
    try:
        news_data = fetch_crypto_news()
    except Exception as e:
        logger.error(f"News fetch crashed: {e}")
        news_data = []
        errors.append("news_fetch")
    logger.info(f"       → {len(news_data)} news items")

    # ── Step 4: AI Analysis ──────────────────────────────────────────────
    logger.info("[4/6] Running AI analysis (Gemini + Google Search)...")
    try:
        analysis = generate_analysis(crypto_data, stock_data, news_data)
    except Exception as e:
        logger.error(f"AI analysis crashed: {e}")
        analysis = {
            "etf_summary": "分析引擎异常",
            "viewpoints": [],
            "risk_alerts": [f"AI分析失败: {e}"],
            "supplementary_news": [],
            "grounding_sources": [],
        }
        errors.append("ai_analysis")
    logger.info(f"       → {len(analysis.get('viewpoints', []))} viewpoints generated")

    # ── Step 5: Assemble Briefing ────────────────────────────────────────
    logger.info("[5/6] Assembling and delivering briefing...")

    briefing = {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": weekday_names[now.weekday()],
        "generated_at": now.isoformat(),
        "is_weekend_recap": now.weekday() == 0,  # Monday
        "market_data": {
            "crypto": crypto_data,
            "stocks": stock_data,
        },
        "news": analysis.get("translated_news", []),
        "analysis": analysis,
        "web_url": os.environ.get("WEB_URL", ""),
    }

    # ── Step 5a: Send to Feishu ──
    try:
        feishu_ok = send_briefing(briefing)
    except Exception as e:
        logger.error(f"Feishu send crashed: {e}")
        feishu_ok = False
        errors.append("feishu")

    # ── Step 6: Save for Web Dashboard ───────────────────────────────────
    logger.info("[6/6] Saving for web dashboard...")
    try:
        web_path = save_daily_briefing(briefing)
    except Exception as e:
        logger.error(f"Web save crashed: {e}")
        web_path = "FAILED"
        errors.append("web_save")

    # ── Summary ──────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("  Pipeline Summary")
    logger.info("=" * 60)
    logger.info(f"  Date      : {briefing['date']} ({briefing['weekday']})")
    logger.info(f"  Crypto    : {len(crypto_data)} tokens fetched")
    logger.info(f"  Stocks    : {len(stock_data.get('primary', []))} primary")
    logger.info(f"  News      : {len(briefing['news'])} translated items")
    logger.info(f"  Viewpoints: {len(analysis.get('viewpoints', []))}")
    logger.info(f"  Feishu    : {'✓ sent' if feishu_ok else '✗ failed'}")
    logger.info(f"  Web       : {web_path}")
    if errors:
        logger.warning(f"  Errors    : {', '.join(errors)}")
    else:
        logger.info(f"  Errors    : None ✓")
    logger.info("=" * 60)

    # Return non-zero only if critical steps failed
    # (data fetch failures are non-critical since AI can still search)
    if "ai_analysis" in errors and "web_save" in errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
