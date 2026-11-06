# Plan: Project Udyam Digital, Team Shenron (IIITD)

> Read `study.md` first for what the problem is; this file covers **what we build, why, and how**.

## Context

Airtel Sync 2026 Digital Track, Stage 1. **The deadline is tonight, 07 Nov 2026, 11:59 PM IST.** The only mandatory upload is a 7-slide deck (`Shenron_IIITD.pdf` + `.pptx`). Airtel's pre-hackathon webinar raised the bar beyond the case PDF:
- **Agentic AI architecture.** Airtel has its own in-house "Agent Bridge" platform, and they want to see how teams orchestrate agents.
- **A live deployed URL** is preferred over a recorded demo.
- **Regulated-entity privacy:** encryption at source and tokenization. If we use an external model, address data localization.
- **Ranking beyond simple weights:** metadata extraction + ML-based ranking.
- Judged on **end-to-end completeness** (discovery → fulfilment) and **analytical approach** (curiosity, structure, understanding the customer). Perfect accuracy isn't the bar.

**Decisions made:** Gemini (free tier) for the AI · Next.js frontend + FastAPI backend · branded **Airtel Business**, with a footnote that the data is synthetic · no mention of how the project was built.

**Rule for tonight:** the deck is the only thing we *must* upload. The prototype makes the deck credible. **Deck work starts at 8:00 PM IST no matter where the prototype stands.**

---

## 1. What we're building (the product)

**"Airtel Udyam": one phone-first journey, four steps, in the owner's language.**

```
Owner (phone, Hindi/English/regional)
   │
   ▼
1. ADVISOR AGENT ── chats, extracts a business profile ──► Rules engine (eligibility)
   │                                                      ► ML ranker (what similar businesses bought)
   ▼                                                      ► Explains the bundle in plain words
2. QUOTE ── one monthly price, toggle add-ons, pick 12/24/36-month contract (price updates live)
   │
   ▼
3. SMART KYC ── consent screen → GSTIN/Udyam lookup (pre-fills everything)
   │            → upload 4 docs → extract fields → cross-check → pass / fix-this list
   ▼
4. TRACKER ── order timeline with expected dates (from install days), no need to call support
   │
   ▼ (stretch)
5. PARTNER CONSOLE ── leads the advisor couldn't close, ranked by propensity score, for field sales / partners
```

### Why each piece exists (it maps to the drop reasons in the data)
| Piece | Drop reasons it removes (leads lost) |
|---|---|
| Advisor | No time for a visit (531) · visit not scheduled (296) · unreachable (805) |
| Quote | Quote too complex (206) · too slow (179) · price too high (414): right-sized bundles |
| Smart KYC | Missing GST/Udyam (94) · paperwork too long (79) · details didn't match (47) · signatory unavailable (53, via e-sign) |
| Tracker | Install delayed (98) · cancelled before install (53) · status chasing (3 calls per customer) |
| Partner console | Keeps field force and partners in the loop (Key Question 4) |

---

## 2. How it works (technical design)

### 2.1 Agents (our answer to "agentic architecture")
One **orchestrator** routes the conversation to three specialist agents. Each agent is a Gemini function-calling loop with its own tools. No heavy framework: the SDK's tool calling plus plain Python.

| Agent | Tools it can call | Deterministic or LLM? |
|---|---|---|
| **Advisor** | `extract_profile`, `eligible_products`, `rank_products`, `build_bundle`, `quote` | The LLM talks and extracts; **rules and pricing are pure code**, so it can't recommend an ineligible product |
| **KYC** | `lookup_gstin`, `lookup_udyam`, `extract_document` (Gemini vision), `validate_kyc` | Extraction by LLM; **all checks are pure code** |
| **Order** | `create_order`, `get_status` | Pure code (a state machine) |

### 2.2 Recommendation = metadata extraction + rules + ML ranking
1. **Metadata extraction.** The LLM turns free chat ("I run 2 dental clinics in Kochi, 12 staff, use Jio hotspot") into a structured profile: segment, business_type, employees, sites, city → tier, has_gstin, current_internet, needs[].
2. **Hard rules** (`product_catalogue.csv`): city tier, min employees/sites, GSTIN required, dependencies. Ineligible products are removed, never just scored down.
3. **ML ranker.** A multi-label model (scikit-learn: one-vs-rest gradient boosting or logistic regression) trained on `smb_leads.csv`. Features: segment, business_type, employees, sites, tier, turnover band, current internet, has_gstin. Labels: which products appear in `products_of_interest` (5,000 leads) and in `bundle_products` (368 activated, weighted higher). Output: P(product is wanted | profile).
4. **Bundle builder.** Takes the top-scored eligible products, adds missing dependencies (e.g. CCTV pulls in broadband), and sets quantities from profile (SIMs ≈ staff, connectivity per site). A segment price ceiling reflects price sensitivity, so a kirana doesn't get a ₹40k bundle.
5. **Explanation.** The LLM writes "why" in plain language, using the rule and ranker reasons we hand it.

### 2.3 Pricing logic (the catalogue gives ranges)
`monthly = max − (max − min) × discount`, where discount = **0** for a 12-month contract, **0.5** for 24 months, **1.0** for 36 months, plus a small multi-product bundle bonus capped at the range minimum. One-time setup fees are shown separately, and we offer **₹0 setup on 24+ months** as a lever against "price too high". The formula is simple, explainable and always inside the catalogue range.

### 2.4 Smart KYC checks (all deterministic, each one explained to the user)
- GSTIN **format + checksum** (real algorithm; accepts the `X` in the PAN, as the README requires)
- GSTIN exists in the registry and is **Active** (not Cancelled/Suspended)
- Udyam exists; its **name and state match** the GST record
- Names across GST cert / Udyam cert / address proof **match** (fuzzy, via stdlib `difflib`)
- Address proof **≤ 90 days old** relative to 2026-07-15
- **All 4 documents present** (K05 is missing its Udyam certificate)
- Signatory ID consistent with the GST legal name (for proprietorships)
- Before coding, we inspect all 47 images (K01–K12) and write down every planted problem, so each one has a check.

