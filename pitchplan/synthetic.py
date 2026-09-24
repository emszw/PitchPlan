"""Synthetic Statcast-style data so the project runs without a network.

The demo hitter has deliberately built-in tendencies (he chases and misses
breaking balls down and away, chases elevated fastballs, and punishes
fastballs middle-in). A good pitch plan should rediscover them, which makes
the demo a useful sanity check for the whole pipeline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

# pitch_type -> (velocity mph, arm-side break in, induced vertical break in)
LEAGUE_SHAPES = {
    "FF": (94.0, 8.0, 16.0), "SI": (93.0, 15.0, 8.0), "FC": (89.0, -2.0, 9.0),
    "SL": (85.0, -5.0, 2.0), "ST": (82.0, -14.0, 1.0), "CU": (79.0, -8.0, -12.0),
    "CH": (85.0, 14.0, 5.0), "FS": (86.0, 10.0, 2.0),
}
LEAGUE_ARSENALS = [
    {"FF": 0.50, "SL": 0.30, "CH": 0.20},
    {"SI": 0.45, "ST": 0.35, "CH": 0.20},
    {"FF": 0.45, "CU": 0.30, "FC": 0.25},
    {"FF": 0.55, "FS": 0.25, "SL": 0.20},
    {"SI": 0.40, "FC": 0.25, "CU": 0.20, "CH": 0.15},
]
DEMO_PITCHER_SHAPES = {"FF": (95.5, 7.0, 18.0), "SL": (86.5, -3.0, 3.0), "CH": (86.0, 15.0, 6.0)}
DEMO_PITCHER_ARSENAL = {"FF": 0.50, "SL": 0.32, "CH": 0.18}


def _demo_hitter_adjust(pt, group, x, z):
    """(swing, whiff, xwOBA-on-contact) adjustments for the demo hitter."""
    ds = dw = dx = 0.0
    if group in ("Breaking", "Offspeed") and x > 0.25 and z < 0.4:
        ds, dw, dx = ds + 0.06, dw + 0.20, dx - 0.12
    if group == "Fastball" and z > 0.72:
        ds, dw, dx = ds + 0.12, dw + 0.12, dx - 0.06
    if group == "Fastball" and x < 0.1 and 0.25 < z < 0.75:
        dw, dx = dw - 0.10, dx + 0.22
    if group == "Offspeed" and z > 0.45:
        dx += 0.12
    return ds, dw, dx


def _demo_pitcher_adjust(pt, group, x, z):
    """Where the demo pitcher's stuff plays best against generic hitters."""
    dw = dx = 0.0
    if pt == "FF" and z > 0.65:
        dw += 0.09
    if pt == "FF" and 0.3 < z < 0.65 and abs(x) < 0.3:
        dx += 0.08
    if pt == "SL" and z < 0.35 and x > 0:
        dw, dx = dw + 0.10, dx - 0.05
    if pt == "CH" and z < 0.35:
        dw += 0.07
    return 0.0, dw, dx


def _choose_pitch(rng, arsenal, b, s):
    types = list(arsenal)
    w = np.array([arsenal[t] for t in types], dtype=float)
    groups = [C.PITCH_GROUPS[t] for t in types]
    if s == 2:
        w *= [1.5 if g != "Fastball" else 1.0 for g in groups]
    if b > s:
        w *= [1.6 if g == "Fastball" else 1.0 for g in groups]
    return types[rng.choice(len(types), p=w / w.sum())]


def _target(rng, group, same_side, b, s):
    if group == "Fastball":
        options = [(0.35, 0.85), (-0.35, 0.70), (0.40, 0.35), (0.0, 0.5)]
        tx, tz = options[rng.choice(4, p=[0.35, 0.2, 0.3, 0.15])]
    elif group == "Breaking":  # away to same-side hitters, back foot otherwise
        tx, tz = (0.45 if same_side else -0.45), 0.05
    else:                      # changeups fade away from opposite-side hitters
        tx, tz = (-0.35 if same_side else 0.35), 0.10
    if b > s:                  # behind: aim closer to the middle
        tx, tz = tx * 0.6, 0.5 + (tz - 0.5) * 0.6
    if s == 2 and group != "Fastball":
        tz -= 0.15
    return rng.normal(tx, 0.5), rng.normal(tz, 0.28)


