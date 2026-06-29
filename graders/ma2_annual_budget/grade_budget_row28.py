# graders/annual_budget/grade_budget_row28.py

def normalize_formula(formula: str) -> str:
    """Normalize for consistent formula comparison."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )


def grade_budget_row28(ws):
    """
    Grades the Total Annual Budget formula in D28.

    Requirement:
    Must contain a SUM function over the exact range D18:D27.

    Full credit: 3 points
    """

    comments = []
    total_points = 0.0

    d28 = ws["D28"].value

    if isinstance(d28, str) and d28.startswith("="):
        f = normalize_formula(d28)

        # Accept any form that includes sum(...) and the correct range
        if f.startswith("=sum") and "d18:d27" in f:
            total_points = 3
        else:
            comments.append("D28 must contain =SUM(D18:D27).")
    else:
        comments.append("D28 must be a formula using =SUM(D18:D27).")

    return {
        "total_points": total_points,
        "comment": " | ".join(comments) if comments else ""
    }
