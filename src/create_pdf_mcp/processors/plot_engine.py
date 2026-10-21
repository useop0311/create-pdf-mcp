import math
import re
from collections import defaultdict
import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
from xml.sax.saxutils import escape
from ..models.figures import (
    FunctionPlotSpec,
    FunctionCurve,
    ImplicitCurve,
    ParametricCurve,
    PolarCurve,
    PlotPoint,
    ShadedArea,
)
from .math_text import format_svg_math_label, _replace_fractions, _replace_roots


_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

_X_SYM = sp.Symbol("x", real=True)
_Y_SYM = sp.Symbol("y", real=True)
_T_SYM = sp.Symbol("t", real=True)
_THETA_SYM = sp.Symbol("theta", real=True)
_R_SYM = sp.Symbol("r", real=True)

_LOCAL_DICT = {
    "x": _X_SYM,
    "y": _Y_SYM,
    "t": _T_SYM,
    "theta": _THETA_SYM,
    "r": _R_SYM,
    "e": sp.E,
    "pi": sp.pi,
    "ln": sp.log,
    "log": sp.log,
    "abs": sp.Abs,
    "Abs": sp.Abs,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sec": sp.sec,
    "csc": sp.csc,
    "cot": sp.cot,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "arcsin": sp.asin,
    "arccos": sp.acos,
    "arctan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "sqrt": sp.sqrt,
    "exp": sp.exp,
    "floor": sp.floor,
    "ceiling": sp.ceiling,
    "ceil": sp.ceiling,
    "sign": sp.sign,
}


def _preprocess_expr_str(raw: str) -> str:
    """Normalizes LaTeX, caret powers, and implicit multiplication for SymPy parsing."""
    s = raw.strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()

    s = _replace_fractions(s)
    s = _replace_roots(s)
    s = re.sub(r"\\(?:left|right)", "", s)
    s = re.sub(r"\|([^|=<>]+)\|", r"Abs(\1)", s)

    latex_funcs = [
        "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh",
        "sin", "cos", "tan", "sec", "csc", "cot",
        "ln", "log", "exp", "sqrt", "pi", "theta",
    ]
    for fn in latex_funcs:
        s = re.sub(rf"\\{fn}(?![a-zA-Z])", f" {fn} ", s)

    s = s.replace("{", "(").replace("}", ")")
    s = s.replace("^", "**")
    return s


def _parse_single_expr(raw: str) -> sp.Expr:
    s = _preprocess_expr_str(raw)
    if "=" in s and not any(op in s for op in ("<=", ">=", "==", "!=")):
        lhs_s, rhs_s = s.split("=", 1)
        lhs = parse_expr(lhs_s.strip(), local_dict=_LOCAL_DICT, transformations=_TRANSFORMATIONS)
        rhs = parse_expr(rhs_s.strip(), local_dict=_LOCAL_DICT, transformations=_TRANSFORMATIONS)
        if lhs in (_Y_SYM, _X_SYM, _R_SYM) and lhs not in rhs.free_symbols:
            return rhs
        if rhs in (_Y_SYM, _X_SYM, _R_SYM) and rhs not in lhs.free_symbols:
            return lhs
        return lhs - rhs
    return parse_expr(s, local_dict=_LOCAL_DICT, transformations=_TRANSFORMATIONS)


def _classify_and_parse_expr(raw: str) -> tuple[str, sp.Expr]:
    """
    Classifies a mathematical expression string into:
    - 'explicit_y': y = f(x)
    - 'explicit_x': x = g(y)
    - 'implicit':   F(x, y) = 0
    - 'polar':      r = f(theta)
    """
    s = _preprocess_expr_str(raw)
    if "=" in s and not any(op in s for op in ("<=", ">=", "==", "!=")):
        lhs_s, rhs_s = s.split("=", 1)
        lhs = parse_expr(lhs_s.strip(), local_dict=_LOCAL_DICT, transformations=_TRANSFORMATIONS)
        rhs = parse_expr(rhs_s.strip(), local_dict=_LOCAL_DICT, transformations=_TRANSFORMATIONS)
        if lhs == _Y_SYM and _Y_SYM not in rhs.free_symbols:
            return "explicit_y", rhs
        if rhs == _Y_SYM and _Y_SYM not in lhs.free_symbols:
            return "explicit_y", lhs
        if lhs == _X_SYM and _X_SYM not in rhs.free_symbols:
            return "explicit_x", rhs
        if rhs == _X_SYM and _X_SYM not in lhs.free_symbols:
            return "explicit_x", lhs
        if lhs == _R_SYM and _R_SYM not in rhs.free_symbols:
            return "polar", rhs
        if rhs == _R_SYM and _R_SYM not in lhs.free_symbols:
            return "polar", lhs
        return "implicit", lhs - rhs

    expr = parse_expr(s, local_dict=_LOCAL_DICT, transformations=_TRANSFORMATIONS)
    free = expr.free_symbols
    if _Y_SYM in free:
        if _X_SYM not in free:
            return "explicit_x", expr
        return "implicit", expr
    if _THETA_SYM in free:
        return "polar", expr
    return "explicit_y", expr


