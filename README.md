# SEPI Enrollment & HR System

**School of Everlasting Pearl, Inc. (SEPI)**
#66 Siruna Village Phase III, Mambugan, Antipolo City
SY 2026–2027

---

## Overview

A full-stack school management system built with **Streamlit** and deployed on **Streamlit Community Cloud**. All data persists in **Cloudflare KV** — accessible from any device simultaneously. Covers student enrollment, HR/payroll, leave management, and financial reporting for Kinder through Junior High School.

---

## Live App & Repository

- **Deployed at:** *(your Streamlit Cloud URL)*
- **GitHub Repo:** `Jbong17/SEPIenrollment`
- **Branch:** `main`

---

## File Structure

```
SEPIenrollment/
├── app.py              # Main application — all UI, routing, portals
├── fees.py             # Fee schedule, discount policy, ESC logic
├── pdf_gen.py          # Enrollment Form, Contract, SOA, Promissory Note
├── payroll.py          # Payroll engine, contribution tables, staff roster
├── hr.py               # HR & Payroll UI — staff, payroll, leave modules
├── hr_pdf.py           # Payslip, Payroll Register, COE, Leave Form PDFs
├── db.py               # Cloudflare KV persistence layer (enrollment)
├── requirements.txt    # Python dependencies
├── sepi_logo.jpg       # School logo (used in all PDFs and portal header)
└── README.md           # This file
```

---

## Portals & Credentials

| Portal | Login Tab | Username | Default Password |
|---|---|---|---|
| Student Portal | Student Portal | *(Tracking ID)* | — |
| Admin Portal | Admin Portal | `admin` | `sepi2026` |
| Payroll Portal | Admin Portal | `payroll` | `payroll2024` |

> **Change passwords in Streamlit Secrets after first deploy.**

---

## Streamlit Secrets

Go to: **share.streamlit.io → your app → ⋮ → Settings → Secrets**

```toml
CF_ACCOUNT_ID    = "dffb0b9be393c741552aa373a3e2d494"
CF_API_TOKEN     = "your-cloudflare-api-token"
ADMIN_PASSWORD   = "sepi2026"
PAYROLL_PASSWORD = "payroll2024"
GMAIL_APP_PASSWORD = ""   # optional — enables OTP password reset
```

> ⚠️ **Security:** Never share your `CF_API_TOKEN` publicly. Regenerate it at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) if exposed. Required permission: **Workers KV Storage: Edit**.

---

## Cloudflare KV Namespaces

| Namespace | ID | Purpose |
|---|---|---|
| `SEPI_Enrollment_Database` | `7d035b4c332449c5993651ab62478609` | Student enrollment records |
| `SEPI_HR_Payroll` | `dfe32c5ff0924b199cea8e36f588f6c4` | HR, payroll, leave records |

**Key format:**

| Namespace | Key | Content |
|---|---|---|
| Enrollment | `student:{SEPI-XXXXXX}` | Student enrollment record (JSON) |
| HR | `teacher:{EMP-XXXXXX}` | Teacher 201 file (JSON) |
| HR | `payroll:{YYYY-MM-N}` | Payroll run (JSON) |
| HR | `leave:{YYYYMMDD-XXXXXX}` | Leave application (JSON) |

> **Data safety:** Updating files on GitHub never affects Cloudflare KV. Your records survive redeployments, app hibernation, and code updates.

---

## Admin Portal

Login: `admin` / `sepi2026`

### Navigation Tabs

| Tab | Purpose |
|---|---|
| 📊 Dashboard | Enrollment stats, 🟢 KV connection status, **🔄 Sync All** button |
| 👥 Students | Search/filter, inline SOA, payment recording, status update, **✏️ Edit Info**, PDF generation, delete |
| 🗂️ Inventory | Per-grade roster with Excel/CSV export |
| 📈 Reports | Monthly collection chart, by-level breakdown, collection rate analysis, export |
| 👨‍🏫 HR & Payroll | Staff Directory, Process Payroll, Payroll History, Documents, Leave Management |
| ☁️ Cloudflare KV | Namespace info, schema reference |
| ⚙️ Settings | Change admin password (OTP via Gmail if configured) |

### Quick Actions (sidebar)
- **📋 New Enrollment** — 6-step enrollment form
- **💳 Update SOA / Payment** — record payments by Tracking ID

---

## Enrollment System

### 6-Step Enrollment Form

| Step | Content |
|---|---|
| 1 | Personal Information |
| 2 | Academic (level, grade, LRN, fee preview) |
| 3 | Parent / Guardian Information |
| 4 | Documents Checklist |
| 5 | Scholarship / Discount + ESC Grantee |
| 6 | Review & Submit + Payment + **Conditional Admission / Promissory Note** |

### Conditional Admission & Promissory Note

If a student has an outstanding balance:
- Check **"Student is conditionally admitted"** on Step 6
- System determines note type automatically:
  - Balance **≤ PHP 15,000** → **Regular Promissory Note**
  - Balance **> PHP 15,000** → **Notarized Promissory Note**
- Edit the 3-installment payment schedule (due dates and amounts)
- Generates a separate PDF with signature lines and — for notarized — a full notary acknowledgement block

