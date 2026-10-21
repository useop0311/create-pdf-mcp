from typing import Literal
from pydantic import BaseModel, Field
from .figures import FigureSpec


class ProblemItem(BaseModel):
    number: int | None = Field(None, description="문항 번호 (미지정 시 1부터 자동 부여)")
    points: int | None = Field(None, description="배점 (예: 2, 3, 4 -> '[4점]'으로 표시)")
    topic_tag: str | None = Field(None, description="단원/유형 태그 (예: '수학Ⅱ - 미분법', '물리학Ⅰ - 역학')")
    stem: str = Field(..., description="문제 본문 (Markdown 및 $...$, $$...$$ LaTeX 수식 지원)")
    conditions: list[str] = Field(
        default_factory=list,
        description="조건 박스 항목 리스트 (예: ['(가) 함수 $f(x)$는 실수 전체에서 미분가능하다.', '(나) $f(1)=0$'])",
    )
    bogi: list[str] = Field(
        default_factory=list,
        description="<보기> 박스 항목 리스트 (예: ['ㄱ. $f(0)=1$', 'ㄴ. $f^{\\prime}(1)>0$', 'ㄷ. 방정식 $f(x)=0$의 실근은 2개이다.'])",
    )
    figures: list[FigureSpec] = Field(default_factory=list, description="문제에 포함할 그래프/도형 리스트")
    choices: list[str] = Field(
        default_factory=list,
        description="객관식 5지선다 리스트 (원문자 ①~⑤는 자동 부여됨. 비어있으면 주관식 문항으로 처리)",
    )
    subjective_type: Literal["auto", "short_answer", "descriptive"] = Field(
        "auto",
        description="주관식 문항 유형: 'auto'(choices 유무에 따라 자동 판별), 'short_answer'(단답형 숫자/수식 기입란), 'descriptive'(서술형 풀이 박스)",
    )
    subjective_box_height: float | Literal["auto", "small", "medium", "large"] = Field(
        "auto",
        description="주관식 답안 박스 높이: 'auto'(단답형 1.1cm / 서술형 4.5cm), 'small'(3cm), 'medium'(5cm), 'large'(8cm), 또는 직접 cm 숫자 지정 (예: 4.0)",
    )
    subjective_label: str | None = Field(
        None,
        description="주관식 답안 박스 라벨 (예: '정답', '풀이 및 정답', '[풀이 과정] / [답]')",
    )
    answer: str = Field(..., description="정답 (예: '③', '15', '$2\\pi$')")
    solution: str | None = Field(None, description="문항 상세 풀이 및 해설 (Markdown + LaTeX 수식 지원)")
    solution_figures: list[FigureSpec] = Field(
        default_factory=list, description="해설지에만 들어갈 보조선 도형/그래프"
    )
    solving_space_cm: float | None = Field(
        None, description="개별 문항 하단 추가 풀이 여백 높이(cm). 미지정 시 레이아웃 기본값 사용"
    )


class ExamPDFRequest(BaseModel):
    title: str = Field("수학 영역", description="시험지 메인 제목 (예: '2027학년도 대학수학능력시험 모의평가 문제지', '물리학Ⅰ 실전 연습')")
    subtitle: str | None = Field("제 2 교시", description="상단 교시/부제목 표시")
    subject_badge: str | None = Field(None, description="우측 상단 과목형 배지 (예: '미적분', '물리학Ⅰ', '홀수형')")
    footer_text: str | None = Field(
        None,
        description="페이지 최하단 좌측에 들어갈 학교/기관명 또는 제작자 문구 (예: '대구일과학고등학교', '제작: 송우섭')",
    )
    footer_note: str | None = Field(
        None,
        description="페이지 최하단 우측에 들어갈 공통 조건/저작권 안내 문구 (예: '* 무단 전재 및 재배포 금지')",
    )
    layout_mode: Literal["exam_2col", "pad_1p1q", "workbook"] = Field(
        "exam_2col",
        description="exam_2col: 수능형 2단 칼럼 / pad_1p1q: 패드 필기용 1페이지 1문항 / workbook: 1단 다문항 학습지",
    )
    problems_per_page: int | None = Field(
        None,
        description="exam_2col 모드에서 한 페이지 최대 문항 수 (기본값 4: 칼럼당 2문항 배치 후 하단 여백 확보)",
    )
    pad_note_style: Literal["blank", "grid", "dotted", "lined", "split_2col"] = Field(
        "grid",
        description="pad_1p1q 모드일 때 하단 70% 필기 영역의 배경 스타일",
    )
    answer_sheet_mode: Literal["append", "separate", "none"] = Field(
        "append",
        description="append: 같은 PDF 뒷부분에 빠른정답+해설 합본 / separate: 문제지·해설지 별도 PDF 2개 생성 / none: 문제지만 생성",
    )
    problems: list[ProblemItem] = Field(..., min_length=1)


class ExamPDFResponse(BaseModel):
    pdf_url: str
    qr_code_url: str
    solution_pdf_url: str | None = None
    page_count: int
    problem_count: int
    layout_mode: str
    summary_markdown: str
