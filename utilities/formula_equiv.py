"""
formula_equiv.py — decide whether a student's Excel formula is mathematically
equivalent to a known-correct formula.

How it works: collect every cell reference in both formulas, assign random
values to them, evaluate both formulas, and compare. Repeat several times. If
they agree on every trial, they compute the same thing — regardless of how the
student wrote it (operand order, parentheses, SUM vs +chain, algebraic rewrites).

Because the inputs are random, a hard-coded number can't match (it won't track
the inputs), so this also enforces "use cell references" without extra checks.

Only safe arithmetic is evaluated (via Python's ast); unsupported things
(cross-sheet refs, unknown functions like PMT/IF) raise, and callers treat that
as "can't verify" and fall back to their existing checks. This module therefore
only ever ADDS acceptance of correct answers — it never credits wrong math.
"""

import ast
import re
import random

_RANGE_RE = re.compile(r"\$?([A-Za-z]{1,3})\$?(\d{1,5})\s*:\s*\$?([A-Za-z]{1,3})\$?(\d{1,5})")
_CELL_RE = re.compile(r"\$?([A-Za-z]{1,3})\$?(\d{1,5})")
_SUPPORTED_FUNCS = ("sum", "min", "max", "average", "abs", "round")


def _col_to_int(col):
    n = 0
    for ch in col.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def _int_to_col(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _expand_range(c1, r1, c2, r2):
    a, b = _col_to_int(c1), _col_to_int(c2)
    cells = []
    for col in range(min(a, b), max(a, b) + 1):
        for row in range(min(int(r1), int(r2)), max(int(r1), int(r2)) + 1):
            cells.append(f"{_int_to_col(col)}{row}")
    return cells


def _normalize(formula):
    """Lowercase-strip and reject things we can't safely evaluate."""
    f = formula.strip()
    if f.startswith("="):
        f = f[1:]
    if "!" in f:               # cross-sheet reference — not numerically checkable here
        raise ValueError("cross-sheet reference")
    f = f.replace("$", "").replace("^", "**")
    return f


def _func_to_python(f):
    """Rewrite SUM/MIN/MAX/AVERAGE(range or args) into Python, expanding ranges."""
    def expand_args(inner):
        parts = []
        for token in inner.split(","):
            token = token.strip()
            m = _RANGE_RE.fullmatch(token)
            if m:
                parts.extend(_expand_range(m.group(1), m.group(2), m.group(3), m.group(4)))
            else:
                parts.append(token)
        return parts

    # Repeatedly replace the innermost supported function call.
    pattern = re.compile(r"\b(sum|min|max|average|abs|round)\s*\(([^()]*)\)", re.I)
    while True:
        m = pattern.search(f)
        if not m:
            break
        name = m.group(1).lower()
        args = expand_args(m.group(2))
        if name == "sum":
            repl = "(" + "+".join(args) + ")"
        elif name == "min":
            repl = "min(" + ",".join(args) + ")"
        elif name == "max":
            repl = "max(" + ",".join(args) + ")"
        elif name == "average":
            repl = "((" + "+".join(args) + ")/" + str(len(args)) + ")"
        elif name == "abs":
            repl = "abs(" + ",".join(args) + ")"
        elif name == "round":
            repl = "round(" + ",".join(args) + ")"
        f = f[: m.start()] + repl + f[m.end():]
    return f


def _refs(formula):
    """Every individual cell reference in a formula (ranges expanded)."""
    f = formula
    refs = set()
    for m in _RANGE_RE.finditer(f):
        refs.update(_expand_range(m.group(1), m.group(2), m.group(3), m.group(4)))
    for m in _CELL_RE.finditer(_RANGE_RE.sub(" ", f)):
        refs.add(f"{m.group(1).upper()}{m.group(2)}")
    return refs


_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
    ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Constant, ast.Name, ast.Load,
    ast.Call, ast.Mod,
)


def _safe_eval(expr, env):
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"unsupported expression element: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ("min", "max", "abs", "round"):
                raise ValueError("unsupported function")
    return eval(compile(tree, "<formula>", "eval"), {"__builtins__": {}, "min": min, "max": max, "abs": abs, "round": round}, env)


def _evaluate(formula, values):
    f = _normalize(formula)
    f = _func_to_python(f)
    # Substitute cell refs with python variable names (the refs themselves are
    # valid identifiers like K36), then eval against the values env.
    env = {ref: values[ref] for ref in values}
    return _safe_eval(f, env)


def formulas_equivalent(student, canonical, trials=12, tol=1e-7):
    """
    True if `student` computes the same as `canonical` across random inputs.
    Returns False (never raises) if the student formula can't be safely
    evaluated, so callers can fall back to their existing checks.
    """
    if not isinstance(student, str) or not isinstance(canonical, str):
        return False
    try:
        refs = _refs(_normalize(student)) | _refs(_normalize(canonical))
    except Exception:
        return False
    if not refs:
        return False
    rng = random.Random(12345)  # deterministic
    for _ in range(trials):
        values = {r: rng.uniform(1.5, 9.5) for r in refs}
        try:
            s = _evaluate(student, values)
            c = _evaluate(canonical, values)
        except Exception:
            return False
        if abs(s - c) > tol * max(1.0, abs(c)):
            return False
    return True


def equivalent_to_any(student, canonicals, trials=12, tol=1e-7):
    """True if the student formula is equivalent to ANY of the canonical forms.
    Use a list when a cell has genuinely distinct valid approaches (e.g. a sum
    form and an expanded-product form that reference different cells)."""
    return any(formulas_equivalent(student, c, trials, tol) for c in (canonicals or []))
