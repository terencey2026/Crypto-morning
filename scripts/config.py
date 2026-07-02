"""
Crypto Morning Briefing - Configuration
========================================
Watchlists, API endpoints, thresholds, and output settings.
Edit this file to customize your briefing content.
"""

import os

# ── API Keys (set via environment variables / GitHub Secrets) ─────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")

# ── Crypto Watchlist (CoinGecko IDs) ─────────────────────────────────────
# Find IDs at: https://www.coingecko.com/
# All crypto tokens listed here are always shown in the briefing.
CRYPTO_WATCHLIST = [
    {"id": "bitcoin",     "symbol": "BTC",  "name": "Bitcoin"},
    {"id": "ethereum",    "symbol": "ETH",  "name": "Ethereum"},
    {"id": "solana",      "symbol": "SOL",  "name": "Solana"},
    {"id": "binancecoin", "symbol": "BNB",  "name": "BNB"},
    {"id": "uniswap",     "symbol": "UNI",  "name": "Uniswap"},
    {"id": "chainlink",   "symbol": "LINK", "name": "Chainlink"},
    {"id": "hyperliquid", "symbol": "HYPE", "name": "Hyperliquid"},
    {"id": "zcash",       "symbol": "ZEC",  "name": "Zcash"},
]

# ── Stock Watchlist (Yahoo Finance Tickers) ──────────────────────────────
# Primary: always shown. Secondary: shown only when |change| > threshold.
STOCK_WATCHLIST = {
    "primary": [
        # 业务类
        {"ticker": "COIN", "name": "Coinbase",          "group": "业务类"},
        {"ticker": "HOOD", "name": "Robinhood",         "group": "业务类"},
        {"ticker": "CRCL", "name": "Circle",            "group": "业务类"},
        # DAT类 (Digital Asset Treasury)
        {"ticker": "MSTR", "name": "Strategy",          "group": "DAT类"},
        {"ticker": "BMNR", "name": "Bitmine Immersion", "group": "DAT类"},
        {"ticker": "PURR", "name": "United Bitcoin",    "group": "DAT类"},
        {"ticker": "FWDI", "name": "FWD Innovation",    "group": "DAT类"},
        {"ticker": "BNC",  "name": "BNC Digital",       "group": "DAT类"},
    ],
    "secondary": [
        # 业务类
        {"ticker": "FIGR",    "name": "FIGR Capital",    "group": "业务类"},
        {"ticker": "GLXY",    "name": "Galaxy Digital",  "group": "业务类"},
        # 矿股
        {"ticker": "IREN",    "name": "Iris Energy",     "group": "矿股"},
        {"ticker": "WULF",    "name": "TeraWulf",        "group": "矿股"},
        {"ticker": "HUT",     "name": "Hut 8",           "group": "矿股"},
        {"ticker": "CORZ",    "name": "Core Scientific", "group": "矿股"},
        {"ticker": "BTDR",    "name": "Bitdeer",         "group": "矿股"},
        # 港股
        {"ticker": "HSK.HK",  "name": "HashKey Group",   "group": "港股"},
        {"ticker": "0863.HK", "name": "OSL Group",       "group": "港股"},
    ],
}

# ── Thresholds ────────────────────────────────────────────────────────────
# Secondary stocks only appear in the briefing when their absolute
# price change exceeds this percentage.
SECONDARY_STOCK_THRESHOLD_PCT = 5.0

# ── Gemini API Settings ──────────────────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-pro-latest"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# ── 3. RSS Feeds (News) ──────────────────────────────────────────────────
# Using RSS instead of API to remain 100% free
RSS_FEEDS = {
    "CoinTelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Bitcoin.com": "https://news.bitcoin.com/feed/"
}

# ── 4. Feishu Configuration ──────────────────────────────────────────────
NUM_VIEWPOINTS = 3          # Number of 【观点—逻辑—标的】 viewpoints to generate
TIMEZONE = "Asia/Shanghai"  # Beijing Time (UTC+8)

# ── Output Paths ─────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DATA_DIR = os.path.join(PROJECT_ROOT, "docs", "data")
