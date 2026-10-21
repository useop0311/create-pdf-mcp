import math
from xml.sax.saxutils import escape
from ..models.figures import GeometryPhysicsSpec, GeoPoint, GeoSegment, GeoCircle, GeoAngle, PhysicsObject
from .math_text import format_svg_math_label


def render_geometry_physics_svg(spec: GeometryPhysicsSpec) -> str:
    """
    Renders declarative geometric figures and physics mechanics diagrams into clean vector SVG.
    """
    # 1. Collect all points to determine bounding box
    raw_points: dict[str, tuple[float, float]] = {}
    for p in spec.points:
        raw_points[p.id] = (p.x, p.y)

    # Include physics objects in bounding box estimation
    all_x = [p.x for p in spec.points]
    all_y = [p.y for p in spec.points]

    for po in spec.physics_objects:
        all_x.append(po.pos[0])
        all_y.append(po.pos[1])
        if po.end_pos:
            all_x.append(po.end_pos[0])
            all_y.append(po.end_pos[1])

    for c in spec.circles:
        if c.center in raw_points:
            cx, cy = raw_points[c.center]
            all_x.extend([cx - c.radius, cx + c.radius])
            all_y.extend([cy - c.radius, cy + c.radius])

    if not all_x:
        all_x = [-1.0, 5.0]
    if not all_y:
        all_y = [-1.0, 5.0]

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # Add margin
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    pad = max(span_x, span_y) * 0.15

    b_min_x, b_max_x = min_x - pad, max_x + pad
    b_min_y, b_max_y = min_y - pad, max_y + pad

    width = 300.0
    aspect = (b_max_y - b_min_y) / (b_max_x - b_min_x)
    height = max(160.0, min(360.0, width * aspect))

    def to_svg_x(x: float) -> float:
        return (x - b_min_x) / (b_max_x - b_min_x) * width

    def to_svg_y(y: float) -> float:
        # Mathematical Cartesian y (upwards) -> SVG y (downwards)
        return height - (y - b_min_y) / (b_max_y - b_min_y) * height

    # Scale factor for physical distances in SVG pixels
    px_scale = width / (b_max_x - b_min_x)

    elements: list[str] = []
    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{spec.width_cm}cm" height="{(spec.width_cm * height / width):.2f}cm" '
        f'style="font-family: \'AppleMyungjo\', \'Apple SD Gothic Neo\', \'Noto Serif CJK KR\', \'Noto Serif KR\', \'New Computer Modern\', serif;">'
    )
    elements.append("""
    <defs>
      <marker id="force-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#111" />
      </marker>
    </defs>
    """)

    # 2. Polygons (fill)
    for poly in spec.polygons:
        poly_pts = poly.get("points", [])
        fill = poly.get("fill", "#f3f4f6")
        stroke = poly.get("stroke", "none")
        if len(poly_pts) >= 3 and all(pid in raw_points for pid in poly_pts):
            svg_pts = [f"{to_svg_x(raw_points[pid][0]):.1f},{to_svg_y(raw_points[pid][1]):.1f}" for pid in poly_pts]
            elements.append(f'<polygon points="{" ".join(svg_pts)}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="1.2"/>')

    # 3. Circles and Arcs
    for c in spec.circles:
        if c.center in raw_points:
            cx, cy = raw_points[c.center]
            scx = to_svg_x(cx)
            scy = to_svg_y(cy)
            sr = c.radius * px_scale
            fill = c.fill or "none"
            dash = 'stroke-dasharray="3,3"' if c.style == "dashed" else ""

            if c.arc_deg:
                start_deg, end_deg = c.arc_deg
                # convert deg to rad
                r1 = math.radians(start_deg)
                r2 = math.radians(end_deg)
                x1 = scx + sr * math.cos(r1)
                y1 = scy - sr * math.sin(r1)
                x2 = scx + sr * math.cos(r2)
                y2 = scy - sr * math.sin(r2)
                large_arc = 1 if (end_deg - start_deg) % 360 > 180 else 0
                elements.append(f'<path d="M {x1:.1f} {y1:.1f} A {sr:.1f} {sr:.1f} 0 {large_arc} 0 {x2:.1f} {y2:.1f}" fill="{escape(fill)}" stroke="#111" stroke-width="1.2" {dash}/>')
            else:
                elements.append(f'<circle cx="{scx:.1f}" cy="{scy:.1f}" r="{sr:.1f}" fill="{escape(fill)}" stroke="#111" stroke-width="1.2" {dash}/>')

    # 4. Angles (Right-angle marker or Arc + Label)
    for ang in spec.angles:
        if ang.vertex in raw_points and ang.p1 in raw_points and ang.p2 in raw_points:
            vx, vy = raw_points[ang.vertex]
            p1x, p1y = raw_points[ang.p1]
            p2x, p2y = raw_points[ang.p2]

            v1x, v1y = p1x - vx, p1y - vy
            v2x, v2y = p2x - vx, p2y - vy
            len1 = math.hypot(v1x, v1y)
            len2 = math.hypot(v2x, v2y)

            if len1 > 1e-5 and len2 > 1e-5:
                u1x, u1y = v1x / len1, v1y / len1
                u2x, u2y = v2x / len2, v2y / len2

                if ang.is_right_angle:
                    # Right angle square marker (size ~ 10px in SVG)
                    sq_sz = 10.0 / px_scale
                    c1x, c1y = vx + u1x * sq_sz, vy + u1y * sq_sz
                    c2x, c2y = c1x + u2x * sq_sz, c1y + u2y * sq_sz
                    c3x, c3y = vx + u2x * sq_sz, vy + u2y * sq_sz

                    p_cmds = [
                        f"M {to_svg_x(c1x):.1f} {to_svg_y(c1y):.1f}",
                        f"L {to_svg_x(c2x):.1f} {to_svg_y(c2y):.1f}",
                        f"L {to_svg_x(c3x):.1f} {to_svg_y(c3y):.1f}",
                    ]
                    elements.append(f'<path d="{" ".join(p_cmds)}" fill="none" stroke="#222" stroke-width="1.0"/>')
                else:
                    # Circular angle arc
                    arc_r = 14.0 / px_scale
                    a1 = math.atan2(u1y, u1x)
                    a2 = math.atan2(u2y, u2x)
                    # normalize angle difference counterclockwise
                    diff = (a2 - a1) % (2 * math.pi)

                    arc_x1 = vx + arc_r * math.cos(a1)
                    arc_y1 = vy + arc_r * math.sin(a1)
                    arc_x2 = vx + arc_r * math.cos(a1 + diff)
                    arc_y2 = vy + arc_r * math.sin(a1 + diff)

                    s_ax1, s_ay1 = to_svg_x(arc_x1), to_svg_y(arc_y1)
                    s_ax2, s_ay2 = to_svg_x(arc_x2), to_svg_y(arc_y2)
                    large = 1 if diff > math.pi else 0

                    elements.append(
                        f'<path d="M {s_ax1:.1f} {s_ay1:.1f} A {14.0:.1f} {14.0:.1f} 0 {large} 0 {s_ax2:.1f} {s_ay2:.1f}" '
                        f'fill="none" stroke="#333" stroke-width="1.0"/>'
                    )

                    if ang.label:
                        mid_a = a1 + diff / 2.0
                        lbl_r = 22.0 / px_scale
                        lx = to_svg_x(vx + lbl_r * math.cos(mid_a))
                        ly = to_svg_y(vy + lbl_r * math.sin(mid_a))
                        elements.append(f'<text x="{lx:.1f}" y="{ly + 3:.1f}" font-size="10" font-style="italic" text-anchor="middle" fill="#111">{format_svg_math_label(ang.label)}</text>')

    # 5. Segments
    for seg in spec.segments:
        if seg.p1 in raw_points and seg.p2 in raw_points:
            p1 = raw_points[seg.p1]
            p2 = raw_points[seg.p2]
            sx1, sy1 = to_svg_x(p1[0]), to_svg_y(p1[1])
            sx2, sy2 = to_svg_x(p2[0]), to_svg_y(p2[1])

            dash = ""
            if seg.style == "dashed":
                dash = 'stroke-dasharray="4,3"'
            elif seg.style == "dotted":
                dash = 'stroke-dasharray="1.5,2"'

            elements.append(
                f'<line x1="{sx1:.1f}" y1="{sy1:.1f}" x2="{sx2:.1f}" y2="{sy2:.1f}" '
                f'stroke="#111" stroke-width="1.3" {dash}/>'
            )

            # Length Label if provided
            if seg.length_label:
                mx = (sx1 + sx2) / 2.0
                my = (sy1 + sy2) / 2.0
                # Normal vector for label offset
                dx = sx2 - sx1
                dy = sy2 - sy1
                l = math.hypot(dx, dy)
                if l > 1e-4:
                    nx = -dy / l * 10.0
                    ny = dx / l * 10.0
                    elements.append(
                        f'<text x="{mx + nx:.1f}" y="{my + ny + 3:.1f}" font-size="9" text-anchor="middle" fill="#333">{format_svg_math_label(seg.length_label)}</text>'
                    )

    # 6. Physics Objects
    for po in spec.physics_objects:
        pos_x, pos_y = po.pos
        spx, spy = to_svg_x(pos_x), to_svg_y(pos_y)

        if po.kind == "vector_arrow" and po.end_pos:
            epx, epy = to_svg_x(po.end_pos[0]), to_svg_y(po.end_pos[1])
            elements.append(
                f'<line x1="{spx:.1f}" y1="{spy:.1f}" x2="{epx:.1f}" y2="{epy:.1f}" '
                f'stroke="{escape(po.color)}" stroke-width="1.8" marker-end="url(#force-arrow)"/>'
            )
            if po.label:
                lx = (spx + epx) / 2.0
                ly = (spy + epy) / 2.0 - 5.0
                elements.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="10" font-weight="bold" font-style="italic" fill="{escape(po.color)}">{format_svg_math_label(po.label)}</text>')

        elif po.kind == "block":
            bw = po.size[0] * px_scale
            bh = po.size[1] * px_scale
            # Rotated rectangle centered at pos
            rad = math.radians(po.angle_deg)
            elements.append(
                f'<g transform="translate({spx:.1f}, {spy:.1f}) rotate({-po.angle_deg})">'
                f'<rect x="{-bw / 2:.1f}" y="{-bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                f'fill="#fff" stroke="{escape(po.color)}" stroke-width="1.5"/>'
            )
            if po.label:
                elements.append(f'<text x="0" y="3" font-size="10" text-anchor="middle" fill="#111">{format_svg_math_label(po.label)}</text>')
            elements.append('</g>')

        elif po.kind == "sphere":
            r = po.size[0] * px_scale / 2.0
            elements.append(
                f'<circle cx="{spx:.1f}" cy="{spy:.1f}" r="{r:.1f}" fill="#fff" stroke="{escape(po.color)}" stroke-width="1.4"/>'
            )
            if po.label:
                elements.append(f'<text x="{spx:.1f}" y="{spy + 3:.1f}" font-size="10" text-anchor="middle" fill="#111">{format_svg_math_label(po.label)}</text>')

        elif po.kind == "incline" and po.end_pos:
            epx, epy = to_svg_x(po.end_pos[0]), to_svg_y(po.end_pos[1])
            # Draw triangle from (spx, spy) to (epx, spy) to (epx, epy)
            tri_pts = f"{spx:.1f},{spy:.1f} {epx:.1f},{spy:.1f} {epx:.1f},{epy:.1f}"
            elements.append(f'<polygon points="{tri_pts}" fill="#f9fafb" stroke="#111" stroke-width="1.5"/>')
            # Hatching on bottom base
            for hx in range(int(min(spx, epx)), int(max(spx, epx)), 8):
                elements.append(f'<line x1="{hx}" y1="{spy}" x2="{hx - 5}" y2="{spy + 6}" stroke="#777" stroke-width="0.8"/>')

        elif po.kind == "spring" and po.end_pos:
            epx, epy = to_svg_x(po.end_pos[0]), to_svg_y(po.end_pos[1])
            dx, dy = epx - spx, epy - spy
            length = math.hypot(dx, dy)
            if length > 5:
                # Zig-zag coil
                coils = max(6, int(length / 8))
                coil_pts = [f"{spx:.1f},{spy:.1f}"]
                for i in range(1, coils):
                    t = i / coils
                    cx = spx + dx * t
                    cy = spy + dy * t
                    # perpendicular offset
                    side = 6.0 if (i % 2 == 1) else -6.0
                    nx = -dy / length * side
                    ny = dx / length * side
                    coil_pts.append(f"{cx + nx:.1f},{cy + ny:.1f}")
                coil_pts.append(f"{epx:.1f},{epy:.1f}")
                elements.append(f'<polyline points="{" ".join(coil_pts)}" fill="none" stroke="#222" stroke-width="1.2"/>')

        elif po.kind == "pulley":
            r = 10.0
            elements.append(f'<circle cx="{spx:.1f}" cy="{spy:.1f}" r="{r:.1f}" fill="#fff" stroke="#111" stroke-width="1.4"/>')
            elements.append(f'<circle cx="{spx:.1f}" cy="{spy:.1f}" r="2.5" fill="#111"/>')

        elif po.kind == "wall_ground" and po.end_pos:
            epx, epy = to_svg_x(po.end_pos[0]), to_svg_y(po.end_pos[1])
            elements.append(f'<line x1="{spx:.1f}" y1="{spy:.1f}" x2="{epx:.1f}" y2="{epy:.1f}" stroke="#111" stroke-width="1.5"/>')
            # Hatch lines
            dx, dy = epx - spx, epy - spy
            l = math.hypot(dx, dy)
            if l > 5:
                steps = int(l / 6)
                for i in range(steps + 1):
                    t = i / max(1, steps)
                    hx = spx + dx * t
                    hy = spy + dy * t
                    elements.append(f'<line x1="{hx:.1f}" y1="{hy:.1f}" x2="{hx - 4:.1f}" y2="{hy + 5:.1f}" stroke="#666" stroke-width="0.8"/>')

    # 7. Points and Point Labels
    for pt in spec.points:
        px = to_svg_x(pt.x)
        py = to_svg_y(pt.y)
        elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.0" fill="#111"/>')

        label = pt.label if pt.label is not None else pt.id
        if label:
            # Automatic label offset
            ox, oy = 5.0, -5.0
            anchor = "start"
            if pt.label_pos == "top":
                ox, oy, anchor = 0.0, -6.0, "middle"
            elif pt.label_pos == "bottom":
                ox, oy, anchor = 0.0, 12.0, "middle"
            elif pt.label_pos == "left":
                ox, oy, anchor = -6.0, 3.0, "end"
            elif pt.label_pos == "right":
                ox, oy, anchor = 6.0, 3.0, "start"
            elif pt.label_pos == "auto":
                # Compute vector from centroid
                c_x = sum(all_x) / len(all_x)
                c_y = sum(all_y) / len(all_y)
                sc_x, sc_y = to_svg_x(c_x), to_svg_y(c_y)
                dir_x = px - sc_x
                dir_y = py - sc_y
                d_len = math.hypot(dir_x, dir_y)
                if d_len > 1e-4:
                    ox = dir_x / d_len * 9.0
                    oy = dir_y / d_len * 9.0
                    anchor = "end" if ox < -2 else ("start" if ox > 2 else "middle")
                    oy += 3.0

            elements.append(
                f'<text x="{px + ox:.1f}" y="{py + oy:.1f}" font-size="10.5" font-style="italic" '
                f'text-anchor="{anchor}" fill="#111">{format_svg_math_label(label)}</text>'
            )

    # Caption if present
    if spec.caption:
        elements.append(
            f'<text x="{width / 2:.1f}" y="{height - 4:.1f}" font-size="9" text-anchor="middle" fill="#666">'
            f'{format_svg_math_label(spec.caption)}</text>'
        )

    elements.append("</svg>")
    return "\n".join(elements)
