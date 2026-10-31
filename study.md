# Study Notes: Airtel Sync 2026, Digital Track

**Team:** Shenron · **Campus:** IIITD · **Case:** Project Udyam Digital

This file explains the whole challenge in plain words: what the competition is, what problem we're solving, what data we have, and what we have to build and submit. If you read only one file before starting, read this one.

---

## 1. The one-paragraph version

Small businesses in India (kirana shops, clinics, CA firms, restaurants) need internet, business SIMs, WhatsApp for customers, CCTV, billing software and so on. A telecom company already sells all of this, but the buying process is slow and painful. A salesperson has to visit, the quote takes days and is full of codes nobody understands, the paperwork is physical, and setup takes two weeks. So most interested businesses give up halfway. Only **7 out of 100** end up as customers. **Our job is to design and build a phone-first, self-service journey where a business owner can chat (in their own language) and get the right bundle recommended, see one clear monthly price, finish KYC in minutes, and track their order. Then we pitch the idea and its business case in a 7-slide deck.**

---

## 2. The competition

| | |
|---|---|
| Name | Airtel Sync 2026, Digital Track (hosted on Unstop) |
| Team | 2 members (final-year CS/IT/AI students) |
| Stage 1 deadline | **07 Nov 2026, 11:59 PM IST** |

### Stages
1. **Case Release & Detailed Submission** ← *we are here.* Submit a 7-slide deck.
2. **Virtual Presentation.** Shortlisted teams present the deck online to Airtel leaders.
3. **Mentorship.** The top 15 teams get mentored by Airtel leaders.
4. **Grand Finale.** At the Airtel office: 15 minutes to present, 5 minutes of jury questions.

### What we upload in Stage 1
- A **7-slide PPT**, uploaded twice: once as **PDF** and once as **PPTX** (max 20 MB each).
- File names: **`Shenron_IIITD.pdf`** and **`Shenron_IIITD.pptx`**.
- It must show: **our approach**, a **detailed competitive analysis**, and the **impact** of our solution.
- We must use the official template: `docs/Submission Template_Sync.pptx`. It has one title slide and one blank content slide with the Airtel/SYNC/Unstop branding.

### What the case PDF additionally asks for
The case document (`docs/Airtel_SYNC_Case.pdf`) lists these deliverables:
1. **Working prototype**: a demo video (max 3 minutes) plus a code repository
2. **Solution architecture diagram**: the main parts of the system and how data flows between them
3. **Business case**: 10 slides or fewer covering target customer, value, pricing/savings, rollout and risks
4. **1-page privacy & security note**: how we protect customer data

The upload page only accepts the 7-slide deck, so these four have to **fit inside the deck**: the architecture and privacy content as slides, and the video and repo as links. The stage name says "Detailed *Prototype* Submission", so we should have a working prototype by the deadline.

---

## 3. The story behind the case

The case uses a **fictional** company so no real company data is exposed:

- **Accel Telecom**: India's #1 mobile operator and a top-2 home broadband player. It's a stand-in for Airtel.
- **Accel Business**: its B2B arm (business customers).

Accel Business is good at serving **large corporates**, but has a small share of India's **6 crore+ MSMEs** (micro, small and medium enterprises).

### What a small business needs today
A typical clinic or shop now wants:
- Broadband or a leased line
- A few business SIM cards
- A WhatsApp/SMS channel to reach customers
- Cloud email and storage
- Basic cybersecurity
- CCTV, or connectivity for a POS (billing machine)

Today the owner buys each of these from a **different vendor**, often a local reseller, with **no single bill and no single support number**.

### Why buying from Accel is painful today
Accel sells most of these products, but **one at a time, through a field sales force built for big companies**:

| Step | What happens today | Why it hurts |
|---|---|---|
| Discovery | A salesperson visits and often pushes whatever product is on this month's target | The owner has to make time for a visit, and the advice is biased |
| Quote | Takes **3–5 days** and arrives as a PDF with product codes | Slow and confusing |
| KYC | GST certificate, Udyam certificate, address proof and signatory ID, collected physically or over email | Paper-heavy, and easy to get wrong |
| Installation | **10–14 days**, and the customer calls **3–4 times** to chase it | Frustrating, and costly for support |
| After sale | Each product is billed and supported separately | No single view for the customer |

