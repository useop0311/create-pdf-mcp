from ..models.figures import FigureSpec, FunctionPlotSpec, GeometryPhysicsSpec, RawSvgSpec
from .plot_engine import render_function_plot_svg
from .geo_phys_engine import render_geometry_physics_svg
from .svg_sanitizer import sanitize_raw_svg


def render_figure_to_svg(spec: FigureSpec) -> str:
    """
    Dispatcher that converts any FigureSpec into an SVG string.
    """
    if spec.type == "function_plot":
        return render_function_plot_svg(spec)
    elif spec.type == "geometry_physics":
        return render_geometry_physics_svg(spec)
    elif spec.type == "raw_svg":
        return sanitize_raw_svg(spec.svg_code, width_cm=spec.width_cm)
    else:
        raise ValueError(f"Unknown figure type: {getattr(spec, 'type', None)}")
