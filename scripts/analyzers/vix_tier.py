"""VIX → tier classification using config/holdings.json `tier_strategy`."""

from dataclasses import dataclass
from typing import Any


@dataclass
class TierResult:
    """Outcome of classifying a VIX value against holdings_config['tier_strategy']."""

    name: str                  # "tier_0" … "tier_5"
    index: int                 # 0 … 5
    action: str                # e.g. "警戒佈局"
    cash_target_pct: int
    buy_list: list[str]
    vix_range: tuple[float, float]
    sell_list: list[str] | None = None
    buy_size_pct: str | None = None
    note: str | None = None


def classify(vix_value: float, holdings_config: dict[str, Any]) -> TierResult:
    """Return the TierResult whose vix_range contains `vix_value` (lo ≤ vix < hi).

    The top tier's high bound is treated as inclusive so a VIX of 100 still maps.
    Raises ValueError if no tier matches (should be unreachable with the spec config).
    """
    strategy = holdings_config["tier_strategy"]
    sorted_keys = sorted(strategy.keys(), key=lambda k: strategy[k]["vix_range"][0])
    last_key = sorted_keys[-1]

    for key in sorted_keys:
        cfg = strategy[key]
        lo, hi = cfg["vix_range"]
        in_range = (lo <= vix_value < hi) or (key == last_key and vix_value >= lo)
        if not in_range:
            continue
        return TierResult(
            name=key,
            index=int(key.removeprefix("tier_")),
            action=cfg["action"],
            cash_target_pct=cfg["cash_target_pct"],
            buy_list=list(cfg.get("buy_list", [])),
            vix_range=(float(lo), float(hi)),
            sell_list=list(cfg["sell_list"]) if "sell_list" in cfg else None,
            buy_size_pct=cfg.get("buy_size_pct"),
            note=cfg.get("note"),
        )

    raise ValueError(f"VIX {vix_value} did not match any tier in tier_strategy")


# Display helpers — kept here so markdown_gen and any future Telegram formatter share them.
TIER_BADGE = {
    0: "🟢",
    1: "🟡",
    2: "🟠",
    3: "🔴",
    4: "🚨",
    5: "💥",
}

TIER_STARS = {0: "", 1: "", 2: "", 3: "⭐", 4: "⭐⭐", 5: "⭐⭐⭐"}
