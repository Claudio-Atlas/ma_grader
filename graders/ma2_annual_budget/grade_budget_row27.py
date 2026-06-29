# graders/annual_budget/grade_budget_row27.py

from utilities.formula_equiv import formulas_equivalent


def normalize_formula(formula: str) -> str:
    """Normalize for easier formula comparison."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )


def grade_budget_row27(ws):
    """
    Grades ROW 27 of the Annual Budget tab.

    Requirements:
    B27 = 12  (1 point)
    C27 = ='Credit Cards'!C25  (2 points)
    D27 = annual cost formula using B27*C27  (2 points)

    Total = 5 points

    Returns:
    {
        "total_points": X,
        "comment": "Only incorrect comments"
    }
    """

    total_points = 0.0
    comments = []

    # -----------------------------
    # B27 — Frequency = 12
    # -----------------------------
    b27 = ws["B27"].value

    if b27 == 12:
        total_points += 1
    else:
        comments.append("B27 must be the number 12.")

    # -----------------------------
    # C27 — ='Credit Cards'!C25
    # -----------------------------
    c27 = ws["C27"].value

    if isinstance(c27, str) and c27.startswith("="):
        f = normalize_formula(c27)

        # Must include both "creditcards" and "c25"
        if ("creditcards" in f) and ("c25" in f):
            total_points += 2
        else:
            comments.append("C27 must reference 'Credit Cards'!C25.")
    else:
        comments.append("C27 must contain a formula referencing 'Credit Cards'!C25.")

    # -----------------------------
    # D27 — Must multiply B27 and C27
    # -----------------------------
    d27 = ws["D27"].value

    if isinstance(d27, str) and d27.startswith("="):
        f = normalize_formula(d27)

        if (("*" in f) and ("b27" in f) and ("c27" in f)) or \
                formulas_equivalent(d27, "=B27*C27"):
            total_points += 2
        else:
            comments.append("D27 must multiply B27 and C27.")
    else:
        comments.append("D27 must be a formula multiplying B27*C27.")

    # -----------------------------
    # Final output
    # -----------------------------
    final_comment = " | ".join(comments) if comments else ""

    return {
        "total_points": total_points,
        "comment": final_comment
    }
