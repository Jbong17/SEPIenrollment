"""
SEPI Enrollment System – Streamlit App
SY 2026–2027
"""

import streamlit as st
import json, uuid, datetime, io, os, base64
from fees import (SCHOOL_NAME, SCHOOL_ADDRESS, SCHOOL_YEAR, SCHOOL_EMAIL,
                  SCHOOL_PHONE, LEVEL_LABEL, GRADES, compute_fees,
                  DISCOUNT_TYPES, DISCOUNT_BY_KEY)
import db as _db
from payroll import (compute_payroll, compute_monthly_payroll, sss_employee,
                      philhealth_employee, pagibig_employee,
                      EMPLOYEE_TYPES, OTHER_DEDUCTION_TYPES,
                      SEPI_INITIAL_STAFF)
from hr_pdf import build_payslip, build_payroll_summary, build_coe, build_leave_form
from pdf_gen import build_enrollment_form, build_contract, build_soa

# HR module functions — loaded from hr.py with safe fallback
try:
    from hr import (
        _hr_headers, _hr_save, _hr_delete_kv, _hr_load_all, _gen_teacher_id,
        _admin_hr, _hr_staff_directory, _hr_process_payroll, _show_monthly_payroll,
        _hr_payroll_history, _hr_documents, page_payroll_portal, _payroll_process_tab,
        _payroll_history_tab, _payroll_staff_tab, _payroll_docs_tab,
        _admin_leave_module
    )
    _HR_MODULE_OK = True
except ImportError:
    _HR_MODULE_OK = False
    def _admin_hr():
        st.error("⚠️ hr.py not found. Please upload hr.py to your GitHub repo.")
    def page_payroll_portal():
        st.error("⚠️ hr.py not found. Please upload hr.py to your GitHub repo.")
    def _admin_leave_module():
        st.error("⚠️ hr.py not found.")

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
if "students"      not in st.session_state: st.session_state.students      = {}
if "admin_password" not in st.session_state:
    # Load from Streamlit secrets if available, else use default
    try:
        st.session_state.admin_password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        st.session_state.admin_password = "sepi2024"
if "otp_code"      not in st.session_state: st.session_state.otp_code      = None
if "otp_expiry"    not in st.session_state: st.session_state.otp_expiry    = None
if "otp_sent_to"   not in st.session_state: st.session_state.otp_sent_to   = None
if "otp_verified"  not in st.session_state: st.session_state.otp_verified  = False
if "pdf_form"    not in st.session_state: st.session_state.pdf_form    = None
if "pdf_contract"not in st.session_state: st.session_state.pdf_contract= None
if "pdf_soa"     not in st.session_state: st.session_state.pdf_soa     = None
if "pdf_tid"     not in st.session_state: st.session_state.pdf_tid     = None
if "soa_update_id" not in st.session_state: st.session_state.soa_update_id = None

# Load student records from Cloudflare KV on first run
_db.db_load_students_into_state()

# HR / Payroll session state — must be initialized BEFORE calling _hr_load_all()
if "teachers"       not in st.session_state: st.session_state.teachers       = {}
if "payroll_runs"   not in st.session_state: st.session_state.payroll_runs   = {}
if "hr_loaded"      not in st.session_state: st.session_state.hr_loaded      = False
if "hr_active_tid"  not in st.session_state: st.session_state.hr_active_tid  = None
if "leave_records"  not in st.session_state: st.session_state.leave_records  = {}
if "leave_loaded"   not in st.session_state: st.session_state.leave_loaded   = False

# Load HR/Payroll records from Cloudflare KV on first run (after session state init)
if _HR_MODULE_OK:
    _hr_load_all()
if "user_type"      not in st.session_state: st.session_state.user_type      = None  # 'admin'|'payroll'|'student'
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
            ("📋", "Multi-level Enrollment", "Kinder to Junior High"),
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
            st.caption("💡 For new enrollment or SOA updates, please contact the school registrar or log in via the Admin Portal.")

        with tab2:
            st.markdown("#### Admin Login")
            un = st.text_input("Username", key="admin_un")
            pw = st.text_input("Password", type="password", key="admin_pw")
            if st.button("Sign In", key="admin_login"):
                payroll_pw = ""
                try: payroll_pw = st.secrets.get("PAYROLL_PASSWORD","payroll2024")
                except Exception: payroll_pw = "payroll2024"
                if un == "admin" and pw == st.session_state.admin_password:
                    st.session_state.user_type = "admin"
                    st.session_state.page      = "admin"
                    st.rerun()
                elif un == "payroll" and pw == payroll_pw:
                    st.session_state.user_type = "payroll"
                    st.session_state.page      = "payroll"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            st.caption("Admin: admin / sepi2024  |  Payroll: payroll / payroll2024")


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
        steps = ["Personal Info","Academic","Parent/Guardian","Documents","Scholarship/Discount","Review & Submit"]
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
        fdata = compute_fees(f["level"], f["grade"], esc_grantee=f.get("escGrantee", False))
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
        if col_n.button("Next: Scholarship/Discount →", use_container_width=True):
            st.session_state.enroll_step = 5; st.rerun()

    # ── Step 5: Review & Submit ───────────────────────────────────────────────
    elif st.session_state.enroll_step == 5:
        st.markdown('<div class="section-hdr">5. SCHOLARSHIP / DISCOUNT</div>', unsafe_allow_html=True)
        st.caption("Only ONE discount may be availed per student. The highest applicable discount will be granted. Discounts apply to Tuition Fee only.")

        # ESC grantee check
        esc_grantee = st.radio(
            "Is the student an ESC (Education Service Contracting) Grantee?",
            ["No", "Yes"],
            index=0 if not f.get("escGrantee") else (1 if f.get("escGrantee") else 0),
            horizontal=True, key="esc_radio"
        )
        f["escGrantee"] = (esc_grantee == "Yes")

        st.markdown("---")
        st.markdown("**Select applicable discount (select None if no discount):**")

        # Build option list — filter ESC-restricted for ESC grantees
        discount_opts = [{"key": "none", "label": "No Discount / Not Applicable", "rate_label": "0%", "description": ""}]
        for d in DISCOUNT_TYPES:
            if f.get("escGrantee") and d["not_for_esc"]:
                continue
            discount_opts.append(d)

        opt_labels = [f"{d['label']}  ({d['rate_label']})" for d in discount_opts]
        cur_key = f.get("discountKey","none")
        cur_idx = next((i for i,d in enumerate(discount_opts) if d["key"]==cur_key), 0)

        sel_idx = st.radio(
            "Discount Type",
            range(len(opt_labels)),
            format_func=lambda i: opt_labels[i],
            index=cur_idx,
            key="discount_radio",
            label_visibility="collapsed"
        )
        sel_disc = discount_opts[sel_idx]
        f["discountKey"] = sel_disc["key"]

        # Show description
        if sel_disc.get("description"):
            st.markdown(f'<div style="background:#fce4ec;border-left:3px solid #c2185b;padding:8px 14px;border-radius:0 8px 8px 0;font-size:12px;color:#333;margin:6px 0"><b>Eligibility:</b> {sel_disc["description"]}</div>', unsafe_allow_html=True)

        # Rate input for variable-rate discounts
        f["discountRate"] = f.get("discountRate", None)
        if sel_disc.get("requires_input") and sel_disc["key"] != "none":
            rate_val = st.slider(
                f"Select discount rate ({sel_disc['rate_min']}% – {sel_disc['rate_max']}%)",
                min_value=sel_disc["rate_min"],
                max_value=sel_disc["rate_max"],
                value=int(f.get("discountRate") or sel_disc["rate_min"]),
                step=5 if sel_disc["rate_max"] - sel_disc["rate_min"] >= 10 else 1,
                key="disc_rate_slider"
            )
            f["discountRate"] = rate_val
        else:
            if sel_disc["key"] != "none":
                f["discountRate"] = sel_disc["rate_min"]
            else:
                f["discountRate"] = 0

        # Document requirement notice
        if sel_disc["key"] != "none":
            st.markdown("---")
            st.info("📎 Supporting documents must be submitted to the Registrar's Office for discount validation. Discount is provisional until documents are verified.")
            st.text_area(
                "Document submitted / Remarks (optional)",
                value=f.get("discountRemarks",""),
                placeholder="e.g. Solo Parent ID No. XXXXXXX submitted on MM/DD/YYYY",
                key="disc_remarks_input",
                height=80
            )
            f["discountRemarks"] = st.session_state.get("disc_remarks_input","")

        # Live fee preview
        if f.get("level") and f.get("grade"):
            fdata_preview = compute_fees(
                f["level"], f["grade"],
                f.get("discountKey"), f.get("discountRate"),
                esc_grantee=f.get("escGrantee", False)
            )
            st.markdown("---")
            st.markdown("**💰 Updated Fee Preview**")
            pc1,pc2,pc3 = st.columns(3)
            tuition_base = fdata_preview["lines"].get("Tuition Fee",0)
            if fdata_preview.get("discount"):
                disc_info = fdata_preview["discount"]
                pc1.metric("Tuition Fee (Original)", f"₱{disc_info['base_tuition']:,.2f}")
                pc2.metric(f"Discount ({disc_info['rate']}%)", f"-₱{disc_info['amount']:,.2f}", delta=f"-{disc_info['rate']}%")
                pc3.metric("Total After Discount", f"₱{fdata_preview['total']:,.2f}")
            else:
                pc1.metric("Tuition Fee", f"₱{tuition_base:,.2f}")
                pc2.metric("Discount", "None")
                pc3.metric("Total", f"₱{fdata_preview['total']:,.2f}")

        col_b5, col_n5 = st.columns(2)
        if col_b5.button("← Back", key="disc_back"):
            st.session_state.enroll_step = 4; st.rerun()
        if col_n5.button("Next: Review & Submit →", key="disc_next", use_container_width=True):
            st.session_state.enroll_step = 6; st.rerun()

    elif st.session_state.enroll_step == 6:
        st.markdown('<div class="section-hdr">6. REVIEW & SUBMIT</div>', unsafe_allow_html=True)
        fdata = compute_fees(f.get("level","jhs"), f.get("grade","Grade 7"),
                             f.get("discountKey"), f.get("discountRate"),
                             esc_grantee=f.get("escGrantee", False))

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
            st.session_state.enroll_step = 5; st.rerun()
        if col_s.button("✅ Submit Enrollment", use_container_width=True):
            tid = gen_id()
            fdata_final = compute_fees(
                f.get("level","jhs"), f.get("grade","Grade 7"),
                f.get("discountKey"), f.get("discountRate"),
                esc_grantee=f.get("escGrantee", False)
            )
            student = {
                **f,
                "trackingId":    tid,
                "status":        "pending",
                "enrolledAt":    datetime.datetime.now().isoformat(),
                "fees":          fdata_final["lines"],
                "totalFees":     fdata_final["total"],
                "discountInfo":  fdata_final.get("discount"),
                "discountAmount":fdata_final.get("discount_amount",0),
                "paidAmount":    f.get("paidAmount", 0),
                "schoolYear":    f.get("schoolYear", SCHOOL_YEAR),
            }
            _db.db_save(student)
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
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"),
                         esc_grantee=s.get("escGrantee", False))
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
      <div style='font-size:22px;font-weight:700;color:#1a1a2e'>{LEVEL_LABEL.get(s.get('level',''),'—')} — {s.get('grade','—')}</div>
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
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**✅ Submitted**")
        for d in submitted:
            st.markdown(
                f'<div style="background:#fce4ec;border:1.5px solid #c2185b;border-radius:10px;padding:10px 14px;margin:5px 0;color:#7b003a;font-size:13px;font-weight:600"><span style="color:#c2185b">✓</span> &nbsp;{d}</div>',
                unsafe_allow_html=True)
    with c2:
        st.markdown("**⏳ Pending**")
        for d in pending:
            st.markdown(
                f'<div style="background:#f8f9fa;border:1.5px solid #e2e8f0;border-radius:10px;padding:10px 14px;margin:5px 0;color:#4a5568;font-size:13px"><span style="color:#94a3b8">○</span> &nbsp;{d}</div>',
                unsafe_allow_html=True)

