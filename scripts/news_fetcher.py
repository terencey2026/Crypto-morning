"""
News Fetcher - Crypto news aggregation from RSS feeds
=====================================================
Fetches recent crypto news from multiple RSS feeds (CoinTelegraph, CoinDesk).
Replaces CryptoPanic API to remain 100% free.
"""

import logging
import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time

logger = logging.getLogger(__name__)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import RSS_FEEDS


def fetch_crypto_news(limit: int = 15) -> list[dict]:
    """
    Fetch recent crypto news from RSS feeds.

    Args:
        limit: Maximum number of news items to return.

    Returns:
        List of dicts, each with keys:
        title, url, source, published_at, sentiment ("neutral")
    """
    all_news = []

    # We only want news from the last 48 hours to be safe
    cutoff_time = time.time() - (48 * 3600)

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:  # Take top 15 from each
                # Check timestamp
                published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                if published_parsed:
                    timestamp = time.mktime(published_parsed)
                    if timestamp < cutoff_time:
                        continue  # Skip old news

                    # Convert to ISO format
                    dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
                    pub_str = dt.isoformat()
                else:
                    pub_str = ""
                    timestamp = 0

                all_news.append({
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "source": source_name,
                    "published_at": pub_str,
                    "sentiment": "neutral",  # RSS doesn't have sentiment
                    "_timestamp": timestamp
                })
        except Exception as e:
            logger.error(f"Failed to fetch RSS from {source_name}: {e}")

    # Sort all news by timestamp descending (newest first)
    all_news.sort(key=lambda x: x.get("_timestamp", 0), reverse=True)

    # Clean up the internal key
    for news in all_news:
        news.pop("_timestamp", None)

    results = all_news[:limit]
    logger.info(f"Fetched {len(results)} recent news items from RSS feeds")
    return results
