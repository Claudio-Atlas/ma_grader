# writers/export_chart_to_image.py
# Cross-platform chart export (Windows uses COM, macOS skips)

from __future__ import annotations  # Python 3.9 compatibility for type hints

import os
import sys
import shutil
from pathlib import Path
from typing import Optional

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


def _try_clear_win32com_gen_cache():
    """
    Fixes common pywin32 cache corruption issues.
    Windows only.
    """
    if not IS_WINDOWS:
        return
    try:
        import win32com
        gen_path = os.path.join(os.path.dirname(win32com.__file__), "gen_py")
        if os.path.isdir(gen_path):
            shutil.rmtree(gen_path, ignore_errors=True)
    except Exception:
        pass


def export_chart_to_image(student_path: str, image_output_dir: str = None) -> Optional[str]:
    """
    Export the XY scatter chart from the student's 'Income Analysis' tab.
    Returns the saved image path if exported, else None.
    
    On macOS: Charts cannot be exported without Excel COM. Returns None.
    On Windows: Uses Excel COM automation.
    
    Args:
        student_path: Path to the student's submission workbook
        image_output_dir: Directory to save the exported chart image
        
    Returns:
        str or None: Path to exported image, or None if not exported
    """
    logger = get_logger()

    # macOS / Linux: Skip chart export (not supported without Excel COM)
    if not IS_WINDOWS or not HAS_WIN32:
        logger.debug(f"Chart export skipped (not supported on {sys.platform})")
        return None

    # Windows with pywin32: Use COM automation
    pythoncom.CoInitialize()

    try:
        student_path = os.path.abspath(student_path)
        student_name = Path(student_path).stem.replace("_MA1", "")

        # Default to workspace temp_charts
        if not image_output_dir:
            image_output_dir = ensure_dir("temp_charts")
        else:
            image_output_dir = os.path.abspath(image_output_dir)
            Path(image_output_dir).mkdir(parents=True, exist_ok=True)

        image_path = os.path.join(image_output_dir, f"{student_name}.png")

        excel = None
        wb = None

        try:
            excel = win32.DispatchEx("Excel.Application")

            try:
                excel.Visible = False
            except Exception:
                pass

            try:
                excel.DisplayAlerts = False
            except Exception:
                pass

            wb = excel.Workbooks.Open(student_path)
            ws = wb.Sheets("Income Analysis")

            for obj in ws.ChartObjects():
                chart = obj.Chart
                if chart.ChartType == -4169:  # XY Scatter
                    chart.Export(image_path)
                    logger.info(f"Exported chart -> {student_name}.png")
                    return image_path

            logger.debug(f"No XY Scatter chart found for {student_name}")
            return None

        except Exception as e:
            msg = str(e)
            if ("CLSIDToClassMap" in msg) or ("MinorVersion" in msg):
                _try_clear_win32com_gen_cache()
                try:
                    excel = win32.DispatchEx("Excel.Application")
                    excel.Visible = False
                    excel.DisplayAlerts = False
                    wb = excel.Workbooks.Open(student_path)
                    ws = wb.Sheets("Income Analysis")

                    for obj in ws.ChartObjects():
                        chart = obj.Chart
                        if chart.ChartType == -4169:
                            chart.Export(image_path)
                            logger.info(f"Exported chart -> {student_name}.png")
                            return image_path

                    logger.debug(f"No XY Scatter chart found for {student_name}")
                    return None
                except Exception as e2:
                    logger.error(f"Chart export failed for {student_name}: {e2}")
                    return None

            logger.error(f"Chart export failed for {student_name}: {e}")
            return None

        finally:
            try:
                if wb is not None:
                    wb.Close(SaveChanges=False)
            except Exception:
                pass

            try:
                if excel is not None:
                    excel.Quit()
            except Exception:
                pass

    finally:
        pythoncom.CoUninitialize()
