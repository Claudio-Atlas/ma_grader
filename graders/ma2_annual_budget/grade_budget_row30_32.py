# graders/annual_budget/grade_budget_row30_32.py

from utilities.formula_equiv import formulas_equivalent


def normalize_formula(formula: str) -> str:
    """Normalize an Excel formula for comparison."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )


def grade_budget_row30(ws):
    """
    Grades D30: Projected Total in 5 Years
    Required: =D28*(1+D29)
    Acceptable: factor reversed, absolute refs ok
    Worth 3 points.
    """

    comments = []
    total_points = 0.0

    val = ws["D30"].value

    if isinstance(val, str) and val.startswith("="):
        f = normalize_formula(val)

        # required references
        has_d28 = "d28" in f
        has_d29 = "d29" in f

        # must multiply
        has_mult = "*" in f

        # acceptable forms of (1+D29) or (D29+1)
        has_growth = ("1+d29" in f) or ("d29+1" in f)

        if (has_d28 and has_d29 and has_mult and has_growth) or \
                formulas_equivalent(val, "=D28*(1+D29)"):
            total_points = 3
        else:
            comments.append("D30 must be =D28*(1+D29) or an equivalent form.")
    else:
        comments.append("D30 must contain a formula multiplying D28 by (1 + D29).")

    return {
        "total_points": total_points,
        "comment": " | ".join(comments) if comments else ""
    }


def grade_budget_row32(ws):
    """
    Grades D32: Remaining Total
    Required: =D31 - D30 (NOT commutative)
    Worth 2 points.
    """

    comments = []
    total_points = 0.0

    val = ws["D32"].value

    if isinstance(val, str) and val.startswith("="):
        f = normalize_formula(val)

        if f == "=d31-d30" or formulas_equivalent(val, "=D31-D30"):
            total_points = 2
        else:
            comments.append("D32 must be =D31-D30.")
    else:
        comments.append("D32 must contain a formula subtracting D30 from D31.")

    return {
        "total_points": total_points,
        "comment": " | ".join(comments) if comments else ""
    }
