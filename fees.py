"""
SEPI Official Fee Schedule SY 2026-2027
Levels offered: Kinder / Preschool, Elementary, Junior High School (JHS)
"""

SCHOOL_ADDRESS = "Zone 10, Brgy. Dela Paz, Antipolo City, Rizal 1870"
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

def get_fee_group(level, grade):
    if level == "preschool":
        return "preschool"
    if level == "elementary":
        num = int("".join(filter(str.isdigit, grade)) or "1")
        return "elem_lower" if num <= 3 else "elem_upper"
    if level == "jhs":
        return "jhs"
    return "elem_lower"

def compute_fees(level, grade):
    group = get_fee_group(level, grade)
    lines = FEE_LINES[group].copy()
    total = sum(lines.values())
    return {"lines": lines, "total": total, "group": group}

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
