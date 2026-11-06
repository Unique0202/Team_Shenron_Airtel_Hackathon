# Airtel Udyam: a small business goes digital in one sitting

Team Shenron, IIITD · Airtel Sync 2026, Digital Track · Case: Project Udyam Digital

A phone-first journey that takes a small business owner from "what do I need?" to "order placed" without a sales visit,
in their own language:

1. **Find your plan.** A chat advisor (10 Indian languages, voice input) learns about the business and recommends a bundle.
   The language model only talks and extracts the profile; eligibility rules, an ML ranker and pricing code decide what is offered.
2. **Your bill.** One clear monthly price, add-ons to toggle, 1/2/3-year plans.
3. **Verify business.** Consent first, GSTIN registry lookup, document photos read and cross-checked (20+ checks).
4. **Track order.** A timeline with expected dates, instead of calling support.

Plus `/partner`: leads that dropped out, ranked by a propensity model, for field sales and local partners.

All business data is synthetic (provided with the case). See `study.md` for the problem, `plan.md` for the design,
`analysis/findings.md` for what the data says.

## Run locally

```bash
# backend (Python 3.13)
cd backend
pip install -r requirements.txt
echo GEMINI_API_KEY=your_key > .env
python test_core.py                      # rules, pricing, KYC answer key: no key needed
uvicorn main:app --port 8000

# frontend (Node 20+)
cd frontend
npm install
npm run dev                              # http://localhost:3000, expects the API on :8000
```

Retrain the models: `python analysis/train_ranker.py`. Reproduce the analysis: `python analysis/eda.py`.

## Layout

```
data/       case data (leads, catalogue, mock GST/Udyam registries, KYC samples)
analysis/   eda.py, findings.md, train_ranker.py
backend/    FastAPI: agents.py, catalogue.py, kyc.py, privacy.py, ranker.py, main.py, tests
frontend/   Next.js: the journey, order tracker, partner console
docs/       case brief and submission template
```
