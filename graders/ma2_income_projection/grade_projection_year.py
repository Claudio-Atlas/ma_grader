def grade_projection_year(ws):
    """
    Grades the Projection Year in K32.
    Student should enter a value exactly 5 years greater than the final CPI year
    in B37. Accepts BOTH a typed number (e.g. 2030) AND the formula =B37+5 (or an
    equivalent, e.g. =5+B37). Binary grading: 1 point if correct, 0 if not.
    """
    from utilities.formula_equiv import formulas_equivalent

    result = {"points": 0, "comment": ""}

    try:
        raw = ws["K32"].value

        # --- Case 1: a formula (e.g. =B37+5) — accept any equivalent form ---
        if isinstance(raw, str) and raw.startswith("="):
            if formulas_equivalent(raw, "=B37+5"):
                result["points"] = 1
                result["comment"] = "Projection year formula (=B37+5) is correct."
            else:
                result["comment"] = "Projection year formula should be =B37+5 (five years after the final CPI year)."
            return result

        # --- Case 2: a typed number — must equal B37 + 5 ---
        last_cpi_year = ws["B37"].value
        if not (isinstance(last_cpi_year, (int, float)) and isinstance(raw, (int, float))):
            result["comment"] = "Missing or invalid year values in B37 or K32."
            return result

        expected_year = int(last_cpi_year) + 5
        if int(raw) == expected_year:
            result["points"] = 1
            result["comment"] = (
                f"Projection year correctly set 5 years after final CPI year ({int(last_cpi_year)} → {int(raw)})."
            )
        else:
            result["comment"] = (
                f"Projection year should be 5 years after final CPI year ({int(last_cpi_year)} → {expected_year})."
            )

    except Exception as e:
        result["comment"] = f"Error grading projection year: {e}"

    return result
