from openpyxl.styles.numbers import BUILTIN_FORMATS

def get_number_format(cell):
    """Return normalized number format for comparison."""
    fmt = cell.number_format.strip().lower()
    return fmt


def is_currency_format(fmt):
    """Currency format (two decimals)."""
    fmt = fmt.replace('[$$-409]', '$')  # Excel sometimes embeds locale tags
    return (
        "0.00" in fmt and
        ("$" in fmt or "accounting" in fmt)
    )


def is_percent_format(fmt):
    """Percentage with 2 decimals."""
    return fmt.endswith("0.00%") or fmt == "0.00%"


def is_integer_format(fmt):
    """Number with 0 decimals."""
    # Includes: "0", "#", "#,##0"
    cleaned = fmt.replace("#", "0")
    return cleaned in {"0", "0", "0", "0"} or cleaned.endswith("##0")


def grade_student_loans_formatting(ws):
    """
    Grades formatting for 12 required cells.

    Scoring:
        • Each correct formatting = 0.25 points
        • Total = 3 points
    """

    results = {}
    total_points = 0.0

    # -----------------------------
    # Expected formats
    # -----------------------------
    percent_cells = ["B14"]
    integer_cells = ["C24", "B27", "B28"]
    currency_cells = ["B29", "B30", "B31", "C25", "C26", "C29", "C30", "C31"]

    # -----------------------------
    # Helper for checking & scoring
    # -----------------------------
    def check_cell(cell_ref, condition_fn, expected_desc):
        nonlocal total_points
        cell = ws[cell_ref]
        fmt = get_number_format(cell)

        entry = {"points": 0, "comment": ""}

        try:
            if condition_fn(fmt):
                entry["points"] = 0.25
                entry["comment"] = f"{cell_ref} formatted correctly as {expected_desc}."
            else:
                entry["comment"] = (
                    f"{cell_ref} incorrect format. Expected {expected_desc}. "
                    f"Found '{fmt}'."
                )
        except Exception as e:
            entry["comment"] = f"Error checking {cell_ref}: {e}"

        total_points += entry["points"]
        results[cell_ref] = entry

    # -----------------------------
    # Run checks
    # -----------------------------
    for cell in percent_cells:
        check_cell(cell, is_percent_format, "percent with two decimals")

    for cell in integer_cells:
        check_cell(cell, is_integer_format, "number with 0 decimals")

    for cell in currency_cells:
        check_cell(cell, is_currency_format, "currency with two decimals")

    # -----------------------------
    # Final package
    # -----------------------------
    results["total_points"] = total_points
    results["comment"] = " | ".join([results[c]["comment"] for c in results if c != "total_points"])

    return results
