"""
SEPI PDF Generator  -  SY 2026-2027
Produces: Enrollment Form | Enrollment Contract | Statement of Account
Format  : Long Bond Paper 8.5" x 13" | Pink accent | SEPI logo watermark
"""

import os, io
from reportlab.lib.pagesizes import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether,
                                Image as RLImage)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from fees import (SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_EMAIL, SCHOOL_PHONE,
                  SCHOOL_CITY, SCHOOL_YEAR, LEVEL_LABEL, compute_fees, DISCOUNT_BY_KEY)

# ── Page layout ───────────────────────────────────────────────────────────────
LONG_BOND  = (8.5 * inch, 13 * inch)
PAGE_W, PAGE_H = LONG_BOND
MARGIN     = 0.75 * inch
CW         = PAGE_W - 2 * MARGIN   # 7.0 inches usable width

LOGO_PATH  = os.path.join(os.path.dirname(__file__), "sepi_logo.jpg")

# Try alternate logo filenames
if not os.path.exists(LOGO_PATH):
    for _name in ["sepi_logo.png", "sepi_logo", "SEPI_Logo_HighResol"]:
        _p = os.path.join(os.path.dirname(__file__), _name)
        if os.path.exists(_p):
            LOGO_PATH = _p
            break

# ── Colors ────────────────────────────────────────────────────────────────────
C_PINK     = colors.HexColor("#C2185B")
C_PINK_MID = colors.HexColor("#E91E63")
C_PINK_LT  = colors.HexColor("#FCE4EC")
C_PINK_FT  = colors.HexColor("#FFF0F5")
C_NAVY     = colors.HexColor("#1A2333")
C_GRAY     = colors.HexColor("#757575")
C_GRID     = colors.HexColor("#E0B0C0")
C_WHITE    = colors.white

# ── Column widths (7.0" total) ─────────────────────────────────────────────────
# Single-col table:  label 1.8" | value 5.2"
LW1  = 1.80 * inch
VW1  = CW - LW1          # 5.20"

# Two-col table:     label 1.2" | value 2.3" | label 1.2" | value 2.3"
LW2  = 1.20 * inch
VW2  = (CW - 2 * LW2) / 2   # 2.30"

# Parent block:      label 1.0" | value 2.5" | label 1.1" | value 2.4"
LP   = 1.00 * inch
VP   = 2.50 * inch
LP2  = 1.10 * inch
VP2  = CW - LP - VP - LP2    # 2.40"

# ── Styles ────────────────────────────────────────────────────────────────────
def _S():
    s = {}
    s["title"]  = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=15,
                    textColor=C_PINK, alignment=TA_CENTER, spaceAfter=2, leading=19)
    s["sub"]    = ParagraphStyle("sub",   fontName="Helvetica",      fontSize=9,
                    textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=5)
    s["sname"]  = ParagraphStyle("sname", fontName="Helvetica-Bold", fontSize=11,
                    textColor=C_PINK, leading=14)
    s["sec"]    = ParagraphStyle("sec",   fontName="Helvetica-Bold", fontSize=8,
                    textColor=C_WHITE, alignment=TA_LEFT, spaceAfter=0,
                    spaceBefore=0, leading=13)
    s["lbl"]    = ParagraphStyle("lbl",   fontName="Helvetica-Bold", fontSize=7.5,
                    textColor=C_PINK, leading=10)
    s["val"]    = ParagraphStyle("val",   fontName="Helvetica",      fontSize=8.5,
                    textColor=C_NAVY, leading=11, wordWrap="LTR")
    s["small"]  = ParagraphStyle("small", fontName="Helvetica",      fontSize=7.5,
                    textColor=C_GRAY, leading=11)
    s["body"]   = ParagraphStyle("body",  fontName="Helvetica",      fontSize=8.5,
                    textColor=C_NAVY, leading=12, spaceAfter=4)
    s["legal"]  = ParagraphStyle("legal", fontName="Helvetica",      fontSize=8.5,
                    textColor=C_NAVY, leading=13, spaceAfter=5, alignment=TA_JUSTIFY)
    s["lblold"] = ParagraphStyle("lblold",fontName="Helvetica-Bold", fontSize=7.5,
                    textColor=C_PINK)
    s["center"] = ParagraphStyle("ctr",   fontName="Helvetica",      fontSize=8.5,
                    textColor=C_NAVY, alignment=TA_CENTER, leading=12)
    s["witness"]= ParagraphStyle("wit",   fontName="Helvetica-Bold", fontSize=9,
                    textColor=C_PINK, alignment=TA_CENTER, spaceAfter=4)
    s["legbold"]= ParagraphStyle("lgb",   fontName="Helvetica-Bold", fontSize=8.5,
                    textColor=C_NAVY, leading=13, spaceAfter=5)
    return s

ST = _S()

