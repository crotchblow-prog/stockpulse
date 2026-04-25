"""Per-holding technical indicators: RSI(14), distance from MAs and 52-week extremes."""

from dataclasses import dataclass
import pandas as pd


@dataclass
class Technicals:
    """Indicators computed from a daily-close series. Any field can be None on insufficient data."""

    rsi_14: float | None
    ma_50: float | None
    ma_200: float | None
    high_52w: float | None
    low_52w: float | None
    pct_from_ma_50: float | None       # (price - ma) / ma
    pct_from_ma_200: float | None
    pct_from_52w_high: float | None    # negative when below the high
    pct_from_52w_low: float | None     # positive when above the low


def rsi(closes: pd.Series, period: int = 14) -> float | None:
    """Wilder's RSI of a daily-close series. Returns None if fewer than period+1 points."""
    if len(closes) < period + 1:
        return None
    delta = closes.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    value = (100 - 100 / (1 + rs)).iloc[-1]
    return float(value) if pd.notna(value) else None


def compute(closes: pd.Series) -> Technicals:
    """Compute the full Technicals bundle from a daily-close series (Series indexed by date)."""
    if closes is None or closes.empty:
        return Technicals(*([None] * 9))
    closes = closes.dropna()
    last = float(closes.iloc[-1])
    ma_50 = float(closes.tail(50).mean()) if len(closes) >= 50 else None
    ma_200 = float(closes.tail(200).mean()) if len(closes) >= 200 else None
    last_year = closes.tail(252)
    high_52w = float(last_year.max()) if not last_year.empty else None
    low_52w = float(last_year.min()) if not last_year.empty else None

    def _pct(p: float, ref: float | None) -> float | None:
        return (p - ref) / ref if ref else None

    return Technicals(
        rsi_14=rsi(closes, 14),
        ma_50=ma_50,
        ma_200=ma_200,
        high_52w=high_52w,
        low_52w=low_52w,
        pct_from_ma_50=_pct(last, ma_50),
        pct_from_ma_200=_pct(last, ma_200),
        pct_from_52w_high=_pct(last, high_52w),
        pct_from_52w_low=_pct(last, low_52w),
    )
