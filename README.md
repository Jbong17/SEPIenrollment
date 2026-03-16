# SEPI Enrollment & HR System

**School of Everlasting Pearl, Inc. (SEPI)**
#66 Siruna Village Phase III, Mambugan, Antipolo City
SY 2026–2027

---

## Overview

A full-stack school management system built with **Streamlit** and deployed on **Streamlit Community Cloud**. Covers student enrollment, payroll, HR, and leave management for Kinder through Junior High School (no SHS).

---

## Live App

Deployed at: *(your Streamlit Cloud URL)*
GitHub Repo: `Jbong17/SEPIenrollment`

---

## File Structure

```
SEPIenrollment/
├── app.py              # Main application (all UI, routing, portals)
├── fees.py             # Fee schedule, discount policy, ESC computation
├── pdf_gen.py          # Enrollment Form, Contract, SOA — ReportLab PDFs
├── payroll.py          # Payroll engine, contribution tables, staff roster
├── hr_pdf.py           # Payslip, Payroll Register, COE, Leave Form — PDFs
├── db.py               # Cloudflare KV persistence layer
├── requirements.txt    # Python dependencies
├── sepi_logo.jpg       # School logo (used in all PDFs and portal header)
└── README.md           # This file
```

---

## Portals & Credentials

| Portal | URL Tab | Username | Default Password |
|---|---|---|---|
| Student Portal | Student Portal tab | *(Tracking ID)* | — |
| Admin Portal | Admin Portal tab | `admin` | `sepi2024` |
| Payroll Portal | Admin Portal tab | `payroll` | `payroll2024` |

> **Important:** Change passwords in Streamlit Secrets after first deploy.

---

## Streamlit Secrets

Go to: **share.streamlit.io → your app → ⋮ → Settings → Secrets**

```toml
CF_ACCOUNT_ID      = "dffb0b9be393c741552aa373a3e2d494"
CF_API_TOKEN       = "your-cloudflare-api-token"
ADMIN_PASSWORD     = "sepi2024"
PAYROLL_PASSWORD   = "payroll2024"
GMAIL_APP_PASSWORD = ""          # optional — enables OTP password change
```

---

## Cloudflare KV Namespaces

| Namespace | ID | Purpose |
|---|---|---|
| `SEPI_Enrollment_Database` | `7d035b4c332449c5993651ab62478609` | Student enrollment records |
| `SEPI_HR_Payroll` | `dfe32c5ff0924b199cea8e36f588f6c4` | Teacher profiles, payroll runs, leave records |

**Key schemes:**

| Namespace | Key pattern | Content |
|---|---|---|
| Enrollment | `student:{SEPI-XXXXXX}` | Full student enrollment record (JSON) |
| HR | `teacher:{EMP-XXX}` | Teacher 201 file (JSON) |
| HR | `payroll:{YYYY-MM}` | Monthly payroll run (JSON) |
| HR | `leave:{YYYYMMDD-XXXXXX}` | Leave application (JSON) |

---

## Student Portal

Accessible via **Tracking ID** (format: `SEPI-XXXXXX`).

**Features:**
- View enrollment status (Pending / Under Review / Approved / Rejected)
- Documents checklist — submitted vs pending
- Fee summary with discount breakdown
- Generate PDF documents (Enrollment Form, Contract, SOA)

---

## Admin Portal

Login: `admin` / `sepi2024`

### Navigation Tabs

| Tab | Purpose |
|---|---|
| 📊 Dashboard | Enrollment stats, Cloudflare KV connection status |
| 👥 Students | Search/filter roster, inline SOA viewer, payment entry, status update |
| 🗂️ Inventory | Per grade level roster with Excel export |
| 📈 Reports | Fee collection summary, CSV export |
| ☁️ Cloudflare KV | Namespace info, schema reference, JSON export |
| ⚙️ Settings | Change admin password (with OTP email if Gmail configured) |

### Sidebar Quick Actions
- **📋 New Enrollment** — opens 6-step enrollment form
- **💳 Update SOA / Payment** — record staggered payments by Tracking ID

### Enrollment Form (6 Steps)
1. Personal Information
2. Educational Background
3. Parent / Guardian Information
4. Enrollment Details
5. Scholarship / Discount
6. Review & Submit

**Documents generated per student:**
- Enrollment Form (7 sections, tracking ID banner, long bond paper)
- Enrollment Contract (8 articles)
- Statement of Account (Sections A–C with discount lines)

---

## Fee Schedule — SY 2026–2027

| Level | Reg Fee | Tuition | Misc | Total |
|---|---|---|---|---|
| Kinder / Preschool | ₱6,000 | ₱10,043 | ₱10,750 | **₱26,793** |
| Elementary Gr 1–3 | ₱6,000 | ₱13,283 | ₱10,750 | **₱30,033** |
| Elementary Gr 4–6 | ₱6,000 | ₱15,703 | ₱10,750 | **₱32,453** |
| JHS Gr 7–10 | ₱6,000 | ₱21,150 | ₱10,750 | **₱37,900** |

*Miscellaneous includes: Library ₱500, Medical/Dental ₱2,000, Test Kits ₱1,250, Energy Fee ₱2,000, Books/LMS ₱5,000*

---

## Discount Policy

