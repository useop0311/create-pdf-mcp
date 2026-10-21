import pytest
from create_pdf_mcp.models.figures import (
    FunctionPlotSpec,
    FunctionCurve,
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
