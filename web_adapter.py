"""
web_adapter.py — Thin wrapper around the MA Grader pipeline for web use.

Accepts a ZIP upload, runs the grading pipeline in a temp workspace,
and returns structured results.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Engine root. When frozen by PyInstaller, bundled code + data live under
# sys._MEIPASS (not next to __file__), so use that as the root.
_FROZEN = getattr(sys, "frozen", False)
if _FROZEN:
    _MA_GRADER_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    _MA_GRADER_DIR = str(Path(__file__).resolve().parent)


def _setup_ma_imports():
    """Temporarily hijack sys.path and clear cached modules so the MA engine's
    absolute imports (from graders.X, from utilities.X, etc.) resolve to
    ma_grader/ subdirectories instead of the app-root graders/ package."""
    import importlib

    # In a frozen build there is no conflicting app-root package to disambiguate
    # from, and the modules are baked into the bundle — so the path/cache
    # juggling below is unnecessary and could wrongly evict bundled modules.
    if _FROZEN:
        if _MA_GRADER_DIR not in sys.path:
            sys.path.insert(0, _MA_GRADER_DIR)
        return

    # Force ma_grader/ to front of path
    if _MA_GRADER_DIR in sys.path:
        sys.path.remove(_MA_GRADER_DIR)
    sys.path.insert(0, _MA_GRADER_DIR)

    # Clear any cached root-level modules that conflict
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith(("graders.", "orchestrator.", "writers.", "utilities.")):
            # Only remove if it's NOT from ma_grader
            mod = sys.modules[mod_name]
            if hasattr(mod, "__file__") and mod.__file__ and "ma_grader" not in mod.__file__:
                del sys.modules[mod_name]
    # Also clear the top-level package refs if they point outside ma_grader
    for pkg in ("graders", "orchestrator", "writers", "utilities"):
        if pkg in sys.modules:
            mod = sys.modules[pkg]
            if hasattr(mod, "__file__") and mod.__file__ and "ma_grader" not in str(mod.__file__):
                del sys.modules[pkg]
            elif hasattr(mod, "__path__"):
                paths = list(mod.__path__)
                if paths and "ma_grader" not in paths[0]:
                    del sys.modules[pkg]

# Assets shipped alongside the engine
_ASSETS_TEMPLATES = os.path.join(_MA_GRADER_DIR, "assets_templates")
_ASSETS_FEEDBACK = os.path.join(_MA_GRADER_DIR, "assets_feedback")


def _seed_workspace(workspace: str) -> None:
    """Copy template xlsx + feedback json into the temp workspace."""
    tpl_dir = os.path.join(workspace, "templates")
    fb_dir = os.path.join(workspace, "feedback")
    os.makedirs(tpl_dir, exist_ok=True)
    os.makedirs(fb_dir, exist_ok=True)

    for fname in os.listdir(_ASSETS_TEMPLATES):
        src = os.path.join(_ASSETS_TEMPLATES, fname)
        dst = os.path.join(tpl_dir, fname)
        if not os.path.exists(dst) and os.path.isfile(src):
            shutil.copy2(src, dst)

    for fname in os.listdir(_ASSETS_FEEDBACK):
        src = os.path.join(_ASSETS_FEEDBACK, fname)
        dst = os.path.join(fb_dir, fname)
        if not os.path.exists(dst) and os.path.isfile(src):
            shutil.copy2(src, dst)


def grade_zip(
    zip_path: str,
    course_label: str,
    assignment_type: str = "MA1",
    workspace: Optional[str] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Run the full MA grading pipeline on a ZIP of student submissions.

    Args:
        zip_path: Path to the uploaded ZIP file on disk.
        course_label: e.g. "MAT-144-501"
        assignment_type: "MA1", "MA2", or "MA3"
        workspace: Optional temp directory to use (created if None).

    Returns:
        Dict with keys:
            students  — list of {name, status, error?}
            master_workbook — path to INSTRUCTOR_MASTER.xlsx (or None)
            graded_path — path to graded_output folder
            success_count — int
            issue_count — int
            logs — list[str]
    """
    cleanup = False
    if workspace is None:
        workspace = tempfile.mkdtemp(prefix="ma_grader_")
        cleanup = False  # caller can clean up via the returned path

    # Fix import resolution before loading any engine modules
    _setup_ma_imports()

    # Point the engine's path system at our temp workspace
    from utilities.paths import set_custom_workspace
    set_custom_workspace(workspace)

    # Seed assets
    _seed_workspace(workspace)

    logs: list[str] = []

    # Import pipeline pieces (after sys.path is set)
    from writers.generate_course_folders import generate_course_folders
    from writers.import_zip_to_student_groups import import_zip_to_student_groups
    from writers.create_grading_sheet import create_grading_sheets_from_folder
    from orchestrator import phase1_grade_all_students, phase1_grade_all_students_ma2, phase1_grade_all_students_ma3
    from writers.build_instructor_master_workbook import build_instructor_master_workbook
    from utilities.errors import GradingResult

    # Minimal pipeline_state dict for the grader's cancellation / result hooks
    pipeline_state: Dict[str, Any] = {
        "cancel_requested": False,
        "grading_result": None,
        # Optional callable(current:int, total:int, student:str) invoked once per
        # student during grading. Used by the desktop app to stream live progress.
        "progress_callback": progress_callback,
    }

    try:
        folder_safe, graded_path, submissions_path = generate_course_folders(
            course_label, assignment_type
        )
        logs.append(f"Created folders for {course_label}")

        import_zip_to_student_groups(zip_path, folder_safe, assignment_type)
        logs.append("Imported ZIP into student groups")

        create_grading_sheets_from_folder(folder_safe, assignment_type=assignment_type)
        logs.append("Created grading sheets")

        assignment_upper = assignment_type.upper() if assignment_type else "MA1"
        if assignment_upper == "MA3":
            phase1_grade_all_students_ma3(submissions_path, graded_path, pipeline_state)
        elif assignment_upper == "MA2":
            phase1_grade_all_students_ma2(submissions_path, graded_path, pipeline_state)
        else:
            phase1_grade_all_students(submissions_path, graded_path, pipeline_state)
        logs.append("Grading complete")

        master_path = None
        try:
            master_path = build_instructor_master_workbook(
                graded_path, assignment_type=assignment_type
            )
            logs.append(f"Built master workbook: {os.path.basename(master_path)}")
        except FileNotFoundError:
            logs.append("No grade files found — master workbook skipped")

        # Build student list from graded files, including paths the Review
        # screen needs (the graded sheet, the student's workbook, any paper).
        students = []
        suffix = f"_{assignment_upper}_Grade.xlsx"
        papers_dir = os.path.join(workspace, "student_papers", folder_safe, assignment_upper)
        if os.path.isdir(graded_path):
            for fn in sorted(os.listdir(graded_path)):
                if fn.endswith(suffix):
                    name = fn[: -len(suffix)]
                    entry = {
                        "name": name,
                        "status": "graded",
                        "grade_file": os.path.join(graded_path, fn),
                        "workbook_file": os.path.join(
                            submissions_path, f"{name}_{assignment_upper}.xlsx"
                        ),
                    }
                    if assignment_upper == "MA2" and os.path.isdir(papers_dir):
                        for ext in (".docx", ".pdf"):
                            p = os.path.join(papers_dir, f"{name}_{assignment_upper}{ext}")
                            if os.path.exists(p):
                                entry["paper_file"] = p
                                break
                    students.append(entry)

        grading_result = pipeline_state.get("grading_result")
        success_count = grading_result.success_count if isinstance(grading_result, GradingResult) else len(students)
        issue_count = len(grading_result.issues) if isinstance(grading_result, GradingResult) else 0

        # Gather issue details
        issues = []
        if isinstance(grading_result, GradingResult):
            for issue in grading_result.issues:
                issues.append({
                    "student": issue.student_name or "Unknown",
                    "problem": issue.problem,
                    "action": issue.action,
                })

        return {
            "students": students,
            "issues": issues,
            "master_workbook": master_path,
            "graded_path": graded_path,
            "workspace": workspace,
            "success_count": success_count,
            "issue_count": issue_count,
            "logs": logs,
        }

    except Exception as exc:
        logs.append(f"Pipeline error: {exc}")
        return {
            "students": [],
            "issues": [],
            "master_workbook": None,
            "graded_path": None,
            "workspace": workspace,
            "success_count": 0,
            "issue_count": 1,
            "logs": logs,
            "error": str(exc),
        }


