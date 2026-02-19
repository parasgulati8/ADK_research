import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from .config import MAX_NEWS_PER_TARGET


def get_company_news(query: str, days_back: int = 3) -> dict:
    """
    Fetch recent news articles for a specific company, sector, or macro topic.

    This is a thin wrapper around NewsAPI that:
    - Applies a configurable days-back window.
    - Returns a compact list of articles suitable for the LLM.

    Args:
        query: Search term, e.g. 'Reliance Industries' or 'Indian IT Sector'.
        days_back: History window in days (default 3).

    Returns:
        dict: Either
          { "articles": [ { "title": ..., "source": ..., "url": ..., "description": ... }, ... ] }
        or
          { "error": "<message>" }
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return {"error": "NewsAPI key not found"}

    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "from": from_date,
        "sortBy": "relevancy",
        "language": "en",
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            return {"error": data.get("message", "Unknown NewsAPI error")}

        raw_articles = data.get("articles", []) or []

        # Format results for the LLM to process easily, limiting count.
        articles = [
            {
                "title": art.get("title"),
                "source": (art.get("source") or {}).get("name"),
                "url": art.get("url"),
                "description": art.get("description"),
            }
            for art in raw_articles[:MAX_NEWS_PER_TARGET]
        ]
        return {
            "query": query,
            "from_date": from_date,
            "articles": articles,
        }
    except requests.Timeout:
        return {"error": "NewsAPI request timed out"}
    except requests.RequestException as exc:
        return {"error": f"NewsAPI request failed: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Unexpected error while fetching news: {exc}"}


def calculate_portfolio_metrics(holdings_json: str) -> Dict[str, object]:
    """
    Calculate aggregate portfolio metrics from a JSON-encoded holdings list.

    The input is expected to be a JSON array of objects with at least:
      - 'tradingsymbol': string
      - 'quantity': number
      - 'last_price' or 'price': number
      - optional 'sector': string

    Returns a dict that can be partially mapped into PortfolioMetrics:
      {
        "total_value": float,
        "total_market_value": float,  # alias for backward compatibility
        "top_5_holdings": [ "SYMBOL: qty", ... ],
        "count": int,
        "sector_allocations": [ { "sector": str, "weight_pct": float }, ... ],
        "top_holding_weight_pct": float | None
      }

    On error, returns: { "error": "<message>" }.
    """
    try:
        holdings = json.loads(holdings_json)
        if not isinstance(holdings, list):
            return {"error": "Holdings JSON must be a list"}

        # Compute per-holding value and total.
        enriched: List[Dict[str, object]] = []
        total_value = 0.0
        for h in holdings:
            if not isinstance(h, dict):
                continue
            try:
                qty = float(h.get("quantity", 0) or 0)
                price = h.get("last_price", h.get("price", 0))
                price_f = float(price or 0)
                value = qty * price_f
            except (TypeError, ValueError):
                value = 0.0
            total_value += value
            enriched.append({**h, "_value": value})

        # Top 5 holdings by absolute quantity (keep old behavior) and by value (for weights).
        summary_labels = [
            f"{h.get('tradingsymbol')}: {h.get('quantity')}"
            for h in holdings[:5]
            if isinstance(h, dict)
        ]

        sector_buckets: Dict[str, float] = {}
        top_holding_weight_pct: Optional[float] = None

        if total_value > 0:
            # Compute sector allocations based on '_value'.
            for h in enriched:
                sector = str(h.get("sector") or "UNKNOWN")
                sector_buckets[sector] = sector_buckets.get(sector, 0.0) + float(
                    h.get("_value", 0.0)
                )

            sector_allocations = [
                {
                    "sector": sector,
                    "weight_pct": round(value / total_value * 100.0, 2),
                }
                for sector, value in sorted(
                    sector_buckets.items(), key=lambda kv: kv[1], reverse=True
                )
            ]

            # Top holding weight by value.
            max_value = max((float(h.get("_value", 0.0)) for h in enriched), default=0.0)
            top_holding_weight_pct = (
                round(max_value / total_value * 100.0, 2) if max_value > 0 else None
            )
        else:
            sector_allocations = []

        return {
            "total_value": round(total_value, 2),
            "total_market_value": round(total_value, 2),  # backward-compatible alias
            "top_5_holdings": summary_labels,
            "count": len(holdings),
            "sector_allocations": sector_allocations,
            "top_holding_weight_pct": top_holding_weight_pct,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to parse holdings: {exc}"}