### Documents Generated (Long Bond 8.5″ × 13″)

| Document | Contents |
|---|---|
| Enrollment Form | 7 sections: personal info, academic, family, documents checklist, discount/ESC |
| Enrollment Contract | 8-article legal agreement |
| Statement of Account | Sections A/B/C with discount and ESC line items, payment history |
| Promissory Note | Regular or Notarized based on balance threshold |

---

## Fee Schedule — SY 2026–2027

| Level | Reg Fee | Tuition | Misc | Total |
|---|---|---|---|---|
| Kinder / Preschool | ₱6,000 | ₱10,043 | ₱10,750 | **₱26,793** |
| Elementary Gr 1–3 | ₱6,000 | ₱13,283 | ₱10,750 | **₱30,033** |
| Elementary Gr 4–6 | ₱6,000 | ₱15,703 | ₱10,750 | **₱32,453** |
| JHS Gr 7–10 | ₱6,000 | ₱21,150 | ₱10,750 | **₱37,900** |

*Misc: Library ₱500 · Medical/Dental ₱2,000 · Test Kits ₱1,250 · Energy ₱2,000 · Books/LMS ₱5,000*

---

## Discount Policy

One discount per student · Applied to tuition fee only · Highest applicable granted

| Discount | Rate |
|---|---|
| Early Enrollment | 5% |
| Sibling Discount | 10% |
| Solo Parent (RA 8972) | 10% |
| Indigenous Peoples | 15% |
| Senior Citizen Guardian | 10% |
| Employee Privilege | 20–50% |
| Referral Incentive | 5% |
| Alumni Legacy | 5–10% |
| Student-Leader / Merit | 5–10% |
| **ESC Government Subsidy** | **₱9,000 fixed** (overrides all school discounts) |

> ESC approval often comes in Q2. Use **✏️ Edit Info** on the student record to toggle ESC status anytime — fees recalculate and save automatically.

---

## Editing Student Records

Each student in Admin → Students has an **✏️ Edit Info** tab with:
- **ESC & Discount** — update ESC status, change discount type
- **Personal Details** — name, contact, email, address
- **Academic** — level, grade, LRN

All changes recalculate fees and save to Cloudflare KV immediately.

---

## Reports & Analytics

Four tabs in the 📈 Reports section:

| Tab | Content |
|---|---|
| 📅 Monthly Collection | Collections by month, running total, % of total due, bar chart |
| 🏫 By Level | Collection per grade level and per grade |
| 📊 Collection Rate | Overall rate gauge (🟢/🟡/🔴), fully paid vs partial vs unpaid |
| 📤 Export | JSON and CSV export of all records |

---

## Payroll Portal

Login: `payroll` / `payroll2024`

### Computation Rates (SEPI-specific)

| Contribution | Rate | Cap |
|---|---|---|
| SSS | 5% of basic | — |
| PhilHealth | 2.5% of basic | — |
| Pag-IBIG | 2% of basic | ₱200/month |

**Structure:**
- 20 working days/month · 10 days per cut-off
- **1st Period:** Basic pay + substitution pay (no deductions)
- **2nd Period:** Basic + ancillary pay + additional pay − all deductions
- Government deductions on 2nd period only
- Per-teacher `hasGovDeductions` flag (false = exempt)

### Deductions per Payroll Run

Entered per teacher on the payroll form:
- Salary Loan / Cash Advance
- Tuition Fee
- Other Deduction
- Government contributions (SSS, PhilHealth, Pag-IBIG) — auto-computed

### Payroll Portal Tabs

| Tab | Purpose |
|---|---|
| 💰 Process Payroll | Select period, enter attendance + deductions, process |
| 📊 Payroll History | All past runs, re-downloadable, **🗑️ delete option** |
| 👥 Staff Directory | 201 file, add/edit/delete staff, photo upload |
| 📄 Documents | Generate individual payslip or COE |
| 🏖️ Leave | File leave, SIL tracker, print leave form |

### Documents Generated

| Document | Format | Notes |
|---|---|---|
| Individual Payslip | Letter | Salary, ancillary, deductions, net pay per period |
| All Payslips (merged) | Single PDF | All staff, ready to print |
| Payroll Register | Landscape long bond | Matches official SEPI format |
| Certificate of Employment | Letter | Blank signature lines, auto-dated |
| Application for Leave Form | Letter | Matches official SEPI form |

### Payslip Format

```
School of Everlasting Pearl, Inc.
PAYSLIP — [MONTH YEAR]
Name: [Employee Name]

Gross Salary & Allowances        Deduction:
  Salary:     PHP xx,xxx           SSS:          PHP xxx
  Ancillary:  PHP  x,xxx           Pag IBIG:     PHP xxx
  TOTAL:      PHP xx,xxx           Phil Health:  PHP xxx
                                   Salary Loan:  PHP xxx
                                   TOTAL:        PHP x,xxx

Net Salary
  1st Period:  PHP x,xxx
  2nd Period:  PHP x,xxx

            School Principal
```

---

## Leave Policy