# ── Base table style ──────────────────────────────────────────────────────────
_BASE_TS = [
    ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
    ("FONTSIZE",      (0,0), (-1,-1), 8.5),
    ("GRID",          (0,0), (-1,-1), 0.4, C_GRID),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ("TOPPADDING",    (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
]

def _lbl(text):
    return Paragraph(text, ST["lbl"])

def _val(text):
    return Paragraph(str(text) if text else "\u2014", ST["val"])

# ── 1-column field row  (label | value spanning full width) ──────────────────
def _row1(label, value):
    """Single full-width row: pink label cell | wide value cell."""
    t = Table([[_lbl(label), _val(value)]],
              colWidths=[LW1, VW1])
    t.setStyle(TableStyle(_BASE_TS + [
        ("BACKGROUND", (0,0), (0,0), C_PINK_LT),
        ("BACKGROUND", (1,0), (1,0), C_PINK_FT),
        ("FONTNAME",   (0,0), (0,0), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0), (0,0), C_PINK),
    ]))
    return t

# ── 2-column field row (label|value|label|value) ──────────────────────────────
def _row2(label1, val1, label2, val2):
    t = Table([[_lbl(label1), _val(val1), _lbl(label2), _val(val2)]],
              colWidths=[LW2, VW2, LW2, VW2])
    t.setStyle(TableStyle(_BASE_TS + [
        ("BACKGROUND", (0,0), (0,0), C_PINK_LT),
        ("BACKGROUND", (2,0), (2,0), C_PINK_LT),
        ("BACKGROUND", (1,0), (1,0), C_PINK_FT),
        ("BACKGROUND", (3,0), (3,0), C_PINK_FT),
        ("FONTNAME",   (0,0), (0,0), "Helvetica-Bold"),
        ("FONTNAME",   (2,0), (2,0), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0), (0,0), C_PINK),
        ("TEXTCOLOR",  (2,0), (2,0), C_PINK),
    ]))
    return t

# ── Parent block: name|occ on one row, contact on next ───────────────────────
def _parent_block(title, name, occ, phone):
    """
    Row 0: Title header spanning full width
    Row 1: Name (label+value) | Occupation (label+value)
    Row 2: Contact Number (label+value) spanning left half
    """
    # Title row
    hdr = Table([[_lbl(title), ""]],
                colWidths=[LP, CW - LP])
    hdr.setStyle(TableStyle(_BASE_TS + [
        ("BACKGROUND", (0,0), (-1,0), C_PINK_LT),
        ("SPAN",       (0,0), (1,0)),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0), (-1,0), C_PINK),
        ("FONTSIZE",   (0,0), (-1,0), 8),
    ]))

    # Name | Occupation row  (LP=1.0" VP=2.5" LP2=1.1" VP2=2.4")
    row_no = Table([[_lbl("Name"), _val(name), _lbl("Occupation"), _val(occ)]],
                   colWidths=[LP, VP, LP2, VP2])
    row_no.setStyle(TableStyle(_BASE_TS + [
        ("BACKGROUND", (0,0), (0,0), C_PINK_LT),
        ("BACKGROUND", (2,0), (2,0), C_PINK_LT),
        ("BACKGROUND", (1,0), (1,0), C_PINK_FT),
        ("BACKGROUND", (3,0), (3,0), C_PINK_FT),
        ("FONTNAME",   (0,0), (0,0), "Helvetica-Bold"),
        ("FONTNAME",   (2,0), (2,0), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0), (0,0), C_PINK),
        ("TEXTCOLOR",  (2,0), (2,0), C_PINK),
    ]))

    # Contact row - full width split in half
    half = CW / 2
    row_c = Table([[_lbl("Contact Number"), _val(phone),
                    _lbl("Email Address"), _val("")]],
                  colWidths=[LP, half - LP, LP2, half - LP2])
    row_c.setStyle(TableStyle(_BASE_TS + [
        ("BACKGROUND", (0,0), (0,0), C_PINK_LT),
        ("BACKGROUND", (2,0), (2,0), C_PINK_LT),
        ("BACKGROUND", (1,0), (1,0), C_PINK_FT),
        ("BACKGROUND", (3,0), (3,0), C_PINK_FT),
        ("FONTNAME",   (0,0), (0,0), "Helvetica-Bold"),
        ("FONTNAME",   (2,0), (2,0), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0), (0,0), C_PINK),
        ("TEXTCOLOR",  (2,0), (2,0), C_PINK),
    ]))

    return [hdr, row_no, row_c]