**Result:** customer acquisition is expensive, few leads convert, and many interested businesses drop out. Meanwhile competitors and digital-first players are starting to offer **instant online sign-up**, though only for single products.

---

## 4. The numbers that prove the problem

The data covers **5,000 business leads from one quarter (Apr–Jun 2026)**.

### The funnel: how many survive each step
| Stage | Leads left | % of previous stage |
|---|---|---|
| Lead created | 5,000 | – |
| Contacted | 3,406 | 68% |
| Needs assessed | 1,974 | 58% |
| Quote accepted | 861 | **44%** ← biggest drop |
| KYC complete | 588 | 68% |
| Activated | **368** | 63% |

### Headline facts
- Only **7.4%** of leads become customers.
- Activation takes **17.6 days** on average, and customers chase their status **3 times**.
- It costs about **₹15,000** to acquire one customer. For comparison, the median bundle is ₹6,900/month, and micro businesses pay only about ₹2,500/month.
- Leads **with a GSTIN activate at 9.6%; without one, only 2.0%.**

### Why people drop out (from `smb_leads.csv`)
This is the most useful table in the case: every drop reason points to something our product should fix.

| Dropped at | Reason | Count | What fixes it |
|---|---|---|---|
| Lead | Unreachable after 3 attempts | 805 | Self-serve journey: the customer starts it on their own time (web/WhatsApp) |
| Lead | Not interested on first call | 470 | Better targeting / lead scoring |
| Lead | Wrong or invalid number | 319 | Phone verification (OTP) at sign-up |
| Contacted | Owner had no time for a visit | 531 | **Advisor** replaces the sales visit |
| Contacted | Locked in with current provider | 325 | Switching offer, competitive pricing |
| Contacted | Visit not scheduled by sales | 296 | **Advisor**, no visit needed |
| Contacted | Only wanted a mobile plan | 280 | Let them buy just that, then upsell later |
| Needs assessed | Price too high | 414 | Right-sized bundles, toggleable add-ons |
| Needs assessed | Competitor offered cheaper plan | 207 | Competitive pricing |
| Needs assessed | Quote too complex to understand | 206 | **Quote**: one plain-language monthly price |
| Needs assessed | Quote took too long to arrive | 179 | **Quote**: instant |
| Needs assessed | Decided to wait | 107 | Follow-up nudges |
| Quote accepted | Missing GST or Udyam document | 94 | **Smart KYC** with registry lookup |
| Quote accepted | Found paperwork too long | 79 | **Smart KYC**, auto-filled forms |
| Quote accepted | Authorised signatory not available | 53 | Remote e-sign |
| Quote accepted | Document details did not match | 47 | **Smart KYC** catches mismatches instantly |
| KYC complete | Installation delayed beyond 21 days | 98 | **Tracker** + realistic install dates |
| KYC complete | Customer cancelled before install | 53 | **Tracker** keeps them informed |
| KYC complete | Site not feasible for fibre | 41 | Check feasibility *before* the quote; offer 5G AirFiber |
| KYC complete | First payment failed | 28 | Retry / payment options |

---

## 5. The problem statement

> **Design and build a digital-first acquisition and onboarding journey that lets a small business owner discover the right bundle, buy it and get it activated with minimal human effort, on a phone, in their preferred language.**

### The 5 key questions we must answer (in the deck)
1. **Who first?** Which kinds of small businesses should Accel target first, and what bundle fits each (products, price, contract length)?
2. **Discovery without a salesperson.** How does a chat/voice advisor (in Hindi and regional languages) ask a few questions and recommend a bundle with a clear monthly price?
3. **Near-instant KYC that stays legal.** How do we use GSTIN/Udyam lookup, document scanning, DigiLocker and e-sign while following India's data protection law (the DPDP Act, 2023)?
4. **Field force and partners.** The existing salespeople and local resellers shouldn't see the app as a threat. What role do they play, so the digital journey helps them?
5. **Measuring success.** Which 3–5 numbers matter (e.g. conversion, time to activate, cost per customer, churn), and what targets do we set?

