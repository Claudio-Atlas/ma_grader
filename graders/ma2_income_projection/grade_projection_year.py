def grade_projection_year(ws):
    """
    Grades the Projection Year in K32.
    Student should enter a value exactly 5 years greater than the final CPI year in B37.
    Binary grading: 1 point if correct, 0 if not.
    """

    result = {"points": 0, "comment": ""}

    try:
        # Read student-provided values
        last_cpi_year = ws["B37"].value
        projected_year = ws["K32"].value

        # Validate both are numeric
        if not (isinstance(last_cpi_year, (int, float)) and isinstance(projected_year, (int, float))):
            result["comment"] = "Missing or invalid year values in B37 or K32."
            return result

        expected_year = int(last_cpi_year) + 5

        if int(projected_year) == expected_year:
            result["points"] = 1
            result["comment"] = (
                f"Projection year correctly set 5 years after final CPI year ({int(last_cpi_year)} → {int(projected_year)})."
            )
        else:
            result["comment"] = (
                f"Projection year should be 5 years after final CPI year ({int(last_cpi_year)} → {expected_year})."
            )

    except Exception as e:
        result["comment"] = f"Error grading projection year: {e}"

    return result