### 2.5 Privacy and security (DPDP Act + webinar asks)
- **Consent screen** before KYC: purpose, what's collected, retention, withdraw option.
- **Tokenization at source:** GSTIN, Udyam no., phone and names are replaced with tokens (`<GSTIN_1>`) before any text reaches the LLM, then swapped back server-side.
- **Masking** in UI and logs (`32TTNX•••••T1ZW`).
- **Data minimisation:** the GSTIN lookup pre-fills data instead of asking for it again; we only request the docs the chosen bundle needs.
- **Retention:** document images are deleted after verification; only the verification result is kept.
- **Localization note:** in production the model would run on an India-region endpoint (e.g. Vertex AI `asia-south1`) or Airtel's in-house platform; the prototype uses synthetic data only.

### 2.6 Stack and deployment
| Part | Tech | Hosted on |
|---|---|---|
| Frontend | Next.js (App Router) + Tailwind, mobile-first | Vercel (free) |
| Backend | FastAPI + scikit-learn + `google-genai` SDK; SQLite for orders | Render (free) |
| Voice input (stretch) | Browser's built-in Web Speech API: no extra service | – |

### 2.7 Repo layout
```
analysis/   eda.py (numbers for the deck) · train_ranker.py (→ backend/models/)
backend/    main.py (API + orders + partner console) · catalogue.py (rules + pricing + bundle) · ranker.py · kyc.py
            agents.py (advisor + KYC agents, model fallback) · privacy.py (tokenize/mask) · test_core.py · eval_kyc.py
frontend/   Next.js app: / (the 4-step journey), /track/[id], /partner
deck/       build_deck.py → Shenron_IIITD.pptx + .pdf (built on the official template)
```

---

## 3. The 7-slide deck

| # | Slide | Content |
|---|---|---|
| 1 | Title | Airtel Udyam · Team Shenron, IIITD · members · **live URL + repo link (+ video)** |
| 2 | The problem, in data | Funnel (7.4%), the 20 drop reasons grouped by fix, 17.6 days, ₹15k CAC, 9.6% vs 2.0% GSTIN effect + our own findings from the data |
| 3 | Approach: who and what | Priority segments + a starter bundle and price for each (Key Question 1) · the 4-step journey (Key Question 2) |
| 4 | The prototype | Screenshots of Advisor → Quote → KYC → Tracker |
| 5 | Architecture, agents and privacy | Agent diagram, data flows, recommendation pipeline, DPDP choices (Key Question 3) |
| 6 | Competitive analysis + go-to-market | Jio Business, Vi Business, Tata Tele Business Services, local ISPs/resellers, digital-first sign-ups: where each wins and loses vs us · role of the field force and partners (Key Question 4) |
| 7 | Impact and metrics | 4–5 metrics with baseline → target (conversion 7.4% → ~15%, time to activate 17.6 → ~5 days, CAC ₹15k → ~₹6k, status calls 3 → ~0, 6-month churn) · rollout · risks |

---

## 4. Tonight's schedule (in priority order; cut from the bottom)

| # | Step | Time | Output |
|---|---|---|---|
| 0 | **You:** get a Gemini API key (aistudio.google.com) · create Render + Vercel accounts linked to GitHub | 15 min | keys/accounts |
| 1 | Data analysis: conversion/churn by segment, source, language, tier and GSTIN; find the "planted signals"; baseline metrics | 45 min | `analysis/findings.md`, deck numbers |
| 2 | Inspect all 47 KYC images → list of planted problems | 20 min | KYC answer list |
| 3 | Backend core: rules, pricing, bundle, GSTIN checksum, registry lookups, KYC checks, orders + `test_core.py` | 1.5 h | working API, tests passing |
| 4 | ML ranker training + Gemini agents + tokenization | 1 h | `/chat` endpoint working |
| 5 | Frontend: 4 screens, mobile-first, language picker | 2 h | clickable journey |
| 6 | Deploy backend (Render) + frontend (Vercel) | 45 min | **live URL** |
| — | **8:00 PM: deck work starts, whatever state the prototype is in** | | |
| 7 | Competitive research (web) | 30 min | slide 6 content |
| 8 | Screenshots + build the deck on the template + PDF export | 1.5 h | `Shenron_IIITD.pptx/.pdf` |
| 9 | Final check + **upload on Unstop before 11:30 PM** (30 min buffer) | 15 min | submitted |
| stretch | Partner console + propensity score · voice input · 3-min demo video | only if time | – |

**What gets cut first if we're late:** the stretch goals → the partner console → regional languages beyond Hindi/English → the ML ranker falls back to rules + segment popularity (the deck still describes the ML design) → the Render backend becomes Next.js API routes. The deck is never cut.

---

## 5. Verification
- `python backend/test_core.py`: asserts that GSTIN checksum validates every registry GSTIN, eligibility rules block known-bad cases, quotes stay inside catalogue ranges, and KYC flags the expected problem for each of K01–K12.
- Advisor test: run ~15 personas we write ourselves (one per segment × size × GSTIN/no-GSTIN × tier, plus edge cases like a 2-employee shop asking for a leased line) through `/chat`; every recommended product must pass the rules engine.
- End-to-end browser check (Playwright) on the **deployed URL** at phone width: chat → quote → KYC with K01 docs (passes) and a bad applicant (flagged) → tracker. Screenshots double as deck images.
- Deck: open the PDF and check 7 slides, the file names, links working, size < 20 MB.
