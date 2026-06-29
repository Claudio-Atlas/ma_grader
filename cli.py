#!/usr/bin/env python3
"""
cli.py — Command-line / sidecar entry point for the MA Grader engine.

This is the bridge the desktop (Electron) app talks to. It runs the existing
grading pipeline (web_adapter.grade_zip) and streams newline-delimited JSON
(NDJSON) events to stdout so the UI can show live progress.

Usage:
    python3 cli.py grade \
        --zip "/path/to/submissions.zip" \
        --course "MAT-144-501" \
        --assignment MA2 \
        --workspace "/path/to/output_folder"

Protocol (one JSON object per line on stdout):
    {"type": "start",    "total": null}
    {"type": "progress", "current": 3, "total": 17, "student": "Jane_Doe"}
    {"type": "result",   "data": { ...full grade_zip dict... }}
    {"type": "error",    "message": "..."}

Anything written to stderr is treated as diagnostic logging by the app.
Exit code 0 on success, 1 on a fatal error.
"""

import os
import sys
import json
import argparse

# Make sure the engine package root is importable whether we're running from
# source (python3 cli.py ...) or frozen by PyInstaller.
#
# When frozen, PyInstaller unpacks bundled code + data files into sys._MEIPASS,
# so __file__ is not a usable on-disk path. Use _MEIPASS as the engine root in
# that case so that asset lookups (assets_templates/, assets_feedback/) resolve.
if getattr(sys, "frozen", False):
    _ENGINE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    _ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)


# Reserve the *real* stdout for NDJSON only. Any stray print() inside the
# engine is redirected to stderr (see _cmd_grade) so it can't corrupt the
# event stream the app parses.
_NDJSON_OUT = sys.stdout


def _emit(obj: dict) -> None:
    """Write a single NDJSON event to the reserved stdout and flush."""
    _NDJSON_OUT.write(json.dumps(obj, default=str) + "\n")
    _NDJSON_OUT.flush()


def _cmd_grade(args: argparse.Namespace) -> int:
    # Imported here so import errors surface as a clean NDJSON error event.
    import web_adapter

    _emit({"type": "start", "total": None})

    def progress(current, total, student):
        _emit({
            "type": "progress",
            "current": current,
            "total": total,
            "student": student,
        })

    # Redirect any engine print() calls to stderr so they don't pollute the
    # NDJSON channel. Our own events still go to the reserved _NDJSON_OUT.
    _saved_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        result = web_adapter.grade_zip(
            zip_path=args.zip,
            course_label=args.course,
            assignment_type=args.assignment,
            workspace=args.workspace,
            progress_callback=progress,
        )
    except Exception as exc:  # noqa: BLE001 - report any failure to the UI
        _emit({"type": "error", "message": str(exc)})
        return 1
    finally:
        sys.stdout = _saved_stdout

    # grade_zip already swallows most errors and returns an "error" key.
    if isinstance(result, dict) and result.get("error"):
        _emit({"type": "result", "data": result})
        return 0

    _emit({"type": "result", "data": result})
    return 0


def _cmd_grade_one(args: argparse.Namespace) -> int:
    import web_adapter

    _emit({"type": "start", "total": 1})

    def progress(current, total, student):
        _emit({"type": "progress", "current": current, "total": total, "student": student})

    _saved_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        result = web_adapter.grade_one(
            workbook_path=args.workbook,
            course_label=args.course,
            student_name=args.student,
            assignment_type=args.assignment,
            workspace=args.workspace,
            paper_path=args.paper,
            progress_callback=progress,
        )
    except Exception as exc:  # noqa: BLE001
        _emit({"type": "error", "message": str(exc)})
        return 1
    finally:
        sys.stdout = _saved_stdout

    _emit({"type": "result", "data": result})
    return 0


def _run_json(make_result) -> int:
    """Run a function that returns a dict, emit it as a single result event.
    Redirects engine stdout to stderr so only the JSON reaches the app."""
    import web_adapter  # noqa: F401  (ensures path is set up)
    _saved = sys.stdout
    sys.stdout = sys.stderr
    try:
        data = make_result()
    except Exception as exc:  # noqa: BLE001
        sys.stdout = _saved
        _emit({"type": "error", "message": str(exc)})
        return 1
    sys.stdout = _saved
    _emit({"type": "result", "data": data})
    return 0


def _cmd_inspect_workbook(args):
    import web_adapter
    return _run_json(lambda: web_adapter.inspect_workbook(args.file))


