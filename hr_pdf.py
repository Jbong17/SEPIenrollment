"""
SEPI HR PDF Generator
Payslip | Payroll Summary Register | Certificate of Employment
"""
import io, os, datetime
from reportlab.lib.pagesizes import inch, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, Image as RLImage,
                                PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from fees import (SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_EMAIL,
                  SCHOOL_PHONE, SCHOOL_CITY)

LETTER     = (8.5*inch, 11*inch)
LEGAL      = (8.5*inch, 13*inch)
LEGAL_L    = (13*inch, 8.5*inch)   # landscape long bond
MARGIN     = 0.5*inch
LOGO_PATH  = os.path.join(os.path.dirname(__file__), "sepi_logo.jpg")
if not os.path.exists(LOGO_PATH):
    for _n in ["sepi_logo.png","sepi_logo","SEPI_Logo_HighResol"]:
        _p = os.path.join(os.path.dirname(__file__), _n)
        if os.path.exists(_p): LOGO_PATH = _p; break

NAVY  = colors.HexColor("#0A1628")
DGRAY = colors.HexColor("#374151")
LGRAY = colors.HexColor("#F3F4F6")
MGRAY = colors.HexColor("#D1D5DB")
WHITE = colors.white
BLACK = colors.black

P = lambda n: f"\u20b1{float(n or 0):,.2f}"
Pd= lambda n: f"({P(n)})" if float(n or 0) else "\u2014"

def _styles():
    s={}
    s["title"] =ParagraphStyle("t",fontName="Helvetica-Bold",fontSize=13,textColor=NAVY,alignment=TA_CENTER,leading=17)
    s["sub"]   =ParagraphStyle("s",fontName="Helvetica",fontSize=9,textColor=DGRAY,alignment=TA_CENTER,leading=11)
    s["sname"] =ParagraphStyle("sn",fontName="Helvetica-Bold",fontSize=11,textColor=NAVY,leading=14)
    s["body"]  =ParagraphStyle("b",fontName="Helvetica",fontSize=9,textColor=DGRAY,leading=12)
    s["bold"]  =ParagraphStyle("bb",fontName="Helvetica-Bold",fontSize=9,textColor=NAVY,leading=12)
    s["lbl"]   =ParagraphStyle("l",fontName="Helvetica-Bold",fontSize=7.5,textColor=DGRAY,leading=10)
    s["val"]   =ParagraphStyle("v",fontName="Helvetica",fontSize=9,textColor=NAVY,leading=11)
    s["small"] =ParagraphStyle("sm",fontName="Helvetica",fontSize=7.5,textColor=colors.HexColor("#6B7280"),leading=10)
    s["legal"] =ParagraphStyle("lg",fontName="Helvetica",fontSize=10,textColor=NAVY,leading=15,alignment=TA_JUSTIFY)
    s["center"]=ParagraphStyle("c",fontName="Helvetica",fontSize=9,textColor=NAVY,alignment=TA_CENTER)
    s["tbl"]   =ParagraphStyle("tb",fontName="Helvetica",fontSize=8,textColor=NAVY,leading=10)
    s["tbl_b"] =ParagraphStyle("tbb",fontName="Helvetica-Bold",fontSize=8,textColor=NAVY,leading=10)
    s["tbl_r"] =ParagraphStyle("tbr",fontName="Helvetica",fontSize=8,textColor=NAVY,leading=10,alignment=TA_RIGHT)
    s["tbl_br"]=ParagraphStyle("tbbr",fontName="Helvetica-Bold",fontSize=8,textColor=NAVY,leading=10,alignment=TA_RIGHT)
    s["tbl_c"] =ParagraphStyle("tbc",fontName="Helvetica",fontSize=8,textColor=NAVY,leading=10,alignment=TA_CENTER)
    return s
ST=_styles()

_BD=[("GRID",(0,0),(-1,-1),0.3,MGRAY),("LEFTPADDING",(0,0),(-1,-1),4),
     ("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),3),
     ("BOTTOMPADDING",(0,0),(-1,-1),3),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
     ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8)]

def _logo_hdr(cw):
    p=Paragraph(f"<b>{SCHOOL_NAME}</b><br/><font size=8 color='#6B7280'>{SCHOOL_ADDRESS}</font><br/><font size=7 color='#6B7280'>{SCHOOL_EMAIL} | {SCHOOL_PHONE}</font>",ST["sname"])
    try:
        logo=RLImage(LOGO_PATH,width=42,height=42)
        data,ww=[[logo,p]],[48,cw-48]
    except Exception:
        data,ww=[[p]],[cw]
    t=Table(data,colWidths=ww)
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("GRID",(0,0),(-1,-1),0,WHITE),
                           ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                           ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    return t

