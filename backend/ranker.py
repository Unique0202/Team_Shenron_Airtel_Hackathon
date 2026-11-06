"""Loads the models trained by analysis/train_ranker.py."""
from pathlib import Path

import joblib
import pandas as pd

from catalogue import SEGMENTS

MODELS = Path(__file__).resolve().parent / "models"
_R = joblib.load(MODELS / "ranker.joblib")
_P = joblib.load(MODELS / "propensity.joblib")


def _row(profile):
    yn = lambda b: "Y" if b else "N"
    return {
        "segment": SEGMENTS[profile["segment"]],
        "business_type": profile.get("business_type", ""),
        "city_tier": str(profile["city_tier"]),
        "annual_turnover_band": profile.get("turnover_band", ""),
        "current_internet": profile.get("current_internet", ""),
        "has_gstin": yn(profile["has_gstin"]),
        "has_udyam": yn(profile.get("has_udyam", False)),
        "employee_count": profile["employees"],
        "num_sites": profile["sites"],
        "lead_source": profile.get("lead_source", "Website form"),
        "preferred_language": profile.get("language", "English"),
    }


def score_products(profile):
    """{pid: 0..1}. Above 0.5 = more likely than average for a business like this."""
    probs = _R["model"].predict_proba(pd.DataFrame([_row(profile)])[_R["cat"] + _R["num"]])[0]
    return {p: round(float(s), 3) for p, s in zip(_R["pids"], probs)}


def propensity(profiles):
    """P(activates) for a list of lead profiles."""
    df = pd.DataFrame([_row(p) for p in profiles])[_P["cols"]]
    return [round(float(s), 3) for s in _P["model"].predict_proba(df)[:, 1]]