# ── Fee table style ───────────────────────────────────────────────────────────
def _fee_ts(n_rows):
    return TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),       C_PINK),
        ("FONTNAME",      (0,0),  (-1,0),        "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0),  (-1,0),        C_WHITE),
        ("FONTSIZE",      (0,0),  (-1,-1),       8.5),
        ("GRID",          (0,0),  (-1,-1),       0.4, C_GRID),
        ("BACKGROUND",    (0,1),  (-1,n_rows-2), C_PINK_FT),
        ("ALIGN",         (1,0),  (1,-1),        "RIGHT"),
        ("LEFTPADDING",   (0,0),  (-1,-1),       6),
        ("RIGHTPADDING",  (0,0),  (-1,-1),       6),
        ("TOPPADDING",    (0,0),  (-1,-1),       5),
        ("BOTTOMPADDING", (0,0),  (-1,-1),       5),
        ("VALIGN",        (0,0),  (-1,-1),       "MIDDLE"),
        ("BACKGROUND",    (0,-1), (-1,-1),       C_PINK),
        ("TEXTCOLOR",     (0,-1), (-1,-1),       C_WHITE),
        ("FONTNAME",      (0,-1), (-1,-1),       "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1), (-1,-1),       9),
    ])

# ── Page frame ────────────────────────────────────────────────────────────────
def _draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PINK)
    canvas.rect(0, PAGE_H - 0.45*inch, PAGE_W, 0.45*inch, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE); canvas.setFont("Helvetica-Bold", 8)
    canvas.drawCentredString(PAGE_W/2, PAGE_H - 0.28*inch, SCHOOL_NAME)
    canvas.setFillColor(C_PINK)
    canvas.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE); canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN, 0.13*inch,
                      f"{SCHOOL_EMAIL}  |  {SCHOOL_PHONE}  |  {SCHOOL_CITY}")
    canvas.drawRightString(PAGE_W - MARGIN, 0.13*inch,
                           f"Page {canvas.getPageNumber()}")
    try:
        canvas.setFillAlpha(0.06)
        canvas.drawImage(LOGO_PATH, (PAGE_W-4*inch)/2, (PAGE_H-4*inch)/2,
                         width=4*inch, height=4*inch, preserveAspectRatio=True, mask="auto")
    except Exception:
        pass
    canvas.setFillAlpha(1)
    canvas.restoreState()

# ── Logo header ───────────────────────────────────────────────────────────────
def _logo_header(sy):
    school_p = Paragraph(
        f"<b>{SCHOOL_NAME}</b><br/>"
        f"<font size=8 color='#757575'>{SCHOOL_ADDRESS}</font><br/>"
        f"<font size=7.5 color='#757575'>SY {sy}</font>",
        ST["sname"])
    try:
        logo = RLImage(LOGO_PATH, width=50, height=50)
        data, cw = [[logo, school_p]], [56, CW - 56]
    except Exception:
        data, cw = [[school_p]], [CW]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("GRID",          (0,0), (-1,-1), 0, C_WHITE),
    ]))
    return t

def _hline():
    return HRFlowable(width="100%", thickness=1.5, color=C_PINK_MID, spaceAfter=5)

def _sec(text):
    """Full-width pink section header bar — uses Table to guarantee edge-to-edge fill."""
    p = Paragraph(f"  {text}", ST["sec"])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0), C_PINK),
        ("LEFTPADDING",   (0,0), (0,0), 8),
        ("RIGHTPADDING",  (0,0), (0,0), 8),
        ("TOPPADDING",    (0,0), (0,0), 5),
        ("BOTTOMPADDING", (0,0), (0,0), 5),
        ("VALIGN",        (0,0), (0,0), "MIDDLE"),
    ]))
    return t

def _peso(n):
    return f"{float(n or 0):,.2f}"


