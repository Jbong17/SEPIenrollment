"""
SEPI Database Layer — Cloudflare KV Persistence
================================================
All student records are stored in Cloudflare KV so they survive
Streamlit hibernation, restarts, and redeployments.

KV Key scheme:
  student:{TRACKING_ID}   →  full student JSON record
  index:all               →  list of all tracking IDs

Requires Streamlit Secrets:
  CF_API_TOKEN  = "your-cloudflare-api-token"
  CF_ACCOUNT_ID = "your-cloudflare-account-id"

How to get those values:
  CF_ACCOUNT_ID → Cloudflare dashboard → right sidebar → Account ID
  CF_API_TOKEN  → Cloudflare dashboard → My Profile → API Tokens
                  → Create Token → "Edit Cloudflare Workers" template
                  (needs KV:Read + KV:Write + Account:Read permissions)
"""

import json, requests, streamlit as st
from typing import Optional

KV_NAMESPACE_ID = "7d035b4c332449c5993651ab62478609"
KV_BASE_URL     = "https://api.cloudflare.com/client/v4"


def _headers() -> Optional[dict]:
    """Return auth headers, or None if not configured."""
    try:
        token = st.secrets["CF_API_TOKEN"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    except Exception:
        return None


def _account_id() -> Optional[str]:
    try:
        return st.secrets["CF_ACCOUNT_ID"]
    except Exception:
        return None


def _kv_url(key: str = "") -> str:
    acct = _account_id()
    base = f"{KV_BASE_URL}/accounts/{acct}/storage/kv/namespaces/{KV_NAMESPACE_ID}"
    return f"{base}/values/{key}" if key else f"{base}/keys"


def is_configured() -> bool:
    """True if Cloudflare credentials are available in Streamlit Secrets."""
    return _headers() is not None and _account_id() is not None


# ── Read ──────────────────────────────────────────────────────────────────────

def get_student(tracking_id: str) -> Optional[dict]:
    """Fetch a single student record from KV."""
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
    """
    Load all student records from KV into a dict keyed by trackingId.
    Falls back to {} if credentials not configured or on any error.
    """
    hdrs = _headers()
    if not hdrs:
        return {}
    try:
        # 1. Get the list of all keys
        r = requests.get(
            _kv_url(),
            headers=hdrs,
            params={"prefix": "student:", "limit": 1000},
            timeout=10
        )
        if r.status_code != 200:
            return {}

        keys_data = r.json()
        keys = [item["name"] for item in keys_data.get("result", [])]

        # 2. Fetch each student record
        students = {}
        for key in keys:
            tracking_id = key.replace("student:", "")
            record = get_student(tracking_id)
            if record:
                students[tracking_id] = record

        return students

    except Exception:
        return {}


# ── Write ─────────────────────────────────────────────────────────────────────

def save_student(student: dict) -> bool:
    """
    Save / update a single student record to KV.
    Returns True on success.
    """
    hdrs = _headers()
    if not hdrs:
        return False
    tid = student.get("trackingId")
    if not tid:
        return False
    try:
        r = requests.put(
            _kv_url(f"student:{tid}"),
            headers={**hdrs, "Content-Type": "application/json"},
            data=json.dumps(student, default=str),
            timeout=8
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def delete_student(tracking_id: str) -> bool:
    """Delete a student record from KV."""
    hdrs = _headers()
    if not hdrs:
        return False
    try:
        r = requests.delete(_kv_url(f"student:{tracking_id}"), headers=hdrs, timeout=8)
        return r.status_code in (200, 204)
    except Exception:
        return False


# ── Streamlit helpers — call these instead of touching session_state directly ─

def db_load_students_into_state():
    """
    On app startup: load all students from KV into st.session_state.students.
    If KV not configured, keeps whatever is already in session_state.
    """
    if not is_configured():
        return  # graceful fallback — session_state already initialised to {}

    # Only load once per session (avoid re-fetching on every rerun)
    if st.session_state.get("_db_loaded"):
        return

    with st.spinner("Loading student records…"):
        students = load_all_students()

    # Merge KV data into session state
    # (session_state records take priority if they're newer — same session edits)
    for tid, record in students.items():
        if tid not in st.session_state.students:
            st.session_state.students[tid] = record

    st.session_state["_db_loaded"] = True


def db_save(student: dict):
    """
    Save student to BOTH session_state AND Cloudflare KV.
    This is the single write function to call everywhere.
    """
    tid = student.get("trackingId")
    if not tid:
        return
    st.session_state.students[tid] = student
    if is_configured():
        save_student(student)


def db_update_field(tracking_id: str, **fields):
    """
    Update specific fields on a student record and persist.
    Usage: db_update_field("SEPI-ABC", status="approved", paidAmount=5000)
    """
    s = st.session_state.students.get(tracking_id)
    if not s:
        return
    s.update(fields)
    st.session_state.students[tracking_id] = s
    if is_configured():
        save_student(s)
