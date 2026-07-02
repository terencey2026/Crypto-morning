"""
Data Fetcher - Crypto prices (CoinGecko) and Stock prices (Yahoo Finance)
=========================================================================
Handles all market data collection with robust error handling.
Each ticker that fails is logged and skipped without crashing the pipeline.
"""

import logging
import requests

logger = logging.getLogger(__name__)

# Import config - use relative import style for scripts directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CRYPTO_WATCHLIST, STOCK_WATCHLIST, SECONDARY_STOCK_THRESHOLD_PCT


def fetch_crypto_prices() -> list[dict]:
    """
    Fetch cryptocurrency prices from CoinGecko free API.

    Returns:
        List of dicts, each with keys:
        symbol, name, price, change_24h_pct, volume_24h, market_cap
        Sorted by absolute 24h change (biggest movers first).
    """
    ids = ",".join(c["id"] for c in CRYPTO_WATCHLIST)
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids,
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h",
    }

    try:
        resp = requests.get(
            url, params=params, timeout=30,
            headers={"Accept": "application/json", "User-Agent": "CryptoBriefing/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"CoinGecko API request failed: {e}")
        return []
    except ValueError as e:
        logger.error(f"CoinGecko returned invalid JSON: {e}")
        return []

    # Build lookup from CoinGecko ID → our config metadata
    config_lookup = {c["id"]: c for c in CRYPTO_WATCHLIST}

    results = []
    for coin in data:
        meta = config_lookup.get(coin.get("id", ""), {})
        results.append({
            "symbol": meta.get("symbol", coin.get("symbol", "?").upper()),
            "name": meta.get("name", coin.get("name", "Unknown")),
            "price": coin.get("current_price") or 0,
            "change_24h_pct": round(coin.get("price_change_percentage_24h") or 0, 2),
            "volume_24h": coin.get("total_volume") or 0,
            "market_cap": coin.get("market_cap") or 0,
        })

    # Sort by absolute change (biggest movers first for quick scanning)
    results.sort(key=lambda x: abs(x["change_24h_pct"]), reverse=True)
    logger.info(f"Fetched {len(results)}/{len(CRYPTO_WATCHLIST)} crypto prices")
    return results


def fetch_stock_prices() -> dict:
    """
    Fetch stock prices from Yahoo Finance for all watchlist tickers.

    Primary stocks are always included in the result.
    Secondary stocks are only included if |change| > SECONDARY_STOCK_THRESHOLD_PCT.

    Returns:
        Dict with keys:
        - "primary": list of stock dicts (always shown)
        - "secondary_alerts": list of stock dicts (only big movers)

        Each stock dict has: ticker, name, price, change_pct, volume, group
    """
    import yfinance as yf

    primary_results = []
    secondary_alerts = []

    for priority in ["primary", "secondary"]:
        stocks = STOCK_WATCHLIST.get(priority, [])

        for stock_info in stocks:
            ticker = stock_info["ticker"]
            name = stock_info["name"]
            group = stock_info["group"]

            try:
                t = yf.Ticker(ticker)
                # Use 5d to ensure we get at least 2 trading days even after weekends
                hist = t.history(period="5d")

                if hist is None or hist.empty:
                    logger.warning(f"No data returned for {ticker} - ticker may be invalid")
                    continue

                # Drop any rows with NaN close prices
                hist = hist.dropna(subset=["Close"])
                if len(hist) < 1:
                    logger.warning(f"No valid close prices for {ticker}")
                    continue

                current_close = float(hist["Close"].iloc[-1])

                # Calculate change vs previous close
                if len(hist) >= 2:
                    prev_close = float(hist["Close"].iloc[-2])
                    change_pct = ((current_close - prev_close) / prev_close) * 100
                else:
                    change_pct = 0.0

                volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0

                entry = {
                    "ticker": ticker,
                    "name": name,
                    "price": round(current_close, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": volume,
                    "group": group,
                }

                if priority == "primary":
                    primary_results.append(entry)
                elif abs(change_pct) >= SECONDARY_STOCK_THRESHOLD_PCT:
                    secondary_alerts.append(entry)
                    logger.info(f"Secondary alert: {ticker} {change_pct:+.2f}%")

            except Exception as e:
                logger.warning(f"Failed to fetch {ticker}: {e}")
                continue

    # Sort each list by absolute change (biggest movers first)
    primary_results.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    secondary_alerts.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    logger.info(
        f"Fetched {len(primary_results)} primary stocks, "
        f"{len(secondary_alerts)} secondary alerts"
    )

    return {
        "primary": primary_results,
        "secondary_alerts": secondary_alerts,
    }
