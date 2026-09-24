"""Small statistical helpers."""
from __future__ import annotations

import numpy as np


def shrink(total: float, n: float, prior: float, k: float) -> float:
    """Blend an observed mean toward a prior, weighted by sample size.

    Equivalent to pretending we had already seen `k` observations at the prior.
    With n = 0 the result is the prior; as n grows it approaches total / n.
    """
    return (total + k * prior) / (n + k)


def ratio(mask_or_values) -> float:
    arr = np.asarray(mask_or_values, dtype=float)
    return float(arr.mean()) if arr.size else float("nan")
