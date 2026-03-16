"""
SEPI PDF Generator  –  SY 2026–2027
Produces: Enrollment Form | Enrollment Contract | Statement of Account
Format  : Long Bond Paper 8.5" × 13" | Pink accent | SEPI logo watermark
Fixes   : correct address, correct school year, no PH notarization block in contract
"""

import os, io
from reportlab.lib.pagesizes import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether, PageBreak,
                                Image as RLImage)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from fees import (SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_EMAIL, SCHOOL_PHONE,
                  SCHOOL_CITY, SCHOOL_YEAR, LEVEL_LABEL, compute_fees)

# ── Page layout ───────────────────────────────────────────────────────────────
LONG_BOND = (8.5 * inch, 13 * inch)
PAGE_W, PAGE_H = LONG_BOND
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

LOGO_PATH = os.path.join(os.path.dirname(__file__), "sepi_logo.jpg")

# ── Colours ───────────────────────────────────────────────────────────────────
PINK_DARK  = colors.HexColor("#C2185B")
PINK_MID   = colors.HexColor("#E91E63")
PINK_LIGHT = colors.HexColor("#FCE4EC")
PINK_FAINT = colors.HexColor("#FFF0F5")
NAVY       = colors.HexColor("#1A2333")
GRAY       = colors.HexColor("#757575")
WHITE      = colors.white

# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    s = {}
    s["doc_title"] = ParagraphStyle("dt", fontName="Helvetica-Bold", fontSize=15,
        textColor=PINK_DARK, alignment=TA_CENTER, spaceAfter=2, leading=19)
    s["doc_sub"] = ParagraphStyle("ds", fontName="Helvetica", fontSize=9,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=5)
    s["school_name"] = ParagraphStyle("sn", fontName="Helvetica-Bold", fontSize=11,
        textColor=PINK_DARK, leading=14)
    s["school_addr"] = ParagraphStyle("sa", fontName="Helvetica", fontSize=8,
        textColor=GRAY, leading=12)
    s["section"] = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=8,
        textColor=WHITE, alignment=TA_LEFT, spaceAfter=0, spaceBefore=8,
        backColor=PINK_DARK, leftIndent=4, leading=13, borderPadding=(3,4,3,4))
    s["body"]      = ParagraphStyle("b",  fontName="Helvetica",      fontSize=8.5, textColor=NAVY, spaceAfter=4, leading=12)
    s["body_bold"] = ParagraphStyle("bb", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY, spaceAfter=4, leading=12)
    s["legal"]     = ParagraphStyle("lg", fontName="Helvetica",      fontSize=8.5, textColor=NAVY, spaceAfter=5, leading=13, alignment=TA_JUSTIFY)
    s["legal_bold"]= ParagraphStyle("lb", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY, spaceAfter=5, leading=13)
    s["small"]     = ParagraphStyle("sm", fontName="Helvetica",      fontSize=7.5, textColor=GRAY, spaceAfter=3, leading=11)
    s["label"]     = ParagraphStyle("lbl",fontName="Helvetica-Bold", fontSize=7.5, textColor=PINK_DARK, spaceAfter=1)
    s["value"]     = ParagraphStyle("vl", fontName="Helvetica",      fontSize=8.5, textColor=NAVY, spaceAfter=2, leading=11)
    s["center"]    = ParagraphStyle("c",  fontName="Helvetica",      fontSize=8.5, textColor=NAVY, alignment=TA_CENTER, spaceAfter=4, leading=12)
    s["witness"]   = ParagraphStyle("w",  fontName="Helvetica-Bold", fontSize=9,   textColor=PINK_DARK, alignment=TA_CENTER, spaceAfter=4)
    return s

ST = _styles()

# ── Table style helpers ───────────────────────────────────────────────────────
_GRID_PINK = colors.HexColor("#E0B0C0")

def _field_ts():
    return TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("TEXTCOLOR",     (0,0), (-1,-1), NAVY),
        ("GRID",          (0,0), (-1,-1), 0.4, _GRID_PINK),
        ("BACKGROUND",    (0,0), (-1,-1), PINK_FAINT),
        ("BACKGROUND",    (0,0), (0,-1),  PINK_LIGHT),
        ("FONTNAME",      (0,0), (0,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0), (0,-1),  PINK_DARK),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ])