---

## 6. What we must build (the prototype)

Think of it as **one journey with four screens**, seen from the business owner's side:

### 6.1 Advisor ("tell me about your business")
- A **GenAI chat assistant** that asks about the business: type, size (employees), number of locations, city, current internet and tools.
- It **recommends a bundle from the product catalogue** and **explains why in plain language** (e.g. "You have 2 clinics and store patient records, so we added cloud backup and a firewall").
- It must follow the catalogue's **eligibility rules** (see §8). Example: it can't offer a leased line to a 3-person shop, or a GST-only product to someone without a GSTIN.
- Ideally it works in **Hindi and regional languages**.
- ⚠️ The judges will run **15 secret test scenarios live** on our advisor during the demo, so it has to be robust, not scripted.

### 6.2 Quote & checkout ("what will I pay?")
- **One clear monthly price** for the whole bundle, plus one-time setup fees.
- **Add-ons the owner can switch on/off**, with the price updating live.
- No product codes; plain names only.

### 6.3 Smart KYC ("prove who you are")
- A **consent screen** first: what data we collect, why, and how long we keep it.
- **Mock GSTIN and Udyam lookups**: the owner types their number and we fetch their details from the mock registry CSVs.
- **Document upload with extraction and validation**: read the uploaded certificate images (OCR), pull out fields, and check them against the registry and against each other.
- **Catch problems**: the 12 sample applicants (K01–K12) include planted issues. The judges have an answer key.

### 6.4 Tracker ("where is my order?")
- An **order status page**, so the owner doesn't need to call support.
- Steps like: order placed → KYC verified → installation scheduled → installed → active.
- Expected dates come from each product's `typical_install_days`.

### Stretch goals (bonus points)
- A **voice or WhatsApp** front end
- A **back-office dashboard** for sales/partners showing leads the advisor couldn't close
- A **propensity score**: a simple model saying which leads are worth calling

---

## 7. The data we've been given (`data/`)

All data is **synthetic**: fictional businesses, people and IDs. The pack's own guide is `data/README.md`.

| File | Rows | What it is | We use it for |
|---|---|---|---|
| `product_catalogue.csv` | 25 | Every product with price range, setup fee, contract length, eligibility rules and dependencies | Advisor recommendations + quote |
| `smb_leads.csv` | 5,000 | One quarter of leads: business profile, how far they got, why they dropped, and (for customers) what they bought, churn and NPS | Business case analysis, segment choice, propensity score, realistic test personas |
| `mock_gstin_registry.csv` | 3,534 | Fake GST registry: GSTIN, legal name, trade name, business type, address, state, status (**Active 3,266 / Cancelled 167 / Suspended 101**) | Backs our "GSTIN lookup" API |
| `mock_udyam_registry.csv` | 2,723 | Fake Udyam (MSME) registry: number, name, Micro/Small/Medium, activity, city | Backs our "Udyam lookup" API |
| `kyc_documents/` | 47 images | Sample documents for 12 applicants (K01–K12): GST certificate, Udyam certificate, signatory ID, address proof (electricity bill) | Testing Smart KYC (OCR + validation) |

### Quick facts about the leads
- **Segments:** Micro retail & services 2,709 · Professional offices 1,247 · Multi-site 755 · Manufacturers 289
- **Lead sources:** Field sales 1,720 · Channel partner 1,010 · Website 995 · Inbound call 504 · Referral 413 · WhatsApp 358
- **Languages:** Hindi 2,137 · English 1,168 · Marathi 505 · Kannada 253 · Gujarati 233 · Telugu 207 · Tamil 207 · Bengali 111 · Punjabi 96 · Malayalam 83
- **Cities:** roughly half tier 1, half tier 2
- **Current internet:** mobile hotspot 1,799 · business broadband 1,433 · home broadband 1,250 · mixed 221 · leased line 173 · none 124
- **Current provider:** 1,505 already use **Accel for mobile only**. These are warm leads to upsell.