def _page_letter(canvas,doc):
    canvas.saveState()
    pw,ph=LETTER
    canvas.setFillColor(NAVY);canvas.rect(0,ph-0.38*inch,pw,0.38*inch,fill=1,stroke=0)
    canvas.setFillColor(WHITE);canvas.setFont("Helvetica-Bold",8)
    canvas.drawCentredString(pw/2,ph-0.23*inch,SCHOOL_NAME)
    canvas.setFillColor(NAVY);canvas.rect(0,0,pw,0.28*inch,fill=1,stroke=0)
    canvas.setFillColor(WHITE);canvas.setFont("Helvetica",7)
    canvas.drawString(MARGIN,0.09*inch,"CONFIDENTIAL — FOR INTERNAL USE ONLY")
    canvas.drawRightString(pw-MARGIN,0.09*inch,f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

def _page_legal_l(canvas,doc):
    canvas.saveState()
    pw,ph=LEGAL_L
    canvas.setFillColor(NAVY);canvas.rect(0,ph-0.38*inch,pw,0.38*inch,fill=1,stroke=0)
    canvas.setFillColor(WHITE);canvas.setFont("Helvetica-Bold",8)
    canvas.drawCentredString(pw/2,ph-0.23*inch,SCHOOL_NAME)
    canvas.setFillColor(NAVY);canvas.rect(0,0,pw,0.28*inch,fill=1,stroke=0)
    canvas.setFillColor(WHITE);canvas.setFont("Helvetica",7)
    canvas.drawString(MARGIN,0.09*inch,"PAYROLL REGISTER — CONFIDENTIAL")
    canvas.drawRightString(pw-MARGIN,0.09*inch,f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

def _irow(l,v,l2="",v2="",cw=None):
    if not cw: cw=[1.4*inch,2.6*inch]
    if l2:
        hw=sum(cw)/2; lw=1.4*inch; vw=hw-lw
        t=Table([[Paragraph(l,ST["lbl"]),Paragraph(v or"\u2014",ST["val"]),
                  Paragraph(l2,ST["lbl"]),Paragraph(v2 or"\u2014",ST["val"])]],
                colWidths=[lw,vw,lw,vw])
    else:
        t=Table([[Paragraph(l,ST["lbl"]),Paragraph(v or"\u2014",ST["val"])]],colWidths=cw)
    t.setStyle(TableStyle(_BD+[("BACKGROUND",(0,0),(0,0),LGRAY),("FONTNAME",(0,0),(0,0),"Helvetica-Bold"),
        ("TEXTCOLOR",(0,0),(0,0),DGRAY)]+([("BACKGROUND",(2,0),(2,0),LGRAY),
        ("FONTNAME",(2,0),(2,0),"Helvetica-Bold"),("TEXTCOLOR",(2,0),(2,0),DGRAY)] if l2 else [])))
    return t

# =============================================================================
#  INDIVIDUAL PAYSLIP  (matches SEPI format from image)
# =============================================================================
def build_payslip(r1: dict, r2: dict, teacher: dict) -> bytes:
    """
    Simple payslip matching SEPI format:
      School header | PAYSLIP | Month Year | Name
      Left:  Gross Salary & Allowances (Salary + Ancillary + TOTAL)
      Right: Deductions (SSS + PagIBIG + PhilHealth + TuitionFee + SalaryLoan + TOTAL)
      Net Salary: 1st Period + 2nd Period
      Signature: Jerald B. Bongalos, School Principal
    """
    buf = io.BytesIO()
    pw, ph = LETTER
    cw = pw - 2*MARGIN
    doc = SimpleDocTemplate(buf, pagesize=LETTER,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN+0.42*inch, bottomMargin=MARGIN+0.32*inch)
    story = []

    basic     = float(teacher.get("basicMonthlyPay", 0) or 0)
    ancillary = float(teacher.get("ancillaryPay", 0) or 0)
    gross_monthly = round(basic + ancillary, 2)

    # Government deductions (monthly totals from r2)
    sss_monthly = r2.get("sss", 0)
    pi_monthly  = r2.get("pagIbig", 0)
    ph_monthly  = r2.get("philHealth", 0)
    loan        = r2.get("salaryLoan", 0)
    tuition     = r2.get("tuitionFee", 0)
    total_deduct = r2.get("totalDeductions", 0)

    # Month label from r1 yearMonth  e.g. "2026-07" -> "JULY 2026"
    import calendar
    ym = r1.get("yearMonth", "")
    try:
        yr, mo = ym.split("-")
        mo_label = f"{calendar.month_name[int(mo)].upper()} {yr}"
    except Exception:
        mo_label = ym

    # ── School header (plain, no pink) ───────────────────────────────────────
    # Box around whole payslip
    border_table_data = [[""]]

    def PS(txt, bold=False, sz=10, align=TA_LEFT, color=BLACK):
        fn = "Helvetica-Bold" if bold else "Helvetica"
        return Paragraph(txt, ParagraphStyle("_", fontName=fn, fontSize=sz,
                                              textColor=color, alignment=align, leading=sz+3))

    story.append(PS("School of Everlasting Pearl, Inc", bold=True, sz=12, align=TA_CENTER))
    story.append(PS("#66 Siruna Village Phase III, Marcos Highway, Mambugan, Antipolo City",
                    sz=8, align=TA_CENTER, color=DGRAY))
    story.append(Spacer(1,3))
    story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceAfter=3))
    story.append(PS("PAYSLIP", bold=True, sz=13, align=TA_CENTER))
    story.append(PS(mo_label, bold=True, sz=11, align=TA_CENTER))
    story.append(Spacer(1,4))

    # Name line
    disp_name = teacher.get("name", "")
    # Convert "PANCHO, Melanie L." -> "Melanie L. Pancho"
    if "," in disp_name:
        parts = disp_name.split(",", 1)
        disp_name = f"{parts[1].strip()} {parts[0].strip().title()}"
    story.append(PS(f"Name:   <b>{disp_name}</b>", sz=10))
    story.append(Spacer(1,8))

    # ── Two-column: Gross | Deductions ────────────────────────────────────────
    def money(n):
        v = float(n or 0)
        if v == 0: return ""
        return f"₱ {v:>10,.2f}"

    def money_b(n):
        v = float(n or 0)
        if v == 0: return "₱          -"
        return f"₱ {v:>10,.2f}"

    L_LW = 1.2*inch  # label col width left side
    L_VW = 1.7*inch  # value col width left side
    R_LW = 1.2*inch
    R_VW = 1.5*inch
    GAP  = 0.1*inch
    half = (cw - GAP) / 2

    def lr(l, v, bold=False):
        fn = "Helvetica-Bold" if bold else "Helvetica"
        return [Paragraph(l, ParagraphStyle("_l", fontName=fn, fontSize=9.5, textColor=NAVY)),
                Paragraph(v, ParagraphStyle("_r", fontName=fn, fontSize=9.5, textColor=NAVY,
                                             alignment=TA_RIGHT))]

    # Left side rows
    left_rows = [
        lr("Gross Salary & Allowances", "", bold=True),
        lr("Salary:", money(basic)),
        lr("Ancillary:", money(ancillary)) if ancillary else lr("", ""),
        lr("Allowances:", ""),
        lr("TOTAL:", money_b(gross_monthly), bold=True),
    ]

    # Right side rows
    right_rows = [
        lr("Deduction:", "", bold=True),
        lr("SSS:", money(sss_monthly)),
        lr("Pag IBIG:", money(pi_monthly)),
        lr("Phil Health:", money(ph_monthly)),
        lr("Tuition Fee:", money(tuition)),
        lr("Salary Loan:", money(loan)),
        lr("TOTAL:", money_b(total_deduct), bold=True),
    ]

    # Pad to equal length
    max_rows = max(len(left_rows), len(right_rows))
    while len(left_rows)  < max_rows: left_rows.append(lr("",""))
    while len(right_rows) < max_rows: right_rows.append(lr("",""))

    combined = [lrow + [Paragraph("", ST["body"])] + rrow
                for lrow, rrow in zip(left_rows, right_rows)]

    cws = [L_LW, L_VW, GAP, R_LW, R_VW]
    tbl = Table(combined, colWidths=cws)
    tbl.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 9.5),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 2),
        ("RIGHTPADDING",  (0,0), (-1,-1), 2),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        # No grid — clean look
    ]))
    story.append(tbl)
    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MGRAY, spaceAfter=4))

    # ── Net Salary ────────────────────────────────────────────────────────────
    story.append(PS("Net Salary", bold=True, sz=10))
    net_tbl = Table([
        [PS("  1st Period:", sz=10), PS(f"₱ {r1['netPay']:,.2f}", bold=True, sz=10)],
        [PS("  2nd Period:", sz=10), PS(f"₱ {r2['netPay']:,.2f}", bold=True, sz=10)],
    ], colWidths=[1.5*inch, 2.0*inch])
    net_tbl.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("GRID",         (0,0),(-1,-1), 0, WHITE),
    ]))
    story.append(net_tbl)
    story.append(Spacer(1,16))

    # ── Signature ─────────────────────────────────────────────────────────────
    sig = Table([
        [PS("Jerald B. Bongalos", bold=True, sz=10, align=TA_CENTER)],
        [PS("School Principal", sz=9, align=TA_CENTER)],
    ], colWidths=[cw])
    sig.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0,WHITE),
                              ("TOPPADDING",(0,0),(-1,-1),2)]))
    story.append(sig)

    doc.build(story, onFirstPage=_page_letter, onLaterPages=_page_letter)
    return buf.getvalue()


