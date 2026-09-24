"""Command-line entry point.

Examples
    python -m pitchplan --demo
    python -m pitchplan --demo --lang es --backtest
    python -m pitchplan --hitter "Juan Soto" --pitcher "Kevin Gausman" \
        --start 2025-03-27 --end 2025-09-28 --backtest
    python -m pitchplan --hitter "Prospect Name" --hitter-csv hitter.csv \
        --pitcher "Our Guy" --pitcher-csv pitcher.csv
"""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

import pandas as pd

from .data import fetch_statcast
from .evaluate import backtest
from .pipeline import build_plan
from .report import plan_bullets, write_html


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _load(name, csv, start, end, role):
    if csv:
        return pd.read_csv(csv)
    if not name:
        raise SystemExit(f"Provide --{'hitter' if role == 'batter' else 'pitcher'} (a name or MLBAM id) or a CSV.")
    print(f"Downloading Statcast data for {name} ({start} to {end})...")
    return fetch_statcast(name, start, end, role)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pitchplan", description="Build a pitch plan for a hitter.")
    ap.add_argument("--demo", action="store_true", help="use built-in synthetic data (no internet needed)")
    ap.add_argument("--hitter", help="hitter name ('First Last' or 'Last, First') or MLBAM id")
    ap.add_argument("--pitcher", help="our pitcher's name or MLBAM id")
    ap.add_argument("--hitter-csv", help="Statcast/Baseball Savant CSV for the hitter")
    ap.add_argument("--pitcher-csv", help="Statcast/Baseball Savant CSV for the pitcher")
    ap.add_argument("--start", default=f"{date.today().year}-03-01")
    ap.add_argument("--end", default=date.today().isoformat())
    ap.add_argument("--lang", choices=["en", "es"], default="en")
    ap.add_argument("--top", type=int, default=3, help="options per count state")
    ap.add_argument("--backtest", action="store_true", help="test the plan on later games")
    ap.add_argument("--out", default="output", help="output folder")
    args = ap.parse_args(argv)

    if args.demo:
        from .synthetic import make_demo_hitter, make_demo_pitcher
        h_raw, p_raw = make_demo_hitter(), make_demo_pitcher()
        h_name, p_name, subtitle = "Demo Hitter", "Demo Pitcher", "Synthetic demo data"
    else:
        h_raw = _load(args.hitter, args.hitter_csv, args.start, args.end, "batter")
        p_raw = _load(args.pitcher, args.pitcher_csv, args.start, args.end, "pitcher")
        h_name = args.hitter or Path(args.hitter_csv).stem
        p_name = args.pitcher or Path(args.pitcher_csv).stem
        subtitle = "" if (args.hitter_csv or args.pitcher_csv) else f"{args.start} – {args.end}"

    result = build_plan(h_raw, p_raw, h_name, p_name, top_n=args.top)
    if args.backtest:
        try:
            result.backtest = backtest(h_raw, p_raw, top_n=args.top)
        except ValueError as exc:
            print(f"Backtest skipped: {exc}")

    out = Path(args.out)
    stem = f"{_slug(h_name)}_vs_{_slug(p_name)}_{args.lang}"
    html_path = write_html(result, out / f"{stem}.html", args.lang, subtitle)
    result.scores.to_csv(out / f"{stem}_scores.csv", index=False)

    print(f"\n{h_name} vs. {p_name}\n")
    for i, line in enumerate(plan_bullets(result, args.lang), 1):
        print(f"  {i}. {line}")
    if result.backtest:
        bt = result.backtest
        print(f"\n  Backtest: {bt['diff']:+.1f} runs saved per 100 pitches when following the plan "
              f"(95% interval {bt['lo']:+.1f} to {bt['hi']:+.1f}).")
    print(f"\nReport: {html_path}\nScores: {out / (stem + '_scores.csv')}")


if __name__ == "__main__":
    main()
