# graders/annual_budget/grade_budget_housing_other.py

from utilities.formula_equiv import formulas_equivalent


def normalize_formula(formula: str) -> str:
    """Normalize an Excel formula to make comparison easier."""
    return (
        formula.strip()
        .lower()
        .replace(" ", "")
        .replace("$", "")
        .replace("(", "")
        .replace(")", "")
    )


def grade_budget_housing_other(ws):
    """
    Grades the Housing → Other rows in the Annual Budget tab.

    Rows graded: 18–25
    Columns:
        B = Frequency per Year      (0.5 pts each → 4 pts total)
        C = Cost                    (0.5 pts each → 4 pts total)
        D = Total Annual Cost       (1.0 pts each → 8 pts total)

    Total: 16 points.

    Returns:
        {
            "total_points": float,
            "comment": "combined comments only for incorrect entries"
        }
    """

    total_points = 0.0
    comments = []

    # ----------------------------------------
    # Define ranges
    # ----------------------------------------
    for row in range(18, 26):  # 18–25 inclusive

        # ------------------------------------------------
        # B-column: Frequency per Year (0.5 points)
        # ------------------------------------------------
        freq_cell = ws[f"B{row}"]
        freq_val = freq_cell.value

        freq_points = 0.0

        if isinstance(freq_val, (int, float)) and (freq_val > 0) and (freq_val <= 52):
            freq_points = 0.5
        else:
            comments.append(
                f"B{row} frequency must be numeric, > 0, and ≤ 52."
            )

        total_points += freq_points

        # ------------------------------------------------
        # C-column: Cost (0.5 points)
        # ------------------------------------------------
        cost_cell = ws[f"C{row}"]
        cost_val = cost_cell.value

        cost_points = 0.0

        if isinstance(cost_val, (int, float)) and (cost_val > 0) and (cost_val < 1_000_000):
            cost_points = 0.5
        else:
            comments.append(
                f"C{row} cost must be numeric and greater than 0."
            )

        total_points += cost_points

        # ------------------------------------------------
        # D-column: Total Annual Cost (1 point)
        # Must be a formula referencing BOTH B[row] and C[row]
        # ------------------------------------------------
        dac_cell = ws[f"D{row}"]
        dac_formula = dac_cell.value

        dac_points = 0.0

        if isinstance(dac_formula, str) and dac_formula.startswith("="):

            f = normalize_formula(dac_formula)

            # Expected references
            b_ref = f"b{row}"
            c_ref = f"c{row}"

            # Check required pieces
            if (("*" in f) and (b_ref in f) and (c_ref in f)) or \
                    formulas_equivalent(dac_formula, f"=B{row}*C{row}"):
                dac_points = 1.0
            else:
                comments.append(
                    f"D{row} incorrect formula. Expected a multiplication using C{row} and B{row}."
                )
        else:
            comments.append(
                f"D{row} must contain a formula referencing C{row} and B{row}."
            )

        total_points += dac_points

    # ------------------------------------------------
    # Package results
    # ------------------------------------------------
    final_comment = " | ".join(comments) if comments else ""

    return {
        "total_points": total_points,
        "comment": final_comment
    }