# =============================================================================
#  PAYROLL SUMMARY REGISTER  (landscape long bond)
# =============================================================================
def build_payroll_summary(monthly_results: list, year_month: str, period_label: str) -> bytes:
    """
    Build the full payroll register in landscape orientation matching SEPI format.
    monthly_results: list of compute_monthly_payroll() dicts, sorted by name
    """
    buf=io.BytesIO()
    pw,ph=LEGAL_L
    cw=pw-2*MARGIN
    doc=SimpleDocTemplate(buf,pagesize=LEGAL_L,leftMargin=MARGIN,rightMargin=MARGIN,
                          topMargin=MARGIN+0.42*inch,bottomMargin=MARGIN+0.32*inch)
    story=[]

    story.append(_logo_hdr(cw))
    story.append(Spacer(1,3))
    story.append(Paragraph("PAYROLL REGISTER",ST["title"]))
    story.append(Paragraph(f"Year/Month: {period_label}",ST["sub"]))
    story.append(HRFlowable(width="100%",thickness=1.5,color=NAVY,spaceAfter=4))

    # ── Column widths (landscape 13" - 1" margins = 12" = 864pt content) ─────
    # No | Name | Basic | P1 Days | P1 Subst | P1 Pay | P2 Days | P2 Addl | P2 Pay
    # | Loan/CA | SSS | PAGIBIG | PhilHealth | TotalDeduct | Net1 | Net2
    # 16 columns total
    cws=[0.28*inch, 1.6*inch, 0.7*inch,   # no, name, basic
         0.45*inch, 0.45*inch, 0.7*inch,   # p1 days, subst, pay
         0.45*inch, 0.55*inch, 0.7*inch,   # p2 days, addl, pay
         0.55*inch, 0.55*inch, 0.55*inch, 0.6*inch, 0.65*inch,  # loan, sss, pi, ph, total
         0.7*inch, 0.7*inch]               # net1, net2
    # Total: 0.28+1.6+0.7+0.45+0.45+0.7+0.45+0.55+0.7+0.55+0.55+0.55+0.6+0.65+0.7+0.7 = 10.93" fits in 12"

    def h(txt,bold=True,c=None):
        fn="Helvetica-Bold" if bold else "Helvetica"
        return Paragraph(txt,ParagraphStyle("_hh",fontName=fn,fontSize=6.5,
                                             textColor=WHITE if c is None else c,
                                             alignment=TA_CENTER,leading=8))
    def c(txt,bold=False,align="RIGHT"):
        fn="Helvetica-Bold" if bold else "Helvetica"
        al=TA_RIGHT if align=="RIGHT" else (TA_CENTER if align=="CENTER" else TA_LEFT)
        return Paragraph(txt,ParagraphStyle("_cc",fontName=fn,fontSize=7,
                                             textColor=NAVY,alignment=al,leading=9))

    # Header rows
    hdr1=[h(""),h("Employee"),h("Basic Pay"),
          h("1st Period",c=WHITE),h(""),h(""),
          h("2nd Period",c=WHITE),h(""),h(""),
          h("Deductions",c=WHITE),h(""),h(""),h(""),h(""),
          h("Schedule of Salary",c=WHITE),h("")]
    hdr2=[h("No."),h("Name"),h(""),
          h("Days\nReported"),h("Subst."),h("Period\nPay"),
          h("Days\nReported"),h("Additional\nPay"),h("Period\nPay"),
          h("Loan/CA"),h("SSS\n(5%)"),h("Pag-IBIG"),h("Phil\nHealth"),h("Total\nDeduct."),
          h("1st\nPeriod"),h("2nd\nPeriod")]

    rows=[hdr1,hdr2]

    # Span setup — will apply via TableStyle
    total_net1=0; total_net2=0
    for i,mr in enumerate(monthly_results,1):
        r1=mr.get("p1",{});r2=mr.get("p2",{})
        basic=float(mr.get("basicMonthlyPay",0) or 0)
        name=mr.get("teacherName","")

        rows.append([
            c(str(i),align="CENTER"),
            c(name,align="LEFT"),
            c(P(basic),bold=True),
            c(f"{r1.get('daysReported',0):.0f}",align="CENTER"),
            c(P(r1.get("substitution",0)) if r1.get("substitution",0) else "\u2014"),
            c(P(r1.get("grossBeforeDeduct",0))),
            c(f"{r2.get('daysReported',0):.0f}",align="CENTER"),
            c(P(r2.get("additionalPay",0)) if r2.get("additionalPay",0) else "\u2014"),
            c(P(r2.get("grossBeforeDeduct",0))),
            c(P(r2.get("salaryLoan",0)) if r2.get("salaryLoan",0) else "\u2014"),
            c(P(r2.get("sss",0))),
            c(P(r2.get("pagIbig",0))),
            c(P(r2.get("philHealth",0))),
            c(P(r2.get("totalDeductions",0)),bold=True),
            c(P(mr.get("totalNet1",0)),bold=True),
            c(P(mr.get("totalNet2",0)),bold=True),
        ])
        total_net1+=mr.get("totalNet1",0)
        total_net2+=mr.get("totalNet2",0)

    # Totals row
    rows.append([
        c(""),c("TOTAL",bold=True,align="LEFT"),c(""),c(""),c(""),c(""),
        c(""),c(""),c(""),c(""),c(""),c(""),c(""),c(""),
        c(P(total_net1),bold=True),
        c(P(total_net2),bold=True),
    ])

    t=Table(rows,colWidths=cws,repeatRows=2)
    n=len(monthly_results)
    ts=TableStyle([
        # All cells
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),7),
        ("GRID",(0,0),(-1,-1),0.3,MGRAY),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(0,0),(-1,1),"CENTER"),
        # Header background
        ("BACKGROUND",(0,0),(-1,1),NAVY),
        # Column group shading
        ("BACKGROUND",(3,2),(5,n+1),colors.HexColor("#F0F9FF")),  # 1st period
        ("BACKGROUND",(6,2),(8,n+1),colors.HexColor("#FFF7ED")),  # 2nd period
        ("BACKGROUND",(9,2),(13,n+1),colors.HexColor("#FEF2F2")), # deductions
        ("BACKGROUND",(14,2),(15,n+1),colors.HexColor("#F0FDF4")),# schedule
        # Totals row
        ("BACKGROUND",(0,n+2),(-1,n+2),LGRAY),
        ("FONTNAME",(0,n+2),(-1,n+2),"Helvetica-Bold"),
        # Header spans row 1
        ("SPAN",(3,0),(5,0)),   # 1st period
        ("SPAN",(6,0),(8,0)),   # 2nd period
        ("SPAN",(9,0),(13,0)),  # deductions
        ("SPAN",(14,0),(15,0)), # schedule
        ("LINEBELOW",(0,1),(-1,1),1,WHITE),
    ])
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1,12))

    # Signatures
    sig=Table([["","",""],["","",""],
               ["__________________________","__________________________","__________________________"],
               ["Prepared by: Payroll Officer","Reviewed by: School Registrar","Approved by: School President"]],
              colWidths=[cw/3-5,cw/3-5,cw/3-5])
    sig.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"Helvetica"),
                              ("FONTSIZE",(0,0),(-1,-1),9),
                              ("ALIGN",(0,0),(-1,-1),"CENTER"),
                              ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(sig)

    doc.build(story,onFirstPage=_page_legal_l,onLaterPages=_page_legal_l)
    return buf.getvalue()