def _fee_ts(n_rows):
    ts = [
        ("BACKGROUND",    (0,0),  (-1,0),       PINK_DARK),
        ("FONTNAME",      (0,0),  (-1,0),        "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0),  (-1,0),        WHITE),
        ("FONTSIZE",      (0,0),  (-1,-1),       8),
        ("GRID",          (0,0),  (-1,-1),       0.4, _GRID_PINK),
        ("BACKGROUND",    (0,1),  (-1,n_rows-2), PINK_FAINT),
        ("ALIGN",         (1,0),  (1,-1),        "RIGHT"),
        ("LEFTPADDING",   (0,0),  (-1,-1),       5),
        ("RIGHTPADDING",  (0,0),  (-1,-1),       5),
        ("TOPPADDING",    (0,0),  (-1,-1),       4),
        ("BOTTOMPADDING", (0,0),  (-1,-1),       4),
        # Total row
        ("BACKGROUND",    (0,-1), (-1,-1),       PINK_DARK),
        ("TEXTCOLOR",     (0,-1), (-1,-1),       WHITE),
        ("FONTNAME",      (0,-1), (-1,-1),       "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1), (-1,-1),       9),
    ]
    return TableStyle(ts)

# ── Page decorators ───────────────────────────────────────────────────────────
def _draw_page(canvas, doc):
    canvas.saveState()
    # Top pink bar
    canvas.setFillColor(PINK_DARK)
    canvas.rect(0, PAGE_H - 0.45*inch, PAGE_W, 0.45*inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE); canvas.setFont("Helvetica-Bold", 8)
    canvas.drawCentredString(PAGE_W/2, PAGE_H - 0.28*inch, SCHOOL_NAME)
    # Bottom bar
    canvas.setFillColor(PINK_DARK)
    canvas.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE); canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN, 0.13*inch,
                      f"{SCHOOL_EMAIL}  |  {SCHOOL_PHONE}  |  {SCHOOL_CITY}")
    canvas.drawRightString(PAGE_W - MARGIN, 0.13*inch,
                           f"Page {canvas.getPageNumber()}")
    # Watermark
    try:
        canvas.setFillAlpha(0.07)
        canvas.drawImage(LOGO_PATH, (PAGE_W-4*inch)/2, (PAGE_H-4*inch)/2,
                         width=4*inch, height=4*inch, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass
    canvas.setFillAlpha(1)
    canvas.restoreState()

# ── Shared header block ───────────────────────────────────────────────────────
def _logo_header(sy):
    school_p = Paragraph(
        f"<b>{SCHOOL_NAME}</b><br/>"
        f"<font size=8 color='#757575'>{SCHOOL_ADDRESS}</font><br/>"
        f"<font size=7.5 color='#757575'>SY {sy}</font>",
        ST["school_name"])
    try:
        logo = RLImage(LOGO_PATH, width=48, height=48)
        data = [[logo, school_p]]
        cw   = [54, CONTENT_W - 54]
    except Exception:
        data = [[school_p]]
        cw   = [CONTENT_W]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("GRID",          (0,0), (-1,-1), 0, WHITE),
    ]))
    return t

def _hline():
    return HRFlowable(width="100%", thickness=1.5, color=PINK_MID, spaceAfter=6, spaceBefore=0)

def _sec(text):
    return Paragraph(f"&nbsp; {text}", ST["section"])

def _field_table(rows, lw=2.3):
    data = [[Paragraph(r[0], ST["label"]), Paragraph(r[1] or "—", ST["value"])]
            for r in rows]
    t = Table(data, colWidths=[lw*inch, CONTENT_W - lw*inch])
    t.setStyle(_field_ts())
    return t

