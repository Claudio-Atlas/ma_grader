from graders.ma2_income_projection.load_cpi_data import get_cpi_value
from utilities.formula_equiv import cell_number


def grade_income_projection_cpi_values(ws, ws_data=None):
    """
    Grades the CPI lookup table (rows 30-37) in the 'Income and Projection' tab.
    Total: 6 points (2 for month pattern, 2 for year increment, 2 for CPI values).

    ws_data (optional): the same sheet loaded data_only=True. The tab is graded
    formulas-only, so a year entered as a formula (e.g. =B30+1) would otherwise
    read as the string "=B30+1"; reading the calculated values here lets those
    "=previous+1" year formulas grade correctly. Cells without a cached value
    (file never recalculated in Excel) fall back to the formulas sheet.
    """
    start_row = 30
    end_row = 37
    rows_count = end_row - start_row + 1

    def num(ref):
        return cell_number(ws, ws_data, ref)

    def as_int(x):
        return int(round(x)) if x is not None else None

    result = {"points": 0, "comment": "", "details": []}

    try:
        month_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
        }

        # ----------------------- 1) Month numbers -----------------------
        base_month = as_int(num(f"A{start_row}"))
        all_months = [as_int(num(f"A{r}")) for r in range(start_row, end_row + 1)]
        if all(m == base_month for m in all_months if m is not None):
            month_points = 2
            result["details"].append(f"All month numbers match ({base_month}).")
        else:
            month_points = 0
            result["details"].append("Month numbers in column A are not consistent.")

        # ----------------------- 2) Year increment ----------------------
        base_year = as_int(num(f"B{start_row}"))
        actual_years = [as_int(num(f"B{r}")) for r in range(start_row, end_row + 1)]
        expected_years = [base_year + i for i in range(rows_count)] if base_year is not None else None
        if expected_years is not None and actual_years == expected_years:
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
        missing_rows = 0  # blank/unreadable rows count against the student
        unavailable = []
        for r in range(start_row, end_row + 1):
            year = as_int(num(f"B{r}"))
            month_num = as_int(num(f"A{r}"))
            cpi_value = num(f"C{r}")

            raw_cpi = ws[f"C{r}"].value
            if cpi_value is None and year and month_num and isinstance(raw_cpi, str) and raw_cpi.startswith("="):
                # A lookup formula (VLOOKUP/INDEX...) with no cached value — we
                # can't compute it here, so flag it rather than mark it wrong.
                unavailable.append(f"row {r} (no calculated value)")
                result["details"].append(
                    f"Row {r}: [MANUAL REVIEW] CPI formula has no saved value "
                    f"(file not recalculated in Excel) — verify by hand."
                )
                continue

            if not (year and month_num and cpi_value):
                result["details"].append(f"Row {r}: missing data.")
                missing_rows += 1
                continue

            try:
                year = int(year)
                month_num = int(month_num)
                month_name = month_map.get(month_num, "Jan")
                student_cpi = float(cpi_value)
            except (TypeError, ValueError):
                result["details"].append(f"Row {r}: could not read year/month/CPI.")
                missing_rows += 1
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

        # Score over every row except those whose reference CPI is unavailable
        # (blank/unreadable rows count as wrong). Benefit of the doubt only when
        # every row was filled in but none could be checked against our data.
        graded_rows = checkable + missing_rows
        if graded_rows > 0:
            cpi_points = round((correct_cpi / graded_rows) * 2, 2)
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
                f" | [MANUAL REVIEW] {len(unavailable)} CPI value(s) couldn't be "
                f"auto-checked ({', '.join(unavailable)}) — not counted against the student."
            )
        result["comment"] = comment

    except Exception as e:
        result["points"] = 0
        result["comment"] = f"Error grading CPI section: {e}"

    return result
