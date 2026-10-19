from openpyxl.worksheet.worksheet import Worksheet

def grade_income_projection_name(ws: Worksheet) -> dict:
    """
    Checks that the student entered their full name correctly in C1 (merged with D1).
    Requirements:
      - Cell C1 is not blank
      - Name has at least 10 characters (students may pad with 'X')

    Returns a dictionary with points and feedback.
    """
    result = {
        "points": 0,
        "comment": ""
    }

    try:
        cell_value = str(ws["C1"].value).strip() if ws["C1"].value else ""

        if not cell_value:
            result["points"] = 0
            result["comment"] = "Your name is missing. Type your full name in cell C1."
        elif len(cell_value) < 10:
            result["points"] = 0.5
            result["comment"] = (
                f"Your name in C1 (\u201c{cell_value}\u201d) needs at least 10 characters. "
                "If your name is shorter, pad it with X's as the instructions say."
            )
        else:
            result["points"] = 1
            result["comment"] = f"Name '{cell_value}' correctly entered."
    except Exception as e:
        result["points"] = 0
        result["comment"] = f"Error checking name cell: {e}"

    return result
