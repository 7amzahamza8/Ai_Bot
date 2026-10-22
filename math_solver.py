"""Mathe-Löser: كل منطق sympy هنا. ملف الـ API (main.py) بس بينادي solve()."""
import itertools
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from datetime import datetime

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from messages import AppError

MAX_LENGTH = 200       # أقصى طول للمعادلة
TIMEOUT_SECONDS = 10   # لو الحساب أطول من كده بيتوقف برسالة خطأ
MAX_HISTORY = 50       # عدد العمليات اللي بتتحفظ في الهستوري


# نتيجة "مفيش حل". الواجهة بتحوّلها لنص باللغة المختارة (kind = "no_solution")
NO_SOLUTION = "∅"


class MathError(AppError):
    """خطأ بمفتاح رسالة من messages.py. الرسالة بتتترجم لما الـ API يرجّعها (error.text(lang))."""


# العمليات اللي بتظهر في الواجهة. "needs" = الخانات الإضافية اللي العملية محتاجاها
OPERATIONS = [
    {"id": "solve", "label": "Lösen",
     "hint": "Gleichung lösen. Ein Gleichungssystem trennst du mit ;",
     "needs": ["variable"]},
    {"id": "simplify", "label": "Vereinfachen",
     "hint": "Ausdruck vereinfachen", "needs": []},
    {"id": "expand", "label": "Ausmultiplizieren",
     "hint": "Klammern auflösen", "needs": []},
    {"id": "factor", "label": "Faktorisieren",
     "hint": "In Faktoren zerlegen", "needs": []},
    {"id": "diff", "label": "Ableiten",
     "hint": "Ableitung nach einer Variable", "needs": ["variable"]},
    {"id": "integrate", "label": "Integrieren",
     "hint": "Unbestimmtes Integral, oder bestimmt mit Von und Bis",
     "needs": ["variable", "lower", "upper"]},
    {"id": "limit", "label": "Grenzwert",
     "hint": "Grenzwert an einem Punkt (oo = unendlich)",
     "needs": ["variable", "point"]},
    {"id": "evalf", "label": "Zahlenwert",
     "hint": "Ausdruck als Dezimalzahl berechnen", "needs": []},
]
_OPS_BY_ID = {op["id"]: op for op in OPERATIONS}

# ---------- الأمان: بنسمح بأدوات رياضية محددة بس ----------
_FUNCS = ["sin", "cos", "tan", "cot", "asin", "acos", "atan", "sinh", "cosh",
          "tanh", "exp", "log", "sqrt", "factorial", "floor", "ceiling"]
LOCALS = {name: getattr(sp, name) for name in _FUNCS}
LOCALS.update({"ln": sp.log, "abs": sp.Abs, "Abs": sp.Abs,
               "pi": sp.pi, "e": sp.E, "oo": sp.oo})
GLOBALS = {name: getattr(sp, name) for name in
           ("Integer", "Float", "Rational", "Symbol", "Function",
            "factorial", "factorial2")}
TRANSFORMATIONS = standard_transformations + (
    convert_xor,                          # x^2 بدل x**2
    implicit_multiplication_application,  # 2x و sin x
)

_ALLOWED_CHARS = re.compile(r"^[A-Za-z0-9+\-*/^().,=;!\s]+$")
_ATTRIBUTE = re.compile(r"\.\s*[A-Za-z]")
_BIG_POWER = re.compile(r"(\^|\*\*)\s*\(?\s*-?\d{4,}")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")

_pool = ThreadPoolExecutor(max_workers=4)

# ---------- الهستوري (في الذاكرة، بيتمسح لما السيرفر يقفل) ----------
_history = []
_history_lock = threading.Lock()
_ids = itertools.count(1)


def operations_list():
    return OPERATIONS


def get_history():
    with _history_lock:
        return list(reversed(_history))   # الأحدث الأول


def clear_history():
    with _history_lock:
        _history.clear()


def _add_history(entry):
    with _history_lock:
        _history.append(entry)
        del _history[:-MAX_HISTORY]


# ---------- قراءة المدخلات ----------
def _txt(value):
    return str(value).replace("**", "^")


def _check(text):
    if not text or not text.strip():
        raise MathError("empty_equation")
    if len(text) > MAX_LENGTH:
        raise MathError("too_long", max=MAX_LENGTH)
    if not _ALLOWED_CHARS.match(text):
        raise MathError("bad_chars")
    if _ATTRIBUTE.search(text):
        raise MathError("dot_before_letter")
    if _BIG_POWER.search(text):
        raise MathError("exponent_too_big")


