"""The two LLM agents. Advisor: chat + metadata extraction, with the rules engine and ML ranker as tools.
KYC: reads document images into fields. Every decision (eligibility, price, validity) is made by code."""
import csv
import json
import os

from google import genai
from google.genai import types

import catalogue as cat
import kyc
from privacy import detokenize, tokenize
from ranker import score_products

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_client = None


def client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


CITY_TIER = {r["city"].lower(): int(r["city_tier"])
             for r in csv.DictReader(open(cat.DATA / "smb_leads.csv", encoding="utf-8"))}
LANGUAGES = ["English", "Hindi", "Marathi", "Tamil", "Telugu", "Kannada", "Gujarati", "Bengali", "Punjabi", "Malayalam"]
CATALOGUE_TEXT = "\n".join(f"{p['id']}: {p['name']} ({p['category']}) - {p['description']}" for p in cat.PRODUCTS.values())

ADVISOR_PROMPT = """You are "Udyam Mitra", Airtel Business's advisor for small businesses in India. You replace the
sales visit: in a short chat you understand the business and recommend the right bundle with one clear monthly price.

LANGUAGE: Always reply in {language}, in simple everyday words (use the script of that language; English
product names are fine). Keep every message short: it is read on a phone. Ask at most 2 questions per message.

WHAT TO LEARN (call update_profile as soon as you learn anything, even mid-conversation):
- type of business, and which segment it is: micro (shop, salon, pharmacy, kirana, small retail/services),
  prof (clinic, CA/law firm, coaching, agency, office), multi (chain with several outlets/branches),
  mfg (manufacturing/factory unit)
- number of employees, number of sites/outlets, city
- whether they have a GST registration (GSTIN). If they share the number it appears as a token like <GSTIN_1>;
  pass that token to verify_gstin. Never ask them to type Aadhaar/PAN.
- current internet/phone setup, and what they want to do (UPI/billing, CCTV, WhatsApp customers, email, backup...)
Infer what you safely can (a "kirana in Pune" is micro, tier 1); ask only for what is missing.

RECOMMEND: once you know segment, employees, sites, city and GST status, call recommend_bundle. Pass product ids
the owner explicitly asked for in wanted_product_ids. Then explain the bundle in 3-5 short lines: what each
product does for THEIR business (use the reasons from the tool), the monthly total and one-time setup. Say they can
switch add-ons on/off and pick a longer contract for a lower price on the next screen.
- Use ONLY prices and products returned by the tool. Never invent prices, discounts or products.
- If a product they wanted is in "blocked", explain why kindly and what we added instead.
- No GSTIN: reassure them that they still get a bundle without GST paperwork, and that GST-only products
  (WhatsApp API, SMS, toll-free, etc.) unlock once they register. We can help with GST registration.
- If they only want a mobile plan, recommend just that (they can add more later).
- Off-topic, or anything outside our catalogue: politely steer back.
If they change something later (more staff, another branch), update_profile and recommend again.

CATALOGUE (for mapping needs to product ids; prices come only from the tool):
{catalogue}
"""


