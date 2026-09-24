"""English / Spanish text for the report."""
from __future__ import annotations

PITCH_NAMES = {
    "en": {"FF": "four-seamer", "FA": "fastball", "SI": "sinker", "FC": "cutter",
           "SL": "slider", "ST": "sweeper", "CU": "curveball", "KC": "knuckle curve",
           "SV": "slurve", "CS": "slow curve", "CH": "changeup", "FS": "splitter",
           "FO": "forkball", "SC": "screwball"},
    "es": {"FF": "recta de cuatro costuras", "FA": "recta", "SI": "sinker", "FC": "cutter",
           "SL": "slider", "ST": "sweeper", "CU": "curva", "KC": "curva de nudillos",
           "SV": "slurve", "CS": "curva lenta", "CH": "cambio", "FS": "splitter",
           "FO": "forkball", "SC": "screwball"},
}
ES_FEMININE = {"FF", "FA", "CU", "KC", "CS"}

REGION_PHRASES = {
    "en": {"Up-In": "up and in", "Up-Middle": "up, middle", "Up-Away": "up and away",
           "Mid-In": "middle-in", "Heart": "middle-middle", "Mid-Away": "middle-away",
           "Down-In": "down and in", "Down-Middle": "down, middle", "Down-Away": "down and away",
           "Chase Up": "above the zone", "Chase Down": "below the zone",
           "Chase In": "off the plate inside", "Chase Away": "off the plate away"},
    "es": {"Up-In": "arriba y adentro", "Up-Middle": "arriba, al centro", "Up-Away": "arriba y afuera",
           "Mid-In": "adentro, a media altura", "Heart": "en el centro", "Mid-Away": "afuera, a media altura",
           "Down-In": "abajo y adentro", "Down-Middle": "abajo, al centro", "Down-Away": "abajo y afuera",
           "Chase Up": "por encima de la zona", "Chase Down": "por debajo de la zona",
           "Chase In": "pegado adentro, fuera de la zona", "Chase Away": "afuera, fuera de la zona"},
}
REGION_SHORT = {
    "en": {"Up-In": "Up-In", "Up-Middle": "Up-Middle", "Up-Away": "Up-Away",
           "Mid-In": "Middle-In", "Heart": "Heart", "Mid-Away": "Middle-Away",
           "Down-In": "Down-In", "Down-Middle": "Down-Middle", "Down-Away": "Down-Away",
           "Chase Up": "Chase up", "Chase Down": "Chase down",
           "Chase In": "Chase in", "Chase Away": "Chase away"},
    "es": {"Up-In": "Arriba-adentro", "Up-Middle": "Arriba-centro", "Up-Away": "Arriba-afuera",
           "Mid-In": "Medio-adentro", "Heart": "Centro", "Mid-Away": "Medio-afuera",
           "Down-In": "Abajo-adentro", "Down-Middle": "Abajo-centro", "Down-Away": "Abajo-afuera",
           "Chase Up": "Fuera: arriba", "Chase Down": "Fuera: abajo",
           "Chase In": "Fuera: adentro", "Chase Away": "Fuera: afuera"},
}
COUNT_LABELS = {
    "en": {"Even": "Early / even count", "Ahead": "Pitcher ahead",
           "Behind": "Pitcher behind", "Two strikes": "Two strikes"},
    "es": {"Even": "Temprano / conteo parejo", "Ahead": "Lanzador adelante",
           "Behind": "Lanzador atrás", "Two strikes": "Dos strikes"},
}
GROUP_LABELS = {
    "en": {"Fastball": "Fastballs", "Breaking": "Breaking balls", "Offspeed": "Offspeed"},
    "es": {"Fastball": "Rectas", "Breaking": "Rompientes", "Offspeed": "Cambios de velocidad"},
}