def _eval_bound(val: float | int | str) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    expr = _parse_single_expr(str(val))
    return float(expr.evalf())


def _safe_eval_1d(fn, val: float) -> float | None:
    try:
        with np.errstate(all="ignore"):
            res = complex(fn(val))
            if abs(res.imag) > 1e-9:
                return None
            f_val = float(res.real)
            return f_val if math.isfinite(f_val) else None
    except Exception:
        return None


def _bisect_domain_edge(fn, u_invalid: float, u_valid: float, steps: int = 14) -> tuple[float, float]:
    """Finds the exact domain boundary where fn transitions between None (NaN/complex) and valid float."""
    lo_inv = u_invalid
    hi_val = u_valid
    last_good_v = _safe_eval_1d(fn, u_valid) or 0.0
    for _ in range(steps):
        mid = 0.5 * (lo_inv + hi_val)
        v_mid = _safe_eval_1d(fn, mid)
        if v_mid is not None:
            hi_val = mid
            last_good_v = v_mid
        else:
            lo_inv = mid
    return hi_val, last_good_v


def _sample_explicit_1d(
    fn,
    u_min: float,
    u_max: float,
    v_min: float,
    v_max: float,
    swap_xy: bool = False,
    num_points: int = 400,
) -> list[list[tuple[float, float]]]:
    """
    Samples y = f(x) (or x = g(y) if swap_xy=True) with:
    - Exact domain boundary bisection (for sqrt, log, etc.)
    - Adaptive midpoint subdivision for high curvature / steep slopes
    - Discontinuity & pole detection (avoiding false vertical asymptote lines)
    """
    v_span = max(v_max - v_min, 1e-3)
    v_clamp_min = v_min - v_span * 2.5
    v_clamp_max = v_max + v_span * 2.5

    us = np.linspace(u_min, u_max, num_points)
    raw_vals = [_safe_eval_1d(fn, float(u)) for u in us]

    segments: list[list[tuple[float, float]]] = []
    curr_seg: list[tuple[float, float]] = []

    def to_pt(u: float, v: float) -> tuple[float, float]:
        return (v, u) if swap_xy else (u, v)

    def subdivide(u_a: float, v_a: float, u_b: float, v_b: float, depth: int = 0) -> list[tuple[float, float]]:
        """Returns intermediate points between (u_a, v_a) and (u_b, v_b), or None if discontinuous."""
        u_m = 0.5 * (u_a + u_b)
        v_m = _safe_eval_1d(fn, u_m)
        if v_m is None or not (v_clamp_min <= v_m <= v_clamp_max):
            return None  # Discontinuity

        # Check if midpoint explodes away from [v_a, v_b] (pole like 1/x or tan(x))
        v_lo, v_hi = min(v_a, v_b), max(v_a, v_b)
        jump = abs(v_b - v_a)
        if jump > v_span * 0.25:
            # For a monotonic jump across a pole, v_m will be outside [v_lo, v_hi] or jump remains huge
            if v_m < v_lo - v_span * 0.1 or v_m > v_hi + v_span * 0.1:
                return None
            # Check sub-midpoints to catch step functions (like floor(x)) or steep poles
            v_q1 = _safe_eval_1d(fn, 0.5 * (u_a + u_m))
            v_q3 = _safe_eval_1d(fn, 0.5 * (u_m + u_b))
            if v_q1 is None or v_q3 is None:
                return None
            max_sub_jump = max(abs(v_q1 - v_a), abs(v_m - v_q1), abs(v_q3 - v_m), abs(v_b - v_q3))
            # In a continuous function, quarter-step jump shrinks by ~1/4. In a step/pole, it stays >= 0.7 * jump!
            if max_sub_jump > jump * 0.75 and jump > v_span * 0.15:
                return None

        # Check linear deviation for adaptive refinement
        lin_v = 0.5 * (v_a + v_b)
        if depth < 4 and (abs(v_m - lin_v) > v_span * 0.008 or jump > v_span * 0.12):
            left_pts = subdivide(u_a, v_a, u_m, v_m, depth + 1)
            if left_pts is None:
                return None
            right_pts = subdivide(u_m, v_m, u_b, v_b, depth + 1)
            if right_pts is None:
                return None
            return left_pts + [to_pt(u_m, v_m)] + right_pts

        return [to_pt(u_m, v_m)] if abs(v_m - lin_v) > v_span * 0.002 else []

    for idx in range(len(us)):
        u_curr = float(us[idx])
        v_curr = raw_vals[idx]

        if v_curr is None or not (v_clamp_min <= v_curr <= v_clamp_max):
            # Transition from valid -> invalid: refine right endpoint if it was a domain boundary (v_curr is None)
            if curr_seg and v_curr is None and idx > 0 and raw_vals[idx - 1] is not None:
                u_edge, v_edge = _bisect_domain_edge(fn, u_curr, float(us[idx - 1]))
                if v_clamp_min <= v_edge <= v_clamp_max:
                    curr_seg.append(to_pt(u_edge, v_edge))
            if curr_seg:
                segments.append(curr_seg)
                curr_seg = []
            continue

        # Transition from invalid -> valid: refine left domain boundary
        if not curr_seg and idx > 0 and raw_vals[idx - 1] is None:
            u_edge, v_edge = _bisect_domain_edge(fn, float(us[idx - 1]), u_curr)
            if v_clamp_min <= v_edge <= v_clamp_max:
                curr_seg.append(to_pt(u_edge, v_edge))

        if curr_seg:
            prev_pt = curr_seg[-1]
            u_prev = prev_pt[1] if swap_xy else prev_pt[0]
            v_prev = prev_pt[0] if swap_xy else prev_pt[1]

            mid_pts = subdivide(u_prev, v_prev, u_curr, v_curr)
            if mid_pts is None:
                segments.append(curr_seg)
                curr_seg = [to_pt(u_curr, v_curr)]
                continue
            curr_seg.extend(mid_pts)

        curr_seg.append(to_pt(u_curr, v_curr))

    if curr_seg:
        segments.append(curr_seg)

    return segments