# =============================================================================
#  1. ENROLLMENT FORM
# =============================================================================
def build_enrollment_form(s: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LONG_BOND,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN + 0.5*inch,
                            bottomMargin=MARGIN + 0.4*inch)
    story = []
    sy    = s.get("schoolYear", SCHOOL_YEAR)
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"),
                         s.get("discountKey"), s.get("discountRate"))

    story.append(_logo_header(sy))
    story.append(Spacer(1, 5))
    story.append(Paragraph("STUDENT ENROLLMENT FORM", ST["title"]))
    story.append(Paragraph(
        "Please complete this form in BLOCK LETTERS. "
        "All information will be treated with confidentiality and used for official school records only.",
        ST["small"]))
    story.append(_hline())

    # Tracking ID & status banner — visible at top of form
    tid = s.get("trackingId","")
    if tid:
        tid_banner = Table([[
            Paragraph("<b>TRACKING ID:</b>", ST["lbl"]),
            Paragraph(f"<b>{tid}</b>", ParagraphStyle("tid", fontName="Helvetica-Bold",
                fontSize=11, textColor=C_PINK, leading=13)),
            Paragraph("<b>SCHOOL YEAR:</b>", ST["lbl"]),
            Paragraph(f"<b>{sy}</b>", ParagraphStyle("sy2", fontName="Helvetica-Bold",
                fontSize=11, textColor=C_NAVY, leading=13)),
            Paragraph("<b>STATUS:</b>", ST["lbl"]),
            Paragraph(f"<b>{(s.get('status','PENDING') or 'PENDING').upper()}</b>",
                ParagraphStyle("st2", fontName="Helvetica-Bold", fontSize=10,
                    textColor=C_PINK, leading=13)),
        ]], colWidths=[1.1*inch, 1.6*inch, 1.1*inch, 1.3*inch, 0.7*inch, 1.2*inch])
        tid_banner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), C_PINK_LT),
            ("GRID",          (0,0), (-1,0), 0.5, C_PINK),
            ("LEFTPADDING",   (0,0), (-1,0), 6),
            ("RIGHTPADDING",  (0,0), (-1,0), 6),
            ("TOPPADDING",    (0,0), (-1,0), 6),
            ("BOTTOMPADDING", (0,0), (-1,0), 6),
            ("VALIGN",        (0,0), (-1,0), "MIDDLE"),
            ("BACKGROUND",    (1,0), (1,0),  C_PINK_FT),
            ("BACKGROUND",    (3,0), (3,0),  C_PINK_FT),
            ("BACKGROUND",    (5,0), (5,0),  C_PINK_FT),
        ]))
        story.append(tid_banner)
        story.append(Spacer(1, 4))

    # ── 1. Student Information ────────────────────────────────────────────────
    story.append(_sec("1.   STUDENT INFORMATION"))
    story.append(Spacer(1, 3))

    name = f"{s.get('lastName','')}, {s.get('firstName','')} {s.get('middleName','')}".strip()
    story.append(_row1("Full Name (Last, First, Middle)", name))
    story.append(_row2("Sex / Gender",
                       (s.get("gender","") or "").capitalize(),
                       "Date of Birth", s.get("birthDate","")))
    story.append(_row2("Place of Birth", s.get("placeOfBirth",""),
                       "Nationality",   s.get("nationality","Filipino")))
    story.append(_row2("Religion",       s.get("religion",""),
                       "Transfer Status", s.get("transferStatus","New Student")))
    addr = " ".join(filter(None, [s.get("address",""), s.get("barangay",""),
                                   s.get("city",""), s.get("province","")]))
    story.append(_row1("Complete Address (House No., Street, Barangay, City/Municipality, Province)", addr))
    story.append(_row2("Mobile Number", s.get("phone",""),
                       "Email Address", s.get("email","")))
    story.append(Spacer(1, 4))

    # ── 2. Educational Background ─────────────────────────────────────────────
    story.append(_sec("2.   EDUCATIONAL BACKGROUND"))
    story.append(Spacer(1, 3))
    story.append(_row2("Learner Reference No. (LRN)", s.get("lrn",""),
                       "Last Grade Completed", s.get("lastGradeCompleted","")))
    story.append(_row1("Last School Attended", s.get("previousSchool","")))
    story.append(Spacer(1, 4))

    # ── 3. Parent / Guardian ──────────────────────────────────────────────────
    story.append(_sec("3.   PARENT / GUARDIAN INFORMATION"))
    story.append(Spacer(1, 3))
    for title, nk, ok, pk in [
        ("Father", "fatherName", "fatherOccupation", "fatherPhone"),
        ("Mother", "motherName", "motherOccupation", "motherPhone"),
    ]:
        for el in _parent_block(title, s.get(nk,""), s.get(ok,""), s.get(pk,"")):
            story.append(el)
    if s.get("guardianName"):
        story.append(_row1("Guardian's Name",   s.get("guardianName","")))
        story.append(_row2("Relationship",       s.get("guardianRelation",""),
                           "Guardian Contact",   s.get("guardianPhone","")))
    story.append(Spacer(1, 4))

    # ── 4. Enrollment Details ─────────────────────────────────────────────────
    story.append(_sec("4.   ENROLLMENT DETAILS"))
    story.append(Spacer(1, 3))
    llbl = {"preschool": "Kinder/Preschool", "elementary": "Elementary",
             "jhs": "Junior High School"}
    grade_disp = f"{llbl.get(s.get('level',''),'—')} — {s.get('grade','—')}"
    story.append(_row2("School Year", sy, "Grade Level", grade_disp))
    pm      = (s.get("paymentMode","Cash") or "Cash").capitalize()
    esc_txt = "Yes" if s.get("escGrantee") else "No"
    story.append(_row2("Mode of Payment", pm, "ESC Grantee", esc_txt))
    story.append(Spacer(1, 4))

    # ── 4B. Scholarship / Discount ────────────────────────────────────────────
    story.append(_sec("4B.  SCHOLARSHIP / DISCOUNT"))
    story.append(Spacer(1, 3))
    disc_info_ef = s.get("discountInfo") or fdata.get("discount")
    if disc_info_ef:
        d_key  = disc_info_ef.get("key","")
        d_lbl  = disc_info_ef.get("label","")
        d_rate = disc_info_ef.get("rate", 0)
        d_amt  = disc_info_ef.get("amount", 0)
        d_base = disc_info_ef.get("base_tuition", 0)
        story.append(_row1("Discount Type Availed", d_lbl))
        story.append(_row2("Discount Rate", f"{d_rate}% on Tuition Fee",
                           "Discount Amount", f"PHP {_peso(d_amt)}"))
        story.append(_row2("Tuition (Original)", f"PHP {_peso(d_base)}",
                           "Tuition (After Discount)", f"PHP {_peso(d_base - d_amt)}"))
        if s.get("discountRemarks"):
            story.append(_row1("Supporting Documents / Remarks", s.get("discountRemarks","")))
        story.append(Paragraph(
            "<i>Discount applies to tuition fee only. Subject to document verification. "
            "Non-cumulative, non-transferable, and non-convertible to cash. "
            "Only one discount per student per school year. — SEPI Discount Policy</i>",
            ParagraphStyle("disc_note", fontName="Helvetica-Oblique", fontSize=7.5,
                           textColor=C_GRAY, leading=11, spaceAfter=3)))
    else:
        story.append(_row2("Discount Type", "No Discount / Not Applicable",
                           "ESC Grantee", esc_txt))
    story.append(Spacer(1, 4))

    # ── 5. Documents Checklist — always start on a fresh page ──────────────
    from reportlab.platypus import PageBreak
    story.append(PageBreak())
    story.append(_sec("5.   REQUIRED DOCUMENTS CHECKLIST"))
    story.append(Spacer(1, 3))
    docs_list = [
        "PSA Birth Certificate", "Form 138 / Report Card", "Good Moral Certificate",
        "Certificate of Completion / Diploma", "School Clearance (if applicable)",
        "2x2 ID Pictures (6 pcs)", "Medical Certificate",
    ]
    docs_state = s.get("docs", {})
    chk_data   = [["Document", "Status"]]
    for d in docs_list:
        chk_data.append([d, "Submitted" if docs_state.get(d) else "Pending"])
    t_docs = Table(chk_data, colWidths=[CW - 1.3*inch, 1.3*inch])
    t_docs.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  C_PINK),
        ("TEXTCOLOR",     (0,0),  (-1,0),  C_WHITE),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8.5),
        ("GRID",          (0,0),  (-1,-1), 0.4, C_GRID),
        ("BACKGROUND",    (0,1),  (-1,-1), C_PINK_FT),
        ("TEXTCOLOR",     (1,1),  (1,-1),  C_PINK),
        ("FONTNAME",      (1,1),  (1,-1),  "Helvetica-Bold"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),
        ("TOPPADDING",    (0,0),  (-1,-1), 5),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 5),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0),  (1,-1),  "CENTER"),
    ]))
    story.append(t_docs)
    story.append(Spacer(1, 4))

    # ── 6. Parent / Guardian Declaration ─────────────────────────────────────
    story.append(_sec("6.   PARENT / GUARDIAN DECLARATION"))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "I hereby certify that the information provided in this enrollment form is true and correct "
        "to the best of my knowledge. I agree to abide by the policies, rules, and regulations of the school.",
        ST["legal"]))
    story.append(Spacer(1, 10))
    sig = Table([
        [Paragraph("Signature of Parent / Guardian", ST["lbl"]),
         Paragraph("Date", ST["lbl"])],
        ["", ""],
        ["__________________________", "_______________"],
    ], colWidths=[3.5*inch, 2.2*inch])
    sig.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("TOPPADDING",    (1,0), (-1,-1), 10),
    ]))
    story.append(sig)
    story.append(Spacer(1, 4))

    # ── 7. For Registrar Use Only ─────────────────────────────────────────────
    story.append(_sec("7.   FOR REGISTRAR USE ONLY"))
    story.append(Spacer(1, 3))
    # fdata already computed at top of function
    story.append(_row2("Tracking ID",       s.get("trackingId",""),
                       "Enrollment Status", (s.get("status","Pending") or "Pending").capitalize()))
    story.append(_row2("Total Assessed Fees", f"PHP {_peso(fdata['total'])}",
                       "Amount Paid",         f"PHP {_peso(s.get('paidAmount',0) or 0)}"))
    story.append(_row2("OR Number", "",
                       "Date Processed", ""))

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()


