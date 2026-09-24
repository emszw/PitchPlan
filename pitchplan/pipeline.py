"""One function that runs the whole analysis."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import config as C
from .data import prepare
from .matchup import avoid, build_arsenal, match_to_arsenal, recommend, score_matchup
from .profile import group_table, tendencies


@dataclass
class PlanResult:
    hitter_name: str
    pitcher_name: str
    hitter_stand: str
    pitcher_hand: str
    switch_hitter: bool
    arsenal: pd.DataFrame
    hitter_pool: pd.DataFrame          # hitter pitches used (with `match` column)
    pitcher_side: pd.DataFrame         # pitcher pitches used
    same_hand_pool: bool
    same_stand_pool: bool
    scores: pd.DataFrame
    recs: dict
    avoid: pd.DataFrame
    tendencies: dict
    groups: pd.DataFrame
    rv_source: str
    backtest: dict | None = field(default=None)


def build_plan(hitter_raw: pd.DataFrame, pitcher_raw: pd.DataFrame,
               hitter_name: str = "Hitter", pitcher_name: str = "Pitcher",
               top_n: int = 3) -> PlanResult:
    h, p = prepare(hitter_raw), prepare(pitcher_raw)
    if h.empty or p.empty:
        raise ValueError("Not enough usable pitches after cleaning the data.")
    ars, hand = build_arsenal(p)

    # A switch hitter will bat from the side opposite the pitcher's hand.
    stands = h["stand"].value_counts()
    switch = len(stands) > 1 and stands.min() >= 50
    stand = ("L" if hand == "R" else "R") if switch else stands.index[0]
    h = h[h["stand"] == stand]

    p_side = p[p["stand"] == stand]
    same_stand = len(p_side) >= C.MIN_SAME_STAND_PITCHES
    if not same_stand:
        p_side = p

    pool, same_hand = match_to_arsenal(h, ars, hand)
    scores = score_matchup(pool, p_side, ars)
    rv_source = "statcast" if "statcast" in (h.attrs.get("rv_source"), p.attrs.get("rv_source")) else "approx"

    return PlanResult(
        hitter_name=hitter_name, pitcher_name=pitcher_name,
        hitter_stand=stand, pitcher_hand=hand, switch_hitter=switch,
        arsenal=ars, hitter_pool=pool, pitcher_side=p_side,
        same_hand_pool=same_hand, same_stand_pool=same_stand,
        scores=scores, recs=recommend(scores, top_n), avoid=avoid(scores),
        tendencies=tendencies(pool), groups=group_table(pool), rv_source=rv_source,
    )
