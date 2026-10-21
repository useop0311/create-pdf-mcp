from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field


class FunctionCurve(BaseModel):
    expr: str = Field(
        ...,
        description=(
            "수학 수식. 양함수(예: 'x**3 - 3*x + 1', '2*sin(pi*x)', 'sqrt(4 - x^2)'), "
            "음함수 방정식(예: 'x^2 + y^2 = 4', 'x^2/4 - y^2/9 = 1', 'x^3 + y^3 - 3*x*y = 0'), "
            "역함수(예: 'x = y^2 - 2*y'), 극방정식(예: 'r = 1 + cos(theta)') 모두 지원"
        ),
    )
    domain: tuple[float, float] | None = Field(None, description="개별 정의 구간 [x_min, x_max]")
    label: str | None = Field(None, description="곡선 라벨 (예: 'y=f(x)', 'x^2+y^2=4')")
    style: Literal["solid", "dashed", "dotted"] = "solid"
    color: str = "#111111"


class ImplicitCurve(BaseModel):
    expr: str = Field(
        ...,
        description="F(x, y) = 0 또는 '좌변 = 우변' 형태의 음함수 수식 (예: 'x^2 + y^2 = 4', 'x^2/9 + y^2/4 = 1', 'x^3 + y^3 - 3*x*y = 0')",
    )
    label: str | None = Field(None, description="음함수 곡선 라벨 (예: 'x^2+y^2=4')")
    style: Literal["solid", "dashed", "dotted"] = "solid"
    color: str = "#111111"


class ParametricCurve(BaseModel):
    x_expr: str = Field(..., description="매개변수 t에 대한 x(t) 수식 (예: '2*cos(t)', 't - sin(t)')")
    y_expr: str = Field(..., description="매개변수 t에 대한 y(t) 수식 (예: '2*sin(t)', '1 - cos(t)')")
    t_range: tuple[float | str, float | str] = Field(
        (0.0, 6.283185307179586),
        description="매개변수 t의 범위 [t_min, t_max] (예: (0, 6.2832) 또는 ('0', '2*pi'))",
    )
    label: str | None = Field(None, description="곡선 라벨")
    style: Literal["solid", "dashed", "dotted"] = "solid"
    color: str = "#111111"


class PolarCurve(BaseModel):
    r_expr: str = Field(..., description="극각 theta(또는 t)에 대한 r = f(theta) 수식 (예: '1 + cos(theta)', '2*sin(3*theta)')")
    theta_range: tuple[float | str, float | str] = Field(
        (0.0, 6.283185307179586),
        description="극각 theta의 범위 [theta_min, theta_max] (예: (0, 6.2832) 또는 ('0', '2*pi'))",
    )
    label: str | None = Field(None, description="곡선 라벨")
    style: Literal["solid", "dashed", "dotted"] = "solid"
    color: str = "#111111"


class PlotPoint(BaseModel):
    x: float
    y: float
    label: str | None = Field(None, description="점 라벨 (예: 'A', 'P(a, b)')")
    label_pos: Literal["top", "bottom", "left", "right", "top-right", "top-left", "bottom-right", "bottom-left"] = "top-right"
    show_projection: Literal["none", "x", "y", "both"] = Field(
        "none", description="x축/y축으로 내리는 수선의 발 점선 및 축 좌표 표시 여부"
    )
    x_tick_label: str | None = Field(None, description="x축 수선의 발 라벨 (예: 'a', '2')")
    y_tick_label: str | None = Field(None, description="y축 수선의 발 라벨 (예: 'f(a)', '3')")
    open_circle: bool = Field(False, description="불연속점 빈 동그라미 여부")


class ShadedArea(BaseModel):
    expr1: str = Field(..., description="위쪽(또는 첫 번째) 함수 수식 (예: 'x**2')")
    expr2: str = Field("0", description="아래쪽 함수 수식 (기본값 '0' 즉 x축)")
    x_range: tuple[float, float] = Field(..., description="적분/색칠 구간 [a, b]")
    color: str = "#d0d7de"


