# graders/annual_budget/grade_budget_formatting.py

def normalize_format(fmt: str) -> str:
    """Normalize number format string for consistent comparison."""
    return fmt.strip().lower().replace(" ", "")


def is_currency_two_decimals(fmt: str) -> bool:
    """
    Determines whether a number format represents currency with two decimals.
    Accepts formats containing a currency symbol and '0.00'.
    """
    f = normalize_format(fmt)
    return ("$" in f or "accounting" in f or "[$" in f) and "0.00" in f


def grade_budget_formatting(ws):
    """
    Grades formatting for D30 and D32.
    - Both must be currency with 2 decimals.
    - D30 worth 2 points
    - D32 worth 2 points
    Total: 4 points

    Comments do NOT reveal that only these two cells were checked.
    """

    results = {}
    total_points = 0.0
    comments = []

    target_cells = ["D30", "D32"]

    for cell_ref in target_cells:
        cell = ws[cell_ref]
        fmt = str(cell.number_format)
        entry = {"points": 0, "comment": ""}

        try:
            if is_currency_two_decimals(fmt):
                entry["points"] = 2
            else:
                entry["comment"] = f"{cell_ref} must be formatted as currency with two decimals."
                comments.append(entry["comment"])
        except Exception:
            entry["comment"] = f"Could not read formatting for {cell_ref}."
            comments.append(entry["comment"])

        total_points += entry["points"]
        results[cell_ref] = entry

    results["total_points"] = total_points
    results["comment"] = " | ".join(comments) if comments else ""

    return results
