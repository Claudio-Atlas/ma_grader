"""
xl.py — load student workbooks with Excel's "future function" prefixes removed.

Excel stores functions added after 2007 with a hidden prefix in the file, e.g.
STDEV.S(...) is saved as _xlfn.STDEV.S(...), and dynamic-array helpers as
_xlfn._xlws.SORT(...). Graders compare formula text, so the prefix made correct
formulas look wrong (=AVERAGE(D14:D63)-STDEV.S(D14:D63) was rejected).

Only use this for workbooks that are read, never saved: Excel needs the
prefixes in files it opens.
"""

import re

from openpyxl import load_workbook as _openpyxl_load

_PREFIX_RE = re.compile(r"_xl(?:fn|ws|udf|pm)\.", re.I)


def strip_future_prefixes(wb):
    """Remove _xlfn./_xlws./_xludf. prefixes from every formula in `wb`."""
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if isinstance(v, str):
                    if v.startswith("=") and "_xl" in v.lower():
                        cell.value = _PREFIX_RE.sub("", v)
                elif type(v).__name__ == "ArrayFormula":
                    text = getattr(v, "text", None)
                    if isinstance(text, str) and "_xl" in text.lower():
                        v.text = _PREFIX_RE.sub("", text)
    return wb


def load_workbook(*args, **kwargs):
    """openpyxl.load_workbook for STUDENT files: formulas come back without the
    hidden future-function prefixes. Cached values (data_only=True) are untouched."""
    wb = _openpyxl_load(*args, **kwargs)
    if not kwargs.get("data_only"):
        strip_future_prefixes(wb)
    return wb


# ---------------------------------------------------------------------------
# Repairing files openpyxl refuses to open
# ---------------------------------------------------------------------------

import os
import shutil
import tempfile
import zipfile

# openpyxl only accepts font families 0-14 (the OOXML spec range). Text pasted
# into Excel from a web page brings fonts like "-Webkit-Standard" with family
# 18; Excel opens the file fine but openpyxl rejects the whole workbook
# ("could not read stylesheet"), so the student got "Invalid data format".
# Font family is irrelevant to grading, so out-of-range values are dropped.
_BAD_FAMILY_RE = re.compile(rb'<(?:\w+:)?family val="(?:1[5-9]|[2-9]\d|\d{3,})"\s*/>')


def _can_open(path):
    try:
        _openpyxl_load(path, read_only=True).close()
        return True
    except Exception:
        return False


def repair_workbook_file(path):
    """Fix known harmless quirks that stop openpyxl opening a student's .xlsx.

    Works in place on the WORKSPACE copy (never the original download).
    Returns True if the file was changed. Files that already open, or that
    fail for some other reason, are left exactly as they were.
    """
    if _can_open(path):
        return False
    try:
        with zipfile.ZipFile(path) as zin:
            styles = zin.read("xl/styles.xml")
            fixed = _BAD_FAMILY_RE.sub(b"", styles)
            if fixed == styles:
                return False
            fd, tmp = tempfile.mkstemp(suffix=".xlsx", dir=os.path.dirname(path))
            os.close(fd)
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = fixed if item.filename == "xl/styles.xml" else zin.read(item.filename)
                    zout.writestr(item, data)
    except (KeyError, zipfile.BadZipFile, OSError):
        return False
    if _can_open(tmp):
        shutil.move(tmp, path)
        return True
    os.remove(tmp)
    return False
