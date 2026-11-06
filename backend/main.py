"""Airtel Udyam API: advisor chat, quote, Smart KYC, order tracker, partner console."""
import os
import random
import uuid
from datetime import date, timedelta

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import catalogue as cat
import kyc
from ranker import propensity

app = FastAPI(title="Airtel Udyam API")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])

# ponytail: in-memory state, fine for a demo; move to Postgres/Redis when it has to survive restarts
SESSIONS, ORDERS = {}, {}
MAX_UPLOAD = 8 * 1024 * 1024
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "application/pdf"}


@app.get("/health")
def health():
    return {"ok": True}


# ---------------- advisor ----------------
class ChatIn(BaseModel):
    session_id: str | None = None
    message: str
    language: str = "English"


@app.post("/chat")
def chat(body: ChatIn):
    from agents import AdvisorSession  # needs GEMINI_API_KEY; the rest of the API works without it
    if not body.message.strip() or len(body.message) > 2000:
        raise HTTPException(400, "message must be 1-2000 characters")
    sid = body.session_id if body.session_id in SESSIONS else uuid.uuid4().hex
    s = SESSIONS.get(sid) or SESSIONS.setdefault(sid, AdvisorSession(body.language))
    try:
        reply, model_saw = s.send(body.message)
    except Exception as e:  # model quota / network: tell the user instead of a 500
        raise HTTPException(503, f"advisor unavailable: {type(e).__name__}")
    profile = {k: v for k, v in s.profile.items() if k != "gstin"}
    if "gstin" in s.profile:
        profile["gstin_masked"] = kyc.mask(s.profile["gstin"])
    return {"session_id": sid, "reply": reply, "model_saw": model_saw, "profile": profile, "bundle": s.bundle}


# ---------------- quote ----------------
class Item(BaseModel):
    id: str
    qty: int


class QuoteIn(BaseModel):
    items: list[Item]
    contract_months: int = 12


def _check_items(items):
    for it in items:
        if it.id not in cat.PRODUCTS or not 1 <= it.qty <= 100:
            raise HTTPException(400, f"bad item {it.id} x{it.qty}")
    ids = {it.id for it in items}
    for it in items:
        if not cat.dependency_ok(it.id, ids):
            names = ", ".join(cat.PRODUCTS[d]["name"] for d in cat.PRODUCTS[it.id]["requires_one_of"])
            raise HTTPException(400, f"{cat.PRODUCTS[it.id]['name']} needs one of: {names}")


@app.post("/quote")
def quote(body: QuoteIn):
    if body.contract_months not in cat.CONTRACTS:
        raise HTTPException(400, "contract_months must be 12, 24 or 36")
    _check_items(body.items)
    return cat.quote([it.model_dump() for it in body.items], body.contract_months)


@app.get("/catalogue")
def catalogue():
    return [{k: (sorted(v) if isinstance(v, set) else v) for k, v in p.items()} for p in cat.PRODUCTS.values()]


# ---------------- Smart KYC ----------------
@app.get("/lookup/gstin/{gstin}")
def lookup_gstin(gstin: str):
    r = kyc.lookup_gstin(gstin)
    if r["found"]:
        r["gstin"] = kyc.mask(r["gstin"])
    return r


@app.get("/lookup/udyam/{udyam}")
def lookup_udyam(udyam: str):
    r = kyc.lookup_udyam(udyam)
    if r["found"]:
        r["udyam_number"] = kyc.mask(r["udyam_number"], 9, 3)
    return r


@app.post("/kyc/extract")
async def kyc_extract(file: UploadFile = File(...)):
    from agents import extract_document
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(400, "upload a PNG, JPG, WEBP or PDF")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "file larger than 8 MB")
    try:
        out = extract_document(data, file.content_type)
    except Exception as e:
        raise HTTPException(503, f"document reader unavailable: {type(e).__name__}")
    # retention: the image is never written to disk; only extracted fields leave this function
    del data
    return out


class KycIn(BaseModel):
    docs: dict[str, dict | None]


@app.post("/kyc/validate")
def kyc_validate(body: KycIn):
    res = kyc.validate(body.docs)
    reg = res["registry"]
    if reg["gstin"]:
        reg["gstin"] = {**reg["gstin"], "gstin": kyc.mask(reg["gstin"]["gstin"])}
    if reg["udyam"]:
        reg["udyam"] = {**reg["udyam"], "udyam_number": kyc.mask(reg["udyam"]["udyam_number"], 9, 3)}
    return res