# =============================================================================
#  2. ENROLLMENT CONTRACT
# =============================================================================
def build_contract(s: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LONG_BOND,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN + 0.5*inch,
                            bottomMargin=MARGIN + 0.4*inch)
    story = []
    sy        = s.get("schoolYear", SCHOOL_YEAR)
    pguardian = (s.get("fatherName") or s.get("motherName") or
                 s.get("guardianName") or "[Parent/Guardian Name]")
    learner   = f"{s.get('firstName','')} {s.get('lastName','')}".strip() or "[Student Name]"
    grade     = s.get("grade", "___")
    lrn       = s.get("lrn", "____________")
    fdata     = compute_fees(s.get("level","jhs"), grade)
    reg_fee   = fdata["lines"].get("Registration Fee", 6000)

    story.append(_logo_header(sy))
    story.append(Spacer(1, 5))
    story.append(Paragraph("ENROLLMENT CONTRACT", ST["title"]))
    story.append(Paragraph(f"School Year {sy}", ST["sub"]))
    story.append(_hline())
    story.append(Spacer(1, 4))

    story.append(Paragraph("THIS CONTRACT OF ENROLLMENT is executed by and between:", ST["legal"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        f"<b>SCHOOL OF EVERLASTING PEARL, INC. (SEPI)</b>, a private educational institution duly "
        f"organized and existing under the laws of the Republic of the Philippines, with principal "
        f"office address at <b>{SCHOOL_ADDRESS}</b>, herein represented by its duly authorized "
        "School Head, hereinafter referred to as the <b>\"SCHOOL\"</b>;", ST["legal"]))
    story.append(Paragraph("&ndash; and &ndash;", ST["center"]))
    story.append(Paragraph(
        f"<b>{pguardian}</b>, of legal age, Filipino citizen, acting in behalf of his/her minor "
        f"child/ward <b>{learner}</b>, enrolled in <b>{grade}</b> with Learner Reference Number "
        f"(LRN) <b>{lrn}</b>, hereinafter referred to as the <b>\"PARENT/GUARDIAN.\"</b>",
        ST["legal"]))
    story.append(Paragraph(
        "The SCHOOL and the PARENT/GUARDIAN are collectively referred to as the <b>\"PARTIES.\"</b>",
        ST["legal"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("WITNESSETH", ST["witness"]))

    for w in [
        "WHEREAS, the SCHOOL provides academic and values-based education in accordance with DepEd standards and its own institutional philosophy;",
        "WHEREAS, the PARENT/GUARDIAN desires to enroll his/her child/ward in the SCHOOL and bind himself/herself to the rules, regulations, and financial obligations attendant thereto;",
        "NOW, THEREFORE, for and in consideration of the foregoing premises, the PARTIES hereby agree as follows:",
    ]:
        story.append(Paragraph(w, ST["legal"]))
    story.append(Spacer(1, 4))

    articles = [
        ("ARTICLE I \u2013 ENROLLMENT AND ACCEPTANCE", [
            "1.1 The SCHOOL accepts the enrollment of the LEARNER subject to compliance with DepEd regulations, submission of credentials, and observance of the SCHOOL\u2019s handbook and policies.",
            "1.2 The PARENT/GUARDIAN warrants the authenticity of all information and documents submitted during enrollment.",
        ]),
        ("ARTICLE II \u2013 DATA PRIVACY", [
            "2.1 The SCHOOL, in compliance with RA 10173 (Data Privacy Act of 2012), shall collect, process, and store personal information of the LEARNER solely for academic, administrative, and regulatory purposes.",
            "2.2 The PARENT/GUARDIAN hereby grants authorization to share necessary data with DepEd, PEAC, ESC, and partner institutions as required by law and existing policies.",
        ]),
        ("ARTICLE III \u2013 COMPLIANCE WITH REGULATIONS", [
            "3.1 The PARENT/GUARDIAN and LEARNER agree to abide by the SCHOOL\u2019s rules and regulations as provided in the official Handbook.",
            "3.2 Disciplinary measures, academic standards, and participation in school programs shall be respected as within the SCHOOL\u2019s academic freedom and professional judgment.",
        ]),
        ("ARTICLE IV \u2013 PAYMENT OF FEES", [
            f"4.1 The PARENT/GUARDIAN binds himself/herself to pay the following: Registration Fee of PHP {_peso(reg_fee)} (non-refundable); Tuition Fee and Miscellaneous Fees as per Statement of Account; and other authorized charges approved by the SCHOOL.",
            "4.2 Fees may be settled by full payment, semestral, or installment basis per the agreed schedule.",
            "4.3 In case of inability to pay, the PARENT/GUARDIAN may execute a Notarized Promissory Note subject to the SCHOOL\u2019s approval.",
        ]),
        ("ARTICLE V \u2013 RELEASE OF CREDENTIALS", [
            "5.1 The SCHOOL reserves the right to withhold credentials (Form 138, Form 137, ESC Certificates, and other documents) until all financial obligations are fully settled.",
            "5.2 Conditional release of certified copies may be granted only under a duly notarized promissory note, provided that balances are settled before graduation or transfer.",
        ]),
        ("ARTICLE VI \u2013 TRANSFER, WITHDRAWAL, AND DROPOUT", [
            "6.1 A withdrawing LEARNER shall be charged: 10% of total fees if withdrawal is within the first week of classes; 20% of total fees if within the second week; 100% of total fees if beyond the second week.",
            "6.2 Dropout learners shall remain liable for fees proportionate to the period attended, subject to equitable adjustments.",
        ]),
        ("ARTICLE VII \u2013 REMEDIES", [
            "7.1 Failure of the PARENT/GUARDIAN to comply with financial or contractual obligations shall authorize the SCHOOL to withhold documents, impose penalties, and/or pursue legal action for collection of unpaid obligations, including attorney\u2019s fees and costs of litigation.",
        ]),
        ("ARTICLE VIII \u2013 MISCELLANEOUS", [
            f"8.1 This contract is valid only for School Year {sy}, unless earlier terminated by withdrawal, transfer, or expulsion.",
            "8.2 Any amendment must be in writing and signed by both PARTIES.",
            "8.3 This contract shall be governed by the laws of the Republic of the Philippines.",
        ]),
    ]

    for title, clauses in articles:
        story.append(KeepTogether([
            Paragraph(title, ST["legbold"]),
            *[Paragraph(c, ST["legal"]) for c in clauses],
            Spacer(1, 4),
        ]))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"IN WITNESS WHEREOF, the PARTIES have hereunto affixed their signatures this "
        f"___ day of _______, _____ at {SCHOOL_CITY}.", ST["legal"]))
    story.append(Spacer(1, 18))

    sig_data = [
        ["PARENT/GUARDIAN",                             "SCHOOL REPRESENTATIVE"],
        ["", ""],
        ["_______________________________",             "_______________________________"],
        [pguardian,                                     "School Principal"],
        ["", ""],
        ["Witness:", ""],
        ["_______________________________",             "_______________________________"],
        ["School Registrar / Data Protection Officer",  "Class Adviser"],
    ]
    tsig = Table(sig_data, colWidths=[CW/2 - 5, CW/2 - 5])
    tsig.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0), (-1,0),  C_PINK),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
    ]))
    story.append(tsig)

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()


