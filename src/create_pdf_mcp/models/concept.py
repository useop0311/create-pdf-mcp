from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from .figures import FigureSpec


class CalloutBox(BaseModel):
    type: Literal[
        "concept",
        "definition",
        "formula",
        "tip",
        "warning",
        "example",
        "passage",
        "grammar",
        "summary",
        "note",
    ] = Field("concept", description="콜아웃 박스 종류")
    title: str | None = Field(None, description="박스 상단 제목")
    content: str | list[str] = Field(..., description="박스 내부 마크다운 본문")
    figures: list[FigureSpec] = Field(default_factory=list, description="박스 내 도형/그래프")

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            for b_alias in ("body", "text"):
                if "content" not in data and b_alias in data:
                    data["content"] = data.pop(b_alias)
        return data


class ConceptExampleItem(BaseModel):
    label: str | None = Field(None, description="예제 라벨 (예: '예제 1', '개념 확인 1')")
    points: int | None = Field(None, description="배점 표시 (선택)")
    topic_tag: str | None = Field(None, description="세부 개념 태그 (선택)")
    stem: str = Field(..., description="예제 발문/문제 본문")
    passage: str | list[str] | None = Field(None, description="예제용 짧은 지문/제시문")
    conditions: list[str] = Field(default_factory=list, description="조건 박스 항목")
    bogi: list[str] = Field(default_factory=list, description="<보기> 박스 항목")
    figures: list[FigureSpec] = Field(default_factory=list, description="예제에 포함할 도형/그래프")
    choices: list[str] = Field(default_factory=list, description="객관식 선지 리스트")
    answer: str | None = Field(None, description="예제 정답")
    solution: str | None = Field(None, description="예제 상세 풀이/해설")
    solution_figures: list[FigureSpec] = Field(default_factory=list, description="예제 해설용 도형/그래프")


class ConceptSection(BaseModel):
    badge: str | None = Field(None, description="단원 배지 (예: 'CHAPTER 01', '개념 01')")
    title: str = Field(..., description="단원/섹션 제목 (예: '미분계수와 도함수')")
    subtitle: str | None = Field(None, description="단원 부제목 또는 핵심 요약")
    learning_objectives: list[str] = Field(default_factory=list, description="단원 상단 학습 목표 리스트")
    markdown: str | list[str] | None = Field(
        None,
        description="섹션 본문 마크다운 (수식, 표, 리스트, 콜아웃, 형광펜, 도형 위치 지정 지원)",
    )
    sidebar_notes: list[str] = Field(
        default_factory=list,
        description="sidebar_note 레이아웃용 좌측 보조단 핵심 키워드/암기 팁/용어 해설",
    )
    callouts: list[CalloutBox] = Field(default_factory=list, description="구조화 콜아웃 박스 리스트")
    figures: list[FigureSpec] = Field(
        default_factory=list,
        description="섹션에 포함할 수식 그래프/도형 리스트",
    )
    examples: list[ConceptExampleItem] = Field(
        default_factory=list,
        description="개념 설명 직후 배치할 선택적 예제/확인 문제",
    )
    page_break_before: bool = Field(False, description="이 섹션 시작 전 강제 페이지 넘김 여부")
    keep_together: Literal["auto", "always", "never"] = Field(
        "auto",
        description="이 섹션이 페이지 경계에서 중간에 잘리지 않도록 묶음 유지할지 여부 ('auto': 1페이지 이내 분량이면 한 덩어리로 유지하여 공간 부족 시 다음 페이지 상단으로 이동)",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            for b_alias in ("content", "body", "text"):
                if "markdown" not in data and b_alias in data:
                    data["markdown"] = data.pop(b_alias)
        return data


class ConceptPDFRequest(BaseModel):
    title: str = Field(..., description="개념서 메인 제목")
    subtitle: str | None = Field(None, description="부제목/과정명")
    subject_badge: str | None = Field(None, description="과목/영역 배지")
    footer_text: str | None = Field(None, description="하단 좌측 기관명/제작자 문구")
    footer_note: str | None = Field(None, description="하단 우측 안내/저작권 문구")
    layout_mode: Literal["concept_book", "sidebar_note", "summary_2col"] = Field(
        "concept_book",
        description="concept_book: 1단 정석 단행본형 / sidebar_note: 보조단(코넬식) 인강교재형 / summary_2col: 2단 요약노트형",
    )
    color_theme: Literal["blue", "emerald", "amber", "purple", "mono"] = Field(
        "blue",
        description="개념서 포인트 컬러 테마 (blue, emerald, amber, purple, mono)",
    )
    font_style: Literal["sans", "serif"] = Field(
        "sans",
        description="본문 글꼴 스타일: 'sans'(IBM Plex Sans KR 기본), 'serif'(명조체)",
    )
    show_toc: bool = Field(False, description="단원 목차(Table of Contents) 자동 생성 여부")
    page_fit_mode: Literal["smart", "section_per_page", "compact_fit", "continuous"] = Field(
        "smart",
        description=(
            "페이지 맞춤 및 넘김 제어 모드: "
            "'smart'(기본값 - 단원/콜아웃/표/소제목 중간 잘림 방지 + 미세 넘침 시 자동 여백 피팅), "
            "'section_per_page'(각 단원을 무조건 새 페이지에서 시작), "
            "'compact_fit'(컴팩트 여백/크기로 페이지 수 최소화), "
            "'continuous'(분할 제약 없이 연속 흐름)"
        ),
    )
    example_solution_mode: Literal["inline", "append", "none"] = Field(
        "inline",
        description="예제 풀이 표시 방식: 'inline'(예제 아래 바로 표시), 'append'(마지막에 모아서 표시), 'none'(숨김)",
    )
    markdown: str | None = Field(
        None,
        description="통 마크다운 원고 (입력 시 #/## 기준으로 섹션 자동 분리 지원)",
    )
    figures: list[FigureSpec] = Field(
        default_factory=list,
        description="통 마크다운에서 {{fig:0}} 등으로 참조할 전역 도형 리스트",
    )
    sections: list[ConceptSection] = Field(
        default_factory=list,
        description="단원별 구조화된 개념 섹션 리스트",
    )


class ConceptPDFResponse(BaseModel):
    pdf_url: str
    qr_code_url: str
    page_count: int
    section_count: int
    layout_mode: str
    color_theme: str
    summary_markdown: str
