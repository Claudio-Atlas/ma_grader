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
                f"The frequency in B{row} should be how many times a year you pay this "
                f"(a number from 1 to 52)."
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
                f"The cost in C{row} should be a dollar amount greater than $0."
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
                    f"Your Total Annual Cost (D{row}) should multiply the cost by the "
                    f"frequency: =C{row}*B{row}."
                )
        else:
            comments.append(
                (f"Your Total Annual Cost (D{row}) is a typed number. Make it a formula, "
                 f"=C{row}*B{row}, so it updates if the cost or frequency changes.")
                if dac_formula not in (None, "") else
                f"Your Total Annual Cost (D{row}) is empty. Enter =C{row}*B{row}."
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
