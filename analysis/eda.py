"""Funnel / conversion / churn breakdowns of smb_leads.csv. Prints the numbers used in the deck."""
import sys
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
L = pd.read_csv(DATA / "smb_leads.csv")
L["activated"] = L.outcome.eq("Activated")
L["churned"] = L.churned_within_6_months.eq("Y")
L["emp_band"] = pd.cut(L.employee_count, [0, 5, 10, 25, 50, 10_000], labels=["1-5", "6-10", "11-25", "26-50", "50+"])
L["sites_band"] = pd.cut(L.num_sites, [0, 1, 2, 5, 1_000], labels=["1", "2", "3-5", "6+"])
L["n_interest"] = L.products_of_interest.fillna("").str.count(";") + 1
L["lang_is_english"] = L.preferred_language.eq("English")

A = L[L.activated]
pd.set_option("display.width", 250, "display.max_rows", 200, "display.max_columns", 30)


def by(col, frame=L):
    g = frame.groupby(col, observed=True)
    out = pd.DataFrame({
        "leads": g.size(),
        "conv_%": (g.activated.mean() * 100).round(1),
        "cac_per_lead": g.acquisition_cost_inr.mean().round(0),
    })
    act = frame[frame.activated].groupby(col, observed=True)
    out["days_to_act"] = act.days_lead_to_activation.mean().round(1)
    out["chase_calls"] = act.customer_follow_up_calls.mean().round(1)
    out["mrr"] = act.monthly_bundle_value_inr.median()
    out["churn_%"] = (act.churned.mean() * 100).round(1)
    out["nps"] = act.nps_score.mean().round(1)
    out["cac_per_activation"] = (g.acquisition_cost_inr.sum() / g.activated.sum()).round(0)
    return out.sort_values("conv_%", ascending=False)


print(f"Leads {len(L)}, activated {len(A)} ({len(A)/len(L):.1%}), "
      f"total acquisition spend Rs {L.acquisition_cost_inr.sum():,.0f}, "
      f"CAC/activation Rs {L.acquisition_cost_inr.sum()/len(A):,.0f}")
print(f"Activated: days {A.days_lead_to_activation.mean():.1f}, chase calls {A.customer_follow_up_calls.mean():.2f}, "
      f"median MRR {A.monthly_bundle_value_inr.median():,.0f}, churn {A.churned.mean():.1%}, NPS avg {A.nps_score.mean():.1f}")
nps = A.nps_score
print(f"NPS score (promoters-detractors): {((nps>=9).mean()-(nps<=6).mean())*100:.0f}")

for col in ["segment", "lead_source", "city_tier", "preferred_language", "lang_is_english", "has_gstin", "has_udyam",
            "current_internet", "current_provider", "annual_turnover_band", "emp_band", "sites_band", "n_interest",
            "contact_role"]:
    print(f"\n=== {col}"); print(by(col))

print("\n=== segment x lead_source conversion %")
print(L.pivot_table(index="segment", columns="lead_source", values="activated", aggfunc="mean").mul(100).round(1))

print("\n=== activated: churn by days-to-activation band / chase calls")
A2 = A.assign(days_band=pd.cut(A.days_lead_to_activation, [0, 10, 15, 20, 30, 100]))
print(A2.groupby("days_band", observed=True).agg(n=("churned", "size"), churn=("churned", "mean"), nps=("nps_score", "mean")).round(2))
print(A.groupby("customer_follow_up_calls").agg(n=("churned", "size"), churn=("churned", "mean"), nps=("nps_score", "mean")).round(2))

print("\n=== activated: bundle size vs churn")
A3 = A.assign(n_products=A.bundle_products.str.count(";") + 1)
print(A3.groupby("n_products").agg(n=("churned", "size"), churn=("churned", "mean"), mrr=("monthly_bundle_value_inr", "median"), nps=("nps_score", "mean")).round(2))

print("\n=== most common products bought (activated)")
items = A.bundle_products.str.split(";").explode().str.split("x").str[0]
print(items.value_counts().head(25).to_string())

print("\n=== products of interest (all leads) top")
print(L.products_of_interest.str.split(";").explode().value_counts().head(25).to_string())

print("\n=== drop reason by segment (% of segment leads)")
print(pd.crosstab(L.drop_reason, L.segment, normalize="columns").mul(100).round(1))

print("\n=== drop reason by language (english vs not) %")
print(pd.crosstab(L.drop_reason, L.lang_is_english, normalize="columns").mul(100).round(1))

print("\n=== created month conversion")
print(by(L.created_date.str[:7].rename("month")))
print("\n=== asked-for vs bought, per product (activated leads only)")
ask = A.products_of_interest.str.split(";").explode()
got = A.bundle_products.str.split(";").explode().str.split("x").str[0]
pairs = A.assign(ask=A.products_of_interest.str.split(";")).explode("ask")
pairs["bought_it"] = [a in b for a, b in zip(pairs.ask, pairs.bundle_products)]
fr = pd.DataFrame({"asked": ask.value_counts(), "bought": got.value_counts(),
                   "asked_and_bought_%": pairs.groupby("ask").bought_it.mean().mul(100).round(0)})
print(fr.sort_values("asked", ascending=False))

print("\n=== conversion % : language x lead_source")
print(L.pivot_table(index="preferred_language", columns="lead_source", values="activated", aggfunc="mean").mul(100).round(1))
print("\n=== field sales: conversion by language")
print(by("preferred_language", L[L.lead_source.eq("Field sales")]))
print("\n=== segment x has_gstin conversion %")
print(L.pivot_table(index="segment", columns="has_gstin", values="activated", aggfunc="mean").mul(100).round(1))
print("\n=== wrong number / unreachable by source (%)")
print(pd.crosstab(L.lead_source, L.drop_reason, normalize="index").mul(100).round(1)[["Wrong or invalid number","Unreachable after 3 attempts","Not interested on first call"]])
sys.stdout.flush()
