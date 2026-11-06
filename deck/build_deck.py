"""Builds Shenron_IIITD.pptx (7 slides) on the official template, then exports the PDF via PowerPoint.
python deck/build_deck.py"""
import copy
import subprocess
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SHOTS = OUT / "screens"

# fill these in before the final export
LIVE_URL = "https://airtel-udyam-kappa.vercel.app"
REPO_URL = "https://github.com/Unique0202/Team_Shenron_Airtel_Hackathon"
MEMBERS = "Member One · Member Two"

RED, RED_DEEP = RGBColor(0xE4, 0x00, 0x00), RGBColor(0xA8, 0x00, 0x0F)
INK, SLATE, GREY = RGBColor(0x1B, 0x1E, 0x25), RGBColor(0x5B, 0x64, 0x72), RGBColor(0x6B, 0x72, 0x80)
LINE, WASH, WHITE = RGBColor(0xE3, 0xE6, 0xEB), RGBColor(0xF3, 0xF5, 0xF8), RGBColor(0xFF, 0xFF, 0xFF)
OK = RGBColor(0x0F, 0x7A, 0x45)
FONT = "Segoe UI"

prs = Presentation(ROOT / "docs" / "Submission Template_Sync.pptx")

title_slide, content_template = prs.slides[0], prs.slides[1]
BG = content_template.shapes[0].image.blob