STRINGS = {
    "en": {
        "title": "Pitch Plan",
        "vs": "vs.",
        "bats": {"R": "Bats R", "L": "Bats L"},
        "throws": {"R": "RHP", "L": "LHP"},
        "the_plan": "The plan",
        "plan_by_count": "Plan by count",
        "count": "Count",
        "option": "Option",
        "runs_saved_note": "Numbers are estimated runs saved per 100 pitches (higher is better for the pitcher).",
        "tendencies": "Hitter tendencies",
        "metric": "Metric", "hitter": "Hitter", "league": "League (approx.)", "sample": "Sample",
        "m_chase_rate": "Chase rate (swings at pitches outside the zone)",
        "m_zone_swing_rate": "Zone swing rate",
        "m_whiff_rate": "Whiff rate (misses per swing)",
        "m_first_pitch_swing_rate": "First-pitch swing rate",
        "m_xwoba_con": "xwOBA on contact",
        "by_group": "By pitch group",
        "group": "Group", "pitches": "Pitches", "swing": "Swing", "chase": "Chase",
        "whiff": "Whiff", "rv100": "Run value / 100 (hitter)",
        "where": "Where to throw each pitch",
        "where_note": "Runs saved per 100 pitches for each of the pitcher's pitches by location, across all counts. "
                      "Green favors the pitcher. Gray = the pitcher rarely throws that pitch there. "
                      "Small number = the hitter's sample vs. similar pitches.",
        "hitter_loc": "Hitter by location",
        "hitter_loc_note": "Top row: whiff rate per swing. Bottom row: xwOBA on contact. "
                           "Small samples are pulled toward the hitter's average for that pitch group.",
        "shapes": "How the matchup was built",
        "shapes_note": "Every pitch the hitter has seen, by movement. Colored pitches were close enough in "
                       "velocity and movement to count as similar to one of the pitcher's pitches (large markers).",
        "catcher_view": "Catcher's view",
        "in": "In", "away": "Away",
        "whiff_title": "Whiff rate", "xwoba_title": "xwOBA on contact",
        "usage": "usage",
        "arm_side": "Arm-side break (in)", "ivb": "Induced vertical break (in)",
        "unmatched": "Not similar",
        "about": "About this report",
        "about_hitter": "Hitter data: {n:,} pitches{hand_note}; {m:,} were similar in shape to the pitcher's arsenal.",
        "hand_note_same": " from {hand} pitchers",
        "hand_note_all": " from all pitchers (not enough vs. {hand} alone)",
        "switch_note": " As a switch hitter he is assumed to bat {side} against this pitcher.",
        "about_pitcher": "Pitcher data: {n:,} pitches{side_note}.",
        "side_note_same": " to {side}-handed hitters",
        "side_note_all": " to all hitters (not enough vs. {side}-handed hitters alone)",
        "about_rv_statcast": "Run values come from Statcast's per-pitch change in run expectancy.",
        "about_rv_approx": "Run values are approximated from count changes and outcomes (no delta_run_exp column in the data).",
        "about_method": "Each option blends the hitter's results against similar pitches (60%) with the pitcher's "
                        "own results (40%). Thin samples are shrunk toward broader estimates, so a handful of "
                        "pitches can't drive a recommendation on its own. When the pitcher is behind, only "
                        "pitches in the zone are recommended.",
        "backtest": "Did the plan work?",
        "backtest_text": "Plan built on games through {cutoff}, then tested on the {n_test:,} later pitches the hitter saw "
                         "that were similar to this arsenal. Pitches that followed the plan: {f_rv:+.1f} runs per 100 "
                         "for the hitter ({n_f:,} pitches). All others: {o_rv:+.1f} ({n_o:,} pitches). "
                         "Difference: {diff:+.1f} runs saved per 100 (95% interval {lo:+.1f} to {hi:+.1f}).",
        "rhp": "right-handed", "lhp": "left-handed",
        # Plan bullets
        "b_first_take": "Takes early: swings at only {rate} of first pitches (league ~30%). Steal strike one with the {opt}.",
        "b_first_ambush": "Ambushes early: swings at {rate} of first pitches (league ~30%). No get-me-over strikes; start him with the {opt}.",
        "b_first_normal": "Early and even counts: the {opt}.",
        "b_putaway": "Put-away pitch with two strikes: the {opt}.",
        "b_putaway_whiff": " He misses on {rate} of his swings at similar pitches there ({n} swings).",
        "b_chase_high": "Expands the zone: chases {rate} of pitches outside it (league ~28%). When ahead, make him chase the {opt}.",
        "b_chase_low": "Disciplined: chases only {rate} (league ~28%). When ahead, attack with the {opt} instead of nibbling.",
        "b_ahead": "When ahead: the {opt}.",
        "b_behind": "When behind: the {opt} is the safest strike.",
        "b_avoid_xw": "Avoid the {opt}: {xw} xwOBA on contact against similar pitches there ({n} balls in play).",
        "b_avoid_rv": "Avoid the {opt}: the worst spot in the matchup ({rv:+.1f} runs per 100).",
    },
    "es": {
        "title": "Plan de pitcheo",
        "vs": "vs.",
        "bats": {"R": "Batea derecho", "L": "Batea zurdo"},
        "throws": {"R": "Lanzador derecho", "L": "Lanzador zurdo"},
        "the_plan": "El plan",
        "plan_by_count": "Plan según el conteo",
        "count": "Conteo",
        "option": "Opción",
        "runs_saved_note": "Los números son carreras ahorradas estimadas por cada 100 lanzamientos (más alto es mejor para el lanzador).",
        "tendencies": "Tendencias del bateador",
        "metric": "Métrica", "hitter": "Bateador", "league": "Liga (aprox.)", "sample": "Muestra",
        "m_chase_rate": "Swings fuera de la zona",
        "m_zone_swing_rate": "Swings dentro de la zona",
        "m_whiff_rate": "Swings fallados (por swing)",
        "m_first_pitch_swing_rate": "Swings al primer lanzamiento",
        "m_xwoba_con": "xwOBA en contacto",
        "by_group": "Por tipo de lanzamiento",
        "group": "Tipo", "pitches": "Lanzamientos", "swing": "Swing", "chase": "Fuera de zona",
        "whiff": "Fallo", "rv100": "Valor de carreras / 100 (bateador)",
        "where": "Dónde tirar cada lanzamiento",
        "where_note": "Carreras ahorradas por cada 100 lanzamientos para cada pitcheo del lanzador según la ubicación, "
                      "en todos los conteos. Verde favorece al lanzador. Gris = el lanzador casi nunca tira ese "
                      "lanzamiento ahí. Número pequeño = muestra del bateador contra lanzamientos similares.",
        "hitter_loc": "El bateador por ubicación",
        "hitter_loc_note": "Arriba: porcentaje de swings fallados. Abajo: xwOBA en contacto. "
                           "Las muestras pequeñas se acercan al promedio del bateador para ese tipo de lanzamiento.",
        "shapes": "Cómo se construyó el enfrentamiento",
        "shapes_note": "Todos los lanzamientos que ha visto el bateador, según su movimiento. Los de color son "
                       "similares en velocidad y movimiento a uno de los lanzamientos del lanzador (marcadores grandes).",
        "catcher_view": "Vista del receptor",
        "in": "Adentro", "away": "Afuera",
        "whiff_title": "Swings fallados", "xwoba_title": "xwOBA en contacto",
        "usage": "uso",
        "arm_side": "Quiebre horizontal, lado del brazo (pulg.)", "ivb": "Quiebre vertical inducido (pulg.)",
        "unmatched": "No similar",
        "about": "Sobre este informe",
        "about_hitter": "Datos del bateador: {n:,} lanzamientos{hand_note}; {m:,} fueron similares al repertorio del lanzador.",
        "hand_note_same": " de lanzadores {hand}s",
        "hand_note_all": " de todos los lanzadores (no hay suficientes de lanzadores {hand}s)",
        "switch_note": " Como bateador ambidiestro, se asume que batea a la {side} contra este lanzador.",
        "about_pitcher": "Datos del lanzador: {n:,} lanzamientos{side_note}.",
        "side_note_same": " a bateadores {side}s",
        "side_note_all": " a todos los bateadores (no hay suficientes contra bateadores {side}s)",
        "about_rv_statcast": "Los valores de carreras vienen del cambio en la expectativa de carreras de Statcast por lanzamiento.",
        "about_rv_approx": "Los valores de carreras son aproximados a partir de los cambios de conteo y los resultados.",
        "about_method": "Cada opción combina los resultados del bateador contra lanzamientos similares (60%) con los "
                        "resultados del propio lanzador (40%). Las muestras pequeñas se ajustan hacia estimaciones "
                        "más amplias, así que unos pocos lanzamientos no deciden una recomendación. Cuando el "
                        "lanzador está atrás en el conteo, solo se recomiendan lanzamientos en la zona.",
        "backtest": "¿Funcionó el plan?",
        "backtest_text": "Plan construido con juegos hasta el {cutoff} y evaluado con los {n_test:,} lanzamientos posteriores "
                         "similares a este repertorio. Lanzamientos que siguieron el plan: {f_rv:+.1f} carreras por 100 "
                         "para el bateador ({n_f:,}). Los demás: {o_rv:+.1f} ({n_o:,}). "
                         "Diferencia: {diff:+.1f} carreras ahorradas por 100 (intervalo del 95%: {lo:+.1f} a {hi:+.1f}).",
        "rhp": "derecho", "lhp": "zurdo",
        "b_first_take": "Deja pasar el primero: solo hace swing al {rate} de los primeros lanzamientos (liga ~30%). Roba el primer strike con {opt}.",
        "b_first_ambush": "Agresivo temprano: hace swing al {rate} de los primeros lanzamientos (liga ~30%). Nada por el medio; empieza con {opt}.",
        "b_first_normal": "Conteos tempranos y parejos: {opt}.",
        "b_putaway": "Para ponchar con dos strikes: {opt}.",
        "b_putaway_whiff": " Falla el {rate} de sus swings contra lanzamientos similares ahí ({n} swings).",
        "b_chase_high": "Sale de la zona: hace swing al {rate} de los lanzamientos fuera de ella (liga ~28%). Con ventaja, hazlo perseguir {opt}.",
        "b_chase_low": "Disciplinado: solo hace swing al {rate} fuera de la zona (liga ~28%). Con ventaja, ataca con {opt} en vez de buscar las esquinas.",
        "b_ahead": "Con ventaja: {opt}.",
        "b_behind": "Atrás en el conteo: {opt} es el strike más seguro.",
        "b_avoid_xw": "Evita {opt}: {xw} de xwOBA en contacto contra lanzamientos similares ahí ({n} bolas en juego).",
        "b_avoid_rv": "Evita {opt}: el peor lugar del enfrentamiento ({rv:+.1f} carreras por 100).",
    },
}


def t(key: str, lang: str):
    return STRINGS[lang][key]


def pitch_name(pt: str, lang: str, capital: bool = False) -> str:
    name = PITCH_NAMES[lang].get(pt, pt)
    return name[:1].upper() + name[1:] if capital else name


def option_phrase(pt: str, region: str, lang: str) -> str:
    """'slider down and away' / 'el slider abajo y afuera' (EN templates add 'the')."""
    phrase = f"{pitch_name(pt, lang)} {REGION_PHRASES[lang][region]}"
    if lang == "es":
        return f"{'la' if pt in ES_FEMININE else 'el'} {phrase}"
    return phrase


def option_short(pt: str, region: str, lang: str) -> str:
    return f"{pitch_name(pt, lang, capital=True)} · {REGION_SHORT[lang][region]}"


def pct(x: float) -> str:
    return f"{x:.0%}"


def woba(x: float) -> str:
    return f"{x:.3f}".lstrip("0") if x < 1 else f"{x:.3f}"