def _cmd_inspect_grade(args):
    import web_adapter
    return _run_json(lambda: web_adapter.inspect_grade(args.file, args.assignment))


def _cmd_update_grade(args):
    import web_adapter
    edits = json.loads(args.edits) if args.edits else []
    return _run_json(lambda: web_adapter.update_grade(args.file, edits))


def _cmd_inspect_paper(args):
    import web_adapter
    return _run_json(lambda: web_adapter.inspect_paper(args.file))


def _cmd_paper_text(args):
    import web_adapter
    return _run_json(lambda: web_adapter.extract_paper_text(args.paper))


def _cmd_ai_test_key(args):
    import web_adapter
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return _run_json(lambda: web_adapter.ai_test_key(key))


def _cmd_ai_grade_paper(args):
    import web_adapter
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = args.model or web_adapter.DEFAULT_AI_MODEL
    return _run_json(lambda: web_adapter.ai_grade_paper(
        args.paper, key, model=model, strictness=args.strictness,
        grade_file=args.grade_file))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ma-grader", description="MA Grader engine CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("grade", help="Grade a ZIP of student submissions")
    g.add_argument("--zip", required=True, help="Path to the submissions .zip")
    g.add_argument("--course", required=True, help='Course label, e.g. "MAT-144-501"')
    g.add_argument("--assignment", default="MA1", choices=["MA1", "MA2", "MA3"],
                   help="Assignment type (default: MA1)")
    g.add_argument("--workspace", default=None,
                   help="Output workspace folder (a temp dir is used if omitted)")
    g.set_defaults(func=_cmd_grade)

    o = sub.add_parser("grade-one", help="Grade a single student's workbook")
    o.add_argument("--workbook", required=True, help="Path to the student's .xlsx")
    o.add_argument("--course", required=True, help='Course label, e.g. "MAT 144 Online"')
    o.add_argument("--student", required=True, help='Student name, "First Last"')
    o.add_argument("--assignment", default="MA1", choices=["MA1", "MA2", "MA3"])
    o.add_argument("--workspace", default=None, help="Persistent workspace folder")
    o.add_argument("--paper", default=None, help="Optional MA2 write-up (.docx/.pdf)")
    o.set_defaults(func=_cmd_grade_one)

    iw = sub.add_parser("inspect-workbook", help="Dump a workbook's cells as JSON")
    iw.add_argument("--file", required=True)
    iw.set_defaults(func=_cmd_inspect_workbook)

    ig = sub.add_parser("inspect-grade", help="Dump a grade sheet's rubric rows as JSON")
    ig.add_argument("--file", required=True)
    ig.add_argument("--assignment", default="MA2", choices=["MA1", "MA2", "MA3"])
    ig.set_defaults(func=_cmd_inspect_grade)

    ug = sub.add_parser("update-grade", help="Write edited scores/comments back")
    ug.add_argument("--file", required=True)
    ug.add_argument("--edits", required=True, help='JSON list of {"cell","value"}')
    ug.set_defaults(func=_cmd_update_grade)

    ip = sub.add_parser("inspect-paper", help="Read the Written Paper rubric section")
    ip.add_argument("--file", required=True, help="Path to the *_Grade.xlsx")
    ip.set_defaults(func=_cmd_inspect_paper)

    pt = sub.add_parser("paper-text", help="Extract text from a .docx/.pdf paper")
    pt.add_argument("--paper", required=True)
    pt.set_defaults(func=_cmd_paper_text)

    tk = sub.add_parser("ai-test-key", help="Validate ANTHROPIC_API_KEY (from env)")
    tk.set_defaults(func=_cmd_ai_test_key)

    ag = sub.add_parser("ai-grade-paper", help="AI-propose levels for a paper (env key)")
    ag.add_argument("--paper", required=True)
    ag.add_argument("--strictness", default="standard",
                    choices=["lenient", "standard", "elite"])
    ag.add_argument("--model", default=None, help="Anthropic model id")
    ag.add_argument("--grade-file", default=None,
                    help="If set, write the AI scores into this grade sheet")
    ag.set_defaults(func=_cmd_ai_grade_paper)

    # Lightweight handshake so the app can verify the sidecar is alive.
    p = sub.add_parser("ping", help="Print a readiness event and exit")
    p.set_defaults(func=lambda a: (_emit({"type": "pong"}) or 0))

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
