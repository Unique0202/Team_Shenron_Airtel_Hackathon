"""Product catalogue: eligibility rules, quantities, pricing and bundle building. Pure code, no LLM."""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

SEGMENTS = {
    "micro": "Micro retail & services",
    "prof": "Professional offices",
    "multi": "Small multi-site businesses",
    "mfg": "Small manufacturers",
}
SEGMENT_CODE = {v: k for k, v in SEGMENTS.items()}
PRIMARY_INTERNET = ["P01", "P02", "P03", "P04", "P05", "P06"]
MOBILE = ["P07", "P08"]
# ponytail: static ceilings from analysis/findings.md (median MRR per segment x ~1.6); refit if pricing changes
PRICE_CEILING = {"micro": 3_000, "prof": 12_000, "multi": 45_000, "mfg": 50_000}
MAX_ITEMS = 6  # bundles above 6 products churn 43% (findings signal 7)
CONTRACTS = {12: 0.25, 24: 0.6, 36: 0.9}  # share of (max - min) price range given as discount


def _load():
    rows = list(csv.DictReader(open(DATA / "product_catalogue.csv", encoding="utf-8")))
    out = {}
    for r in rows:
        out[r["product_id"]] = {
            "id": r["product_id"],
            "category": r["category"],
            "name": r["product_name"],
            "description": r["description"],
            "unit": r["unit"],
            "price_min": int(r["price_min_inr_per_month"]),
            "price_max": int(r["price_max_inr_per_month"]),
            "setup": int(r["one_time_setup_inr"]),
            "min_contract": int(r["min_contract_months"]),
            "tiers": {int(t) for t in r["available_city_tiers"].split(";")},
            "min_employees": int(r["min_employees"]),
            "min_sites": int(r["min_sites"]),
            "requires_gstin": r["requires_gstin"] == "Y",
            "requires_one_of": [p for p in r["requires_one_of"].split("|") if p],
            "install_days": int(r["typical_install_days"]),
            "segments": r["target_segments"].split(";"),
        }
    return out


PRODUCTS = _load()


def eligibility(pid, profile):
    """(ok, reason). profile keys: segment, employees, sites, city_tier, has_gstin."""
    p = PRODUCTS[pid]
    if profile["city_tier"] not in p["tiers"]:
        return False, f"{p['name']} is only sold in tier {'/'.join(map(str, sorted(p['tiers'])))} cities"
    if profile["employees"] < p["min_employees"]:
        return False, f"{p['name']} needs at least {p['min_employees']} employees"
    if profile["sites"] < p["min_sites"]:
        return False, f"{p['name']} needs at least {p['min_sites']} sites"
    if p["requires_gstin"] and not profile["has_gstin"]:
        return False, f"{p['name']} needs an active GSTIN"
    return True, ""


def eligible_products(profile):
    return [pid for pid in PRODUCTS if eligibility(pid, profile)[0]]