def _outcome(rng, pt, group, x, z, b, s, adjust):
    half = C.ZONE_HALF_WIDTH_FT
    dist = max(abs(x) - half, (z - 1) * 1.8, -z * 1.8, 0.0)
    in_zone = dist == 0
    ds, dw, dx = adjust(pt, group, x, z)

    if in_zone:  # hitters swing most at pitches near the middle
        edge = min(half - abs(x), z * 1.8, (1 - z) * 1.8)
        p_swing = 0.55 + min(edge, 0.5) * 0.6
    else:
        p_swing = 0.55 * np.exp(-dist / 0.45)
    if b == 0 and s == 0:
        p_swing -= 0.12
    if s == 2:
        p_swing += 0.20 if in_zone else 0.10
    if b == 3 and s == 0:
        p_swing = 0.05
    if rng.random() >= np.clip(p_swing + ds, 0.01, 0.97):
        return ("called_strike" if in_zone else "ball"), None, np.nan

    p_whiff = {"Fastball": 0.17, "Breaking": 0.31, "Offspeed": 0.29}[group]
    p_whiff += (0.0 if in_zone else 0.15) + dw
    if rng.random() < np.clip(p_whiff, 0.02, 0.9):
        return "swinging_strike", None, np.nan
    if rng.random() < 0.45 + (0.0 if in_zone else 0.12):
        return "foul", None, np.nan

    xw = float(np.clip((0.37 if in_zone else 0.25) + dx + rng.normal(0, 0.18), 0.0, 1.9))
    if rng.random() < np.clip(0.8 * xw, 0.03, 0.9):
        p_hr = np.clip((xw - 0.45) * 0.9, 0, 0.7)
        u = rng.random()
        event = ("home_run" if u < p_hr else "double" if u < p_hr + 0.20
                 else "triple" if u < p_hr + 0.22 else "single")
    else:
        event = "field_out"
    return "hit_into_play", event, xw


def _simulate_pa(rng, stand, hand, arsenal, shapes, adjust, game_date, offset):
    rows, b, s = [], 0, 0
    same_side = stand == hand
    for pitch_number in range(1, 15):
        pt = _choose_pitch(rng, arsenal, b, s)
        v, hb, ivb = np.array(shapes[pt]) + offset + rng.normal(0, [0.8, 1.5, 1.5])
        x_rel, z_norm = _target(rng, C.PITCH_GROUPS[pt], same_side, b, s)
        sz_top, sz_bot = 3.4 + rng.normal(0, 0.05), 1.6 + rng.normal(0, 0.04)
        desc, event, xw = _outcome(rng, pt, C.PITCH_GROUPS[pt], x_rel, z_norm, b, s, adjust)

        if desc == "ball" and b == 3:
            event = "walk"
        elif desc in ("called_strike", "swinging_strike") and s == 2:
            event = "strikeout"
        rows.append({
            "game_date": game_date, "pitch_type": pt, "release_speed": round(v, 1),
            "pfx_x": (-hb if hand == "R" else hb) / 12, "pfx_z": ivb / 12,
            "plate_x": x_rel if stand == "R" else -x_rel,
            "plate_z": sz_bot + z_norm * (sz_top - sz_bot),
            "sz_top": sz_top, "sz_bot": sz_bot, "stand": stand, "p_throws": hand,
            "balls": b, "strikes": s, "pitch_number": pitch_number,
            "description": desc, "events": event, "estimated_woba_using_speedangle": xw,
        })
        if event is not None:
            break
        if desc == "ball":
            b += 1
        elif desc in ("called_strike", "swinging_strike") or (desc == "foul" and s < 2):
            s += 1
    return rows


def _dates(rng, n):
    days = pd.date_range("2025-03-27", "2025-09-28", freq="D")
    return np.sort(rng.choice(days, size=n))


def make_demo_hitter(seed: int = 7, n_pa: int = 650) -> pd.DataFrame:
    """A right-handed hitter facing a league-like mix of pitchers."""
    rng = np.random.default_rng(seed)
    rows = []
    for date in _dates(rng, n_pa):
        hand = "R" if rng.random() < 0.68 else "L"
        arsenal = LEAGUE_ARSENALS[rng.integers(len(LEAGUE_ARSENALS))]
        offset = rng.normal(0, [1.0, 1.5, 1.5])
        rows += _simulate_pa(rng, "R", hand, arsenal, LEAGUE_SHAPES,
                             _demo_hitter_adjust, date, offset)
    return pd.DataFrame(rows)


def make_demo_pitcher(seed: int = 11, n_pa: int = 750) -> pd.DataFrame:
    """A right-handed pitcher with a riding fastball, gyro slider and changeup."""
    rng = np.random.default_rng(seed)
    rows = []
    for date in _dates(rng, n_pa):
        stand = "R" if rng.random() < 0.5 else "L"
        rows += _simulate_pa(rng, stand, "R", DEMO_PITCHER_ARSENAL, DEMO_PITCHER_SHAPES,
                             _demo_pitcher_adjust, date, np.zeros(3))
    return pd.DataFrame(rows)
