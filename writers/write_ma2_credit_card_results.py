# writers/credit_card_writer.py

def write_credit_card_results_to_grading_sheet(
    wb_grading,
    results: dict
):
    """
    Writes Credit Cards tab grading results into the *existing*
    student's grading sheet workbook object.

    This function does NOT save the workbook — main.py saves it.
    """

    # Access the grading sheet inside the already-open workbook
    ws = wb_grading["Grading Sheet"]

    # Pull sections safely
    params     = results.get("parameters", {})
    amort      = results.get("amortization", {})
    summary    = results.get("summary", {})
    formatting = results.get("formatting", {})

    # Extract points
    params_score     = params.get("total_points", 0)
    amort_score      = amort.get("total_points", 0)
    summary_score    = summary.get("total_points", 0)
    formatting_score = formatting.get("total_points", 0)

    # Extract comments
    params_comment     = params.get("comment", "")
    amort_comment      = amort.get("comment", "")
    summary_comment    = summary.get("comment", "")
    formatting_comment = formatting.get("comment", "")

    # ---------------------------------------------
    # WRITE SCORES + COMMENTS
    # ---------------------------------------------
    ws["F17"] = params_score
    ws["G17"] = params_comment

    ws["F18"] = amort_score
    ws["G18"] = amort_comment

    ws["F19"] = summary_score
    ws["G19"] = summary_comment

    ws["F20"] = formatting_score
    ws["G20"] = formatting_comment

    # We DO NOT save here — main.py handles saving
    return True
