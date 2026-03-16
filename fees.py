"""
SEPI Official Fee Schedule SY 2026-2027
Levels offered: Kinder / Preschool, Elementary, Junior High School (JHS)
"""

SCHOOL_ADDRESS = "#66 Siruna Village Phase III, Mambugan, Antipolo City"
SCHOOL_YEAR    = "2026-2027"
SCHOOL_NAME    = "SCHOOL OF EVERLASTING PEARL, INC. (SEPI)"
SCHOOL_EMAIL   = "sepiregistrar@gmail.com"
SCHOOL_PHONE   = "09171861591"
SCHOOL_CITY    = "Antipolo City, Rizal"

FEE_LINES = {
    "preschool": {
        "Registration Fee":     6000.00,
        "Tuition Fee":         10043.00,
        "Library Fee":           500.00,
        "Medical / Dental Fee": 2000.00,
        "Test Kits":            1250.00,
        "Energy Fee":           2000.00,
        "Books / LMS":          5000.00,
    },
    "elem_lower": {
        "Registration Fee":     6000.00,
        "Tuition Fee":         13283.00,
        "Library Fee":           500.00,
        "Medical / Dental Fee": 2000.00,
        "Test Kits":            1250.00,
        "Energy Fee":           2000.00,
        "Books / LMS":          5000.00,
    },
    "elem_upper": {
        "Registration Fee":     6000.00,
        "Tuition Fee":         15703.00,
        "Library Fee":           500.00,
        "Medical / Dental Fee": 2000.00,
        "Test Kits":            1250.00,
        "Energy Fee":           2000.00,
        "Books / LMS":          5000.00,
    },
    "jhs": {
        "Registration Fee":     6000.00,
        "Tuition Fee":         21150.00,
        "Library Fee":           500.00,
        "Medical / Dental Fee": 2000.00,
        "Test Kits":            1250.00,
        "Energy Fee":           2000.00,
        "Books / LMS":          5000.00,
    },
}

# ── Discount Schedule (per SEPI Tuition Fee Discount Policy) ─────────────────
# Applies to TUITION FEE ONLY. Only 1 discount per student (highest applicable).
# ESC grantees cannot combine discounts.

DISCOUNT_TYPES = [
    {
        "key":         "early_enrollment",
        "label":       "Early Enrollment Discount",
        "rate_min":    5,
        "rate_max":    5,
        "rate_label":  "5%",
        "description": "At least 80% of tuition paid on or before the published deadline (e.g. May 15).",
        "not_for_esc": True,
        "requires_input": False,
    },
    {
        "key":         "sibling",
        "label":       "Sibling Discount",
        "rate_min":    10,
        "rate_max":    10,
        "rate_label":  "10%",
        "description": "For families with 2+ enrolled children; applied to the sibling in the higher grade.",
        "not_for_esc": True,
        "requires_input": False,
    },
    {
        "key":         "solo_parent",
        "label":       "Solo Parent Discount",
        "rate_min":    10,
        "rate_max":    10,
        "rate_label":  "10%",
        "description": "Valid Solo Parent ID per RA 8972 issued by LGU.",
        "not_for_esc": True,
        "requires_input": False,
    },
    {
        "key":         "indigenous_peoples",
        "label":       "Indigenous Peoples (IP) Discount",
        "rate_min":    15,
        "rate_max":    15,
        "rate_label":  "15%",
        "description": "NCIP or authorized certificate of membership required.",
        "not_for_esc": True,
        "requires_input": False,
    },
    {
        "key":         "senior_citizen_guardian",
        "label":       "Senior Citizen Guardian Discount",
        "rate_min":    10,
        "rate_max":    10,
        "rate_label":  "10%",
        "description": "Legal guardianship confirmed by court or DSWD certificate.",
        "not_for_esc": True,
        "requires_input": False,
    },
    {
        "key":         "employee_privilege",
        "label":       "Employee Privilege Discount",
        "rate_min":    20,
        "rate_max":    50,
        "rate_label":  "20–50%",
        "description": "Based on employment classification: Full-time, Part-time, Teaching/Non-teaching.",
        "not_for_esc": False,
        "requires_input": True,   # encoder must enter exact rate
    },
    {
        "key":         "referral",
        "label":       "Referral Incentive",
        "rate_min":    5,
        "rate_max":    5,
        "rate_label":  "5%",
        "description": "For successfully referring a newly enrolled student. One-time only.",
        "not_for_esc": False,
        "requires_input": False,
    },
    {
        "key":         "alumni_legacy",
        "label":       "Alumni Legacy Discount",
        "rate_min":    5,
        "rate_max":    10,
        "rate_label":  "5–10%",
        "description": "For children of school alumni. Proof of graduation required.",
        "not_for_esc": False,
        "requires_input": True,
    },
    {
        "key":         "merit_student_leader",
        "label":       "Student-Leader / Merit-Based Discount",
        "rate_min":    5,
        "rate_max":    10,
        "rate_label":  "5–10%",
        "description": "SSG Officers, org officers, Mr./Ms. SEPI, students who represented SEPI with distinction.",
        "not_for_esc": False,
        "requires_input": True,
    },
]

