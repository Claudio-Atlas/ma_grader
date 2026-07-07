"""
check_formatting.py — Validates cell formatting in Visualization tab

Grading: 4 points for proper formatting

Cells to check:
- Bin table (E22:E24): Number with 2 decimal places
- Lower/Upper limits (D28:E38): Number with 2 decimal places
- Title of Bin (F28:F38): Number with 2 decimal places
- Frequency (G28:G38): Number with 0 decimal places
- Relative Frequency (H28:H38): Percentage with 0 decimal places
"""

from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _is_number_format_2dp(format_code: str) -> bool:
    """Check if format shows 2 decimal places."""
    if not format_code:
        return False
    return ".00" in format_code or "0.00" in format_code


def _is_number_format_0dp(format_code: str) -> bool:
    """Check if format shows 0 decimal places (integer).

    NOTE: Excel's default "General" is NOT counted as correct — an unformatted
    cell hasn't been explicitly formatted as an integer, and counting it inflated
    scores on blank sheets (the "11 of 58 correct when nothing was done" bug).
    """
    if not format_code or format_code == "General":
        return False
    # Explicit integer format like "0" or "#,##0"
    if format_code in ["0", "#,##0"]:
        return True
    # Number without a decimal portion
    if "0" in format_code and "." not in format_code:
        return True
    return False


def _is_percentage_format(format_code: str) -> bool:
    """Check if format is percentage."""
    if not format_code:
        return False
    return "%" in format_code


def check_visualization_formatting(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]]]:
    """
    Check formatting of cells in Visualization tab.
    
    Args:
        sheet: Visualization worksheet
        
    Returns:
        Tuple of (score, feedback_list)
    """
    feedback = []
    correct_count = 0
    total_checks = 0

    # Each category is (label, list-of-cells, format-test). We tally correct vs
    # total per category so the detailed feedback reflects the actual failing
    # cells (previously only the bin table reported problems, so the count and
    # the listed issues disagreed).
    categories = [
        ("E22:E24 (Bin Min/Max/Width — 2 decimals)",
         ["E22", "E23", "E24"], _is_number_format_2dp),
        ("D28:F38 (Limits & Bin Titles — 2 decimals)",
         [f"{c}{r}" for r in range(28, 39) for c in ("D", "E", "F")], _is_number_format_2dp),
        ("G28:G38 (Frequency — 0 decimals)",
         [f"G{r}" for r in range(28, 39)], _is_number_format_0dp),
        ("H28:H38 (Relative Frequency — percentage)",
         [f"H{r}" for r in range(28, 39)], _is_percentage_format),
    ]

    for label, cells, test in categories:
        cat_correct = 0
        for cell_ref in cells:
            total_checks += 1
            if test(sheet[cell_ref].number_format):
                cat_correct += 1
        correct_count += cat_correct
        # Report any category with formatting problems, showing how many.
        if cat_correct < len(cells):
            feedback.append(("VIS_FORMAT_CELL_WRONG", {
                "cell": f"{label}: {cat_correct}/{len(cells)} correct"
            }))

    # Calculate score (4 points total)
    score = round((correct_count / total_checks) * 4.0, 2)

    # Summary feedback
    if correct_count == total_checks:
        feedback = [("VIS_FORMAT_ALL_CORRECT", {})]
    else:
        feedback.insert(0, ("VIS_FORMAT_PARTIAL", {"correct": correct_count, "total": total_checks}))

    return score, feedback