def _stitch_segments(
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    tol: float = 1e-5,
) -> list[list[tuple[float, float]]]:
    """Stitches disconnected Marching Squares line segments into continuous polylines."""
    if not segments:
        return []

    def pt_key(pt: tuple[float, float]) -> tuple[int, int]:
        return (round(pt[0] / tol), round(pt[1] / tol))

    adj: dict[tuple[int, int], list[tuple[int, tuple[float, float], tuple[int, int]]]] = defaultdict(list)
    for idx, (p1, p2) in enumerate(segments):
        k1, k2 = pt_key(p1), pt_key(p2)
        if k1 == k2:
            continue
        adj[k1].append((idx, p2, k2))
        adj[k2].append((idx, p1, k1))

    used = [False] * len(segments)
    polylines: list[list[tuple[float, float]]] = []

    for idx, (p1, p2) in enumerate(segments):
        if used[idx]:
            continue
        k1, k2 = pt_key(p1), pt_key(p2)
        if k1 == k2:
            used[idx] = True
            continue
        used[idx] = True
        chain = [p1, p2]

        # Extend forward from k2
        curr_k = k2
        while True:
            next_step = None
            for n_idx, n_pt, n_k in adj[curr_k]:
                if not used[n_idx]:
                    next_step = (n_idx, n_pt, n_k)
                    break
            if next_step is None:
                break
            n_idx, n_pt, n_k = next_step
            used[n_idx] = True
            chain.append(n_pt)
            curr_k = n_k

        # Extend backward from k1
        curr_k = k1
        while True:
            prev_step = None
            for n_idx, n_pt, n_k in adj[curr_k]:
                if not used[n_idx]:
                    prev_step = (n_idx, n_pt, n_k)
                    break
            if prev_step is None:
                break
            n_idx, n_pt, n_k = prev_step
            used[n_idx] = True
            chain.insert(0, n_pt)
            curr_k = n_k

        polylines.append(chain)

    return polylines


_MS_TABLE = {
    1: [(3, 0)],
    2: [(0, 1)],
    3: [(3, 1)],
    4: [(1, 2)],
    6: [(0, 2)],
    7: [(3, 2)],
    8: [(2, 3)],
    9: [(0, 2)],
    11: [(1, 2)],
    12: [(1, 3)],
    13: [(0, 1)],
    14: [(3, 0)],
}