def _grade_template_name(assignment_upper: str) -> str:
    """Filename of the grading-sheet template for an assignment."""
    if assignment_upper == "MA3":
        return "MA3_Grading_Sheet_Template.xlsx"
    if assignment_upper == "MA2":
        return "MA2_Grading_Sheet_Template.xlsx"
    return "Grading_Sheet_Template.xlsx"


def grade_one(
    workbook_path: str,
    course_label: str,
    student_name: str,
    assignment_type: str = "MA1",
    workspace: Optional[str] = None,
    paper_path: Optional[str] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Grade a SINGLE student's workbook and merge the result into the existing
    course folder (used for late or re-submitted work).

    Unlike grade_zip, this takes the student's .xlsx directly (no ZIP) and a
    typed student name. The graded sheet is written into the same
    graded_output/<course> folder as a prior batch, and the instructor master
    workbook is rebuilt so the student appears alongside everyone else.

    Args:
        workbook_path: Path to the student's .xlsx submission.
        course_label: e.g. "MAT 144 Online" (must match the batch to merge in).
        student_name: "First Last" — used to name the output and (MA1) initials.
        assignment_type: "MA1" | "MA2" | "MA3".
        workspace: Persistent workspace folder (defaults to a temp dir).
        paper_path: Optional MA2 write-up document (.docx/.pdf). Copied alongside
            the submission for later manual grading; not auto-graded here.
        progress_callback: Optional callable(current, total, student).

    Returns: same shape as grade_zip, plus "student" (the one graded) and
        "paper_file" (stored copy of the paper, or None).
    """
    if workspace is None:
        workspace = tempfile.mkdtemp(prefix="ma_grader_")

    _setup_ma_imports()

    from utilities.paths import set_custom_workspace, ensure_dir
    set_custom_workspace(workspace)
    _seed_workspace(workspace)

    logs: list[str] = []

    from writers.generate_course_folders import generate_course_folders
    from utilities.paths import ws_path
    from orchestrator import (
        phase1_grade_all_students,
        phase1_grade_all_students_ma2,
        phase1_grade_all_students_ma3,
    )
    from writers.build_instructor_master_workbook import build_instructor_master_workbook
    from utilities.errors import GradingResult

    assignment_upper = assignment_type.upper() if assignment_type else "MA1"

    # Normalize the typed name into the same First_Last convention the batch uses.
    readable_name = "_".join(part for part in str(student_name).split() if part) or "Unknown"
    submission_filename = f"{readable_name}_{assignment_upper}.xlsx"
    grading_filename = f"{readable_name}_{assignment_upper}_Grade.xlsx"

    pipeline_state: Dict[str, Any] = {
        "cancel_requested": False,
        "grading_result": None,
        "progress_callback": progress_callback,
        # Restrict grading to just this one file inside the shared folder.
        "only_filename": submission_filename,
    }

    try:
        if not os.path.exists(workbook_path):
            raise FileNotFoundError(f"Submission file not found: {workbook_path}")

        folder_safe, graded_path, submissions_path = generate_course_folders(
            course_label, assignment_upper
        )
        logs.append(f"Using course folder for {course_label}")

        # Copy the student's workbook into the shared submissions folder.
        submission_dest = os.path.join(submissions_path, submission_filename)
        shutil.copyfile(workbook_path, submission_dest)

        # Copy a fresh grading sheet for this student (overwrites on re-grade).
        template_path = ws_path("templates", _grade_template_name(assignment_upper))
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Grading template not found: {template_path}")
        grading_dest = os.path.join(graded_path, grading_filename)
        shutil.copyfile(template_path, grading_dest)
        logs.append(f"Prepared grading sheet for {readable_name}")

        # Optionally stash the MA2 write-up paper next to the submission.
        paper_file = None
        if paper_path and os.path.exists(paper_path):
            papers_dir = ensure_dir("student_papers", folder_safe, assignment_upper)
            ext = os.path.splitext(paper_path)[1] or ".docx"
            paper_file = os.path.join(papers_dir, f"{readable_name}_{assignment_upper}{ext}")
            shutil.copyfile(paper_path, paper_file)
            logs.append("Stored write-up paper for manual grading")

        # Grade just this one file using the same per-assignment grader.
        if assignment_upper == "MA3":
            phase1_grade_all_students_ma3(submissions_path, graded_path, pipeline_state)
        elif assignment_upper == "MA2":
            phase1_grade_all_students_ma2(submissions_path, graded_path, pipeline_state)
        else:
            phase1_grade_all_students(submissions_path, graded_path, pipeline_state)
        logs.append("Grading complete")

        # Rebuild master so the (possibly new) student is included with the batch.
        master_path = None
        try:
            master_path = build_instructor_master_workbook(
                graded_path, assignment_type=assignment_type
            )
            logs.append(f"Rebuilt master workbook: {os.path.basename(master_path)}")
        except FileNotFoundError:
            logs.append("No grade files found — master workbook skipped")

        grading_result = pipeline_state.get("grading_result")
        success_count = grading_result.success_count if isinstance(grading_result, GradingResult) else 1
        issues = []
        if isinstance(grading_result, GradingResult):
            for issue in grading_result.issues:
                issues.append({
                    "student": issue.student_name or readable_name,
                    "problem": issue.problem,
                    "action": issue.action,
                })

        return {
            "student": readable_name,
            "students": [{
                "name": readable_name,
                "status": "graded",
                "grade_file": grading_dest,
                "workbook_file": submission_dest,
                **({"paper_file": paper_file} if paper_file else {}),
            }] if success_count else [],
            "issues": issues,
            "master_workbook": master_path,
            "graded_path": graded_path,
            "grade_file": grading_dest,
            "paper_file": paper_file,
            "workspace": workspace,
            "success_count": success_count,
            "issue_count": len(issues),
            "logs": logs,
        }

    except Exception as exc:
        logs.append(f"Single-grade error: {exc}")
        return {
            "student": readable_name,
            "students": [],
            "issues": [],
            "master_workbook": None,
            "graded_path": None,
            "grade_file": None,
            "paper_file": None,
            "workspace": workspace,
            "success_count": 0,
            "issue_count": 1,
            "logs": logs,
            "error": str(exc),
        }


# ===========================================================================
# Review-mode helpers: inspect a student workbook, inspect a grade sheet, and
# write edited scores/comments back. Used by the desktop app's Review screen.
# ===========================================================================

def inspect_workbook(workbook_path: str,
                     max_rows: int = 200,
                     max_cols: int = 40) -> Dict[str, Any]:
    """
    Read a student workbook into a JSON-friendly grid: per sheet, the non-empty
    cells with their cached value and (if any) the formula the student entered.

    Formulas come from a normal load; values come from a data_only load (Excel's
    last-saved cached results). We do not recompute formulas.
    """
    _setup_ma_imports()
    from openpyxl import load_workbook

    if not os.path.exists(workbook_path):
        return {"error": f"Workbook not found: {workbook_path}", "sheets": []}

    wb_f = load_workbook(workbook_path, data_only=False)
    try:
        wb_v = load_workbook(workbook_path, data_only=True)
    except Exception:
        wb_v = None

    sheets = []
    for name in wb_f.sheetnames:
        ws_f = wb_f[name]
        ws_v = wb_v[name] if (wb_v and name in wb_v.sheetnames) else None
        nrows = min(ws_f.max_row or 0, max_rows)
        ncols = min(ws_f.max_column or 0, max_cols)
        # Pull values into a lookup first (read_only sheets stream once).
        value_map = {}
        if ws_v is not None:
            for row in ws_v.iter_rows(min_row=1, max_row=nrows, max_col=ncols):
                for c in row:
                    if c.value is not None:
                        value_map[(c.row, c.column)] = c.value
        cells = []
        for row in ws_f.iter_rows(min_row=1, max_row=nrows, max_col=ncols):
            for c in row:
                fv = c.value
                vv = value_map.get((c.row, c.column))
                if fv is None and vv is None:
                    continue
                formula = fv if (isinstance(fv, str) and fv.startswith("=")) else None
                value = vv if vv is not None else (None if formula else fv)
                cells.append({
                    "ref": c.coordinate,
                    "r": c.row,
                    "c": c.column,
                    "v": value,
                    "f": formula,
                })
        sheets.append({"name": name, "rows": nrows, "cols": ncols, "cells": cells})

    wb_f.close()
    if wb_v is not None:
        wb_v.close()
    return {"sheets": sheets}


def inspect_grade(grade_path: str, assignment_type: str = "MA2") -> Dict[str, Any]:
    """
    Read the editable rubric rows out of a grading sheet: label, possible
    points, currently-awarded points, comment, and the cells to write back to.
    Rows whose 'possible points' is a formula (subtotals/totals) are skipped.
    """
    _setup_ma_imports()
    from openpyxl import load_workbook

    if not os.path.exists(grade_path):
        return {"error": f"Grade sheet not found: {grade_path}", "rows": []}

    wb = load_workbook(grade_path)
    ws = wb["Grading Sheet"] if "Grading Sheet" in wb.sheetnames else wb.active

    rows = []
    total_possible = 0.0
    total_awarded = 0.0
    for r in range(1, (ws.max_row or 0) + 1):
        possible = ws.cell(r, 5).value  # col E
        if not isinstance(possible, (int, float)):
            continue
        section = ws.cell(r, 1).value
        comp = ws.cell(r, 2).value
        req = ws.cell(r, 3).value
        awarded = ws.cell(r, 6).value   # col F
        comment = ws.cell(r, 7).value   # col G
        aw = awarded if isinstance(awarded, (int, float)) else None
        rows.append({
            "row": r,
            "label": (comp if isinstance(comp, str) else None) or
                     (req if isinstance(req, str) else None) or
                     (section if isinstance(section, str) else None) or f"Row {r}",
            "requirement": req if isinstance(req, str) else None,
            "section": section if isinstance(section, str) else None,
            "possible": possible,
            "awarded": aw,
            "comment": comment if isinstance(comment, str) else "",
            "awarded_cell": f"F{r}",
            "comment_cell": f"G{r}",
        })
        total_possible += possible
        if aw is not None:
            total_awarded += aw

    wb.close()
    return {
        "rows": rows,
        "total_possible": round(total_possible, 2),
        "total_awarded": round(total_awarded, 2),
    }


def update_grade(grade_path: str, edits) -> Dict[str, Any]:
    """
    Write edited scores/comments back into the grade sheet, preserving its
    formulas and formatting. `edits` is a list of {"cell": "F3", "value": ...}.
    """
    _setup_ma_imports()
    from openpyxl import load_workbook

    if not os.path.exists(grade_path):
        return {"ok": False, "error": f"Grade sheet not found: {grade_path}"}

    wb = load_workbook(grade_path)
    ws = wb["Grading Sheet"] if "Grading Sheet" in wb.sheetnames else wb.active
    for e in (edits or []):
        cell = e.get("cell")
        if not cell:
            continue
        ws[cell] = e.get("value")
    wb.save(grade_path)
    wb.close()

    info = inspect_grade(grade_path)
    return {
        "ok": True,
        "total_awarded": info.get("total_awarded"),
        "total_possible": info.get("total_possible"),
    }


# ===========================================================================
# MA2 write-up (paper) grading: read the paper section, extract document text,
# and optionally have Claude propose level/comment for each rubric criterion.
# ===========================================================================

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_AI_MODEL = "claude-sonnet-4-6"


def inspect_paper(grade_path: str) -> Dict[str, Any]:
    """
    Read the 'Written Paper' section out of an MA2 grade sheet and pair each row
    with the canonical rubric (level options + exact points). Returns the
    criteria with their current awarded points / comment and the cells to write.
    """
    _setup_ma_imports()
    from openpyxl import load_workbook
    from graders.ma2_paper import rubric as R

    if not os.path.exists(grade_path):
        return {"error": f"Grade sheet not found: {grade_path}", "criteria": []}

    wb = load_workbook(grade_path)
    ws = wb["Grading Sheet"] if "Grading Sheet" in wb.sheetnames else wb.active

    # Find the "Written Paper" header row in column A.
    header_row = None
    for r in range(1, (ws.max_row or 0) + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and v.strip().lower() == "written paper":
            header_row = r
            break

    if header_row is None:
        wb.close()
        return {
            "error": "This grade sheet has no Written Paper section. Re-grade the "
                     "student with the updated MA2 template.",
            "criteria": [],
        }

    criteria = []
    subtotal_awarded = 0.0
    start = header_row + 1
    for i, crit in enumerate(R.CRITERIA):
        r = start + i
        possible = ws.cell(r, 5).value
        awarded = ws.cell(r, 6).value
        comment = ws.cell(r, 7).value
        aw = awarded if isinstance(awarded, (int, float)) else None
        if aw is not None:
            subtotal_awarded += aw
        criteria.append({
            "key": crit["key"],
            "name": crit["name"],
            "row": r,
            "possible": possible if isinstance(possible, (int, float)) else crit["points"][4],
            "awarded": aw,
            "comment": comment if isinstance(comment, str) else "",
            "awarded_cell": f"F{r}",
            "comment_cell": f"G{r}",
            "levels": R.criterion_levels(crit),
            "selected_level": R.level_for_points(crit, aw),
        })

    wb.close()
    return {
        "criteria": criteria,
        "subtotal_awarded": round(subtotal_awarded, 2),
        "total_possible": R.TOTAL_POSSIBLE,
    }


def extract_paper_text(paper_path: str, max_chars: int = 40000) -> Dict[str, Any]:
    """Extract readable text from a .docx or .pdf write-up for viewing/AI."""
    if not paper_path or not os.path.exists(paper_path):
        return {"ok": False, "error": "Paper file not found.", "text": ""}

    ext = os.path.splitext(paper_path)[1].lower()
    try:
        if ext == ".docx":
            import docx  # python-docx
            doc = docx.Document(paper_path)
            parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
            text = "\n".join(parts)
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(paper_path)
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        else:
            return {"ok": False, "error": f"Unsupported document type: {ext}", "text": ""}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Could not read document: {exc}", "text": ""}

    text = (text or "").strip()
    truncated = len(text) > max_chars
    return {"ok": True, "text": text[:max_chars], "truncated": truncated, "chars": len(text)}


_STRICTNESS_GUIDANCE = {
    "lenient": "Grade generously. Give the student the benefit of the doubt; when a "
               "response sits between two levels, choose the HIGHER one.",
    "standard": "Apply the rubric neutrally, exactly as written.",
    "elite": "Grade strictly to a high bar. Reserve the top level (Target) for "
             "excellent, complete, well-supported responses; when a response sits "
             "between two levels, choose the LOWER one.",
}


def _build_paper_prompt(paper_text: str, strictness: str = "standard") -> str:
    from graders.ma2_paper import rubric as R
    guidance = _STRICTNESS_GUIDANCE.get((strictness or "standard").lower(),
                                        _STRICTNESS_GUIDANCE["standard"])
    lines = [
        "You are grading a student's MAT-144 financial-literacy write-up against a "
        "fixed rubric. For EACH criterion, choose the single best level (1-5) and "
        "write one concise sentence of justification addressed to the student.",
        "",
        f"Grading stance: {guidance}",
        "",
        "Levels: 5=Target, 4=Acceptable, 3=Approaching, 2=Insufficient, 1=Unsatisfactory.",
        "",
        "Criteria and what each level means:",
    ]
    for c in R.CRITERIA:
        lines.append(f'- {c["name"]} (key: {c["key"]}, max {c["points"][4]} pts):')
        for idx in range(4, -1, -1):
            lines.append(f'    {idx+1} ({R.LEVEL_NAMES[idx]}): {c["descriptions"][idx]}')
    lines += [
        "",
        "Return ONLY a JSON array, no prose, with one object per criterion:",
        '[{"key":"project_heading","level":4,"comment":"..."}, ...]',
        "Include all eight criteria, using the exact keys shown above.",
        "",
        "=== STUDENT WRITE-UP ===",
        paper_text or "(empty)",
    ]
    return "\n".join(lines)


def _anthropic_post(api_key, payload, timeout=60):
    import requests
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    return requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=timeout)


def ai_test_key(api_key: str, model: str = DEFAULT_AI_MODEL) -> Dict[str, Any]:
    """Validate an Anthropic key with a tiny request."""
    if not api_key:
        return {"ok": False, "error": "No API key provided."}
    try:
        resp = _anthropic_post(api_key, {
            "model": model,
            "max_tokens": 4,
            "messages": [{"role": "user", "content": "ping"}],
        }, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Could not reach Anthropic: {exc}"}
    if resp.status_code == 200:
        return {"ok": True}
    return {"ok": False, "error": f"Key rejected ({resp.status_code}): {resp.text[:200]}"}


def ai_grade_paper(paper_path: str, api_key: str,
                   model: str = DEFAULT_AI_MODEL,
                   strictness: str = "standard",
                   grade_file: str = None) -> Dict[str, Any]:
    """
    Extract the paper text and ask Claude to propose a level + comment for each
    of the 8 criteria. `strictness` is one of lenient | standard | elite and only
    nudges how demanding Claude is; it never changes the rubric's point values.

    If `grade_file` is provided, the suggestions are also WRITTEN into that grade
    sheet's Written Paper section (used by the batch flow). Without it, suggestions
    are returned only, for the human to confirm before saving (the single panel).
    """
    _setup_ma_imports()
    from graders.ma2_paper import rubric as R

    if not api_key:
        return {"error": "No API key set. Add your Anthropic key in Settings."}

    extracted = extract_paper_text(paper_path)
    if not extracted.get("ok"):
        return {"error": extracted.get("error", "Could not read the paper.")}

    prompt = _build_paper_prompt(extracted["text"], strictness)
    try:
        resp = _anthropic_post(api_key, {
            "model": model,
            "max_tokens": 1800,
            "messages": [{"role": "user", "content": prompt}],
        })
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Could not reach Anthropic: {exc}"}

    if resp.status_code != 200:
        return {"error": f"Anthropic API error ({resp.status_code}): {resp.text[:200]}"}

    try:
        text = resp.json()["content"][0]["text"]
        s, e = text.find("["), text.rfind("]")
        parsed = json.loads(text[s:e + 1]) if s >= 0 and e > s else []
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Could not parse AI response: {exc}"}

    # Tolerant matching: Claude may return the exact key, or the criterion's
    # name, or a lightly different spelling. Match on a normalized form of any.
    def _norm(s):
        return "".join(ch for ch in str(s).lower() if ch.isalnum())

    by_key = {c["key"]: c for c in R.CRITERIA}
    by_norm = {}
    for c in R.CRITERIA:
        by_norm[_norm(c["key"])] = c
        by_norm[_norm(c["name"])] = c

    suggestions = []
    used = set()
    for item in parsed:
        raw = item.get("key") or item.get("criterion") or item.get("name") or ""
        crit = (
            by_key.get(raw)
            or by_norm.get(_norm(raw))
            or by_norm.get(_norm(item.get("name", "")))
        )
        if not crit or crit["key"] in used:
            continue
        try:
            level = int(item.get("level"))
        except Exception:  # noqa: BLE001
            level = None
        if not level or level < 1 or level > 5:
            continue
        used.add(crit["key"])
        suggestions.append({
            "key": crit["key"],
            "name": crit["name"],
            "level": level,
            "points": R.points_for_level(crit["key"], level),
            "comment": str(item.get("comment", "")).strip(),
        })

    written = False
    if grade_file and suggestions:
        info = inspect_paper(grade_file)
        cellmap = {c["key"]: c for c in info.get("criteria", [])}
        edits = []
        for s in suggestions:
            c = cellmap.get(s["key"])
            if c:
                edits.append({"cell": c["awarded_cell"], "value": s["points"]})
                edits.append({"cell": c["comment_cell"], "value": s["comment"]})
        if edits:
            update_grade(grade_file, edits)
            written = True

    return {
        "suggestions": suggestions,
        "model": model,
        "strictness": strictness,
        "written": written,
    }

