"""Tunable constants for pitchplan.

Everything a user might reasonably want to tweak lives here, so the modelling
choices are visible in one place instead of buried in the code.
"""

# --- Pitch types -----------------------------------------------------------
PITCH_GROUPS = {
    "FF": "Fastball", "FA": "Fastball", "SI": "Fastball", "FC": "Fastball",
    "SL": "Breaking", "ST": "Breaking", "CU": "Breaking", "KC": "Breaking",
    "SV": "Breaking", "CS": "Breaking",
    "CH": "Offspeed", "FS": "Offspeed", "FO": "Offspeed", "SC": "Offspeed",
}
GROUP_ORDER = ["Fastball", "Breaking", "Offspeed"]

# --- Statcast "description" values ----------------------------------------
BALL_DESCRIPTIONS = {"ball", "blocked_ball", "pitchout", "intent_ball"}
CALLED_STRIKE_DESCRIPTIONS = {"called_strike"}
WHIFF_DESCRIPTIONS = {"swinging_strike", "swinging_strike_blocked", "foul_tip", "missed_bunt"}
FOUL_DESCRIPTIONS = {"foul", "foul_bunt", "foul_pitchout"}
IN_PLAY_DESCRIPTIONS = {"hit_into_play", "hit_into_play_no_out", "hit_into_play_score"}
SWING_DESCRIPTIONS = WHIFF_DESCRIPTIONS | FOUL_DESCRIPTIONS | IN_PLAY_DESCRIPTIONS | {"bunt_foul_tip"}

# --- Approximate run values (batter's perspective, runs) -------------------
# Used only when the data has no `delta_run_exp` column (e.g. some CSV exports
# or synthetic data). Values are relative to the start of a plate appearance
# and are rough public linear-weight style estimates, not an exact model.
COUNT_VALUES = {
    (0, 0): 0.000, (1, 0): 0.037, (2, 0): 0.098, (3, 0): 0.183,
    (0, 1): -0.043, (1, 1): -0.012, (2, 1): 0.042, (3, 1): 0.141,
    (0, 2): -0.100, (1, 2): -0.077, (2, 2): -0.036, (3, 2): 0.057,
}
EVENT_VALUES = {
    "single": 0.46, "double": 0.76, "triple": 1.03, "home_run": 1.40,
    "walk": 0.31, "intent_walk": 0.31, "hit_by_pitch": 0.33,
    "field_error": 0.46, "strikeout": -0.27, "strikeout_double_play": -0.60,
    "grounded_into_double_play": -0.60, "double_play": -0.60,
    "sac_fly": -0.05, "sac_bunt": -0.10,
}
IN_PLAY_OUT_VALUE = -0.26

# --- Strike zone geometry --------------------------------------------------
ZONE_HALF_WIDTH_FT = 0.83   # half the plate (0.708 ft) plus a ball radius
WASTE_MARGIN_FT = 0.9       # further than this outside the zone = "Waste"
DEFAULT_SZ_TOP = 3.4
DEFAULT_SZ_BOT = 1.6

ZONE_REGIONS = [
    "Up-In", "Up-Middle", "Up-Away",
    "Mid-In", "Heart", "Mid-Away",
    "Down-In", "Down-Middle", "Down-Away",
]
CHASE_REGIONS = ["Chase Up", "Chase Down", "Chase In", "Chase Away"]
RECOMMENDABLE_REGIONS = ZONE_REGIONS + CHASE_REGIONS

# --- Count states ----------------------------------------------------------
COUNT_STATES = ["Even", "Ahead", "Behind", "Two strikes"]
# Baseball logic layered on top of the numbers: when behind, only recommend
# pitches in the zone. "Ahead" means the pitcher is ahead.
ALLOWED_REGIONS = {
    "Even": ZONE_REGIONS + CHASE_REGIONS,
    "Ahead": ZONE_REGIONS + CHASE_REGIONS,
    "Behind": ZONE_REGIONS,
    "Two strikes": ZONE_REGIONS + CHASE_REGIONS,
}

# --- League context (approximate recent MLB averages; report context only) --
LEAGUE_REFS = {
    "chase_rate": 0.28,
    "zone_swing_rate": 0.67,
    "whiff_rate": 0.25,
    "first_pitch_swing_rate": 0.30,
    "xwoba_con": 0.370,
}

# --- Modelling knobs -------------------------------------------------------
# Shrinkage strength: "act as if we'd already seen k pitches at the prior".
SHRINK_K = {"pitch": 150, "region": 60, "cell": 40, "count": 150}

# Pitch-shape similarity: (velocity mph, arm-side break in, induced vert. break in)
SIMILARITY_SCALES = (2.0, 4.0, 4.0)
SIMILARITY_MAX_DIST = 2.0

MIN_SAME_HAND_PITCHES = 400    # else use hitter data vs both pitcher hands
MIN_SAME_STAND_PITCHES = 500   # else use pitcher data vs both batter sides
MIN_ARSENAL_PITCHES = 30
MIN_ARSENAL_SHARE = 0.03
MIN_USAGE_SHARE = 0.03         # pitcher must throw pitch there >= 3% of the time
MAX_OPTIONS_PER_PITCH = 2      # keep each count's options varied
MIN_SAMPLE_FOR_AVOID = 15
AVOID_THRESHOLD = -1.0          # only flag spots costing > 1 run per 100 pitches

WEIGHTS = {"hitter": 0.6, "pitcher": 0.4}
