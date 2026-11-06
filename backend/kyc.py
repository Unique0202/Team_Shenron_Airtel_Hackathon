"""Smart KYC: registry lookups, GSTIN checksum and cross-document checks. Pure code, no LLM."""
import csv
import re
from datetime import date
from difflib import SequenceMatcher

from catalogue import DATA

TODAY = date(2026, 7, 15)  # README: use 2026-07-15 as "today" for date checks
MAX_BILL_AGE_DAYS = 90
DOC_TYPES = {
    "gst_certificate": "GST registration certificate",
    "udyam_certificate": "Udyam registration certificate",
    "signatory_id": "Authorised signatory ID",
    "address_proof": "Address proof (utility bill)",
}

LABELS = {  # field labels as printed on the documents; validate() reads these keys
    "gst_certificate": ["GSTIN", "Legal name", "Trade name", "Constitution", "Address of principal place of business",
                        "Date of liability", "Type of registration"],
    "udyam_certificate": ["Udyam reg. number", "Enterprise name", "Major activity", "City", "State",
                          "Date of registration"],
    "signatory_id": ["Name", "Designation", "For business", "ID no.", "Valid till"],
    "address_proof": ["Consumer no.", "Billed to", "Supply address", "Bill date", "Units consumed", "Amount due (INR)"],
}

GST_STATE = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand",
    "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh",
}

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
UDYAM_RE = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$")
B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _index(file, key):
    return {r[key]: r for r in csv.DictReader(open(DATA / file, encoding="utf-8"))}


GSTIN_DB = _index("mock_gstin_registry.csv", "gstin")
UDYAM_DB = _index("mock_udyam_registry.csv", "udyam_number")
UDYAM_STATE = {u.split("-")[1]: r["state"] for u, r in UDYAM_DB.items()}  # e.g. KL -> Kerala


def gstin_check_char(first14):
    total = 0
    for i, ch in enumerate(first14):
        v = B36.index(ch) * (2 if i % 2 else 1)
        total += v // 36 + v % 36
    return B36[(36 - total % 36) % 36]


def gstin_format(g):
    """(ok, reason). Real GSTIN structure + checksum; the README asks us to accept 'X' as PAN entity type."""
    g = (g or "").strip().upper()
    if not GSTIN_RE.match(g):
        return False, "GSTIN must be 15 characters: 2-digit state code, 10-character PAN, entity number, 'Z', check digit"
    if g[:2] not in GST_STATE:
        return False, f"'{g[:2]}' is not a valid GST state code"
    if gstin_check_char(g[:14]) != g[14]:
        return False, "GSTIN check digit is wrong (possible typo or tampered number)"
    return True, ""


TO_LETTER = str.maketrans("0158", "OISB")
TO_DIGIT = str.maketrans("OISBZ", "01582")


def fix_gstin_ocr(g):
    """Undo common photo misreads (O/0, I/1, S/5, B/8) using the GSTIN structure: letters where the format
    needs letters, digits where it needs digits. Accepted only if the result passes the checksum, so a
    genuinely altered number still fails."""
    g = (g or "").strip().upper().replace(" ", "")
    if len(g) != 15 or gstin_format(g)[0]:
        return g
    kinds = "DDLLLLLDDDDLAZA"  # D digit, L letter, A either, Z literal
    fixed = "".join(c.translate(TO_DIGIT) if k == "D" else c.translate(TO_LETTER) if k == "L" else c
                    for c, k in zip(g, kinds))
    for cand in {fixed, fixed[:14] + fixed[14].translate(TO_LETTER), fixed[:14] + fixed[14].translate(TO_DIGIT)}:
        if gstin_format(cand)[0]:
            return cand
    return g


def lookup_gstin(g):
    g = (g or "").strip().upper()
    ok, why = gstin_format(g)
    if not ok:
        return {"found": False, "error": why}
    r = GSTIN_DB.get(g)
    if not r:
        return {"found": False, "error": "GSTIN not found in the GST registry"}
    return {"found": True, **r}


def lookup_udyam(u):
    u = (u or "").strip().upper()
    if not UDYAM_RE.match(u):
        return {"found": False, "error": "Udyam number must look like UDYAM-XX-00-1234567"}
    r = UDYAM_DB.get(u)
    return {"found": True, **r} if r else {"found": False, "error": "Udyam number not found in the Udyam registry"}


def near_gstins(g):
    """Registry GSTINs exactly one character away from g (typo or tampering)."""
    g = (g or "").strip().upper()
    if len(g) != 15:
        return []
    same_glyph = str.maketrans("OI", "01")  # O/0 and I/1 are easy to misread on a photo; don't count them
    g = g.translate(same_glyph)
    return [r for r in GSTIN_DB if sum(a != b for a, b in zip(r.translate(same_glyph), g)) == 1]


