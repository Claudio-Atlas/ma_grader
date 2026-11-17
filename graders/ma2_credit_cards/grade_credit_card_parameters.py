from utilities.xl import load_workbook  # strips _xlfn. prefixes

def extract_credit_card_values(ws_random):
    """
    Reads reference randomized values from the Random tab.
    Returns a dictionary:
    {
        "apr": float,
        "balance": float,
        "payments_per_year": int,
        "min_percent": float,
        "fixed_min": float
    }
    """

    apr = ws_random["H21"].value
    balance = ws_random["H19"].value
    payments_per_year = 12      # Always 12
    min_percent = ws_random["H20"].value
    fixed_min = ws_random["H22"].value

    return {
        "apr": apr,
        "balance": balance,
        "payments_per_year": payments_per_year,
        "min_percent": min_percent,
        "fixed_min": fixed_min,
    }


def grade_credit_card_parameters(student_file_path):
    """
    Grades the 5 green-box parameters on the Credit Cards tab:
        C13 APR
        C14 Starting Balance
        C15 Payments per Year
        C17 Min %
        C18 Fixed Minimum
    Each worth 1 point; 0.5 when the right value was typed in the cell next
    to its green box (e.g. D17 instead of C17).

    Returns:
    {
        "C13": {...},
        "C14": {...},
        "C15": {...},
        "C17": {...},
        "C18": {...},
        "total_points": X,
        "comment": "...",
        "locations": {"C17": "D17", ...}  # only the misplaced ones
    }
    """

    wb = load_workbook(student_file_path, data_only=True)
    ws_cc = wb["Credit Cards"]
    ws_random = wb["Random"]

    ref = extract_credit_card_values(ws_random)

    checks = {
        "C13": ref["apr"]/100,
        "C14": ref["balance"],
        "C15": ref["payments_per_year"],
        "C17": ref["min_percent"]/100,
        "C18": ref["fixed_min"],
    }

    results = {}
    total = 0
    comments = []
    labels = {
        "C13": "APR", "C14": "starting balance", "C15": "payments per year",
        "C17": "minimum payment percentage", "C18": "fixed minimum payment",
    }

    def show(cell, v):
        if not isinstance(v, (int, float)):
            return f"\u201c{v}\u201d"
        if cell in ("C13", "C17") and v <= 1:
            return f"{v * 100:g}%"
        if cell in ("C14", "C18"):
            return f"${v:,.2f}".replace(".00", "")
        return f"{v:g}"

    def is_number(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    def as_number(v):
        if is_number(v):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.strip().replace(",", "").replace("$", ""))
            except ValueError:
                return None
        return None

    # Where each value actually is. Usually its own green cell; when that cell
    # is empty, a value typed one cell over (e.g. D17 instead of C17) is still
    # the student's parameter, and their table formulas point at it.
    locations = {}

    for cell, expected in checks.items():
        student_val = ws_cc[cell].value
        entry = {"points": 0, "comment": ""}

        if student_val in (None, ""):
            row = cell[1:]
            moved = next((f"{col}{row}" for col in "BDEF"
                          if as_number(ws_cc[f"{col}{row}"].value) is not None), None)
            if moved is None:
                entry["comment"] = (
                    f"Your {labels[cell]} ({cell}) is empty. Enter the value from the "
                    f"description in cell A3."
                )
            else:
                locations[cell] = moved
                found = as_number(ws_cc[moved].value)
                if abs(found - expected) < 0.01:
                    entry["points"] = 0.5
                    entry["comment"] = (
                        f"Your {labels[cell]} is in {moved} instead of {cell}. The value is right, "
                        f"but it belongs in the green box at {cell}."
                    )
                else:
                    entry["comment"] = (
                        f"Your {labels[cell]} is in {moved} instead of {cell}, and it's "
                        f"{show(cell, found)} where the description in cell A3 gives "
                        f"{show(cell, expected)}. Enter the right value in {cell}."
                    )
            total += entry["points"]
            results[cell] = entry
            comments.append(entry["comment"])
            continue

        if not is_number(student_val):
            number = as_number(student_val)
            if number is None:
                entry["comment"] = (
                    f"Your {labels[cell]} ({cell}) should be a number, but it contains "
                    f"{show(cell, student_val)}. Type just the number."
                )
                results[cell] = entry
                comments.append(entry["comment"])
                continue
            student_val = number

        # Compare with tolerance for percentages
        if abs(student_val - expected) < 0.01:
            entry["points"] = 1
            entry["comment"] = f"{cell} correct ({student_val})."
        else:
            entry["comment"] = (
                f"Your {labels[cell]} ({cell}) is {show(cell, student_val)}, but the "
                f"description in cell A3 gives {show(cell, expected)}. Double-check it against A3."
            )

        total += entry["points"]
        results[cell] = entry
        comments.append(entry["comment"])

    results["total_points"] = total
    results["locations"] = locations
    results["comment"] = " | ".join(comments)

    wb.close()
    return results