# =============================================================================
#  3. STATEMENT OF ACCOUNT
# =============================================================================
def build_soa(s: dict) -> bytes:
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=LONG_BOND,
                             leftMargin=MARGIN, rightMargin=MARGIN,
                             topMargin=MARGIN + 0.5*inch,
                             bottomMargin=MARGIN + 0.4*inch)
    story = []
    sy    = s.get("schoolYear", SCHOOL_YEAR)
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"),
                         s.get("discountKey"), s.get("discountRate"))
    lines = fdata["lines"]
    total = fdata["total"]
    paid  = float(s.get("paidAmount", 0) or 0)
    bal   = total - paid
    llbl  = {"preschool":"Kinder/Preschool","elementary":"Elementary","jhs":"Junior High School"}
    name  = f"{s.get('lastName','')}, {s.get('firstName','')} {s.get('middleName','')}".strip()
    gdisp = f"{llbl.get(s.get('level',''),'—')} — {s.get('grade','—')}"
    pname = s.get("fatherName") or s.get("motherName") or "—"

    story.append(_logo_header(sy))
    story.append(Spacer(1, 5))
    story.append(Paragraph("STATEMENT OF ACCOUNT", ST["title"]))
    story.append(Paragraph(f"School Year {sy}", ST["sub"]))
    story.append(_hline())
    story.append(Spacer(1, 4))

    # Student header rows
    story.append(_row2("Student Name",    name,                   "Grade Level",    gdisp))
    story.append(_row2("Tracking ID",     s.get("trackingId","—"), "LRN",            s.get("lrn","—")))
    esc_disp = "Yes (ESC Grantee)" if s.get("escGrantee") else "No"
    disc_disp = ""
    disc_soa = s.get("discountInfo") or fdata.get("discount")
    if disc_soa:
        disc_disp = f"{disc_soa.get('label','')} ({disc_soa.get('rate',0)}%)"
    else:
        disc_disp = "None"
    story.append(_row2("ESC Grantee", esc_disp, "Discount Applied", disc_disp))
    story.append(_row2("Parent/Guardian", pname,                   "Contact Number", s.get("phone","—")))
    story.append(Spacer(1, 6))

    FW = CW - 1.8*inch   # fee particulars column width

    # ── A. Previous Balance ────────────────────────────────────────────────────
    story.append(_sec("A.   OUTSTANDING BALANCE FROM PREVIOUS SCHOOL YEAR/S"))
    story.append(Spacer(1, 3))
    prev = [["Particulars", "Amount (PHP)"],
            ["Tuition Balance", "\u2014"],
            ["Miscellaneous Fees", "\u2014"],
            ["Other Fees", "\u2014"],
            ["TOTAL PREVIOUS BALANCE", "0.00"]]
    tp = Table(prev, colWidths=[FW, 1.8*inch])
    tp.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  C_PINK),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8.5),
        ("GRID",          (0,0),  (-1,-1), 0.4, C_GRID),
        ("BACKGROUND",    (0,1),  (-1,-2), C_PINK_FT),
        ("ALIGN",         (1,0),  (1,-1),  "RIGHT"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",    (0,0),  (-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("BACKGROUND",    (0,-1), (-1,-1), C_PINK_LT),
        ("TEXTCOLOR",     (0,-1), (-1,-1), C_PINK),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
    ]))
    story.append(tp)
    story.append(Spacer(1, 6))

    # ── B. Current Assessment ──────────────────────────────────────────────────
    story.append(_sec(f"B.   CURRENT SCHOOL YEAR ASSESSMENT  (SY {sy})"))
    story.append(Spacer(1, 3))
    curr = [["Particulars", "Amount (PHP)"]]
    disc_info_soa = s.get("discountInfo") or fdata.get("discount")
    for k, v in lines.items():
        if k == "Tuition Fee" and disc_info_soa:
            d_base = disc_info_soa.get("base_tuition", v)
            d_amt  = disc_info_soa.get("amount", 0)
            d_rate = disc_info_soa.get("rate", 0)
            curr.append([f"Tuition Fee (Gross)", _peso(d_base)])
            curr.append([f"  Less: {disc_info_soa.get('label','')} ({d_rate}%)",
                         f"({_peso(d_amt)})"])
            curr.append(["Tuition Fee (Net)", _peso(v)])
        else:
            curr.append([k, _peso(v)])
    curr.append(["TOTAL SCHOOL FEES", _peso(total)])
    tc = Table(curr, colWidths=[FW, 1.8*inch])
    tc.setStyle(_fee_ts(len(curr)))
    story.append(tc)
    story.append(Spacer(1, 6))

    # ── C. Summary ─────────────────────────────────────────────────────────────
    story.append(_sec("C.   SUMMARY OF PAYABLES"))
    story.append(Spacer(1, 3))
    summ = [
        ["Particulars", "Amount (PHP)"],
        ["Balance from Previous SY", "0.00"],
        ["Current SY Net Assessment", _peso(total)],
        ["TOTAL ASSESSMENT DUE", _peso(total)],
        [f"Less: Payment upon Enrollment / Tuition", f"({_peso(paid)})"],
        ["OUTSTANDING BALANCE *", _peso(bal)],
    ]
    tsum = Table(summ, colWidths=[FW, 1.8*inch])
    tsum.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  C_PINK),("TEXTCOLOR",(0,0),(-1,0),C_WHITE),
        ("FONTNAME",      (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),  (-1,-1), 8.5),
        ("GRID",          (0,0),  (-1,-1), 0.4, C_GRID),
        ("BACKGROUND",    (0,1),  (-1,-2), C_PINK_FT),
        ("ALIGN",         (1,0),  (1,-1),  "RIGHT"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",    (0,0),  (-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("BACKGROUND",    (0,3),  (-1,3),  C_PINK_LT),
        ("TEXTCOLOR",     (0,3),  (-1,3),  C_PINK),
        ("FONTNAME",      (0,3),  (-1,3),  "Helvetica-Bold"),
        ("BACKGROUND",    (0,-1), (-1,-1), C_PINK),
        ("TEXTCOLOR",     (0,-1), (-1,-1), C_WHITE),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1), (-1,-1), 9),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
    ]))
    story.append(tsum)
    story.append(Spacer(1, 3))
    story.append(Paragraph("* Outstanding balance must be settled per the agreed payment schedule.", ST["small"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "All charges have been reviewed and approved by the Finance Office in accordance with "
        "DepEd policies and the school\u2019s schedule of fees.", ST["legal"]))
    story.append(Paragraph(
        "This certification is issued upon the request of the parent/guardian for whatever "
        "legitimate purpose it may serve.", ST["legal"]))
    story.append(Paragraph(
        f"For verification please contact us at <b>{SCHOOL_EMAIL}</b> or call/text "
        f"<b>{SCHOOL_PHONE}</b>.", ST["legal"]))
    story.append(Spacer(1, 14))

    sig2 = Table([
        ["Prepared by:", "", "Reviewed by:", ""],
        ["", "", "", ""],
        ["______________________", "", "______________________", ""],
        ["School Registrar / DPO", "", "School Principal", ""],
        ["", "", "", ""],
        ["Approved by:", "", "", ""],
        ["", "", "", ""],
        ["______________________", "", "", ""],
        ["Mr. Jasper E. Elipane", "", "", ""],
        ["School President", "", "", ""],
    ], colWidths=[2.0*inch, 0.4*inch, 2.2*inch, CW - 4.6*inch])
    sig2.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("FONTNAME",   (0,0), (0,0),  "Helvetica-Bold"),("TEXTCOLOR",(0,0),(0,0),C_PINK),
        ("FONTNAME",   (2,0), (2,0),  "Helvetica-Bold"),("TEXTCOLOR",(2,0),(2,0),C_PINK),
        ("FONTNAME",   (0,5), (0,5),  "Helvetica-Bold"),("TEXTCOLOR",(0,5),(0,5),C_PINK),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",(0,0), (-1,-1), 0),
    ]))
    story.append(sig2)

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return buf.getvalue()
