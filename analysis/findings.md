# What the leads data tells us

Source: `data/smb_leads.csv` (5,000 leads, Apr–Jun 2026). Reproduce with `python analysis/eda.py`.
"Conv" = lead → activated. "CAC/act" = acquisition spend ÷ activations.

## Baseline (today)
| Metric | Value |
|---|---|
| Lead → activation | **7.4%** (368 / 5,000) |
| CAC per activated customer | **₹15,053** (₹55.4 lakh spent in the quarter) |
| Lead → activation time | **17.6 days** |
| Status-chasing calls per customer | **3.0** |
| 6-month churn | **15.2%** |
| NPS (promoters − detractors) | **−25** (average score 6.9) |
| Median bundle | ₹6,900/month |

## The 8 signals that shape our solution

**1. Chasing calls predict churn: the Tracker pays for itself.**
| Follow-up calls | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 6-month churn | 6% | 14% | 12% | 20% | **28%** |
| NPS score | 7.5 | 7.2 | 6.9 | 6.7 | 6.0 |

Customers who chase 5 times churn at about **4.5×** the rate of those who chase once. Every status call we remove is retention.

**2. Digital leads are the cheapest but nobody closes them.**
| Source | Conv | Cost/lead | CAC/act | Unreachable |
|---|---|---|---|---|
| Referral | **14.8%** | ₹605 | **₹4,099** | 11% |
| Inbound call | 9.5% | ₹487 | ₹5,113 | 11% |
| Channel partner | 8.0% | ₹1,672 | ₹20,851 | 15% |
| Field sales | 7.3% | ₹1,769 | **₹24,335** | 14% |
| Website form | 4.3% | ₹274 | ₹6,352 | **26%** |
| WhatsApp campaign | **2.8%** | ₹112 | ₹4,026 | **32%** |

Website and WhatsApp leads cost 6–15× less per lead than field sales, yet convert worst, mostly because 26–32% are never reached. They fill a form and then wait for a call. **If the advisor converts them instantly, at the moment they're interested, this becomes the cheapest channel we have.** Even reaching field-sales-level conversion (7.3%) would cut WhatsApp CAC to about ₹1,500.

**3. Field sales is wasted on micro businesses.**
Field sales converts micro retail at **3.0%** but professional offices at 11.9% and multi-site businesses at 12.2%. Micro businesses are 55% of leads, but their CAC/act is ₹20,007 against a ₹2,470/month bundle, and their churn is 22.7%. **Micro → digital self-serve. Field force → multi-site, manufacturers and large professional offices.** That's our Key Question 4 answer.

**4. The salesforce sells what's on target, not what was asked for.**
For activated customers, how often was a product they asked for actually in their bundle?
- **Asked for but rarely sold:** 5G AirFiber P04 **8%** (39 asked, 9 sold) · Website P18 **0%** · Business SMS P14 12% · WhatsApp API P15 20% · Managed Firewall P21 3%
- **Sold far more than asked:** Postpaid 599 P08 (28 asked → 192 sold) · Fibre 100 P01 (40 → 180) · Cloud email P16 (29 → 175)

This is the case's "pitches whatever is on target this month" problem, visible in the data. **The advisor starts from the stated need**, and the ML ranker learns from what activated *and stayed*.

**5. No GSTIN = no deal (today).**
| | Conv | CAC/act | Churn |
|---|---|---|---|
| Has GSTIN | 9.6% | ₹12,686 | 14.5% |
| No GSTIN | **2.0%** | **₹41,728** | 23.3% |

1,466 leads (29%) have no GSTIN, and 6 products require one (WhatsApp API, SMS, toll-free…). **The advisor builds a GST-free bundle for them** (P01/P04/P07/P16/P19/P23 need no GSTIN) and offers to help with GST registration. It doesn't drop them.

**6. Language is a hidden barrier for field sales.**
Field sales conversion: Bengali 13.2% · Gujarati 10.8% · English 8.3% · Hindi 6.9% · Kannada 5.6% · **Tamil 2.6%** (CAC/act **₹74,530**). A vernacular advisor reaches these owners in their own language.

**7. Over-selling backfires.**
Bundles with 3–6 products churn 10–16%. With 2 products, 24%; with **8 products, 43%**. The bundle builder caps bundles at about 6 products and applies a segment price ceiling.

**8. Who to target first.**
| Segment | Share | Conv | Median MRR | Churn | CAC/act |
|---|---|---|---|---|---|
| Professional offices | 25% | 11.1% | ₹6,575 | 13.8% | **₹10,695** |
| Small multi-site | 15% | 11.0% | **₹28,080** | 10.8% | ₹15,614 |
| Small manufacturers | 6% | **12.8%** | ₹15,910 | **8.1%** | ₹15,324 |
| Micro retail & services | 54% | 4.1% | ₹2,470 | **22.7%** | ₹20,007 |

Also: existing **Accel mobile-only customers** (1,505 leads, 30%) convert at 9.2%, the warmest base to upsell. Mobile-hotspot users churn at 24.7%.

**Our pick:** lead the digital journey with **professional offices** (best conversion-to-cost ratio, simple needs, comfortable on a phone), and use it to **make micro businesses profitable** (they can't afford a ₹20k field visit). Multi-site businesses and manufacturers go to the field force, with the advisor as a pre-qualifier.

## Targets we propose (12 months)
| Metric | Today | Target | Why it's credible |
|---|---|---|---|
| Lead → activation | 7.4% | **15%** | Digital leads reach referral-level conversion; no-visit drops (827) and quote drops (385) mostly removed |
| Time to activation | 17.6 days | **≤ 7 days** | Instant quote + KYC in minutes; install time (2–7 days for fibre/AirFiber) becomes the only wait |
| CAC per activation | ₹15,053 | **≤ ₹6,000** | Micro and digital leads move off field sales |
| Status-chasing calls | 3.0 | **< 0.5** | Tracker + proactive updates |
| 6-month churn | 15.2% | **≤ 10%** | Fewer chases (signal 1), right-sized bundles (signal 7) |
