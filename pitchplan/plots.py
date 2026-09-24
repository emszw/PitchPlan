"""Figures for the report (matplotlib, returned as PNG bytes)."""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import Normalize, TwoSlopeNorm, to_rgb  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from . import config as C  # noqa: E402
from .i18n import GROUP_LABELS, pitch_name, t  # noqa: E402
from .profile import location_grid  # noqa: E402

PITCH_COLORS = ["#d1495b", "#2e86ab", "#edae49", "#66a182", "#8d6cab", "#4f5d75"]
GRAY = "#d9d9d9"


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def _cells(stand: str) -> dict:
    """Rectangle (x, y, w, h) for every region, drawn from the catcher's view.

    For a right-handed hitter, inside is on the catcher's left; for a lefty it
    is on the right.
    """
    cols = {"In": 0, "Middle": 1, "Away": 2} if stand == "R" else {"In": 2, "Middle": 1, "Away": 0}
    rows = {"Down": 0, "Mid": 1, "Up": 2}
    cells = {}
    for r in C.ZONE_REGIONS:
        v, h = ("Mid", "Middle") if r == "Heart" else r.split("-")
        cells[r] = (cols[h], rows[v], 1, 1)
    in_left = stand == "R"
    cells["Chase Up"] = (0, 3.12, 3, 0.6)
    cells["Chase Down"] = (0, -0.72, 3, 0.6)
    cells["Chase In"] = (-0.72 if in_left else 3.12, 0, 0.6, 3)
    cells["Chase Away"] = (3.12 if in_left else -0.72, 0, 0.6, 3)
    return cells


def draw_grid(ax, stand, values, notes, cmap, norm, fmt, lang, gray=frozenset(), title=""):
    for region, (x, y, w, h) in _cells(stand).items():
        val = values.get(region)
        color = GRAY if (region in gray or val is None or np.isnan(val)) else cmap(norm(val))
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="white", lw=1.5))
        r, g, b = to_rgb(color)
        ink = "white" if 0.299 * r + 0.587 * g + 0.114 * b < 0.5 else "#222"
        if val is not None and not np.isnan(val) and region not in gray:
            ax.text(x + w / 2, y + h / 2 + (0.08 if h >= 1 else 0.0), fmt(val),
                    ha="center", va="center", fontsize=8.5 if w >= 1 else 6.5,
                    fontweight="bold", color=ink, rotation=0 if w >= 1 or len(fmt(val)) <= 3 else 90)
        note = notes.get(region)
        if note is not None and h >= 1 and w >= 1:
            ax.text(x + w / 2, y + h / 2 - 0.25, note, ha="center", va="center", fontsize=6.5, color=ink)
    ax.add_patch(Rectangle((0, 0), 3, 3, fill=False, edgecolor="#222", lw=1.8))
    ax.set_xlim(-0.8, 3.8)
    ax.set_ylim(-0.8, 3.8)
    ax.set_aspect("equal")
    ax.set_xticks([-0.42, 3.42])
    labels = [t("in", lang), t("away", lang)] if stand == "R" else [t("away", lang), t("in", lang)]
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticks([])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=10, fontweight="bold")


def where_to_throw(result, lang: str) -> bytes:
    sc = result.scores.drop_duplicates(["pitch", "region"])
    pitches = list(result.arsenal.index)
    vmax = max(3.0, float(np.nanpercentile(np.abs(sc["region_runs_saved_100"]), 95)))
    norm, cmap = TwoSlopeNorm(0, -vmax, vmax), plt.get_cmap("RdYlGn")

    fig, axes = plt.subplots(1, len(pitches), figsize=(3.2 * len(pitches), 3.6))
    axes = np.atleast_1d(axes)
    for ax, p in zip(axes, pitches):
        d = sc[sc["pitch"] == p].set_index("region")
        vals = d["region_runs_saved_100"].to_dict()
        notes = {r: f"n={int(n)}" for r, n in d["h_pitches"].items()}
        gray = frozenset(d.index[~d["feasible"]])
        usage = result.arsenal.loc[p, "usage"]
        title = f"{pitch_name(p, lang, capital=True)} ({t('usage', lang)} {usage:.0%})"
        draw_grid(ax, result.hitter_stand, vals, notes, cmap, norm,
                  lambda v: f"{v:+.1f}", lang, gray, title)
    fig.suptitle(t("catcher_view", lang), fontsize=8, color="#666", y=0.06)
    return _png(fig)


def hitter_locations(result, lang: str) -> bytes:
    grid = location_grid(result.hitter_pool)
    groups = [g for g in C.GROUP_ORDER if g in grid]
    fig, axes = plt.subplots(2, len(groups), figsize=(3.2 * len(groups), 7.0), squeeze=False)
    whiff_norm = Normalize(0.05, 0.50)
    xw_norm = TwoSlopeNorm(C.LEAGUE_REFS["xwoba_con"], 0.20, 0.60)
    for j, g in enumerate(groups):
        w = grid[g]["whiff"]
        draw_grid(axes[0, j], result.hitter_stand, {r: v for r, (v, _) in w.items()},
                  {r: f"{n} sw" for r, (_, n) in w.items()}, plt.get_cmap("Greens"), whiff_norm,
                  lambda v: f"{v:.0%}", lang,
                  title=f"{GROUP_LABELS[lang][g]} · {t('whiff_title', lang)}")
        x = grid[g]["xwoba"]
        draw_grid(axes[1, j], result.hitter_stand, {r: v for r, (v, _) in x.items()},
                  {r: f"{n} bip" for r, (_, n) in x.items()}, plt.get_cmap("RdYlGn_r"), xw_norm,
                  lambda v: f"{v:.3f}".lstrip("0"), lang,
                  title=f"{GROUP_LABELS[lang][g]} · {t('xwoba_title', lang)}")
    fig.suptitle(t("catcher_view", lang), fontsize=8, color="#666", y=0.02)
    return _png(fig)


def matchup_shapes(result, lang: str) -> bytes:
    pool, ars = result.hitter_pool, result.arsenal
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    un = pool[pool["match"].isna()]
    ax.scatter(un["hb_arm"], un["ivb"], s=6, c="#bbbbbb", alpha=0.5, label=t("unmatched", lang))
    for color, (p, row) in zip(PITCH_COLORS, ars.iterrows()):
        m = pool[pool["match"] == p]
        ax.scatter(m["hb_arm"], m["ivb"], s=8, color=color, alpha=0.45)
        ax.scatter(row["hb_arm"], row["ivb"], s=260, color=color, edgecolor="black", lw=1.5, zorder=5,
                   marker="*", label=f"{pitch_name(p, lang, capital=True)} ({row['velo']:.1f} mph)")
    ax.axhline(0, color="#999", lw=0.8)
    ax.axvline(0, color="#999", lw=0.8)
    ax.set_xlabel(t("arm_side", lang))
    ax.set_ylabel(t("ivb", lang))
    ax.legend(fontsize=8, loc="upper left", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    return _png(fig)
