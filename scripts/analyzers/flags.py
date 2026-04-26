"""Closed-vocabulary flags for a holding — deterministic, stable order, diff-friendly."""

from __future__ import annotations

from dataclasses import dataclass, field

# Closed vocabulary. Order is the canonical emission order — do not reshuffle.
FLAG_VOCAB: tuple[str, ...] = (
    # Momentum
    "oversold_rsi",
    "overbought_rsi",
    # Trend
    "near_50dma",
    "below_50dma",
    "below_200dma",
    # Extremes
    "near_52w_low",
    "near_52w_high",
    "deep_drawdown",
    # P&L
    "underwater",
    "big_gain",
    # Calendar
    "earnings_within_7d",
    "earnings_within_3d",
    # Tags
    "high_risk_tag",
    "event_play",
    # Tier
    "buy_list_member",
    "sell_list_member",
    "beta_size_warn",
)

_FLAG_INDEX: dict[str, int] = {name: i for i, name in enumerate(FLAG_VOCAB)}

# Tags that mark a position as an event play (binary catalyst / activist target).
EVENT_PLAY_TAGS: frozenset[str] = frozenset({"muddy_waters_target", "event_play", "activist_target"})


@dataclass
class FlagInputs:
    """All facts a holding contributes to flag derivation. None means unknown — flag is skipped."""

    symbol: str
    rsi_14: float | None = None
    pct_from_ma_50: float | None = None        # (price - ma) / ma; e.g. -0.05 = 5% below
    pct_from_ma_200: float | None = None
    pct_from_52w_high: float | None = None     # negative when below the high
    pct_from_52w_low: float | None = None      # positive when above the low
    vs_cost: float | None = None               # (price - avg_cost) / avg_cost
    days_to_earnings: int | None = None        # countdown in calendar days; None when unknown
    tags: tuple[str, ...] = field(default_factory=tuple)
    tier_index: int | None = None              # 0..5
    tier_buy_list: tuple[str, ...] = field(default_factory=tuple)
    tier_sell_list: tuple[str, ...] = field(default_factory=tuple)


def derive_flags(inp: FlagInputs) -> list[str]:
    """Return the closed-vocab flags that fire for this holding, in FLAG_VOCAB order."""
    fired: set[str] = set()

    # ── Momentum ────────────────────────────────────────────────────────────
    if inp.rsi_14 is not None:
        if inp.rsi_14 < 30:
            fired.add("oversold_rsi")
        elif inp.rsi_14 > 70:
            fired.add("overbought_rsi")

    # ── Trend ───────────────────────────────────────────────────────────────
    if inp.pct_from_ma_50 is not None:
        if abs(inp.pct_from_ma_50) < 0.02:
            fired.add("near_50dma")
        if inp.pct_from_ma_50 < -0.05:
            fired.add("below_50dma")
    if inp.pct_from_ma_200 is not None and inp.pct_from_ma_200 < 0:
        fired.add("below_200dma")

    # ── Extremes ────────────────────────────────────────────────────────────
    if inp.pct_from_52w_low is not None and inp.pct_from_52w_low < 0.05:
        fired.add("near_52w_low")
    if inp.pct_from_52w_high is not None and inp.pct_from_52w_high > -0.02:
        fired.add("near_52w_high")
    if inp.pct_from_52w_high is not None and inp.pct_from_52w_high < -0.30:
        fired.add("deep_drawdown")

    # ── P&L ─────────────────────────────────────────────────────────────────
    if inp.vs_cost is not None:
        if inp.vs_cost < -0.10:
            fired.add("underwater")
        if inp.vs_cost > 0.20:
            fired.add("big_gain")

    # ── Calendar ────────────────────────────────────────────────────────────
    if inp.days_to_earnings is not None and 0 <= inp.days_to_earnings <= 7:
        fired.add("earnings_within_7d")
        if inp.days_to_earnings <= 3:
            fired.add("earnings_within_3d")  # 3d implies 7d

    # ── Tags ────────────────────────────────────────────────────────────────
    tag_set = {t.lower() for t in inp.tags}
    if "high_risk" in tag_set:
        fired.add("high_risk_tag")
    if tag_set & EVENT_PLAY_TAGS:
        fired.add("event_play")

    # ── Tier ────────────────────────────────────────────────────────────────
    if inp.symbol in inp.tier_buy_list:
        fired.add("buy_list_member")
    if _matches_sell_list(inp.symbol, tag_set, inp.tier_sell_list):
        fired.add("sell_list_member")
    if (
        inp.tier_index is not None
        and inp.tier_index <= 1
        and "high_beta" in tag_set
    ):
        fired.add("beta_size_warn")

    return sorted(fired, key=_FLAG_INDEX.__getitem__)


def is_watchworthy(flags: list[str]) -> bool:
    """True if any flag besides bare buy_list_member fires — used to filter the Watch List."""
    return any(f != "buy_list_member" for f in flags)


def _matches_sell_list(symbol: str, tag_set: set[str], sell_list: tuple[str, ...]) -> bool:
    """Match by exact ticker or tier_strategy wildcard tag like 'high_beta_*'."""
    for entry in sell_list:
        if entry == symbol:
            return True
        if entry.endswith("_*"):
            tag = entry[:-2]
            if tag in tag_set:
                return True
    return False
