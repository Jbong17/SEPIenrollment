"""
SEPI Official Fee Schedule SY 2026–2027
Source: Official fee tables provided by administration
"""

SCHOOL_ADDRESS = "Zone 10, Brgy. Dela Paz, Antipolo City, Rizal 1870"
SCHOOL_YEAR    = "2026-2027"
SCHOOL_NAME    = "SCHOOL OF EVERLASTING PEARL, INC. (SEPI)"
SCHOOL_EMAIL   = "sepiregistrar@gmail.com"
SCHOOL_PHONE   = "09171861591"
SCHOOL_CITY    = "Antipolo City, Rizal"

# ── Fee line-items per level group ────────────────────────────────────────────
# Each dict: { particular: amount }
FEE_LINES = {
    "preschool": {
        "Registration Fee":     6_000.00,
        "Tuition Fee":         10_043.00,
        "Library Fee":            500.00,
        "Medical / Dental Fee": 2_000.00,
        "Test Kits":            1_250.00,
        "Energy Fee":           2_000.00,
        "Books / LMS":          5_000.00,
    },
    "elem_lower": {          # Grades 1 – 3
        "Registration Fee":     6_000.00,
        "Tuition Fee":         13_283.00,
        "Library Fee":            500.00,
        "Medical / Dental Fee": 2_000.00,
        "Test Kits":            1_250.00,
        "Energy Fee":           2_000.00,
        "Books / LMS":          5_000.00,
    },
    "elem_upper": {          # Grades 4 – 6
        "Registration Fee":     6_000.00,
        "Tuition Fee":         15_703.00,
        "Library Fee":            500.00,
        "Medical / Dental Fee": 2_000.00,
        "Test Kits":            1_250.00,
        "Energy Fee":           2_000.00,
        "Books / LMS":          5_000.00,
    },
    "jhs": {                 # Grades 7 – 10
        "Registration Fee":     6_000.00,
        "Tuition Fee":         21_150.00,
        "Library Fee":            500.00,
        "Medical / Dental Fee": 2_000.00,
        "Test Kits":            1_250.00,
        "Energy Fee":           2_000.00,
        "Books / LMS":          5_000.00,
    },
    "shs": {                 # Grades 11 – 12  ← TBD: admin will update
        "Registration Fee":     6_000.00,
        "Tuition Fee":         25_000.00,   # placeholder – update when provided
        "Library Fee":            500.00,
        "Medical / Dental Fee": 2_000.00,
        "Test Kits":            1_250.00,
        "Energy Fee":           2_000.00,
        "Books / LMS":          5_000.00,
    },
}

def get_fee_group(level: str, grade: str) -> str:
    """Return fee-group key based on level + grade."""
    if level == "preschool":
        return "preschool"
    if level == "elementary":
        num = int("".join(filter(str.isdigit, grade)) or "1")
        return "elem_lower" if num <= 3 else "elem_upper"
    if level == "jhs":
        return "jhs"
    if level == "shs":
        return "shs"
    return "elem_lower"

def compute_fees(level: str, grade: str) -> dict:
    """Return line-items dict and total for a student."""
    group  = get_fee_group(level, grade)
    lines  = FEE_LINES[group].copy()
    total  = sum(lines.values())
    return {"lines": lines, "total": total, "group": group}

LEVEL_LABEL = {
    "preschool":  "Kinder / Preschool",
    "elementary": "Elementary",
    "jhs":        "Junior High School",
    "shs":        "Senior High School",
}
GRADES = {
    "preschool":  ["Nursery", "Kinder 1", "Kinder 2"],
    "elementary": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"],
    "jhs":        ["Grade 7", "Grade 8", "Grade 9", "Grade 10"],
    "shs":        ["Grade 11", "Grade 12"],
}
STRANDS = ["STEM", "ABM", "HUMSS", "GAS", "TVL – ICT", "TVL – HE", "TVL – IA",
           "Sports Track", "Arts & Design Track"]
