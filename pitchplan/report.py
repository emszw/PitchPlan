"""Plain-language plan + a self-contained one-page HTML report."""
from __future__ import annotations

import base64
import html
from pathlib import Path

import numpy as np

from . import config as C
from . import plots
from .i18n import (COUNT_LABELS, GROUP_LABELS, option_phrase, option_short, pct, t, woba)


# ---------------------------------------------------------------------------
# The written plan
# ---------------------------------------------------------------------------
def _top(result, count_state, regions=None):
    df = result.recs.get(count_state)
    if df is None or df.empty:
        return None
    if regions is not None:
        df = df[df["region"].isin(regions)]
    return None if df.empty else df.iloc[0]


def _best_chase(result):
    """Best feasible chase-location option when the pitcher is ahead."""
    sc = result.scores
    sub = sc[(sc["count_state"] == "Ahead") & sc["feasible"] & sc["region"].isin(C.CHASE_REGIONS)]
    return None if sub.empty else sub.sort_values("runs_saved_100", ascending=False).iloc[0]


def plan_bullets(result, lang: str = "en") -> list[str]:
    tend, out = result.tendencies, []
    L = C.LEAGUE_REFS
    opt = lambda row: option_phrase(row["pitch"], row["region"], lang)  # noqa: E731

    even = _top(result, "Even")
    if even is not None:
        fps, n = tend["first_pitch_swing_rate"]
        if n >= 40 and fps <= L["first_pitch_swing_rate"] - 0.08:
            out.append(t("b_first_take", lang).format(rate=pct(fps), opt=opt(even)))
        elif n >= 40 and fps >= L["first_pitch_swing_rate"] + 0.08:
            out.append(t("b_first_ambush", lang).format(rate=pct(fps), opt=opt(even)))
        else:
            out.append(t("b_first_normal", lang).format(opt=opt(even)))

    two = _top(result, "Two strikes")
    if two is not None:
        text = t("b_putaway", lang).format(opt=opt(two))
        if two["h_swings"] >= 10 and not np.isnan(two["h_whiff_rate"]):
            text += t("b_putaway_whiff", lang).format(rate=pct(two["h_whiff_rate"]), n=int(two["h_swings"]))
        out.append(text)

    chase, n = tend["chase_rate"]
    ahead = _top(result, "Ahead")
    if n >= 50 and chase >= L["chase_rate"] + 0.03 and _best_chase(result) is not None:
        out.append(t("b_chase_high", lang).format(rate=pct(chase), opt=opt(_best_chase(result))))
    elif n >= 50 and chase <= L["chase_rate"] - 0.03:
        zone_ahead = _top(result, "Ahead", C.ZONE_REGIONS)
        if zone_ahead is not None:
            out.append(t("b_chase_low", lang).format(rate=pct(chase), opt=opt(zone_ahead)))
    elif ahead is not None:
        out.append(t("b_ahead", lang).format(opt=opt(ahead)))

    behind = _top(result, "Behind")
    if behind is not None:
        out.append(t("b_behind", lang).format(opt=opt(behind)))

    for _, row in result.avoid.iterrows():
        if row["h_bip"] >= 5 and not np.isnan(row["h_xwoba_con"]):
            out.append(t("b_avoid_xw", lang).format(opt=opt(row), xw=woba(row["h_xwoba_con"]),
                                                    n=int(row["h_bip"])))
        else:
            out.append(t("b_avoid_rv", lang).format(opt=opt(row), rv=row["region_runs_saved_100"]))
    return out


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
CSS = """
:root{--ink:#1d2330;--muted:#5b6475;--line:#e3e6ec;--accent:#134a8e;--good:#1e7a46;--bad:#b3261e;--bg:#f6f7f9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.page{max-width:1000px;margin:0 auto;padding:28px 22px 48px}
header{background:var(--accent);color:#fff;border-radius:12px;padding:20px 24px;margin-bottom:18px}
header h1{margin:0;font-size:26px}header p{margin:4px 0 0;opacity:.85;font-size:14px}
section{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 22px;margin-bottom:16px}
h2{font-size:17px;margin:0 0 10px;color:var(--accent)}
ol.plan{margin:0;padding-left:22px}ol.plan li{margin:6px 0;font-size:16px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}
td.num{text-align:right;font-variant-numeric:tabular-nums}.pos{color:var(--good);font-weight:600}.neg{color:var(--bad);font-weight:600}
.note{color:var(--muted);font-size:13px;margin:8px 0 0}.wrap{overflow-x:auto}img{max-width:100%;height:auto;display:block;margin:6px auto}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:760px){.grid2{grid-template-columns:1fr}}
ul.about{margin:0;padding-left:18px;color:var(--muted);font-size:13px}
@media print{body{background:#fff}section,header{break-inside:avoid}}
"""


def _img(png: bytes, alt: str) -> str:
    return f'<img alt="{html.escape(alt)}" src="data:image/png;base64,{base64.b64encode(png).decode()}">'


