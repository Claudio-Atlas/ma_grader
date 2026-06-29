# writers/insert_saved_images_into_grading_sheets.py
# Cross-platform image insertion (Windows uses COM, macOS uses openpyxl)

import os
import sys
from pathlib import Path

from utilities.logger import get_logger
from utilities.paths import ensure_dir

# Check if we're on Windows
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    try:
        import pythoncom
        import win32com.client as win32
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False


def _detect_assignment_type(graded_output_dir: str) -> str:
    """Detect assignment type from existing grading files in the folder."""
    if not os.path.isdir(graded_output_dir):
        return "MA1"  # Default if directory doesn't exist
    for fn in os.listdir(graded_output_dir):
        fn_lower = fn.lower()
        if fn_lower.endswith("_grade.xlsx"):
            # Extract assignment type from filename like "Student_Name_MA3_Grade.xlsx"
            for atype in ["MA1", "MA2", "MA3"]:
                if f"_{atype.lower()}_grade.xlsx" in fn_lower:
                    return atype
    return "MA1"  # Default fallback


def insert_images_into_grading_sheets(temp_chart_dir: str = None, graded_output_dir: str = None, assignment_type: str = None):
    """
    Inserts each PNG chart into the corresponding student's grading sheet.
    
    On Windows: Uses Excel COM automation
    On macOS: Uses openpyxl (if images exist)
    
    Args:
        temp_chart_dir: Directory containing exported chart images
        graded_output_dir: Directory containing grading sheets to insert into
        assignment_type: Type of assignment (MA1, MA2, MA3) - auto-detected if not provided
    """
    logger = get_logger()

    if not graded_output_dir:
        raise ValueError("graded_output_dir is required (should be the course folder).")

    # Default to workspace temp_charts
    temp_chart_dir = ensure_dir("temp_charts") if not temp_chart_dir else os.path.abspath(temp_chart_dir)
    graded_output_dir = os.path.abspath(graded_output_dir)
    
    # Auto-detect assignment type if not provided
    if not assignment_type:
        assignment_type = _detect_assignment_type(graded_output_dir)

    if not os.path.isdir(temp_chart_dir):
        logger.info(f"No temp_chart_dir found: {temp_chart_dir} (skipping image insertion)")
        return

    pngs = [f for f in os.listdir(temp_chart_dir) if f.lower().endswith(".png")]
    if not pngs:
        logger.info("No PNG charts found to insert (this is normal on macOS)")
        return

    logger.info(f"Found {len(pngs)} chart images to insert")

    # Use appropriate method based on platform
    if IS_WINDOWS and HAS_WIN32:
        _insert_images_win32(temp_chart_dir, graded_output_dir, pngs, assignment_type)
    else:
        _insert_images_openpyxl(temp_chart_dir, graded_output_dir, pngs, assignment_type)


def _insert_images_openpyxl(temp_chart_dir: str, graded_output_dir: str, pngs: list, assignment_type: str = "MA1"):
    """Insert images using openpyxl (cross-platform)."""
    logger = get_logger()
    
    try:
        from openpyxl import load_workbook
        from openpyxl.drawing.image import Image
    except ImportError:
        logger.warning("openpyxl not available for image insertion")
        return

    inserted_count = 0
    error_count = 0

    for image_file in pngs:
        student_name = Path(image_file).stem
        grading_file = os.path.join(graded_output_dir, f"{student_name}_{assignment_type}_Grade.xlsx")

        if not os.path.exists(grading_file):
            logger.warning(f"No grading sheet for {student_name}")
            continue

        image_path = os.path.join(temp_chart_dir, image_file)
        wb = None

        try:
            wb = load_workbook(grading_file)
            ws = wb["Grading Sheet"]

            img = Image(image_path)
            img.anchor = "J4"
            ws.add_image(img)

            wb.save(grading_file)
            logger.debug(f"Inserted chart for {student_name}")
            inserted_count += 1

        except Exception as e:
            logger.error(f"Failed to insert chart for {student_name}: {e}")
            error_count += 1
        
        finally:
            # Ensure workbook is always closed to prevent file locks and memory leaks
            if wb is not None:
                wb.close()

    logger.info(f"Image insertion complete: {inserted_count} inserted, {error_count} errors")


def _insert_images_win32(temp_chart_dir: str, graded_output_dir: str, pngs: list, assignment_type: str = "MA1"):
    """Insert images using Windows COM automation."""
    logger = get_logger()
    
    pythoncom.CoInitialize()

    inserted_count = 0
    error_count = 0

    try:
        excel = None

        try:
            excel = win32.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False

            for image_file in pngs:
                student_name = Path(image_file).stem
                grading_file = os.path.join(graded_output_dir, f"{student_name}_{assignment_type}_Grade.xlsx")

                if not os.path.exists(grading_file):
                    logger.warning(f"No grading sheet for {student_name}")
                    continue

                image_path = os.path.join(temp_chart_dir, image_file)

                wb = None
                try:
                    wb = excel.Workbooks.Open(grading_file)
                    ws = wb.Sheets("Grading Sheet")

                    anchor = ws.Range("J4")
                    ws.Shapes.AddPicture(
                        Filename=os.path.abspath(image_path),
                        LinkToFile=False,
                        SaveWithDocument=True,
                        Left=anchor.Left,
                        Top=anchor.Top,
                        Width=-1,
                        Height=-1
                    )

                    wb.Save()
                    wb.Close()
                    wb = None
                    logger.debug(f"Inserted chart for {student_name}")
                    inserted_count += 1

                except Exception as e:
                    logger.error(f"Failed to insert chart for {student_name}: {e}")
                    error_count += 1
                    try:
                        if wb is not None:
                            wb.Close(SaveChanges=False)
                    except Exception:
                        pass

        finally:
            try:
                if excel is not None:
                    excel.Quit()
            except Exception:
                pass

    finally:
        pythoncom.CoUninitialize()
    
    logger.info(f"Image insertion complete: {inserted_count} inserted, {error_count} errors")