def _two_col(rows, lw=1.8):
    """Two label-value pairs per row."""
    half = CONTENT_W/2 - 0.05*inch
    data = []
    for r in rows:
        l1,v1,l2,v2 = r
        data.append([Paragraph(l1, ST["label"]), Paragraph(v1 or "—", ST["value"]),
                     Paragraph(l2, ST["label"]), Paragraph(v2 or "—", ST["value"])])
    t = Table(data, colWidths=[lw*inch, half-lw*inch, lw*inch, half-lw*inch])
    t.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.4, _GRID_PINK),
        ("BACKGROUND",    (0,0), (-1,-1), PINK_FAINT),
        ("BACKGROUND",    (0,0), (0,-1),  PINK_LIGHT),
        ("BACKGROUND",    (2,0), (2,-1),  PINK_LIGHT),
        ("FONTNAME",      (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTNAME",      (2,0), (2,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0), (0,-1),  PINK_DARK),
        ("TEXTCOLOR",     (2,0), (2,-1),  PINK_DARK),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

def _peso(n): return f"{n:,.2f}"

# ═══════════════════════════════════════════════════════════════════════════════
#  1.  ENROLLMENT FORM
# ═══════════════════════════════════════════════════════════════════════════════
def build_enrollment_form(s: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LONG_BOND,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN + 0.5*inch,
                            bottomMargin=MARGIN + 0.4*inch)
    story = []
    sy = s.get("schoolYear", SCHOOL_YEAR)
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"))

    story.append(_logo_header(sy))
    story.append(Spacer(1, 5))
    story.append(Paragraph("STUDENT ENROLLMENT FORM", ST["doc_title"]))
    story.append(Paragraph(
        "Please complete this form in BLOCK LETTERS. All information will be treated "
        "with confidentiality and used for official school records only.", ST["small"]))
    story.append(_hline())

    # 1. Student information
    story.append(_sec("1.   STUDENT INFORMATION"))
    story.append(Spacer(1,4))
    name = f"{s.get('lastName','')}, {s.get('firstName','')} {s.get('middleName','')}".strip()
    story.append(_field_table([
        ("Full Name (Last, First, Middle)", name),
        ("Preferred Name / Nickname",       s.get("nickname","")),
    ]))
    story.append(_two_col([
        ("Sex / Gender",   (s.get("gender","") or "").capitalize(), "Date of Birth", s.get("birthDate","")),
        ("Place of Birth", s.get("placeOfBirth",""),                "Nationality",   s.get("nationality","Filipino")),
        ("Religion",       s.get("religion",""),                    "Transfer Status", s.get("transferStatus","New Student")),
    ]))
    story.append(_field_table([
        ("Complete Address (House No., Street, Barangay, City/Municipality, Province)",
         f"{s.get('address','')} {s.get('barangay','')} {s.get('city','')} {s.get('province','')}".strip()),
    ]))
    story.append(_two_col([
        ("Mobile Number", s.get("phone",""), "Email Address", s.get("email","")),
    ]))
    story.append(Spacer(1,5))

    # 2. Educational background
    story.append(_sec("2.   EDUCATIONAL BACKGROUND"))
    story.append(Spacer(1,4))
    story.append(_two_col([
        ("Learner Reference No. (LRN)", s.get("lrn",""), "Last Grade Completed", s.get("lastGradeCompleted","")),
    ]))
    story.append(_field_table([
        ("Last School Attended", s.get("previousSchool","")),
    ]))
    story.append(Spacer(1,5))

    # 3. Parent/Guardian
    story.append(_sec("3.   PARENT / GUARDIAN INFORMATION"))
    story.append(Spacer(1,4))
    for title, nk, ok, pk in [
        ("Father", "fatherName","fatherOccupation","fatherPhone"),
        ("Mother", "motherName","motherOccupation","motherPhone"),
    ]:
        hdr = Table([[Paragraph(f"<b>{title}</b>", ST["label"]), ""]],
                    colWidths=[2.3*inch, CONTENT_W - 2.3*inch])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), PINK_LIGHT),
            ("SPAN",        (0,0), (1,0)),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",  (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("GRID",        (0,0), (-1,-1), 0.4, _GRID_PINK),
        ]))
        story.append(hdr)
        story.append(_two_col([
            ("Name", s.get(nk,""), "Occupation", s.get(ok,"")),
            ("Contact Number", s.get(pk,""), "Email", ""),
        ]))
    if s.get("guardianName"):
        story.append(_field_table([
            ("Guardian's Name", s.get("guardianName","")),
            ("Relationship",    s.get("guardianRelation","")),
            ("Contact Number",  s.get("guardianPhone","")),
        ]))
    story.append(Spacer(1,5))

    # 4. Enrollment details
    story.append(_sec("4.   ENROLLMENT DETAILS"))
    story.append(Spacer(1,4))
    llabel = {"preschool":"Kinder / Preschool","elementary":"Elementary","jhs":"Junior High School",}
    story.append(_two_col([
        ("School Year",  sy,   "Grade Level", f"{llabel.get(s.get('level',''),'—')} — {s.get('grade','—')}"),
        ("Strand/Track", s.get("strand","N/A"), "Mode of Payment", (s.get("paymentMode","Cash") or "Cash").capitalize()),
    ]))
    story.append(Spacer(1,5))

    # 5. Documents checklist
    story.append(_sec("5.   REQUIRED DOCUMENTS CHECKLIST"))
    story.append(Spacer(1,4))
    docs_list = [
        "PSA Birth Certificate", "Form 138 / Report Card", "Good Moral Certificate",
        "Certificate of Completion / Diploma", "School Clearance (if applicable)",
        "2×2 ID Pictures (6 pcs)", "Medical Certificate",
    ]

    docs_state = s.get("docs", {})
    chk_data = [["Document", "Status"]]
    for d in docs_list:
        chk_data.append([d, "✓  Submitted" if docs_state.get(d) else "○  Pending"])
    t_docs = Table(chk_data, colWidths=[CONTENT_W - 1.2*inch, 1.2*inch])
    t_docs.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  PINK_DARK),
        ("TEXTCOLOR",     (0,0),  (-1,0),  WHITE),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("GRID",          (0,0),  (-1,-1), 0.4, _GRID_PINK),
        ("BACKGROUND",    (0,1),  (-1,-1), PINK_FAINT),
        ("TEXTCOLOR",     (1,1),  (1,-1),  PINK_DARK),
        ("FONTNAME",      (1,1),  (1,-1),  "Helvetica-Bold"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
        ("TOPPADDING",    (0,0),  (-1,-1), 4),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 4),
    ]))
    story.append(t_docs)
    story.append(Spacer(1,5))

    # 6. Declaration
    story.append(_sec("6.   PARENT / GUARDIAN DECLARATION"))
    story.append(Spacer(1,4))
    story.append(Paragraph(
        "I hereby certify that the information provided in this enrollment form is true "
        "and correct to the best of my knowledge. I agree to abide by the policies, rules, "
        "and regulations of the school.", ST["legal"]))
    story.append(Spacer(1,10))
    sig = Table([
        [Paragraph("Signature of Parent/Guardian", ST["label"]), Paragraph("Date", ST["label"])],
        ["",""],
        ["___________________________","_______________"],
    ], colWidths=[3.5*inch, 2*inch])
    sig.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("TOPPADDING",    (1,0), (-1,-1), 10),
    ]))
    story.append(sig)
    story.append(Spacer(1,5))

    # 7. For registrar use
    story.append(_sec("7.   FOR REGISTRAR USE ONLY"))
    story.append(Spacer(1,4))
    story.append(_two_col([
        ("Tracking ID", s.get("trackingId",""), "Enrollment Status", (s.get("status","Pending") or "Pending").capitalize()),
        ("Total Assessed Fees", f"PHP {_peso(fdata['total'])}", "Amount Paid", f"PHP {_peso(s.get('paidAmount',0) or 0)}"),
        ("OR Number", "", "Date Processed", ""),
    ]))

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
#  2.  ENROLLMENT CONTRACT
# ═══════════════════════════════════════════════════════════════════════════════
def build_contract(s: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LONG_BOND,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN + 0.5*inch,
                            bottomMargin=MARGIN + 0.4*inch)
    story = []
    sy         = s.get("schoolYear", SCHOOL_YEAR)
    pguardian  = s.get("fatherName") or s.get("motherName") or s.get("guardianName") or "[Parent/Guardian Name]"
    learner    = f"{s.get('firstName','')} {s.get('lastName','')}".strip() or "[Student Name]"
    grade      = s.get("grade","___")
    lrn        = s.get("lrn","____________")
    fdata      = compute_fees(s.get("level","jhs"), grade)
    reg_fee    = fdata["lines"].get("Registration Fee", 6000)

    story.append(_logo_header(sy))
    story.append(Spacer(1,5))
    story.append(Paragraph("ENROLLMENT CONTRACT", ST["doc_title"]))
    story.append(Paragraph(f"School Year {sy}", ST["doc_sub"]))
    story.append(_hline())
    story.append(Spacer(1,4))

    story.append(Paragraph("THIS CONTRACT OF ENROLLMENT is executed by and between:", ST["legal"]))
    story.append(Spacer(1,3))
    story.append(Paragraph(
        f"<b>SCHOOL OF EVERLASTING PEARL, INC. (SEPI)</b>, a private educational institution duly "
        f"organized and existing under the laws of the Republic of the Philippines, with principal "
        f"office address at <b>{SCHOOL_ADDRESS}</b>, herein represented by its duly authorized "
        f'School Head, hereinafter referred to as the <b>"SCHOOL"</b>;', ST["legal"]))
    story.append(Paragraph("– and –", ST["center"]))
    story.append(Paragraph(
        f"<b>{pguardian}</b>, of legal age, Filipino citizen, acting in behalf of his/her minor "
        f"child/ward <b>{learner}</b>, enrolled in <b>{grade}</b> with Learner Reference Number "
        f"(LRN) <b>{lrn}</b>, hereinafter referred to as the <b>\"PARENT/GUARDIAN.\"</b>",
        ST["legal"]))
    story.append(Paragraph(
        'The SCHOOL and the PARENT/GUARDIAN are collectively referred to as the <b>"PARTIES."</b>',
        ST["legal"]))
    story.append(Spacer(1,6))

    story.append(Paragraph("WITNESSETH", ST["witness"]))
    for w in [
        "WHEREAS, the SCHOOL provides academic and values-based education in accordance with DepEd standards and its own institutional philosophy;",
        "WHEREAS, the PARENT/GUARDIAN desires to enroll his/her child/ward in the SCHOOL and bind himself/herself to the rules, regulations, and financial obligations attendant thereto;",
        "NOW, THEREFORE, for and in consideration of the foregoing premises, the PARTIES hereby agree as follows:",
    ]:
        story.append(Paragraph(w, ST["legal"]))
    story.append(Spacer(1,4))

    articles = [
        ("ARTICLE I – ENROLLMENT AND ACCEPTANCE", [
            "1.1 The SCHOOL accepts the enrollment of the LEARNER subject to compliance with DepEd regulations, submission of credentials, and observance of the SCHOOL's handbook and policies.",
            "1.2 The PARENT/GUARDIAN warrants the authenticity of all information and documents submitted during enrollment.",
        ]),
        ("ARTICLE II – DATA PRIVACY", [
            "2.1 The SCHOOL, in compliance with RA 10173 (Data Privacy Act of 2012), shall collect, process, and store personal information of the LEARNER solely for academic, administrative, and regulatory purposes.",
            "2.2 The PARENT/GUARDIAN hereby grants authorization to share necessary data with DepEd, PEAC, ESC, and partner institutions as required by law and existing policies.",
        ]),
        ("ARTICLE III – COMPLIANCE WITH REGULATIONS", [
            "3.1 The PARENT/GUARDIAN and LEARNER agree to abide by the SCHOOL's rules and regulations as provided in the official Handbook.",
            "3.2 Disciplinary measures, academic standards, and participation in school programs shall be respected as within the SCHOOL's academic freedom and professional judgment.",
        ]),
        ("ARTICLE IV – PAYMENT OF FEES", [
            f"4.1 The PARENT/GUARDIAN binds himself/herself to pay the following: Registration Fee of PHP {_peso(reg_fee)} (non-refundable); Tuition Fee and Miscellaneous Fees as per Statement of Account; and other authorized charges approved by the SCHOOL.",
            "4.2 Fees may be settled by full payment, semestral, or installment basis per the agreed schedule.",
            "4.3 In case of inability to pay, the PARENT/GUARDIAN may execute a Notarized Promissory Note subject to the SCHOOL's approval.",
        ]),
        ("ARTICLE V – RELEASE OF CREDENTIALS", [
            "5.1 The SCHOOL reserves the right to withhold credentials (Form 138, Form 137, ESC Certificates, and other documents) until all financial obligations are fully settled.",
            "5.2 Conditional release of certified copies may be granted only under a duly notarized promissory note, provided that balances are settled before graduation or transfer.",
        ]),
        ("ARTICLE VI – TRANSFER, WITHDRAWAL, AND DROPOUT", [
            "6.1 A withdrawing LEARNER shall be charged: 10% of total fees if withdrawal is within the first week of classes; 20% of total fees if within the second week; 100% of total fees if beyond the second week.",
            "6.2 Dropout learners shall remain liable for fees proportionate to the period attended, subject to equitable adjustments.",
        ]),
        ("ARTICLE VII – REMEDIES", [
            "7.1 Failure of the PARENT/GUARDIAN to comply with financial or contractual obligations shall authorize the SCHOOL to withhold documents, impose penalties, and/or pursue legal action for collection of unpaid obligations, including attorney's fees and costs of litigation.",
        ]),
        ("ARTICLE VIII – MISCELLANEOUS", [
            f"8.1 This contract is valid only for School Year {sy}, unless earlier terminated by withdrawal, transfer, or expulsion.",
            "8.2 Any amendment must be in writing and signed by both PARTIES.",
            "8.3 This contract shall be governed by the laws of the Republic of the Philippines.",
        ]),
    ]

    for title, clauses in articles:
        story.append(KeepTogether([
            Paragraph(title, ST["legal_bold"]),
            *[Paragraph(c, ST["legal"]) for c in clauses],
            Spacer(1, 4),
        ]))

    story.append(Spacer(1,6))
    story.append(Paragraph(
        f"IN WITNESS WHEREOF, the PARTIES have hereunto affixed their signatures this "
        f"___ day of _______, _____ at {SCHOOL_CITY}.", ST["legal"]))
    story.append(Spacer(1,18))

    sig_data = [
        ["PARENT/GUARDIAN",                             "SCHOOL REPRESENTATIVE"],
        ["",""],
        ["_______________________________",             "_______________________________"],
        [pguardian,                                     "School Principal"],
        ["",""],
        ["Witness:",""],
        ["_______________________________",             "_______________________________"],
        ["School Registrar / Data Protection Officer",  "Class Adviser"],
    ]
    tsig = Table(sig_data, colWidths=[CONTENT_W/2-5, CONTENT_W/2-5])
    tsig.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0), (-1,0),  PINK_DARK),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
    ]))
    story.append(tsig)
    # NOTE: Republic of the Philippines / notarization block removed per admin instruction

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
#  3.  STATEMENT OF ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════════
def build_soa(s: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LONG_BOND,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN + 0.5*inch,
                            bottomMargin=MARGIN + 0.4*inch)
    story = []
    sy    = s.get("schoolYear", SCHOOL_YEAR)
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"))
    lines = fdata["lines"]
    total = fdata["total"]
    paid  = float(s.get("paidAmount",0) or 0)
    bal   = total - paid
    llabel= {"preschool":"Kinder/Preschool","elementary":"Elementary",
             "jhs":"Junior High School",}
    name  = f"{s.get('lastName','')}, {s.get('firstName','')} {s.get('middleName','')}".strip()
    grade_disp = f"{llabel.get(s.get('level',''),'—')} — {s.get('grade','—')}"

    story.append(_logo_header(sy))
    story.append(Spacer(1,5))
    story.append(Paragraph("STATEMENT OF ACCOUNT", ST["doc_title"]))
    story.append(Paragraph(f"School Year {sy}", ST["doc_sub"]))
    story.append(_hline())
    story.append(Spacer(1,4))

    # Student header
    story.append(_two_col([
        ("Student Name",      name or "—",              "Grade Level",    grade_disp),
        ("Tracking ID",       s.get("trackingId","—"),  "LRN",            s.get("lrn","—")),
        ("ESC Grantee",       "☐ Yes   ☐ No",            "Other Subsidy",  "N/A"),
        ("Parent / Guardian", s.get("fatherName") or s.get("motherName","—"),
         "Contact Number",    s.get("phone","—")),
    ]))
    story.append(Spacer(1,8))

    # A. Previous Balance
    story.append(_sec("A.   OUTSTANDING BALANCE FROM PREVIOUS SCHOOL YEAR/S"))
    story.append(Spacer(1,4))
    prev = [["Particulars","Amount (PHP)"],
            ["Tuition Balance","—"],
            ["Miscellaneous Fees","—"],
            ["Other Fees","—"],
            ["TOTAL PREVIOUS BALANCE","0.00"]]
    tp = Table(prev, colWidths=[CONTENT_W - 1.8*inch, 1.8*inch])
    tps = TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  PINK_DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("GRID",          (0,0),  (-1,-1), 0.4, _GRID_PINK),
        ("BACKGROUND",    (0,1),  (-1,-2), PINK_FAINT),
        ("ALIGN",         (1,0),  (1,-1),  "RIGHT"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
        ("TOPPADDING",    (0,0),  (-1,-1), 4),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 4),
        ("BACKGROUND",    (0,-1), (-1,-1), PINK_LIGHT),
        ("TEXTCOLOR",     (0,-1), (-1,-1), PINK_DARK),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
    ])
    tp.setStyle(tps)
    story.append(tp)
    story.append(Spacer(1,8))

    # B. Current SY Assessment
    story.append(_sec(f"B.   CURRENT SCHOOL YEAR ASSESSMENT  (SY {sy})"))
    story.append(Spacer(1,4))
    curr = [["Particulars","Amount (PHP)"]]
    for k,v in lines.items():
        curr.append([k, _peso(v)])
    curr.append(["TOTAL SCHOOL FEES", _peso(total)])
    tc = Table(curr, colWidths=[CONTENT_W - 1.8*inch, 1.8*inch])
    tc.setStyle(_fee_ts(len(curr)))
    story.append(tc)
    story.append(Spacer(1,8))

    # C. Summary of Payables
    story.append(_sec("C.   SUMMARY OF PAYABLES"))
    story.append(Spacer(1,4))
    summ = [
        ["Particulars","Amount (PHP)"],
        ["Balance from Previous SY","0.00"],
        ["Current SY Net Assessment",_peso(total)],
        ["TOTAL ASSESSMENT DUE",_peso(total)],
        [f"Less: Payment upon Enrollment / Tuition",f"({_peso(paid)})"],
        ["OUTSTANDING BALANCE *",_peso(bal)],
    ]
    ts_rows = len(summ)
    tsum = Table(summ, colWidths=[CONTENT_W - 1.8*inch, 1.8*inch])
    tsums = TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  PINK_DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8),
        ("GRID",          (0,0),  (-1,-1), 0.4, _GRID_PINK),
        ("BACKGROUND",    (0,1),  (-1,-2), PINK_FAINT),
        ("ALIGN",         (1,0),  (1,-1),  "RIGHT"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
        ("TOPPADDING",    (0,0),  (-1,-1), 4),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 4),
        # Total row (row 3)
        ("BACKGROUND",    (0,3),  (-1,3),  PINK_LIGHT),
        ("TEXTCOLOR",     (0,3),  (-1,3),  PINK_DARK),
        ("FONTNAME",      (0,3),  (-1,3),  "Helvetica-Bold"),
        # Outstanding row (last)
        ("BACKGROUND",    (0,-1), (-1,-1), PINK_DARK),
        ("TEXTCOLOR",     (0,-1), (-1,-1), WHITE),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1), (-1,-1), 9),
    ])
    tsum.setStyle(tsums)
    story.append(tsum)
    story.append(Spacer(1,4))
    story.append(Paragraph(
        "* Outstanding balance must be settled per the agreed payment schedule.", ST["small"]))
    story.append(Spacer(1,8))

    story.append(Paragraph(
        "All charges have been reviewed and approved by the Finance Office in accordance with "
        "DepEd policies and the school's schedule of fees.", ST["legal"]))
    story.append(Paragraph(
        "This certification is issued upon the request of the parent/guardian for whatever "
        "legitimate purpose it may serve.", ST["legal"]))
    story.append(Paragraph(
        f"For verification please contact us at <b>{SCHOOL_EMAIL}</b> or call/text "
        f"<b>{SCHOOL_PHONE}</b>.", ST["legal"]))
    story.append(Spacer(1,14))

    sig2 = Table([
        ["Prepared by:","","Reviewed by:",""],
        ["","","",""],
        ["______________________","","______________________",""],
        ["School Registrar / DPO","","School Principal",""],
        ["","","",""],
        ["Approved by:","","",""],
        ["","","",""],
        ["______________________","","",""],
        ["Mr. Jasper E. Elipane","","",""],
        ["School President","","",""],
    ], colWidths=[2*inch, 0.4*inch, 2.2*inch, CONTENT_W - 4.6*inch])
    sig2.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("FONTNAME",   (0,0), (0,0),  "Helvetica-Bold"),("TEXTCOLOR",(0,0),(0,0),PINK_DARK),
        ("FONTNAME",   (2,0), (2,0),  "Helvetica-Bold"),("TEXTCOLOR",(2,0),(2,0),PINK_DARK),
        ("FONTNAME",   (0,5), (0,5),  "Helvetica-Bold"),("TEXTCOLOR",(0,5),(0,5),PINK_DARK),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",(0,0), (-1,-1), 0),
    ]))
    story.append(sig2)

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()