def quantity(pid, profile):
    e, s = max(1, profile["employees"]), max(1, profile["sites"])
    unit = PRODUCTS[pid]["unit"]
    q = {
        "per site": s,
        "per counter": s,
        "per camera": max(2, s),
        "per line": min(6, max(1, round(e * 0.5))),
        "per user": e if e <= 10 else min(25, round(e * 0.5)),
        "per device": min(20, max(1, round(e * 0.5))),
        "per channel": min(4, max(2, e // 2)),
        "per vehicle": min(10, max(1, e // 6)),
    }.get(unit, 1)
    return q


def unit_price(pid, contract_months, n_products):
    p = PRODUCTS[pid]
    f = min(1.0, CONTRACTS[contract_months] + 0.05 * max(0, n_products - 3))
    return round(p["price_max"] - (p["price_max"] - p["price_min"]) * f)


def quote(items, contract_months=12):
    """items: [{"id", "qty"}]. Returns line items + totals. Setup halved at 24 months, waived at 36."""
    n = len(items)
    min_needed = max((PRODUCTS[it["id"]]["min_contract"] for it in items), default=12)
    contract_months = max(contract_months, min(c for c in CONTRACTS if c >= min_needed))
    setup_factor = {12: 1.0, 24: 0.5, 36: 0.0}[contract_months]
    lines = []
    for it in items:
        p = PRODUCTS[it["id"]]
        up = unit_price(it["id"], contract_months, n)
        lines.append({
            "id": p["id"], "name": p["name"], "description": p["description"], "unit": p["unit"],
            "qty": it["qty"], "unit_price": up, "monthly": up * it["qty"],
            "setup": round(p["setup"] * it["qty"] * setup_factor), "setup_list": p["setup"] * it["qty"],
            "install_days": p["install_days"],
        })
    return {
        "contract_months": contract_months,
        "lines": lines,
        "monthly_total": sum(l["monthly"] for l in lines),
        "setup_total": sum(l["setup"] for l in lines),
        "setup_saved": sum(l["setup_list"] - l["setup"] for l in lines),
        "ready_in_days": max((l["install_days"] for l in lines), default=0),
    }


def dependency_ok(pid, ids):
    deps = PRODUCTS[pid]["requires_one_of"]
    return not deps or any(d in ids for d in deps)


def build_bundle(profile, scores, wanted=(), contract_months=12):
    """Pick a right-sized, rule-compliant bundle.

    scores: {pid: relevance 0..1} from the ML ranker. wanted: product ids the owner explicitly asked for.
    Returns bundle items, suggested add-ons, and why each product was (not) included.
    """
    seg = profile["segment"]
    ok = set(eligible_products(profile))
    reasons, blocked = {}, {}
    for pid in wanted:
        if pid not in ok:
            blocked[pid] = eligibility(pid, profile)[1]

    chosen = []
    # 1. one primary internet link (most products depend on it)
    # the link may use at most half the segment budget, so the rest of the bundle still fits
    internet = [p for p in PRIMARY_INTERNET if p in ok
                and quote([{"id": p, "qty": quantity(p, profile)}], contract_months)["monthly_total"] <= PRICE_CEILING[seg] / 2]
    internet = internet or [p for p in PRIMARY_INTERNET if p in ok][:1]
    asked_net = [p for p in wanted if p in internet]
    if internet:
        best = asked_net[0] if asked_net else max(internet, key=lambda p: scores.get(p, 0))
        chosen.append(best)
        reasons[best] = "you asked for it" if asked_net else "main internet connection for your business"
    # 2. everything else the owner asked for, then the ranker's best picks
    for pid in wanted:
        if pid in ok and pid not in chosen and pid not in internet:
            chosen.append(pid)
            reasons[pid] = "you asked for it"
    for pid in sorted(ok, key=lambda p: -scores.get(p, 0)):
        if len(chosen) >= MAX_ITEMS:
            break
        if pid in chosen or pid in PRIMARY_INTERNET or scores.get(pid, 0) < 0.35:
            continue
        if pid in MOBILE and any(m in chosen for m in MOBILE):
            continue
        chosen.append(pid)
        reasons[pid] = f"popular with businesses like yours ({round(scores[pid] * 100)}% match)"

    # 3. dependencies: drop anything whose prerequisite is missing
    chosen = [p for p in chosen if dependency_ok(p, chosen)]

    # 4. price ceiling: drop the weakest suggestions (never what the owner asked for)
    items = [{"id": p, "qty": quantity(p, profile)} for p in chosen]
    while quote(items, contract_months)["monthly_total"] > PRICE_CEILING[seg]:
        optional = [it for it in items if reasons[it["id"]] not in ("you asked for it",) and it["id"] != chosen[0]]
        if not optional:
            break
        weakest = min(optional, key=lambda it: scores.get(it["id"], 0))
        items.remove(weakest)

    in_bundle = {it["id"] for it in items}
    addons = [p for p in sorted(ok, key=lambda p: -scores.get(p, 0))
              if p not in in_bundle and dependency_ok(p, in_bundle) and p not in PRIMARY_INTERNET][:4]
    return {
        "items": items,
        "addons": [{"id": p, "qty": quantity(p, profile), "name": PRODUCTS[p]["name"]} for p in addons],
        "reasons": {p: reasons[p] for p in in_bundle},
        "blocked": blocked,
        "quote": quote(items, contract_months),
    }
