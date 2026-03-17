"""
SEPI Payroll Computation Engine  -  SY 2026-2027
=================================================
SEPI rates (from official payroll register):
  SSS        : 5%  of basic monthly salary (flat, employee share)
  PhilHealth : 2.5% of basic monthly salary (employee share)
  Pag-IBIG   : 2%  of basic monthly salary, capped at PHP 200/month

Payroll structure (semi-monthly, 20 working days/month):
  - 1st Period (days 1-15)  : 10 working days, basic pay only + substitution
  - 2nd Period (days 16-end): 10 working days, basic + ancillary + additional
  - All government deductions applied on 2nd period only
"""

WORKING_DAYS_MONTHLY = 20
WORKING_DAYS_CUTOFF  = 10

SSS_RATE     = 0.05
PH_RATE      = 0.025
PAGIBIG_RATE = 0.02
PAGIBIG_CAP  = 200.0

EMPLOYEE_TYPES = [
    "Full-time Teaching",
    "Part-time Teaching",
    "Full-time Non-teaching",
]

OTHER_DEDUCTION_TYPES = [
    "Salary Loan / Cash Advance",
    "SSS Loan",
    "Pag-IBIG Loan",
    "Tuition Fee",
    "Other Deduction",
]


def sss_employee(basic: float) -> float:
    return round(basic * SSS_RATE, 2)

def philhealth_employee(basic: float) -> float:
    return round(basic * PH_RATE, 2)

def pagibig_employee(basic: float) -> float:
    return min(round(basic * PAGIBIG_RATE, 2), PAGIBIG_CAP)

def daily_rate(basic: float) -> float:
    return round(basic / WORKING_DAYS_MONTHLY, 4)


def compute_payroll(teacher: dict, period_data: dict) -> dict:
    """
    Compute one semi-monthly period.

    teacher fields:
      basicMonthlyPay  : float
      ancillaryPay     : float  (fixed monthly ancillary, released fully on 2nd period)
      hasGovDeductions : bool   (False = exempt from SSS/PH/PI)

    period_data keys:
      period_type   : "1st" | "2nd"
      period_label  : str
      year_month    : str   e.g. "2026-07"
      days_reported : float (out of 10)
      substitution  : float (1st period extra pay)
      additional_pay: float (2nd period ad-hoc extra)
      salary_loan   : float
      tuition_fee   : float
      other_deductions: dict {label: amount}
    """
    basic     = float(teacher.get("basicMonthlyPay", 0) or 0)
    ancillary = float(teacher.get("ancillaryPay", 0) or 0)
    dr        = daily_rate(basic)
    p_type    = period_data.get("period_type", "1st")
    days      = float(period_data.get("days_reported", WORKING_DAYS_CUTOFF) or WORKING_DAYS_CUTOFF)
    subst     = float(period_data.get("substitution", 0) or 0)
    addl_pay  = float(period_data.get("additional_pay", 0) or 0)
    salary_loan = float(period_data.get("salary_loan", 0) or 0)
    tuition_fee = float(period_data.get("tuition_fee", 0) or 0)
    other_deductions = period_data.get("other_deductions", {}) or {}

    # ── Earnings ──────────────────────────────────────────────────────────────
    base_pay = round(dr * days, 2)
    if p_type == "1st":
        gross = round(base_pay + subst, 2)
    else:
        gross = round(base_pay + ancillary + addl_pay, 2)

    # ── Government contributions ──────────────────────────────────────────────
    has_gov = teacher.get("hasGovDeductions", True)
    sss_m = sss_employee(basic) if has_gov else 0.0
    ph_m  = philhealth_employee(basic) if has_gov else 0.0
    pi_m  = pagibig_employee(basic) if has_gov else 0.0
    total_gov = round(sss_m + ph_m + pi_m, 2)

    other_total = round(
        salary_loan + tuition_fee +
        sum(float(v or 0) for v in other_deductions.values()), 2)

    # ── Deductions applied on 2nd period only ─────────────────────────────────
    if p_type == "2nd":
        total_deductions = round(total_gov + other_total, 2)
    else:
        total_deductions = 0.0
        total_gov = sss_m = ph_m = pi_m = 0.0
        salary_loan = tuition_fee = other_total = 0.0

    net_pay = round(gross - total_deductions, 2)

    return {
        "teacherId":         teacher.get("teacherId"),
        "teacherName":       teacher.get("name"),
        "position":          teacher.get("position"),
        "employeeType":      teacher.get("employeeType"),
        "basicMonthlyPay":   basic,
        "ancillaryPay":      ancillary,
        "dailyRate":         round(dr, 2),
        "periodType":        p_type,
        "periodLabel":       period_data.get("period_label", ""),
        "yearMonth":         period_data.get("year_month", ""),
        "daysReported":      days,
        "basePay":           base_pay,
        "substitution":      subst if p_type == "1st" else 0,
        "ancillaryReleased": ancillary if p_type == "2nd" else 0,
        "additionalPay":     addl_pay if p_type == "2nd" else 0,
        "grossPay":          gross,
        "sss":               round(sss_m, 2),
        "philHealth":        round(ph_m, 2),
        "pagIbig":           round(pi_m, 2),
        "totalGovDeductions":total_gov,
        "salaryLoan":        salary_loan,
        "tuitionFee":        tuition_fee,
        "otherDeductions":   other_deductions,
        "totalOtherDeductions": other_total,
        "totalDeductions":   total_deductions,
        "netPay":            net_pay,
    }


