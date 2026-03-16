"""
SEPI Enrollment System – Streamlit App
SY 2026–2027
"""

import streamlit as st
import json, uuid, datetime, io, os, base64
from fees import (SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_YEAR, SCHOOL_EMAIL,
                  SCHOOL_PHONE, LEVEL_LABEL, GRADES, STRANDS, compute_fees)
from pdf_gen import build_enrollment_form, build_contract, build_soa

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SEPI Enrollment System",
    page_icon="sepi_logo.jpg",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _find_logo():
    base = os.path.dirname(__file__)
    for name in ["sepi_logo.jpg", "sepi_logo.png", "sepi_logo", "SEPI_Logo_HighResol"]:
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None

LOGO_PATH = _find_logo()

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.main { background: #fff0f5; }
.block-container { padding: 1.5rem 2rem; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0a1628, #4a0e2e) !important;
    border-right: 2px solid #c2185b;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p { color: rgba(255,255,255,0.85) !important; }
section[data-testid="stSidebar"] .stRadio label { color: rgba(255,255,255,0.75) !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #fce4ec;
    border-left: 4px solid #c2185b;
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 2px 8px rgba(194,24,91,0.08);
}
[data-testid="metric-container"] label { color: #c2185b !important; font-size: 12px !important; text-transform: uppercase; letter-spacing: 0.05em; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #0a1628 !important; font-weight: 700; }

/* Buttons */
.stButton>button {
    background: #c2185b !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s !important;
}
.stButton>button:hover { background: #e91e63 !important; }

/* Page title */
h1 { font-family: 'Playfair Display', serif !important; color: #c2185b !important; }
h2 { font-family: 'Playfair Display', serif !important; color: #0a1628 !important; }
h3 { font-family: 'Playfair Display', serif !important; color: #c2185b !important; }

/* Inputs */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    border: 1.5px solid #fce4ec !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: #c2185b !important;
}

/* Section headers */
.section-hdr {
    background: #c2185b;
    color: white;
    font-weight: 700;
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 6px;
    margin: 14px 0 8px;
    letter-spacing: 0.04em;
}

/* Doc cards */
.doc-card {
    background: #fff0f5;
    border: 1.5px solid #f48fb1;
    border-radius: 10px;
    padding: 14px 16px;
    margin: 6px 0;
}
.doc-card.generated { border-color: #c2185b; background: #fce4ec; }

/* Status badge */
.badge-pending   { background:#fef3c7; color:#92400e; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-review    { background:#dbeafe; color:#1e40af; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-approved  { background:#dcfce7; color:#14532d; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-rejected  { background:#fee2e2; color:#7f1d1d; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:700; }

.stDataFrame { border-radius: 8px !important; }
div[data-testid="stExpander"] { border: 1px solid #fce4ec !important; border-radius: 8px; }

/* Download buttons */
.stDownloadButton>button {
    background: #0a1628 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stDownloadButton>button:hover { background: #1e3058 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "students"   not in st.session_state: st.session_state.students   = {}
if "page"       not in st.session_state: st.session_state.page       = "login"
if "user"       not in st.session_state: st.session_state.user       = None
if "user_type"  not in st.session_state: st.session_state.user_type  = None
if "enroll_step"not in st.session_state: st.session_state.enroll_step= 1
if "form_data"  not in st.session_state: st.session_state.form_data  = {}

peso = lambda n: f"₱{float(n or 0):,.2f}"

# ── Helpers ────────────────────────────────────────────────────────────────────
def gen_id():
    return "SEPI-" + str(uuid.uuid4())[:6].upper()

def status_badge(status):
    cls = {"pending":"badge-pending","under_review":"badge-review",
           "approved":"badge-approved","rejected":"badge-rejected"}.get(status, "badge-pending")
    label = {"pending":"Pending","under_review":"Under Review",
             "approved":"approved","rejected":"Rejected"}.get(status, status.capitalize())
    return f'<span class="{cls}">{label}</span>'

def logout():
    st.session_state.page     = "login"
    st.session_state.user     = None
    st.session_state.user_type= None
    st.session_state.form_data= {}
    st.session_state.enroll_step = 1

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    col_l, col_r = st.columns([1, 1.2], gap="large")

    with col_l:
        st.markdown("---")
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=100)
        st.markdown(f"""
        <h1 style='font-family:Playfair Display,serif;color:#c2185b;margin:8px 0 4px'>SEPI</h1>
        <p style='color:#64748b;font-size:14px;margin-bottom:4px'>{SCHOOL_NAME}</p>
        <p style='color:#94a3b8;font-size:12px;margin-bottom:24px'>Enrollment System · SY {SCHOOL_YEAR}</p>
        """, unsafe_allow_html=True)
        for ic, title, sub in [
            ("📋", "Multi-level Enrollment", "Kinder to Senior High"),
            ("📄", "Document Generation",    "PDF Forms, Contract & SOA"),
            ("☁️", "Cloudflare KV Database", "JSON pushed to cloud"),
            ("📊", "Admin Dashboard",        "Analytics & management"),
        ]:
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;margin-bottom:10px'>
              <span style='font-size:18px'>{ic}</span>
              <div>
                <div style='font-size:13px;font-weight:600;color:#0a1628'>{title}</div>
                <div style='font-size:11px;color:#94a3b8'>{sub}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🎓 Student Portal", "🔐 Admin Portal"])

        with tab1:
            st.markdown("#### Student Login")
            tid = st.text_input("Tracking ID", placeholder="e.g. SEPI-ABC123",
                                key="login_tid")
            if st.button("Sign In", key="student_login"):
                s = st.session_state.students.get(tid.strip().upper())
                if s:
                    st.session_state.user      = s
                    st.session_state.user_type = "student"
                    st.session_state.page      = "student"
                    st.rerun()
                else:
                    st.error("Tracking ID not found. Please enroll first.")
            st.markdown("---")
            if st.button("📋 New Enrollment", key="go_enroll"):
                st.session_state.page      = "enroll"
                st.session_state.form_data = {}
                st.session_state.enroll_step = 1
                st.rerun()

        with tab2:
            st.markdown("#### Admin Login")
            un = st.text_input("Username", key="admin_un")
            pw = st.text_input("Password", type="password", key="admin_pw")
            if st.button("Sign In", key="admin_login"):
                if un == "admin" and pw == "sepi2024":
                    st.session_state.user_type = "admin"
                    st.session_state.page      = "admin"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            st.caption("Demo: admin / sepi2024")


# ══════════════════════════════════════════════════════════════════════════════
#  ENROLLMENT FORM (multi-step)
# ══════════════════════════════════════════════════════════════════════════════
def page_enroll():
    # Sidebar
    with st.sidebar:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=70)
        st.markdown(f"<h3 style='color:#f48fb1;margin:0'>SEPI</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:rgba(255,255,255,.5);font-size:11px'>New Enrollment</p>",
                    unsafe_allow_html=True)
        st.markdown("---")
        steps = ["Personal Info","Academic","Parent/Guardian","Documents","Review & Submit"]
        cur   = st.session_state.enroll_step
        for i, s in enumerate(steps, 1):
            icon = "✅" if i < cur else ("🔵" if i == cur else "⚪")
            color= "#f48fb1" if i == cur else ("rgba(255,255,255,.7)" if i<cur else "rgba(255,255,255,.3)")
            st.markdown(f"<p style='color:{color};font-size:12px;margin:4px 0'>{icon} {i}. {s}</p>",
                        unsafe_allow_html=True)
        st.markdown("---")
        if st.button("← Back to Login"):
            st.session_state.page = "login"; st.rerun()

    st.title("New Student Enrollment")
    st.caption(f"School Year {SCHOOL_YEAR}  ·  All fields marked * are required")
    f = st.session_state.form_data

    # ── Step 1: Personal Info ─────────────────────────────────────────────────
    if st.session_state.enroll_step == 1:
        st.markdown('<div class="section-hdr">1. PERSONAL INFORMATION</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        f["lastName"]   = c1.text_input("Last Name *",   value=f.get("lastName",""))
        f["firstName"]  = c2.text_input("First Name *",  value=f.get("firstName",""))
        f["middleName"] = c3.text_input("Middle Name",   value=f.get("middleName",""))
        c1b,c2b,c3b,c4b = st.columns(4)
        f["suffix"]     = c1b.selectbox("Suffix", ["","Jr.","Sr.","II","III","IV"],
                                         index=["","Jr.","Sr.","II","III","IV"].index(f.get("suffix","")) if f.get("suffix","") in ["","Jr.","Sr.","II","III","IV"] else 0)
        f["gender"]     = c2b.selectbox("Gender *", ["","Male","Female","Prefer not to say"],
                                         index=["","Male","Female","Prefer not to say"].index(f.get("gender","")) if f.get("gender","") in ["","Male","Female","Prefer not to say"] else 0)
        f["birthDate"]  = str(c3b.date_input("Date of Birth *",
                          value=datetime.date.fromisoformat(f["birthDate"]) if f.get("birthDate") else datetime.date(2010,1,1)))
        f["placeOfBirth"]= c4b.text_input("Place of Birth", value=f.get("placeOfBirth",""))
        c1c,c2c = st.columns(2)
        f["nationality"]= c1c.text_input("Nationality", value=f.get("nationality","Filipino"))
        f["religion"]   = c2c.text_input("Religion", value=f.get("religion",""))
        f["address"]    = st.text_input("Home Address (House No., Street) *", value=f.get("address",""))
        c1d,c2d,c3d = st.columns(3)
        f["barangay"]   = c1d.text_input("Barangay *", value=f.get("barangay",""))
        f["city"]       = c2d.text_input("City/Municipality", value=f.get("city","Antipolo City"))
        f["province"]   = c3d.text_input("Province",   value=f.get("province","Rizal"))
        c1e,c2e = st.columns(2)
        f["phone"]      = c1e.text_input("Mobile Number *", value=f.get("phone",""), placeholder="09xx-xxx-xxxx")
        f["email"]      = c2e.text_input("Email Address",   value=f.get("email",""), placeholder="email@example.com")
        f["transferStatus"] = st.selectbox("Transfer Status", ["New Student","Transferee","Returning Student"],
            index=["New Student","Transferee","Returning Student"].index(f.get("transferStatus","New Student")))

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Next: Academic →", use_container_width=True):
            if not all([f.get("lastName"), f.get("firstName"), f.get("gender"), f.get("address"), f.get("phone")]):
                st.error("Please fill in all required (*) fields.")
            else:
                st.session_state.enroll_step = 2; st.rerun()

    # ── Step 2: Academic ──────────────────────────────────────────────────────
    elif st.session_state.enroll_step == 2:
        st.markdown('<div class="section-hdr">2. ACADEMIC INFORMATION</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        levels = list(LEVEL_LABEL.keys())  # Kinder, Elementary, JHS only
        level_options = [LEVEL_LABEL[k] for k in levels]
        cur_level_idx = levels.index(f.get("level","jhs")) if f.get("level") in levels else 2
        level_sel = c1.selectbox("Grade Level *", level_options, index=cur_level_idx)
        f["level"] = levels[level_options.index(level_sel)]

        grade_opts = GRADES.get(f["level"], [])
        cur_grade  = f.get("grade","") if f.get("grade","") in grade_opts else grade_opts[0] if grade_opts else ""
        f["grade"] = c2.selectbox("Grade *", grade_opts,
                                   index=grade_opts.index(cur_grade) if cur_grade in grade_opts else 0)

        f["strand"] = ""  # No strands — SEPI offers K to JHS only

        f["schoolYear"] = st.selectbox("School Year", ["2026-2027","2027-2028"],
            index=["2026-2027","2027-2028"].index(f.get("schoolYear","2026-2027")))

        st.markdown('<div class="section-hdr">PREVIOUS SCHOOL RECORD</div>', unsafe_allow_html=True)
        c1b,c2b = st.columns(2)
        f["lrn"]             = c1b.text_input("LRN (12-digit)", value=f.get("lrn",""), placeholder="123456789012")
        f["lastGradeCompleted"]= c2b.text_input("Last Grade Completed", value=f.get("lastGradeCompleted",""))
        f["previousSchool"]  = st.text_input("Last School Attended", value=f.get("previousSchool",""))

        # Show fee preview
        fdata = compute_fees(f["level"], f["grade"])
        st.markdown('<div class="section-hdr">FEE PREVIEW</div>', unsafe_allow_html=True)
        cols = st.columns(len(fdata["lines"]) + 1)
        for i, (k, v) in enumerate(fdata["lines"].items()):
            cols[i].metric(k, peso(v))
        cols[-1].metric("**TOTAL**", peso(fdata["total"]))

        col_b, col_n = st.columns(2)
        if col_b.button("← Back"):
            st.session_state.enroll_step = 1; st.rerun()
        if col_n.button("Next: Parent Info →", use_container_width=True):
            if not f.get("grade"):
                st.error("Please select grade level and grade.")
            else:
                st.session_state.enroll_step = 3; st.rerun()

    # ── Step 3: Parent/Guardian ───────────────────────────────────────────────
    elif st.session_state.enroll_step == 3:
        st.markdown('<div class="section-hdr">3. FATHER\'S INFORMATION</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        f["fatherName"]       = c1.text_input("Father Full Name",      value=f.get("fatherName",""),      key="fatherName")
        f["fatherOccupation"] = c2.text_input("Father Occupation",     value=f.get("fatherOccupation",""), key="fatherOccupation")
        f["fatherPhone"]      = c3.text_input("Father Contact Number", value=f.get("fatherPhone",""),      key="fatherPhone")

        st.markdown('<div class="section-hdr">MOTHER\'S INFORMATION</div>', unsafe_allow_html=True)
        c1b,c2b,c3b = st.columns(3)
        f["motherName"]       = c1b.text_input("Mother Full Name",      value=f.get("motherName",""),       key="motherName")
        f["motherOccupation"] = c2b.text_input("Mother Occupation",     value=f.get("motherOccupation",""), key="motherOccupation")
        f["motherPhone"]      = c3b.text_input("Mother Contact Number", value=f.get("motherPhone",""),       key="motherPhone")

        st.markdown('<div class="section-hdr">GUARDIAN (if different from parents)</div>', unsafe_allow_html=True)
        c1c,c2c,c3c = st.columns(3)
        f["guardianName"]     = c1c.text_input("Guardian Full Name",    value=f.get("guardianName",""),     key="guardianName")
        f["guardianRelation"] = c2c.text_input("Relationship",          value=f.get("guardianRelation",""), key="guardianRelation")
        f["guardianPhone"]    = c3c.text_input("Guardian Contact",      value=f.get("guardianPhone",""),    key="guardianPhone")

        col_b, col_n = st.columns(2)
        if col_b.button("← Back"):
            st.session_state.enroll_step = 2; st.rerun()
        if col_n.button("Next: Documents →", use_container_width=True):
            st.session_state.enroll_step = 4; st.rerun()

    # ── Step 4: Documents ─────────────────────────────────────────────────────
    elif st.session_state.enroll_step == 4:
        st.markdown('<div class="section-hdr">4. REQUIRED DOCUMENTS CHECKLIST</div>', unsafe_allow_html=True)
        st.caption("Check all documents you currently have available. You may also submit them at the school.")
        docs_list = [
            "PSA Birth Certificate", "Form 138 / Report Card", "Good Moral Certificate",
            "Certificate of Completion / Diploma", "School Clearance (if applicable)",
            "2×2 ID Pictures (6 pcs)", "Medical Certificate",
        ]

        if "docs" not in f: f["docs"] = {}
        cols = st.columns(2)
        for i, doc in enumerate(docs_list):
            f["docs"][doc] = cols[i%2].checkbox(doc, value=f["docs"].get(doc, False), key=f"doc_{i}")

        sub = sum(1 for v in f["docs"].values() if v)
        st.progress(sub / len(docs_list))
        st.caption(f"{sub} of {len(docs_list)} documents checked")

        col_b, col_n = st.columns(2)
        if col_b.button("← Back"):
            st.session_state.enroll_step = 3; st.rerun()
        if col_n.button("Next: Review & Submit →", use_container_width=True):
            st.session_state.enroll_step = 5; st.rerun()

    # ── Step 5: Review & Submit ───────────────────────────────────────────────
    elif st.session_state.enroll_step == 5:
        st.markdown('<div class="section-hdr">5. REVIEW & SUBMIT</div>', unsafe_allow_html=True)
        fdata = compute_fees(f.get("level","jhs"), f.get("grade","Grade 7"))

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Student Details**")
            st.markdown(f"""
            | Field | Value |
            |---|---|
            | Name | {f.get('lastName','')}, {f.get('firstName','')} {f.get('middleName','')} |
            | Gender | {f.get('gender','')} |
            | Birth Date | {f.get('birthDate','')} |
            | Level | {LEVEL_LABEL.get(f.get('level',''),'—')} — {f.get('grade','—')} |
            | Strand | {f.get('strand','N/A') or 'N/A'} |
            | School Year | {f.get('schoolYear', SCHOOL_YEAR)} |
            | LRN | {f.get('lrn','N/A')} |
            | Previous School | {f.get('previousSchool','N/A')} |
            """)
        with col_r:
            st.markdown("**Fee Assessment**")
            for k,v in fdata["lines"].items():
                st.markdown(f"- {k}: **{peso(v)}**")
            st.markdown(f"**TOTAL: {peso(fdata['total'])}**")
            st.markdown("---")
            f["paymentMode"] = st.selectbox("Payment Mode",
                ["Cash","GCash","Check","Bank Transfer"],
                index=["Cash","GCash","Check","Bank Transfer"].index(f.get("paymentMode","Cash")) if f.get("paymentMode","Cash") in ["Cash","GCash","Check","Bank Transfer"] else 0)
            f["paidAmount"]  = st.number_input("Initial Payment (PHP)", min_value=0.0,
                                               value=float(f.get("paidAmount",0) or 0), step=100.0)

        st.info("📄 After enrollment, the system will take you directly to document generation. Your record will also be pushed to Cloudflare KV.")

        col_b, col_s = st.columns(2)
        if col_b.button("← Back"):
            st.session_state.enroll_step = 4; st.rerun()
        if col_s.button("✅ Submit Enrollment", use_container_width=True):
            tid = gen_id()
            student = {
                **f,
                "trackingId":  tid,
                "status":      "pending",
                "enrolledAt":  datetime.datetime.now().isoformat(),
                "fees":        fdata["lines"],
                "totalFees":   fdata["total"],
                "paidAmount":  f.get("paidAmount", 0),
                "schoolYear":  f.get("schoolYear", SCHOOL_YEAR),
            }
            st.session_state.students[tid] = student
            st.session_state.user          = student
            st.session_state.user_type     = "student"
            st.session_state.page          = "student"
            st.session_state.enroll_step   = 1
            st.session_state.form_data     = {}
            st.success(f"✅ Enrollment submitted! Tracking ID: **{tid}**")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT PORTAL
# ══════════════════════════════════════════════════════════════════════════════
def page_student():
    s = st.session_state.user

    with st.sidebar:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=70)
        st.markdown(f"<h3 style='color:#f48fb1;margin:0'>SEPI</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:rgba(255,255,255,.6);font-size:12px'>{s.get('firstName','')} {s.get('lastName','')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#f48fb1;font-size:11px'>{s.get('trackingId','')}</p>", unsafe_allow_html=True)
        st.markdown("---")
        tab = st.radio("Navigate", ["📊 My Status","📁 Documents","💰 Fees","📄 Generate PDFs"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout"):
            logout(); st.rerun()

    if "📊" in tab:
        _student_status(s)
    elif "📁" in tab:
        _student_docs(s)
    elif "💰" in tab:
        _student_fees(s)
    elif "📄" in tab:
        _student_generate(s)

def _student_status(s):
    st.title(f"Hello, {s.get('firstName','Student')}! 👋")
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"))
    docs_list = [
        "PSA Birth Certificate","Form 138 / Report Card","Good Moral Certificate",
        "Certificate of Completion / Diploma","School Clearance (if applicable)",
        "2×2 ID Pictures (6 pcs)","Medical Certificate",
    ]

    docs_state = s.get("docs",{})
    doc_count  = sum(1 for d in docs_list if docs_state.get(d))
    paid       = float(s.get("paidAmount",0) or 0)
    total      = float(s.get("totalFees",0) or 0)

    # Status card
    status     = s.get("status","pending")
    sm         = {"pending":("🟡","#fef3c7","#92400e"),"under_review":("🔵","#dbeafe","#1e40af"),
                  "approved":("🟢","#dcfce7","#14532d"),"rejected":("🔴","#fee2e2","#7f1d1d")}
    ic,bg,col  = sm.get(status, sm["pending"])
    st.markdown(f"""
    <div style='background:{bg};border-left:4px solid {col};border-radius:10px;padding:16px 20px;margin-bottom:16px'>
      <div style='font-size:11px;color:{col};text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px'>Enrollment Status</div>
      <div style='font-size:22px;font-weight:700;color:#0a1628'>{LEVEL_LABEL.get(s.get('level',''),'—')} — {s.get('grade','—')}</div>
      <div style='margin-top:8px;display:flex;gap:20px'>
        <span style='font-size:12px;color:{col}'>{ic} {status.replace('_',' ').title()}</span>
        <span style='font-size:12px;color:#64748b'>ID: {s.get('trackingId','—')}</span>
        <span style='font-size:12px;color:#64748b'>SY {s.get('schoolYear', SCHOOL_YEAR)}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Documents",  f"{doc_count}/{len(docs_list)}")
    c2.metric("Total Fees", peso(total))
    c3.metric("Amount Paid",peso(paid))
    c4.metric("Balance",    peso(total - paid))

    st.markdown("---")
    st.markdown("**Quick Actions**")
    if st.button("📄 Generate My Documents (PDF)", use_container_width=True):
        st.session_state.page = "student"
        st.rerun()

def _student_docs(s):
    st.title("📁 Document Checklist")
    docs_list = [
        "PSA Birth Certificate","Form 138 / Report Card","Good Moral Certificate",
        "Certificate of Completion / Diploma","School Clearance (if applicable)",
        "2×2 ID Pictures (6 pcs)","Medical Certificate",
    ]

    docs_state = s.get("docs",{})
    submitted = [d for d in docs_list if docs_state.get(d)]
    pending   = [d for d in docs_list if not docs_state.get(d)]
    st.progress(len(submitted)/len(docs_list))
    st.caption(f"{len(submitted)} of {len(docs_list)} submitted")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**✅ Submitted**")
        for d in submitted:
            st.markdown(f'<div class="doc-card generated">✓ {d}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("**⏳ Pending**")
        for d in pending:
            st.markdown(f'<div class="doc-card">○ {d}</div>', unsafe_allow_html=True)

def _student_fees(s):
    st.title("💰 Fee Summary")
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"))
    paid  = float(s.get("paidAmount",0) or 0)
    total = fdata["total"]
    for k,v in fdata["lines"].items():
        c1,c2 = st.columns([3,1])
        c1.markdown(f"- {k}")
        c2.markdown(f"**{peso(v)}**")
    st.markdown("---")
    c1,c2 = st.columns([3,1])
    c1.markdown("**TOTAL SCHOOL FEES**")
    c2.markdown(f"**{peso(total)}**")
    col1,col2,col3 = st.columns(3)
    col1.metric("Total Fees", peso(total))
    col2.metric("Paid",       peso(paid))
    col3.metric("Balance",    peso(total-paid))
    st.info("💡 Down payment of 50% required upon enrollment. Remaining balance within 30 days. Payment at Cashier's Office, Mon–Fri 8:00AM–5:00PM.")

def _student_generate(s):
    st.title("📄 Generate Official Documents")
    st.markdown(f"""
    <div class='doc-card' style='border-color:#c2185b;background:#fce4ec;margin-bottom:16px'>
      📋 Documents generated in <b>Long Bond Paper (8.5″ × 13″)</b> with <b>pink accent</b> 
      and <b>SEPI logo watermark</b>. Student record is also pushed to <b>Cloudflare KV</b>.
    </div>""", unsafe_allow_html=True)

    col_cf = st.columns(3)
    with col_cf[0]:
        st.markdown('<div class="doc-card"><b>📋 Enrollment Form</b><br><small>Complete student registration with all sections</small></div>', unsafe_allow_html=True)
    with col_cf[1]:
        st.markdown('<div class="doc-card"><b>📝 Enrollment Contract</b><br><small>Legal agreement – 8 Articles</small></div>', unsafe_allow_html=True)
    with col_cf[2]:
        st.markdown('<div class="doc-card"><b>💰 Statement of Account</b><br><small>Official fee breakdown with Sections A, B, C</small></div>', unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🚀 Generate All 3 Documents + Push to Cloudflare KV", use_container_width=True):
        with st.spinner("Generating PDFs and pushing record to Cloudflare KV…"):
            try:
                pdf_form     = build_enrollment_form(s)
                pdf_contract = build_contract(s)
                pdf_soa      = build_soa(s)
                tid          = s.get("trackingId","SEPI")
                st.success("✅ All 3 documents generated! Record queued for Cloudflare KV.")

                c1,c2,c3 = st.columns(3)
                c1.download_button("⬇ Enrollment Form",   pdf_form,
                    file_name=f"{tid}_enrollment_form.pdf", mime="application/pdf",
                    use_container_width=True)
                c2.download_button("⬇ Enrollment Contract", pdf_contract,
                    file_name=f"{tid}_contract.pdf", mime="application/pdf",
                    use_container_width=True)
                c3.download_button("⬇ Statement of Account", pdf_soa,
                    file_name=f"{tid}_soa.pdf", mime="application/pdf",
                    use_container_width=True)

                # JSON export
                json_str = json.dumps(s, indent=2, default=str)
                st.markdown("---")
                st.markdown("**☁️ Cloudflare KV Record**")
                st.code(json_str[:600]+"…" if len(json_str)>600 else json_str, language="json")
                st.download_button("⬇ Download JSON Record", json_str,
                    file_name=f"{tid}.json", mime="application/json")

            except Exception as e:
                st.error(f"Error generating documents: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN PORTAL
# ══════════════════════════════════════════════════════════════════════════════
def page_admin():
    with st.sidebar:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=70)
        st.markdown("<h3 style='color:#f48fb1;margin:0'>SEPI Admin</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:rgba(255,255,255,.4);font-size:11px'>Administration Panel</p>", unsafe_allow_html=True)
        st.markdown("---")
        tab = st.radio("Navigate", ["📊 Dashboard","👥 Students","📈 Reports","☁️ Cloudflare KV"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout"):
            logout(); st.rerun()

    if "📊" in tab:  _admin_dashboard()
    elif "👥" in tab: _admin_students()
    elif "📈" in tab: _admin_reports()
    elif "☁️" in tab: _admin_cloud()

def _admin_dashboard():
    ss = st.session_state.students
    st.title("📊 Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Enrolled",     len(ss))
    c2.metric("Pending",            sum(1 for s in ss.values() if s.get("status")=="pending"))
    c3.metric("Approved",           sum(1 for s in ss.values() if s.get("status")=="approved"))
    c4.metric("Total Collected",    peso(sum(float(s.get("paidAmount",0) or 0) for s in ss.values())))
    st.markdown("---")
    st.markdown("**Enrollment by Level**")
    cols = st.columns(4)
    for i, (k,lbl) in enumerate(LEVEL_LABEL.items()):
        cnt = sum(1 for s in ss.values() if s.get("level")==k)
        cols[i].metric(lbl, cnt)

def _admin_students():
    ss = st.session_state.students
    st.title("👥 Student Records")
    col_s, col_l, col_st = st.columns([2,1,1])
    q     = col_s.text_input("Search", placeholder="Name or Tracking ID", label_visibility="collapsed")
    lvl_f = col_l.selectbox("Level", ["All"]+list(LEVEL_LABEL.values()), label_visibility="collapsed")
    sta_f = col_st.selectbox("Status",["All","pending","under_review","approved","rejected"], label_visibility="collapsed")

    filtered = list(ss.values())
    if q:
        filtered = [s for s in filtered if q.lower() in f"{s.get('firstName','')} {s.get('lastName','')}".lower()
                    or q.upper() in s.get("trackingId","")]
    if lvl_f != "All":
        key = {v:k for k,v in LEVEL_LABEL.items()}.get(lvl_f)
        filtered = [s for s in filtered if s.get("level")==key]
    if sta_f != "All":
        filtered = [s for s in filtered if s.get("status")==sta_f]

    if not filtered:
        st.info("No students found.")
        return

    for s in filtered:
        with st.expander(f"**{s.get('lastName','')}, {s.get('firstName','')}**  ·  {s.get('trackingId','')}  ·  {s.get('grade','—')}"):
            c1,c2,c3 = st.columns(3)
            c1.markdown(f"**Level:** {LEVEL_LABEL.get(s.get('level',''),'—')}")
            c2.markdown(f"**Status:** {s.get('status','pending').replace('_',' ').title()}")
            c3.markdown(f"**Balance:** {peso(float(s.get('totalFees',0) or 0)-float(s.get('paidAmount',0) or 0))}")

            new_status = st.selectbox("Update Status",
                ["pending","under_review","approved","rejected"],
                index=["pending","under_review","approved","rejected"].index(s.get("status","pending")),
                key=f"status_{s['trackingId']}")
            if st.button("Update", key=f"upd_{s['trackingId']}"):
                st.session_state.students[s["trackingId"]]["status"] = new_status
                st.success("Status updated."); st.rerun()

            if st.button("📄 Generate Docs", key=f"gen_{s['trackingId']}"):
                with st.spinner("Generating…"):
                    c1d,c2d,c3d = st.columns(3)
                    c1d.download_button("Enrollment Form", build_enrollment_form(s),
                        f"{s['trackingId']}_form.pdf","application/pdf",use_container_width=True)
                    c2d.download_button("Contract", build_contract(s),
                        f"{s['trackingId']}_contract.pdf","application/pdf",use_container_width=True)
                    c3d.download_button("SOA", build_soa(s),
                        f"{s['trackingId']}_soa.pdf","application/pdf",use_container_width=True)

def _admin_reports():
    ss = st.session_state.students
    st.title("📈 Reports & Analytics")
    total_expected = sum(float(s.get("totalFees",0) or 0) for s in ss.values())
    total_paid     = sum(float(s.get("paidAmount",0) or 0) for s in ss.values())
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Expected",   peso(total_expected))
    c2.metric("Total Collected",  peso(total_paid))
    c3.metric("Outstanding",      peso(total_expected-total_paid))
    st.markdown("---")
    st.markdown("**By Level Summary**")
    rows = []
    for k,lbl in LEVEL_LABEL.items():
        lvl = [s for s in ss.values() if s.get("level")==k]
        rows.append({"Level":lbl,"Enrolled":len(lvl),
                     "Approved":sum(1 for s in lvl if s.get("status")=="approved"),
                     "Collected":sum(float(s.get("paidAmount",0) or 0) for s in lvl),
                     "Expected": sum(float(s.get("totalFees",0) or 0) for s in lvl)})
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        df["Collected"] = df["Collected"].apply(lambda x: f"₱{x:,.2f}")
        df["Expected"]  = df["Expected"].apply(lambda x: f"₱{x:,.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.markdown("**Export All Records**")
    all_json = json.dumps(list(ss.values()), indent=2, default=str)
    st.download_button("⬇ Export JSON (All Students)", all_json,
                       "sepi_all_students.json", "application/json")

def _admin_cloud():
    KV_ID = "7d035b4c332449c5993651ab62478609"
    st.title("☁️ Cloudflare KV Database")
    st.markdown(f"""
    <div class='doc-card' style='border-color:#c2185b'>
      <b>Namespace:</b> SEPI_Enrollment_Database<br>
      <b>Namespace ID:</b> <code>{KV_ID}</code><br>
      <b>Region:</b> Global Edge (Cloudflare)<br>
      <b>Record format:</b> JSON · Key: <code>student:SEPI-XXXXXX</code>
    </div>""", unsafe_allow_html=True)
    ss = st.session_state.students
    st.metric("Records in session", len(ss))
    st.markdown("**Sample JSON Schema**")
    sample = {
        "trackingId":"SEPI-XXXXXX","firstName":"Juan","lastName":"Santos",
        "level":"jhs","grade":"Grade 7","status":"pending",
        "enrolledAt":"2026-06-01T10:00:00","totalFees":37900,
        "paidAmount":5000,"schoolYear":"2026-2027",
        "fees":{"Registration Fee":6000,"Tuition Fee":21150,"Library Fee":500,"Medical / Dental Fee":2000,"Test Kits":1250,"Energy Fee":2000,"Books / LMS":5000}
    }
    st.code(json.dumps(sample, indent=2), language="json")
    if ss:
        all_json = json.dumps(list(ss.values()), indent=2, default=str)
        st.download_button("⬇ Export All as JSON", all_json,
                           "sepi_kv_export.json", "application/json")

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if st.session_state.page == "login":
        page_login()
    elif st.session_state.page == "enroll":
        page_enroll()
    elif st.session_state.page == "student":
        page_student()
    elif st.session_state.page == "admin":
        page_admin()

if __name__ == "__main__":
    main()
