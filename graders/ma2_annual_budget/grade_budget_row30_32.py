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
        # Use the equivalence engine as the authority: it respects parentheses
        # and exponents, so =D28*(1+D29) and =(1+D29)*D28 pass, but the wrong
        # =D28*(1+D29)^5 is correctly rejected. The old substring test stripped
        # parentheses and ignored "^", so it let the ^5 version through.
        if formulas_equivalent(val, "=D28*(1+D29)"):
            total_points = 3
        else:
            comments.append(
                "D30 must be =D28*(1+D29) or an equivalent form "
                "(note: raising to a power, e.g. ^5, is incorrect here)."
            )
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