class FunctionPlotSpec(BaseModel):
    type: Literal["function_plot"] = "function_plot"
    x_range: tuple[float, float] = Field((-4.0, 4.0), description="x축 표시 범위")
    y_range: tuple[float, float] = Field((-4.0, 4.0), description="y축 표시 범위")
    functions: list[FunctionCurve] = Field(default_factory=list, description="양함수/음함수/극방정식 곡선 리스트")
    implicit_curves: list[ImplicitCurve] = Field(default_factory=list, description="음함수 F(x, y) = 0 곡선 리스트 (Marching Squares)")
    parametric_curves: list[ParametricCurve] = Field(default_factory=list, description="매개변수 (x(t), y(t)) 곡선 리스트")
    polar_curves: list[PolarCurve] = Field(default_factory=list, description="극좌표 r = f(theta) 곡선 리스트")
    points: list[PlotPoint] = Field(default_factory=list)
    shaded_areas: list[ShadedArea] = Field(default_factory=list)
    asymptotes_x: list[float] = Field(default_factory=list, description="수직 점근선 x=c 리스트")
    asymptotes_y: list[float] = Field(default_factory=list, description="수평 점근선 y=c 리스트")
    show_grid: bool = False
    equal_aspect: bool = Field(False, description="x축과 y축의 1:1 등비율(원/기하 왜곡 방지) 적용 여부")
    width_cm: float = 6.5
    caption: str | None = None


# 2. 선언형 기하 및 물리 도형
class GeoPoint(BaseModel):
    id: str = Field(..., description="점 식별자 (예: 'A', 'B', 'O')")
    x: float
    y: float
    label: str | None = Field(None, description="표시할 라벨 (미지정 시 id 사용, 빈 문자열이면 숨김)")
    label_pos: str = "auto"


class GeoSegment(BaseModel):
    p1: str
    p2: str
    style: Literal["solid", "dashed", "dotted"] = "solid"
    length_label: str | None = Field(None, description="선분 길이 표시 (예: '4', '2\\sqrt{3}')")
    tick_marks: int = Field(0, description="등변 표시 작대기 개수 (1, 2, 3)")


class GeoCircle(BaseModel):
    center: str
    radius: float
    arc_deg: tuple[float, float] | None = Field(None, description="호(Arc)만 그릴 경우 (시작각, 끝각)")
    style: Literal["solid", "dashed"] = "solid"
    fill: str | None = None


class GeoAngle(BaseModel):
    vertex: str = Field(..., description="각의 꼭짓점 ID")
    p1: str = Field(..., description="시작 반직선 위의 점 ID")
    p2: str = Field(..., description="끝 반직선 위의 점 ID")
    is_right_angle: bool = Field(False, description="직각(ㄱ자) 마커 표시 여부")
    label: str | None = Field(None, description="각도 라벨 (예: 'θ', '60°', 'π/3')")


class PhysicsObject(BaseModel):
    kind: Literal["block", "sphere", "incline", "wall_ground", "spring", "pulley", "vector_arrow"]
    pos: tuple[float, float] = Field(..., description="기준 좌표 (x, y)")
    end_pos: tuple[float, float] | None = Field(None, description="선형 요소(빗면, 용수철, 벡터 화살표, 벽면)의 끝점 (x2, y2)")
    size: tuple[float, float] = (1.0, 0.8)
    angle_deg: float = 0.0
    label: str | None = Field(None, description="질량/힘 라벨 (예: 'm', '2m', 'F', 'mg', 'v_0')")
    color: str = "#222222"


class GeometryPhysicsSpec(BaseModel):
    type: Literal["geometry_physics"] = "geometry_physics"
    points: list[GeoPoint] = Field(default_factory=list)
    segments: list[GeoSegment] = Field(default_factory=list)
    polygons: list[dict] = Field(default_factory=list, description="다각형 채우기 (예: {'points': ['A','B','C'], 'fill': '#f0f0f0'})")
    circles: list[GeoCircle] = Field(default_factory=list)
    angles: list[GeoAngle] = Field(default_factory=list)
    physics_objects: list[PhysicsObject] = Field(default_factory=list)
    width_cm: float = 6.5
    caption: str | None = None


# 3. 자유 형식 SVG
class RawSvgSpec(BaseModel):
    type: Literal["raw_svg"] = "raw_svg"
    svg_code: str = Field(..., description="<svg ...>...</svg> 전체 문자열")
    width_cm: float = 6.5
    caption: str | None = None


FigureSpec = Annotated[
    Union[FunctionPlotSpec, GeometryPhysicsSpec, RawSvgSpec],
    Field(discriminator="type"),
]
