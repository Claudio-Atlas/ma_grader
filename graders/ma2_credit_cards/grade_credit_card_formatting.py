# graders/credit_cards/grade_credit_card_formatting.py

from openpyxl import load_workbook

def _is_currency(fmt):
    """Currency format (two decimals)."""
    fmt = fmt.replace('[$$-409]', '$')  # Excel sometimes embeds locale tags
    return (
        "0.00" in fmt and
        ("$" in fmt or "accounting" in fmt)
    )

def _is_percentage(fmt: str) -> bool:
    if not isinstance(fmt, str):
        return False
    fmt = fmt.lower().replace(" ", "")
    return "%" in fmt or "0.00%" in fmt or "percent" in fmt

def _has_two_decimals(fmt: str) -> bool:
    if not isinstance(fmt, str):
        return False
    # A reliable check: look for ".00" or similar patterns
    return "0.00" in fmt or ".00" in fmt

def _has_zero_decimals(fmt: str) -> bool:
    if not isinstance(fmt, str):
        return False
    # Looks for whole-number formatting
    fmt = fmt.replace(" ", "")
    return fmt == "0" or fmt == "0_);(0)" or fmt.startswith("0") and ".00" not in fmt


def grade_credit_card_formatting(student_file_path):
    """
    Checks formatting requirements on the 'Credit Cards' tab.
    Each cell worth 0.25 points.
    Total: 2.0 points.

    Requirements:
        C13: percent, 2 decimals
        C14: currency, 2 decimals
        C17: percent, 2 decimals
        C18: currency, 2 decimals
        J25: number, 2 decimals
        J26: currency, 2 decimals
        J27: currency, 2 decimals
        C40: currency, 2 decimals
    """

    wb = load_workbook(student_file_path, data_only=False)
    ws = wb["Credit Cards"]

    checks = {
        "C13": {"type": "percent", "decimals": 2},
        "C14": {"type": "currency", "decimals": 2},
        "C17": {"type": "percent", "decimals": 2},
        "C18": {"type": "currency", "decimals": 2},
        "J25": {"type": "number",  "decimals": 2},
        "J26": {"type": "currency", "decimals": 2},
        "J27": {"type": "currency", "decimals": 2},
        "C40": {"type": "currency", "decimals": 2},
    }

    results = {}
    total_points = 0

    for cell, rule in checks.items():
        fmt = ws[cell].number_format
        entry = {"points": 0, "comment": ""}

        fmt_ok = True

        # ---- TYPE CHECK ----
        if rule["type"] == "currency":
            if not _is_currency(fmt):
                fmt_ok = False
                entry["comment"] += f"{cell} should be currency format. "
        elif rule["type"] == "percent":
            if not _is_percentage(fmt):
                fmt_ok = False
                entry["comment"] += f"{cell} should be percentage format. "
        elif rule["type"] == "number":
            # Must NOT look like currency/percent
            if _is_currency(fmt) or _is_percentage(fmt):
                fmt_ok = False
                entry["comment"] += f"{cell} should be a regular number (not currency/percent). "

        # ---- DECIMAL CHECK ----
        if rule["decimals"] == 2:
            if not _has_two_decimals(fmt):
                fmt_ok = False
                entry["comment"] += f"{cell} should display two decimals. "
        elif rule["decimals"] == 0:
            if not _has_zero_decimals(fmt):
                fmt_ok = False
                entry["comment"] += f"{cell} should have no decimals. "

        # Award points
        if fmt_ok:
            entry["points"] = 0.5
            entry["comment"] = f"{cell} formatting correct."
        else:
            entry["comment"] = entry["comment"].strip()

        total_points += entry["points"]
        results[cell] = entry

    wb.close()

    results["total_points"] = total_points
    results["comment"] = " | ".join([f"{c}: {r['comment']}" for c, r in results.items() if c in checks])

    return results
