# writers/write_annual_budget_results.py

def write_annual_budget_results_to_grading_sheet(wb_grading, results):
    """
    Writes all Annual Budget grader results into the existing student's
    grading sheet workbook (same workbook used for Income & Projection, Credit Cards, and Student Loans).

    EXPECTED RESULTS STRUCTURE (from grade_annual_budget_tab):

        results = {
            "housing_other": {...},   # -> Row 22
            "row26": {...},           # -> Row 23
            "row27": {...},           # -> Row 24
            "row28": {...},           # -> Row 25
            "row30": {...},           # -> Row 26 (combined with row32)
            "row32": {...},           # -> Row 26 (combined with row30)
            "formatting": {...},      # -> Row 28
        }
    """

    ws = wb_grading["Grading Sheet"]

    # -------------------------
    # Extract all results using
    # the actual keys from the wrapper
    # -------------------------
    housing_other = results.get("housing_other", {})
    row26        = results.get("row26", {})
    row27        = results.get("row27", {})
    row28        = results.get("row28", {})
    row30        = results.get("row30", {})
    row32        = results.get("row32", {})
    formatting   = results.get("formatting", {})
    pie_chart    = results.get("pie_chart", {})

    # -------------------------
    # Combine row30 + row32
    # into one line on the grading sheet
    # -------------------------
    combined_30_32_points = row30.get("total_points", 0) + row32.get("total_points", 0)

    combined_comments_list = []
    for section in (row30, row32):
        c = section.get("comment", "")
        if c:
            combined_comments_list.append(c)
    combined_30_32_comment = " | ".join(combined_comments_list)

    # -------------------------
    # WRITE SCORES (Column F)
    # -------------------------
    ws["F22"] = housing_other.get("total_points", 0)  # Housing → Other
    ws["F23"] = row26.get("total_points", 0)          # Subsidized Monthly Loan row
    ws["F24"] = row27.get("total_points", 0)          # Credit Card Monthly Payment row
    ws["F25"] = row28.get("total_points", 0)          # Total Annual Budget (D28)

    ws["F26"] = combined_30_32_points                 # Projected + Remaining Total (D30 & D32)

    ws["F27"] = pie_chart.get("total_points", 0)      # Pie chart (auto-graded)
    ws["F28"] = formatting.get("total_points", 0)     # Formatting for D30 & D32

    # -------------------------
    # WRITE COMMENTS (Column G)
    # -------------------------
    ws["G22"] = housing_other.get("comment", "")
    ws["G23"] = row26.get("comment", "")
    ws["G24"] = row27.get("comment", "")
    ws["G25"] = row28.get("comment", "")
    ws["G26"] = combined_30_32_comment

    ws["G27"] = pie_chart.get("comment", "")    # Pie chart feedback (auto-graded)
    ws["G28"] = formatting.get("comment", "")