DISCOUNT_BY_KEY = {d["key"]: d for d in DISCOUNT_TYPES}

# ESC (Education Service Contracting) — fixed government subsidy
ESC_SUBSIDY_AMOUNT = 9_000.00  # PHP 9,000 deducted from tuition fee


def get_fee_group(level, grade):
    if level == "preschool":
        return "preschool"
    if level == "elementary":
        num = int("".join(filter(str.isdigit, grade)) or "1")
        return "elem_lower" if num <= 3 else "elem_upper"
    if level == "jhs":
        return "jhs"
    return "elem_lower"


def compute_fees(level, grade, discount_key=None, discount_rate=None,
                 esc_grantee=False):
    """
    Returns fee breakdown including ESC subsidy and/or school discount.

    ESC grantees receive a fixed PHP 9,000 deduction from tuition (government subsidy).
    ESC grantees may NOT combine this with school discounts (policy rule).

    discount_key : key from DISCOUNT_TYPES (or None)  — ignored for ESC grantees
    discount_rate: integer percentage                  — ignored for ESC grantees
    esc_grantee  : bool — if True, applies PHP 9,000 ESC subsidy only
    """
    group        = get_fee_group(level, grade)
    lines        = FEE_LINES[group].copy()
    tuition_base = lines["Tuition Fee"]

    discount_info   = None
    discount_amount = 0.0
    esc_info        = None

    if esc_grantee:
        # ESC overrides all school discounts
        esc_deduction = min(ESC_SUBSIDY_AMOUNT, tuition_base)
        lines["Tuition Fee"] = round(tuition_base - esc_deduction, 2)
        esc_info = {
            "type":         "ESC",
            "label":        "ESC Government Subsidy",
            "amount":       esc_deduction,
            "base_tuition": tuition_base,
        }
        discount_amount = esc_deduction
        discount_info   = esc_info

    elif discount_key and discount_key != "none":
        d = DISCOUNT_BY_KEY.get(discount_key)
        if d:
            if discount_rate and d["requires_input"]:
                rate = max(d["rate_min"], min(d["rate_max"], int(discount_rate)))
            else:
                rate = d["rate_min"]
            discount_amount = round(tuition_base * rate / 100, 2)
            lines["Tuition Fee"] = round(tuition_base - discount_amount, 2)
            discount_info = {
                "key":          discount_key,
                "label":        d["label"],
                "rate":         rate,
                "amount":       discount_amount,
                "base_tuition": tuition_base,
            }

    total = round(sum(lines.values()), 2)
    return {
        "lines":           lines,
        "total":           total,
        "group":           group,
        "discount":        discount_info,
        "discount_amount": discount_amount,
        "esc_grantee":     esc_grantee,
        "esc_info":        esc_info,
    }


LEVEL_LABEL = {
    "preschool":  "Kinder / Preschool",
    "elementary": "Elementary",
    "jhs":        "Junior High School",
}

GRADES = {
    "preschool":  ["Nursery", "Kinder 1", "Kinder 2"],
    "elementary": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"],
    "jhs":        ["Grade 7", "Grade 8", "Grade 9", "Grade 10"],
}
