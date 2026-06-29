# graders/credit_cards/grade_credit_cards_tab.py

from openpyxl import load_workbook

# ---- Imports for each credit card sub-grader ----
from graders.ma2_credit_cards.extract_credit_card_values import extract_credit_card_values
from graders.ma2_credit_cards.grade_credit_card_parameters import grade_credit_card_parameters
from graders.ma2_credit_cards.grade_credit_card_amortization import grade_credit_card_amortization
from graders.ma2_credit_cards.compute_credit_card_payoff import compute_credit_card_payoff_months
from graders.ma2_credit_cards.grade_credit_card_summary import grade_credit_card_summary
from graders.ma2_credit_cards.grade_credit_card_formatting import grade_credit_card_formatting


def grade_credit_cards_tab(student_file_path):
    """
    Master wrapper that grades the entire Credit Cards tab.
    
    Returns dictionary:

    {
        "extracted_values": {...},
        "parameters": {...},
        "amortization": {...},
        "summary": {...},
        "formatting": {...}
    }
    """

    try:
        # -------------------------
        # Load sheets for extraction
        # -------------------------
        wb_v = load_workbook(student_file_path, data_only=True)
        ws_rand = wb_v["Random"]
        ws_cc_v = wb_v["Credit Cards"]

        # ==========================================================
        # 1) Extract randomized true values from Random sheet
        # ==========================================================
        extracted_values = extract_credit_card_values(student_file_path)

        # ==========================================================
        # 2) Grade the green-box parameters (C13/C14/C15/C17/C18)
        # ==========================================================
        parameters = grade_credit_card_parameters(student_file_path)

        # ==========================================================
        # 3) Grade amortization table:
        #    - formula structure
        #    - payoff row checks
        # ==========================================================
        amortization = grade_credit_card_amortization(student_file_path)

        payoff_month = amortization["payoff_row"]["payoff_month"]
        excel_row = amortization["payoff_row"]["excel_row"]

        # ==========================================================
        # 4) Now that we know payoff_month → grade the summary boxes
        # ==========================================================
        summary = grade_credit_card_summary(student_file_path, payoff_month, excel_row)

        # ==========================================================
        # 5) Check formatting
        # ==========================================================
        formatting = grade_credit_card_formatting(student_file_path)

        wb_v.close()

        # ==========================================================
        # BUILD RETURN OBJECT
        # ==========================================================
        return {
            "extracted_values": extracted_values,
            "parameters": parameters,
            "amortization": amortization,
            "summary": summary,
            "formatting": formatting
        }

    except Exception as e:
        return {"error": f"Error grading Credit Cards tab: {e}"}