| Leave Type | Key | Notes |
|---|---|---|
| Service Incentive Leave (SIL) | `SIL` | 1 day/month, max 10/SY |
| Sick Leave | `Sick` | Deducted from SIL credit |
| Personal Leave | `Personal` | Deducted from SIL credit |
| Vacation Leave | `Vacation` | Without pay |
| Maternity Leave (RA 11210) | `Maternity` | Attach hospital documents |
| Solo Parent Leave (RA 8972) | `SoloParent` | Attach Solo Parent ID |
| VAWC Leave (RA 9262) | `VAWC` | For women victims of violence |
| Magna Carta for Women (RA 9710) | `MagnaCartaWomen` | Attach medical certificate |
| Paternity Leave (RA 8187) | `Paternity` | 7 days, first 4 deliveries |
| Others | `Others` | Specify in remarks |

---

## Pre-loaded Staff (18 total)

| # | Name | Basic Pay | Ancillary | Gov Deductions |
|---|---|---|---|---|
| 1 | BONGALOS, Jerald B. | ₱22,000 | ₱0 | No |
| 2 | PANCHO, Melanie L. | ₱12,000 | ₱2,500 | Yes |
| 3 | PEDROSO, Ptr. Marcial Lou | ₱12,000 | ₱0 | Yes |
| 4 | PECSON, Sofia C. | ₱14,000 | ₱2,000 | Yes |
| 5 | ESTEBAN, Jireh F. | ₱9,500 | ₱500 | Yes |
| 6 | CASAS, Myrna R. | ₱12,000 | ₱500 | Yes |
| 7 | CAPON, Jenifer A. | ₱9,500 | ₱1,500 | Yes |
| 8 | FLORES, Princess F. | ₱9,500 | ₱500 | Yes |
| 9 | ESTEBAN, Shella Mae P. | ₱9,500 | ₱750 | Yes |
| 10 | FRANCISCO, John Mark G. | ₱9,500 | ₱1,000 | Yes |
| 11 | BALDESOTO, Jean Berlyn | ₱10,500 | ₱0 | Yes |
| 12 | BIBAT, Samuel F. | ₱10,500 | ₱0 | Yes |
| 13 | PAREJA, Marjorie Joyce S. | ₱9,500 | ₱500 | Yes |
| 14 | MISME, Marah M. | ₱10,000 | ₱1,000 | Yes |
| 15 | EGSANE, Jocelyn C. | ₱10,500 | ₱500 | Yes |
| 16 | MEMBRILLO, Ramcess | ₱10,500 | ₱500 | Yes |
| 17 | MARCELO, May B. | ₱9,500 | ₱0 | No |
| 18 | ESTEBAN, Jessie S. | ₱11,500 | ₱0 | No |

> Staff are loaded from Cloudflare KV on login. The pre-loaded list above only seeds if KV is empty (offline mode). All staff you add through the Staff Directory are saved permanently to KV.

---

## Multi-Device Sync

All data syncs automatically across devices via Cloudflare KV.

| Scenario | What to do |
|---|---|
| Added a student on Device A, need to see on Device B | Click **🔄 Sync All** on Dashboard |
| Added a teacher on Device A, need to see on Device B | Click **🔄 Sync** in HR & Payroll tab |
| Records disappear after sync | Wait 5–10 seconds (KV propagation), then sync again |

> **Sync is non-destructive** — it only adds/updates records from KV, never removes existing ones. Safe to click anytime.

---

## Dependencies (`requirements.txt`)

```
streamlit>=1.32.0
reportlab>=4.0.0
pillow>=10.0.0
pandas>=2.0.0
openpyxl
requests>=2.31.0
pypdf
```

---

## First-Time Deploy

1. Fork or clone `Jbong17/SEPIenrollment`
2. Upload `sepi_logo.jpg` to repo root
3. Go to [share.streamlit.io](https://share.streamlit.io) → New app → Connect repo
4. Set main file: `app.py`
5. Add Secrets (see Streamlit Secrets section above)
6. Deploy — app starts in ~60 seconds
7. Open Dashboard — confirm 🟢 **"Cloudflare KV connected"**

---

## Updating Code (Safe)

Uploading new `.py` files to GitHub **never deletes data**. Cloudflare KV is completely separate from the code. You can update any file anytime.

**Recommended upload method:** GitHub → Add file → **Upload files** (drag & drop) — avoids truncation issues with the web editor for large files.

---

## School Info

| Field | Value |
|---|---|
| School Name | School of Everlasting Pearl, Inc. (SEPI) |
| Motto | "Leading Lifelong Learners" |
| Address | #66 Siruna Village Phase III, Mambugan, Antipolo City |
| DepEd School ID | 402954 |
| ESC School ID | 403694 |
| Recognition Nos. | K-042 s.2009 · E-041 s.2012 · 026 s.2011 |
| Email | sepiregistrar@gmail.com · sepi402954@gmail.com |
| Phone | 09171861591 |
| Levels Offered | Kinder/Preschool · Elementary · Junior High School |
| School Year | 2026–2027 |

---

*Built with ❤️ for SEPI — Kinder to Junior High*
