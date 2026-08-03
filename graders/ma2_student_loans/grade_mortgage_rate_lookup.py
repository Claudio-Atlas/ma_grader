import json
import os

# Fallback reference file (only used if the workbook has no Mortgage Rates tab).
JSON_PATH = os.path.join(os.path.dirname(__file__), "mortgage_rates.json")


def load_mortgage_rates():
    """Load the locally-saved mortgage rate reference file (fallback only)."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _rate_from_tab(mortgage_ws, year, month):
    """Look up the reference rate on the workbook's own 'Mortgage Rates' tab.

    Layout: column A holds the year; months run Jan..Dec across columns B..M
    (Jan = column 2, so month m lives in column m + 1). Returns a float, or None
    if the year/month cell isn't present or is blank.
    """
    if mortgage_ws is None:
        return None
    if not (1 <= month <= 12):
        return None
    target_col = month + 1  # Jan(1)->B(2), ... Dec(12)->M(13)
    for row in range(1, mortgage_ws.max_row + 1):
        a = mortgage_ws.cell(row=row, column=1).value
        try:
            if a is not None and int(a) == year:
                v = mortgage_ws.cell(row=row, column=target_col).value
                return float(v) if isinstance(v, (int, float)) else None
        except (TypeError, ValueError):
            continue
    return None


def grade_mortgage_rate_lookup(ws, mortgage_ws=None):
    """
    Grades the student's mortgage rate lookup on the 'Student Loans' tab.

    B12 → Year   B13 → Month number (1-12)   B14 → student's entered rate

    The expected rate is read from the workbook's own 'Mortgage Rates' tab (so it
    never goes stale); the bundled JSON is only a fallback. B14 is interpreted
    according to its number format: in a percent-formatted cell the stored value
    is a fraction (0.0744 -> 7.44%), so a raw 7.44 there actually means 744% and
    is wrong.

    Scoring: 1 point if the entered rate matches within ±0.05 percentage points.
    """
    result = {"points": 0, "comment": ""}

    try:
        year_cell = ws["B12"].value
        month_cell = ws["B13"].value
        b14 = ws["B14"]
        student_val = b14.value

        if year_cell is None or month_cell is None or student_val is None:
            result["comment"] = "Missing year (B12), month (B13), or mortgage rate (B14)."
            return {"B14": result, "total_points": 0}

        year = int(year_cell)
        month = int(month_cell)

        # --- Expected rate: prefer the workbook's Mortgage Rates tab ---
        ref_val = _rate_from_tab(mortgage_ws, year, month)
        if ref_val is None:
            rates = load_mortgage_rates()
            ref_val = rates.get(str(year), {}).get(str(month), None)

        if ref_val is None:
            result["comment"] = (
                f"No reference rate found for {month}/{year} (check the Mortgage Rates tab)."
            )
            return {"B14": result, "total_points": 0}

        # --- Interpret the student's entry using its number format ---
        try:
            student_num = float(student_val)
        except (TypeError, ValueError):
            result["comment"] = "Mortgage rate (B14) must be numeric."
            return {"B14": result, "total_points": 0}

        is_percent_formatted = "%" in str(b14.number_format)
        if is_percent_formatted:
            # Stored value is a fraction; the displayed percent is value*100.
            # (0.0744 -> 7.44%;  7.44 -> 744%, which is wrong.)
            student_percent = student_num * 100
        else:
            # Plain number: treat as a percent figure, but a sub-1 value was
            # almost certainly typed as a decimal fraction (0.0744 -> 7.44%).
            student_percent = student_num * 100 if student_num < 1 else student_num

        tolerance = 0.05  # ±0.05 percentage points
        if abs(student_percent - ref_val) <= tolerance:
            result["points"] = 1
            result["comment"] = (
                f"Correct mortgage rate ({student_percent:.2f}% matches {ref_val:.2f}%)."
            )
        else:
            result["comment"] = (
                f"Incorrect mortgage rate. Expected ≈ {ref_val:.2f}%, "
                f"your entry reads as {student_percent:.2f}%."
            )

    except Exception as e:
        result["comment"] = f"Error grading mortgage rate lookup: {e}"

    return {"B14": result, "total_points": result["points"]}