def compute_monthly_payroll(teacher: dict, p1: dict, p2: dict) -> dict:
    r1 = compute_payroll(teacher, {**p1, "period_type": "1st"})
    r2 = compute_payroll(teacher, {**p2, "period_type": "2nd"})
    basic     = float(teacher.get("basicMonthlyPay", 0) or 0)
    ancillary = float(teacher.get("ancillaryPay", 0) or 0)
    return {
        "teacherId":       teacher.get("teacherId"),
        "teacherName":     teacher.get("name"),
        "position":        teacher.get("position"),
        "employeeType":    teacher.get("employeeType"),
        "basicMonthlyPay": basic,
        "ancillaryPay":    ancillary,
        "grossMonthly":    round(basic + ancillary, 2),
        "yearMonth":       p1.get("year_month", ""),
        "p1": r1, "p2": r2,
        "totalNet1":       r1["netPay"],
        "totalNet2":       r2["netPay"],
        "totalNetMonth":   round(r1["netPay"] + r2["netPay"], 2),
        "totalDeductions": r2["totalDeductions"],
    }


SEPI_INITIAL_STAFF = [
    {"name":"BONGALOS, Jerald B.","lastName":"BONGALOS","firstName":"Jerald","middleName":"B.",
     "position":"School Principal","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":22000,"ancillaryPay":0,"dateHired":"","hasGovDeductions":False},
    {"name":"PANCHO, Melanie L.","lastName":"PANCHO","firstName":"Melanie","middleName":"L.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":12000,"ancillaryPay":2500,"dateHired":""},
    {"name":"PEDROSO, Ptr. Marcial Lou","lastName":"PEDROSO","firstName":"Marcial Lou","middleName":"",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":12000,"ancillaryPay":0,"dateHired":""},
    {"name":"PECSON, Sofia C.","lastName":"PECSON","firstName":"Sofia","middleName":"C.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":14000,"ancillaryPay":2000,"dateHired":""},
    {"name":"ESTEBAN, Jireh F.","lastName":"ESTEBAN","firstName":"Jireh","middleName":"F.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":500,"dateHired":""},
    {"name":"CASAS, Myrna R.","lastName":"CASAS","firstName":"Myrna","middleName":"R.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":12000,"ancillaryPay":500,"dateHired":""},
    {"name":"CAPON, Jenifer A.","lastName":"CAPON","firstName":"Jenifer","middleName":"A.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":1500,"dateHired":""},
    {"name":"FLORES, Princess F.","lastName":"FLORES","firstName":"Princess","middleName":"F.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":500,"dateHired":""},
    {"name":"ESTEBAN, Shella Mae P.","lastName":"ESTEBAN","firstName":"Shella Mae","middleName":"P.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":750,"dateHired":""},
    {"name":"FRANCISCO, John Mark G.","lastName":"FRANCISCO","firstName":"John Mark","middleName":"G.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":1000,"dateHired":""},
    {"name":"BALDESOTO, Jean Berlyn","lastName":"BALDESOTO","firstName":"Jean Berlyn","middleName":"",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":10500,"ancillaryPay":0,"dateHired":""},
    {"name":"BIBAT, Samuel F.","lastName":"BIBAT","firstName":"Samuel","middleName":"F.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":10500,"ancillaryPay":0,"dateHired":""},
    {"name":"PAREJA, Marjorie Joyce S.","lastName":"PAREJA","firstName":"Marjorie Joyce","middleName":"S.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":500,"dateHired":""},
    {"name":"MISME, Marah M.","lastName":"MISME","firstName":"Marah","middleName":"M.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":10000,"ancillaryPay":1000,"dateHired":""},
    {"name":"EGSANE, Jocelyn C.","lastName":"EGSANE","firstName":"Jocelyn","middleName":"C.",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":10500,"ancillaryPay":500,"dateHired":""},
    {"name":"MEMBRILLO, Ramcess","lastName":"MEMBRILLO","firstName":"Ramcess","middleName":"",
     "position":"Teacher","employeeType":"Full-time Teaching","employmentStatus":"Regular",
     "basicMonthlyPay":10500,"ancillaryPay":500,"dateHired":""},
    {"name":"MARCELO, May B.","lastName":"MARCELO","firstName":"May","middleName":"B.",
     "position":"Non-teaching Staff","employeeType":"Full-time Non-teaching","employmentStatus":"Regular",
     "basicMonthlyPay":9500,"ancillaryPay":0,"dateHired":"","hasGovDeductions":False},
    {"name":"ESTEBAN, Jessie S.","lastName":"ESTEBAN","firstName":"Jessie","middleName":"S.",
     "position":"Non-teaching Staff","employeeType":"Full-time Non-teaching","employmentStatus":"Regular",
     "basicMonthlyPay":11500,"ancillaryPay":0,"dateHired":"","hasGovDeductions":False},
]
