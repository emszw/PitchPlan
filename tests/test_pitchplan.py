import numpy as np
import pandas as pd
import pytest

from pitchplan import build_plan, plan_bullets, write_html
from pitchplan import config as C
from pitchplan.data import approx_run_values, assign_regions, count_states
from pitchplan.evaluate import backtest
from pitchplan.stats import shrink
from pitchplan.synthetic import make_demo_hitter, make_demo_pitcher


@pytest.fixture(scope="module")
def demo():
    return make_demo_hitter(), make_demo_pitcher()


def test_regions():
    x = np.array([0.0, -0.6, 1.2, 0.0, 0.0, 0.0])
    z = np.array([0.5, 0.8, 0.5, 1.3, 2.0, -0.1])
    got = assign_regions(x, z, np.full(6, 1.8))
    assert list(got) == ["Heart", "Up-In", "Chase Away", "Chase Up", "Waste", "Chase Down"]


def test_count_states():
    got = count_states([0, 0, 2, 3, 1], [0, 1, 0, 2, 1])
    assert list(got) == ["Even", "Ahead", "Behind", "Two strikes", "Even"]


def test_approx_run_values():
    df = pd.DataFrame({
        "balls": [0, 1, 3], "strikes": [0, 2, 1],
        "description": ["ball", "swinging_strike", "ball"],
        "events": [None, "strikeout", "walk"],
    })
    rv = approx_run_values(df)
    assert rv[0] == pytest.approx(C.COUNT_VALUES[(1, 0)])
    assert rv[1] == pytest.approx(C.EVENT_VALUES["strikeout"] - C.COUNT_VALUES[(1, 2)])
    assert rv[2] > 0


def test_shrink():
    assert shrink(0, 0, 0.3, 50) == pytest.approx(0.3)
    assert shrink(50, 100, 0.3, 50) == pytest.approx((50 + 15) / 150)


def test_demo_plan(demo, tmp_path):
    result = build_plan(*demo, "Demo Hitter", "Demo Pitcher")
    assert list(result.arsenal.index) == ["FF", "SL", "CH"]
    for c in C.COUNT_STATES:
        recs = result.recs[c]
        assert not recs.empty
        assert recs["feasible"].all()
        assert recs["region"].isin(C.ALLOWED_REGIONS[c]).all()
    # The demo hitter was built to crush fastballs middle-in; the plan should say avoid it.
    assert ("FF", "Mid-In") in set(zip(result.avoid["pitch"], result.avoid["region"]))
    for lang in ("en", "es"):
        assert len(plan_bullets(result, lang)) >= 4
        assert write_html(result, tmp_path / f"r_{lang}.html", lang).stat().st_size > 10_000


def test_backtest(demo):
    bt = backtest(*demo)
    assert bt["n_f"] > 0 and bt["n_o"] > 0
    assert bt["lo"] <= bt["diff"] <= bt["hi"]
