"""
check_scatterplot.py — Validate scatterplot chart on Income Analysis tab

Purpose: Checks that students have created a proper XY scatter chart with:
         - The chart itself present and using correct data
         - Appropriate title and axis labels
         - A trendline
         - Trendline extended to show predictions (8-24 years range)

Author: Clayton Ragsdale
Dependencies: openpyxl chart objects

Grading Breakdown (8 points total, split into two rows):
    Row 6 (F6) - Chart & Labels (6 points):
        - XY-Scatterplot of BLS data present: 3 points
        - Appropriate title: 1 point
        - X-axis label: 1 point
        - Y-axis label: 1 point
    
    Row 7 (F7) - Trendline (2 points):
        - Trendline added: 1 point
        - Trendline extended (8 years left, 24 years right): 1 point
"""

from typing import Tuple, List, Dict, Any, Optional
import re
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.chart import ScatterChart
from openpyxl.chart.series import XYSeries


def _check_chart_data_source(scatter_chart) -> Tuple[str, str]:
    """
    Check if the scatter chart uses the correct BLS data.

    The correct data should be from columns A (years of education) and B (income).
    WRONG data would be using column E (predicted income) or column D.

    Returns:
        Tuple of:
            - str: "correct", "wrong", or "unverify" (couldn't read the refs)
            - str: Description of what data was found
    """
    if scatter_chart is None or not hasattr(scatter_chart, 'series'):
        return "unverify", "No chart series found"
    
    for series in scatter_chart.series:
        # Check X values (should be column A - years of education from BLS data)
        x_ref = None
        y_ref = None
        
        # Get X values reference
        if hasattr(series, 'xVal') and series.xVal is not None:
            if hasattr(series.xVal, 'numRef') and series.xVal.numRef is not None:
                x_ref = getattr(series.xVal.numRef, 'f', None)
        
        # Get Y values reference  
        if hasattr(series, 'yVal') and series.yVal is not None:
            if hasattr(series.yVal, 'numRef') and series.yVal.numRef is not None:
                y_ref = getattr(series.yVal.numRef, 'f', None)
        
        # Also try val attribute (alternative structure)
        if hasattr(series, 'val') and series.val is not None:
            if hasattr(series.val, 'numRef') and series.val.numRef is not None:
                if y_ref is None:
                    y_ref = getattr(series.val.numRef, 'f', None)
        
        # Analyze the references
        # Correct X data: Column A (e.g., 'Income Analysis'!$A$19:$A$26)
        # Correct Y data: Column B (e.g., 'Income Analysis'!$B$19:$B$26)
        # WRONG Y data: Column E (predicted values)
        
        x_ref_str = str(x_ref).upper() if x_ref else ""
        y_ref_str = str(y_ref).upper() if y_ref else ""
        
        # Check if Y data uses column E (predictions) - this is WRONG
        if y_ref_str and ('$E$' in y_ref_str or ':E' in y_ref_str or 'E:' in y_ref_str or y_ref_str.endswith('E')):
            return "wrong", f"Chart uses predicted values (column E) instead of actual BLS data. Y-ref: {y_ref}"

        # Check if Y data uses column D (prediction years) - also WRONG
        if y_ref_str and ('$D$' in y_ref_str or ':D' in y_ref_str or 'D:' in y_ref_str):
            if x_ref_str and ('$E$' in x_ref_str or ':E' in x_ref_str):
                return "wrong", f"Chart uses prediction data instead of BLS data. X-ref: {x_ref}, Y-ref: {y_ref}"

        # Check if correct columns are used (A for X, B for Y)
        x_uses_a = x_ref_str and ('$A$' in x_ref_str or ':A' in x_ref_str or 'A:' in x_ref_str)
        y_uses_b = y_ref_str and ('$B$' in y_ref_str or ':B' in y_ref_str or 'B:' in y_ref_str)

        if x_uses_a and y_uses_b:
            return "correct", f"Correct BLS data used. X-ref: {x_ref}, Y-ref: {y_ref}"

        # If we can't determine, check for column E explicitly as wrong
        if '$E' in x_ref_str or '$E' in y_ref_str:
            return "wrong", f"Chart appears to use prediction column E. X-ref: {x_ref}, Y-ref: {y_ref}"

    # Couldn't read/confirm the data references — flag for manual review.
    return "unverify", "Could not read the chart's data references"


def _has_connecting_lines(chart) -> bool:
    """
    Conservatively detect whether the data points are joined by connecting lines
    (i.e. it's a 'scatter with lines' rather than a markers-only scatter plot).

    We return True only when we POSITIVELY see a drawn line, so a correct
    markers-only chart is never penalized by accident:
      - scatterStyle 'line' / 'smooth'  -> lines, no markers
      - a data series with an explicit drawn line (not noFill)
    The trendline is a separate object and is NOT considered here.
    """
    style = str(getattr(chart, "scatterStyle", "") or "").lower()
    if style in ("line", "smooth"):
        return True

    for s in getattr(chart, "series", []):
        gp = getattr(s, "graphicalProperties", None)
        ln = getattr(gp, "line", None) if gp is not None else None
        if ln is None:
            continue
        if getattr(ln, "noFill", False):
            continue  # this series explicitly has no line — markers only
        # The only reliable signal of a drawn line is an actual color fill.
        # (openpyxl/Excel set prstDash='solid' and a line object by default even
        # for markers-only charts, so those must NOT count.)
        if (getattr(ln, "solidFill", None) is not None
                or getattr(ln, "gradFill", None) is not None):
            return True
    return False