### Important rules hidden in the README
- **"Today" is 2026-07-15** for any date check (e.g. address proof must be **no older than 90 days**).
- GSTINs are in the **real 15-character format with a valid checksum**, so we can build a real format validator. One catch: the 4th character of the embedded PAN is always **`X`**, which isn't valid in real life, so our validator must accept `X`.
- Udyam numbers look like `UDYAM-KL-00-3078801`. District code `00` doesn't exist in reality, which is on purpose.
- **Privacy:** treat the data as if it were real. Collect only what's needed, show consent before KYC, **mask IDs in logs and the UI**, and explain how long documents are kept.

### Things already noticed in the KYC images
- **K05 has no Udyam certificate** (that's why there are 47 images, not 48). It's probably a planted problem.
- The documents have a diagonal **"SYNTHETIC SPECIMEN" watermark** over the text, and long addresses **wrap mid-word** onto the next line ("…Visakhapatnam, A / ndhra Pradesh"). OCR has to cope with both.

---

## 8. The products (`product_catalogue.csv`)

Segment codes: **micro** = micro retail & services, **prof** = professional offices, **multi** = multi-site, **mfg** = manufacturers.

| ID | Product | In plain words | ₹/month | Min. size | Needs GSTIN? | Needs one of |
|---|---|---|---|---|---|---|
| P01 | Biz Fibre 100 | 100 Mbps office broadband | 999–1,199 /site | – | No | – |
| P02 | Biz Fibre 300 | 300 Mbps broadband | 1,499–1,799 /site | – | No | – |
| P03 | Biz Fibre 1G | 1 Gbps broadband, priority support (**tier 1 cities only**) | 3,999–4,499 /site | 5 employees | **Yes** | – |
| P04 | 5G AirFiber 100 | Wireless broadband for places without fibre, plug and play | 899–1,099 /site | – | No | – |
| P05 | Leased Line 20 | Dedicated 20 Mbps, 99.5% uptime guarantee (₹10k setup, 21 days to install) | 8,000–12,000 /site | 10 employees | **Yes** | – |
| P06 | Leased Line 100 | Dedicated 100 Mbps, 99.9% uptime (₹15k setup, 30 days) | 25,000–35,000 /site | 25 employees | **Yes** | – |
| P07 | Postpaid 299 | Business SIM, 50 GB, unlimited calls | 299–399 /line | – | No | – |
| P08 | Postpaid 599 | Business SIM, 150 GB, roaming, priority care | 599–799 /line | – | No | – |
| P09 | Backup Failover | Router that switches to 4G/5G if main internet dies | 499–599 /site | – | No | P01/02/03/05/06 |
| P10 | Managed SD-WAN | Manage internet across many branches centrally | 2,500–3,500 /site | 10 emp, **3 sites** | **Yes** | P01/02/03/05/06 |
| P11 | Static IP | Fixed internet address (for CCTV, servers) | 200–300 /IP | – | No | P01/02/03 |
| P12 | Cloud Telephony | Office phone lines over internet, IVR, recording | 1,000–1,500 /channel | 3 employees | **Yes** | any internet P01–P06 |
| P13 | Toll-free Number | 1800 number | 1,500–2,000 | – | **Yes** | – |
| P14 | Business SMS 10k | 10,000 SMS/month for alerts and offers | 1,500–2,000 | – | **Yes** | – |
| P15 | WhatsApp Business API | Verified WhatsApp with catalogue, 1,000 chats/month | 999–1,499 | – | **Yes** | – |
| P16 | Cloud Email & Office | Email on own domain, docs, video calls | 125–150 /user | – | No | – |
| P17 | Cloud Backup 1 TB | Auto backup of PCs and phones | 499–699 | – | No | – |
| P18 | Website + Domain | Domain and a simple 5-page website | 299–499 | – | No | – |
| P19 | Cloud POS & Billing | GST billing, inventory, UPI/card on a tablet | 599–899 /counter | – | No | – |
| P20 | Endpoint Security | Antivirus / ransomware protection | 99–149 /device | – | No | – |
| P21 | Managed Firewall | Professionally managed firewall at the office | 1,999–2,999 /site | 10 employees | **Yes** | P01/02/03/05/06 |
| P22 | Secure Wi-Fi + Guest | Managed Wi-Fi with a separate customer network | 399–599 /site | – | No | P01/02/03/04 |
| P23 | Cloud CCTV | HD camera with 30-day cloud recording | 199–299 /camera | – | No | any internet P01–P06 |
| P24 | Machine Monitoring IoT | Sensors tracking machine uptime and energy | 149–249 /device | 10 employees | **Yes** | – |
| P25 | Fleet Tracker | GPS tracker for vehicles | 199–299 /vehicle | – | No | – |

### Rules the advisor must respect
- **City tier:** only sell a product where it's available. P03 is tier 1 only; everything else is tier 1 and 2.
- **Minimum size:** `min_employees` and `min_sites` must be met.
- **GSTIN:** if `requires_gstin = Y`, the customer must have a **valid and Active** GSTIN. Cancelled or suspended doesn't count.
- **Dependencies:** if a product says "needs one of", the bundle must include at least one of those. CCTV is useless without internet.
- **Install time:** `typical_install_days` drives the expected activation date in the Tracker.
- Most products also have a **one-time setup fee** and a **minimum contract** (mostly 12 months).

---

## 9. Customer segments (from the case appendix)

| Segment | Share of SMBs | Examples | What they use today | What they need | Price sensitivity |
|---|---|---|---|---|---|
| Micro retail & services | 55% | Kirana, salon, pharmacy | Owner's mobile + hotspot, UPI QR | Reliable internet for UPI/POS, WhatsApp catalogue | **Very high** |
| Professional offices | 25% | Clinic, CA firm, coaching centre | Home broadband, personal Gmail | Uptime, cloud email/storage, data security | Medium |
| Small multi-site | 15% | Restaurant chain, 3–10 stores | A different ISP at each site, no central IT | One bill, central management, CCTV, failover | Medium–low |
| Small manufacturers | 5% | Auto-parts unit, textile unit | Leased line or local ISP | Dedicated bandwidth, IoT for machines, ERP access | Low |

The trade-off: micro is the biggest group but the least willing to pay, while manufacturers pay the most but are few. Choosing which segment to go after first is one of the key questions.

---

## 10. KYC and compliance, explained

| Term | Plain meaning |
|---|---|
| **KYC** | "Know Your Customer": proving the business and the person signing are real |
| **GSTIN** | 15-character GST tax ID of a business. Structure: `2-digit state code + 10-char PAN + entity no. + 'Z' + check digit`. Example: `32TTNXB7384T1ZW` (32 = Kerala) |
| **PAN** | Permanent Account Number (income-tax ID). It's embedded inside the GSTIN |
| **Udyam registration** | The government's free MSME registration. It proves the business is a micro/small/medium enterprise. Format: `UDYAM-<state>-<district>-<7 digits>` |
| **Signatory ID** | ID of the person legally allowed to sign for the business |
| **Address proof** | Here, an electricity bill. It must be **≤ 90 days old** (as of 2026-07-15) |
| **OCR** | Reading text out of an image of a document |
| **DigiLocker** | Government app where citizens' verified documents are stored. A company can fetch them with the user's permission, so there's nothing to upload |
| **e-sign** | Legally valid digital signature (usually Aadhaar OTP-based), so no physical signing is needed |
| **DPDP Act, 2023** | India's Digital Personal Data Protection Act. Key ideas we must show: **consent** (ask clearly before collecting), **purpose limitation** (use data only for the stated reason), **data minimisation** (collect only what's needed), **retention limits** (delete when no longer needed), and the user's right to withdraw consent |

