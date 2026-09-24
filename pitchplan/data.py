"""Loading raw Statcast data and turning it into analysis-ready features."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

REQUIRED_COLUMNS = [
    "pitch_type", "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z",
    "stand", "p_throws", "balls", "strikes", "description",
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def lookup_player_id(name: str) -> int:
    """Turn 'Last, First', 'First Last', or an MLBAM id string into an id."""
    name = str(name).strip()
    if name.isdigit():
        return int(name)
    from pybaseball import playerid_lookup

    if "," in name:
        last, first = (p.strip() for p in name.split(",", 1))
    else:
        parts = name.split()
        if len(parts) < 2:
            raise ValueError(f"Use 'First Last' or 'Last, First' (got {name!r}).")
        first, last = parts[0], " ".join(parts[1:])
    res = playerid_lookup(last, first).dropna(subset=["key_mlbam"])
    if res.empty:
        raise ValueError(f"No MLBAM id found for {name!r}. Try passing the numeric id.")
    res = res.sort_values("mlb_played_last", ascending=False)  # most recent player
    return int(res.iloc[0]["key_mlbam"])


def fetch_statcast(player: str, start: str, end: str, role: str) -> pd.DataFrame:
    """Download pitch-level Statcast data with pybaseball (role: batter|pitcher)."""
    try:
        import pybaseball
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("pybaseball is required: pip install -r requirements.txt") from exc
    pybaseball.cache.enable()
    pid = lookup_player_id(player)
    fetch = pybaseball.statcast_batter if role == "batter" else pybaseball.statcast_pitcher
    df = fetch(start, end, player_id=pid)
    if df is None or len(df) == 0:
        raise ValueError(f"No Statcast data for {player} between {start} and {end}.")
    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def assign_regions(x_rel, z_norm, height) -> np.ndarray:
    """Label each pitch with a location region from the batter's point of view.

    x_rel:  horizontal location in feet, negative = inside, positive = away.
    z_norm: 0 at the bottom of the zone, 1 at the top.
    height: zone height in feet (used to measure distance above/below).
    """
    x_rel, z_norm, height = map(np.asarray, (x_rel, z_norm, height))
    half = C.ZONE_HALF_WIDTH_FT

    horiz = np.where(x_rel < -half / 3, "In", np.where(x_rel > half / 3, "Away", "Middle"))
    vert = np.where(z_norm > 2 / 3, "Up", np.where(z_norm < 1 / 3, "Down", "Mid"))
    zone = np.char.add(np.char.add(vert.astype(str), "-"), horiz.astype(str))
    zone = np.where(zone == "Mid-Middle", "Heart", zone)

    over_x = np.abs(x_rel) - half
    over_up = (z_norm - 1) * height
    over_down = -z_norm * height
    in_zone = (over_x <= 0) & (over_up <= 0) & (over_down <= 0)
    waste = (over_x > C.WASTE_MARGIN_FT) | (over_up > C.WASTE_MARGIN_FT) | (over_down > C.WASTE_MARGIN_FT)

    horiz_dir = np.where(x_rel < 0, "Chase In", "Chase Away")
    vert_dir = np.where(over_up > over_down, "Chase Up", "Chase Down")
    chase = np.where(over_x >= np.maximum(over_up, over_down), horiz_dir, vert_dir)

    return np.where(in_zone, zone, np.where(waste, "Waste", chase)).astype(object)


def count_states(balls, strikes) -> np.ndarray:
    b, s = np.asarray(balls), np.asarray(strikes)
    return np.select(
        [s == 2, s > b, b > s], ["Two strikes", "Ahead", "Behind"], default="Even"
    ).astype(object)


def _after_value(b: int, s: int, desc: str, event) -> float:
    if isinstance(event, str) and event in C.EVENT_VALUES:
        return C.EVENT_VALUES[event]
    if desc in C.IN_PLAY_DESCRIPTIONS:
        return C.IN_PLAY_OUT_VALUE
    if desc == "hit_by_pitch":
        return C.EVENT_VALUES["hit_by_pitch"]
    if desc in C.BALL_DESCRIPTIONS:
        return C.EVENT_VALUES["walk"] if b == 3 else C.COUNT_VALUES[(b + 1, s)]
    if (desc in C.CALLED_STRIKE_DESCRIPTIONS or desc in C.WHIFF_DESCRIPTIONS
            or desc in ("bunt_foul_tip", "foul_bunt")):
        return C.EVENT_VALUES["strikeout"] if s == 2 else C.COUNT_VALUES[(b, s + 1)]
    if desc in C.FOUL_DESCRIPTIONS:
        return C.COUNT_VALUES[(b, min(s + 1, 2))]
    return C.COUNT_VALUES[(b, s)]


def approx_run_values(df: pd.DataFrame) -> np.ndarray:
    """Rough per-pitch run value from count changes and outcomes."""
    events = df["events"] if "events" in df else pd.Series([None] * len(df), index=df.index)
    out = np.empty(len(df))
    rows = zip(df["balls"], df["strikes"], df["description"].astype(str), events)
    for i, (b, s, d, e) in enumerate(rows):
        out[i] = _after_value(int(b), int(s), d, e) - C.COUNT_VALUES[(int(b), int(s))]
    return out


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean raw Statcast rows and add every feature the rest of the code uses."""
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Data is missing required columns: {missing}")

    df = raw[raw["pitch_type"].isin(C.PITCH_GROUPS.keys())]
    df = df.dropna(subset=["release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z"]).copy()
    df = df.reset_index(drop=True)

    for col, default in (("sz_top", C.DEFAULT_SZ_TOP), ("sz_bot", C.DEFAULT_SZ_BOT)):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default) if col in df else default
    bad = (df["sz_top"] - df["sz_bot"]) < 1.0
    df.loc[bad, "sz_top"], df.loc[bad, "sz_bot"] = C.DEFAULT_SZ_TOP, C.DEFAULT_SZ_BOT

    df["balls"] = df["balls"].astype(int).clip(0, 3)
    df["strikes"] = df["strikes"].astype(int).clip(0, 2)
    df["pitch_group"] = df["pitch_type"].map(C.PITCH_GROUPS)

    # Movement in inches, horizontal break mirrored so + is always arm side.
    df["ivb"] = df["pfx_z"] * 12
    df["hb_arm"] = np.where(df["p_throws"] == "R", -df["pfx_x"], df["pfx_x"]) * 12

    # Location relative to the batter: + is away, - is inside.
    df["x_rel"] = np.where(df["stand"] == "R", df["plate_x"], -df["plate_x"])
    height = df["sz_top"] - df["sz_bot"]
    df["z_norm"] = (df["plate_z"] - df["sz_bot"]) / height
    df["region"] = assign_regions(df["x_rel"], df["z_norm"], height)
    df["in_zone"] = df["region"].isin(C.ZONE_REGIONS)

    desc = df["description"].astype(str)
    df["is_swing"] = desc.isin(C.SWING_DESCRIPTIONS)
    df["is_whiff"] = desc.isin(C.WHIFF_DESCRIPTIONS)
    df["is_in_play"] = desc.isin(C.IN_PLAY_DESCRIPTIONS)
    df["count_state"] = count_states(df["balls"], df["strikes"])

    approx = approx_run_values(df)
    if "delta_run_exp" in df and df["delta_run_exp"].notna().any():
        df["rv"] = pd.to_numeric(df["delta_run_exp"], errors="coerce").fillna(pd.Series(approx))
        df.attrs["rv_source"] = "statcast"
    else:
        df["rv"] = approx
        df.attrs["rv_source"] = "approx"

    xw = (pd.to_numeric(df["estimated_woba_using_speedangle"], errors="coerce")
          if "estimated_woba_using_speedangle" in df else np.nan)
    df["xwoba_con"] = np.where(df["is_in_play"], xw, np.nan)

    if "game_date" in df:
        df["game_date"] = pd.to_datetime(df["game_date"])
    return df