def _marching_squares_implicit(
    expr: sp.Expr,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    grid_res: int = 180,
) -> list[list[tuple[float, float]]]:
    """
    Evaluates an implicit curve F(x, y) = 0 using 2D Marching Squares with
    linear sub-cell interpolation, saddle disambiguation, pole rejection, and polyline stitching.
    """
    f_xy = sp.lambdify((_X_SYM, _Y_SYM), expr, modules=["numpy", "math"])

    xs = np.linspace(x_min, x_max, grid_res)
    ys = np.linspace(y_min, y_max, grid_res)
    X, Y = np.meshgrid(xs, ys)

    with np.errstate(all="ignore"):
        try:
            Z = f_xy(X, Y)
            if np.ndim(Z) == 0:
                Z = np.full_like(X, float(Z))
            else:
                Z = np.asarray(Z, dtype=float)
        except Exception:
            def _scalar_f(xv: float, yv: float) -> float:
                try:
                    c = complex(f_xy(xv, yv))
                    return float(c.real) if abs(c.imag) < 1e-9 else float("nan")
                except Exception:
                    return float("nan")
            Z = np.vectorize(_scalar_f, otypes=[float])(X, Y)

    Z0 = Z[:-1, :-1]  # bottom-left
    Z1 = Z[:-1, 1:]   # bottom-right
    Z2 = Z[1:, 1:]    # top-right
    Z3 = Z[1:, :-1]   # top-left

    valid = np.isfinite(Z0) & np.isfinite(Z1) & np.isfinite(Z2) & np.isfinite(Z3)

    eps = 1e-12
    Z0_s = np.where(Z0 == 0, eps, Z0)
    Z1_s = np.where(Z1 == 0, eps, Z1)
    Z2_s = np.where(Z2 == 0, eps, Z2)
    Z3_s = np.where(Z3 == 0, eps, Z3)

    mask = (
        ((Z0_s > 0).astype(np.uint8))
        | ((Z1_s > 0).astype(np.uint8) << 1)
        | ((Z2_s > 0).astype(np.uint8) << 2)
        | ((Z3_s > 0).astype(np.uint8) << 3)
    )

    active_ys, active_xs = np.where(valid & (mask > 0) & (mask < 15))

    def interp(x_a: float, y_a: float, z_a: float, x_b: float, y_b: float, z_b: float) -> tuple[float, float]:
        denom = z_a - z_b
        t = 0.5 if abs(denom) < 1e-15 else max(0.0, min(1.0, z_a / denom))
        return (x_a + t * (x_b - x_a), y_a + t * (y_b - y_a))

    raw_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for i, j in zip(active_ys, active_xs):
        m = int(mask[i, j])
        x0, x1 = float(xs[j]), float(xs[j + 1])
        y0, y1 = float(ys[i]), float(ys[i + 1])
        z0, z1, z2, z3 = float(Z0_s[i, j]), float(Z1_s[i, j]), float(Z2_s[i, j]), float(Z3_s[i, j])

        def get_edge_pt(edge_idx: int) -> tuple[float, float]:
            if edge_idx == 0:
                return interp(x0, y0, z0, x1, y0, z1)
            elif edge_idx == 1:
                return interp(x1, y0, z1, x1, y1, z2)
            elif edge_idx == 2:
                return interp(x0, y1, z3, x1, y1, z2)
            else:
                return interp(x0, y0, z0, x0, y1, z3)

        if m in (5, 10):
            xc, yc = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            try:
                with np.errstate(all="ignore"):
                    zc = float(f_xy(xc, yc))
                if not math.isfinite(zc):
                    zc = 0.25 * (z0 + z1 + z2 + z3)
            except Exception:
                zc = 0.25 * (z0 + z1 + z2 + z3)
            if m == 5:
                pairs = [(3, 2), (0, 1)] if zc > 0 else [(3, 0), (1, 2)]
            else:
                pairs = [(3, 0), (1, 2)] if zc > 0 else [(3, 2), (0, 1)]
        else:
            pairs = _MS_TABLE.get(m, [])

        for e_start, e_end in pairs:
            p_start = get_edge_pt(e_start)
            p_end = get_edge_pt(e_end)
            xm, ym = 0.5 * (p_start[0] + p_end[0]), 0.5 * (p_start[1] + p_end[1])
            try:
                with np.errstate(all="ignore"):
                    zm = abs(float(f_xy(xm, ym)))
                max_corner = max(abs(z0), abs(z1), abs(z2), abs(z3))
                if not math.isfinite(zm) or zm > max_corner * 2.0 + 1.0:
                    continue
            except Exception:
                continue
            raw_segments.append((p_start, p_end))

    tol = min(x_max - x_min, y_max - y_min) / (grid_res * 50.0)
    return _stitch_segments(raw_segments, tol=max(tol, 1e-6))


