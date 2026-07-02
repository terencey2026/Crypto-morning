"""
AI Analyzer - Gemini API with Google Search grounding
======================================================
Sends structured market data + news to Gemini for analysis.
Gemini uses Google Search in real-time to supplement the data
(ETF flows, macro events, etc.) and generates viewpoints
in the strict 【观点—逻辑—标的】 format.
"""

import json
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_API_URL, TIMEZONE, NUM_VIEWPOINTS


# ── Prompt Template ──────────────────────────────────────────────────────

ANALYSIS_PROMPT = """你是一位资深的加密货币投研分析师，正在为每日 8:45 的晨会准备加密板块发言。

## 当前信息
- 日期：{date} ({weekday})
{weekend_note}

## 一、加密货币行情（过去24小时）
{crypto_table}

## 二、加密概念股行情（隔夜美股）
### 主要标的
{primary_stocks_table}

{secondary_section}

## 三、近期重要新闻
{news_list}

---

## 你的任务

请基于上述数据完成以下工作：

### 任务A：补充搜索
通过搜索补充以下信息（用于丰富分析，不要单独列出）：
- 加密货币现货ETF（IBIT, ETHA等）的最新单日资金流向
- 过去24小时可能遗漏的重大加密/宏观事件
- 上述异动标的的具体驱动因素

### 任务B：生成晨会观点
生成 {num_viewpoints} 条核心观点，严格遵守以下规则：
1. **每条观点必须按【观点——逻辑——标的】结构**
2. **禁止纯新闻播报**——每条必须有明确的方向判断（看多/看空/观望）
3. **观点必须对应到具体的 ETF / 个股 / 代币**
4. 分析风格因标的而异：
   - 交易型标的 → 关注技术位、催化剂、时间窗口
   - 中长线标的 → 关注产业逻辑、估值、行业趋势
5. **涨跌幅最大的标的必须优先分析**
6. 逻辑要有层次，不要只有一句话

### 任务C：新闻翻译与整理
将上述【近期重要新闻】挑选3-5条最重要的，**翻译成流畅的中文**，并根据新闻内容判断情绪（positive/negative/neutral）。

### 任务D：ETF概况
用1-2句话概括加密ETF的最新资金流向情况。

### 任务E：风险提示
列出1-2条当前需要关注的核心风险。

---

请严格按照以下JSON格式输出（不要输出JSON以外的任何内容）：

{{
  "etf_summary": "BTC现货ETF昨日净流入/流出XXX，ETH ETF...",
  "translated_news": [
    {{
      "title": "中文翻译后的新闻标题",
      "url": "原始新闻链接",
      "source": "原始来源",
      "sentiment": "positive 或 negative 或 neutral"
    }}
  ],
  "viewpoints": [
    {{
      "title": "简短标题（如：看多BTC突破7万）",
      "direction": "bullish 或 bearish 或 neutral",
      "view": "一句话核心观点",
      "logic": "详细逻辑，可以分多点阐述（用分号分隔）",
      "targets": "具体标的，如 BTC / MSTR / IBIT"
    }}
  ],
  "risk_alerts": [
    "风险提示内容"
  ],
  "supplementary_news": [
    {{
      "title": "通过搜索发现的补充新闻标题",
      "summary": "一句话概要",
      "source": "来源名称",
      "url": "来源链接"
    }}
  ]
}}"""


# ── Helper Formatters ────────────────────────────────────────────────────

def _format_crypto_table(crypto_data: list) -> str:
    """Format crypto prices as a markdown table for the prompt."""
    if not crypto_data:
        return "（暂无数据）"

    lines = [
        "| 代币 | 价格 (USD) | 24h涨跌 | 24h成交量 |",
        "|------|-----------|---------|----------|",
    ]
    for c in crypto_data:
        arrow = "🔺" if c["change_24h_pct"] > 0 else "🔻" if c["change_24h_pct"] < 0 else "➖"
        vol = _format_volume(c["volume_24h"])
        price = f"${c['price']:,.2f}" if c["price"] >= 1 else f"${c['price']:.4f}"
        lines.append(
            f"| {c['symbol']} | {price} | {arrow} {c['change_24h_pct']:+.2f}% | {vol} |"
        )
    return "\n".join(lines)


def _format_stocks_table(stocks: list) -> str:
    """Format stock prices as a markdown table for the prompt."""
    if not stocks:
        return "（暂无数据）"

    lines = [
        "| 股票 | 类型 | 价格 (USD) | 隔夜涨跌 |",
        "|------|------|-----------|---------|",
    ]
    for s in stocks:
        arrow = "🔺" if s["change_pct"] > 0 else "🔻" if s["change_pct"] < 0 else "➖"
        lines.append(
            f"| {s['ticker']} ({s['name']}) | {s['group']} | ${s['price']:.2f} | {arrow} {s['change_pct']:+.2f}% |"
        )
    return "\n".join(lines)


def _format_news_list(news: list) -> str:
    """Format news as a numbered list for the prompt."""
    if not news:
        return "（暂无重要新闻）"

    sentiment_icons = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}
    lines = []
    for i, n in enumerate(news[:10], 1):
        icon = sentiment_icons.get(n.get("sentiment", ""), "⚪")
        lines.append(f"{i}. {icon} {n['title']} — 来源: {n.get('source', 'Unknown')}")
    return "\n".join(lines)


