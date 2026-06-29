import json
import os

# Path to the pre-exported mortgage rates JSON (sits next to this module).
# Resolve relative to __file__ so it works regardless of the working directory
# and when the engine source is bundled into the packaged app.
JSON_PATH = os.path.join(os.path.dirname(__file__), "mortgage_rates.json")


def load_mortgage_rates():
    """Load the locally-saved mortgage rate reference file."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def grade_mortgage_rate_lookup(ws):
    """
    Grades the student's mortgage rate lookup on the 'Student Loans' tab.

    B12 → Year (e.g., 2023)
    B13 → Month number (1–12)
    B14 → Student's entered mortgage rate (should be formatted as a percent)

    Scoring:
        1 point if student's entered rate matches JSON value within ±0.05%.
    Returns:
        {
            "B14": {"points": X, "comment": "..."},
            "total_points": X
        }
    """
    result = {"points": 0, "comment": ""}

    try:
        year_cell = ws["B12"].value
        month_cell = ws["B13"].value
        student_val = ws["B14"].value

        # --- Validate inputs ---
        if year_cell is None or month_cell is None or student_val is None:
            result["comment"] = "Missing year (B12), month (B13), or mortgage rate (B14)."
            return {
                "B14": result,
                "total_points": 0
            }

        year = str(int(year_cell))
        month = str(int(month_cell))

        # --- Load reference data ---
        rates = load_mortgage_rates()
        ref_val = rates.get(year, {}).get(month, None)

        if ref_val is None:
            result["comment"] = (
                f"No reference rate found for {month}/{year} (check Mortgage Rates tab)."
            )
            return {"B14": result, "total_points": 0}

        # --- Normalize student's entry ---
        try:
            student_num = float(student_val)
        except Exception:
            result["comment"] = "Mortgage rate (B14) must be numeric."
            return {"B14": result, "total_points": 0}

        # Convert decimal to percent if needed
        if student_num < 1:
            student_percent = student_num * 100
        else:
            student_percent = student_num

        # --- Compare within tolerance ---
        tolerance = 0.05  # ±0.05%
        if abs(student_percent - ref_val) <= tolerance:
            result["points"] = 1
            result["comment"] = (
                f"Correct mortgage rate ({student_percent:.2f}% matches {ref_val:.2f}%)."
            )
        else:
            result["comment"] = (
                f"Incorrect mortgage rate. Expected ≈ {ref_val:.2f}%, "
                f"you entered {student_percent:.2f}%."
            )

    except Exception as e:
        result["comment"] = f"Error grading mortgage rate lookup: {e}"

    # --- Final return structure (matches your spec) ---
    return {
        "B14": result,
        "total_points": result["points"],
    }