def mask(s, keep_start=6, keep_end=4):
    """'32TTNXB7384T1ZW' -> '32TTNX•••••T1ZW'. Used for anything shown in UI or logs."""
    s = s or ""
    return s if len(s) <= keep_start + keep_end else s[:keep_start] + "•" * (len(s) - keep_start - keep_end) + s[-keep_end:]


def norm(s):
    s = re.sub(r"\(prop\.?\s*(.*?)\)", r"\1", (s or "").lower())
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", s)).strip()


def same(a, b, threshold=0.88):
    return bool(a and b) and SequenceMatcher(None, norm(a), norm(b)).ratio() >= threshold


def canonical(doc_type, fields):
    """Map extracted labels ('Udyam Reg. Number', 'GSTIN No') onto the labels validate() expects."""
    out = {k: v for k, v in fields.items() if k.startswith("_")}
    for key, val in fields.items():
        if key.startswith("_"):
            continue
        best = max(LABELS.get(doc_type, []), key=lambda lab: SequenceMatcher(None, norm(lab), norm(key)).ratio(),
                   default=None)
        if best and SequenceMatcher(None, norm(best), norm(key)).ratio() >= 0.75:
            out[best] = (val or "").strip()
        else:
            out[key] = val
    return out


def proprietor(legal_name):
    """'Neha Kaur (Prop. Vindhya Tours)' -> 'Neha Kaur'."""
    m = re.match(r"\s*(.*?)\s*\(prop", legal_name or "", re.I)
    return m.group(1) if m else None