def _parse(text):
    text = text.strip()
    if not text:
        raise MathError("side_empty")
    try:
        result = parse_expr(text, local_dict=dict(LOCALS),
                            global_dict=dict(GLOBALS),
                            transformations=TRANSFORMATIONS)
    except Exception:
        raise MathError("parse_failed", text=text) from None
    if not isinstance(result, sp.Expr):
        raise MathError("parse_failed", text=text)
    return result


def _symbol(name):
    name = name.strip()
    if not _NAME.match(name):
        raise MathError("bad_variable", name=name)
    return sp.Symbol(name)


def _need_variable(expr, name):
    if name:
        return _symbol(name)
    symbols = sorted(expr.free_symbols, key=str)
    if len(symbols) == 1:
        return symbols[0]
    if not symbols:
        raise MathError("no_variable")
    names = ", ".join(str(s) for s in symbols)
    raise MathError("many_variables", names=names)


# ---------- العمليات ----------
def _solve(text, variable):
    parts = [p.strip() for p in text.split(";") if p.strip()]
    if not parts:
        raise MathError("empty_equation")

    exprs, shown = [], []
    for part in parts:
        if part.count("=") > 1:
            raise MathError("one_equals")
        if "=" in part:
            left, right = (_parse(side) for side in part.split("="))
        else:
            left, right = _parse(part), sp.Integer(0)   # من غير = يعني = 0
        exprs.append(left - right)
        shown.append(f"{sp.latex(left)} = {sp.latex(right)}")
    input_latex = r" \quad ; \quad ".join(shown)

    all_symbols = sorted(set().union(*(e.free_symbols for e in exprs)), key=str)
    if variable:
        var = _symbol(variable)
        if var not in all_symbols:
            raise MathError("var_not_in_equation", var=var)
        var_list = [var]
    elif len(all_symbols) <= 1 or len(exprs) > 1:
        var_list = all_symbols
    else:
        names = ", ".join(str(s) for s in all_symbols)
        raise MathError("many_variables", names=names)
    if not var_list:
        raise MathError("no_variable")

    no_solution = (NO_SOLUTION, r"\varnothing", input_latex)

    if len(exprs) == 1 and len(var_list) == 1:
        var = var_list[0]
        solutions = sp.solve(exprs[0], var)
        if not solutions:
            return no_solution
        result = ";  ".join(f"{var} = {_txt(s)}" for s in solutions)
        latex = r",\quad ".join(f"{sp.latex(var)} = {sp.latex(s)}" for s in solutions)
        return result, latex, input_latex

    solutions = sp.solve(exprs, var_list, dict=True)
    if not solutions:
        return no_solution
    lines, latex_lines = [], []
    for sol in solutions:
        lines.append(", ".join(f"{k} = {_txt(v)}" for k, v in sol.items()))
        latex_lines.append(r",\; ".join(f"{sp.latex(k)} = {sp.latex(v)}" for k, v in sol.items()))
    return "\n".join(lines), r" \quad\lor\quad ".join(latex_lines), input_latex


def _expression_op(text, operation, variable, point, lower, upper):
    if "=" in text or ";" in text:
        raise MathError("no_equals_here")
    expr = _parse(text)
    input_latex = sp.latex(expr)
    suffix, latex_suffix = "", ""

    if operation == "simplify":
        res = sp.simplify(expr)
    elif operation == "expand":
        res = sp.expand(expr)
    elif operation == "factor":
        res = sp.factor(expr)
    elif operation == "diff":
        res = sp.diff(expr, _need_variable(expr, variable))
    elif operation == "integrate":
        var = _need_variable(expr, variable)
        if lower or upper:
            if not (lower and upper):
                raise MathError("need_bounds")
            res = sp.integrate(expr, (var, _parse(lower), _parse(upper)))
        else:
            res = sp.integrate(expr, var)
            suffix, latex_suffix = " + C", " + C"
        if res.has(sp.Integral):
            raise MathError("integral_unsolvable")
    elif operation == "limit":
        var = _need_variable(expr, variable)
        target = _parse(point) if point else sp.Integer(0)
        res = sp.limit(expr, var, target)
        if res.has(sp.Limit):
            raise MathError("limit_unsolvable")
    elif operation == "evalf":
        if expr.free_symbols:
            raise MathError("has_variables")
        res = sp.N(expr, 15)
    else:
        raise MathError("unknown_operation")

    return _txt(res) + suffix, sp.latex(res) + latex_suffix, input_latex