Per SEPI Tuition Fee Discount Policy (adopted by School Board):
- Only **one discount per student** — highest applicable is granted
- Discounts apply to **tuition fee only**
- ESC grantees receive **₱9,000 government subsidy** (overrides all school discounts)

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
| ESC Government Subsidy | ₱9,000 fixed |

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
- 20 working days/month, 10 days per cut-off
- **1st Period** (days 1–15): Basic pay only + substitution pay
- **2nd Period** (days 16–end): Basic + ancillary pay + additional pay − all deductions
- Deductions (government + loans) applied on 2nd period only

**Employees exempt from government deductions:**
- Bongalos, Jerald B. (Principal)
- Marcelo, May B. (Non-teaching)
- Esteban, Jessie S. (Non-teaching)

### Navigation Tabs

| Tab | Purpose |
|---|---|
| 💰 Process Payroll | Select month, enter attendance, process |
| 📊 Payroll History | All past runs, re-downloadable |
| 👥 Staff Directory | 201 file, add/edit/delete, photo upload |
| 📄 Documents | Generate payslip or COE individually |
| 🏖️ Leave | File leave, SIL tracker, print leave form |

### Documents Generated

| Document | Format |
|---|---|
| Individual Payslip | Letter, simple SEPI format |
| All Payslips (merged) | Single PDF, all staff |
| Payroll Register | Landscape long bond, matches official format |
| Certificate of Employment | Letter, blank signature lines, auto-date |
| Application for Leave Form | Letter, matches official SEPI form |

### Payslip Format
```
School of Everlasting Pearl, Inc
PAYSLIP — [MONTH YEAR]
Name: [Employee Name]

Gross Salary & Allowances    Deduction:
  Salary:    ₱ xx,xxx         SSS:         ₱ xxx
  Ancillary: ₱  x,xxx         Pag IBIG:    ₱ xxx
  TOTAL:     ₱ xx,xxx         Phil Health: ₱ xxx
                               Salary Loan: ₱ xxx
                               TOTAL:       ₱ x,xxx

Net Salary
  1st Period: ₱ x,xxx
  2nd Period: ₱ x,xxx

  Jerald B. Bongalos
  School Principal
```

### Pre-loaded Staff (18 total)

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

---

## Leave Policy (SEPI)

| Leave Type | Key | Notes |
|---|---|---|
| Service Incentive Leave (SIL) | `SIL` | 1 day/month, max 10/SY |
| Sick Leave | `Sick` | Deducted from SIL credit |
| Personal Leave | `Personal` | Deducted from SIL credit |
| Vacation Leave | `Vacation` | Without pay |
| Maternity Leave (RA 11210) | `Maternity` | With pay |
| Solo Parent Leave (RA 8972) | `SoloParent` | Attach Solo Parent ID |
| VAWC Leave (RA 9262) | `VAWC` | For women victims of violence |
| Magna Carta for Women (RA 9710) | `MagnaCartaWomen` | Attach medical cert |
| Paternity Leave (RA 8187) | `Paternity` | 7 days, first 4 deliveries |
| Others | `Others` | Specify in remarks |

**SIL rules:** Submit at least 10 working days in advance. Sick/Personal deducted from SIL. Unused SIL convertible upon EOSY or separation.

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

## Getting Started (New Deploy)

1. Fork or clone `Jbong17/SEPIenrollment`
2. Upload `sepi_logo.jpg` to the repo root
3. Go to [share.streamlit.io](https://share.streamlit.io) → New app → Connect repo
4. Set main file: `app.py`
5. Add Secrets (see Streamlit Secrets section above)
6. Deploy — app starts in ~60 seconds

**First time the Payroll Portal loads:** All 18 SEPI staff are automatically seeded into Cloudflare KV. No manual entry needed.

---

## SOA Payment Update Workflow

1. Admin logs in → Sidebar → **💳 Update SOA / Payment**
2. Enter student Tracking ID → Look Up
3. View fee summary, payment history, running balance
4. Record new payment: amount, mode (Cash/GCash/Bank/Check), date, OR number, remarks
5. System updates paidAmount and paymentHistory in Cloudflare KV
6. Generate updated SOA PDF reflecting new balance

---

## Data Persistence

All data is stored in **Cloudflare KV** (survives hibernation and redeployment):

| Event | Without KV | With KV |
|---|---|---|
| App hibernates (7 days idle) | ❌ All data lost | ✅ Safe |
| App redeploys | ❌ All data lost | ✅ Reloaded on startup |
| Browser session ends | ❌ Session lost | ✅ Student logs in with Tracking ID |

---

## School Info

| Field | Value |
|---|---|
| School Name | School of Everlasting Pearl, Inc. (SEPI) |
| Address | #66 Siruna Village Phase III, Mambugan, Antipolo City |
| DepEd School ID | 402954 |
| ESC School ID | 403694 |
| Email | sepiregistrar@gmail.com |
| Phone | 09171861591 |
| School President | Mr. Jasper E. Elipane |
| School Principal | Mr. Jerald B. Bongalos, MScT, LPT |
| Levels Offered | Kinder / Preschool, Elementary, Junior High School |
| School Year | 2026–2027 |

---

*Built with ❤️ for SEPI — Kinder to Junior High*