def validate(docs):
    """docs: {doc_type: {field: value} or None}, using the field labels printed on the documents.

    Returns {"status": "verified" | "action_needed", "checks": [{id, ok, severity, message}], "registry": {...}}.
    """
    checks = []

    def add(cid, ok, message, severity="error"):
        checks.append({"id": cid, "ok": bool(ok), "severity": "ok" if ok else severity, "message": message})

    gst = docs.get("gst_certificate") or {}
    udy = docs.get("udyam_certificate") or {}
    sig = docs.get("signatory_id") or {}
    bill = docs.get("address_proof") or {}

    for t, label in DOC_TYPES.items():
        if not docs.get(t):
            add(f"{t}_present", False, f"{label} is missing. Please upload it.")
        elif docs[t].get("_unreadable"):
            add(f"{t}_readable", False, f"{label} is blurred or unreadable. Please upload a clearer photo.")

    # --- GST certificate vs GST registry
    reg_g = None
    if gst and not gst.get("_unreadable"):
        g = fix_gstin_ocr(gst.get("GSTIN", ""))
        ok, why = gstin_format(g)
        near = [] if ok else near_gstins(g)
        add("gstin_format", ok, "GSTIN format and check digit are valid" if ok else why + (
            f". It differs by one character from registered GSTIN {mask(near[0])}, so the number may have been altered"
            if near else ""))
        if ok:
            reg_g = GSTIN_DB.get(g.strip().upper())
            add("gstin_registry", reg_g, "GSTIN found in GST registry" if reg_g else "GSTIN not found in GST registry")
        if reg_g:
            add("gstin_active", reg_g["status"] == "Active",
                f"GST registration is {reg_g['status']}" + ("" if reg_g["status"] == "Active" else
                                                            ". Products that need a GSTIN cannot be activated"))
            add("gst_legal_name", same(gst.get("Legal name"), reg_g["legal_name"], 0.95),
                "Legal name matches GST registry" if same(gst.get("Legal name"), reg_g["legal_name"], 0.95)
                else f"Legal name on certificate ('{gst.get('Legal name')}') differs from registry ('{reg_g['legal_name']}')")
            add("gst_trade_name", same(gst.get("Trade name"), reg_g["trade_name"], 0.95),
                "Trade name matches GST registry" if same(gst.get("Trade name"), reg_g["trade_name"], 0.95)
                else f"Trade name on certificate ('{gst.get('Trade name')}') differs from registry ('{reg_g['trade_name']}')")
            addr = gst.get("Address of principal place of business")
            add("gst_address", same(addr, reg_g["principal_place_of_business"], 0.9),
                "Address matches GST registry" if same(addr, reg_g["principal_place_of_business"], 0.9)
                else "Address on GST certificate differs from GST registry", "warning")
            st = GST_STATE.get(g[:2])
            add("gst_state_code", st == reg_g["state"], f"GSTIN state code {g[:2]} = {st}" if st == reg_g["state"]
                else f"GSTIN state code {g[:2]} ({st}) does not match registered state {reg_g['state']}")
        prop = proprietor(gst.get("Legal name"))
        if prop and gst.get("Trade name"):
            inside = re.search(r"\(prop\.?\s*(.*?)\)", gst.get("Legal name", ""), re.I).group(1)
            add("gst_internal_names", same(inside, gst["Trade name"], 0.9),
                "Business name is consistent within the GST certificate" if same(inside, gst["Trade name"], 0.9)
                else f"GST certificate names two different businesses: '{inside}' and '{gst['Trade name']}'")

    # --- Udyam certificate vs Udyam registry and GST
    reg_u = None
    if udy and not udy.get("_unreadable"):
        u = (udy.get("Udyam reg. number") or "").strip()
        if not u:
            add("udyam_number", False, "Udyam registration number is blank on the certificate")
        else:
            res = lookup_udyam(u)
            add("udyam_registry", res["found"], "Udyam number found in Udyam registry" if res["found"] else res["error"])
            reg_u = res if res["found"] else None
        if reg_u:
            add("udyam_name", same(udy.get("Enterprise name"), reg_u["enterprise_name"]),
                "Enterprise name matches Udyam registry" if same(udy.get("Enterprise name"), reg_u["enterprise_name"])
                else f"Enterprise name differs from Udyam registry ('{reg_u['enterprise_name']}')")
            code_state = UDYAM_STATE.get(u.split("-")[1])
            add("udyam_state_code", code_state == reg_u["state"] == udy.get("State", reg_u["state"]),
                "Udyam state is consistent" if code_state == reg_u["state"] == udy.get("State", reg_u["state"])
                else "Udyam state code, certificate and registry disagree")
        biz = gst.get("Trade name") or (reg_g or {}).get("trade_name")
        if biz and udy.get("Enterprise name"):
            add("udyam_vs_gst_name", same(udy["Enterprise name"], biz),
                "Udyam and GST certificates are for the same business" if same(udy["Enterprise name"], biz)
                else f"Udyam is for '{udy['Enterprise name']}' but GST is for '{biz}'")
        gst_state = (reg_g or {}).get("state") or GST_STATE.get((gst.get("GSTIN") or "")[:2])
        if gst_state and udy.get("State"):
            add("udyam_vs_gst_state", udy["State"] == gst_state,
                "Udyam and GST are registered in the same state" if udy["State"] == gst_state
                else f"Udyam state ({udy['State']}) differs from GST state ({gst_state})")

    # --- Signatory ID
    if sig:
        biz = gst.get("Trade name") or udy.get("Enterprise name")
        add("signatory_business", same(sig.get("For business"), biz),
            "Signatory ID is issued for this business" if same(sig.get("For business"), biz)
            else f"Signatory ID is for '{sig.get('For business')}', not '{biz}'")
        prop = proprietor(gst.get("Legal name"))
        if prop:
            add("signatory_is_proprietor", same(sig.get("Name"), prop),
                f"Signatory {sig.get('Name')} is the registered proprietor" if same(sig.get("Name"), prop)
                else f"For a proprietorship the proprietor ({prop}) must sign, but the ID is for {sig.get('Name')}")
        constitution = gst.get("Constitution") or (reg_g or {}).get("constitution", "")
        needed = {"Limited Liability Partnership": ("Partner",), "Private Limited Company": ("Director",)}.get(constitution)
        if needed:
            d = sig.get("Designation", "")
            okd = any(n.lower() in d.lower() for n in needed)
            add("signatory_authority", okd, f"{d} can sign for a {constitution}" if okd else
                f"For a {constitution} the signatory is usually a {needed[0]}. A '{d}' needs an authorisation letter",
                "warning")
        try:
            valid = date.fromisoformat(sig.get("Valid till", ""))
            add("signatory_valid", valid >= TODAY, "Signatory ID is valid" if valid >= TODAY
                else f"Signatory ID expired on {valid}")
        except ValueError:
            add("signatory_valid", False, "Signatory ID validity date could not be read", "warning")

    # --- Address proof
    if bill:
        biz = gst.get("Trade name") or udy.get("Enterprise name")
        add("bill_name", same(bill.get("Billed to"), biz) or same(bill.get("Billed to"), gst.get("Legal name")),
            "Address proof is in the business's name" if same(bill.get("Billed to"), biz)
            or same(bill.get("Billed to"), gst.get("Legal name"))
            else f"Address proof is billed to '{bill.get('Billed to')}', not '{biz}'")
        gaddr = gst.get("Address of principal place of business") or (reg_g or {}).get("principal_place_of_business")
        add("bill_address", same(bill.get("Supply address"), gaddr, 0.9),
            "Supply address matches the GST address" if same(bill.get("Supply address"), gaddr, 0.9)
            else "Supply address on the bill differs from the GST address")
        try:
            age = (TODAY - date.fromisoformat(bill.get("Bill date", ""))).days
            add("bill_recent", 0 <= age <= MAX_BILL_AGE_DAYS,
                f"Bill is {age} days old (limit {MAX_BILL_AGE_DAYS})" if 0 <= age <= MAX_BILL_AGE_DAYS
                else f"Bill is {age} days old. Address proof must be from the last {MAX_BILL_AGE_DAYS} days")
        except ValueError:
            add("bill_recent", False, "Bill date could not be read", "warning")

    failed = [c for c in checks if c["severity"] == "error"]
    return {
        "status": "verified" if not failed else "action_needed",
        "checks": checks,
        "registry": {"gstin": reg_g, "udyam": reg_u},
    }
