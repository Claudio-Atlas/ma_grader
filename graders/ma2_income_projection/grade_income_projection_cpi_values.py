from graders.ma2_income_projection.load_cpi_data import get_cpi_value


def grade_income_projection_cpi_values(ws, ws_data=None):
    """
    Grades the CPI lookup table (rows 30-37) in the 'Income and Projection' tab.
    Total: 6 points (2 for month pattern, 2 for year increment, 2 for CPI values).

    ws_data (optional): the same sheet loaded data_only=True. The tab is graded
    formulas-only, so a year entered as a formula (e.g. =B30+1) would otherwise
    read as the string "=B30+1"; reading the calculated values here lets those
    "=previous+1" year formulas grade correctly.
    """
    start_row = 30
    end_row = 37
    rows_count = end_row - start_row + 1

    # Prefer calculated values (handles =previous+1 style formulas for the years).
    dv = ws_data if ws_data is not None else ws

    result = {"points": 0, "comment": "", "details": []}

    try:
        month_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
        }

        # ----------------------- 1) Month numbers -----------------------
        base_month = dv[f"A{start_row}"].value
        all_months = [dv[f"A{r}"].value for r in range(start_row, end_row + 1)]
        if all(m == base_month for m in all_months if m is not None):
            month_points = 2
            result["details"].append(f"All month numbers match ({base_month}).")
        else:
            month_points = 0
            result["details"].append("Month numbers in column A are not consistent.")

        # ----------------------- 2) Year increment ----------------------
        base_year = int(dv[f"B{start_row}"].value)
        expected_years = [base_year + i for i in range(rows_count)]
        actual_years = [int(dv[f"B{r}"].value) for r in range(start_row, end_row + 1)]
        if actual_years == expected_years:
            year_points = 2
            result["details"].append("Years increment correctly from the starting year.")
        else:
            year_points = 0
            result["details"].append(
                f"Year sequence incorrect. Expected {expected_years}, got {actual_years}"
            )

        # ----------------------- 3) CPI values ---------------------------
        # Only count rows we can actually verify. When the reference CPI isn't
        # available yet (recent months not in our data), don't penalize — flag
        # the row for manual review instead of marking it wrong.
        correct_cpi = 0
        checkable = 0
        unavailable = []
        for r in range(start_row, end_row + 1):
            year = dv[f"B{r}"].value
            month_num = dv[f"A{r}"].value
            cpi_value = dv[f"C{r}"].value

            if not (year and month_num and cpi_value):
                result["details"].append(f"Row {r}: missing data.")
                continue

            try:
                year = int(year)
                month_num = int(month_num)
                month_name = month_map.get(month_num, "Jan")
                student_cpi = float(cpi_value)
            except (TypeError, ValueError):
                result["details"].append(f"Row {r}: could not read year/month/CPI.")
                continue

            try:
                expected_cpi = get_cpi_value(year, month_name)  # raises if unavailable
            except ValueError:
                # Reference CPI not available for this month — can't auto-grade.
                unavailable.append(f"{month_name} {year}")
                result["details"].append(
                    f"Row {r}: [MANUAL REVIEW] CPI for {month_name} {year} not in "
                    f"reference data — verify by hand (student entered {student_cpi:.3f})."
                )
                continue

            checkable += 1
            if abs(student_cpi - expected_cpi) <= 0.01:
                correct_cpi += 1
                result["details"].append(f"Row {r}: CPI correct ({student_cpi:.3f}).")
            else:
                result["details"].append(
                    f"Row {r}: CPI mismatch (expected {expected_cpi:.3f}, got {student_cpi:.3f})."
                )

        # Score over the rows we could check (unavailable rows don't count against
        # the student). If none were checkable, give the benefit of the doubt.
        if checkable > 0:
            cpi_points = round((correct_cpi / checkable) * 2, 2)
        else:
            cpi_points = 2.0

        total_points = month_points + year_points + cpi_points
        result["points"] = total_points
        comment = (
            f"Months check: {month_points}/2, Years check: {year_points}/2, "
            f"CPI values: {cpi_points}/2 → Total {total_points}/6"
        )
        if unavailable:
            comment += (
                f" | [MANUAL REVIEW] {len(unavailable)} recent month(s) not in the "
                f"reference data ({', '.join(unavailable)}) — not counted against the student."
            )
        result["comment"] = comment

    except Exception as e:
        result["points"] = 0
        result["comment"] = f"Error grading CPI section: {e}"

    return result