def _extract_text_from_title(title_obj) -> str:
    """
    Extract plain text from an openpyxl chart title or axis title object.
    
    The title can be a simple string or a complex RichText object.
    This function handles both cases and extracts the actual text content.
    """
    if title_obj is None:
        return ""
    
    # If it's already a string, return it
    if isinstance(title_obj, str):
        return title_obj.strip()
    
    # Try to get text from RichText structure
    # The text is typically in nested Paragraph -> RegularTextRun -> t attributes
    title_str = str(title_obj)
    
    # Extract all t='...' values from the string representation
    texts = re.findall(r"t='([^']*)'", title_str)
    if texts:
        # Join the text parts and clean up
        result = ' '.join(t for t in texts if t.strip())
        return result.strip()
    
    # Fallback: try common attributes
    if hasattr(title_obj, 'text') and title_obj.text:
        return str(title_obj.text).strip()
    
    return ""


def check_scatterplot(ws: Worksheet) -> Tuple[float, float, List[Tuple[str, Dict[str, Any]]]]:
    """
    Check the scatterplot chart on the Income Analysis worksheet.
    
    Returns TWO separate scores for the grading sheet:
        - chart_labels_score (F6): Chart present + title + axis labels (0-6 pts)
        - trendline_score (F7): Trendline + extension (0-2 pts)
    
    Grading Logic:
        Chart & Labels (6 points for F6):
            - 3 points: XY Scatter chart exists
            - 1 point: Chart has a title
            - 1 point: X-axis has a label
            - 1 point: Y-axis has a label
        
        Trendline (2 points for F7):
            - 1 point: Any series has a trendline
            - 1 point: Trendline extended to cover prediction range
    
    Args:
        ws: The openpyxl Worksheet object for the Income Analysis tab
    
    Returns:
        Tuple of:
            - chart_labels_score: float (0-6) for F6
            - trendline_score: float (0-2) for F7
            - feedback: List of (code, params) tuples describing each check
    
    Example:
        >>> chart_score, trendline_score, feedback = check_scatterplot(worksheet)
        >>> print(f"Chart & Labels: {chart_score}/6, Trendline: {trendline_score}/2")
    """
    chart_labels_score = 0.0  # For F6 (max 6)
    trendline_score = 0.0     # For F7 (max 2)
    feedback: List[Tuple[str, Dict[str, Any]]] = []
    
    # ============================================================
    # Step 1: Find a scatter chart on the worksheet
    # ============================================================
    scatter_chart: Optional[ScatterChart] = None
    
    # Get all charts from the worksheet
    charts = getattr(ws, '_charts', [])
    
    for chart in charts:
        if isinstance(chart, ScatterChart):
            scatter_chart = chart
            break
    
    # Check if we found a scatter chart
    if scatter_chart is None:
        # No scatter chart found
        feedback.append(("IA_SCATTER_NOT_FOUND", {}))
        # Return early - can't check other criteria without a chart
        return 0.0, 0.0, feedback
    
    # ============================================================
    # Step 2: Chart Present - XY Scatter (3 points) → F6
    # ============================================================
    # If we got here, we found a scatter chart
    # But we need to verify it uses the CORRECT data (BLS data from columns A & B)
    # NOT the predicted values from column E
    
    data_state, data_source_info = _check_chart_data_source(scatter_chart)

    if data_state == "correct":
        # Full credit - correct BLS data used
        chart_labels_score += 3.0
        feedback.append(("IA_SCATTER_FOUND", {"data_source": "correct"}))

        # A scatter plot should show markers only (plus the trendline). If the
        # data points are joined by connecting lines, deduct 1 point.
        if _has_connecting_lines(scatter_chart):
            chart_labels_score -= 1.0
            feedback.append(("IA_SCATTER_HAS_LINES", {
                "note": "Data points are connected with lines. A scatter plot "
                        "should show markers only (the trendline is separate). -1 point."
            }))
    elif data_state == "wrong":
        # Partial credit (1/3) - chart exists but uses wrong data
        chart_labels_score += 1.0
        feedback.append(("IA_SCATTER_WRONG_DATA", {
            "message": "Chart uses incorrect data. Should use BLS data (columns A & B), not predicted values.",
            "detail": data_source_info,
            "points_earned": 1.0,
            "points_possible": 3.0
        }))
    else:
        # Data source couldn't be read — flag for manual review (0 pending).
        feedback.append(("IA_SCATTER_DATA_UNVERIFIED", {
            "message": "[MANUAL REVIEW] Could not read the chart's data source "
                       "automatically. Confirm it plots the BLS data (columns A & B) "
                       "and award up to 3 of the chart points.",
            "detail": data_source_info,
            "points_earned": 0.0,
            "points_possible": 3.0
        }))
    
    # ============================================================
    # Step 3: Check Title (1 point) → F6
    # ============================================================
    title_text = _extract_text_from_title(scatter_chart.title)
    
    if title_text:
        chart_labels_score += 1.0
        feedback.append(("IA_SCATTER_TITLE_PRESENT", {"title": title_text}))
    else:
        feedback.append(("IA_SCATTER_TITLE_MISSING", {}))
    
    # ============================================================
    # Step 4: Check X-Axis Label (1 point) → F6
    # ============================================================
    x_axis = scatter_chart.x_axis
    
    if x_axis is not None:
        x_label = _extract_text_from_title(x_axis.title)
        
        if x_label:
            chart_labels_score += 1.0
            feedback.append(("IA_SCATTER_XLABEL_PRESENT", {"label": x_label}))
        else:
            feedback.append(("IA_SCATTER_XLABEL_MISSING", {}))
    else:
        feedback.append(("IA_SCATTER_XLABEL_MISSING", {}))
    
    # ============================================================
    # Step 5: Check Y-Axis Label (1 point) → F6
    # ============================================================
    y_axis = scatter_chart.y_axis
    
    if y_axis is not None:
        y_label = _extract_text_from_title(y_axis.title)
        
        if y_label:
            chart_labels_score += 1.0
            feedback.append(("IA_SCATTER_YLABEL_PRESENT", {"label": y_label}))
        else:
            feedback.append(("IA_SCATTER_YLABEL_MISSING", {}))
    else:
        feedback.append(("IA_SCATTER_YLABEL_MISSING", {}))
    
    # ============================================================
    # Step 6: Check Trendline (1 point) → F7
    # ============================================================
    has_trendline = False
    trendline_obj = None
    
    # Check each series for a trendline
    for series in scatter_chart.series:
        if hasattr(series, 'trendline') and series.trendline is not None:
            has_trendline = True
            trendline_obj = series.trendline
            break
    
    if has_trendline:
        trendline_score += 1.0
        feedback.append(("IA_SCATTER_TRENDLINE_PRESENT", {}))
    else:
        feedback.append(("IA_SCATTER_TRENDLINE_MISSING", {}))
    
    # ============================================================
    # Step 7: Check Trendline Extension (1 point) → F7
    # ============================================================
    # The trendline should extend from 8 years (left) to 24 years (right)
    # This is done via trendline backward/forward properties in Excel
    #
    # Based on real student data:
    #   - X-data typically ranges from ~10-20 years of education
    #   - Need to extend backward to 8 (about 2 years back)
    #   - Need to extend forward to 24 (about 4 years forward)
    #
    # IMPORTANT: We must check that backward/forward are ACTUALLY set to non-zero values.
    # Default values of None, 0, or 0.0 mean the trendline is NOT extended.
    
    extension_correct = False
    backward_val = None
    forward_val = None
    
    # Check trendline backward/forward extension
    if trendline_obj is not None:
        backward = getattr(trendline_obj, 'backward', None)
        forward = getattr(trendline_obj, 'forward', None)
        
        # Convert to float for comparison, treating None as 0
        try:
            backward_val = float(backward) if backward is not None else 0.0
        except (ValueError, TypeError):
            backward_val = 0.0
        
        try:
            forward_val = float(forward) if forward is not None else 0.0
        except (ValueError, TypeError):
            forward_val = 0.0
        
        # Student needs meaningful extension - at least 1 unit forward to show predictions
        # The assignment specifically asks to extend the trendline to show predicted values
        # Typical requirement: extend forward by at least 2-4 years to reach prediction range (20-24)
        # Being reasonable: forward >= 2 shows intent to extend for predictions
        has_meaningful_forward = forward_val >= 2.0
        
        # Backward extension is nice to have but not strictly required
        # If they have backward, that's a bonus, but forward is what shows predictions
        has_backward = backward_val >= 1.0
        
        # Primary check: must have forward extension to show predictions
        if has_meaningful_forward:
            extension_correct = True
        elif has_backward and forward_val >= 1.0:
            # If they extended both ways but forward is small, still count it
            extension_correct = True
    
    if extension_correct:
        trendline_score += 1.0
        feedback.append(("IA_SCATTER_EXTENDED_CORRECT", {
            "backward": backward_val,
            "forward": forward_val
        }))
    else:
        feedback.append(("IA_SCATTER_EXTENDED_MISSING", {
            "expected_min": 8,
            "expected_max": 24,
            "actual_backward": backward_val,
            "actual_forward": forward_val
        }))
    
    return chart_labels_score, trendline_score, feedback
