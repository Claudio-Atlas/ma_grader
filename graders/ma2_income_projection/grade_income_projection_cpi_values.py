from graders.ma2_income_projection.load_cpi_data import get_cpi_value

def grade_income_projection_cpi_values(ws):
    """
    Grades the CPI lookup table (rows 29–37) in the 'Income and Projection' tab.
    Total: 6 points (2 for month pattern, 2 for year increment, 2 for correct CPI values)
    """
    start_row = 30
    end_row = 37
    rows_count = end_row - start_row + 1

    result = {
        "points": 0,
        "comment": "",
        "details": []
    }

    try:
        # -----------------------
        # 1️⃣ Check Month Numbers
        # -----------------------
        base_month = ws[f"A{start_row}"].value
        all_months = [ws[f"A{r}"].value for r in range(start_row, end_row + 1)]

        if all(m == base_month for m in all_months if m is not None):
            month_points = 2
            result["details"].append(f"✅ All month numbers match ({base_month}).")
        else:
            month_points = 0
            result["details"].append("❌ Month numbers in column A are not consistent.")

        # -----------------------
        # 2️⃣ Check Year Increment
        # -----------------------
        base_year = int(ws[f"B{start_row}"].value)
        expected_years = [base_year + i for i in range(rows_count)]
        actual_years = [int(ws[f"B{r}"].value) for r in range(start_row, end_row + 1)]

        if actual_years == expected_years:
            year_points = 2
            result["details"].append("✅ Years increment correctly from starting year.")
        else:
            year_points = 0
            result["details"].append(
                f"❌ Year sequence incorrect. Expected {expected_years}, got {actual_years}"
            )

        # -----------------------
        # 3️⃣ Check CPI Values
        # -----------------------
        correct_cpi = 0
        for i, r in enumerate(range(start_row, end_row + 1)):
            year = int(ws[f"B{r}"].value)
            month_num = int(ws[f"A{r}"].value)
            cpi_value = ws[f"C{r}"].value

            if not (year and month_num and cpi_value):
                result["details"].append(f"Row {r}: missing data.")
                continue

            # Convert month number → month abbreviation
            month_map = {
                1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
            }
            month_name = month_map.get(month_num, "Jan")

            try:
                # ✅ Ensure both arguments are correct types
                expected_cpi = get_cpi_value(int(year), month_name)
                student_cpi = float(cpi_value)

                if abs(student_cpi - expected_cpi) <= 0.01:
                    correct_cpi += 1
                    result["details"].append(
                        f"Row {r}: ✅ CPI correct ({student_cpi:.3f})"
                    )
                else:
                    result["details"].append(
                        f"Row {r}: ❌ CPI mismatch (expected {expected_cpi:.3f}, got {student_cpi:.3f})"
                    )
            except Exception as e:
                result["details"].append(f"Row {r}: error checking CPI ({e})")

        # Full credit if all rows correct, proportional otherwise
        cpi_points = round((correct_cpi / rows_count) * 2, 2)

        # -----------------------
        # Total Points + Summary
        # -----------------------
        total_points = month_points + year_points + cpi_points
        result["points"] = total_points
        result["comment"] = (
            f"Months check: {month_points}/2, Years check: {year_points}/2, "
            f"CPI values: {cpi_points}/2 → Total {total_points}/6"
        )

    except Exception as e:
        result["points"] = 0
        result["comment"] = f"Error grading CPI section: {e}"

    return result
