"""
SEPI Database Layer — Cloudflare KV Persistence
================================================
Enrollment records stored in SEPI_Enrollment_Database KV namespace.
Key format: student:{TRACKING_ID}

IMPORTANT: Uses Content-Type: text/plain for KV writes (CF KV requirement).
"""

import json, requests, streamlit as st
from typing import Optional

KV_NAMESPACE_ID = "7d035b4c332449c5993651ab62478609"
KV_BASE_URL     = "https://api.cloudflare.com/client/v4"


def _headers() -> Optional[dict]:
    try:
        token = st.secrets["CF_API_TOKEN"]
        if not token:
            return None
        return {
            "Authorization": f"Bearer {token}",
        }
    except Exception:
        return None


def _account_id() -> Optional[str]:
    try:
        aid = st.secrets["CF_ACCOUNT_ID"]
        return aid if aid else None
    except Exception:
        return None


def _kv_url(key: str = "") -> str:
    acct = _account_id()
    base = f"{KV_BASE_URL}/accounts/{acct}/storage/kv/namespaces/{KV_NAMESPACE_ID}"
    return f"{base}/values/{key}" if key else f"{base}/keys"


def is_configured() -> bool:
    return _headers() is not None and _account_id() is not None


def verify_connection() -> tuple:
    """
    Test actual KV connectivity. Returns (ok: bool, message: str).
    Call this from the dashboard to show real connection status.
    """
    hdrs = _headers()
    if not hdrs:
        return False, "CF_API_TOKEN not set in Streamlit Secrets"
    acct = _account_id()
    if not acct:
        return False, "CF_ACCOUNT_ID not set in Streamlit Secrets"
    try:
        r = requests.get(
            f"{KV_BASE_URL}/accounts/{acct}/storage/kv/namespaces/{KV_NAMESPACE_ID}/keys",
            headers=hdrs,
            params={"limit": 10},
            timeout=8
        )
        if r.status_code == 200:
            return True, f"Connected — {r.json().get('result_info', {}).get('count', '?')} records"
        elif r.status_code == 401:
            return False, "Invalid API token — update CF_API_TOKEN in Streamlit Secrets"
        elif r.status_code == 403:
            return False, "Token lacks KV permissions — recreate token with Workers KV:Edit"
        else:
            return False, f"KV error {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, f"Network error: {str(e)[:100]}"


def get_student(tracking_id: str) -> Optional[dict]:
    hdrs = _headers()
    if not hdrs:
        return None
    try:
        r = requests.get(_kv_url(f"student:{tracking_id}"), headers=hdrs, timeout=8)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def load_all_students() -> dict:
    hdrs = _headers()
    if not hdrs:
        return {}
    try:
        r = requests.get(
            _kv_url(),
            headers=hdrs,
            params={"prefix": "student:", "limit": 1000},
            timeout=12
        )
        if r.status_code != 200:
            return {}
        keys = [item["name"] for item in r.json().get("result", [])]
        students = {}
        for key in keys:
            tid = key.replace("student:", "")
            r2  = requests.get(_kv_url(key), headers=hdrs, timeout=8)
            if r2.status_code == 200:
                try:
                    students[tid] = r2.json()
                except Exception:
                    pass
        return students
    except Exception:
        return {}


def save_student(student: dict) -> bool:
    hdrs = _headers()
    if not hdrs:
        return False
    tid = student.get("trackingId")
    if not tid:
        return False
    try:
        # CF KV requires text/plain for value writes
        write_headers = {**hdrs, "Content-Type": "text/plain"}
        r = requests.put(
            _kv_url(f"student:{tid}"),
            headers=write_headers,
            data=json.dumps(student, default=str),
            timeout=10
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def delete_student(tracking_id: str) -> bool:
    hdrs = _headers()
    if not hdrs:
        return False
    try:
        r = requests.delete(_kv_url(f"student:{tracking_id}"), headers=hdrs, timeout=8)
        return r.status_code in (200, 204)
    except Exception:
        return False


def db_load_students_into_state(force: bool = False):
    """Load students from KV into session state.
    If force=True, clears existing state and reloads everything from KV.
    """
    if not is_configured():
        return
    if st.session_state.get("_db_loaded") and not force:
        return
    if force:
        st.session_state.students = {}
    students = load_all_students()
    for tid, record in students.items():
        st.session_state.students[tid] = record
    st.session_state["_db_loaded"] = True


def db_save(student: dict):
    tid = student.get("trackingId")
    if not tid:
        return
    st.session_state.students[tid] = student
    if is_configured():
        ok = save_student(student)
        if not ok:
            st.warning(f"⚠️ Could not save {tid} to cloud. Check Cloudflare credentials in Streamlit Secrets.", icon="☁️")


def db_update_field(tracking_id: str, **fields):
    s = st.session_state.students.get(tracking_id)
    if not s:
        return
    s.update(fields)
    st.session_state.students[tracking_id] = s
    if is_configured():
        save_student(s)