### Checks Smart KYC should do (likely)
- Is the GSTIN in the right format with a correct checksum? Does it exist in the registry? Is it **Active**?
- Does the name/address on the certificate **match** the registry and the other documents?
- Do the Udyam details match the GST details (same business, same state)?
- Is the address proof **recent enough** (≤ 90 days)?
- Is any required document **missing** (like K05)?
- Are the signatory details consistent?

---

## 11. How we'll probably be judged

- **Technical depth.** Does the prototype actually work? Does the advisor give sensible, rule-compliant recommendations on unseen scenarios? Does KYC catch the planted problems?
- **Business judgement.** Segment choice, pricing, rollout, a realistic role for the field force, sensible metrics and targets.
- **Competitive analysis.** Airtel explicitly asked for this.
- **Impact.** How much better would conversion, time to activate and acquisition cost get, in numbers?
- **Privacy and compliance.** DPDP-aware design.

**What the judges have and we don't:** 15 advisor test scenarios, the KYC answer key, the "signals" deliberately planted in the leads data (patterns we're meant to discover), and the scripts that generated the data.

---

## 12. Deliverables checklist (Stage 1)

- [ ] `Shenron_IIITD.pptx`: 7 slides on the official template
- [ ] `Shenron_IIITD.pdf`: the same deck exported to PDF
- [ ] Inside the deck: approach, competitive analysis, impact
- [ ] Inside the deck: architecture diagram
- [ ] Inside the deck: privacy & security choices
- [ ] Inside the deck: answers to the 5 key questions
- [ ] Working prototype: Advisor, Quote, Smart KYC, Tracker
- [ ] Demo video, ≤ 3 minutes (linked in the deck)
- [ ] Code repository (linked in the deck)

