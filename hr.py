"""
SEPI HR & Payroll Module
Imported by app.py — all HR, payroll and leave management functions.
"""
import os, datetime, json
import streamlit as st
import pandas as pd
from fees import SCHOOL_YEAR, LEVEL_LABEL
from payroll import (compute_payroll, compute_monthly_payroll, sss_employee,
                     philhealth_employee, pagibig_employee,
                     EMPLOYEE_TYPES, OTHER_DEDUCTION_TYPES, SEPI_INITIAL_STAFF)
from hr_pdf import build_payslip, build_payroll_summary, build_coe, build_leave_form

LOGO_PATH = None
for _name in ["sepi_logo.jpg","sepi_logo.png","sepi_logo"]:
    _p = os.path.join(os.path.dirname(__file__), _name)
    if os.path.exists(_p):
        LOGO_PATH = _p; break

HR_KV_NS   = "dfe32c5ff0924b199cea8e36f588f6c4"
HR_KV_BASE = "https://api.cloudflare.com/client/v4"

def peso(n): return f"\u20b1{float(n or 0):,.2f}"

LEAVE_TYPES_LIST = [
    ("SIL","Service Incentive Leave (SIL)","Earned at 1 day/month, max 10/SY"),
    ("Sick","Sick Leave","Deducted from SIL credit"),
    ("Personal","Personal Leave","Deducted from SIL credit"),
    ("Vacation","Vacation Leave","Without pay"),
    ("Maternity","Maternity Leave (RA 11210)","With pay, attach hospital documents"),
    ("SoloParent","Solo Parent Leave (RA 8972)","Attach valid Solo Parent ID"),
    ("VAWC","VAWC Leave (RA 9262)","For women victims of violence"),
    ("MagnaCartaWomen","Magna Carta for Women Leave (RA 9710)","Attach medical certificate"),
    ("Paternity","Paternity Leave (RA 8187)","7 days, first 4 deliveries"),
    ("Others","Others","Specify in remarks"),
]
LEAVE_KEY_TO_LABEL = {k: lbl for k, lbl, _ in LEAVE_TYPES_LIST}
SIL_RATE_PER_MONTH = 1.0
SIL_MAX_PER_SY     = 10.0

# ══════════════════════════════════════════════════════════════════════════════
#  HR & PAYROLL MODULE
# ══════════════════════════════════════════════════════════════════════════════
HR_KV_NS   = "dfe32c5ff0924b199cea8e36f588f6c4"
HR_KV_BASE = "https://api.cloudflare.com/client/v4"

def _hr_headers():
    try:
        token = st.secrets["CF_API_TOKEN"]
        return {"Authorization": f"Bearer {token}"} if token else None
    except Exception:
        return None


def _hr_kv_verify() -> tuple:
    """Test actual HR KV connectivity. Returns (ok, message)."""
    import requests as _req
    hdrs = _hr_headers()
    if not hdrs:
        return False, "CF_API_TOKEN not set in Streamlit Secrets"
    try:
        acct = st.secrets.get("CF_ACCOUNT_ID","")
        if not acct:
            return False, "CF_ACCOUNT_ID not set"
        r = _req.get(
            f"{HR_KV_BASE}/accounts/{acct}/storage/kv/namespaces/{HR_KV_NS}/keys",
            headers=hdrs, params={"limit": 10}, timeout=8
        )
        if r.status_code == 200:
            return True, f"HR KV connected ({r.json().get('result_info',{}).get('count','?')} records)"
        elif r.status_code == 401:
            return False, "Invalid API token — update CF_API_TOKEN in Streamlit Secrets"
        else:
            return False, f"HR KV error {r.status_code}"
    except Exception as e:
        return False, f"Network error: {str(e)[:80]}"

def _hr_save(key: str, value: dict) -> bool:
    """Save a record to SEPI_HR_Payroll KV namespace. Returns True on success."""
    import requests, json as _json
    hdrs = _hr_headers()
    if not hdrs:
        st.warning("⚠️ CF_API_TOKEN missing — HR record not saved to cloud.", icon="☁️")
        return False
    try:
        acct = st.secrets.get("CF_ACCOUNT_ID","")
        if not acct:
            st.warning("⚠️ CF_ACCOUNT_ID missing — HR record not saved to cloud.", icon="☁️")
            return False
        url = f"{HR_KV_BASE}/accounts/{acct}/storage/kv/namespaces/{HR_KV_NS}/values/{key}"
        save_headers = {
            "Authorization": hdrs["Authorization"],
            "Content-Type":  "text/plain",
        }
        resp = requests.put(url, headers=save_headers,
                            data=_json.dumps(value, default=str), timeout=10)
        if resp.status_code not in (200, 201):
            st.error(f"☁️ KV save failed ({resp.status_code}): {resp.text[:100]}")
            return False
        return True
    except Exception as e:
        st.error(f"☁️ KV save error: {str(e)[:100]}")
        return False

def _hr_delete_kv(key: str):
    import requests
    hdrs = _hr_headers()
    if not hdrs: return
    acct = st.secrets.get("CF_ACCOUNT_ID","")
    url  = f"{HR_KV_BASE}/accounts/{acct}/storage/kv/namespaces/{HR_KV_NS}/values/{key}"
    try: requests.delete(url, headers=hdrs, timeout=8)
    except Exception: pass

def _hr_load_all():
    """
    Load all HR/Payroll records from Cloudflare KV into session state.
    Called once per session. Loads: teachers, payroll_runs, leave_records.
    """
    import requests, json as _json
    if st.session_state.hr_loaded:
        return
    hdrs = _hr_headers()
    if not hdrs:
        # No credentials — work in-memory only
        st.session_state.hr_loaded = True
        return
    try:
        acct = st.secrets.get("CF_ACCOUNT_ID","")
    except Exception:
        st.session_state.hr_loaded = True
        return
    base = f"{HR_KV_BASE}/accounts/{acct}/storage/kv/namespaces/{HR_KV_NS}"
    try:
        r = requests.get(f"{base}/keys", headers=hdrs,
                         params={"limit": 10000}, timeout=12)
        if r.status_code != 200:
            st.session_state.hr_loaded = True
            return
        keys = [item["name"] for item in r.json().get("result", [])]
        for key in keys:
            try:
                rv = requests.get(f"{base}/values/{key}", headers=hdrs, timeout=8)
                if rv.status_code != 200:
                    continue
                # Try JSON parse first, fallback to text
                try:
                    record = rv.json()
                except Exception:
                    continue
                if key.startswith("teacher:"):
                    tid = key.replace("teacher:", "")
                    st.session_state.teachers[tid] = record
                elif key.startswith("payroll:"):
                    st.session_state.payroll_runs[key] = record
                elif key.startswith("leave:"):
                    if "leave_records" not in st.session_state:
                        st.session_state.leave_records = {}
                    st.session_state.leave_records[key] = record
            except Exception:
                continue
    except Exception:
        pass
    st.session_state.hr_loaded = True

def _gen_teacher_id():
    import uuid
    return "EMP-" + str(uuid.uuid4())[:6].upper()


# ── MAIN HR PAGE ───────────────────────────────────────────────────────────────
def _admin_hr():
    # Always attempt load (will skip if already loaded unless flag was reset by Sync)
    _hr_load_all()
    st.title("👨‍🏫 HR & Payroll")
    # ── Sync button — force reload from KV ──────────────────────────────────
    sync_col1, sync_col2 = st.columns([3,1])
    n_teachers = len(st.session_state.teachers)
    n_payroll  = len(st.session_state.payroll_runs)
    sync_col1.caption(f"☁️ Loaded from KV: **{n_teachers}** staff · **{n_payroll}** payroll runs")
    if sync_col2.button("🔄 Sync", key="hr_sync_btn", help="Reload all HR records from Cloudflare KV"):
        st.session_state.hr_loaded = False
        st.rerun()

    hr_tab = st.tabs(["👥 Staff Directory", "💰 Process Payroll",
                       "📋 Payroll History", "📄 Documents", "🏖️ Leave Management"])

    with hr_tab[0]: _hr_staff_directory()
    with hr_tab[1]: _hr_process_payroll()
    with hr_tab[2]: _hr_payroll_history()
    with hr_tab[3]: _hr_documents()
    with hr_tab[4]: _admin_leave_module()


