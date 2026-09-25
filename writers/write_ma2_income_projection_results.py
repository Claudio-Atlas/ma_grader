def write_income_projection_results(ws_grading, results):
    """
    Writes Income and Projection grading results into the Grading Sheet.
    Expects results from grade_income_projection_tab(ws).

    Cell layout (Income and Projection section):
    Row 3  → Name (1 pt)
    Row 4  → CPI Table (6 pts)
    Row 5  → Slope + Intercept (4 pts)
    Row 6  → CPI Projection Section (6 pts)
    Row 7  → Income Projection Section (6 pts)
    Row 8  → Formatting Section (3 pts)
    """

    try:
        # --- Row 3: Name check ---
        ws_grading["F3"] = results["name_check"]["points"]
        ws_grading["G3"] = results["name_check"]["comment"]

        # --- Row 4: CPI table values ---
        ws_grading["F4"] = results["cpi_values"]["points"]
        ws_grading["G4"] = results["cpi_values"]["comment"]

        # --- Row 5: Slope + Intercept combined ---
        slope_pts = results["slope_formula"]["points"]
        intercept_pts = results["intercept_formula"]["points"]
        total_slope_intercept = slope_pts + intercept_pts
        combined_comment = (
            f"Slope: {results['slope_formula']['comment']} | "
            f"Intercept: {results['intercept_formula']['comment']}"
        )

        ws_grading["F5"] = total_slope_intercept
        ws_grading["G5"] = combined_comment

        # --- Row 6: CPI Projection section ---
        ws_grading["F6"] = results["cpi_projection_section"]["points"]
        ws_grading["G6"] = results["cpi_projection_section"]["comment"]

        # --- Row 7: Income Projection section ---
        ws_grading["F7"] = results["income_projection_section"]["points"]
        ws_grading["G7"] = results["income_projection_section"]["comment"]

        # --- Row 8: Formatting section ---
        ws_grading["F8"] = results["formatting_section"]["points"]
        ws_grading["G8"] = results["formatting_section"]["comment"]

        # --- Section total: keep it a LIVE formula so it updates if an
        # instructor edits any of the section scores (F3:F8) by hand. Writing a
        # hard-coded number here (the old behavior) silently broke the total. ---
        ws_grading["F9"] = "=SUM(F3:F8)"

        #print("✅ Income and Projection results written successfully.")

    except Exception as e:
        print(f"❌ Error writing Income and Projection results: {e}")