def _sample_parametric_curve(
    x_expr: sp.Expr,
    y_expr: sp.Expr,
    param_sym: sp.Symbol,
    t_min: float,
    t_max: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    num_points: int = 500,
) -> list[list[tuple[float, float]]]:
    """Samples a 2D parametric curve (x(t), y(t)) over t in [t_min, t_max]."""
    fx = sp.lambdify(param_sym, x_expr, modules=["numpy", "math"])
    fy = sp.lambdify(param_sym, y_expr, modules=["numpy", "math"])

    x_span = max(x_max - x_min, 1e-3)
    y_span = max(y_max - y_min, 1e-3)
    x_clamp_min, x_clamp_max = x_min - x_span * 2.5, x_max + x_span * 2.5
    y_clamp_min, y_clamp_max = y_min - y_span * 2.5, y_max + y_span * 2.5

    ts = np.linspace(t_min, t_max, num_points)
    segments: list[list[tuple[float, float]]] = []
    curr_seg: list[tuple[float, float]] = []

    for t_val in ts:
        xv = _safe_eval_1d(fx, float(t_val))
        yv = _safe_eval_1d(fy, float(t_val))
        if (
            xv is None
            or yv is None
            or not (x_clamp_min <= xv <= x_clamp_max)
            or not (y_clamp_min <= yv <= y_clamp_max)
        ):
            if curr_seg:
                segments.append(curr_seg)
                curr_seg = []
            continue

        if curr_seg:
            px, py = curr_seg[-1]
            if abs(xv - px) > x_span * 0.6 or abs(yv - py) > y_span * 0.6:
                segments.append(curr_seg)
                curr_seg = [(xv, yv)]
                continue

        curr_seg.append((xv, yv))

    if curr_seg:
        segments.append(curr_seg)

    return segments


