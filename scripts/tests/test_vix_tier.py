"""Boundary tests for vix_tier.classify — every range edge listed in the spec."""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from analyzers import vix_tier  # noqa: E402

HOLDINGS = json.loads((SCRIPTS_DIR.parent / "config" / "holdings.json").read_text("utf-8"))


@pytest.mark.parametrize(
    "vix,expected_index",
    [
        (0.0, 0),
        (14.99, 0),
        (15.0, 1),
        (17.99, 1),
        (18.0, 2),
        (24.59, 2),
        (24.6, 3),
        (29.49, 3),
        (29.5, 4),
        (34.99, 4),
        (35.0, 5),
        (75.0, 5),
        (100.0, 5),
    ],
)
def test_classify_boundaries(vix, expected_index):
    result = vix_tier.classify(vix, HOLDINGS)
    assert result.index == expected_index, f"VIX {vix} → expected tier_{expected_index}, got {result.name}"


def test_classify_returns_action_text():
    result = vix_tier.classify(20.0, HOLDINGS)
    assert result.action == "觀察"
    assert "MSFT" in result.buy_list


def test_top_tier_buy_size_label():
    result = vix_tier.classify(50.0, HOLDINGS)
    assert result.index == 5
    assert "all in" in (result.buy_size_pct or "")