# ---------------------------------------------------------------- helpers
def new_slide():
    s = prs.slides.add_slide(content_template.slide_layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    pic = s.shapes.add_picture(_bg_file(), 0, 0, prs.slide_width, prs.slide_height)
    s.shapes._spTree.remove(pic._element)
    s.shapes._spTree.insert(2, pic._element)  # keep the branded background at the back
    return s


def _bg_file():
    f = OUT / "_bg.jpg"
    if not f.exists():
        f.write_bytes(BG)
    return str(f)


def text(slide, x, y, w, h, paras, size=11, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=1.0, after=0):
    """paras: str | list of str | list of list of (text, {opts}) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.line_spacing = spacing
        para.space_after = Pt(after)
        runs = p if isinstance(p, list) else [(p, {})]
        for t, o in runs:
            r = para.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.color.rgb = o.get("color", color)
            if o.get("link"):
                r.hyperlink.address = o["link"]
                _link_uses_text_colour(r)
    return tb


def _link_uses_text_colour(run):
    """PowerPoint draws links in the theme colour unless the link carries the 2018 'use text colour' extension."""
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    click = run._r.find(f"{{{a}}}rPr/{{{a}}}hlinkClick")
    ext = etree.SubElement(etree.SubElement(click, f"{{{a}}}extLst"), f"{{{a}}}ext")
    ext.set("uri", "{A12FA001-AC4F-418D-AE19-62706E023703}")
    etree.SubElement(ext, "{http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor}hlinkClr",
                     nsmap={"ahyp": "http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor"}).set("val", "tx")


def box(slide, x, y, w, h, fill=WHITE, line=LINE, radius=True, weight=0.75):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shp.adjustments[0] = 0.08
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(weight)
    shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def label_box(slide, x, y, w, h, title, sub="", fill=WHITE, line=LINE, title_color=INK, size=9.5):
    box(slide, x, y, w, h, fill, line)
    paras = [[(title, {"bold": True, "color": title_color, "size": size})]]
    if sub:
        paras.append([(sub, {"color": RGBColor(0xD5, 0xD9, 0xE0) if fill == INK else SLATE, "size": size - 1.5})])
    text(slide, x + 0.08, y + 0.04, w - 0.16, h - 0.08, paras, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)


def arrow(slide, x1, y1, x2, y2, color=GREY):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(1.25)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd")
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return c


def heading(slide, title, kicker=None):
    text(slide, 0.42, 0.72, 9.1, 0.5, title, size=19, bold=True)
    if kicker:
        text(slide, 0.42, 1.2, 9.1, 0.3, kicker, size=10.5, color=SLATE)


def table(slide, x, y, w, rows, col_w, size=8.5, header_fill=INK, row_h=0.27, highlight_last=False):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = shp.table
    tbl.first_row = True
    tbl.horz_banding = False
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            last = highlight_last and i == len(rows) - 1
            cell.fill.fore_color.rgb = header_fill if i == 0 else (RGBColor(0xFD, 0xEC, 0xEC) if last else
                                                                  (WHITE if i % 2 else WASH))
            tf = cell.text_frame
            tf.word_wrap = True
            tf.paragraphs[0].text = ""
            r = tf.paragraphs[0].add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = i == 0 or j == 0 or last
            r.font.color.rgb = WHITE if i == 0 else (RED_DEEP if last and j == 0 else INK)
    return tbl


def style_chart(chart, size=9):
    chart.has_legend = False
    chart.has_title = False
    chart.font.name = FONT
    chart.font.size = Pt(size)
    chart.font.color.rgb = SLATE
    plot = chart.plots[0]
    plot.gap_width = 45
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.size = Pt(size)
    dl.font.color.rgb = INK
    dl.font.bold = True
    va = chart.value_axis
    va.visible = False
    va.has_major_gridlines = False
    ca = chart.category_axis
    ca.format.line.color.rgb = LINE
    ca.has_major_gridlines = False
    ca.tick_labels.font.size = Pt(size)
    ca.tick_labels.font.color.rgb = INK
    return plot


def color_points(plot, colors):
    for pt_idx, c in enumerate(colors):
        pt = plot.series[0].points[pt_idx]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c


def phone(slide, img, x, y, h):
    w = h * 390 / 844
    pic = slide.shapes.add_picture(str(img), Inches(x), Inches(y), height=Inches(h))
    pic.line.color.rgb = LINE
    pic.line.width = Pt(1)
    return w


# ---------------------------------------------------------------- slide 1: title
s = title_slide
text(s, 0.62, 2.72, 4.6, 0.55, "Airtel Udyam", size=30, bold=True, color=WHITE)
text(s, 0.62, 3.25, 4.6, 0.4, "A small business goes digital in one sitting", size=14, color=WHITE)
text(s, 0.62, 3.78, 4.6, 0.9, [
    [("Team Shenron, IIITD", {"bold": True, "size": 12})],
    [(MEMBERS, {"size": 10.5})],
], color=WHITE, spacing=1.15)
# one link per text box: PowerPoint's PDF export drops the second link in a shared box
text(s, 0.62, 4.52, 4.8, 0.22, [[("Live prototype  ", {"bold": True}), (LIVE_URL, {"link": LIVE_URL})]],
     size=9.5, color=WHITE)
text(s, 0.62, 4.74, 4.8, 0.22, [[("Code  ", {"bold": True}), (REPO_URL.replace("https://", ""), {"link": REPO_URL})]],
     size=9.5, color=WHITE)

# ---------------------------------------------------------------- slide 2: problem in data
s = content_template
for ph in list(s.placeholders):
    ph._element.getparent().remove(ph._element)
heading(s, "Only 7 in 100 interested businesses become customers",
        "One quarter of SMB leads (5,000, Apr–Jun 2026): 17.6 days to activate, 3 status calls per customer, ₹15,053 to acquire each customer")
cd = CategoryChartData()
stages = ["Lead", "Contacted (68%)", "Needs assessed (58%)", "Quote accepted (44%)", "KYC complete (68%)", "Activated (63%)"]
cd.categories = list(reversed(stages))
cd.add_series("Leads", list(reversed([5000, 3406, 1974, 861, 588, 368])))
ch = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.3), Inches(1.55), Inches(4.5), Inches(2.2), cd).chart
plot = style_chart(ch, 8.5)
plot.data_labels.number_format = "#,##0"
plot.data_labels.number_format_is_linked = False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
color_points(plot, [RED] + [GREY] * 5)
text(s, 0.42, 3.8, 4.3, 0.2, "Funnel stage (% of previous stage). Source: smb_leads.csv", size=7.5, color=SLATE)

text(s, 0.42, 4.05, 4.4, 0.25, "What we found in the data", size=10.5, bold=True)
text(s, 0.42, 4.3, 4.45, 0.85, [
    [("Status chasing predicts churn: ", {"bold": True}), ("1 call 6% churn, 5 calls 28%.", {})],
    [("Digital leads are cheapest ", {"bold": True}), ("(₹112–274 per lead) but 26–32% are never reached.", {})],
    [("Sales sells the target, not the need: ", {"bold": True}), ("5G AirFiber asked 39×, sold 9×.", {})],
    [("No GSTIN, no deal: ", {"bold": True}), ("2.0% conversion vs 9.6%; Tamil leads via field sales 2.6%.", {})],
], size=8.5, spacing=1.05, after=2)

text(s, 5.15, 1.62, 4.4, 0.25, "Where the 4,632 lost leads went, and what fixes it", size=10.5, bold=True)
table(s, 5.15, 1.92, 4.42, [
    ["Why they left", "Leads", "Our fix"],
    ["Never reached, or no one visited", "1,951", "Advisor works any time, no visit"],
    ["Quote slow, complex or too pricey", "1,006", "Instant plain bill, right-sized bundle"],
    ["Not interested, locked in, mobile only", "1,182", "Better targeting; start with one SIM"],
    ["Paperwork, mismatched documents", "273", "Smart KYC + e-sign"],
    ["Waited after KYC (install, payment)", "220", "Tracker; check feasibility upfront"],
], [1.75, 0.5, 2.17], size=8, row_h=0.36)
text(s, 5.15, 4.15, 4.4, 0.9, [
    [("2,830 of the lost leads ", {"bold": True, "color": RED_DEEP}),
     ("(61%) dropped for reasons a self-serve journey removes: no visit, slow or confusing quote, paperwork, silence after KYC.", {})],
], size=9, spacing=1.1)

# ---------------------------------------------------------------- slide 3: approach
s = new_slide()
heading(s, "Who to win first, with what bundle, at what price",
        "Lead with professional offices, win micro businesses digitally, keep field sales for chains. Bundles are the prototype's real output.")
cols = [
    ("1  Professional offices", "25% of leads · 11.1% convert · lowest CAC (₹10,695)",
     "Dental clinic, 2 sites, 12 staff", "Fibre 300 ×2, cloud backup, endpoint security, managed firewall, cloud email",
     "₹9,811 / month", "2-year plan, setup halved to ₹4,000", "Digital-first: owners are online and need uptime + data safety"),
    ("2  Micro retail & services", "54% of leads · 4.1% convert · CAC ₹20,007 vs ₹2,470 bill",
     "Kirana in Lucknow, 3 staff, no GSTIN", "5G AirFiber (no fibre wait), cloud POS & billing, 2 CCTV cameras, website",
     "₹2,825 / month", "No GST paperwork needed; live in 4 days", "Digital only: a field visit costs more than 8 months of revenue"),
    ("3  Multi-site & manufacturers", "21% of leads · 11–13% convert · ₹16–28k bills, churn 8–11%",
     "Restaurant chain, 5 outlets, 60 staff", "Fibre 300 ×5, SD-WAN, 4G failover, CCTV, cloud telephony, 6 SIMs",
     "₹33,754 / month", "2-year plan (SD-WAN minimum)", "Field sales, with the advisor pre-qualifying the lead"),
]
for i, (name, why, who, what, price, terms, channel) in enumerate(cols):
    x = 0.42 + i * 3.08
    box(s, x, 1.6, 2.92, 2.62)
    text(s, x + 0.15, 1.7, 2.65, 2.45, [
        [(name, {"bold": True, "size": 11.5, "color": RED_DEEP if i < 2 else INK})],
        [(why, {"size": 8, "color": SLATE})],
        [("Example: " + who, {"bold": True, "size": 9})],
        [(what, {"size": 8.5})],
        [(price, {"bold": True, "size": 17})],
        [(terms, {"size": 8, "color": SLATE})],
        [(channel, {"size": 8.5, "bold": True})],
    ], spacing=1.05, after=4)
steps = [("Chat", "5 minutes, 10 languages, voice"), ("Bill", "instant, one monthly price"),
         ("Verify", "10 minutes, consent first"), ("Track", "install in 2–7 days, no calls")]
for i, (t, d) in enumerate(steps):
    x = 0.42 + i * 2.33
    box(s, x, 4.37, 2.12, 0.6, fill=WASH, line=None)
    text(s, x + 0.12, 4.42, 1.95, 0.5, [[(f"{i + 1}  {t}", {"bold": True, "size": 10.5})], [(d, {"size": 8, "color": SLATE})]],
         anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        arrow(s, x + 2.13, 4.67, x + 2.32, 4.67)

# ---------------------------------------------------------------- slide 4: prototype
s = new_slide()
heading(s, "Working prototype: first message to placed order, on a phone")
caps = [("1_advisor.png", "Advisor understands the business and explains the plan in plain words"),
        ("2_bill.png", "One monthly bill like a shop receipt; toggle services, pick 1–3 years"),
        ("3_kyc_flagged.png", "Smart KYC caught a planted problem: two business names on one GST certificate"),
        ("4_tracker.png", "Order tracker with expected dates replaces status calls")]
for i, (img, cap) in enumerate(caps):
    x = 0.42 + i * 1.78
    phone(s, SHOTS / img, x, 1.3, 3.2)
    text(s, x, 4.57, 1.55, 0.6, [[(f"{i + 1}  ", {"bold": True, "color": RED}), (cap, {})]], size=7.5, spacing=1.0)
box(s, 7.55, 1.3, 2.05, 3.85, fill=WASH, line=None)
text(s, 7.68, 1.4, 1.82, 3.7, [
    [("Try it", {"bold": True, "size": 11})],
    [(LIVE_URL.replace("https://", ""), {"size": 8.5, "color": RED_DEEP, "bold": True})],
    [("Tested", {"bold": True, "size": 11})],
    [("Hindi + English chats end to end; 10 languages and voice input", {"size": 8})],
    [("Rules catch all 6 planted KYC problems in the 12 sample applicants; the 6 clean ones pass", {"size": 8})],
    [("Every recommended bundle passes eligibility, dependency and budget rules (automated tests)", {"size": 8})],
    [("Also built", {"bold": True, "size": 11})],
    [("Under-the-hood panel: profile, ML scores, what the model saw", {"size": 8})],
    [("Partner console: dropped leads ranked by likelihood to convert", {"size": 8})],
], spacing=1.05, after=3)

# ---------------------------------------------------------------- slide 5: architecture + privacy
s = new_slide()
heading(s, "Agents talk, rules decide: built for regulated customer data")
label_box(s, 0.42, 1.35, 1.5, 0.62, "Business owner", "web or WhatsApp, voice, 10 languages", fill=WASH, line=None)
arrow(s, 1.93, 1.66, 2.25, 1.66)
label_box(s, 2.27, 1.35, 1.95, 0.62, "Privacy gateway", "GSTIN, PAN, phone, Aadhaar → tokens before any model call",
          fill=RGBColor(0xFD, 0xEC, 0xEC), line=None, title_color=RED_DEEP)
arrow(s, 4.23, 1.66, 4.55, 1.66)
label_box(s, 4.57, 1.35, 1.7, 0.62, "Orchestrator API", "journey state, fallback across models", fill=INK, line=None,
          title_color=WHITE)
agents = [("Advisor agent", "chat + profile extraction", 0.42),
          ("KYC agent", "reads document photos", 2.52),
          ("Order agent", "state machine, no model", 4.62)]
for name, sub, x in agents:
    label_box(s, x, 2.3, 1.95, 0.55, name, sub, line=RED, title_color=RED_DEEP)
for x in (1.4, 3.5, 5.6):
    arrow(s, 5.42, 1.98, x, 2.28)
tools = [
    (0.42, ["Rules engine: city tier, size, GSTIN, dependencies", "ML ranker: 25 product models, AUC 0.78",
            "Pricing: contract & bundle discounts, budget cap"]),
    (2.52, ["Blur check before any model call", "GST & Udyam registry lookup, checksum + misread repair",
            "20 cross-document checks (names, state, 90-day bill)"]),
    (4.62, ["Tracker with expected dates + WhatsApp updates", "Per-SIM-user e-KYC step (DoT rule)",
            "Partner console: propensity model, AUC 0.75"]),
]
for x, items in tools:
    arrow(s, x + 0.97, 2.86, x + 0.97, 3.02)
    for k, t in enumerate(items):
        box(s, x, 3.04 + k * 0.42, 1.95, 0.36, fill=WASH, line=None)
        text(s, x + 0.07, 3.06 + k * 0.42, 1.82, 0.32, t, size=7.5, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.42, 4.37, 6.2, 0.75, [
    [("Why judges can trust the output: ", {"bold": True}),
     ("the language model only converses and extracts. Which products are allowed, what they cost and whether KYC passes is "
      "decided by code, so the advisor cannot invent a price or sell an ineligible product. Busy or out-of-quota models fail "
      "over in seconds; each document photo is read only once.", {})],
], size=8.5, spacing=1.1)
box(s, 6.75, 1.35, 2.85, 3.8, fill=WASH, line=None)
text(s, 6.88, 1.43, 2.62, 3.65, [
    [("Privacy by design (DPDP Act 2023)", {"bold": True, "size": 10.5})],
    [("Consent first: ", {"bold": True}), ("purpose, what is collected, retention and withdrawal shown before KYC", {})],
    [("Tokenization at source: ", {"bold": True}), ("identifiers never reach the external model", {})],
    [("Masking ", {"bold": True}), ("in screens, API responses and logs (32TTNX•••••T1ZW)", {})],
    [("Minimisation: ", {"bold": True}), ("registry lookup pre-fills details; only 4 documents asked", {})],
    [("Retention: ", {"bold": True}), ("photos are read in memory, never stored; only the verification result is kept", {})],
    [("Localisation: ", {"bold": True}), ("production runs the model in an India region or on Airtel's Agent Bridge", {})],
    [("Telecom rules: ", {"bold": True}), ("business KYC is instant; each SIM user still completes their own e-KYC", {})],
], size=8, spacing=1.05, after=4)

# ---------------------------------------------------------------- slide 6: competition
s = new_slide()
heading(s, "Rivals stop at “request a callback”; we close online, on one bill")
table(s, 0.42, 1.3, 9.18, [
    ["", "Bundle across products", "Online checkout", "Indian languages", "One bill", "Digital KYC", "Entry price / month"],
    ["Jio Business", "Partly: BB + cloud + landline", "Partly: buy online or callback", "No (English pages)", "Partly",
     "No, at install", "₹801 (100 Mbps)"],
    ["Vi Business", "No: mobile only", "Partly: form, 48 h callback", "Not stated", "No", "Partly, doorstep",
     "Not published"],
    ["Tata Tele Business", "Partly: office packs", "No: callback, partners", "Partly: voice AI", "Partly", "No",
     "Quote only"],
    ["Airtel Business today", "No: separate silos", "No: callback in 1 day", "No", "No", "No", "₹499 (2022 list)"],
    ["Local ISPs", "No: broadband only", "Partly: app booking", "Local staff", "No", "Partly, app upload", "~₹699"],
    ["Single-product apps", "No: one tool each", "Yes, minutes", "Partly", "No", "Yes", "₹59–2,799 each"],
    ["Airtel Udyam (ours)", "Yes: 25 products, rules-checked", "Yes", "Yes: 10 + voice", "Yes", "Yes: registry + e-sign",
     "₹2,825 (kirana bundle)"],
], [1.45, 1.75, 1.5, 1.15, 0.65, 1.2, 1.48], size=7.5, row_h=0.3, highlight_last=True)
blocks = [
    ("Where we win", ["Close simple cases online; telcos all stop at a callback",
                      "One bundle, one bill replaces 4–6 vendors (ISP, telco, WhatsApp, email, POS, CCTV)",
                      "Only Airtel owns network, SIMs, WhatsApp channel and partners to do it"]),
    ("Watch out", ["Jio sets the price anchor (₹801): sell total value, not Mbps",
                   "Tata Tele is moving to advisor + voice AI; speed matters",
                   "SaaS apps sign up in minutes: our checkout must match"]),
    ("Field force & partners", ["Advisor closes simple cases; complex and dropped leads go to people",
                                "Partner console ranks leads: top 20% hold 47% of activations",
                                "Partners earn commission on assisted digital sign-ups; installs stay human"]),
]
for i, (t, items) in enumerate(blocks):
    x = 0.42 + i * 3.08
    text(s, x, 3.83, 2.95, 1.3, [[(t, {"bold": True, "size": 10, "color": RED_DEEP if i == 0 else INK})]]
         + [[("• " + it, {"size": 8})] for it in items], spacing=1.05, after=2)
text(s, 0.42, 5.17, 7.5, 0.18, "Sources: operator websites and press, Oct 2025 – Nov 2026 (full list in analysis/competition.md).",
     size=6.5, color=SLATE)

# ---------------------------------------------------------------- slide 7: impact
s = new_slide()
heading(s, "Impact: 2× the customers from the same leads, at 60% lower cost")
table(s, 0.42, 1.3, 5.6, [
    ["Metric", "Today", "Target (12 mo)", "Lever"],
    ["Lead → activation", "7.4%", "15%", "No-visit and quote drops recovered online"],
    ["Time to activate", "17.6 days", "≤ 7 days", "Instant quote and KYC; install is the only wait"],
    ["Acquisition cost", "₹15,053", "≤ ₹6,000", "Micro and digital leads off field sales"],
    ["Status calls / customer", "3.0", "< 0.5", "Tracker + proactive WhatsApp updates"],
    ["6-month churn", "15.2%", "≤ 10%", "Fewer chases, right-sized bundles (≤ 6 items)"],
], [1.45, 0.8, 0.95, 2.4], size=8, row_h=0.33)
cd = CategoryChartData()
cd.categories = ["1", "2", "3", "4", "5"]
cd.add_series("Churn", [0.06, 0.14, 0.12, 0.20, 0.28])
text(s, 6.3, 1.3, 3.3, 0.3, "6-month churn by status calls the customer made", size=9, bold=True)
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.2), Inches(1.55), Inches(3.4), Inches(1.75), cd).chart
plot = style_chart(ch, 8)
plot.data_labels.number_format = "0%"
plot.data_labels.number_format_is_linked = False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
color_points(plot, [GREY, GREY, GREY, GREY, RED])
text(s, 6.3, 3.3, 3.3, 0.2, "Status calls per activated customer (n = 368)", size=7.5, color=SLATE)
box(s, 0.42, 3.4, 5.6, 0.62, fill=RGBColor(0xFD, 0xEC, 0xEC), line=None)
text(s, 0.55, 3.44, 5.4, 0.55, [
    [("Same 5,000 leads a quarter: ", {"bold": True}),
     ("368 → 750 customers. At the median ₹6,900 bill that is about ₹3.2 crore more annual revenue from each quarter's leads, "
      "for ₹45 lakh of acquisition spend instead of ₹55 lakh today.", {})],
], size=8.5, anchor=MSO_ANCHOR.MIDDLE, spacing=1.05)
text(s, 0.42, 4.15, 3.0, 1.0, [
    [("Rollout", {"bold": True, "size": 10})],
    [("0–3 months: ", {"bold": True}), ("pilot in Kochi and Lucknow, professional offices + micro, 3 languages", {})],
    [("3–9 months: ", {"bold": True}), ("10 cities, WhatsApp front end, partner console to channel partners", {})],
    [("9–12 months: ", {"bold": True}), ("national, 10 languages, on Airtel's Agent Bridge", {})],
], size=8, spacing=1.05, after=2)
text(s, 3.45, 4.15, 2.85, 1.0, [
    [("Risks and mitigations", {"bold": True, "size": 10})],
    [("Wrong advice: ", {"bold": True}), ("rules decide, human handoff in one tap", {})],
    [("Model outage or quota: ", {"bold": True}), ("multi-model fallback, cached reads", {})],
    [("Channel conflict: ", {"bold": True}), ("partners paid on assisted digital deals", {})],
    [("SIM KYC rules: ", {"bold": True}), ("per-user e-KYC built into the tracker", {})],
], size=8, spacing=1.05, after=2)
text(s, 6.5, 3.62, 3.1, 1.5, [
    [("Next", {"bold": True, "size": 10})],
    [("Site-feasibility check before the quote (41 leads lost to “fibre not feasible”)", {"size": 8})],
    [("GST registration help for the 29% of leads without a GSTIN", {"size": 8})],
    [("A/B test the advisor against field sales in the pilot", {"size": 8})],
], spacing=1.05, after=2)

# ---------------------------------------------------------------- order, save, export
# content_template became slide 2; new slides were appended in order, so the deck is already 1..7
assert len(prs.slides) == 7, len(prs.slides)
pptx = OUT / "Shenron_IIITD.pptx"
prs.save(pptx)
(OUT / "_bg.jpg").unlink(missing_ok=True)
print("saved", pptx)

if "--pdf" in sys.argv:
    pdf = OUT / "Shenron_IIITD.pdf"
    ps = (f"$p = New-Object -ComObject PowerPoint.Application; "
          f"$d = $p.Presentations.Open('{pptx}', $true, $false, $false); "
          f"$d.SaveAs('{pdf}', 32); $d.Close(); $p.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    # PowerPoint's PDF export drops hyperlinks unpredictably: add them over the URL text ourselves
    import fitz
    doc = fitz.open(pdf)
    for page in doc:
        for url in (LIVE_URL, REPO_URL):
            for needle in {url, url.replace("https://", "")}:
                for rect in page.search_for(needle):
                    page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": url})
    doc.saveIncr()
    print("saved", pdf, f"{pdf.stat().st_size / 1e6:.1f} MB",
          sorted({l["uri"] for p in doc for l in p.get_links()}))