def _format_volume(vol: float) -> str:
    """Format volume to human-readable string."""
    if vol >= 1e12:
        return f"${vol / 1e12:.1f}T"
    elif vol >= 1e9:
        return f"${vol / 1e9:.1f}B"
    elif vol >= 1e6:
        return f"${vol / 1e6:.0f}M"
    elif vol >= 1e3:
        return f"${vol / 1e3:.0f}K"
    else:
        return f"${vol:.0f}"


# ── Main Analysis Function ───────────────────────────────────────────────

def generate_analysis(crypto_data: list, stock_data: dict, news_data: list) -> dict:
    """
    Send market data to Gemini API for analysis with Google Search grounding.

    Args:
        crypto_data: List of crypto price dicts from data_fetcher
        stock_data: Dict with "primary" and "secondary_alerts" from data_fetcher
        news_data: List of news dicts from news_fetcher

    Returns:
        Dict with keys: etf_summary, viewpoints, risk_alerts,
        supplementary_news, grounding_sources
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set — cannot run analysis")
        return _empty_analysis("GEMINI_API_KEY 未配置")

    # ── Build the prompt ──
    now = datetime.now(ZoneInfo(TIMEZONE))
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[now.weekday()]
    is_monday = now.weekday() == 0

    weekend_note = ""
    if is_monday:
        weekend_note = (
            "⚠️ 今天是周一，你需要覆盖整个周末（周六和周日）的所有重要信息和事件，"
            "包括周末期间加密货币的价格波动和重大新闻。"
        )

    secondary = stock_data.get("secondary_alerts", [])
    if secondary:
        secondary_section = (
            f"### 次要标的异动（涨跌幅 > 5%）\n{_format_stocks_table(secondary)}"
        )
    else:
        secondary_section = "### 次要标的：无显著异动"

    prompt = ANALYSIS_PROMPT.format(
        date=now.strftime("%Y-%m-%d"),
        weekday=weekday,
        weekend_note=weekend_note,
        crypto_table=_format_crypto_table(crypto_data),
        primary_stocks_table=_format_stocks_table(stock_data.get("primary", [])),
        secondary_section=secondary_section,
        news_list=_format_news_list(news_data),
        num_viewpoints=NUM_VIEWPOINTS,
    )

    # ── Call Gemini API (REST) ──
    url = GEMINI_API_URL.format(model=GEMINI_MODEL)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "responseMimeType": "application/json",
        },
    }

    try:
        logger.info(f"Calling Gemini API ({GEMINI_MODEL}) with Google Search grounding...")
        resp = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else "Unknown"
        logger.error(f"Gemini API request failed (HTTP {status_code}): {e}")
        return _empty_analysis(f"Gemini API 请求失败 (HTTP {status_code}): {e}")
    except ValueError as e:
        logger.error(f"Gemini returned invalid JSON response: {e}")
        return _empty_analysis(f"Gemini 返回无效响应")

    # ── Parse response ──
    candidates = result.get("candidates", [])
    if not candidates:
        logger.error(f"Gemini returned no candidates. Full response: {json.dumps(result, ensure_ascii=False)[:500]}")
        return _empty_analysis("Gemini 未返回任何结果")

    candidate = candidates[0]

    # Extract text content (may be split across multiple parts)
    text_parts = []
    for part in candidate.get("content", {}).get("parts", []):
        if "text" in part:
            text_parts.append(part["text"])

    text = "".join(text_parts).strip()
    if not text:
        logger.error("Gemini returned empty text content")
        return _empty_analysis("Gemini 返回空内容")

    # Parse the JSON from Gemini's response
    try:
        analysis = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini output as JSON: {e}")
        logger.error(f"Raw text (first 500 chars): {text[:500]}")
        # Try to extract JSON from the text (sometimes Gemini wraps it)
        analysis = _try_extract_json(text)
        if analysis is None:
            return _empty_analysis("Gemini 输出格式解析失败")

    # Extract grounding sources from metadata
    grounding = candidate.get("groundingMetadata", {})
    sources = []
    for chunk in grounding.get("groundingChunks", []):
        web = chunk.get("web", {})
        if web:
            sources.append({
                "title": web.get("title", ""),
                "url": web.get("uri", ""),
            })

    analysis["grounding_sources"] = sources

    # Validate required fields
    analysis.setdefault("etf_summary", "ETF数据暂不可用")
    analysis.setdefault("viewpoints", [])
    analysis.setdefault("risk_alerts", [])
    analysis.setdefault("supplementary_news", [])
    analysis.setdefault("translated_news", [])

    logger.info(
        f"Analysis complete: {len(analysis['viewpoints'])} viewpoints, "
        f"{len(analysis['risk_alerts'])} risks, "
        f"{len(sources)} grounding sources"
    )
    return analysis


def _try_extract_json(text: str) -> dict | None:
    """Try to extract JSON from text that might have extra content around it."""
    # Try to find JSON object boundaries
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _empty_analysis(reason: str = "") -> dict:
    """Return empty analysis structure when the API fails."""
    return {
        "etf_summary": "ETF数据暂不可用",
        "viewpoints": [],
        "risk_alerts": [f"⚠️ AI分析引擎异常{f'：{reason}' if reason else ''}，请手动查阅市场信息"],
        "supplementary_news": [],
        "translated_news": [],
        "grounding_sources": [],
    }
