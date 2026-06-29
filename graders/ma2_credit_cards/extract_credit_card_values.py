# graders/credit_card/extract_credit_card_values.py

from openpyxl import load_workbook

def extract_credit_card_values(student_file_path):
    """
    Extracts the four randomized values used in the Credit Card tab.
    These values are generated in the hidden 'Random' sheet.

    Random!H19 → credit card balance (dollars)
    Random!H20 → minimum payment percent (e.g., 2.5)
    Random!H22 → fixed minimum payment (dollars)
    Random!H21 → APR (annual percentage rate, e.g., 24)

    Returns a dictionary:
        {
            "balance":  float,
            "min_percent": float,
            "fixed_min": float,
            "apr": float
        }
    """

    wb = load_workbook(student_file_path, data_only=True)

    # Hidden sheet is still accessible even if Excel hides it
    ws_rand = wb["Random"]

    try:
        balance     = ws_rand["H19"].value
        min_percent = ws_rand["H20"].value
        apr_percent = ws_rand["H21"].value
        fixed_min   = ws_rand["H22"].value

        # Convert all to floats to protect downstream grading
        extracted = {
            "balance": float(balance),
            "min_percent": float(min_percent),
            "fixed_min": float(fixed_min),
            "apr": float(apr_percent)
        }

    except Exception as e:
        raise ValueError(f"Error extracting credit card values from Random sheet: {e}")

    wb.close()
    return extracted