# ── TAB 1: STAFF DIRECTORY ─────────────────────────────────────────────────────
def _hr_staff_directory():
    teachers = st.session_state.teachers
    st.markdown(f"**{len(teachers)} staff member{'s' if len(teachers)!=1 else ''} enrolled**")

    # ── Summary metrics ───────────────────────────────────────────────────────
    if teachers:
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total Staff", len(teachers))
        m2.metric("Full-time Teaching",
                  sum(1 for t in teachers.values() if "Full-time Teaching" in t.get("employeeType","")))
        m3.metric("Part-time Teaching",
                  sum(1 for t in teachers.values() if "Part-time" in t.get("employeeType","")))
        m4.metric("Non-teaching",
                  sum(1 for t in teachers.values() if "Non-teaching" in t.get("employeeType","")))
        st.markdown("---")

    # ── Add new teacher ───────────────────────────────────────────────────────
    with st.expander("➕ Enroll New Staff Member", expanded=(len(teachers)==0)):
        with st.form("enroll_teacher_form", clear_on_submit=True):
            st.markdown("**Personal Information**")
            c1,c2,c3 = st.columns(3)
            t_last   = c1.text_input("Last Name *",      key="t_last")
            t_first  = c2.text_input("First Name *",     key="t_first")
            t_middle = c3.text_input("Middle Name",      key="t_middle")
            c1b,c2b  = st.columns(2)
            t_pos    = c1b.text_input("Position / Designation *", key="t_pos",
                                       placeholder="e.g. Teacher I, Grade School Coordinator")
            t_type   = c2b.selectbox("Employment Type *", EMPLOYEE_TYPES, key="t_type")
            c1c,c2c,c3c = st.columns(3)
            t_hired  = c1c.text_input("Date Hired (e.g. June 2022) *", key="t_hired",
                                       placeholder="e.g. June 1, 2022")
            t_status = c2c.selectbox("Employment Status",
                                      ["Regular","Probationary","Contractual"], key="t_status")
            t_gender = c3c.selectbox("Gender", ["","Male","Female","Prefer not to say"], key="t_gender")
            st.markdown("**Compensation**")
            c1d,c2d,c3d = st.columns(3)
            t_basic  = c1d.number_input("Basic Monthly Salary (PHP) *", min_value=0.0,
                                         step=500.0, key="t_basic")
            t_ancil  = c2d.number_input("Ancillary Pay / Monthly Allowance (PHP)",
                                         min_value=0.0, step=100.0, key="t_ancil",
                                         help="Fixed monthly amount released on 2nd period (e.g. 2,500)")
            c3d.markdown(" ")  # spacer
            st.markdown("**Government Contributions & IDs**")
            c1e,c2e,c3e,c4e = st.columns(4)
            t_sss    = c1e.text_input("SSS Number",      key="t_sss", placeholder="12-3456789-0")
            t_ph     = c2e.text_input("PhilHealth No.",  key="t_ph",  placeholder="12-345678901-2")
            t_pi     = c3e.text_input("Pag-IBIG No.",    key="t_pi",  placeholder="1234-5678-9012")
            t_tin    = c4e.text_input("TIN",             key="t_tin", placeholder="123-456-789")
            t_contact= st.text_input("Contact Number",   key="t_contact")
            t_email  = st.text_input("Email Address",    key="t_email")
            t_address= st.text_input("Home Address",     key="t_address")
            t_govded = st.checkbox("Apply Government Deductions (SSS, PhilHealth, Pag-IBIG)",
                                    value=True, key="t_govded",
                                    help="Uncheck for employees exempt from mandatory contributions")
            t_photo  = st.file_uploader("2x2 Photo (optional, JPG/PNG)",
                                         type=["jpg","jpeg","png"], key="t_photo")
            submitted = st.form_submit_button("💾 Enroll Staff Member", use_container_width=True)
            if submitted:
                if not all([t_last, t_first, t_pos, t_basic]):
                    st.error("Please fill in all required (*) fields.")
                else:
                    tid = _gen_teacher_id()
                    teacher = {
                        "teacherId":      tid,
                        "name":           f"{t_last.upper()}, {t_first} {t_middle}".strip(", "),
                        "lastName":       t_last,
                        "firstName":      t_first,
                        "middleName":     t_middle,
                        "position":       t_pos,
                        "employeeType":   t_type,
                        "employmentStatus": t_status,
                        "gender":         t_gender,
                        "dateHired":      t_hired,
                        "basicMonthlyPay": t_basic,
                        "ancillaryPay":    t_ancil,
                        "sssNo":           t_sss,
                        "philHealthNo":    t_ph,
                        "pagIbigNo":       t_pi,
                        "tin":             t_tin,
                        "contact":         t_contact,
                        "email":           t_email,
                        "address":         t_address,
                        "hasGovDeductions": t_govded,
                        "photoB64":       __import__("base64").b64encode(t_photo.read()).decode() if t_photo else "",
                        "enrolledOn":     datetime.datetime.now().isoformat(),
                    }
                    st.session_state.teachers[tid] = teacher
                    _hr_save(f"teacher:{tid}", teacher)
                    st.success(f"✅ {teacher['name']} enrolled with ID **{tid}**")
                    st.rerun()

    # ── Teacher list ─────────────────────────────────────────────────────────
    if not teachers:
        st.info("No staff members enrolled yet. Use the form above to add your first teacher.")
        return

    st.markdown("**Staff Roster**")
    for tid, t in sorted(teachers.items(), key=lambda x: x[1].get("lastName","")):
        with st.expander(f"**{t.get('name','—')}**  ·  {t.get('position','—')}  ·  {t.get('employeeType','—')}"):
            # 201 File tabs
            f201, fedit, fdel = st.tabs(["📁 201 File", "✏️ Edit", "🗑️ Delete"])

            with f201:
                # Show photo if available
                if t.get("photoB64"):
                    import base64 as _b64d
                    import io as _pio
                    try:
                        ph_bytes = _b64d.b64decode(t["photoB64"])
                        st.image(_pio.BytesIO(ph_bytes), width=100, caption=t.get("name",""))
                    except Exception: pass
                fi1,fi2 = st.columns(2)
                with fi1:
                    st.markdown("**Employment Details**")
                    for lbl, val in [
                        ("Employee ID",   t.get("teacherId")),
                        ("Full Name",     t.get("name")),
                        ("Position",      t.get("position")),
                        ("Type",          t.get("employeeType")),
                        ("Status",        t.get("employmentStatus")),
                        ("Date Hired",    t.get("dateHired")),
                        ("Gender",        t.get("gender")),
                    ]:
                        st.markdown(f"**{lbl}:** {val or '—'}")
                with fi2:
                    st.markdown("**Compensation & Contributions**")
                    basic = float(t.get("basicMonthlyPay",0) or 0)
                    sss_m   = sss_employee(basic)
                    ph_m    = philhealth_employee(basic)
                    pi_m    = pagibig_employee(basic)
                    ancil = float(t.get("ancillaryPay",0) or 0)
                    for lbl, val in [
                        ("Basic Monthly Pay",   peso(basic)),
                        ("Ancillary Pay",        peso(ancil)),
                        ("Gross Monthly",        peso(basic+ancil)),
                        ("SSS No.",             t.get("sssNo","—")),
                        ("SSS Contribution",    f"{peso(sss_m)}/month  ({peso(sss_m/2)}/cut-off)"),
                        ("PhilHealth No.",      t.get("philHealthNo","—")),
                        ("PhilHealth Premium",  f"{peso(ph_m)}/month  ({peso(ph_m/2)}/cut-off)"),
                        ("Pag-IBIG No.",        t.get("pagIbigNo","—")),
                        ("Pag-IBIG Contribution",f"{peso(pi_m)}/month  ({peso(pi_m/2)}/cut-off)"),
                        ("TIN",                 t.get("tin","—")),
                        ("Contact",             t.get("contact","—")),
                        ("Email",               t.get("email","—")),
                    ]:
                        st.markdown(f"**{lbl}:** {val or '—'}")

            with fedit:
                with st.form(f"edit_{tid}", clear_on_submit=False):
                    ec1,ec2 = st.columns(2)
                    new_pos   = ec1.text_input("Position", value=t.get("position",""), key=f"ep_{tid}")
                    new_type  = ec2.selectbox("Employment Type", EMPLOYEE_TYPES,
                                               index=EMPLOYEE_TYPES.index(t.get("employeeType", EMPLOYEE_TYPES[0]))
                                               if t.get("employeeType") in EMPLOYEE_TYPES else 0,
                                               key=f"et_{tid}")
                    ec3,ec4   = st.columns(2)
                    new_basic = ec3.number_input("Basic Monthly Pay", value=float(t.get("basicMonthlyPay",0) or 0),
                                                  step=500.0, key=f"eb_{tid}")
                    new_ancil = ec4.number_input("Ancillary Pay (PHP)", value=float(t.get("ancillaryPay",0) or 0),
                                                  step=100.0, key=f"ea_{tid}")
                    new_status= st.selectbox("Employment Status",
                                              ["Regular","Probationary","Contractual"],
                                              index=["Regular","Probationary","Contractual"].index(
                                                  t.get("employmentStatus","Regular"))
                                              if t.get("employmentStatus") in ["Regular","Probationary","Contractual"] else 0,
                                              key=f"es_{tid}")
                    new_govded = st.checkbox("Apply Government Deductions",
                                              value=t.get("hasGovDeductions", True),
                                              key=f"egd_{tid}")
                    new_hired  = st.text_input("Date Hired (e.g. June 1, 2022)",
                                               value=t.get("dateHired",""), key=f"eh_{tid}")
                    new_photo  = st.file_uploader("Update Photo (JPG/PNG)",
                                                   type=["jpg","jpeg","png"], key=f"ep2_{tid}")
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        import base64 as _b64e
                        updates = {
                            "position": new_pos,
                            "employeeType": new_type,
                            "basicMonthlyPay": new_basic,
                            "ancillaryPay": new_ancil,
                            "employmentStatus": new_status,
                            "hasGovDeductions": new_govded,
                            "dateHired": new_hired,
                        }
                        if new_photo:
                            updates["photoB64"] = _b64e.b64encode(new_photo.read()).decode()
                        st.session_state.teachers[tid].update(updates)
                        _hr_save(f"teacher:{tid}", st.session_state.teachers[tid])
                        st.success("✅ Updated."); st.rerun()

            with fdel:
                st.markdown(
                    f'<div style="background:#fee2e2;border:1px solid #f87171;border-radius:8px;'
                    f'padding:10px 14px;font-size:12px;color:#7f1d1d;margin-bottom:10px">'
                    f'⚠️ Permanently delete <b>{t.get("name","")}</b> ({tid}) '
                    f'and all payroll records? This cannot be undone.</div>',
                    unsafe_allow_html=True)
                ck = f"del_teacher_{tid}"
                if not st.session_state.get(ck):
                    if st.button("🗑️ Delete Staff Member", key=f"delbtn_{tid}", use_container_width=True):
                        st.session_state[ck] = True; st.rerun()
                else:
                    dc1,dc2 = st.columns(2)
                    if dc1.button("✅ Yes, Delete Permanently", key=f"delconf_{tid}", use_container_width=True):
                        del st.session_state.teachers[tid]
                        _hr_delete_kv(f"teacher:{tid}")
                        st.session_state.pop(ck, None)
                        st.success(f"✅ {t.get('name','')} deleted."); st.rerun()
                    if dc2.button("❌ Cancel", key=f"delcancel_{tid}", use_container_width=True):
                        st.session_state.pop(ck, None); st.rerun()


