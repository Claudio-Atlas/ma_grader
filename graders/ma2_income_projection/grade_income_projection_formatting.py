def grade_income_projection_formatting(ws):
    """
    Checks formatting for key cells on the Income and Projection tab.
    Each correct format earns 0.5 points. Total = 3 points.
    H19, H20: Number (3 decimals)
    K33: Number (3 decimals)
    K34: Percentage (2 decimals)
    K35, K36, K37: Currency ($, 2 decimals)
    """

    result = {"points": 0, "comment": ""}
    details = []
    total_points = 0.0

    try:
        checks = [
            ("H19", "number", 3, 0.5),
            ("H20", "number", 3, 0.5),
            ("K33", "number", 3, 0.5),
            ("K34", "percent", 2, 0.5),
            ("K35", "currency", 2, 0.5),
            ("K36", "currency", 2, 0.25),
            ("K37", "currency", 2, 0.25),
        ]

        for cell_ref, fmt_type, decimals, weight in checks:
            cell = ws[cell_ref]
            fmt = str(cell.number_format).lower()

            # --- Identify format type ---
            if fmt_type == "number":
                if "0.000" in fmt or fmt.startswith("0.000"):
                    total_points += weight
                    details.append(f"{cell_ref}: ✅ Number format with 3 decimals.")
                else:
                    details.append(f"{cell_ref}: ❌ Expected number format with 3 decimals (found '{fmt}').")

            elif fmt_type == "percent":
                if "%" in fmt and ("0.00" in fmt or "0.0%" in fmt):
                    total_points += weight
                    details.append(f"{cell_ref}: ✅ Percentage format with 2 decimals.")
                else:
                    details.append(f"{cell_ref}: ❌ Expected percentage format with 2 decimals (found '{fmt}').")

            elif fmt_type == "currency":
                if "$" in fmt or "[$" in fmt or "₤" in fmt or "€" in fmt:
                    if "0.00" in fmt:
                        total_points += weight
                        details.append(f"{cell_ref}: ✅ Currency format with 2 decimals.")
                    else:
                        details.append(f"{cell_ref}: ❌ Currency missing 2 decimals (found '{fmt}').")
                else:
                    details.append(f"{cell_ref}: ❌ Expected currency format (found '{fmt}').")

        result["points"] = round(total_points, 2)
        result["comment"] = f"Formatting check complete: {result['points']}/3 points."
        result["details"] = details

    except Exception as e:
        result["comment"] = f"Error checking formatting: {e}"

    return result
