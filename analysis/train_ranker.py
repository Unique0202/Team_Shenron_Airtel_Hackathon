"""Train (1) the product ranker: P(owner wants product | business profile), one model per product,
and (2) the lead propensity model: P(lead activates | profile + source). Saves to backend/models/."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "backend" / "models"
OUT.mkdir(exist_ok=True)

L = pd.read_csv(ROOT / "data" / "smb_leads.csv")
PIDS = [f"P{i:02d}" for i in range(1, 26)]

CAT = ["segment", "business_type", "city_tier", "annual_turnover_band", "current_internet", "has_gstin", "has_udyam"]
NUM = ["employee_count", "num_sites"]


def features(extra_cat=()):
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT + list(extra_cat)),
        ("num", FunctionTransformer(np.log1p), NUM),
    ])


# ---- 1. product ranker -------------------------------------------------------------
asked = L.products_of_interest.fillna("").str.split(";")
bought = L.bundle_products.fillna("").str.split(";").apply(lambda xs: [x.split("x")[0] for x in xs if x])
Y = np.array([[int(p in a or p in b) for p in PIDS] for a, b in zip(asked, bought)])
# leads that activated and stayed are the strongest evidence of a good fit
w = np.where(L.outcome.eq("Activated") & L.churned_within_6_months.ne("Y"), 3.0,
             np.where(L.outcome.eq("Activated"), 1.5, 1.0))

X = L[CAT + NUM].astype({"city_tier": str})
Xtr, Xte, Ytr, Yte, wtr, _ = train_test_split(X, Y, w, test_size=0.2, random_state=7)
sklearn.set_config(enable_metadata_routing=True)  # lets sample_weight reach each per-product model
ranker = Pipeline([
    ("f", features()),
    ("m", OneVsRestClassifier(LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced")
                              .set_fit_request(sample_weight=True))),
])
ranker.fit(Xtr, Ytr, sample_weight=wtr)
P = ranker.predict_proba(Xte)
aucs = {p: roc_auc_score(Yte[:, i], P[:, i]) for i, p in enumerate(PIDS) if 0 < Yte[:, i].sum() < len(Yte)}
print(f"ranker: mean per-product AUC {np.mean(list(aucs.values())):.3f}")
print("  " + ", ".join(f"{p}={a:.2f}" for p, a in aucs.items()))
# precision@3: of the 3 products we rank highest, how many did the lead ask for / buy?
top3 = np.argsort(-P, axis=1)[:, :3]
print(f"ranker: precision@3 {np.mean([Yte[i, top3[i]].mean() for i in range(len(Yte))]):.3f} "
      f"(random baseline {Yte.mean():.3f})")
ranker.fit(X, Y, sample_weight=w)  # final model on all data
joblib.dump({"model": ranker, "pids": PIDS, "cat": CAT, "num": NUM}, OUT / "ranker.joblib")

# ---- 2. lead propensity ---------------------------------------------------------------
PCAT = ["lead_source", "preferred_language"]
Xp = L[CAT + NUM + PCAT].astype({"city_tier": str})
yp = L.outcome.eq("Activated").astype(int)
Xtr, Xte, ytr, yte = train_test_split(Xp, yp, test_size=0.2, random_state=7, stratify=yp)
prop = Pipeline([("f", features(PCAT)), ("m", LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced"))])
prop.fit(Xtr, ytr)
s = prop.predict_proba(Xte)[:, 1]
top = np.argsort(-s)[: len(s) // 5]
print(f"propensity: AUC {roc_auc_score(yte, s):.3f}; top-20% of leads hold "
      f"{yte.iloc[top].sum() / yte.sum():.0%} of activations (conv {yte.iloc[top].mean():.1%} vs {yte.mean():.1%})")
prop.fit(Xp, yp)
joblib.dump({"model": prop, "cols": CAT + NUM + PCAT}, OUT / "propensity.joblib")
print("saved", *OUT.iterdir())
