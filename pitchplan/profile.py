"""Describe what a hitter does: approach, swing-and-miss, and damage."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .stats import ratio, shrink


def tendencies(h: pd.DataFrame) -> dict:
    """Headline approach metrics with their sample sizes."""
    first = (h["balls"] == 0) & (h["strikes"] == 0)
    out_zone, swings = ~h["in_zone"], h["is_swing"]
    bip = h["xwoba_con"].dropna()
    return {
        "pitches": int(len(h)),
        "chase_rate": (ratio(h.loc[out_zone, "is_swing"]), int(out_zone.sum())),
        "zone_swing_rate": (ratio(h.loc[h["in_zone"], "is_swing"]), int(h["in_zone"].sum())),
        "whiff_rate": (ratio(h.loc[swings, "is_whiff"]), int(swings.sum())),
        "first_pitch_swing_rate": (ratio(h.loc[first, "is_swing"]), int(first.sum())),
        "xwoba_con": (float(bip.mean()) if len(bip) else np.nan, int(len(bip))),
    }


def group_table(h: pd.DataFrame) -> pd.DataFrame:
    """Approach and results by pitch group (fastball / breaking / offspeed)."""
    rows = []
    for g in C.GROUP_ORDER:
        d = h[h["pitch_group"] == g]
        if d.empty:
            continue
        oz = d[~d["in_zone"]]
        rows.append({
            "group": g, "pitches": len(d),
            "swing_rate": ratio(d["is_swing"]),
            "chase_rate": ratio(oz["is_swing"]),
            "whiff_rate": ratio(d.loc[d["is_swing"], "is_whiff"]),
            "xwoba_con": d["xwoba_con"].mean(),
            "rv_per_100": d["rv"].mean() * 100,
        })
    return pd.DataFrame(rows)


def location_grid(h: pd.DataFrame, k_whiff: float = 20, k_xw: float = 10) -> dict:
    """Shrunk whiff rate and xwOBA on contact for every group x region.

    Returns {group: {"whiff": {region: (value, swings)},
                     "xwoba": {region: (value, balls_in_play)}}}
    """
    out = {}
    regions = C.RECOMMENDABLE_REGIONS
    for g in C.GROUP_ORDER:
        d = h[h["pitch_group"] == g]
        if d.empty:
            continue
        sw = d[d["is_swing"]]
        base_whiff = sw["is_whiff"].mean() if len(sw) else C.LEAGUE_REFS["whiff_rate"]
        bip = d.dropna(subset=["xwoba_con"])
        base_xw = bip["xwoba_con"].mean() if len(bip) else C.LEAGUE_REFS["xwoba_con"]
        whiff, xw = {}, {}
        for r in regions:
            s_r = sw[sw["region"] == r]
            whiff[r] = (shrink(s_r["is_whiff"].sum(), len(s_r), base_whiff, k_whiff), len(s_r))
            b_r = bip[bip["region"] == r]
            xw[r] = (shrink(b_r["xwoba_con"].sum(), len(b_r), base_xw, k_xw), len(b_r))
        out[g] = {"whiff": whiff, "xwoba": xw}
    return out