def render_function_plot_svg(spec: FunctionPlotSpec) -> str:
    """
    Renders a Korean exam/textbook style function graph into clean, high-precision vector SVG.
    Supports:
    - Explicit functions: y = f(x) and x = g(y) with adaptive subdivision & domain-edge bisection
    - Implicit curves: F(x, y) = 0 via 2D Marching Squares & polyline stitching
    - Parametric curves: (x(t), y(t))
    - Polar curves: r = f(theta)
    - Shaded integral/area regions, asymptotes, projection lines, and math typography labels
    """
    x_min, x_max = spec.x_range
    y_min, y_max = spec.y_range

    if x_max <= x_min:
        x_min, x_max = -4.0, 4.0
    if y_max <= y_min:
        y_min, y_max = -4.0, 4.0

    # SVG canvas dimensions (pt)
    width = 320.0
    pad_left = 25.0
    pad_right = 25.0
    pad_top = 25.0
    pad_bottom = 25.0
    plot_w = width - pad_left - pad_right

    if spec.equal_aspect:
        aspect = (y_max - y_min) / (x_max - x_min)
        plot_h = max(140.0, min(320.0, plot_w * aspect))
        height = plot_h + pad_top + pad_bottom
    else:
        height = 240.0
        plot_h = height - pad_top - pad_bottom

    def to_svg_x(x: float) -> float:
        return pad_left + (x - x_min) / (x_max - x_min) * plot_w

    def to_svg_y(y: float) -> float:
        return pad_top + (y_max - y) / (y_max - y_min) * plot_h

    origin_x = to_svg_x(0.0)
    origin_y = to_svg_y(0.0)

    axis_x = max(pad_left, min(width - pad_right, origin_x))
    axis_y = max(pad_top, min(height - pad_bottom, origin_y))

    elements: list[str] = []

    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{spec.width_cm}cm" height="{(spec.width_cm * height / width):.2f}cm" '
        f'style="font-family: \'New Computer Modern\', \'Times New Roman\', \'AppleMyungjo\', \'Noto Serif CJK KR\', \'Noto Serif KR\', \'Apple SD Gothic Neo\', serif;">'
    )
    elements.append(f"""
    <defs>
      <marker id="axis-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#111" />
      </marker>
      <clipPath id="plot-clip">
        <rect x="{pad_left:.1f}" y="{pad_top:.1f}" width="{plot_w:.1f}" height="{plot_h:.1f}" />
      </clipPath>
    </defs>
    """)

    elements.append('<g clip-path="url(#plot-clip)">')

    # 1. Shaded Areas (drawn underneath curves and axes)
    for area in spec.shaded_areas:
        a_min, a_max = area.x_range
        a_min = max(x_min, a_min)
        a_max = min(x_max, a_max)
        if a_max <= a_min:
            continue

        try:
            expr1 = _parse_single_expr(area.expr1)
            expr2 = _parse_single_expr(area.expr2)
            f1 = sp.lambdify(_X_SYM, expr1, modules=["numpy", "math"])
            f2 = sp.lambdify(_X_SYM, expr2, modules=["numpy", "math"])

            xs = np.linspace(a_min, a_max, 180)
            y1s = [_safe_eval_1d(f1, float(v)) for v in xs]
            y2s = [_safe_eval_1d(f2, float(v)) for v in xs]

            valid_pairs = [
                (float(x), y1, y2)
                for x, y1, y2 in zip(xs, y1s, y2s)
                if y1 is not None and y2 is not None
            ]
            if len(valid_pairs) >= 2:
                pts_top = [f"{to_svg_x(x):.1f},{to_svg_y(y1):.1f}" for x, y1, _ in valid_pairs]
                pts_bot = [f"{to_svg_x(x):.1f},{to_svg_y(y2):.1f}" for x, _, y2 in reversed(valid_pairs)]
                all_pts = pts_top + pts_bot
                elements.append(f'<polygon points="{" ".join(all_pts)}" fill="{escape(area.color)}" opacity="0.6" />')
        except Exception:
            pass

    # 2. Grid (Optional)
    if spec.show_grid:
        grid_lines = []
        for gx in range(math.floor(x_min), math.ceil(x_max) + 1):
            sx = to_svg_x(gx)
            grid_lines.append(f'<line x1="{sx:.1f}" y1="{pad_top}" x2="{sx:.1f}" y2="{height - pad_bottom}" stroke="#eee" stroke-width="0.8"/>')
        for gy in range(math.floor(y_min), math.ceil(y_max) + 1):
            sy = to_svg_y(gy)
            grid_lines.append(f'<line x1="{pad_left}" y1="{sy:.1f}" x2="{width - pad_right}" y2="{sy:.1f}" stroke="#eee" stroke-width="0.8"/>')
        elements.extend(grid_lines)

    # 3. Asymptotes
    for ax in spec.asymptotes_x:
        if x_min <= ax <= x_max:
            sx = to_svg_x(ax)
            elements.append(f'<line x1="{sx:.1f}" y1="{pad_top}" x2="{sx:.1f}" y2="{height - pad_bottom}" stroke="#777" stroke-width="1.0" stroke-dasharray="3,3"/>')
    for ay in spec.asymptotes_y:
        if y_min <= ay <= y_max:
            sy = to_svg_y(ay)
            elements.append(f'<line x1="{pad_left}" y1="{sy:.1f}" x2="{width - pad_right}" y2="{sy:.1f}" stroke="#777" stroke-width="1.0" stroke-dasharray="3,3"/>')

    # Helper to emit SVG path segments and compute smart curve label
    curve_labels: list[str] = []

    def _emit_curve_segments(
        segments: list[list[tuple[float, float]]],
        style: str,
        color: str,
        label: str | None,
    ) -> None:
        dash = ""
        if style == "dashed":
            dash = 'stroke-dasharray="4,3"'
        elif style == "dotted":
            dash = 'stroke-dasharray="1.5,2"'

        for seg in segments:
            if len(seg) < 2:
                continue
            d_cmds = [f"M {to_svg_x(seg[0][0]):.1f} {to_svg_y(seg[0][1]):.1f}"]
            for pt in seg[1:]:
                d_cmds.append(f"L {to_svg_x(pt[0]):.1f} {to_svg_y(pt[1]):.1f}")
            elements.append(
                f'<path d="{" ".join(d_cmds)}" fill="none" stroke="{escape(color)}" '
                f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" {dash}/>'
            )

        if label and segments:
            # Pick segment with the most visible points
            vis_segments = []
            for seg in segments:
                v = [
                    pt for pt in seg
                    if pad_left <= to_svg_x(pt[0]) <= width - pad_right
                    and pad_top <= to_svg_y(pt[1]) <= height - pad_bottom
                ]
                if v:
                    vis_segments.append(v)

            vis = vis_segments[-1] if vis_segments else segments[-1]
            if not vis:
                return

            idx = min(int(len(vis) * 0.82), len(vis) - 1)
            pt = vis[idx]
            sx = to_svg_x(pt[0])
            sy = to_svg_y(pt[1])

            p_prev = vis[max(0, idx - 4)]
            p_next = vis[min(len(vis) - 1, idx + 4)]
            dx = to_svg_x(p_next[0]) - to_svg_x(p_prev[0])
            dy = to_svg_y(p_next[1]) - to_svg_y(p_prev[1])
            dist = math.hypot(dx, dy)

            if dist > 1e-4:
                nx = -dy / dist
                ny = dx / dist
                if ny > 0:
                    nx, ny = -nx, -ny
            else:
                nx, ny = 0.0, -1.0

            offset = 13.0
            lx = sx + nx * offset
            ly = sy + ny * offset

            if lx > width - pad_right - 25:
                anchor = "end"
                lx = min(width - pad_right - 2, lx)
            elif lx < pad_left + 25:
                anchor = "start"
                lx = max(pad_left + 2, lx)
            else:
                anchor = "middle"

            ly = max(pad_top + 10, min(height - pad_bottom - 4, ly))

            formatted_label = format_svg_math_label(label)
            curve_labels.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="10" font-style="italic" '
                f'fill="{escape(color)}" stroke="white" stroke-width="2.5" '
                f'paint-order="stroke fill" text-anchor="{anchor}">{formatted_label}</text>'
            )

    # 4A. Functions (auto-detecting explicit_y, explicit_x, implicit, or polar!)
    for curve in spec.functions:
        try:
            kind, expr = _classify_and_parse_expr(curve.expr)
            if kind == "explicit_y":
                c_min = max(x_min, curve.domain[0]) if curve.domain else x_min
                c_max = min(x_max, curve.domain[1]) if curve.domain else x_max
                if c_max <= c_min:
                    continue
                fn = sp.lambdify(_X_SYM, expr, modules=["numpy", "math"])
                segments = _sample_explicit_1d(fn, c_min, c_max, y_min, y_max, swap_xy=False)
            elif kind == "explicit_x":
                c_min = max(y_min, curve.domain[0]) if curve.domain else y_min
                c_max = min(y_max, curve.domain[1]) if curve.domain else y_max
                if c_max <= c_min:
                    continue
                fn = sp.lambdify(_Y_SYM, expr, modules=["numpy", "math"])
                segments = _sample_explicit_1d(fn, c_min, c_max, x_min, x_max, swap_xy=True)
            elif kind == "polar":
                t_min = curve.domain[0] if curve.domain else 0.0
                t_max = curve.domain[1] if curve.domain else 2.0 * math.pi
                param_sym = _THETA_SYM if _THETA_SYM in expr.free_symbols else _T_SYM
                x_expr = expr * sp.cos(param_sym)
                y_expr = expr * sp.sin(param_sym)
                segments = _sample_parametric_curve(x_expr, y_expr, param_sym, t_min, t_max, x_min, x_max, y_min, y_max)
            else:  # implicit
                bx_min = max(x_min, curve.domain[0]) if curve.domain else x_min
                bx_max = min(x_max, curve.domain[1]) if curve.domain else x_max
                segments = _marching_squares_implicit(expr, bx_min, bx_max, y_min, y_max)

            _emit_curve_segments(segments, curve.style, curve.color, curve.label)
        except Exception:
            pass

    # 4B. Dedicated Implicit Curves (Marching Squares)
    for icurve in spec.implicit_curves:
        try:
            _, expr = _classify_and_parse_expr(icurve.expr)
            segments = _marching_squares_implicit(expr, x_min, x_max, y_min, y_max)
            _emit_curve_segments(segments, icurve.style, icurve.color, icurve.label)
        except Exception:
            pass

    # 4C. Dedicated Parametric Curves
    for pcurve in spec.parametric_curves:
        try:
            x_expr = _parse_single_expr(pcurve.x_expr)
            y_expr = _parse_single_expr(pcurve.y_expr)
            t_min = _eval_bound(pcurve.t_range[0])
            t_max = _eval_bound(pcurve.t_range[1])
            free = x_expr.free_symbols | y_expr.free_symbols
            param_sym = _THETA_SYM if (_THETA_SYM in free and _T_SYM not in free) else _T_SYM
            segments = _sample_parametric_curve(x_expr, y_expr, param_sym, t_min, t_max, x_min, x_max, y_min, y_max)
            _emit_curve_segments(segments, pcurve.style, pcurve.color, pcurve.label)
        except Exception:
            pass

    # 4D. Dedicated Polar Curves
    for polcurve in spec.polar_curves:
        try:
            r_expr = _parse_single_expr(polcurve.r_expr)
            t_min = _eval_bound(polcurve.theta_range[0])
            t_max = _eval_bound(polcurve.theta_range[1])
            free = r_expr.free_symbols
            param_sym = _T_SYM if (_T_SYM in free and _THETA_SYM not in free) else _THETA_SYM
            x_expr = r_expr * sp.cos(param_sym)
            y_expr = r_expr * sp.sin(param_sym)
            segments = _sample_parametric_curve(x_expr, y_expr, param_sym, t_min, t_max, x_min, x_max, y_min, y_max)
            _emit_curve_segments(segments, polcurve.style, polcurve.color, polcurve.label)
        except Exception:
            pass

    # End clipped group
    elements.append("</g>")

    # 5. Coordinate Axes (x-axis and y-axis, unclipped so arrowheads are sharp)
    elements.append(
        f'<line x1="{pad_left - 8:.1f}" y1="{axis_y:.1f}" x2="{width - pad_right + 12:.1f}" y2="{axis_y:.1f}" '
        f'stroke="#111" stroke-width="1.2" marker-end="url(#axis-arrow)" />'
    )
    elements.append(
        f'<line x1="{axis_x:.1f}" y1="{height - pad_bottom + 8:.1f}" x2="{axis_x:.1f}" y2="{pad_top - 12:.1f}" '
        f'stroke="#111" stroke-width="1.2" marker-end="url(#axis-arrow)" />'
    )

    # Axis Labels (x, y, O in math italics)
    elements.append(f'<text x="{width - pad_right + 14:.1f}" y="{axis_y + 4:.1f}" font-size="12" font-style="italic" fill="#111">x</text>')
    elements.append(f'<text x="{axis_x - 3:.1f}" y="{pad_top - 14:.1f}" font-size="12" font-style="italic" text-anchor="middle" fill="#111">y</text>')
    if x_min < 0 < x_max and y_min < 0 < y_max:
        elements.append(f'<text x="{axis_x - 6:.1f}" y="{axis_y + 12:.1f}" font-size="11" font-style="italic" text-anchor="end" fill="#111">O</text>')

    # 6. Curve Labels (rendered on top of curves and axes)
    elements.extend(curve_labels)

    # 7. Points, Projections, and Labels
    for pt in spec.points:
        px = to_svg_x(pt.x)
        py = to_svg_y(pt.y)

        # Projections to axes
        if pt.show_projection in ("x", "both"):
            elements.append(
                f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{axis_y:.1f}" '
                f'stroke="#555" stroke-width="0.9" stroke-dasharray="2,2" />'
            )
            raw_x_label = pt.x_tick_label or f"{pt.x:g}"
            x_label = format_svg_math_label(raw_x_label)
            if abs(pt.x) > 1e-4:  # Avoid colliding with origin O
                elements.append(
                    f'<text x="{px:.1f}" y="{axis_y + 12:.1f}" font-size="10" stroke="white" stroke-width="2.0" paint-order="stroke fill" text-anchor="middle" fill="#222">{x_label}</text>'
                )

        if pt.show_projection in ("y", "both"):
            elements.append(
                f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{axis_x:.1f}" y2="{py:.1f}" '
                f'stroke="#555" stroke-width="0.9" stroke-dasharray="2,2" />'
            )
            raw_y_label = pt.y_tick_label or f"{pt.y:g}"
            y_label = format_svg_math_label(raw_y_label)
            if abs(pt.y) > 1e-4:  # Avoid colliding with origin O
                elements.append(
                    f'<text x="{axis_x - 5:.1f}" y="{py + 3:.1f}" font-size="10" stroke="white" stroke-width="2.0" paint-order="stroke fill" text-anchor="end" fill="#222">{y_label}</text>'
                )

        # Point circle
        if pt.open_circle:
            elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.8" fill="#fff" stroke="#111" stroke-width="1.2" />')
        else:
            elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="#111" />')

        # Point Label
        if pt.label:
            offset_x, offset_y = 6.0, -6.0
            anchor = "start"
            if "left" in pt.label_pos:
                offset_x = -6.0
                anchor = "end"
            if "bottom" in pt.label_pos:
                offset_y = 12.0
            if pt.label_pos == "top":
                offset_x, offset_y, anchor = 0.0, -6.0, "middle"
            elif pt.label_pos == "bottom":
                offset_x, offset_y, anchor = 0.0, 12.0, "middle"

            formatted_pt_label = format_svg_math_label(pt.label)
            elements.append(
                f'<text x="{px + offset_x:.1f}" y="{py + offset_y:.1f}" font-size="10" '
                f'stroke="white" stroke-width="2.0" paint-order="stroke fill" '
                f'text-anchor="{anchor}" fill="#111">{formatted_pt_label}</text>'
            )

    # Caption if present
    if spec.caption:
        formatted_caption = format_svg_math_label(spec.caption)
        elements.append(
            f'<text x="{width / 2:.1f}" y="{height - 5:.1f}" font-size="9" text-anchor="middle" fill="#666">'
            f'{formatted_caption}</text>'
        )

    elements.append("</svg>")
    return "\n".join(elements)
