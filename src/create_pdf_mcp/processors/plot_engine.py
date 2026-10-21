import math
import numpy as np
import sympy as sp
from xml.sax.saxutils import escape
from ..models.figures import FunctionPlotSpec, FunctionCurve, PlotPoint, ShadedArea
from .math_text import format_svg_math_label


def render_function_plot_svg(spec: FunctionPlotSpec) -> str:
    """
    Renders a Korean exam/textbook style function graph into clean, high-precision vector SVG.
    Features:
    - Centered coordinate axes with arrowheads
    - Italic axis labels: x, y, and origin O
    - Mathematically evaluated curves (SymPy + NumPy) with discontinuity detection
    - Bounded canvas clipping so curves never bleed past axes into margins
    - Smart collision-free curve labels with crisp white outline
    - Shaded integral/area regions
    - Dashed projection lines and coordinate tick labels
    """
    # SVG canvas dimensions (pt)
    width = 320.0
    height = 240.0
    pad_left = 25.0
    pad_right = 25.0
    pad_top = 25.0
    pad_bottom = 25.0

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    x_min, x_max = spec.x_range
    y_min, y_max = spec.y_range

    if x_max <= x_min:
        x_min, x_max = -4.0, 4.0
    if y_max <= y_min:
        y_min, y_max = -4.0, 4.0

    def to_svg_x(x: float) -> float:
        return pad_left + (x - x_min) / (x_max - x_min) * plot_w

    def to_svg_y(y: float) -> float:
        return pad_top + (y_max - y) / (y_max - y_min) * plot_h

    # Clamping for calculation safety
    y_clamp_min = y_min - (y_max - y_min) * 2.0
    y_clamp_max = y_max + (y_max - y_min) * 2.0

    origin_x = to_svg_x(0.0)
    origin_y = to_svg_y(0.0)

    # Clamp origin position for visible axis drawing
    axis_x = max(pad_left, min(width - pad_right, origin_x))
    axis_y = max(pad_top, min(height - pad_bottom, origin_y))

    elements: list[str] = []

    # SVG Header and Definitions (Arrowheads, Fonts, and Plot Clip Path)
    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{spec.width_cm}cm" height="{(spec.width_cm * height / width):.2f}cm" '
        f'style="font-family: \'AppleMyungjo\', \'Apple SD Gothic Neo\', \'Noto Serif CJK KR\', \'Noto Serif KR\', \'New Computer Modern\', serif;">'
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

    # Elements clipped to the plot rectangle (shaded areas, grid, asymptotes, and curves)
    elements.append('<g clip-path="url(#plot-clip)">')

    # 1. Shaded Areas (drawn underneath curves and axes)
    for area in spec.shaded_areas:
        a_min, a_max = area.x_range
        a_min = max(x_min, a_min)
        a_max = min(x_max, a_max)
        if a_max <= a_min:
            continue

        try:
            x_sym = sp.Symbol("x")
            f1 = sp.lambdify(x_sym, sp.sympify(area.expr1), modules=["numpy", "math"])
            f2 = sp.lambdify(x_sym, sp.sympify(area.expr2), modules=["numpy", "math"])

            xs = np.linspace(a_min, a_max, 150)
            y1s = np.array([float(f1(val)) for val in xs])
            y2s = np.array([float(f2(val)) for val in xs])

            # Build polygon path
            pts_top = [f"{to_svg_x(x):.1f},{to_svg_y(y):.1f}" for x, y in zip(xs, y1s)]
            pts_bot = [f"{to_svg_x(x):.1f},{to_svg_y(y):.1f}" for x, y in reversed(list(zip(xs, y2s)))]
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

    # 4. Function Curves
    curve_labels: list[str] = []
    for curve in spec.functions:
        try:
            x_sym = sp.Symbol("x")
            expr = sp.sympify(curve.expr)
            f = sp.lambdify(x_sym, expr, modules=["numpy", "math"])

            c_min = max(x_min, curve.domain[0]) if curve.domain else x_min
            c_max = min(x_max, curve.domain[1]) if curve.domain else x_max
            if c_max <= c_min:
                continue

            num_points = 350
            xs = np.linspace(c_min, c_max, num_points)
            segments: list[list[tuple[float, float]]] = []
            curr_seg: list[tuple[float, float]] = []

            last_y = None
            for x_val in xs:
                try:
                    y_val = float(f(x_val))
                    if math.isnan(y_val) or math.isinf(y_val) or not (y_clamp_min <= y_val <= y_clamp_max):
                        if curr_seg:
                            segments.append(curr_seg)
                            curr_seg = []
                        last_y = None
                        continue

                    # Check for huge jumps (discontinuity like tan(x) or 1/x)
                    if last_y is not None and abs(y_val - last_y) > (y_max - y_min) * 0.7:
                        if curr_seg:
                            segments.append(curr_seg)
                            curr_seg = []

                    curr_seg.append((x_val, y_val))
                    last_y = y_val
                except Exception:
                    if curr_seg:
                        segments.append(curr_seg)
                        curr_seg = []
                    last_y = None

            if curr_seg:
                segments.append(curr_seg)

            dash = ""
            if curve.style == "dashed":
                dash = 'stroke-dasharray="4,3"'
            elif curve.style == "dotted":
                dash = 'stroke-dasharray="1.5,2"'

            for seg in segments:
                if len(seg) < 2:
                    continue
                d_cmds = [f"M {to_svg_x(seg[0][0]):.1f} {to_svg_y(seg[0][1]):.1f}"]
                for pt in seg[1:]:
                    d_cmds.append(f"L {to_svg_x(pt[0]):.1f} {to_svg_y(pt[1]):.1f}")
                elements.append(
                    f'<path d="{" ".join(d_cmds)}" fill="none" stroke="{escape(curve.color)}" '
                    f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" {dash}/>'
                )

            # Smart Curve Label Positioning (stored to render outside clip-path)
            if curve.label and segments:
                target_seg = segments[-1]
                vis = [
                    pt for pt in target_seg
                    if pad_left <= to_svg_x(pt[0]) <= width - pad_right
                    and pad_top <= to_svg_y(pt[1]) <= height - pad_bottom
                ]
                if not vis:
                    vis = target_seg

                idx = int(len(vis) * 0.82)
                idx = min(idx, len(vis) - 1)
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

                formatted_label = format_svg_math_label(curve.label)
                curve_labels.append(
                    f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="10" font-style="italic" '
                    f'fill="{escape(curve.color)}" stroke="white" stroke-width="2.5" '
                    f'paint-order="stroke fill" text-anchor="{anchor}">{formatted_label}</text>'
                )

        except Exception as e:
            # Fallback for complex expressions
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
