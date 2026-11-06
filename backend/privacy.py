"""Tokenization at source: identifiers never reach the external model; they are swapped for tokens
and resolved back only inside our backend."""
import re

PATTERNS = [
    ("GSTIN", re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b", re.I)),
    ("UDYAM", re.compile(r"\bUDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}\b", re.I)),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I)),
    ("AADHAAR", re.compile(r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b")),
    ("PHONE", re.compile(r"(?:\+91[\s-]?)?\b[6-9][0-9]{9}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")),
]


def tokenize(text, vault):
    """Replace identifiers with <KIND_n> tokens; vault (dict) keeps token -> real value for this session."""
    reverse = {v: k for k, v in vault.items()}
    for kind, rx in PATTERNS:
        def swap(m):
            val = m.group(0).upper() if kind in ("GSTIN", "UDYAM", "PAN") else m.group(0)
            if val not in reverse:
                tok = f"<{kind}_{sum(k.startswith(f'<{kind}_') for k in vault) + 1}>"
                vault[tok], reverse[val] = val, tok
            return reverse[val]
        text = rx.sub(swap, text)
    return text


def detokenize(text, vault, masked=True):
    """Put identifiers back into model output (masked by default, for display)."""
    from kyc import mask
    for tok, val in vault.items():
        text = text.replace(tok, mask(val) if masked else val)
    return text


if __name__ == "__main__":
    v = {}
    t = tokenize("My GSTIN is 32ttnxb7384t1zw, call 9876543210 or a@b.in; GSTIN again 32TTNXB7384T1ZW", v)
    assert "32TTNXB" not in t.upper() and "9876543210" not in t and t.count("<GSTIN_1>") == 2, t
    assert detokenize(t, v, masked=False).startswith("My GSTIN is 32TTNXB7384T1ZW"), detokenize(t, v, masked=False)
    print("ok:", t)
