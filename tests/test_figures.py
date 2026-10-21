import pytest
from create_pdf_mcp.models.figures import (
    FunctionPlotSpec,
    FunctionCurve,
    ImplicitCurve,
    ParametricCurve,
    PolarCurve,
    PlotPoint,
    ShadedArea,
    GeometryPhysicsSpec,
    GeoPoint,
    GeoSegment,
    GeoAngle,
    PhysicsObject,
    RawSvgSpec,
)
from create_pdf_mcp.processors.figure_renderer import render_figure_to_svg


def test_function_plot_svg():
    spec = FunctionPlotSpec(
        x_range=(-3.0, 3.0),
        y_range=(-4.0, 4.0),
        functions=[
            FunctionCurve(expr="x**3 - 3*x", label="y=f(x)"),
            FunctionCurve(expr="x", style="dashed", color="#0066cc"),
        ],
        points=[
            PlotPoint(x=1.0, y=-2.0, label="P(1, -2)", show_projection="both"),
            PlotPoint(x=-1.0, y=2.0, label="Q(-1, 2)", open_circle=True),
        ],
        shaded_areas=[
            ShadedArea(expr1="x**3 - 3*x", expr2="0", x_range=(0.0, 1.732))
        ],
    )
    svg = render_figure_to_svg(spec)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "axis-arrow" in svg
    assert "y=f(x)" in svg
    assert "P(1, -2)" in svg
    assert 'clip-path="url(#plot-clip)"' in svg


def test_parabola_curve_evaluation_and_clipping():
    # Verify non-linear curve evaluation (avoiding y=x bug)
    spec = FunctionPlotSpec(
        x_range=(-1.0, 5.0),
        y_range=(-1.0, 5.0),
        functions=[
            FunctionCurve(expr="-x**2 + 4*x", label="y=-x^2+4x"),
            FunctionCurve(expr="x", label="y=x"),
        ],
        points=[
            PlotPoint(x=3.0, y=3.0, label="(3, 3)", show_projection="both"),
        ],
        shaded_areas=[
            ShadedArea(expr1="-x**2 + 4*x", expr2="x", x_range=(0.0, 3.0))
        ]
    )
    svg = render_figure_to_svg(spec)
    assert 'clipPath id="plot-clip"' in svg
    assert 'paint-order="stroke fill"' in svg

    # Extract path for -x**2 + 4*x
    import re
    paths = re.findall(r'<path d="([^"]+)" fill="none"[^>]*>', svg)
    assert len(paths) >= 2

    # Path 0 should be -x**2 + 4*x
    # Vertex is at x=2, y=4. At x=2, svg_x = 25 + (2 - (-1))/6 * 270 = 25 + 135 = 160.0
    # svg_y = 25 + (5 - 4)/6 * 190 = 25 + 31.67 = 56.7
    pts_str = paths[0].split()
    # Find points near svg_x=160
    found_vertex = False
    for i in range(1, len(pts_str) - 2, 3):
        x = float(pts_str[i])
        y = float(pts_str[i + 1])
        if abs(x - 160.0) < 2.0:
            assert abs(y - 56.7) < 3.0  # y must be near 4 (svg_y 56.7), NOT 160 (which was the y=x bug!)
            found_vertex = True
            break
    assert found_vertex, "Vertex of parabola at x=2, y=4 must be present with true mathematical y-coord"



def test_geometry_physics_svg():
    spec = GeometryPhysicsSpec(
        points=[
            GeoPoint(id="A", x=0.0, y=0.0),
            GeoPoint(id="B", x=4.0, y=0.0),
            GeoPoint(id="C", x=0.0, y=3.0),
        ],
        segments=[
            GeoSegment(p1="A", p2="B", length_label="4"),
            GeoSegment(p1="B", p2="C", length_label="5"),
            GeoSegment(p1="C", p2="A", length_label="3"),
        ],
        angles=[
            GeoAngle(vertex="A", p1="B", p2="C", is_right_angle=True),
            GeoAngle(vertex="B", p1="A", p2="C", label="θ"),
        ],
        physics_objects=[
            PhysicsObject(kind="block", pos=(2.0, 1.5), label="m"),
            PhysicsObject(kind="vector_arrow", pos=(2.0, 1.5), end_pos=(2.0, 0.5), label="mg"),
        ],
    )
    svg = render_figure_to_svg(spec)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "mg" in svg
    assert "θ" in svg


def test_raw_svg_sanitization():
    spec = RawSvgSpec(
        svg_code='<svg width="200" height="100"><script>alert(1)</script><circle cx="50" cy="50" r="30" fill="red"/></svg>'
    )
    svg = render_figure_to_svg(spec)
    assert "<script" not in svg
    assert "viewBox" in svg
    assert "<circle" in svg


def test_implicit_parametric_and_polar_curves():
    import re
    spec = FunctionPlotSpec(
        x_range=(-4.0, 4.0),
        y_range=(-4.0, 4.0),
        equal_aspect=True,
        functions=[
            # Auto-detected implicit equation inside FunctionCurve
            FunctionCurve(expr="x^2 + y^2 = 9", label="x^2+y^2=9"),
            # Auto-detected inverse explicit equation x = g(y)
            FunctionCurve(expr="x = y^2 - 2", label="x=y^2-2", style="dashed"),
        ],
        implicit_curves=[
            # Folium of Descartes via Marching Squares
            ImplicitCurve(expr="x^3 + y^3 - 3*x*y = 0", label="x^3+y^3=3xy", color="#b91c1c"),
        ],
        parametric_curves=[
            # Astroid curve
            ParametricCurve(
                x_expr="2*cos(t)^3",
                y_expr="2*sin(t)^3",
                t_range=("0", "2*pi"),
                label="Astroid",
                color="#1d4ed8",
            ),
        ],
        polar_curves=[
            # Cardioid curve
            PolarCurve(
                r_expr="1 + cos(theta)",
                theta_range=("0", "2*pi"),
                label="r=1+\\cos\\theta",
                color="#15803d",
            ),
        ],
    )
    svg = render_figure_to_svg(spec)
    paths = re.findall(r'<path d="([^"]+)" fill="none"[^>]*>', svg)
    # All 5 curves should produce non-empty vector paths
    assert len(paths) >= 5
    # Verify math label conversion (x^2 -> x², \theta -> θ)
    assert "x²+y²=9" in svg
    assert "x³+y³=3xy" in svg
    assert "r=1+cosθ" in svg or "θ" in svg


def test_domain_boundary_bisection_and_discontinuity():
    import re
    spec = FunctionPlotSpec(
        x_range=(-3.0, 3.0),
        y_range=(-3.0, 3.0),
        functions=[
            FunctionCurve(expr="sqrt(4 - x^2)", label="y=\\sqrt{4-x^2}"),
            FunctionCurve(expr="1 / (x - 1)", label="y=1/(x-1)", style="dashed"),
        ],
    )
    svg = render_figure_to_svg(spec)
    paths = re.findall(r'<path d="([^"]+)" fill="none"[^>]*>', svg)
    # Semicircle (1 path) + hyperbola 1/(x-1) (split into 2 disconnected branches across x=1)
    assert len(paths) == 3