# ── TAB 2: PROCESS PAYROLL ─────────────────────────────────────────────────────
def _hr_process_payroll():
    teachers = st.session_state.teachers
    if not teachers:
        st.info("No staff members enrolled. Go to Staff Directory to add teachers first.")
        return

    st.markdown("#### Process Semi-Monthly Payroll")
    st.caption("Semi-monthly: 1st cut-off covers the 1st–15th; 2nd cut-off covers the 16th–end of month.")

    # ── Period selector ───────────────────────────────────────────────────────
    import datetime
    today   = datetime.date.today()
    months  = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
    pc1,pc2,pc3 = st.columns(3)
    sel_yr  = pc1.selectbox("Year",  [2025,2026,2027],
                             index=[2025,2026,2027].index(today.year) if today.year in [2025,2026,2027] else 1,
                             key="pr_year")
    sel_mo  = pc2.selectbox("Month", months,
                             index=today.month-1, key="pr_month")
    sel_co  = pc3.selectbox("Cut-off", ["1st (1st–15th)","2nd (16th–end of month)"], key="pr_cutoff")
    co_num  = 1 if "1st" in sel_co else 2
    period_key   = f"{sel_yr}-{months.index(sel_mo)+1:02d}-{co_num}"
    cutoff_label = f"{sel_mo} {sel_yr} — {'1st' if co_num==1 else '2nd'} Cut-off"

    st.markdown(f"**Payroll Period: {cutoff_label}**")
    st.markdown("---")

    # Check if already processed
    run_key = f"payroll:{period_key}"
    existing = st.session_state.payroll_runs.get(run_key)
    if existing:
        st.success(f"✅ Payroll for **{cutoff_label}** has already been processed.")
        if st.button("🔄 Re-process (overwrite)", key="reprocess_pr"):
            del st.session_state.payroll_runs[run_key]
            st.rerun()
        _show_payroll_run(existing, cutoff_label, caller="process")
        return

    # ── Input form per teacher ────────────────────────────────────────────────
    st.markdown("**Enter attendance and adjustments for each staff member:**")
    inputs = {}
    for tid, t in sorted(teachers.items(), key=lambda x: x[1].get("lastName","")):
        name  = t.get("name","—")
        basic = float(t.get("basicMonthlyPay",0) or 0)
        allow = float(t.get("fixedAllowance",0) or 0)
        atype = t.get("allowanceType","Transportation Allowance")
        with st.expander(f"**{name}** — {t.get('position','—')} | Basic: {peso(basic)}/month"):
            ia1,ia2,ia3 = st.columns(3)
            abs_days = ia1.number_input("Absences (days)", min_value=0.0, max_value=11.0,
                                         step=0.5, value=0.0, key=f"abs_{tid}_{period_key}")
            tard_hrs = ia2.number_input("Tardiness (hours)", min_value=0.0, max_value=88.0,
                                         step=0.5, value=0.0, key=f"tard_{tid}_{period_key}")
            ot_hrs   = ia3.number_input("Overtime (hours)", min_value=0.0,
                                         step=0.5, value=0.0, key=f"ot_{tid}_{period_key}")
            ib1,ib2  = st.columns(2)
            bonus    = ib1.number_input("Bonus / Special Pay (PHP)", min_value=0.0,
                                         step=100.0, value=0.0, key=f"bon_{tid}_{period_key}")
            oth_ded  = ib2.number_input("Other Deduction (PHP)", min_value=0.0,
                                         step=100.0, value=0.0, key=f"ded_{tid}_{period_key}")
            oth_label= st.text_input("Deduction Label", value="",
                                      placeholder="e.g. Cash Advance",
                                      key=f"dedlbl_{tid}_{period_key}")
            inputs[tid] = {
                "period":       period_key,
                "cutoffLabel":  cutoff_label,
                "absences":     abs_days,
                "tardiness_hrs":tard_hrs,
                "overtime_hrs": ot_hrs,
                "bonus":        bonus,
                "allowances":   {atype: allow} if allow else {},
                "other_deductions": {oth_label or "Other Deduction": oth_ded} if oth_ded else {},
            }

    st.markdown("---")
    if st.button("🚀 Process Payroll", key="run_payroll", use_container_width=True):
        with st.spinner("Computing payroll…"):
            results = {}
            for tid, cutoff_data in inputs.items():
                t = teachers[tid]
                results[tid] = compute_payroll(t, cutoff_data)
            payroll_run = {
                "periodKey":    period_key,
                "cutoffLabel":  cutoff_label,
                "processedOn":  datetime.datetime.now().isoformat(),
                "results":      results,
                "totalNetPay":  round(sum(r["netPay"] for r in results.values()), 2),
                "totalGross":   round(sum(r["grossPay"] for r in results.values()), 2),
            }
            st.session_state.payroll_runs[run_key] = payroll_run
            _hr_save(run_key, payroll_run)
        st.success(f"✅ Payroll processed for {len(results)} staff members!")
        st.rerun()