---

## 13. Glossary

| Term | Meaning |
|---|---|
| MSME / SMB | Micro, small and medium enterprises / small and medium businesses. Used interchangeably here |
| B2B | Business-to-business: selling to companies, not individuals |
| Lead | A business that showed interest but hasn't bought yet |
| Funnel | The steps from lead to paying customer; people drop off at each step |
| Activation | The service is installed and live, so the lead is now a customer |
| Bundle | Several products sold together under one price |
| CAC | Customer Acquisition Cost: money spent (sales, partners) to win one customer |
| Churn | A customer leaving. Here, `churned_within_6_months` |
| NPS | Net Promoter Score: "how likely are you to recommend us", rated 0–10 |
| Propensity score | A model's estimate of how likely a lead is to convert |
| Field force | The company's own salespeople who visit customers |
| Channel partner | A local reseller/agent who sells on the company's behalf for commission |
| Tier 1 / Tier 2 city | Big metros / smaller cities |
| Leased line | A dedicated, guaranteed internet connection that isn't shared with others |
| FWA / AirFiber | Fixed Wireless Access: home/office broadband delivered over 5G instead of cable |
| SLA | Service Level Agreement: a guaranteed uptime, e.g. 99.9% |
| Static IP | A fixed internet address, needed for remote CCTV viewing or servers |
| SD-WAN | Software that manages internet links across many branches from one place |
| POS | Point-of-sale: the billing counter/machine |
| DLT | India's mandatory registration for businesses sending commercial SMS |
| SOC | Security Operations Centre: a team that monitors for cyber threats |

---

## 14. Things we still need to study before planning

These are the open questions that `plan.md` will answer:

1. **Data deep-dive.** Which segments, sources, languages and cities convert best and churn least? What are the "signals planted in the leads data"?
2. **Segment and bundle choice.** Which 1–2 segments to lead with, and a starter bundle and price for each.
3. **Pricing logic.** The catalogue gives price *ranges*. How do we pick a point in the range (e.g. by contract length or bundle size)?
4. **Competitors.** What Jio Business, Vi Business, local ISPs and digital-first players offer small businesses, and how fast their sign-up is.
5. **Tech choices.** Which model powers the advisor, how to do OCR reliably on watermarked images, how multilingual support works, and what stack lets us build all four modules in 7 days.
6. **KYC rules.** Inspect all 47 documents and list every check we need, so we catch every planted problem.
7. **Field force / partner model.** Where humans stay in the loop (complex leads, site surveys, installs, assisted sign-up).
8. **Metrics.** Pick 3–5 metrics with today's baseline (from the data) and our targets.
9. **Deck story.** How to fit all of this into 7 slides.