def _plan_table(result, lang):
    n_opts = max((len(d) for d in result.recs.values()), default=0)
    head = "".join(f"<th>{t('option', lang)} {i + 1}</th>" for i in range(n_opts))
    rows = []
    for c in C.COUNT_STATES:
        cells = []
        for _, r in result.recs[c].iterrows():
            cls = "pos" if r["runs_saved_100"] > 0 else "neg"
            cells.append(f"<td>{html.escape(option_short(r['pitch'], r['region'], lang))} "
                         f"<span class='{cls}'>({r['runs_saved_100']:+.1f})</span></td>")
        cells += ["<td></td>"] * (n_opts - len(cells))
        rows.append(f"<tr><td><b>{COUNT_LABELS[lang][c]}</b></td>{''.join(cells)}</tr>")
    return (f"<div class='wrap'><table><tr><th>{t('count', lang)}</th>{head}</tr>{''.join(rows)}</table></div>"
            f"<p class='note'>{t('runs_saved_note', lang)}</p>")


def _tendency_table(result, lang):
    rows = []
    for key in ["chase_rate", "zone_swing_rate", "whiff_rate", "first_pitch_swing_rate", "xwoba_con"]:
        val, n = result.tendencies[key]
        f = woba if key == "xwoba_con" else pct
        rows.append(f"<tr><td>{t('m_' + key, lang)}</td><td class='num'><b>{f(val)}</b></td>"
                    f"<td class='num'>{f(C.LEAGUE_REFS[key])}</td><td class='num'>{n:,}</td></tr>")
    g_rows = []
    for _, r in result.groups.iterrows():
        g_rows.append(
            f"<tr><td>{GROUP_LABELS[lang][r['group']]}</td><td class='num'>{int(r['pitches']):,}</td>"
            f"<td class='num'>{pct(r['swing_rate'])}</td><td class='num'>{pct(r['chase_rate'])}</td>"
            f"<td class='num'>{pct(r['whiff_rate'])}</td><td class='num'>{woba(r['xwoba_con'])}</td>"
            f"<td class='num'>{r['rv_per_100']:+.1f}</td></tr>")
    return (
        f"<div class='wrap'><table><tr><th>{t('metric', lang)}</th><th>{t('hitter', lang)}</th>"
        f"<th>{t('league', lang)}</th><th>{t('sample', lang)}</th></tr>{''.join(rows)}</table></div>"
        f"<h2 style='margin-top:16px'>{t('by_group', lang)}</h2>"
        f"<div class='wrap'><table><tr><th>{t('group', lang)}</th><th>{t('pitches', lang)}</th>"
        f"<th>{t('swing', lang)}</th><th>{t('chase', lang)}</th><th>{t('whiff', lang)}</th>"
        f"<th>xwOBAcon</th><th>{t('rv100', lang)}</th></tr>{''.join(g_rows)}</table></div>")


def _about(result, lang):
    hand_word = t("rhp" if result.pitcher_hand == "R" else "lhp", lang)
    side_word = t("rhp" if result.hitter_stand == "R" else "lhp", lang)
    pool = result.hitter_pool
    hand_note = t("hand_note_same" if result.same_hand_pool else "hand_note_all", lang).format(hand=hand_word)
    items = [t("about_hitter", lang).format(n=len(pool), m=int(pool["match"].notna().sum()), hand_note=hand_note)]
    if result.switch_hitter:
        side = {"en": {"R": "right-handed", "L": "left-handed"},
                "es": {"R": "derecha", "L": "izquierda"}}[lang][result.hitter_stand]
        items[0] += t("switch_note", lang).format(side=side)
    side_note = t("side_note_same" if result.same_stand_pool else "side_note_all", lang).format(side=side_word)
    items.append(t("about_pitcher", lang).format(n=len(result.pitcher_side), side_note=side_note))
    items.append(t("about_rv_statcast" if result.rv_source == "statcast" else "about_rv_approx", lang))
    items.append(t("about_method", lang))
    return "<ul class='about'>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ul>"


def _backtest(result, lang):
    bt = result.backtest
    if not bt:
        return ""
    text = t("backtest_text", lang).format(**bt)
    return f"<section><h2>{t('backtest', lang)}</h2><p>{html.escape(text)}</p></section>"


def write_html(result, path: str | Path, lang: str = "en", subtitle: str = "") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bullets = "".join(f"<li>{html.escape(b)}</li>" for b in plan_bullets(result, lang))
    title = f"{t('title', lang)}: {result.hitter_name} {t('vs', lang)} {result.pitcher_name}"
    meta = f"{t('bats', lang)[result.hitter_stand]} · {t('throws', lang)[result.pitcher_hand]}"
    if subtitle:
        meta += f" · {subtitle}"

    doc = f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><div class="page">
<header><h1>{html.escape(title)}</h1><p>{html.escape(meta)}</p></header>
<section><h2>{t('the_plan', lang)}</h2><ol class="plan">{bullets}</ol></section>
<section><h2>{t('plan_by_count', lang)}</h2>{_plan_table(result, lang)}</section>
<section><h2>{t('where', lang)}</h2>{_img(plots.where_to_throw(result, lang), t('where', lang))}
<p class="note">{t('where_note', lang)}</p></section>
<section><h2>{t('tendencies', lang)}</h2>{_tendency_table(result, lang)}</section>
<section><h2>{t('hitter_loc', lang)}</h2>{_img(plots.hitter_locations(result, lang), t('hitter_loc', lang))}
<p class="note">{t('hitter_loc_note', lang)}</p></section>
<section><h2>{t('shapes', lang)}</h2>{_img(plots.matchup_shapes(result, lang), t('shapes', lang))}
<p class="note">{t('shapes_note', lang)}</p></section>
{_backtest(result, lang)}
<section><h2>{t('about', lang)}</h2>{_about(result, lang)}</section>
</div></body></html>"""
    path.write_text(doc, encoding="utf-8")
    return path