# =============================================================================
#  CERTIFICATE OF EMPLOYMENT
# =============================================================================
def build_coe(teacher: dict) -> bytes:
    """
    Generate Certificate of Employment.
    - Signature lines are blank (no pre-filled names).
    - Date of issuance is auto-generated at time of PDF creation.
    - Purpose: whatever legal purpose it may serve.
    - Photo included if teacher has 'photoB64' field.
    """
    buf=io.BytesIO()
    pw,ph=LETTER
    cw=pw-2*MARGIN
    doc=SimpleDocTemplate(buf,pagesize=LETTER,leftMargin=MARGIN,rightMargin=MARGIN,
                          topMargin=MARGIN+0.42*inch,bottomMargin=MARGIN+0.32*inch)
    story=[]
    today=datetime.date.today()
    name=teacher.get("name","")
    pos=teacher.get("position","")
    etype=teacher.get("employeeType","")
    estatus=teacher.get("employmentStatus","Regular")
    hired=teacher.get("dateHired","")
    basic=float(teacher.get("basicMonthlyPay",0) or 0)
    photo_b64=teacher.get("photoB64","")

    # ── Header with optional photo ────────────────────────────────────────────
    story.append(_logo_hdr(cw))
    story.append(Spacer(1,6))
    story.append(HRFlowable(width="100%",thickness=2,color=NAVY,spaceAfter=4))
    story.append(Paragraph("CERTIFICATE OF EMPLOYMENT",ST["title"]))
    story.append(HRFlowable(width="100%",thickness=1,color=MGRAY,spaceAfter=12))

    # ── Optional 2x2 photo ────────────────────────────────────────────────────
    if photo_b64:
        import base64 as _b64
        try:
            raw=_b64.b64decode(photo_b64)
            img_buf=io.BytesIO(raw)
            photo_img=RLImage(img_buf,width=1.0*inch,height=1.0*inch)
            ph_tbl=Table([[photo_img,""]],colWidths=[1.1*inch,cw-1.1*inch])
            ph_tbl.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                         ("GRID",(0,0),(-1,-1),0,WHITE),
                                         ("LEFTPADDING",(0,0),(-1,-1),0),
                                         ("RIGHTPADDING",(0,0),(-1,-1),0)]))
            story.append(ph_tbl)
            story.append(Spacer(1,4))
        except Exception:
            pass

    story.append(Paragraph("TO WHOM IT MAY CONCERN:",ST["bold"]))
    story.append(Spacer(1,10))
    story.append(Paragraph(
        f"This is to certify that <b>{name}</b> is a <b>{estatus} {etype}</b> employee of "
        f"the <b>{SCHOOL_NAME}</b>, with principal office address at {SCHOOL_ADDRESS}, "
        f"currently holding the position of <b>{pos}</b>.",ST["legal"]))
    story.append(Spacer(1,8))
    if hired:
        story.append(Paragraph(
            f"He/She has been continuously employed in this institution since <b>{hired}</b> and "
            f"is currently receiving a basic monthly salary of <b>{P(basic)}</b> (Philippine Pesos).",ST["legal"]))
    else:
        story.append(Paragraph(
            f"He/She is currently receiving a basic monthly salary of <b>{P(basic)}</b> (Philippine Pesos).",ST["legal"]))
    story.append(Spacer(1,8))
    story.append(Paragraph(
        f"This certification is issued upon the request of the above-named employee "
        f"for whatever legal purpose it may serve.",ST["legal"]))
    story.append(Spacer(1,8))
    day_suffix=lambda d:("th" if 11<=d<=13 else {1:"st",2:"nd",3:"rd"}.get(d%10,"th"))
    d=today.day
    story.append(Paragraph(
        f"Issued this <b>{d}{day_suffix(d)} day of {today.strftime('%B %Y')}</b> at {SCHOOL_CITY}.",ST["legal"]))
    story.append(Spacer(1,28))
    # Blank signature lines
    sig=Table([["",""],["",""],
               ["__________________________","__________________________"],
               ["School Principal","School President"]],
              colWidths=[cw/2-5,cw/2-5])
    sig.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"Helvetica"),
                              ("FONTSIZE",(0,0),(-1,-1),9.5),
                              ("ALIGN",(0,0),(-1,-1),"CENTER"),
                              ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(sig)
    story.append(Spacer(1,16))
    story.append(HRFlowable(width="100%",thickness=0.5,color=MGRAY,spaceAfter=3))
    story.append(Paragraph(f"For verification: {SCHOOL_EMAIL} | {SCHOOL_PHONE}",ST["small"]))
    doc.build(story,onFirstPage=_page_letter,onLaterPages=_page_letter)
    return buf.getvalue()


