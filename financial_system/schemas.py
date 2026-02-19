from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# -------------------------
# Portfolio domain
# -------------------------


class Holding(BaseModel):
    """Normalized representation of a single portfolio holding."""

    symbol: str = Field(..., description="Trading symbol, e.g. RELIANCE")
    name: Optional[str] = Field(None, description="Company name, if available")
    sector: Optional[str] = Field(None, description="Sector/industry, if known")
    quantity: float = Field(..., ge=0)
    avg_price: Optional[float] = Field(None, ge=0)
    last_price: Optional[float] = Field(None, ge=0)
    value: Optional[float] = Field(
        None,
        description="Current market value = quantity * last_price (or MCP price field).",
    )
    weight_pct: Optional[float] = Field(
        None,
        description="Percentage of total portfolio value in this holding.",
    )
    unrealized_pnl: Optional[float] = Field(
        None,
        description="Unrealized profit/loss in absolute terms.",
    )


class SectorAllocation(BaseModel):
    sector: str
    weight_pct: float


class PortfolioMetrics(BaseModel):
    total_value: float = Field(..., ge=0)
    cash_value: Optional[float] = Field(None, ge=0)
    cash_ratio_pct: Optional[float] = Field(None, ge=0, le=100)
    top_holding_weight_pct: Optional[float] = None
    sector_allocations: List[SectorAllocation] = Field(default_factory=list)


class PortfolioSummary(BaseModel):
    """Top-level object produced by the portfolio data agent."""

    holdings: List[Holding]
    metrics: PortfolioMetrics
    top_tickers: List[str] = Field(
        default_factory=list,
        description="Tickers that contribute most to portfolio risk/weight.",
    )
    top_sectors: List[str] = Field(
        default_factory=list,
        description="Sectors with highest portfolio allocation.",
    )
    as_of: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this summary was generated (UTC).",
    )


# -------------------------
# Risk & performance
# -------------------------


class RiskItem(BaseModel):
    code: str = Field(
        ...,
        description="Machine-friendly identifier, e.g. CONCENTRATION_RISK.",
    )
    message: str = Field(..., description="Human-readable explanation of the risk.")
    severity: Literal["low", "medium", "high"]
    affected_symbols: List[str] = Field(
        default_factory=list,
        description="Symbols materially affected by this risk.",
    )


class PerformanceItem(BaseModel):
    symbol: str
    return_pct: Optional[float] = None
    comment: Optional[str] = None


class RiskPerformanceSummary(BaseModel):
    risk_items: List[RiskItem] = Field(default_factory=list)
    performance_items: List[PerformanceItem] = Field(default_factory=list)
    key_flags: List[str] = Field(
        default_factory=list,
        description="Short bullet-style flags like 'High small-cap exposure'.",
    )


# -------------------------
# News & macro
# -------------------------


class NewsArticle(BaseModel):
    title: str
    source: str
    url: str
    description: Optional[str] = None


class NewsSignal(BaseModel):
    target: str = Field(
        ...,
        description="Ticker, sector, or macro topic this signal applies to.",
    )
    target_type: Literal["ticker", "sector", "macro"]
    signal: Literal["bullish", "bearish", "neutral"]
    horizon: Literal["short_term", "medium_term", "long_term"]
    rationale: str
    articles: List[NewsArticle] = Field(default_factory=list)


class NewsSummary(BaseModel):
    signals: List[NewsSignal] = Field(default_factory=list)
    overall_macro_view: Optional[str] = None


# -------------------------
# Final recommendations
# -------------------------


class ActionItem(BaseModel):
    priority: Literal["high", "medium", "low"]
    action_type: Literal["buy", "sell", "hold", "rebalance", "watchlist"]
    target: str = Field(
        ...,
        description="Ticker, sector, or 'portfolio' this action refers to.",
    )
    rationale: str
    risk_note: Optional[str] = None
    time_horizon: Optional[Literal["short_term", "medium_term", "long_term"]] = None


class RecommendationPlan(BaseModel):
    actions: List[ActionItem] = Field(default_factory=list)
    high_level_view: str = Field(
        ...,
        description="1–3 paragraph summary of portfolio health and strategy.",
    )
    next_review_horizon: Optional[str] = Field(
        None,
        description="When to revisit this analysis, e.g. '1 month'.",
    )
    report_markdown: Optional[str] = Field(
        None,
        description="User-facing report formatted as Markdown.",
    )