def _student_fees(s):
    st.title("💰 Fee Summary")
    fdata = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"),
                         esc_grantee=s.get("escGrantee", False))
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
    <div class='doc-card' style='border-color:#c2185b;background:#fce4ec;margin-bottom:16px;color:#1a1a2e'>
      <span style='color:#c2185b'>📋</span> <span style='color:#333'>Documents generated in <b>Long Bond Paper (8.5″ × 13″)</b> with <b>pink accent</b>
      and <b>SEPI logo watermark</b>. Student record also saved as JSON for Cloudflare KV.</span>
    </div>""", unsafe_allow_html=True)

    col_cf = st.columns(3)
    with col_cf[0]:
        st.markdown('<div class="doc-card"><b style="color:#c2185b">📋 Enrollment Form</b><br><small style="color:#333">Complete student registration with all sections</small></div>', unsafe_allow_html=True)
    with col_cf[1]:
        st.markdown('<div class="doc-card"><b style="color:#c2185b">📝 Enrollment Contract</b><br><small style="color:#333">Legal agreement – 8 Articles</small></div>', unsafe_allow_html=True)
    with col_cf[2]:
        st.markdown('<div class="doc-card"><b style="color:#c2185b">💰 Statement of Account</b><br><small style="color:#333">Official fee breakdown with Sections A, B, C</small></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Generate button — stores PDFs in session state so download buttons persist
    if st.button("🚀 Generate All 3 Documents", use_container_width=True,
                 key="btn_generate_docs"):
        with st.spinner("Generating PDFs…"):
            try:
                st.session_state.pdf_form     = build_enrollment_form(s)
                st.session_state.pdf_contract = build_contract(s)
                st.session_state.pdf_soa      = build_soa(s)
                st.session_state.pdf_tid      = s.get("trackingId", "SEPI")
                st.rerun()
            except Exception as e:
                st.error(f"Error generating documents: {e}")

    # Download buttons shown from session state — persist across reruns
    tid = st.session_state.get("pdf_tid")
    if tid and tid == s.get("trackingId") and st.session_state.get("pdf_form"):
        st.success("✅ All 3 documents ready — click below to download each one.")
        c1, c2, c3 = st.columns(3)
        c1.download_button(
            label="⬇ Enrollment Form",
            data=st.session_state.pdf_form,
            file_name=f"{tid}_enrollment_form.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_form_{tid}"
        )
        c2.download_button(
            label="⬇ Enrollment Contract",
            data=st.session_state.pdf_contract,
            file_name=f"{tid}_contract.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_contract_{tid}"
        )
        c3.download_button(
            label="⬇ Statement of Account",
            data=st.session_state.pdf_soa,
            file_name=f"{tid}_soa.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_soa_{tid}"
        )
        # JSON record
        st.markdown("---")
        st.markdown("**☁️ JSON Record (for Cloudflare KV)**")
        json_str = json.dumps(s, indent=2, default=str)
        st.code(json_str[:600] + ("…" if len(json_str) > 600 else ""), language="json")
        st.download_button(
            label="⬇ Download JSON Record",
            data=json_str,
            file_name=f"{tid}.json",
            mime="application/json",
            key=f"dl_json_{tid}"
        )


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
        tab = st.radio("Navigate", ["📊 Dashboard","👥 Students","🗂️ Inventory","📈 Reports","👨‍🏫 HR & Payroll","☁️ Cloudflare KV","⚙️ Settings"], label_visibility="collapsed")
        st.markdown("---")
        st.markdown("<p style='color:rgba(255,255,255,.5);font-size:11px;text-transform:uppercase;letter-spacing:.06em'>Quick Actions</p>", unsafe_allow_html=True)
        if st.button("📋 New Enrollment", key="admin_go_enroll", use_container_width=True):
            st.session_state.page = "enroll"
            st.session_state.form_data = {}
            st.session_state.enroll_step = 1
            st.session_state.pop("discount_preview", None)
            st.rerun()
        if st.button("💳 Update SOA / Payment", key="admin_go_soa", use_container_width=True):
            st.session_state.page = "soa_update"
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout"):
            logout(); st.rerun()

    if "📊" in tab:  _admin_dashboard()
    elif "👥" in tab: _admin_students()
    elif "🗂️" in tab: _admin_inventory()
    elif "📈" in tab: _admin_reports()
    elif "👨" in tab: _admin_hr()
    elif "☁️" in tab: _admin_cloud()
    elif "⚙️" in tab: _admin_settings()

def _admin_dashboard():
    ss = st.session_state.students
    st.title("📊 Dashboard")
    # Database connection status
    if _db.is_configured():
        st.success("☁️ **Cloudflare KV connected** — all records are persisted. Data survives hibernation.")
    else:
        st.warning("⚠️ **Cloudflare KV not configured** — records are in-memory only and will be lost on hibernation. "
                   "Add `CF_API_TOKEN` and `CF_ACCOUNT_ID` to Streamlit Secrets to enable persistence.")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Enrolled",     len(ss))
    c2.metric("Pending",            sum(1 for s in ss.values() if s.get("status")=="pending"))
    c3.metric("Approved",           sum(1 for s in ss.values() if s.get("status")=="approved"))
    c4.metric("Total Collected",    peso(sum(float(s.get("paidAmount",0) or 0) for s in ss.values())))
    st.markdown("---")
    st.markdown("**Enrollment by Level**")
    cols = st.columns(3)
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

    # ── Bulk Delete (filtered records only) ───────────────────────────────────
    if len(filtered) > 0:
        with st.expander(f"🗑️ Bulk Delete ({len(filtered)} filtered records)", expanded=False):
            st.markdown(
                f'<div style="background:#fee2e2;border:1px solid #f87171;border-radius:8px;'
                f'padding:10px 14px;font-size:12px;color:#7f1d1d">'
                f'⚠️ This will permanently delete all <b>{len(filtered)}</b> currently filtered student records '
                f'from both the app and Cloudflare KV. Use the filters above to target specific records '
                f'(e.g. search "SEPI-SAMPLE" to delete only test entries).</div>',
                unsafe_allow_html=True
            )
            bulk_confirm = st.checkbox(
                f"I confirm I want to delete {len(filtered)} records permanently",
                key="bulk_del_confirm"
            )
            if st.button("🗑️ Delete All Filtered Records",
                         key="bulk_del_btn",
                         disabled=not bulk_confirm,
                         use_container_width=True):
                deleted = 0
                for s in filtered:
                    tid = s["trackingId"]
                    if _db.is_configured():
                        _db.delete_student(tid)
                    if tid in st.session_state.students:
                        del st.session_state.students[tid]
                    deleted += 1
                st.session_state.pop("bulk_del_confirm", None)
                st.success(f"✅ {deleted} records deleted successfully.")
                st.rerun()
    st.markdown("---")

    for s in filtered:
        tid    = s["trackingId"]
        total  = float(s.get("totalFees",0) or 0)
        paid   = float(s.get("paidAmount",0) or 0)
        bal    = total - paid
        status = s.get("status","pending")
        status_icons = {"pending":"🟡","under_review":"🔵","approved":"🟢","rejected":"🔴"}
        ic = status_icons.get(status,"🟡")

        with st.expander(
            f"{ic} **{s.get('lastName','')}, {s.get('firstName','')}** "
            f"·  {tid}  ·  {s.get('grade','—')}  "
            f"·  Balance: {peso(bal)}"
        ):
            # ── Student Summary ───────────────────────────────────────────────
            sc1,sc2,sc3,sc4 = st.columns(4)
            sc1.metric("Total Fees",   peso(total))
            sc2.metric("Amount Paid",  peso(paid))
            sc3.metric("Balance",      peso(bal))
            sc4.metric("Status",       status.replace("_"," ").title())

            inner_tabs = st.tabs(["📊 SOA & Payments", "📋 Student Info", "⚙️ Actions"])

            # ── TAB 1: Inline SOA Viewer ──────────────────────────────────────
            with inner_tabs[0]:
                st.markdown("#### 💰 Statement of Account")
                fdata_view = compute_fees(s.get("level","jhs"), s.get("grade","Grade 7"),
                                          s.get("discountKey"), s.get("discountRate"),
                                          esc_grantee=s.get("escGrantee", False))

                # Fee breakdown table
                import pandas as pd
                fee_rows = []
                disc_info_v = s.get("discountInfo") or fdata_view.get("discount")
                for k, v in fdata_view["lines"].items():
                    if k == "Tuition Fee" and disc_info_v:
                        d_base = disc_info_v.get("base_tuition", v)
                        d_amt  = disc_info_v.get("amount", 0)
                        d_rate = disc_info_v.get("rate", 0)
                        fee_rows.append({"Particular": "Tuition Fee (Gross)", "Amount": f"₱{d_base:,.2f}", "Note": ""})
                        fee_rows.append({"Particular": f"  Discount: {disc_info_v.get('label','')} ({d_rate}%)", "Amount": f"(₱{d_amt:,.2f})", "Note": "Applied"})
                        fee_rows.append({"Particular": "Tuition Fee (Net)", "Amount": f"₱{v:,.2f}", "Note": ""})
                    else:
                        fee_rows.append({"Particular": k, "Amount": f"₱{v:,.2f}", "Note": ""})
                fee_rows.append({"Particular": "TOTAL SCHOOL FEES", "Amount": f"₱{fdata_view['total']:,.2f}", "Note": ""})

                fee_df = pd.DataFrame(fee_rows)
                st.dataframe(fee_df, use_container_width=True, hide_index=True,
                    column_config={
                        "Particular": st.column_config.TextColumn(width="large"),
                        "Amount":     st.column_config.TextColumn(width="medium"),
                        "Note":       st.column_config.TextColumn(width="small"),
                    })

                # Summary row
                ps1, ps2, ps3, ps4 = st.columns(4)
                ps1.metric("Total Assessed",  peso(fdata_view["total"]))
                ps2.metric("Discount Applied",peso(disc_info_v.get("amount",0) if disc_info_v else 0))
                ps3.metric("Total Paid",       peso(paid))
                ps4.metric("Outstanding",      peso(bal),
                           delta=f"-{peso(bal)}" if bal > 0 else "✅ Fully Paid",
                           delta_color="inverse" if bal > 0 else "normal")

                # ── Payment History ───────────────────────────────────────────
                st.markdown("#### 📋 Payment History")
                history = s.get("paymentHistory", [])
                if history:
                    hist_df = pd.DataFrame(history)
                    hist_df.index = range(1, len(hist_df)+1)
                    st.dataframe(hist_df, use_container_width=True,
                        column_config={
                            "Date":    st.column_config.TextColumn(width="small"),
                            "Amount":  st.column_config.TextColumn(width="medium"),
                            "Mode":    st.column_config.TextColumn(width="small"),
                            "OR No.":  st.column_config.TextColumn(width="medium"),
                            "Remarks": st.column_config.TextColumn(width="large"),
                        })
                    # Running balance
                    running = fdata_view["total"]
                    rb_rows = []
                    for h in history:
                        amt_str = str(h.get("Amount","0")).replace("PHP","").replace("₱","").replace(",","").strip()
                        try:
                            amt = float(amt_str)
                        except Exception:
                            amt = 0
                        running -= amt
                        rb_rows.append({"Payment": h.get("Amount",""), "After Payment Balance": f"₱{max(running,0):,.2f}"})
                    st.markdown("**Running Balance**")
                    st.dataframe(pd.DataFrame(rb_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No payments recorded yet.")

                # ── Quick payment entry ───────────────────────────────────────
                st.markdown("#### ➕ Record Payment")
                with st.form(f"quick_pay_{tid}", clear_on_submit=True):
                    qp1, qp2, qp3 = st.columns(3)
                    qp_amt  = qp1.number_input("Amount (PHP)", min_value=1.0,
                                                max_value=float(max(bal,1)),
                                                value=min(1000.0, float(max(bal,1))),
                                                step=100.0, key=f"qpa_{tid}")
                    qp_mode = qp2.selectbox("Mode", ["Cash","GCash","Bank Transfer","Check"],
                                             key=f"qpm_{tid}")
                    qp_date = qp3.date_input("Date", value=datetime.date.today(),
                                              key=f"qpd_{tid}")
                    qp_or   = st.text_input("OR Number", placeholder="Optional", key=f"qpo_{tid}")
                    qp_note = st.text_input("Remarks", placeholder="e.g. June installment",
                                             key=f"qpn_{tid}")
                    qp_save = st.form_submit_button("💾 Save Payment", use_container_width=True)
                    if qp_save:
                        if qp_amt > bal + 0.01:
                            st.error(f"Exceeds balance of {peso(bal)}")
                        else:
                            new_rec = {"Date": str(qp_date), "Amount": f"PHP {qp_amt:,.2f}",
                                       "Mode": qp_mode, "OR No.": qp_or or "—",
                                       "Remarks": qp_note or "—"}
                            s_pay = st.session_state.students[tid]
                            if "paymentHistory" not in s_pay:
                                s_pay["paymentHistory"] = []
                            s_pay["paymentHistory"].append(new_rec)
                            s_pay["paidAmount"] = paid + qp_amt
                            _db.db_save(s_pay)
                            if (st.session_state.get("user") and
                                    st.session_state.user.get("trackingId") == tid):
                                st.session_state.user["paidAmount"] = paid + qp_amt
                            st.success(f"✅ Payment of {peso(qp_amt)} saved!"); st.rerun()

            # ── TAB 2: Student Info ───────────────────────────────────────────
            with inner_tabs[1]:
                si1, si2 = st.columns(2)
                with si1:
                    st.markdown("**Personal**")
                    for lbl, val in [
                        ("Name", f"{s.get('lastName','')}, {s.get('firstName','')} {s.get('middleName','')}"),
                        ("Gender",    (s.get("gender","") or "").capitalize()),
                        ("Birthdate", s.get("birthDate","")),
                        ("Address",   f"{s.get('address','')} {s.get('barangay','')} {s.get('city','')}".strip()),
                        ("Mobile",    s.get("phone","")),
                        ("LRN",       s.get("lrn","") or "—"),
                    ]:
                        st.markdown(f"**{lbl}:** {val or '—'}")
                with si2:
                    st.markdown("**Family**")
                    for lbl, val in [
                        ("Father", s.get("fatherName","")),
                        ("Mother", s.get("motherName","")),
                        ("Guardian", s.get("guardianName","")),
                        ("Prev. School", s.get("previousSchool","")),
                        ("ESC Grantee", "Yes" if s.get("escGrantee") else "No"),
                        ("Discount", (s.get("discountInfo") or {}).get("label","None")),
                    ]:
                        st.markdown(f"**{lbl}:** {val or '—'}")

            # ── TAB 3: Actions ────────────────────────────────────────────────
            with inner_tabs[2]:
                st.markdown("**Update Enrollment Status**")
                new_status = st.selectbox("Status",
                    ["pending","under_review","approved","rejected"],
                    index=["pending","under_review","approved","rejected"].index(s.get("status","pending")),
                    key=f"status_{tid}")
                if st.button("✅ Update Status", key=f"upd_{tid}"):
                    s_updated = {**st.session_state.students[tid], "status": new_status}
                    _db.db_save(s_updated)
                    st.success("Status updated."); st.rerun()

                st.markdown("---")
                st.markdown("**Generate PDF Documents**")
                gen_key = f"admin_pdf_{tid}"
                if st.button("📄 Generate All Docs", key=f"gen_{tid}", use_container_width=True):
                    with st.spinner("Generating…"):
                        try:
                            st.session_state[gen_key] = {
                                "form":     build_enrollment_form(s),
                                "contract": build_contract(s),
                                "soa":      build_soa(s),
                            }
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                if st.session_state.get(gen_key):
                    pdfs = st.session_state[gen_key]
                    c1d, c2d, c3d = st.columns(3)
                    c1d.download_button("⬇ Enrollment Form", pdfs["form"],
                        f"{tid}_form.pdf", "application/pdf",
                        use_container_width=True, key=f"adl_form_{tid}")
                    c2d.download_button("⬇ Contract", pdfs["contract"],
                        f"{tid}_contract.pdf", "application/pdf",
                        use_container_width=True, key=f"adl_contract_{tid}")
                    c3d.download_button("⬇ SOA", pdfs["soa"],
                        f"{tid}_soa.pdf", "application/pdf",
                        use_container_width=True, key=f"adl_soa_{tid}")

                # ── Danger Zone ───────────────────────────────────────────────
                st.markdown("---")
                st.markdown("**🗑️ Delete Student Record**")
                st.markdown(
                    f'<div style="background:#fee2e2;border:1px solid #f87171;border-radius:8px;'
                    f'padding:10px 14px;font-size:12px;color:#7f1d1d;margin-bottom:10px">'
                    f'⚠️ This will permanently delete <b>{s.get("firstName","")} {s.get("lastName","")}</b> '
                    f'({tid}) from both the app and Cloudflare KV. This action cannot be undone.</div>',
                    unsafe_allow_html=True
                )
                # Two-step confirmation to prevent accidental deletion
                confirm_key = f"confirm_del_{tid}"
                if not st.session_state.get(confirm_key):
                    if st.button("🗑️ Delete This Record",
                                 key=f"del_btn_{tid}",
                                 use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.error(f"Are you sure you want to delete **{tid}** — {s.get('firstName','')} {s.get('lastName','')}? This cannot be undone.")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("✅ Yes, Delete Permanently",
                                  key=f"del_confirm_{tid}",
                                  use_container_width=True):
                        # Remove from KV
                        if _db.is_configured():
                            _db.delete_student(tid)
                        # Remove from session state
                        if tid in st.session_state.students:
                            del st.session_state.students[tid]
                        # Clear any cached PDFs for this student
                        for k in [f"admin_pdf_{tid}", f"updated_soa_{tid}", confirm_key]:
                            st.session_state.pop(k, None)
                        st.success(f"✅ Record {tid} deleted successfully.")
                        st.rerun()
                    if cc2.button("❌ Cancel",
                                  key=f"del_cancel_{tid}",
                                  use_container_width=True):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()

def _admin_reports():
    import pandas as pd
    from collections import defaultdict

    ss = st.session_state.students
    st.title("📈 Reports & Analytics")

    if not ss:
        st.info("No enrolled students yet.")
        return

    all_students   = list(ss.values())
    total_expected = sum(float(s.get("totalFees",0) or 0) for s in all_students)
    total_paid     = sum(float(s.get("paidAmount",0) or 0) for s in all_students)
    total_balance  = total_expected - total_paid
    collection_rate = round((total_paid / total_expected * 100), 1) if total_expected > 0 else 0

    # ── Top KPI row ───────────────────────────────────────────────────────────
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Total Students",    len(all_students))
    k2.metric("Total Assessed",    peso(total_expected))
    k3.metric("Total Collected",   peso(total_paid))
    k4.metric("Outstanding",       peso(total_balance))
    k5.metric("Collection Rate",   f"{collection_rate}%",
              delta=f"{collection_rate}% collected",
              delta_color="normal" if collection_rate >= 50 else "inverse")

    st.markdown("---")

    # ── Report tabs ───────────────────────────────────────────────────────────
    r_tabs = st.tabs(["📅 Monthly Collection", "🏫 By Level", "📊 Collection Rate", "📤 Export"])

    # ── TAB 1: Monthly Collection ─────────────────────────────────────────────
    with r_tabs[0]:
        st.markdown("#### Monthly Collection Report")
        st.caption("Based on payment history recorded per student.")

        # Aggregate payments by month from paymentHistory
        monthly = defaultdict(lambda: {"collected": 0.0, "transactions": 0})
        for s in all_students:
            for ph in s.get("paymentHistory", []):
                try:
                    date_str = ph.get("Date","")
                    if not date_str: continue
                    ym = date_str[:7]  # "YYYY-MM"
                    amt_str = str(ph.get("Amount","0")).replace("PHP","").replace("₱","").replace(",","").strip()
                    amt = float(amt_str)
                    monthly[ym]["collected"] += amt
                    monthly[ym]["transactions"] += 1
                except Exception:
                    pass

        # Also count initial payments from paidAmount on enrollment date
        enrollment_by_month = defaultdict(float)
        for s in all_students:
            enrolled_at = s.get("enrolledAt","")
            if enrolled_at and len(enrolled_at) >= 7:
                ym = enrolled_at[:7]
                init_paid = float(s.get("paidAmount",0) or 0)
                # Only add if no payment history (avoid double counting)
                if not s.get("paymentHistory") and init_paid > 0:
                    monthly[ym]["collected"] += init_paid
                    monthly[ym]["transactions"] += 1

        if monthly:
            months_sorted = sorted(monthly.keys())
            running_total = 0
            month_rows = []
            for ym in months_sorted:
                data = monthly[ym]
                collected = round(data["collected"], 2)
                running_total += collected
                try:
                    yr, mo = ym.split("-")
                    import calendar
                    mo_label = f"{calendar.month_name[int(mo)]} {yr}"
                except Exception:
                    mo_label = ym
                rate_of_total = round(collected / total_expected * 100, 1) if total_expected > 0 else 0
                month_rows.append({
                    "Month":          mo_label,
                    "Collected":      f"PHP {collected:,.2f}",
                    "Transactions":   data["transactions"],
                    "Running Total":  f"PHP {running_total:,.2f}",
                    "% of Total Due": f"{rate_of_total}%",
                })

            df_monthly = pd.DataFrame(month_rows)
            st.dataframe(df_monthly, use_container_width=True, hide_index=True,
                column_config={
                    "Month":          st.column_config.TextColumn(width="medium"),
                    "Collected":      st.column_config.TextColumn(width="medium"),
                    "Transactions":   st.column_config.NumberColumn(width="small"),
                    "Running Total":  st.column_config.TextColumn(width="medium"),
                    "% of Total Due": st.column_config.TextColumn(width="small"),
                })

            # Bar chart — monthly collection
            try:
                chart_data = pd.DataFrame({
                    "Month":     [r["Month"] for r in month_rows],
                    "Collected": [monthly[m]["collected"] for m in months_sorted],
                })
                st.bar_chart(chart_data.set_index("Month"), color="#C2185B")
            except Exception:
                pass

            # Download monthly report
            csv_m = df_monthly.to_csv(index=False)
            st.download_button("⬇ Download Monthly Collection (CSV)", csv_m,
                               "SEPI_Monthly_Collection.csv", "text/csv",
                               key="dl_monthly_csv")
        else:
            st.info("No payment history recorded yet. Payments logged through the SOA Update or Admin → Students → Record Payment will appear here.")

    # ── TAB 2: By Level & Grade ───────────────────────────────────────────────
    with r_tabs[1]:
        st.markdown("#### Collection by Level")
        level_rows = []
        for k, lbl in LEVEL_LABEL.items():
            lvl = [s for s in all_students if s.get("level") == k]
            exp  = sum(float(s.get("totalFees",0) or 0) for s in lvl)
            paid = sum(float(s.get("paidAmount",0) or 0) for s in lvl)
            rate = round(paid / exp * 100, 1) if exp > 0 else 0
            level_rows.append({
                "Level":           lbl,
                "Students":        len(lvl),
                "Approved":        sum(1 for s in lvl if s.get("status")=="approved"),
                "Total Assessed":  f"PHP {exp:,.2f}",
                "Total Collected": f"PHP {paid:,.2f}",
                "Outstanding":     f"PHP {exp-paid:,.2f}",
                "Collection Rate": f"{rate}%",
            })
        st.dataframe(pd.DataFrame(level_rows), use_container_width=True, hide_index=True)

        st.markdown("#### Collection by Grade")
        GRADE_ORDER = {
            "Nursery":0,"Kinder 1":1,"Kinder 2":2,
            "Grade 1":3,"Grade 2":4,"Grade 3":5,"Grade 4":6,"Grade 5":7,"Grade 6":8,
            "Grade 7":9,"Grade 8":10,"Grade 9":11,"Grade 10":12,
        }
        grade_data = defaultdict(lambda:{"students":0,"expected":0,"paid":0})
        for s in all_students:
            g = s.get("grade","—")
            grade_data[g]["students"] += 1
            grade_data[g]["expected"] += float(s.get("totalFees",0) or 0)
            grade_data[g]["paid"]     += float(s.get("paidAmount",0) or 0)

        grade_rows = []
        for g in sorted(grade_data.keys(), key=lambda x: GRADE_ORDER.get(x, 99)):
            d = grade_data[g]
            rate = round(d["paid"] / d["expected"] * 100, 1) if d["expected"] > 0 else 0
            grade_rows.append({
                "Grade":           g,
                "Students":        d["students"],
                "Total Assessed":  f"PHP {d['expected']:,.2f}",
                "Total Collected": f"PHP {d['paid']:,.2f}",
                "Outstanding":     f"PHP {d['expected']-d['paid']:,.2f}",
                "Collection Rate": f"{rate}%",
            })
        st.dataframe(pd.DataFrame(grade_rows), use_container_width=True, hide_index=True)

    # ── TAB 3: Collection Rate Analysis ───────────────────────────────────────
    with r_tabs[2]:
        st.markdown("#### Collection Rate Analysis")

        # Overall rate gauge
        col_gauge, col_stats = st.columns([1,1])
        with col_gauge:
            st.markdown(f"""
            <div style="background:{'#dcfce7' if collection_rate>=75 else ('#fef3c7' if collection_rate>=50 else '#fee2e2')};
                        border:2px solid {'#16a34a' if collection_rate>=75 else ('#d97706' if collection_rate>=50 else '#dc2626')};
                        border-radius:16px;padding:24px;text-align:center">
              <div style="font-size:13px;color:#374151;font-weight:600;margin-bottom:8px">
                OVERALL COLLECTION RATE
              </div>
              <div style="font-size:52px;font-weight:800;color:{'#16a34a' if collection_rate>=75 else ('#d97706' if collection_rate>=50 else '#dc2626')}">
                {collection_rate}%
              </div>
              <div style="font-size:11px;color:#6b7280;margin-top:8px">
                PHP {total_paid:,.2f} collected out of PHP {total_expected:,.2f}
              </div>
              <div style="font-size:11px;color:#6b7280;margin-top:4px">
                {'✅ On track' if collection_rate >= 75 else ('⚠️ Needs attention' if collection_rate >= 50 else '🔴 Critical — below 50%')}
              </div>
            </div>""", unsafe_allow_html=True)

        with col_stats:
            st.markdown("**Per-Student Collection Status**")
            fully_paid  = sum(1 for s in all_students
                              if float(s.get("paidAmount",0) or 0) >= float(s.get("totalFees",0) or 0) - 0.01)
            partial     = sum(1 for s in all_students
                              if 0 < float(s.get("paidAmount",0) or 0) < float(s.get("totalFees",0) or 0))
            unpaid      = sum(1 for s in all_students
                              if float(s.get("paidAmount",0) or 0) == 0)
            rs1,rs2,rs3 = st.columns(3)
            rs1.metric("Fully Paid",   fully_paid,  delta=f"{round(fully_paid/len(all_students)*100,1)}%")
            rs2.metric("Partial",      partial,      delta=f"{round(partial/len(all_students)*100,1)}%")
            rs3.metric("Unpaid",       unpaid,       delta=f"{round(unpaid/len(all_students)*100,1)}%",
                       delta_color="inverse" if unpaid > 0 else "normal")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Students with Outstanding Balance**")
            with_balance = [(s.get("lastName",""),
                             s.get("firstName",""),
                             s.get("grade",""),
                             s.get("trackingId",""),
                             float(s.get("totalFees",0) or 0) - float(s.get("paidAmount",0) or 0))
                            for s in all_students
                            if float(s.get("totalFees",0) or 0) - float(s.get("paidAmount",0) or 0) > 0.01]
            with_balance.sort(key=lambda x: -x[4])
            if with_balance:
                bal_df = pd.DataFrame(with_balance,
                    columns=["Last Name","First Name","Grade","Tracking ID","Balance"])
                bal_df["Balance"] = bal_df["Balance"].apply(lambda x: f"PHP {x:,.2f}")
                st.dataframe(bal_df, use_container_width=True, hide_index=True)
            else:
                st.success("All students are fully paid!")

    # ── TAB 4: Export ─────────────────────────────────────────────────────────
    with r_tabs[3]:
        st.markdown("#### Export Records")
        ec1, ec2 = st.columns(2)

        all_json = json.dumps(list(ss.values()), indent=2, default=str)
        ec1.download_button("⬇ Export All Students (JSON)", all_json,
                           "sepi_all_students.json", "application/json",
                           key="exp_reports", use_container_width=True)

        # Full CSV export
        export_rows = []
        for s in all_students:
            exp  = float(s.get("totalFees",0) or 0)
            paid = float(s.get("paidAmount",0) or 0)
            export_rows.append({
                "Tracking ID":    s.get("trackingId",""),
                "Last Name":      s.get("lastName",""),
                "First Name":     s.get("firstName",""),
                "Level":          LEVEL_LABEL.get(s.get("level",""),"—"),
                "Grade":          s.get("grade",""),
                "Status":         s.get("status",""),
                "Total Fees":     exp,
                "Amount Paid":    paid,
                "Balance":        exp - paid,
                "Collection Rate":f"{round(paid/exp*100,1) if exp else 0}%",
                "Enrolled On":    s.get("enrolledAt","")[:10],
                "School Year":    s.get("schoolYear",""),
            })
        csv_all = pd.DataFrame(export_rows).to_csv(index=False)
        ec2.download_button("⬇ Export All Students (CSV)", csv_all,
                           "sepi_all_students.csv", "text/csv",
                           key="exp_reports_csv", use_container_width=True)

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
                           "sepi_kv_export.json", "application/json", key="exp_kv")




# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT INVENTORY PER GRADE LEVEL
# ══════════════════════════════════════════════════════════════════════════════
def _admin_inventory():
    import pandas as pd
    import io as _io

    ss   = st.session_state.students
    sy   = SCHOOL_YEAR

    st.title("🗂️ Student Inventory")
    st.caption(f"School Year {sy}  ·  Complete student roster organized by grade level")

    if not ss:
        st.info("No enrolled students yet.")
        return

    # ── Build master list ─────────────────────────────────────────────────────
    all_students = list(ss.values())

    STATUS_COLOR = {
        "pending":      ("🟡", "#fef3c7", "#92400e"),
        "under_review": ("🔵", "#dbeafe", "#1e40af"),
        "approved":     ("🟢", "#dcfce7", "#14532d"),
        "rejected":     ("🔴", "#fee2e2", "#7f1d1d"),
    }

    LEVEL_ORDER = ["preschool","elementary","jhs"]
    LEVEL_LABEL_MAP = {
        "preschool":  "Kinder / Preschool",
        "elementary": "Elementary",
        "jhs":        "Junior High School",
    }
    GRADE_ORDER = {
        "Nursery":0,"Kinder 1":1,"Kinder 2":2,
        "Grade 1":3,"Grade 2":4,"Grade 3":5,"Grade 4":6,"Grade 5":7,"Grade 6":8,
        "Grade 7":9,"Grade 8":10,"Grade 9":11,"Grade 10":12,
    }

    # ── Summary stat row ──────────────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Students", len(all_students))
    c2.metric("Kinder/Preschool", sum(1 for s in all_students if s.get("level")=="preschool"))
    c3.metric("Elementary",       sum(1 for s in all_students if s.get("level")=="elementary"))
    c4.metric("Junior High",      sum(1 for s in all_students if s.get("level")=="jhs"))
    approved = sum(1 for s in all_students if s.get("status")=="approved")
    c5.metric("Approved", f"{approved}/{len(all_students)}")

    st.markdown("---")

    # ── Filters row ───────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([2,1,1,1])
    search_q  = fc1.text_input("Search student", placeholder="Name or Tracking ID…",
                                label_visibility="collapsed", key="inv_search")
    filt_stat = fc2.selectbox("Status", ["All","pending","under_review","approved","rejected"],
                               label_visibility="collapsed", key="inv_status")
    filt_sy   = fc3.selectbox("School Year", ["All", sy],
                               label_visibility="collapsed", key="inv_sy")
    export_fmt= fc4.selectbox("Export as", ["Excel (.xlsx)","CSV (.csv)"],
                               label_visibility="collapsed", key="inv_export_fmt")

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = all_students[:]
    if search_q:
        q = search_q.lower()
        filtered = [s for s in filtered if
                    q in f"{s.get('firstName','')} {s.get('lastName','')}".lower()
                    or q in s.get("trackingId","").lower()
                    or q in s.get("grade","").lower()]
    if filt_stat != "All":
        filtered = [s for s in filtered if s.get("status")==filt_stat]
    if filt_sy != "All":
        filtered = [s for s in filtered if s.get("schoolYear")==filt_sy]

    # ── Build master DataFrame for export ─────────────────────────────────────
    def _to_row(s):
        paid = float(s.get("paidAmount",0) or 0)
        total= float(s.get("totalFees",0) or 0)
        docs_list = [
            "PSA Birth Certificate","Form 138 / Report Card","Good Moral Certificate",
            "Certificate of Completion / Diploma","School Clearance (if applicable)",
            "2x2 ID Pictures (6 pcs)","Medical Certificate",
        ]
        docs_state = s.get("docs",{})
        docs_submitted = sum(1 for d in docs_list if docs_state.get(d))
        return {
            "Tracking ID":        s.get("trackingId",""),
            "Last Name":          s.get("lastName",""),
            "First Name":         s.get("firstName",""),
            "Middle Name":        s.get("middleName",""),
            "Gender":             (s.get("gender","") or "").capitalize(),
            "Date of Birth":      s.get("birthDate",""),
            "Level":              LEVEL_LABEL_MAP.get(s.get("level",""),"—"),
            "Grade":              s.get("grade",""),
            "School Year":        s.get("schoolYear",""),
            "LRN":                s.get("lrn",""),
            "Transfer Status":    s.get("transferStatus",""),
            "Enrollment Status":  (s.get("status","") or "").replace("_"," ").title(),
            "Mobile":             s.get("phone",""),
            "Email":              s.get("email",""),
            "Father Name":        s.get("fatherName",""),
            "Mother Name":        s.get("motherName",""),
            "Address":            f"{s.get('address','')} {s.get('barangay','')} {s.get('city','')}".strip(),
            "Total Fees":         total,
            "Amount Paid":        paid,
            "Balance":            total - paid,
            "Docs Submitted":     f"{docs_submitted}/{len(docs_list)}",
            "Previous School":    s.get("previousSchool",""),
            "Enrolled On":        s.get("enrolledAt","")[:10] if s.get("enrolledAt") else "",
        }

    master_df = pd.DataFrame([_to_row(s) for s in filtered])

    # ── Export button ─────────────────────────────────────────────────────────
    if not master_df.empty:
        if "Excel" in export_fmt:
            xls_buf = _io.BytesIO()
            with pd.ExcelWriter(xls_buf, engine="openpyxl") as writer:
                # Master sheet
                master_df.to_excel(writer, sheet_name="All Students", index=False)
                # One sheet per grade level
                for lvl_key in LEVEL_ORDER:
                    lvl_students = [s for s in filtered if s.get("level")==lvl_key]
                    if not lvl_students:
                        continue
                    lvl_df = pd.DataFrame([_to_row(s) for s in lvl_students])
                    sheet_name = {"preschool":"Kinder-Preschool",
                                  "elementary":"Elementary","jhs":"Junior High"}[lvl_key]
                    lvl_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    # Per-grade sheets inside each level
                    grades_in_lvl = sorted(
                        set(s.get("grade","") for s in lvl_students),
                        key=lambda g: GRADE_ORDER.get(g,99)
                    )
                    for grade in grades_in_lvl:
                        g_students = [s for s in lvl_students if s.get("grade")==grade]
                        g_df = pd.DataFrame([_to_row(s) for s in g_students])
                        g_sheet = grade.replace(" ","")[:31]
                        g_df.to_excel(writer, sheet_name=g_sheet, index=False)
            xls_buf.seek(0)
            st.download_button(
                "⬇ Export Full Inventory (Excel)",
                xls_buf.getvalue(),
                f"SEPI_Student_Inventory_{sy}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="inv_export_xlsx", use_container_width=True
            )
        else:
            csv_str = master_df.to_csv(index=False)
            st.download_button(
                "⬇ Export Full Inventory (CSV)",
                csv_str,
                f"SEPI_Student_Inventory_{sy}.csv",
                "text/csv",
                key="inv_export_csv", use_container_width=True
            )

    st.markdown("---")

    # ── Grade-level tabs ───────────────────────────────────────────────────────
    level_tabs = st.tabs(["📋 All Levels",
                          "🌸 Kinder / Preschool",
                          "📚 Elementary",
                          "🏫 Junior High School"])

    def _render_grade_table(students_in_level, level_key):
        if not students_in_level:
            st.info("No students in this level.")
            return

        # Get sorted unique grades
        grades = sorted(
            set(s.get("grade","") for s in students_in_level),
            key=lambda g: GRADE_ORDER.get(g, 99)
        )

        for grade in grades:
            grade_students = [s for s in students_in_level if s.get("grade")==grade]
            if not grade_students:
                continue

            approved_g  = sum(1 for s in grade_students if s.get("status")=="approved")
            pending_g   = sum(1 for s in grade_students if s.get("status")=="pending")
            total_bal_g = sum(float(s.get("totalFees",0) or 0) - float(s.get("paidAmount",0) or 0)
                              for s in grade_students)

            with st.expander(
                f"**{grade}** — {len(grade_students)} student{'s' if len(grade_students)!=1 else ''}  "
                f"| ✅ {approved_g} approved  | ⏳ {pending_g} pending  "
                f"| Outstanding: ₱{total_bal_g:,.2f}",
                expanded=(len(grades) == 1)
            ):
                # Grade-level summary cards
                gs1,gs2,gs3,gs4 = st.columns(4)
                gs1.metric("Enrolled",  len(grade_students))
                gs2.metric("Approved",  approved_g)
                gs3.metric("Pending",   pending_g)
                gs4.metric("Outstanding Balance", f"₱{total_bal_g:,.2f}")

                # Student roster table
                rows = []
                for i, s in enumerate(sorted(grade_students,
                                             key=lambda x: x.get("lastName","").lower()), 1):
                    paid  = float(s.get("paidAmount",0) or 0)
                    total = float(s.get("totalFees",0) or 0)
                    bal   = total - paid
                    status= s.get("status","pending")
                    ic, bg, col = STATUS_COLOR.get(status, ("🟡","#fef3c7","#92400e"))
                    docs_list = [
                        "PSA Birth Certificate","Form 138 / Report Card","Good Moral Certificate",
                        "Certificate of Completion / Diploma","School Clearance (if applicable)",
                        "2x2 ID Pictures (6 pcs)","Medical Certificate",
                    ]
                    docs_state = s.get("docs",{})
                    docs_done  = sum(1 for d in docs_list if docs_state.get(d))
                    rows.append({
                        "#":             i,
                        "Tracking ID":   s.get("trackingId",""),
                        "Last Name":     s.get("lastName",""),
                        "First Name":    s.get("firstName",""),
                        "M.I.":          (s.get("middleName","") or " ")[:1] + ".",
                        "Gender":        (s.get("gender","") or "")[:1].upper(),
                        "LRN":           s.get("lrn","") or "—",
                        "Transfer":      (s.get("transferStatus","") or "")[:3],
                        "Status":        status.replace("_"," ").title(),
                        "Docs":          f"{docs_done}/{len(docs_list)}",
                        "Total Fees":    f"₱{total:,.2f}",
                        "Paid":          f"₱{paid:,.2f}",
                        "Balance":       f"₱{bal:,.2f}",
                        "Contact":       s.get("phone","") or "—",
                    })

                df = pd.DataFrame(rows)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "#":           st.column_config.NumberColumn(width="small"),
                        "Tracking ID": st.column_config.TextColumn(width="medium"),
                        "Last Name":   st.column_config.TextColumn(width="medium"),
                        "First Name":  st.column_config.TextColumn(width="medium"),
                        "M.I.":        st.column_config.TextColumn(width="small"),
                        "Gender":      st.column_config.TextColumn(width="small"),
                        "LRN":         st.column_config.TextColumn(width="medium"),
                        "Transfer":    st.column_config.TextColumn(width="small"),
                        "Status":      st.column_config.TextColumn(width="medium"),
                        "Docs":        st.column_config.TextColumn(width="small"),
                        "Total Fees":  st.column_config.TextColumn(width="medium"),
                        "Paid":        st.column_config.TextColumn(width="medium"),
                        "Balance":     st.column_config.TextColumn(width="medium"),
                        "Contact":     st.column_config.TextColumn(width="medium"),
                    }
                )

                # Per-grade export
                g_df = pd.DataFrame([_to_row(s) for s in grade_students])
                g_csv = g_df.to_csv(index=False)
                st.download_button(
                    f"⬇ Export {grade} roster (CSV)",
                    g_csv,
                    f"SEPI_{grade.replace(' ','_')}_{sy}.csv",
                    "text/csv",
                    key=f"inv_csv_{level_key}_{grade.replace(' ','_')}",
                    use_container_width=False,
                )

    # Tab 0: All Levels
    with level_tabs[0]:
        _render_grade_table(filtered, "all")

    # Tab 1: Preschool
    with level_tabs[1]:
        ps = [s for s in filtered if s.get("level")=="preschool"]
        st.caption(f"{len(ps)} student{'s' if len(ps)!=1 else ''} enrolled")
        _render_grade_table(ps, "preschool")

    # Tab 2: Elementary
    with level_tabs[2]:
        el = [s for s in filtered if s.get("level")=="elementary"]
        st.caption(f"{len(el)} student{'s' if len(el)!=1 else ''} enrolled")
        _render_grade_table(el, "elementary")

    # Tab 3: JHS
    with level_tabs[3]:
        jh = [s for s in filtered if s.get("level")=="jhs"]
        st.caption(f"{len(jh)} student{'s' if len(jh)!=1 else ''} enrolled")
        _render_grade_table(jh, "jhs")


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN SETTINGS — Change Password with OTP
# ══════════════════════════════════════════════════════════════════════════════
import random, smtplib, hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _send_otp_email(otp: str, sender_email: str, sender_app_password: str) -> bool:
    """Send OTP to sepiregistrar@gmail.com via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"SEPI Admin Portal — Password Change OTP: {otp}"
        msg["From"]    = sender_email
        msg["To"]      = sender_email   # send to school email itself

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                    border:1px solid #f48fb1;border-radius:12px;overflow:hidden">
          <div style="background:#c2185b;padding:18px 24px">
            <h2 style="color:#fff;margin:0;font-size:18px">SEPI Enrollment System</h2>
            <p style="color:rgba(255,255,255,.8);margin:4px 0 0;font-size:12px">
              School of Everlasting Pearl, Inc.
            </p>
          </div>
          <div style="padding:24px">
            <p style="color:#333;font-size:14px">A password change was requested for the Admin Portal.</p>
            <p style="color:#333;font-size:14px">Your One-Time Password (OTP) is:</p>
            <div style="background:#fce4ec;border:2px solid #c2185b;border-radius:10px;
                        text-align:center;padding:20px;margin:16px 0">
              <span style="font-size:36px;font-weight:700;letter-spacing:10px;
                           color:#c2185b;font-family:monospace">{otp}</span>
            </div>
            <p style="color:#666;font-size:12px">
              This OTP is valid for <b>5 minutes</b>.<br>
              If you did not request this, please ignore this email.
            </p>
          </div>
          <div style="background:#f8f9fa;padding:12px 24px;text-align:center">
            <p style="color:#94a3b8;font-size:11px;margin:0">
              SEPI Enrollment System · sepiregistrar@gmail.com
            </p>
          </div>
        </div>"""

        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_app_password)
            server.sendmail(sender_email, sender_email, msg.as_string())
        return True
    except Exception as e:
        st.session_state["_email_error"] = str(e)
        return False


def _admin_settings():
    st.title("⚙️ Admin Settings")
    st.caption("Change the admin portal password using OTP verification sent to the school email.")

    # ── Gmail SMTP Configuration ──────────────────────────────────────────────
    with st.expander("📧 Email Configuration (Gmail SMTP)", expanded=False):
        st.markdown("""
        To enable OTP email delivery, you need a **Gmail App Password** for `sepiregistrar@gmail.com`.

        **One-time setup steps:**
        1. Go to [myaccount.google.com](https://myaccount.google.com) → **Security** → **2-Step Verification** (enable if not yet)
        2. Go to **App passwords** → Select app: *Mail* → Select device: *Other* → name it *SEPI*
        3. Copy the 16-character app password
        4. On Streamlit Cloud → your app → **Settings** → **Secrets** → add:
        ```toml
        GMAIL_APP_PASSWORD = "your-16-char-app-password"
        ADMIN_PASSWORD = "your-current-admin-password"
        ```
        """)

    st.markdown("---")

    # ── Get email config ──────────────────────────────────────────────────────
    school_email = "sepiregistrar@gmail.com"
    try:
        gmail_app_pw = st.secrets["GMAIL_APP_PASSWORD"]
        email_configured = True
    except Exception:
        gmail_app_pw = None
        email_configured = False

    if not email_configured:
        st.warning("⚠️ Gmail App Password not configured yet. Follow the setup steps above, then come back.")
        st.markdown("**In the meantime, you can change the password directly below (no OTP):**")
        with st.form("direct_pw_form"):
            cur_pw  = st.text_input("Current Password", type="password", key="dir_cur")
            new_pw  = st.text_input("New Password",     type="password", key="dir_new")
            new_pw2 = st.text_input("Confirm New Password", type="password", key="dir_new2")
            submitted = st.form_submit_button("🔒 Change Password", use_container_width=True)
            if submitted:
                if cur_pw != st.session_state.admin_password:
                    st.error("Current password is incorrect.")
                elif len(new_pw) < 6:
                    st.error("New password must be at least 6 characters.")
                elif new_pw != new_pw2:
                    st.error("Passwords do not match.")
                else:
                    st.session_state.admin_password = new_pw
                    st.success("✅ Password changed successfully! Remember to add it to Streamlit Secrets so it persists after redeployment.")
        return

    # ── STEP 1: Request OTP ───────────────────────────────────────────────────
    st.markdown("### Step 1 — Request OTP")
    st.markdown(f"An OTP will be sent to **{school_email}**")

    col1, col2 = st.columns([2,1])
    otp_sent   = st.session_state.get("otp_code") is not None
    otp_expiry = st.session_state.get("otp_expiry")
    otp_valid  = otp_expiry and datetime.datetime.now() < otp_expiry

    if otp_sent and otp_valid:
        remaining = int((otp_expiry - datetime.datetime.now()).total_seconds())
        st.info(f"📨 OTP sent to {school_email}. Valid for {remaining // 60}m {remaining % 60}s. Check your inbox.")
    
    if col1.button("📨 Send OTP to School Email",
                   key="send_otp_btn",
                   disabled=(otp_sent and otp_valid),
                   use_container_width=True):
        otp = str(random.randint(100000, 999999))
        st.session_state.otp_code     = hashlib.sha256(otp.encode()).hexdigest()
        st.session_state.otp_expiry   = datetime.datetime.now() + datetime.timedelta(minutes=5)
        st.session_state.otp_verified = False
        with st.spinner("Sending OTP email…"):
            success = _send_otp_email(otp, school_email, gmail_app_pw)
        if success:
            st.success(f"✅ OTP sent to {school_email}! Check your inbox.")
            st.rerun()
        else:
            err = st.session_state.pop("_email_error","Unknown error")
            st.error(f"❌ Failed to send email: {err}")
            st.session_state.otp_code   = None
            st.session_state.otp_expiry = None

    if col2.button("🔄 Resend OTP", key="resend_otp_btn", use_container_width=True):
        st.session_state.otp_code   = None
        st.session_state.otp_expiry = None
        st.rerun()

    st.markdown("---")

    # ── STEP 2: Verify OTP ────────────────────────────────────────────────────
    st.markdown("### Step 2 — Enter OTP")

    with st.form("otp_verify_form"):
        otp_input  = st.text_input("Enter the 6-digit OTP from your email",
                                    max_chars=6, placeholder="e.g. 483920",
                                    key="otp_input_field")
        verify_btn = st.form_submit_button("✔️ Verify OTP", use_container_width=True)

        if verify_btn:
            if not st.session_state.get("otp_code"):
                st.error("Please request an OTP first.")
            elif not otp_valid:
                st.error("OTP has expired. Please request a new one.")
                st.session_state.otp_code = None
            elif hashlib.sha256(otp_input.encode()).hexdigest() != st.session_state.otp_code:
                st.error("❌ Incorrect OTP. Please try again.")
            else:
                st.session_state.otp_verified = True
                st.success("✅ OTP verified! Proceed to set your new password below.")
                st.rerun()

    st.markdown("---")

    # ── STEP 3: Set New Password (only after OTP verified) ────────────────────
    st.markdown("### Step 3 — Set New Password")

    if not st.session_state.get("otp_verified"):
        st.info("🔒 Complete OTP verification above to unlock this section.")
        return

    st.success("🔓 Identity verified — enter your new password below.")
    with st.form("new_pw_form"):
        new_pw  = st.text_input("New Password", type="password",
                                 placeholder="Minimum 8 characters", key="new_pw_1")
        new_pw2 = st.text_input("Confirm New Password", type="password",
                                 key="new_pw_2")
        save_btn = st.form_submit_button("💾 Save New Password", use_container_width=True)

        if save_btn:
            if len(new_pw) < 8:
                st.error("Password must be at least 8 characters.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            else:
                st.session_state.admin_password = new_pw
                # Clear OTP state
                st.session_state.otp_code     = None
                st.session_state.otp_expiry   = None
                st.session_state.otp_verified = False
                st.success("✅ Password changed successfully!")
                st.info(
                    "**Important:** To make this permanent across redeployments, "
                    "go to Streamlit Cloud → your app → Settings → Secrets and update:\n"
                    "`ADMIN_PASSWORD = \"your-new-password\"`"
                )


# ══════════════════════════════════════════════════════════════════════════════
#  SOA PAYMENT UPDATE PAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_soa_update():
    with st.sidebar:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=70)
        st.markdown("<h3 style='color:#f48fb1;margin:0'>SEPI</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:rgba(255,255,255,.5);font-size:11px'>SOA Payment Update</p>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("← Back to Login"):
            st.session_state.page = "login"; st.rerun()

    st.title("💳 SOA Payment Update")
    st.caption("Enter the student's Tracking ID to record a new payment or view payment history.")

    tid_input = st.text_input("Tracking ID", placeholder="e.g. SEPI-ABC123", key="soa_tid_input")

    if st.button("🔍 Look Up Student", key="soa_lookup", use_container_width=True):
        s = st.session_state.students.get(tid_input.strip().upper())
        if s:
            st.session_state.soa_update_id = tid_input.strip().upper()
        else:
            st.error("Tracking ID not found.")
            st.session_state.soa_update_id = None

    sid = st.session_state.get("soa_update_id")
    if not sid:
        return

    s = st.session_state.students.get(sid)
    if not s:
        st.error("Student record not found.")
        return

    # ── Student summary ───────────────────────────────────────────────────────
    total    = float(s.get("totalFees", 0) or 0)
    paid     = float(s.get("paidAmount", 0) or 0)
    balance  = total - paid
    llabel   = {"preschool": "Kinder/Preschool", "elementary": "Elementary", "jhs": "Junior High School"}

    st.markdown(f"""
    <div style='border:0.5px solid #f48fb1;border-radius:12px;padding:16px 20px;
                background:var(--color-background-primary);margin-bottom:16px'>
      <div style='font-size:13px;font-weight:600;color:#c2185b;margin-bottom:8px'>
        {s.get("lastName","")}, {s.get("firstName","")} {s.get("middleName","")}
      </div>
      <div style='font-size:12px;color:#555'>
        {llabel.get(s.get("level",""),"—")} — {s.get("grade","—")} &nbsp;|&nbsp;
        ID: {sid} &nbsp;|&nbsp; SY {s.get("schoolYear","2026-2027")}
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Fees",   peso(total))
    c2.metric("Total Paid",   peso(paid))
    c3.metric("Balance",      peso(balance), delta=f"-{peso(balance)}" if balance > 0 else "Fully Paid")

    # ── Payment history ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📋 Payment History**")
    history = s.get("paymentHistory", [])
    if history:
        import pandas as pd
        df = pd.DataFrame(history)
        df.index = df.index + 1
        st.dataframe(df, use_container_width=True, hide_index=False)
    else:
        st.info("No payment records yet.")

    # ── Add new payment ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**➕ Record New Payment**")

    with st.form("payment_form", clear_on_submit=True):
        pc1, pc2, pc3 = st.columns(3)
        pay_amount = pc1.number_input("Payment Amount (PHP)", min_value=1.0,
                                       max_value=float(max(balance, 1)),
                                       value=min(1000.0, float(max(balance, 1))),
                                       step=100.0, key="pay_amount_input")
        pay_mode   = pc2.selectbox("Payment Mode",
                                    ["Cash", "GCash", "Bank Transfer", "Check"],
                                    key="pay_mode_input")
        pay_date   = pc3.date_input("Payment Date",
                                     value=datetime.date.today(),
                                     key="pay_date_input")
        pay_or     = st.text_input("OR Number (Official Receipt)", placeholder="Optional",
                                    key="pay_or_input")
        pay_note   = st.text_input("Remarks / Notes", placeholder="e.g. January installment",
                                    key="pay_note_input")
        submitted  = st.form_submit_button("💾 Save Payment", use_container_width=True)

        if submitted:
            if pay_amount <= 0:
                st.error("Payment amount must be greater than zero.")
            elif pay_amount > balance + 0.01:
                st.error(f"Amount exceeds balance of {peso(balance)}.")
            else:
                new_record = {
                    "Date":    str(pay_date),
                    "Amount":  f"PHP {pay_amount:,.2f}",
                    "Mode":    pay_mode,
                    "OR No.":  pay_or or "—",
                    "Remarks": pay_note or "—",
                }
                if "paymentHistory" not in st.session_state.students[sid]:
                    st.session_state.students[sid]["paymentHistory"] = []
                new_paid = paid + pay_amount
                s_soa = st.session_state.students[sid]
                s_soa["paymentHistory"].append(new_record)
                s_soa["paidAmount"] = new_paid
                _db.db_save(s_soa)
                if (st.session_state.get("user") and
                        st.session_state.user.get("trackingId") == sid):
                    st.session_state.user["paidAmount"] = new_paid
                    st.session_state.user["paymentHistory"] = s_soa["paymentHistory"]
                st.success(f"✅ Payment of {peso(pay_amount)} recorded successfully!")
                st.rerun()

    # ── Generate updated SOA ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📄 Download Updated SOA**")
    st.caption("Generates an updated Statement of Account reflecting all payments recorded.")

    soa_key = f"updated_soa_{sid}"
    if st.button("🔄 Generate Updated SOA PDF", key=f"gen_updated_soa_{sid}",
                 use_container_width=True):
        with st.spinner("Generating updated SOA…"):
            try:
                updated_student = st.session_state.students[sid]
                st.session_state[soa_key] = build_soa(updated_student)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.get(soa_key):
        st.download_button(
            label=f"⬇ Download Updated SOA — {sid}",
            data=st.session_state[soa_key],
            file_name=f"{sid}_updated_soa.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_updated_soa_{sid}"
        )


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
    elif st.session_state.page == "soa_update":
        page_soa_update()
    elif st.session_state.page == "payroll":
        page_payroll_portal()

if __name__ == "__main__":
    main()