# =============================================================================
#  APPLICATION FOR LEAVE FORM (matches SEPI official form)
# =============================================================================
def build_leave_form(leave: dict) -> bytes:
    """
    Generate a printable Application for Leave Form.
    leave dict keys: name, date_filed, leave_type, leave_type_other,
                     dates (list of {from, to, days, reason}),
                     sil_month, sil_earned, sil_used, sil_remaining,
                     remarks, approved (bool|None)
    """
    buf=io.BytesIO()
    pw,ph=LETTER
    cw=pw-2*MARGIN
    doc=SimpleDocTemplate(buf,pagesize=LETTER,leftMargin=MARGIN,rightMargin=MARGIN,
                          topMargin=MARGIN+0.42*inch,bottomMargin=MARGIN+0.32*inch)
    story=[]

    # ── Header ────────────────────────────────────────────────────────────────
    # Logo + school details as header table
    school_txt=Paragraph(
        f"<b>SCHOOL OF EVERLASTING PEARL, INC.</b><br/>"
        f"<font size=8>#066 Siruna Village – Phase III, Marcos Highway, Mambugan, Antipolo City 1870</font><br/>"
        f"<font size=7.5>eMail: sepi402954@gmail.com | sepiregistrar@gmail.com</font><br/>"
        f"<font size=7.5>DepEd School ID No.: 402954 | ESC School ID No.: 403694</font><br/>"
        f"<font size=7.5>Government Recognition Nos.: K-042 s.2009 | E-041 s.2012 | 026 s.2011</font>",
        ParagraphStyle("_sh",fontName="Helvetica",fontSize=9,textColor=NAVY,leading=12))
    try:
        logo=RLImage(LOGO_PATH,width=52,height=52)
        ht=Table([[logo,school_txt]],colWidths=[58,cw-58])
    except Exception:
        ht=Table([[school_txt]],colWidths=[cw])
    ht.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("GRID",(0,0),(-1,-1),0,WHITE),
                             ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                             ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    story.append(ht)
    story.append(Spacer(1,4))
    story.append(HRFlowable(width="100%",thickness=2,color=NAVY,spaceAfter=3))
    story.append(Paragraph("APPLICATION FOR LEAVE FORM",
                            ParagraphStyle("_alf",fontName="Helvetica-Bold",fontSize=13,
                                           textColor=NAVY,alignment=TA_CENTER,leading=16)))
    story.append(HRFlowable(width="100%",thickness=1,color=MGRAY,spaceAfter=8))

    # ── Fields 1 & 2 ──────────────────────────────────────────────────────────
    name_val = leave.get("name","") or "_"*36
    date_val = leave.get("date_filed","") or "_"*16

    def lf(label,val,ul=True):
        und = ("_"*len(str(val))*2) if not val else ""
        return Paragraph(f"<b>{label}</b> {val}{und}",
                         ParagraphStyle("_lf",fontName="Helvetica",fontSize=10,
                                        textColor=NAVY,leading=14))

    story.append(lf("1.  Name:", name_val))
    story.append(lf("2.  Date Filed:", date_val))
    story.append(Spacer(1,4))

    # ── Field 3: Leave Type checkboxes ────────────────────────────────────────
    story.append(Paragraph("<b>3.  Leave Type:</b>",
                            ParagraphStyle("_",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY)))
    story.append(Paragraph("(Indicate your leave request by placing an “X” inside the appropriate box below.)",
                            ParagraphStyle("_s",fontName="Helvetica",fontSize=8.5,textColor=DGRAY,leading=11)))
    story.append(Spacer(1,3))

    sel = leave.get("leave_type","")
    LEAVE_TYPES = [
        ("Service Incentive Leave (SIL)",     "earned at 1 day/month, max of 10/SY", "SIL",     True),
        ("Maternity Leave",                    "(RA 11210)",                           "Maternity",False),
        ("Sick Leave",                         "(deducted from SIL credit)",           "Sick",    True),
        ("Solo Parent Leave",                  "(RA 8972)",                            "SoloParent",False),
        ("Personal Leave",                     "(deducted from SIL credit)",           "Personal",True),
        ("VAWC Leave",                         "(RA 9262)",                            "VAWC",    False),
        ("Vacation Leave",                     "(without pay)",                        "Vacation",True),
        ("Magna Carta for Women Leave",        "(RA 9710)",                            "MagnaCartaWomen",False),
        ("Paternity Leave",                    "(RA 8187)",                            "Paternity",True),
        ("Others:",                            leave.get("leave_type_other",""),       "Others",  False),
    ]

    def chk_cell(label,sub,key,left):
        tick = "[X]" if sel==key else "[  ]"
        txt = f"{tick}  <b>{label}</b><br/><font size=7.5 color='#6B7280'>{sub}</font>"
        return Paragraph(txt,ParagraphStyle("_ch",fontName="Helvetica",fontSize=9,textColor=NAVY,leading=12))

    lt_rows=[]
    pairs = list(zip(LEAVE_TYPES[::2], LEAVE_TYPES[1::2]))
    for left_item,right_item in pairs:
        lt_rows.append([chk_cell(*left_item[:3],True),chk_cell(*right_item[:3],False)])
    lt=Table(lt_rows,colWidths=[cw/2,cw/2])
    lt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,MGRAY),
                             ("BACKGROUND",(0,0),(-1,-1),LGRAY),
                             ("LEFTPADDING",(0,0),(-1,-1),6),
                             ("TOPPADDING",(0,0),(-1,-1),4),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4),
                             ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(lt)
    story.append(Spacer(1,8))

    # ── Field 4: Leave Details ────────────────────────────────────────────────
    story.append(Paragraph("<b>4.  Leave Details</b>",
                            ParagraphStyle("_",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY)))
    story.append(Spacer(1,3))
    dates = leave.get("dates",[]) or []
    # Ensure at least 2 rows
    while len(dates)<2: dates.append({"from":"","to":"","days":"","reason":""})
    ld_data=[["Inclusive Date(s) of Leave Requested","Total Days Applied","Reason / Remarks"]]
    for row in dates[:3]:
        date_str = f"{row.get('from','')} to {row.get('to','')}" if row.get("from") else ""
        ld_data.append([date_str or "___________________________________",
                        str(row.get("days","")) or "_____",
                        row.get("reason","") or "______________"])
    ld=Table(ld_data,colWidths=[cw*0.5,cw*0.2,cw*0.3])
    ld.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,MGRAY),
                             ("BACKGROUND",(0,0),(-1,0),LGRAY),
                             ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                             ("FONTSIZE",(0,0),(-1,-1),9),
                             ("LEFTPADDING",(0,0),(-1,-1),6),
                             ("TOPPADDING",(0,0),(-1,-1),5),
                             ("BOTTOMPADDING",(0,0),(-1,-1),10),
                             ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story.append(ld)
    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%",thickness=1,color=NAVY,spaceAfter=6))

    # ── Field 5: SIL Credit Tracker ───────────────────────────────────────────
    story.append(Paragraph("<b>5.  SIL Credit Tracker</b> (To be filled by Principal)",
                            ParagraphStyle("_",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY)))
    story.append(Spacer(1,3))
    sil_data=[["Month","SIL Earned","SIL Used","SIL Remaining"],
              [leave.get("sil_month",""),leave.get("sil_earned",""),
               leave.get("sil_used",""),leave.get("sil_remaining","")]]
    sil_t=Table(sil_data,colWidths=[cw*0.25,cw*0.25,cw*0.25,cw*0.25])
    sil_t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,MGRAY),
                                ("BACKGROUND",(0,0),(-1,0),LGRAY),
                                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                                ("FONTSIZE",(0,0),(-1,-1),9),
                                ("LEFTPADDING",(0,0),(-1,-1),6),
                                ("TOPPADDING",(0,0),(-1,-1),10),
                                ("BOTTOMPADDING",(0,0),(-1,-1),10),
                                ("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story.append(sil_t)
    story.append(Spacer(1,8))

    # ── Approval section ──────────────────────────────────────────────────────
    appr_str = "Approved" if leave.get("approved")==True else ("Disapproved" if leave.get("approved")==False else "Approved / Disapproved:")
    remarks = leave.get("remarks","") or ""
    appr_tbl=Table([
        [Paragraph("<b>Approved / Disapproved:</b>",ParagraphStyle("_",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY)),
         Paragraph(f"<b>Remarks/Actions:</b><br/>{remarks}",ParagraphStyle("_",fontName="Helvetica",fontSize=9,textColor=NAVY,leading=13))],
        [Paragraph("<br/><br/>__________________________<br/>Jerald B. Bongalos, MScT, LPT<br/>School Principal",
                   ParagraphStyle("_c",fontName="Helvetica",fontSize=9,textColor=NAVY,alignment=TA_CENTER,leading=13)),""],
    ],colWidths=[cw*0.45,cw*0.55])
    appr_tbl.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,MGRAY),
                                   ("LEFTPADDING",(0,0),(-1,-1),8),
                                   ("TOPPADDING",(0,0),(-1,-1),6),
                                   ("BOTTOMPADDING",(0,0),(-1,-1),6),
                                   ("VALIGN",(0,0),(-1,-1),"TOP"),
                                   ("ROWSPAN",(1,1),(1,1),True),
                                   ("SPAN",(1,0),(1,1))]))
    story.append(appr_tbl)
    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%",thickness=1,color=NAVY,spaceAfter=5))

    # ── Notes box ─────────────────────────────────────────────────────────────
    notes=[
        "1.  Submit this form at least 10 working days in advance unless emergency.",
        "2.  SIL may be used for sick leave, personal time, or emergencies.",
        "3.  Leave under RA (Laws) – Attach supporting documents e.g. Solo Parent ID.",
        "4.  SIL Conversion – upon EOSY / separation from service.",
    ]
    notes_content=[Paragraph("<b>NOTES:</b>",ParagraphStyle("_",fontName="Helvetica-Bold",fontSize=9,textColor=NAVY))]
    for n in notes:
        notes_content.append(Paragraph(n,ParagraphStyle("_n",fontName="Helvetica",fontSize=9,textColor=NAVY,leading=13,leftIndent=8)))
    ntbl=Table([[n] for n in notes_content],colWidths=[cw])
    ntbl.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0,WHITE),
                               ("BOX",(0,0),(-1,-1),0.5,NAVY),
                               ("LEFTPADDING",(0,0),(-1,-1),8),
                               ("TOPPADDING",(0,0),(-1,-1),3),
                               ("BOTTOMPADDING",(0,0),(-1,-1),3),
                               ("BACKGROUND",(0,0),(-1,-1),LGRAY)]))
    story.append(ntbl)
    story.append(Spacer(1,6))
    story.append(Paragraph('"Leading Lifelong Learners"',
                            ParagraphStyle("_motto",fontName="Helvetica-Oblique",fontSize=9,
                                           textColor=DGRAY,alignment=TA_CENTER)))

    doc.build(story,onFirstPage=_page_letter,onLaterPages=_page_letter)
    return buf.getvalue()
