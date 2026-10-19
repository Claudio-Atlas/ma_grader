# graders/annual_budget/grade_budget_row26.py

from utilities.formula_equiv import formulas_equivalent


def normalize_formula(formula: str) -> str:
    """Normalize for easy formula comparison."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )


def grade_budget_row26(ws):
    """
    Grades ROW 26 of the Annual Budget tab.

    B26 = Frequency (must be 12) → 1 pt
    C26 = ='Student Loan'!B29 reference → 2 pts
    D26 = B26*C26 annual cost formula → 2 pts

    Total = 5 points

    Returns dict:
    {
        "total_points": X,
        "comment": "only incorrect comments"
    }
    """

    total_points = 0.0
    comments = []

    # -----------------------------
    # B26 — Frequency = 12
    # -----------------------------
    b26 = ws["B26"].value

    if b26 == 12:
        total_points += 1
    else:
        comments.append("The frequency for your subsidized loan payment (B26) should be 12, one payment a month.")

    # -----------------------------
    # C26 — ='Student Loan'!B29
    # -----------------------------
    c26 = ws["C26"].value

    if isinstance(c26, str) and c26.startswith("="):
        f = normalize_formula(c26)

        # Accept "student loan" or "student loans"
        if ("studentloan" in f or "studentloans" in f) and "b29" in f:
            total_points += 2
        else:
            comments.append("The subsidized loan cost (C26) should pull the payment straight from the Student Loans tab: ='Student Loan'!B29.")
    else:
        comments.append("The subsidized loan cost (C26) is typed in. Make it a formula that points at the Student Loans tab, ='Student Loan'!B29, so it updates automatically.")

    # -----------------------------
    # D26 — Annual cost = B26*C26
    # -----------------------------
    d26 = ws["D26"].value

    if isinstance(d26, str) and d26.startswith("="):
        f = normalize_formula(d26)

        if (("*" in f) and ("b26" in f) and ("c26" in f)) or \
                formulas_equivalent(d26, "=B26*C26"):
            total_points += 2
        else:
            comments.append("The Total Annual Cost for your subsidized loan (D26) should multiply the frequency by the cost: =B26*C26.")
    else:
        comments.append("The Total Annual Cost for your subsidized loan (D26) needs a formula: =B26*C26.")

    # -----------------------------
    # Final package
    # -----------------------------
    final_comment = " | ".join(comments) if comments else ""

    return {
        "total_points": total_points,
        "comment": final_comment
    }
