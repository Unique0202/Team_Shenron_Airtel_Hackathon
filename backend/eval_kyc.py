"""Live check: read every sample document with the KYC agent, validate, compare with the answer key.
python eval_kyc.py   (needs GEMINI_API_KEY)"""
import time
from concurrent.futures import ThreadPoolExecutor

import main  # noqa: F401 - loads backend/.env
from agents import extract_document
from catalogue import DATA
from kyc import DOC_TYPES, validate
from test_core import EXPECTED_ERRORS

DOCS = DATA / "kyc_documents"


def read(path):
    for attempt in range(3):
        try:
            return extract_document(path.read_bytes(), "image/png")
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                return {"doc_type": "error", "fields": {}, "error": str(e)[:120]}
            time.sleep(5)


start = time.time()
paths = sorted(DOCS.glob("*.png"))
with ThreadPoolExecutor(4) as pool:
    out = dict(zip(paths, pool.map(read, paths)))

correct = 0
for k in sorted(EXPECTED_ERRORS):
    docs = {t: None for t in DOC_TYPES}
    for p, r in out.items():
        if p.name.startswith(k):
            slot = p.stem[len(k) + 1:]
            if r["doc_type"] != slot:
                print(f"  {p.name}: classified as {r['doc_type']} {r.get('error', '')}")
            docs[slot] = r["fields"]
    got = {c["id"] for c in validate(docs)["checks"] if c["severity"] == "error"}
    ok = got == EXPECTED_ERRORS[k]
    correct += ok
    print(f"{k} {'OK  ' if ok else 'MISS'} expected {sorted(EXPECTED_ERRORS[k]) or 'clean'} got {sorted(got) or 'clean'}")
print(f"\n{correct}/12 applicants match the answer key ({time.time() - start:.0f}s for {len(paths)} documents)")
