"""Core checks: python test_core.py (no network, no API key needed)."""
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import catalogue as cat
import kyc
from ranker import score_products

# 1. GSTIN checksum: every registry GSTIN is valid, and a one-character change is caught
assert all(kyc.gstin_format(g)[0] for g in kyc.GSTIN_DB), "checksum rejects a registry GSTIN"
assert not kyc.gstin_format("32TTNXB7384T1ZX")[0]
assert kyc.near_gstins("08YKZXS8189L1ZO") == ["08YKZXS5189L1ZO"]

# 2. KYC answer key we derived for the 12 sample applicants (fixtures transcribed from data/kyc_documents)
EXPECTED_ERRORS = {
    "K01": {"gstin_active", "udyam_number"},            # GST cancelled, Udyam number blank
    "K02": set(), "K03": set(),
    "K04": {"gst_certificate_readable"},                # blurred GST certificate
    "K05": {"udyam_certificate_present"},               # Udyam certificate missing
    "K06": {"gstin_format"},                            # GSTIN altered (5 -> 8), checksum fails
    "K07": {"gst_legal_name", "gst_internal_names"},    # 'Shri' vs 'Neelgiri' Physio Clinic
    "K08": set(), "K09": set(), "K10": set(),
    "K11": {"bill_recent"},                             # electricity bill 257 days old
    "K12": set(),
}
samples = json.load(open(Path(__file__).parent / "fixtures" / "kyc_samples.json", encoding="utf-8"))
for k, docs in samples.items():
    got = {c["id"] for c in kyc.validate(docs)["checks"] if c["severity"] == "error"}
    assert got == EXPECTED_ERRORS[k], f"{k}: expected {EXPECTED_ERRORS[k]}, got {got}"

# 3. label canonicalisation for model-extracted fields
assert kyc.canonical("udyam_certificate", {"Udyam Reg. Number": " UDYAM-KL-00-1 "})["Udyam reg. number"] == "UDYAM-KL-00-1"

# 4. eligibility rules
shop = dict(segment="micro", employees=2, sites=1, city_tier=2, has_gstin=False)
assert not cat.eligibility("P05", shop)[0]   # leased line needs 10+ employees and GSTIN
assert not cat.eligibility("P03", shop)[0]   # 1 Gbps fibre is tier-1 only
assert not cat.eligibility("P15", shop)[0]   # WhatsApp API needs GSTIN
assert cat.eligibility("P04", shop)[0]
assert not cat.eligibility("P10", dict(shop, employees=50, has_gstin=True))[0]  # SD-WAN needs 3 sites

# 5. bundles: always rule-compliant, dependency-complete, inside the price ceiling; quotes inside catalogue ranges
profiles = [
    dict(segment=s, business_type=b, employees=e, sites=n, city_tier=t, has_gstin=g, current_internet=i)
    for s, b, e, n, t, g, i in [
        ("micro", "Kirana store", 2, 1, 2, False, "Mobile hotspot"), ("micro", "Pharmacy", 4, 1, 1, True, "None"),
        ("prof", "Dental clinic", 12, 2, 2, True, "Home broadband"), ("prof", "CA firm", 8, 1, 1, True, ""),
        ("multi", "Restaurant chain", 60, 5, 1, True, "Mixed per site"), ("multi", "Gym chain", 20, 3, 2, False, ""),
        ("mfg", "Textile unit", 40, 1, 2, True, "Leased line"), ("mfg", "Printing press", 6, 1, 1, False, ""),
    ]
]
for p in profiles:
    for wanted in ([], ["P05", "P15", "P23"]):
        b = cat.build_bundle(p, score_products(p), wanted)
        ids = {it["id"] for it in b["items"]}
        assert ids, p
        assert all(cat.eligibility(i, p)[0] for i in ids), (p, ids)
        assert all(cat.dependency_ok(i, ids) for i in ids), (p, ids)
        assert len(ids) <= cat.MAX_ITEMS
        assert ids & set(cat.PRIMARY_INTERNET), "every bundle has an internet link"
        q = b["quote"]
        assert q["monthly_total"] <= cat.PRICE_CEILING[p["segment"]] or len(ids) == 1 or wanted, (p, q["monthly_total"])
        for line in q["lines"]:
            pr = cat.PRODUCTS[line["id"]]
            assert pr["price_min"] <= line["unit_price"] <= pr["price_max"], line
        for w in wanted:  # what the owner asked for is either included or explained
            assert w in ids or w in b["blocked"], (p, w)

# 6. longer contract never costs more
items = [{"id": "P02", "qty": 1}, {"id": "P16", "qty": 5}, {"id": "P23", "qty": 2}]
m = [cat.quote(items, c)["monthly_total"] for c in (12, 24, 36)]
assert m[0] >= m[1] >= m[2], m
assert cat.quote([{"id": "P10", "qty": 3}, {"id": "P02", "qty": 3}], 12)["contract_months"] == 24  # SD-WAN min 24

print("all core checks passed")