# ---------------- orders / tracker ----------------
STEPS = ["Order placed", "KYC verified", "Agreement e-signed", "Installation scheduled", "Installed", "Service active"]


class OrderIn(BaseModel):
    items: list[Item]
    contract_months: int = 12
    business_name: str = ""
    kyc_status: str = "verified"


def _timeline(o):
    start = date.fromisoformat(o["created"])
    days = [0, 0, 0, 1, o["quote"]["ready_in_days"], o["quote"]["ready_in_days"]]
    return [{"step": s, "expected": (start + timedelta(days=d)).isoformat(), "done": i <= o["step"]}
            for i, (s, d) in enumerate(zip(STEPS, days))]


@app.post("/orders")
def create_order(body: OrderIn):
    if body.kyc_status != "verified":
        raise HTTPException(400, "KYC must be verified before placing an order")
    _check_items(body.items)
    oid = f"UD{random.randint(100000, 999999)}"
    q = cat.quote([it.model_dump() for it in body.items], body.contract_months)
    ORDERS[oid] = {"id": oid, "business_name": body.business_name[:120], "created": date.today().isoformat(),
                   "quote": q, "step": 2}
    return order(oid)


@app.get("/orders/{oid}")
def order(oid: str):
    o = ORDERS.get(oid)
    if not o:
        raise HTTPException(404, "order not found")
    start = date.fromisoformat(o["created"])
    lines = [{"name": l["name"], "qty": l["qty"],
              "ready_by": (start + timedelta(days=l["install_days"])).isoformat()} for l in o["quote"]["lines"]]
    return {**o, "status": STEPS[o["step"]], "timeline": _timeline(o), "lines": lines}


@app.post("/orders/{oid}/advance")
def advance(oid: str):
    """Demo control: simulates the field team completing the next step."""
    o = ORDERS.get(oid) or {}
    if not o:
        raise HTTPException(404, "order not found")
    o["step"] = min(o["step"] + 1, len(STEPS) - 1)
    return order(oid)


# ---------------- partner console ----------------
def _partner_leads():
    L = pd.read_csv(cat.DATA / "smb_leads.csv")
    open_ = L[L.outcome.eq("Dropped") & L.stage_reached.isin(["Lead", "Contacted", "Needs assessed"])].copy()
    rows = [{"segment": cat.SEGMENT_CODE[r.segment], "business_type": r.business_type, "city_tier": r.city_tier,
             "turnover_band": r.annual_turnover_band, "current_internet": r.current_internet,
             "has_gstin": r.has_gstin == "Y", "has_udyam": r.has_udyam == "Y", "employees": r.employee_count,
             "sites": r.num_sites, "lead_source": r.lead_source, "language": r.preferred_language}
            for r in open_.itertuples()]
    open_["score"] = propensity(rows)
    action = {
        "Unreachable after 3 attempts": "Send WhatsApp link to the self-serve advisor",
        "Owner had no time for a visit": "Send WhatsApp link to the self-serve advisor",
        "Visit not scheduled by sales": "Send WhatsApp link to the self-serve advisor",
        "Quote took too long to arrive": "Share instant quote link",
        "Quote too complex to understand": "Share instant quote link",
        "Price too high": "Offer 24-month price (setup halved)",
        "Competitor offered cheaper plan": "Offer 24-month price (setup halved)",
        "Locked in with current provider": "Schedule follow-up at contract end",
        "Only wanted a mobile plan": "Sell mobile plan now, upsell later",
    }
    open_["next_action"] = open_.drop_reason.map(action).fillna("Partner call in preferred language")
    top = open_.sort_values("score", ascending=False).head(60)
    return [{"lead_id": r.lead_id, "business": r.business_name, "type": r.business_type, "city": r.city,
             "language": r.preferred_language, "source": r.lead_source, "dropped_at": r.stage_reached,
             "reason": r.drop_reason, "contact": f"{r.contact_name.split()[0]} {r.contact_name.split()[-1][0]}.",
             "score": r.score, "next_action": r.next_action} for r in top.itertuples()]


PARTNER_LEADS = _partner_leads()


@app.get("/partner/leads")
def partner_leads():
    return PARTNER_LEADS