class AdvisorSession:
    def __init__(self, language="English"):
        self.language = language if language in LANGUAGES else "English"
        self.profile = {}
        self.bundle = None
        self.vault = {}  # privacy token -> real value, never leaves the backend
        self.chat = client().chats.create(model=MODEL, config=types.GenerateContentConfig(
            system_instruction=ADVISOR_PROMPT.format(language=self.language, catalogue=CATALOGUE_TEXT),
            tools=[self.update_profile, self.verify_gstin, self.recommend_bundle],
            temperature=0.3,
        ))

    # ---- tools (the model calls these; docstrings are what it sees) ----
    def update_profile(self, business_type: str = "", segment: str = "", employees: int = 0, sites: int = 0,
                       city: str = "", has_gstin: str = "", current_internet: str = "", needs: str = "") -> dict:
        """Save what you learned about the business. Only pass fields you learned; leave others empty.
        segment: one of micro, prof, multi, mfg. has_gstin: "yes" or "no".
        current_internet: e.g. Mobile hotspot, Home broadband, Business broadband, Leased line, None."""
        p = self.profile
        if business_type: p["business_type"] = business_type
        if segment in cat.SEGMENTS: p["segment"] = segment
        if employees: p["employees"] = int(employees)
        if sites: p["sites"] = int(sites)
        if city:
            p["city"] = city
            p["city_tier"] = CITY_TIER.get(city.strip().lower(), 2)  # unknown city: assume tier 2 (fewer products)
        if has_gstin.lower() in ("yes", "no") and not p.get("gstin_verified"):
            p["has_gstin"] = has_gstin.lower() == "yes"
        if current_internet: p["current_internet"] = current_internet
        if needs: p["needs"] = needs
        return {"saved": {k: v for k, v in p.items() if k != "gstin"}, "still_missing": self._missing()}

    def verify_gstin(self, gstin_token: str) -> dict:
        """Check a GSTIN the owner shared (pass the token, e.g. <GSTIN_1>) against the GST registry."""
        res = kyc.lookup_gstin(self.vault.get(gstin_token.strip(), gstin_token))
        if not res["found"]:
            return {"valid": False, "reason": res["error"]}
        self.profile.update(has_gstin=res["status"] == "Active", gstin_verified=True, gstin=res["gstin"])
        return {"valid": True, "status": res["status"], "business_name": res["trade_name"],
                "constitution": res["constitution"], "state": res["state"]}

    def recommend_bundle(self, wanted_product_ids: list[str] | None = None) -> dict:
        """Build the recommended bundle for the saved profile. wanted_product_ids: ids the owner explicitly asked for."""
        if self._missing():
            return {"error": "need more information first", "still_missing": self._missing()}
        wanted = [w for w in (wanted_product_ids or []) if w in cat.PRODUCTS]
        scores = score_products(self.profile)
        b = cat.build_bundle(self.profile, scores, wanted)
        b["scores"] = dict(sorted(scores.items(), key=lambda kv: -kv[1])[:8])
        self.bundle = b
        q = b["quote"]
        return {
            "products": [{"name": l["name"], "qty": l["qty"], "monthly_inr": l["monthly"], "why": b["reasons"][l["id"]]}
                         for l in q["lines"]],
            "monthly_total_inr": q["monthly_total"], "one_time_setup_inr": q["setup_total"],
            "contract_months": q["contract_months"], "ready_in_days": q["ready_in_days"],
            "blocked": {cat.PRODUCTS[k]["name"]: v for k, v in b["blocked"].items()},
            "optional_addons": [a["name"] for a in b["addons"]],
        }

    def _missing(self):
        need = ["segment", "employees", "sites", "city_tier", "has_gstin"]
        return [k for k in need if k not in self.profile]

    def send(self, text):
        """Returns (reply for the owner, exactly what the model was sent)."""
        safe = tokenize(text, self.vault)
        reply = self.chat.send_message(safe).text or ""
        return detokenize(reply, self.vault), safe


EXTRACT_PROMPT = """This is a photo or scan of an Indian business KYC document. Identify its type and read it.
doc_type: one of gst_certificate, udyam_certificate, signatory_id, address_proof, other.
Copy every label/value pair exactly as printed, using the printed label as the key. Values that wrap onto the next
line belong together (join them). Ignore watermarks. Write dates as printed. If a label is printed with no value,
use "". legible: false if the image is too blurred, cropped or dark to read the ID numbers with confidence.
Return JSON: {"doc_type": "...", "legible": true, "fields": {"Label": "value", ...}}"""


def extract_document(data: bytes, mime_type: str) -> dict:
    resp = client().models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=data, mime_type=mime_type), EXTRACT_PROMPT],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
    )
    out = json.loads(resp.text)
    doc_type = out.get("doc_type", "other")
    fields = kyc.canonical(doc_type, out.get("fields") or {})
    if not out.get("legible", True):
        fields["_unreadable"] = True
    return {"doc_type": doc_type, "fields": fields}