def _run(expression, operation, variable, point, lower, upper):
    if operation not in _OPS_BY_ID:
        raise MathError("unknown_operation")
    _check(expression)
    if operation == "solve":
        return _solve(expression, variable)
    return _expression_op(expression, operation, variable, point, lower, upper)


# ---------- الدالة اللي الـ API بينادي عليها ----------
def solve(expression, operation, variable=None, point=None, lower=None, upper=None):
    expression = (expression or "").strip()
    variable, point = (variable or "").strip() or None, (point or "").strip() or None
    lower, upper = (lower or "").strip() or None, (upper or "").strip() or None

    future = _pool.submit(_run, expression, operation, variable, point, lower, upper)
    try:
        result, latex, input_latex = future.result(timeout=TIMEOUT_SECONDS)
    except FutureTimeout:
        raise MathError("timeout", seconds=TIMEOUT_SECONDS) from None
    except MathError:
        raise
    except Exception as error:
        raise MathError("calc_failed", kind=type(error).__name__) from None

    entry = {
        "id": next(_ids),
        "time": datetime.now().strftime("%H:%M:%S"),
        "expression": expression,
        "operation": operation,
        "operation_label": _OPS_BY_ID[operation]["label"],
        "result": result,
        "latex": latex,
        "input_latex": input_latex,
        "kind": "no_solution" if result == NO_SOLUTION else "ok",
        "params": {"variable": variable, "point": point, "lower": lower, "upper": upper},
    }
    _add_history(entry)
    return entry


# ---------- Diagramm ----------
PLOT_RANGE = (-10, 10)
PLOT_POINTS = 400


def render_png(x, y, title):
    """بيرسم المنحنى ويرجّع data-URI لصورة PNG. matplotlib (Figure) من غير pyplot، عشان آمن مع الخيوط."""
    import base64
    import io

    import numpy as np
    from matplotlib.figure import Figure

    finite = y[np.isfinite(y)]
    if finite.size == 0:
        raise MathError("plot_empty")

    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    ax.plot(x, np.where(np.isfinite(y), y, np.nan), linewidth=2)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.grid(True, alpha=0.3)
    ax.set_title(title.replace("$", ""), fontsize=10)

    # tan(x) أو 1/x بيوصلوا لقيم ضخمة: نقصّ المحور الرأسي عشان باقي المنحنى يبان
    low, high = np.percentile(finite, [2, 98])
    pad = (high - low) * 0.5 or 1.0
    if finite.max() > high + 4 * pad or finite.min() < low - 4 * pad:
        ax.set_ylim(low - pad, high + pad)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _plot(expression, var_name):
    try:
        import numpy as np
    except ImportError:
        raise MathError("plot_needs_matplotlib") from None
    _check(expression)       # نفس فحص باقي العمليات: بدونه parse_expr ممكن ينفّذ كود
    if "=" in expression or ";" in expression:
        raise MathError("plot_no_equals")
    expr = _parse(expression)
    var = _symbol(var_name or "x")
    others = sorted(expr.free_symbols - {var}, key=str)
    if others:
        raise MathError("many_variables", names=", ".join(str(s) for s in others))

    func = sp.lambdify(var, expr, modules=["numpy"])
    x = np.linspace(PLOT_RANGE[0], PLOT_RANGE[1], PLOT_POINTS)
    with np.errstate(all="ignore"):
        y = np.asarray(func(x))
        if np.iscomplexobj(y):
            y = np.where(np.abs(y.imag) < 1e-12, y.real, np.nan)
        y = np.broadcast_to(y.astype(float), x.shape)      # دالة ثابتة زي "5" بترجّع رقم واحد
    return render_png(x, y, f"y = {_txt(expr)}")


def plot_expression(expression, var_name="x"):
    """بيرجّع data-URI لصورة PNG لرسم الدالة بين -10 و 10 (بنفس المهلة والحماية بتاعة solve)."""
    future = _pool.submit(_plot, (expression or "").strip(), (var_name or "").strip())
    try:
        return future.result(timeout=TIMEOUT_SECONDS)
    except FutureTimeout:
        raise MathError("timeout", seconds=TIMEOUT_SECONDS) from None
    except MathError:
        raise
    except Exception as error:
        raise MathError("plot_failed", kind=type(error).__name__) from None
