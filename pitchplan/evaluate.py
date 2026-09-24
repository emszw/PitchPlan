"""Backtest: build the plan on early games, check it on later ones."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import prepare
from .matchup import match_to_arsenal
from .pipeline import build_plan


def backtest(hitter_raw: pd.DataFrame, pitcher_raw: pd.DataFrame, split: float = 0.5,
             top_n: int = 3, n_boot: int = 2000, seed: int = 0) -> dict:
    """Compare hitter run value on later pitches that did vs. didn't follow the plan.

    Only pitches similar to the pitcher's arsenal count, so the comparison is
    "pitches like ours, thrown where the plan said" vs. "pitches like ours,
    thrown elsewhere". Run values are from the hitter's side (lower is better).
    """
    if "game_date" not in hitter_raw:
        raise ValueError("Backtesting needs a game_date column.")
    dates = pd.to_datetime(hitter_raw["game_date"])
    cutoff = dates.quantile(split)
    train, test_raw = hitter_raw[dates <= cutoff], hitter_raw[dates > cutoff]
    plan = build_plan(train, pitcher_raw, top_n=top_n)

    test = prepare(test_raw)
    test = test[test["stand"] == plan.hitter_stand]
    test, _ = match_to_arsenal(test, plan.arsenal, plan.pitcher_hand)
    test = test[test["match"].notna()]
    recs = {(r["pitch"], r["region"], c) for c, d in plan.recs.items() for _, r in d.iterrows()}
    followed = np.array([(m, r, c) in recs for m, r, c
                         in zip(test["match"], test["region"], test["count_state"])], dtype=bool)

    f_rv, o_rv = test.loc[followed, "rv"].to_numpy(), test.loc[~followed, "rv"].to_numpy()
    if len(f_rv) < 20 or len(o_rv) < 20:
        raise ValueError("Not enough later pitches to backtest the plan.")
    rng = np.random.default_rng(seed)
    diffs = [(rng.choice(o_rv, len(o_rv)).mean() - rng.choice(f_rv, len(f_rv)).mean()) * 100
             for _ in range(n_boot)]
    return {
        "cutoff": cutoff.date().isoformat(), "n_test": int(len(test)),
        "n_f": int(len(f_rv)), "n_o": int(len(o_rv)),
        "f_rv": f_rv.mean() * 100, "o_rv": o_rv.mean() * 100,
        "diff": (o_rv.mean() - f_rv.mean()) * 100,
        "lo": float(np.percentile(diffs, 2.5)), "hi": float(np.percentile(diffs, 97.5)),
    }
