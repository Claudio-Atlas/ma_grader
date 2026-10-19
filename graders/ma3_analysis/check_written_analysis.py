"""
check_written_analysis.py — Extracts written analysis for manual grading

Grading: 5 points (manual grading by instructor)
    - 2 pts: Correctly indicates improvement
    - 2 pts: Interprets lower/upper bounds
    - 1 pt: Grammar, punctuation, spelling

The written response is in the area around row 43 (merged cells).
We extract the text and copy it to the grading sheet for instructor review.
"""

from typing import Tuple, List
from openpyxl.worksheet.worksheet import Worksheet


def _find_written_response(sheet: Worksheet) -> str:
    """
    Search for the written response in the Analysis sheet.
    
    The response is typically in a merged cell area around rows 40-50.
    We look for cells with substantial text content.
    """
    # Search area - the written response section
    search_rows = range(39, 55)
    search_cols = ["F", "G", "B", "C", "D", "E"]
    
    found_text = ""
    
    for row in search_rows:
        for col in search_cols:
            cell = sheet[f"{col}{row}"]
            value = cell.value
            
            if value and isinstance(value, str):
                text = value.strip()
                
                # Skip instruction text (starts with numbers or contains "5b")
                if text and not text[0].isdigit():
                    # Skip the sheet's own short labels. Only short text (or text
                    # that STARTS with a label) counts: a real answer is expected
                    # to mention "68%" and the bounds, so a plain substring test
                    # threw away exactly the answers we're looking for.
                    skip_labels = [
                        "lower bound", "upper bound", "68%", "answer:",
                        "legend", "if a cell", "you should"
                    ]
                    low = text.lower()
                    is_label = any(low.startswith(label) for label in skip_labels) or (
                        len(text) < 60 and any(label in low for label in skip_labels)
                    )
                    
                    if not is_label and len(text) > 50:
                        # This looks like the student's written response
                        if len(text) > len(found_text):
                            found_text = text
    
    # Also specifically check row 43 column F/G area
    for col in ["F", "G", "B"]:
        cell = sheet[f"{col}43"]
        value = cell.value
        if value and isinstance(value, str) and len(value.strip()) > len(found_text):
            text = value.strip()
            if not text[0].isdigit() and len(text) > 30:
                found_text = text
    
    return found_text


def model_answer(values_sheet) -> str:
    """The expected sentence, using this student's own empirical-rule bounds
    (G36/G37), so the instructor can compare at a glance."""
    if values_sheet is None:
        return ""
    lo, hi = values_sheet["G36"].value, values_sheet["G37"].value
    if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
        return ""
    direction = "an increase" if lo > 0 or (lo + hi) / 2 > 0 else "a change"
    return (
        "According to the empirical rule, approximately 68% of the students should "
        f"expect to see {direction} in their scores between {lo:.2f} and {hi:.2f} points."
    )


def check_written_analysis(sheet: Worksheet) -> Tuple[float, List[Tuple[str, dict]], str]:
    """
    Extract written analysis for manual grading.
    
    Args:
        sheet: Analysis worksheet
        
    Returns:
        Tuple of (score, feedback_list, written_text)
        - score is 0 (manual grading required)
        - feedback contains the extracted text for instructor review
        - written_text is the raw text for the grading sheet
    """
    feedback = []
    
    written_text = _find_written_response(sheet)
    
    if not written_text:
        feedback.append(("WRITTEN_MISSING", {}))
        return 0.0, feedback, ""
    
    if len(written_text) < 50:
        feedback.append(("WRITTEN_TOO_SHORT", {"length": len(written_text)}))
        # Still include the text for review
        feedback.append(("WRITTEN_FOUND", {"text": written_text[:500]}))
        return 0.0, feedback, written_text
    
    # Truncate for feedback display if very long
    display_text = written_text[:500]
    if len(written_text) > 500:
        display_text += "..."
    
    feedback.append(("WRITTEN_FOUND", {"text": display_text}))
    
    # Return 0 score - instructor must manually grade
    # The written_text is passed to the writer to put in the grading sheet
    return 0.0, feedback, written_text