def _show_payroll_run(run: dict, label: str, caller: str = "main"):
    """Display a processed payroll run with summary and per-employee detail."""
    import pandas as pd
    results = run.get("results", {})
    st.markdown(f"**{label}** — Processed {run.get('processedOn','')[:10]}")
    sm1,sm2,sm3,sm4 = st.columns(4)
    sm1.metric("Staff Count",   len(results))
    sm2.metric("Total Gross",   peso(run.get("totalGross",0)))
    sm3.metric("Total Net Pay", peso(run.get("totalNetPay",0)))
    sm4.metric("Total Deductions",
               peso(run.get("totalGross",0) - run.get("totalNetPay",0)))

    # Summary table
    rows = []
    for tid, r in sorted(results.items(), key=lambda x: x[1].get("teacherName","")):
        rows.append({
            "Name":         r.get("teacherName",""),
            "Position":     r.get("position",""),
            "Basic Cutoff": peso(r.get("basicCutoff",0)),
            "Allowances":   peso(r.get("totalAllowances",0)),
            "Deductions":   peso(r.get("totalDeductions",0)),
            "Gross Pay":    peso(r.get("grossPay",0)),
            "Net Pay":      peso(r.get("netPay",0)),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Per-employee payslip download
    st.markdown("**Download Individual Payslips:**")
    cols = st.columns(min(len(results), 4))
    for i, (tid, r) in enumerate(results.items()):
        col = cols[i % 4]
        ps_key = f"ps_{caller}_{tid}_{run['periodKey']}"
        if not st.session_state.get(ps_key):
            if col.button(f"📄 {r.get('teacherName','').split(',')[0]}",
                          key=f"genpslip_{caller}_{tid}_{run['periodKey']}", use_container_width=True):
                _teacher = st.session_state.teachers.get(tid, r)
                st.session_state[ps_key] = build_payslip(r["p1"], r["p2"], _teacher)
                st.rerun()
        else:
            col.download_button(
                f"⬇ {r.get('teacherName','').split(',')[0]}",
                st.session_state[ps_key],
                f"Payslip_{tid}_{run['periodKey']}.pdf",
                "application/pdf",
                use_container_width=True,
                key=f"dlps_{caller}_{tid}_{run['periodKey']}"
            )

    # Excel export
    st.markdown("---")
    xls_key = f"xls_{run['periodKey']}"
    if not st.session_state.get(xls_key):
        if st.button("📊 Export Payroll Register (Excel)", key=f"genxls_{caller}_{run['periodKey']}",
                     use_container_width=True):
            import io as _io
            all_rows = [r for r in results.values()]
            df_xls = pd.DataFrame([{
                "Employee ID":      r.get("teacherId"),
                "Name":             r.get("teacherName"),
                "Position":         r.get("position"),
                "Employment Type":  r.get("employeeType"),
                "Basic Monthly":    r.get("basicMonthlySalary"),
                "Basic Cutoff":     r.get("basicCutoff"),
                "Absences (days)":  r.get("absences"),
                "Tardiness (hrs)":  r.get("tardinessHrs"),
                "Absence Deduction":r.get("absenceDeduction"),
                "Tardiness Deduction":r.get("tardinessDeduction"),
                "Overtime Pay":     r.get("overtimePay"),
                "Allowances":       r.get("totalAllowances"),
                "Bonus":            r.get("bonus"),
                "Gross Pay":        r.get("grossPay"),
                "SSS":              r.get("sssCutoff"),
                "PhilHealth":       r.get("philHealthCutoff"),
                "Pag-IBIG":         r.get("pagIbigCutoff"),
                "Other Deductions": r.get("totalOtherDeductions"),
                "Total Deductions": r.get("totalDeductions"),
                "Net Pay":          r.get("netPay"),
            } for r in all_rows])
            xls_buf = _io.BytesIO()
            with pd.ExcelWriter(xls_buf, engine="openpyxl") as writer:
                df_xls.to_excel(writer, sheet_name=label[:31], index=False)
            xls_buf.seek(0)
            st.session_state[xls_key] = xls_buf.getvalue()
            st.rerun()
    else:
        st.download_button("⬇ Download Payroll Register",
                           st.session_state[xls_key],
                           f"PayrollRegister_{run['periodKey']}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"dlxls_{caller}_{run['periodKey']}")


# ── TAB 3: PAYROLL HISTORY ─────────────────────────────────────────────────────
def _hr_payroll_history():
    runs = st.session_state.payroll_runs
    if not runs:
        st.info("No payroll runs processed yet.")
        return
    st.markdown(f"**{len(runs)} payroll run{'s' if len(runs)!=1 else ''} on record**")
    for key in sorted(runs.keys(), reverse=True):
        run = runs[key]
        label = run.get("cutoffLabel","")
        with st.expander(f"**{label}** — {len(run.get('results',{}))} staff | Net: {peso(run.get('totalNetPay',0))} | Processed: {run.get('processedOn','')[:10]}"):
            _show_payroll_run(run, label, caller=f"hist_{key}")


# ── TAB 4: DOCUMENTS ──────────────────────────────────────────────────────────
def _hr_documents():
    teachers = st.session_state.teachers
    st.markdown("#### Generate HR Documents")
    if not teachers:
        st.info("No staff members enrolled yet.")
        return

    st.markdown("**Certificate of Employment**")
    dc1,dc2 = st.columns([2,1])
    sel_tid  = dc1.selectbox("Select Staff Member",
                              options=list(teachers.keys()),
                              format_func=lambda tid: f"{teachers[tid].get('name','—')} ({tid})",
                              key="coe_teacher")
    coe_key = f"coe_{sel_tid}"
    if not st.session_state.get(coe_key):
        if st.button("📄 Generate COE", key="gen_coe", use_container_width=True):
            with st.spinner("Generating…"):
                st.session_state[coe_key] = build_coe(
                    teachers[sel_tid])
            st.rerun()
    else:
        t = teachers[sel_tid]
        st.download_button(
            f"⬇ Download COE — {t.get('name','')}",
            st.session_state[coe_key],
            f"COE_{sel_tid}.pdf",
            "application/pdf",
            key=f"dl_coe_{sel_tid}"
        )
        if st.button("🔄 Regenerate", key=f"regen_coe_{sel_tid}"):
            st.session_state.pop(coe_key, None); st.rerun()

    st.markdown("---")
    st.markdown("**Payslip (from processed payroll run)**")
    runs = st.session_state.payroll_runs
    if not runs:
        st.info("Process a payroll run first to generate individual payslips.")
        return
    ps1,ps2 = st.columns(2)
    sel_run_key = ps1.selectbox("Payroll Period",
                                 options=sorted(runs.keys(), reverse=True),
                                 format_func=lambda k: runs[k].get("cutoffLabel",k),
                                 key="ps_run")
    run_results = runs.get(sel_run_key,{}).get("results",{})
    sel_emp = ps2.selectbox("Staff Member",
                             options=list(run_results.keys()),
                             format_func=lambda tid: run_results[tid].get("teacherName",tid),
                             key="ps_emp") if run_results else None
    if sel_emp:
        ps_key = f"doc_ps_{sel_emp}_{sel_run_key}"
        if not st.session_state.get(ps_key):
            if st.button("📄 Generate Payslip", key="gen_ps_doc", use_container_width=True):
                with st.spinner("Generating…"):
                    _t = st.session_state.teachers.get(sel_emp, run_results[sel_emp])
                    st.session_state[ps_key] = build_payslip(
                        run_results[sel_emp]["p1"], run_results[sel_emp]["p2"], _t)
                st.rerun()
        else:
            st.download_button(
                f"⬇ Download Payslip — {run_results[sel_emp].get('teacherName','')}",
                st.session_state[ps_key],
                f"Payslip_{sel_emp}_{sel_run_key}.pdf",
                "application/pdf",
                key=f"dl_doc_ps_{caller}_{sel_emp}_{sel_run_key}"
            )


# ══════════════════════════════════════════════════════════════════════════════
#  PAYROLL PORTAL  (dedicated login: username=payroll)
# ══════════════════════════════════════════════════════════════════════════════
def page_payroll_portal():
    """Standalone payroll portal — accessed via payroll credentials."""
    _hr_load_all()

    # Auto-seed SEPI initial staff ONLY if:
    # 1. No teachers were loaded from KV (truly empty), AND
    # 2. KV is not configured (offline mode) OR explicitly not loaded yet
    # This prevents overwriting custom records added on another device.
    if not st.session_state.teachers:
        hdrs_check = _hr_headers()
        if not hdrs_check:
            # Offline mode — seed from defaults so the portal is usable
            for idx, staff in enumerate(SEPI_INITIAL_STAFF, 1):
                tid = f"EMP-{idx:03d}"
                teacher = {**staff, "teacherId": tid,
                           "enrolledOn": datetime.datetime.now().isoformat(),
                           "sssNo": "", "philHealthNo": "", "pagIbigNo": "",
                           "tin": "", "contact": "", "email": "", "address": "",
                           "ancillaryPay": staff.get("ancillaryPay", 0)}
                st.session_state.teachers[tid] = teacher
        # If KV IS configured but returned empty, do NOT auto-seed —
        # the user will add staff manually via the Staff Directory.

    with st.sidebar:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=60)
        st.markdown("<h3 style='color:#f48fb1;margin:0'>SEPI Payroll</h3>",
                    unsafe_allow_html=True)
        st.markdown("<p style='color:rgba(255,255,255,.5);font-size:11px'>Payroll Officer Portal</p>",
                    unsafe_allow_html=True)
        st.markdown("---")
        tab = st.radio("Navigate",
                       ["💰 Process Payroll", "📊 Payroll History",
                        "👥 Staff Directory", "📄 Documents", "🏖️ Leave"],
                       label_visibility="collapsed")
        st.markdown("---")
        if st.button("🔄 Sync from Cloud", key="payroll_sync", use_container_width=True,
                     help="Reload all records from Cloudflare KV"):
            st.session_state.hr_loaded = False
            st.rerun()
        if st.button("🚪 Logout"):
            logout(); st.rerun()

    if "💰" in tab:       _payroll_process_tab()
    elif "📊" in tab:    _payroll_history_tab()
    elif "👥" in tab:    _payroll_staff_tab()
    elif "📄" in tab:    _payroll_docs_tab()
    elif "🏖️" in tab:   _admin_leave_module()


# ── Process Payroll ────────────────────────────────────────────────────────────
def _payroll_process_tab():
    teachers = st.session_state.teachers
    st.title("💰 Process Semi-Monthly Payroll")
    st.caption("20 working days/month · 10 days per cut-off · Deductions applied on 2nd period")

    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    pc1,pc2,pc3 = st.columns(3)
    sel_yr  = pc1.selectbox("Year",  [2025,2026,2027],
                             index=1, key="pr2_year")
    sel_mo  = pc2.selectbox("Month", months,
                             index=datetime.date.today().month-1, key="pr2_month")
    mo_num  = months.index(sel_mo)+1
    ym_str  = f"{sel_yr}-{mo_num:02d}"
    period_label = f"{sel_mo} {sel_yr}"

    run_key = f"payroll:{ym_str}"
    existing = st.session_state.payroll_runs.get(run_key)

    if existing:
        st.success(f"✅ Payroll for **{period_label}** is already processed.")
        _show_monthly_payroll(existing, period_label, ym_str, caller="process")
        if st.button("🔄 Re-process this month"):
            del st.session_state.payroll_runs[run_key]
            st.rerun()
        return

    st.markdown(f"**Enter attendance data for {period_label}:**")
    st.markdown("---")

    # Sort teachers: teaching first, then non-teaching, alphabetically
    sorted_teachers = sorted(
        teachers.values(),
        key=lambda t: (0 if "Teaching" == t.get("employeeType","")[-8:] else 1,
                       t.get("lastName",""))
    )

    inputs_1 = {}  # 1st period inputs
    inputs_2 = {}  # 2nd period inputs

    st.markdown("#### 1st Period (Days 1–15, max 10 working days)")
    with st.container():
        # Header
        hc = st.columns([0.3,2.5,1,1,1])
        hc[0].markdown("**#**"); hc[1].markdown("**Name**")
        hc[2].markdown("**Days**"); hc[3].markdown("**Substitution (₱)**")
        hc[4].markdown("**Salary Loan**")

        for i, t in enumerate(sorted_teachers, 1):
            tid = t["teacherId"]
            rc  = st.columns([0.3,2.5,1,1,1])
            rc[0].markdown(f"{i}")
            ancil_t = float(t.get("ancillaryPay",0) or 0)
            basic_t = float(t.get("basicMonthlyPay",0) or 0)
            rc[1].markdown(f"**{t.get('name','')}**  \n*Basic: {basic_t:,.0f}  Ancillary: {ancil_t:,.0f}*")
            d1   = rc[2].number_input("", min_value=0.0, max_value=10.0, value=10.0,
                                       step=1.0, key=f"d1_{tid}_{ym_str}", label_visibility="collapsed")
            sub  = rc[3].number_input("", min_value=0.0, value=0.0,
                                       step=100.0, key=f"s1_{tid}_{ym_str}", label_visibility="collapsed")
            loan = rc[4].number_input("", min_value=0.0, value=0.0,
                                       step=100.0, key=f"ln_{tid}_{ym_str}", label_visibility="collapsed")
            inputs_1[tid] = {"days": d1, "substitution": sub, "salary_loan_store": loan}

    st.markdown("#### 2nd Period (Days 16–End, max 10 working days) + Deductions")
    st.caption("Government deductions (SSS/PhilHealth/Pag-IBIG) are auto-computed. Enter other deductions below.")
    with st.container():
        hc2 = st.columns([0.3, 2.2, 0.8, 0.9, 0.9, 0.9, 1.0])
        hc2[0].markdown("**#**")
        hc2[1].markdown("**Name**")
        hc2[2].markdown("**Days**")
        hc2[3].markdown("**Addl Pay**")
        hc2[4].markdown("**Salary Loan**")
        hc2[5].markdown("**Tuition Fee**")
        hc2[6].markdown("**Other Deduct.**")

        for i, t in enumerate(sorted_teachers, 1):
            tid = t["teacherId"]
            rc2 = st.columns([0.3, 2.2, 0.8, 0.9, 0.9, 0.9, 1.0])
            rc2[0].markdown(f"{i}")
            basic_t = float(t.get("basicMonthlyPay",0) or 0)
            ancil_t = float(t.get("ancillaryPay",0) or 0)
            rc2[1].markdown("**" + t.get("name","") + "** — PHP " + f"{basic_t:,.0f}")
            d2    = rc2[2].number_input("", min_value=0.0, max_value=10.0, value=10.0,
                                         step=1.0, key=f"d2_{tid}_{ym_str}", label_visibility="collapsed")
            addl  = rc2[3].number_input("", min_value=0.0, value=0.0,
                                         step=100.0, key=f"ap_{tid}_{ym_str}", label_visibility="collapsed")
            loan  = rc2[4].number_input("", min_value=0.0, value=0.0,
                                         step=100.0, key=f"sl_{tid}_{ym_str}", label_visibility="collapsed")
            tuit  = rc2[5].number_input("", min_value=0.0, value=0.0,
                                         step=100.0, key=f"tf_{tid}_{ym_str}", label_visibility="collapsed")
            othr  = rc2[6].number_input("", min_value=0.0, value=0.0,
                                         step=100.0, key=f"od_{tid}_{ym_str}", label_visibility="collapsed")
            inputs_2[tid] = {
                "days":              d2,
                "additional_pay":    addl,
                "salary_loan":       loan,
                "tuition_fee":       tuit,
                "other_deductions":  {"Other": othr} if othr else {},
            }

    st.markdown("---")
    if st.button("🚀 Process Payroll", use_container_width=True, key="run_pr2"):
        with st.spinner("Computing…"):
            results = {}
            for t in sorted_teachers:
                tid = t["teacherId"]
                p1_data = {
                    "period_type": "1st",
                    "period_label": f"{period_label} — 1st Period",
                    "year_month": ym_str,
                    "days_reported": inputs_1[tid]["days"],
                    "substitution": inputs_1[tid]["substitution"],
                    "salary_loan": 0,
                }
                p2_data = {
                    "period_type": "2nd",
                    "period_label": f"{period_label} — 2nd Period",
                    "year_month": ym_str,
                    "days_reported": inputs_2[tid]["days"],
                    "additional_pay": inputs_2[tid]["additional_pay"],
                    "salary_loan": inputs_1[tid]["salary_loan_store"] + inputs_2[tid].get("salary_loan", 0),
                    "tuition_fee": inputs_2[tid].get("tuition_fee", 0),
                    "other_deductions": inputs_2[tid].get("other_deductions", {}),
                }
                results[tid] = compute_monthly_payroll(t, p1_data, p2_data)
            payroll_run = {
                "runKey": run_key,
                "yearMonth": ym_str,
                "periodLabel": period_label,
                "processedOn": datetime.datetime.now().isoformat(),
                "results": results,
                "staffCount": len(results),
                "totalNet1": round(sum(r["totalNet1"] for r in results.values()), 2),
                "totalNet2": round(sum(r["totalNet2"] for r in results.values()), 2),
                "totalNetMonth": round(sum(r["totalNetMonth"] for r in results.values()), 2),
            }
            st.session_state.payroll_runs[run_key] = payroll_run
            _hr_save(run_key, payroll_run)
        st.success(f"✅ Payroll processed for {len(results)} staff members!")
        st.rerun()


def _show_monthly_payroll(run: dict, period_label: str, ym_str: str, caller: str = "main"):
    """Show processed payroll summary + generate printable files."""
    import pandas as pd
    results = run.get("results", {})

    # Summary metrics
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Staff",      run.get("staffCount",0))
    m2.metric("Total Net 1st", peso(run.get("totalNet1",0)))
    m3.metric("Total Net 2nd", peso(run.get("totalNet2",0)))
    m4.metric("Grand Total",   peso(run.get("totalNetMonth",0)))
    st.markdown("---")

    # Quick summary table
    rows=[]
    for mr in sorted(results.values(), key=lambda x: x.get("teacherName","")):
        rows.append({
            "Name":      mr.get("teacherName",""),
            "Basic Pay": peso(mr.get("basicMonthlyPay",0)),
            "1st Net":   peso(mr.get("totalNet1",0)),
            "2nd Net":   peso(mr.get("totalNet2",0)),
            "Monthly Net":peso(mr.get("totalNetMonth",0)),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("---")

    # ── Generate printable files ──────────────────────────────────────────────
    st.markdown("**📄 Generate Printable Documents**")
    gc1,gc2 = st.columns(2)

    # Payroll Summary Register
    summary_key = f"pr_summary_{caller}_{ym_str}"
    if not st.session_state.get(summary_key):
        if gc1.button("📊 Generate Payroll Register",
                       key=f"gen_reg_{caller}_{ym_str}", use_container_width=True):
            with st.spinner("Building register…"):
                mr_list = sorted(results.values(),
                                 key=lambda x: (
                                     0 if "Non-teaching" not in x.get("employeeType","") else 1,
                                     x.get("teacherName","")
                                 ))
                st.session_state[summary_key] = build_payroll_summary(
                    mr_list, ym_str, period_label)
            st.rerun()
    else:
        gc1.download_button("⬇ Download Payroll Register",
                             st.session_state[summary_key],
                             f"PayrollRegister_{ym_str}.pdf",
                             "application/pdf",
                             use_container_width=True,
                             key=f"dl_reg_{caller}_{ym_str}")

    # All Payslips
    all_ps_key = f"pr_allps_{caller}_{ym_str}"
    if not st.session_state.get(all_ps_key):
        if gc2.button("📋 Generate All Payslips",
                       key=f"gen_all_ps_{caller}_{ym_str}", use_container_width=True):
            with st.spinner("Generating payslips…"):
                from reportlab.platypus import SimpleDocTemplate
                from pypdf import PdfWriter
                import io as _io
                writer = PdfWriter()
                for mr in sorted(results.values(), key=lambda x: x.get("teacherName","")):
                    tid = mr["p1"]["teacherId"]
                    t   = st.session_state.teachers.get(tid, {})
                    ps  = build_payslip(mr["p1"], mr["p2"], t)
                    from pypdf import PdfReader
                    reader = PdfReader(_io.BytesIO(ps))
                    for page in reader.pages:
                        writer.add_page(page)
                merged_buf = _io.BytesIO()
                writer.write(merged_buf)
                st.session_state[all_ps_key] = merged_buf.getvalue()
            st.rerun()
    else:
        gc2.download_button("⬇ Download All Payslips",
                             st.session_state[all_ps_key],
                             f"AllPayslips_{ym_str}.pdf",
                             "application/pdf",
                             use_container_width=True,
                             key=f"dl_all_ps_{caller}_{ym_str}")

    # Individual payslips
    st.markdown("**Individual Payslips:**")
    ps_cols = st.columns(4)
    for i, mr in enumerate(sorted(results.values(), key=lambda x: x.get("teacherName",""))):
        tid = mr["p1"]["teacherId"]
        t   = st.session_state.teachers.get(tid, {})
        ps_key = f"ind_ps_{tid}_{ym_str}"
        col = ps_cols[i % 4]
        short_name = mr.get("teacherName","").split(",")[0]
        if not st.session_state.get(ps_key):
            if col.button(f"📄 {short_name}", key=f"gips_{tid}_{ym_str}",
                          use_container_width=True):
                st.session_state[ps_key] = build_payslip(mr["p1"], mr["p2"], t)
                st.rerun()
        else:
            col.download_button(f"⬇ {short_name}",
                                st.session_state[ps_key],
                                f"Payslip_{tid}_{ym_str}.pdf",
                                "application/pdf",
                                use_container_width=True,
                                key=f"dlips_{tid}_{ym_str}")


# ── Payroll History Tab ────────────────────────────────────────────────────────
def _payroll_history_tab():
    st.title("📊 Payroll History")
    runs = st.session_state.payroll_runs
    if not runs:
        st.info("No payroll runs yet."); return
    for key in sorted(runs.keys(), reverse=True):
        run = runs[key]
        lbl = run.get("periodLabel","")
        with st.expander(f"**{lbl}** — {run.get('staffCount',0)} staff | "
                          f"Total Net: {peso(run.get('totalNetMonth',0))} | "
                          f"Processed: {run.get('processedOn','')[:10]}"):
            _show_monthly_payroll(run, lbl, run.get("yearMonth",""), caller=f"hist_{key}")


# ── Staff Directory Tab ────────────────────────────────────────────────────────
def _payroll_staff_tab():
    _hr_staff_directory()  # reuse admin HR staff directory


# ── Documents Tab ──────────────────────────────────────────────────────────────
def _payroll_docs_tab():
    _hr_documents()  # reuse admin HR documents tab


# ══════════════════════════════════════════════════════════════════════════════
#  LEAVE MANAGEMENT MODULE
# ══════════════════════════════════════════════════════════════════════════════
LEAVE_TYPES_LIST = [
    ("SIL",              "Service Incentive Leave (SIL)",        "Earned at 1 day/month, max 10/SY"),
    ("Sick",             "Sick Leave",                           "Deducted from SIL credit"),
    ("Personal",         "Personal Leave",                       "Deducted from SIL credit"),
    ("Vacation",         "Vacation Leave",                       "Without pay"),
    ("Maternity",        "Maternity Leave (RA 11210)",           "With pay, attach hospital documents"),
    ("SoloParent",       "Solo Parent Leave (RA 8972)",          "Attach valid Solo Parent ID"),
    ("VAWC",             "VAWC Leave (RA 9262)",                 "For women victims of violence"),
    ("MagnaCartaWomen",  "Magna Carta for Women Leave (RA 9710)","Attach medical certificate"),
    ("Paternity",        "Paternity Leave (RA 8187)",            "7 days, first 4 deliveries"),
    ("Others",           "Others",                              "Specify in remarks"),
]
LEAVE_KEY_TO_LABEL = {k: lbl for k, lbl, _ in LEAVE_TYPES_LIST}

# SIL: 1 day per month worked, max 10 days per school year
SIL_RATE_PER_MONTH = 1.0
SIL_MAX_PER_SY     = 10.0


def _get_sil_balance(tid: str) -> float:
    """Compute current SIL balance from leave history."""
    leaves = st.session_state.get("leave_records", {})
    teacher_leaves = [l for l in leaves.values() if l.get("teacherId") == tid]
    sil_earned   = float(st.session_state.teachers.get(tid, {}).get("silAccumulated", 0) or 0)
    sil_used     = sum(
        float(l.get("totalDays", 0) or 0)
        for l in teacher_leaves
        if l.get("leaveType") in ("SIL", "Sick", "Personal") and l.get("status") == "Approved"
    )
    return max(0.0, round(sil_earned - sil_used, 2))


def _admin_leave_module():
    """Leave management tab — accessible from both Admin and Payroll portals."""
    _hr_load_all()
    # Ensure leave_records session state exists
    if "leave_records" not in st.session_state:
        st.session_state.leave_records = {}
    if "leave_loaded" not in st.session_state:
        st.session_state.leave_loaded = False
    # Load from KV once
    if not st.session_state.leave_loaded:
        import requests, json
        hdrs = _hr_headers()
        if hdrs:
            acct = st.secrets.get("CF_ACCOUNT_ID","")
            base = f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{HR_KV_NS}"
            try:
                r = requests.get(f"{base}/keys", headers=hdrs,
                                 params={"prefix":"leave:","limit": 10000}, timeout=10)
                if r.status_code == 200:
                    for item in r.json().get("result",[]):
                        rv = requests.get(f"{base}/values/{item['name']}", headers=hdrs, timeout=8)
                        if rv.status_code == 200:
                            st.session_state.leave_records[item["name"]] = rv.json()
            except Exception: pass
        st.session_state.leave_loaded = True

    teachers = st.session_state.teachers
    leave_tabs = st.tabs(["📋 Leave Applications", "➕ File Leave", "📊 SIL Tracker", "🖨 Print Form"])

    # ── TAB 1: Leave Applications ─────────────────────────────────────────────
    with leave_tabs[0]:
        st.markdown("#### All Leave Applications")
        records = st.session_state.leave_records
        if not records:
            st.info("No leave applications filed yet.")
        else:
            import pandas as pd
            rows = []
            for k, l in sorted(records.items(), reverse=True):
                rows.append({
                    "ID":          k.replace("leave:",""),
                    "Employee":    l.get("teacherName",""),
                    "Leave Type":  LEAVE_KEY_TO_LABEL.get(l.get("leaveType",""), l.get("leaveType","")),
                    "Date Filed":  l.get("dateFiled",""),
                    "From":        l.get("dateFrom",""),
                    "To":          l.get("dateTo",""),
                    "Days":        l.get("totalDays",""),
                    "Status":      l.get("status","Pending"),
                    "Reason":      l.get("reason",""),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Approve / Disapprove
            st.markdown("**Update Status:**")
            sel_leave = st.selectbox("Select application",
                                      options=list(records.keys()),
                                      format_func=lambda k: f"{records[k].get('teacherName','')} — {records[k].get('dateFiled','')} — {LEAVE_KEY_TO_LABEL.get(records[k].get('leaveType',''),'')}",
                                      key="sel_leave_update")
            lc1,lc2,lc3 = st.columns(3)
            new_lstat = lc1.selectbox("New Status", ["Pending","Approved","Disapproved"],
                                       index=["Pending","Approved","Disapproved"].index(
                                           records[sel_leave].get("status","Pending")),
                                       key="leave_new_stat")
            l_remarks = lc2.text_input("Remarks", key="leave_remarks_upd")
            if lc3.button("✅ Update", key="leave_upd_btn", use_container_width=True):
                st.session_state.leave_records[sel_leave]["status"]  = new_lstat
                if l_remarks:
                    st.session_state.leave_records[sel_leave]["remarks"] = l_remarks
                _hr_save(sel_leave, st.session_state.leave_records[sel_leave])
                st.success("Updated."); st.rerun()

    # ── TAB 2: File Leave ─────────────────────────────────────────────────────
    with leave_tabs[1]:
        st.markdown("#### File a Leave Application")
        with st.form("file_leave_form", clear_on_submit=True):
            fl1,fl2 = st.columns(2)
            sel_emp = fl1.selectbox("Employee *",
                                     options=sorted(teachers.keys(),
                                                    key=lambda t: teachers[t].get("lastName","")),
                                     format_func=lambda t: teachers[t].get("name",""),
                                     key="fl_emp")
            fl_date = fl2.date_input("Date Filed *", value=datetime.date.today(), key="fl_date")
            lt_options = [k for k,_,_ in LEAVE_TYPES_LIST]
            lt_labels  = [lbl for _,lbl,_ in LEAVE_TYPES_LIST]
            fl_ltype = st.selectbox("Leave Type *",
                                     options=lt_options,
                                     format_func=lambda k: LEAVE_KEY_TO_LABEL.get(k,k),
                                     key="fl_ltype")
            fl_other = ""
            if fl_ltype == "Others":
                fl_other = st.text_input("Specify Other Leave Type", key="fl_other")
            fl_desc = [d for k,_,d in LEAVE_TYPES_LIST if k==fl_ltype]
            if fl_desc:
                st.caption(f"ℹ️ {fl_desc[0]}")
            ldc1,ldc2,ldc3 = st.columns(3)
            fl_from   = ldc1.date_input("From *", value=datetime.date.today(), key="fl_from")
            fl_to     = ldc2.date_input("To *",   value=datetime.date.today(), key="fl_to")
            fl_days   = ldc3.number_input("Total Days *", min_value=0.5, step=0.5, value=1.0, key="fl_days")
            fl_reason = st.text_area("Reason / Remarks", key="fl_reason", height=70)
            fl_submit = st.form_submit_button("📥 Submit Leave Application", use_container_width=True)

            if fl_submit:
                import uuid
                lid = f"leave:{datetime.date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
                teacher = teachers[sel_emp]
                sil_bal = _get_sil_balance(sel_emp)
                record = {
                    "leaveId":     lid,
                    "teacherId":   sel_emp,
                    "teacherName": teacher.get("name",""),
                    "leaveType":   fl_ltype,
                    "leaveTypeOther": fl_other,
                    "dateFiled":   str(fl_date),
                    "dateFrom":    str(fl_from),
                    "dateTo":      str(fl_to),
                    "totalDays":   fl_days,
                    "reason":      fl_reason,
                    "status":      "Pending",
                    "remarks":     "",
                    "silBalanceBefore": sil_bal,
                }
                st.session_state.leave_records[lid] = record
                _hr_save(lid, record)
                st.success(f"✅ Leave filed for {teacher.get('name','')} — {LEAVE_KEY_TO_LABEL.get(fl_ltype,'')} | {fl_days} day/s")
                st.rerun()

    # ── TAB 3: SIL Tracker ────────────────────────────────────────────────────
    with leave_tabs[2]:
        st.markdown("#### SIL (Service Incentive Leave) Tracker")
        st.caption(f"Rate: {SIL_RATE_PER_MONTH} day per month worked | Maximum: {SIL_MAX_PER_SY} days per school year")
        import pandas as pd

        # Add SIL credits
        st.markdown("**Add SIL Credits (monthly):**")
        sil1,sil2,sil3 = st.columns(3)
        sil_emp = sil1.selectbox("Employee",
                                  options=sorted(teachers.keys(),
                                                 key=lambda t: teachers[t].get("lastName","")),
                                  format_func=lambda t: teachers[t].get("name",""),
                                  key="sil_emp")
        sil_add = sil2.number_input("Days to Add", min_value=0.5, max_value=1.0,
                                     value=1.0, step=0.5, key="sil_add")
        if sil3.button("➕ Add SIL", key="sil_add_btn", use_container_width=True):
            current = float(st.session_state.teachers[sil_emp].get("silAccumulated",0) or 0)
            new_sil = min(round(current + sil_add, 2), SIL_MAX_PER_SY)
            st.session_state.teachers[sil_emp]["silAccumulated"] = new_sil
            _hr_save(f"teacher:{sil_emp}", st.session_state.teachers[sil_emp])
            st.success(f"SIL credited. New balance: {new_sil} days"); st.rerun()

        st.markdown("---")

        # SIL summary table
        sil_rows = []
        for tid, t in sorted(teachers.items(), key=lambda x: x[1].get("lastName","")):
            accumulated = float(t.get("silAccumulated",0) or 0)
            used        = sum(float(l.get("totalDays",0) or 0)
                              for l in st.session_state.leave_records.values()
                              if l.get("teacherId")==tid
                              and l.get("leaveType") in ("SIL","Sick","Personal")
                              and l.get("status")=="Approved")
            balance     = max(0.0, round(accumulated - used, 2))
            sil_rows.append({
                "Employee":    t.get("name",""),
                "Position":    t.get("position",""),
                "SIL Earned":  accumulated,
                "SIL Used":    round(used,2),
                "SIL Balance": balance,
                "Status":      "⚠️ No credit" if accumulated==0 else ("✅ OK" if balance>0 else "❌ Exhausted"),
            })
        st.dataframe(pd.DataFrame(sil_rows), use_container_width=True, hide_index=True,
                     column_config={
                         "SIL Earned":  st.column_config.NumberColumn(format="%.1f days"),
                         "SIL Used":    st.column_config.NumberColumn(format="%.1f days"),
                         "SIL Balance": st.column_config.NumberColumn(format="%.1f days"),
                     })

    # ── TAB 4: Print Leave Form ───────────────────────────────────────────────
    with leave_tabs[3]:
        st.markdown("#### Generate Printable Leave Form")
        records = st.session_state.leave_records
        if records:
            st.markdown("**From filed applications:**")
            sel_lp = st.selectbox("Select application to print",
                                   options=list(records.keys()),
                                   format_func=lambda k: f"{records[k].get('teacherName','')} — {records[k].get('dateFiled','')} — {LEAVE_KEY_TO_LABEL.get(records[k].get('leaveType',''),'')}",
                                   key="sel_leave_print")
            lp_key = f"lp_{sel_lp}"
            if not st.session_state.get(lp_key):
                if st.button("🖨 Generate Leave Form PDF", key="gen_lp", use_container_width=True):
                    r = records[sel_lp]
                    t = teachers.get(r.get("teacherId",""),{})
                    sil_bal = _get_sil_balance(r.get("teacherId",""))
                    leave_dict = {
                        "name":          r.get("teacherName",""),
                        "date_filed":    r.get("dateFiled",""),
                        "leave_type":    r.get("leaveType",""),
                        "leave_type_other": r.get("leaveTypeOther",""),
                        "dates":         [{"from":r.get("dateFrom",""),
                                           "to":r.get("dateTo",""),
                                           "days":r.get("totalDays",""),
                                           "reason":r.get("reason","")}],
                        "sil_month":     "",
                        "sil_earned":    t.get("silAccumulated",""),
                        "sil_used":      "",
                        "sil_remaining": sil_bal,
                        "remarks":       r.get("remarks",""),
                        "approved":      (True if r.get("status")=="Approved"
                                          else (False if r.get("status")=="Disapproved"
                                                else None)),
                    }
                    st.session_state[lp_key] = build_leave_form(leave_dict)
                    st.rerun()
            else:
                r = records[sel_lp]
                st.download_button("⬇ Download Leave Form PDF",
                                   st.session_state[lp_key],
                                   f"LeaveForm_{r.get('teacherName','').replace(' ','_')}_{r.get('dateFiled','')}.pdf",
                                   "application/pdf",
                                   use_container_width=True,
                                   key=f"dl_{lp_key}")

        st.markdown("---")
        st.markdown("**Or generate a blank form:**")
        if st.button("🖨 Blank Leave Form", key="gen_blank_lp", use_container_width=True):
            blank = {
                "name":"","date_filed":"","leave_type":"","leave_type_other":"",
                "dates":[],"sil_month":"","sil_earned":"","sil_used":"","sil_remaining":"",
                "remarks":"","approved":None,
            }
            st.session_state["blank_leave_pdf"] = build_leave_form(blank)
            st.rerun()
        if st.session_state.get("blank_leave_pdf"):
            st.download_button("⬇ Download Blank Form",
                               st.session_state["blank_leave_pdf"],
                               "SEPI_LeaveForm_Blank.pdf","application/pdf",
                               key="dl_blank_lp")
