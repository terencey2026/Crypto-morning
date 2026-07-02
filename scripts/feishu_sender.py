"""
Feishu Sender - Push briefing to Feishu via Webhook (Interactive Card)
======================================================================
Formats the briefing data into a visually rich Feishu card message
and sends it to a group via custom bot webhook.
"""

import json
import logging
import requests

logger = logging.getLogger(__name__)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import FEISHU_WEBHOOK_URL


def send_briefing(briefing: dict) -> bool:
    """
    Send the morning briefing to Feishu as an interactive card.

    Args:
        briefing: Full briefing data dict (same structure saved to JSON)

    Returns:
        True if sent successfully, False otherwise.
    """
    if not FEISHU_WEBHOOK_URL:
        logger.warning("FEISHU_WEBHOOK_URL not set — skipping Feishu push")
        return False

    try:
        card = _build_card(briefing)
        payload = {"msg_type": "interactive", "card": card}

        resp = requests.post(
            FEISHU_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        # Feishu returns code=0 on success
        code = result.get("code") or result.get("StatusCode") or result.get("Code")
        if code == 0:
            logger.info("Feishu message sent successfully")
            return True
        else:
            logger.error(f"Feishu API returned error: {json.dumps(result, ensure_ascii=False)}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Feishu webhook request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error building/sending Feishu card: {e}")
        return False


# ── Card Builder ─────────────────────────────────────────────────────────

def _build_card(briefing: dict) -> dict:
    """Build a Feishu interactive card from briefing data."""
    date = briefing.get("date", "")
    weekday = briefing.get("weekday", "")
    is_recap = briefing.get("is_weekend_recap", False)

    elements = []

    # ── Crypto Market ──
    crypto = briefing.get("market_data", {}).get("crypto", [])
    if crypto:
        elements.append(_md("**📊 加密货币行情**"))
        lines = []
        for c in crypto:
            arrow = "🔺" if c["change_24h_pct"] > 0 else "🔻" if c["change_24h_pct"] < 0 else "➖"
            price = f"${c['price']:,.2f}" if c["price"] >= 1 else f"${c['price']:.4f}"
            lines.append(f"**{c['symbol']}**  {price}  {arrow} {c['change_24h_pct']:+.2f}%")
        elements.append(_md("\n".join(lines)))
        elements.append(_hr())

    # ── Concept Stocks ──
    stocks = briefing.get("market_data", {}).get("stocks", {})
    primary = stocks.get("primary", [])
    if primary:
        elements.append(_md("**📈 概念股行情（美股隔夜）**"))

        # Group by category
        grouped = {}
        for s in primary:
            g = s.get("group", "其他")
            grouped.setdefault(g, []).append(s)

        lines = []
        for group_name, group_stocks in grouped.items():
            lines.append(f"**{group_name}**")
            for s in group_stocks:
                arrow = "🔺" if s["change_pct"] > 0 else "🔻" if s["change_pct"] < 0 else "➖"
                lines.append(f"  {s['ticker']}  ${s['price']:.2f}  {arrow} {s['change_pct']:+.2f}%")
        elements.append(_md("\n".join(lines)))

    # Secondary alerts
    secondary = stocks.get("secondary_alerts", [])
    if secondary:
        alert_lines = ["**🔔 次要标的异动**"]
        for s in secondary:
            arrow = "🔺" if s["change_pct"] > 0 else "🔻"
            alert_lines.append(f"  {s['ticker']} ({s['group']}) {arrow} {s['change_pct']:+.2f}%")
        elements.append(_md("\n".join(alert_lines)))

    elements.append(_hr())

    # ── ETF Summary ──
    etf_summary = briefing.get("analysis", {}).get("etf_summary", "")
    if etf_summary:
        elements.append(_md(f"**💰 ETF概况**\n{etf_summary}"))
        elements.append(_hr())

    # ── News Events ──
    news = briefing.get("news", [])
    supp_news = briefing.get("analysis", {}).get("supplementary_news", [])
    if news or supp_news:
        elements.append(_md("**📰 隔夜重大事件**"))
        event_lines = []
        # Original news from CryptoPanic
        for n in news[:5]:
            icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(n.get("sentiment"), "⚪")
            event_lines.append(f"{icon} {n['title']}")
        # Supplementary news from Gemini search
        for n in supp_news[:3]:
            event_lines.append(f"📌 {n.get('title', '')} — {n.get('summary', '')}")
        elements.append(_md("\n".join(event_lines)))
        elements.append(_hr())

    # ── Core Viewpoints (most important section) ──
    viewpoints = briefing.get("analysis", {}).get("viewpoints", [])
    if viewpoints:
        elements.append(_md("**💡 核心观点**"))
        for i, vp in enumerate(viewpoints, 1):
            direction_label = {
                "bullish": "🟢 看多",
                "bearish": "🔴 看空",
                "neutral": "🟡 观望",
            }.get(vp.get("direction", ""), "⚪")

            vp_text = (
                f"**观点{i}：{direction_label} — {vp.get('title', '')}**\n"
                f"【观点】{vp.get('view', '')}\n"
                f"【逻辑】{vp.get('logic', '')}\n"
                f"【标的】{vp.get('targets', '')}"
            )
            elements.append(_md(vp_text))
            if i < len(viewpoints):
                elements.append(_hr())

    # ── Risk Alerts ──
    risks = briefing.get("analysis", {}).get("risk_alerts", [])
    if risks:
        elements.append(_hr())
        risk_text = "**⚠️ 风险提示**\n" + "\n".join(f"• {r}" for r in risks)
        elements.append(_md(risk_text))

    # ── Web Link ──
    web_url = briefing.get("web_url", "")
    if web_url:
        elements.append(_hr())
        elements.append(_md(f"🔗 [查看完整报告 →]({web_url})"))

    # ── Assemble Card ──
    title = f"🔥 加密晨报 — {date} ({weekday})"
    if is_recap:
        title = f"🔥 加密晨报（周末综合版） — {date} ({weekday})"

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": "turquoise",
        },
        "elements": elements,
    }


# ── Element Helpers ──────────────────────────────────────────────────────

def _md(text: str) -> dict:
    """Markdown text element."""
    return {"tag": "markdown", "content": text}


def _hr() -> dict:
    """Horizontal rule / divider."""
    return {"tag": "hr"}
