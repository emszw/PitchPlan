"""The matchup engine: our pitcher's arsenal vs. this hitter.

Steps
1. Summarise the pitcher's arsenal (average shape of each pitch).
2. Find the pitches the hitter has seen that *move like* each of those pitches.
3. Estimate run value for every pitch x location x count cell, for both the
   hitter (vs. similar pitches) and the pitcher (his own results), using
   hierarchical shrinkage so thin samples lean on broader estimates.
4. Blend the two, filter to locations the pitcher can actually hit, and rank.

Run values are from the batter's perspective (positive = good for the hitter),
so the report flips the sign and shows "runs saved per 100 pitches".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .stats import shrink


def build_arsenal(p: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    hand = p["p_throws"].mode().iloc[0]
    ars = (p.groupby("pitch_type")
             .agg(n=("release_speed", "size"), velo=("release_speed", "mean"),
                  hb_arm=("hb_arm", "mean"), ivb=("ivb", "mean")))
    ars["usage"] = ars["n"] / ars["n"].sum()
    ars = ars[(ars["n"] >= C.MIN_ARSENAL_PITCHES) & (ars["usage"] >= C.MIN_ARSENAL_SHARE)]
    if ars.empty:
        raise ValueError("Pitcher has no pitch type with enough data to build an arsenal.")
    return ars.sort_values("usage", ascending=False), hand


def match_to_arsenal(h: pd.DataFrame, ars: pd.DataFrame, hand: str) -> tuple[pd.DataFrame, bool]:
    """Tag each pitch the hitter saw with the arsenal pitch it most resembles.

    Uses same-handed pitchers only when there is enough data, because a slider
    from a lefty and a righty attacks the hitter from opposite directions.
    """
    same = h[h["p_throws"] == hand]
    same_hand = len(same) >= C.MIN_SAME_HAND_PITCHES
    pool = (same if same_hand else h).copy()

    scales = np.array(C.SIMILARITY_SCALES)
    feats = pool[["release_speed", "hb_arm", "ivb"]].to_numpy() / scales
    cents = ars[["velo", "hb_arm", "ivb"]].to_numpy() / scales
    dist = np.sqrt(((feats[:, None, :] - cents[None, :, :]) ** 2).sum(axis=2))
    nearest = dist.argmin(axis=1)
    pool["match_dist"] = dist.min(axis=1)
    pool["match"] = np.where(pool["match_dist"] <= C.SIMILARITY_MAX_DIST,
                             ars.index.to_numpy()[nearest], None)
    return pool, same_hand


def _lookup(stats: pd.DataFrame, key) -> tuple[float, int]:
    try:
        row = stats.loc[key]
        return float(row["sum"]), int(row["count"])
    except KeyError:
        return 0.0, 0


def hierarchical_rv(base: pd.DataFrame, keyed: pd.DataFrame, key: str,
                    pitches: list[str], use_groups: bool = False) -> pd.DataFrame:
    """Shrunk run value per pitch x region x count.

    Hierarchy: overall -> pitch -> pitch x region -> pitch x region x count,
    where the count level's prior is the region estimate plus a count offset
    (how much better/worse this player does in that count state overall).

    With use_groups=True (the hitter side) two extra layers borrow strength
    from *every* pitch in the same group, not only the similar ones:
    overall -> group -> group x region, and the similar-pitch x region prior
    is group x region plus how the similar pitch differs from its group.

    `base` sets the overall mean, count offsets and group layers; `keyed`
    holds the pitches labelled with `key` (arsenal pitch type).
    """
    K = C.SHRINK_K
    overall = float(base["rv"].mean()) if len(base) else 0.0
    by_count = base.groupby("count_state")["rv"].agg(["sum", "count"])
    offset = {c: shrink(*_lookup(by_count, c), overall, K["count"]) - overall
              for c in C.COUNT_STATES}

    by_pitch = keyed.groupby(key)["rv"].agg(["sum", "count"])
    by_region = keyed.groupby([key, "region"])["rv"].agg(["sum", "count"])
    by_cell = keyed.groupby([key, "region", "count_state"])["rv"].agg(["sum", "count"])
    by_group = base.groupby("pitch_group")["rv"].agg(["sum", "count"])
    by_group_region = base.groupby(["pitch_group", "region"])["rv"].agg(["sum", "count"])

    rows = []
    for p in pitches:
        s, n = _lookup(by_pitch, p)
        g = C.PITCH_GROUPS[p]
        g_est = shrink(*_lookup(by_group, g), overall, K["pitch"]) if use_groups else overall
        p_est = shrink(s, n, g_est, K["pitch"])
        for r in C.RECOMMENDABLE_REGIONS:
            if use_groups:
                gr_est = shrink(*_lookup(by_group_region, (g, r)), g_est, K["region"])
                prior = gr_est + (p_est - g_est)
            else:
                prior = p_est
            s2, n2 = _lookup(by_region, (p, r))
            r_est = shrink(s2, n2, prior, K["region"])
            for c in C.COUNT_STATES:
                s3, n3 = _lookup(by_cell, (p, r, c))
                est = shrink(s3, n3, r_est + offset[c], K["cell"])
                rows.append({"pitch": p, "region": r, "count_state": c,
                             "est": est, "n": n3, "region_est": r_est, "region_n": n2,
                             "pitch_est": p_est, "pitch_n": n})
    return pd.DataFrame(rows)


def hitter_cell_stats(matched: pd.DataFrame) -> pd.DataFrame:
    """Descriptive stats for the hitter vs. similar pitches, by pitch x region."""
    g = matched.groupby(["match", "region"])
    s = g.agg(h_pitches=("rv", "size"), h_swings=("is_swing", "sum"),
              h_whiffs=("is_whiff", "sum"), h_bip=("xwoba_con", "count"),
              h_xwoba_con=("xwoba_con", "mean")).reset_index()
    s["h_whiff_rate"] = s["h_whiffs"] / s["h_swings"].replace(0, np.nan)
    return s.rename(columns={"match": "pitch"})


def score_matchup(pool: pd.DataFrame, p_side: pd.DataFrame, ars: pd.DataFrame) -> pd.DataFrame:
    pitches = list(ars.index)
    matched = pool[pool["match"].notna()]
    hit = hierarchical_rv(pool, matched, "match", pitches, use_groups=True)
    pit = hierarchical_rv(p_side, p_side[p_side["pitch_type"].isin(pitches)], "pitch_type", pitches)
    df = hit.merge(pit, on=["pitch", "region", "count_state"], suffixes=("_h", "_p"))

    counts = p_side.groupby(["pitch_type", "region"]).size()
    totals = p_side.groupby("pitch_type").size()
    df["usage_share"] = [counts.get((p, r), 0) / totals.get(p, np.inf)
                         for p, r in zip(df["pitch"], df["region"])]
    df["feasible"] = df["usage_share"] >= C.MIN_USAGE_SHARE

    wh, wp = C.WEIGHTS["hitter"], C.WEIGHTS["pitcher"]
    df["runs_saved_100"] = -(wh * df["est_h"] + wp * df["est_p"]) * 100
    df["region_runs_saved_100"] = -(wh * df["region_est_h"] + wp * df["region_est_p"]) * 100
    df = df.merge(hitter_cell_stats(matched), on=["pitch", "region"], how="left")
    fill = {"h_pitches": 0, "h_swings": 0, "h_whiffs": 0, "h_bip": 0}
    return df.fillna(fill)


def recommend(scores: pd.DataFrame, top_n: int = 3) -> dict[str, pd.DataFrame]:
    """Best feasible options for each count state, kept varied across pitches."""
    recs = {}
    for c in C.COUNT_STATES:
        sub = scores[(scores["count_state"] == c) & scores["feasible"]
                     & scores["region"].isin(C.ALLOWED_REGIONS[c])]
        picked, per_pitch = [], {}
        for idx, row in sub.sort_values("runs_saved_100", ascending=False).iterrows():
            if per_pitch.get(row["pitch"], 0) >= C.MAX_OPTIONS_PER_PITCH:
                continue
            picked.append(idx)
            per_pitch[row["pitch"]] = per_pitch.get(row["pitch"], 0) + 1
            if len(picked) == top_n:
                break
        recs[c] = sub.loc[picked]
    return recs


def avoid(scores: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    """Worst feasible pitch x location combos (across all counts)."""
    regional = scores.drop_duplicates(["pitch", "region"])
    regional = regional[regional["feasible"]
                        & (regional["h_pitches"] >= C.MIN_SAMPLE_FOR_AVOID)
                        & (regional["region_runs_saved_100"] < C.AVOID_THRESHOLD)]
    return regional.sort_values("region_runs_saved_100").head(n)
