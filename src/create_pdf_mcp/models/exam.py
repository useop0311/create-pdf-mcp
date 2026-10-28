from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from .figures import FigureSpec


class PassageGroup(BaseModel):
    problem_numbers: list[int] | None = Field(
        None,
        description="이 공통 지문에 연결된 문항 번호 리스트 (예: [1, 2, 3] 또는 [41, 42])",
    )
    start_number: int | None = Field(
        None,
        description="공통 지문이 시작되는 첫 문항 번호 (problem_numbers 미지정 시 사용, 예: 1)",
    )
    end_number: int | None = Field(
        None,
        description="공통 지문이 끝나는 마지막 문항 번호 (예: 3)",
    )
    header: str | None = Field(
        None,
        description="공통 지문 상단 안내문 (미지정 시 '[1~3] 다음 글을 읽고 물음에 답하시오.' 자동 생성)",
    )
    title: str | None = Field(
        None,
        description="지문 박스 내부 상단 제목 (있을 경우)",
    )
    passage: str | list[str] = Field(
        ...,
        description="공통 지문 본문 텍스트 (문자열 또는 단락별 리스트. 복합 지문 '(가)...', '(나)...', 밑줄 <u>...</u>, 빈칸 ______ 지원)",
    )
    source: str | None = Field(
        None,
        description="지문 하단 우측 출전/출처 표기 (예: '박지원, 「호질」', '정약용, 「목민심서」')",
    )
    footnotes: list[str] | str | None = Field(
        None,
        description="지문 하단 어휘 주석/각주 (예: ['* resilient: 회복력 있는', '** paradigm: 패러다임'])",
    )


class SubProblemItem(BaseModel):
    number: int | str | None = Field(
        None,
        description="새끼문제(소문항) 번호 또는 라벨 (예: 1, '(1)', '1)', '6-1', '(가)'). 미지정 시 '(1)', '(2)' 순으로 자동 부여",
    )
    points: int | None = Field(None, description="소문항 배점 (예: 2, 3 -> '[3점]'으로 표시)")
    topic_tag: str | None = Field(None, description="소문항 세부 유형 태그 (선택)")
    stem: str = Field(
        ...,
        description="소문항 문제 본문 (Markdown, 빈칸 표현 ____ 또는 [빈칸] 또는 (      ), 및 $...$, $$...$$ LaTeX 수식 지원)",
    )
    passage: str | list[str] | None = Field(
        None,
        description="소문항 전용 지문/제시문 박스 (빈칸 문장, 대화문, 제시문 등)",
    )
    conditions: list[str] = Field(
        default_factory=list,
        description="소문항 조건 박스 항목 리스트",
    )
    bogi: list[str] = Field(
        default_factory=list,
        description="소문항 <보기> 박스 항목 리스트",
    )
    bogi_title: str | None = Field(
        None,
        description="소문항 <보기> 박스 상단 제목 (기본값: '<보기>')",
    )
    given_box: str | list[str] | None = Field(
        None,
        description="소문항 주어진 글/문장 박스",
    )
    given_box_title: str | None = Field(
        None,
        description="소문항 주어진 글 상단 제목",
    )
    passage_title: str | None = Field(
        None,
        description="소문항 지문 제목",
    )
    passage_source: str | None = Field(
        None,
        description="소문항 지문 출처",
    )
    passage_footnotes: list[str] | str | None = Field(
        None,
        description="소문항 지문 어휘 풀이/각주",
    )
    figures: list[FigureSpec] = Field(default_factory=list, description="소문항에 포함할 그래프/도형 리스트")
    choices: list[str] = Field(
        default_factory=list,
        description="소문항 객관식 5지선다 리스트 (원문자 ①~⑤는 자동 부여됨. 비어있으면 주관식 소문항으로 처리)",
    )
    subjective_type: Literal["auto", "short_answer", "descriptive", "none"] = Field(
        "auto",
        description="소문항 주관식 문항 유형: 'auto'(choices 유무에 따라 자동 판별), 'short_answer'(단답형 숫자/수식 기입란), 'descriptive'(서술형 풀이 박스), 'none'(별도 답란 박스 없음)",
    )
    subjective_box_height: float | Literal["auto", "small", "medium", "large"] = Field(
        "auto",
        description="소문항 주관식 답안 박스 높이: 'auto'(단답형 1.1cm / 서술형 4.5cm), 'small'(3cm), 'medium'(5cm), 'large'(8cm), 또는 직접 cm 숫자 지정 (예: 4.0)",
    )
    subjective_label: str | None = Field(
        None,
        description="소문항 주관식 답안 박스 라벨 (예: '정답', '풀이 과정 및 정답')",
    )
    answer: str | None = Field(None, description="소문항 정답 (예: '③', '15', '$2\\pi$')")
    solution: str | None = Field(None, description="소문항 상세 풀이 및 해설 (Markdown + LaTeX 수식 지원)")
    solution_figures: list[FigureSpec] = Field(
        default_factory=list, description="소문항 해설지에만 들어갈 보조선 도형/그래프"
    )
    solving_space_cm: float | None = Field(
        None, description="소문항 하단 추가 풀이 여백 높이(cm). 미지정 시 기본값 사용"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if "number" not in data and "label" in data:
                data["number"] = data.pop("label")
            if "stem" not in data and "question" in data:
                data["stem"] = data.pop("question")
            for p_alias in ("box", "reading_passage", "text_box"):
                if "passage" not in data and p_alias in data:
                    data["passage"] = data.pop(p_alias)
        return data


class ProblemItem(BaseModel):
    number: int | str | None = Field(
        None,
        description="문항 번호 또는 라벨 (예: 1, 6, '6번', '[4~8번]'). 미지정 시 1부터 자동 부여",
    )
    points: int | None = Field(None, description="배점 (예: 2, 3, 4 -> '[3점]'으로 표시)")
    topic_tag: str | None = Field(
        None,
        description="단원/유형 태그 (예: '독서 - 인문/철학', '영어 - 빈칸 추론', '수학Ⅱ - 미분법')",
    )
    group_header: str | None = Field(
        None,
        description="문항군 공통 지시문 헤더 (예: '[4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오.', '[6~7] 다음 글을 읽고 물음에 답하시오.'). 연속된 문항에 동일한 값을 지정해도 첫 문항 상단에 한 번만 출력됨",
    )
    group_passage: str | list[str] | None = Field(
        None,
        description="문항군(예: [4~8번]) 전체가 공유하는 공통 지문/제시문 박스",
    )
    group_conditions: list[str] = Field(
        default_factory=list,
        description="문항군 전체가 공유하는 공통 조건 박스 항목 리스트",
    )
    group_bogi: list[str] = Field(
        default_factory=list,
        description="문항군 전체가 공유하는 공통 <보기> 박스 항목 리스트 (예: 빈칸에 들어갈 문장 후보군 또는 단어 풀)",
    )
    group_figures: list[FigureSpec] = Field(
        default_factory=list,
        description="문항군 전체가 공유하는 공통 그래프/도형 리스트",
    )
    stem: str = Field(
        ...,
        description="문제 본문/발문 (Markdown, <u>밑줄</u>, 빈칸 표현 ____ 또는 [빈칸] 또는 (      ), 및 $...$, $$...$$ LaTeX 수식 지원. 새끼문제 사용 시 '다음 물음에 답하시오.' 등 공통 발문 입력)",
    )
    passage: str | list[str] | None = Field(
        None,
        description="문항 지문 본문 (영어 독해 단독 지문, 국어 단독/공통 지문 등. 문자열 또는 단락 리스트 입력 가능)",
    )
    passage_title: str | None = Field(
        None,
        description="지문 상단 안내문 또는 지문 제목 (예: '[1~3] 다음 글을 읽고 물음에 답하시오.' 또는 지문 제목)",
    )
    passage_source: str | None = Field(
        None,
        description="지문 하단 우측 출전/출처 표기 (예: '윤동주, 「쉽게 씌어진 시」')",
    )
    passage_footnotes: list[str] | str | None = Field(
        None,
        description="지문 하단 어휘 주석/각주 (예: ['* ephemeral: 덧없는', '** ubiquitous: 어디에나 있는'])",
    )
    passage_position: Literal["auto", "after_stem", "before_stem"] = Field(
        "auto",
        description="지문 배치 위치: 'after_stem'(발문 아래에 배치 - 영어 단독 독해 문항 기본), 'before_stem'(문항 번호 위에 배치 - 국어/영어 세트 문항 기본), 'auto'(passage_range 유무에 따라 자동 판별)",
    )
    passage_range: str | None = Field(
        None,
        description="공통 지문(세트 문항)일 때 묶이는 문항 범위 또는 안내 헤더 (예: '1~3', '[41~42] 다음 글을 읽고, 물음에 답하시오.'). 지정 시 문항 위에 공통 지문으로 배치됨",
    )
    given_box: str | list[str] | None = Field(
        None,
        description="영어/국어 '주어진 글(문장 삽입 / 글의 순서 도입부)' 또는 <제시문> 박스 텍스트 (발문 아래, 본 지문 위에 별도 박스로 표시)",
    )
    given_box_title: str | None = Field(
        None,
        description="given_box 상단 라벨 (예: '주어진 글', '주어진 문장', '제시문'. 미지정 시 라벨 없는 박스)",
    )
    conditions: list[str] = Field(
        default_factory=list,
        description="조건 박스 항목 리스트 (예: ['(가) 함수 $f(x)$는 실수 전체에서 미분가능하다.', '(나) $f(1)=0$'])",
    )
    bogi: list[str] = Field(
        default_factory=list,
        description="<보기> 박스 항목 리스트 또는 단락 텍스트 (예: ['ㄱ. $f(0)=1$', 'ㄴ. $f^{\\prime}(1)>0$'] 또는 국어 <보기> 지문)",
    )
    bogi_title: str | None = Field(
        None,
        description="<보기> 박스의 커스텀 제목 (기본값: '<보 기>', 예: '<조 건>', '<자 료>')",
    )
    figures: list[FigureSpec] = Field(default_factory=list, description="문제에 포함할 그래프/도형 리스트")
    choices: list[str] = Field(
        default_factory=list,
        description="객관식 5지선다 리스트 (원문자 ①~⑤는 자동 부여됨. 비어있으면 주관식 문항 또는 새끼문제 보유 문항으로 처리)",
    )
    sub_problems: list[SubProblemItem] = Field(
        default_factory=list,
        description="새끼문제(소문항) 리스트 (예: '6. 물음에 답하시오.' 아래의 '(1) ...', '(2) ...' 소문항들)",
    )
    subjective_type: Literal["auto", "short_answer", "descriptive", "none"] = Field(
        "auto",
        description="주관식 문항 유형: 'auto'(choices 및 sub_problems 유무에 따라 자동 판별), 'short_answer'(단답형 숫자/수식/단어 기입란), 'descriptive'(서술형 풀이 박스), 'none'(별도 답란 박스 없음)",
    )
    subjective_box_height: float | Literal["auto", "small", "medium", "large"] = Field(
        "auto",
        description="주관식 답안 박스 높이: 'auto'(단답형 1.1cm / 서술형 4.5cm), 'small'(3cm), 'medium'(5cm), 'large'(8cm), 또는 직접 cm 숫자 지정 (예: 4.0)",
    )
    subjective_label: str | None = Field(
        None,
        description="주관식 답안 박스 라벨 (예: '정답', '풀이 및 정답', '[풀이 과정] / [답]')",
    )
    answer: str | None = Field(
        None,
        description="정답 (예: '③', '15', '$2\\pi$'). sub_problems가 있는 경우 생략 가능하며 각 소문항의 정답으로부터 자동 생성됨",
    )
    solution: str | None = Field(None, description="문항 상세 풀이 및 해설 (Markdown + LaTeX 수식 지원)")
    solution_figures: list[FigureSpec] = Field(
        default_factory=list, description="해설지에만 들어갈 보조선 도형/그래프"
    )
    solving_space_cm: float | None = Field(
        None, description="개별 문항 하단 추가 풀이 여백 높이(cm). 미지정 시 과목/지문 유무에 따라 자동 설정"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            for h_alias in ("instruction", "section_header", "header", "group_instruction"):
                if "group_header" not in data and h_alias in data:
                    data["group_header"] = data.pop(h_alias)
            for s_alias in ("sub_questions", "subproblems", "children"):
                if "sub_problems" not in data and s_alias in data:
                    data["sub_problems"] = data.pop(s_alias)
            for p_alias in ("box", "reading_passage", "text_box"):
                if "passage" not in data and p_alias in data:
                    data["passage"] = data.pop(p_alias)
            if "stem" not in data and "question" in data:
                data["stem"] = data.pop("question")
        return data

    @field_validator("conditions", "bogi", mode="before")
    @classmethod
    def _normalize_str_or_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            stripped = v.strip()
            return [stripped] if stripped else []
        return v


class ExamPDFRequest(BaseModel):
    title: str = Field(
        "수학 영역",
        description="시험지 메인 제목 (예: '2027학년도 대학수학능력시험 문제지', '국어 영역', '영어 영역', '수학 영역')",
    )
    subtitle: str | None = Field("제 2 교시", description="상단 교시/부제목 표시 (예: '제 1 교시', '제 2 교시', '제 3 교시')")
    subject_badge: str | None = Field(
        None,
        description="우측 상단 과목형/유형 배지 (예: '홀수형', '국어', '영어', '미적분', '물리학Ⅰ')",
    )
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
    font_style: Literal["serif", "sans"] = Field(
        "serif",
        description="글꼴 스타일: 'serif'(기본 한국어 수능 명조체), 'sans'(IBM Plex Sans KR 고딕체)",
    )
    problems_per_page: int | None = Field(
        None,
        description="exam_2col 모드에서 한 페이지 최대 문항 수 (선택 사항)",
    )
    pad_note_style: Literal["blank", "grid", "dotted", "lined", "split_2col"] = Field(
        "grid",
        description="pad_1p1q 모드일 때 하단 필기 영역의 배경 스타일",
    )
    answer_sheet_mode: Literal["append", "separate", "none"] = Field(
        "append",
        description="append: 같은 PDF 뒷부분에 빠른정답+해설 합본 / separate: 문제지·해설지 별도 PDF 2개 생성 / none: 문제지만 생성",
    )
    passage_groups: list[PassageGroup] = Field(
        default_factory=list,
        description="공통 지문(세트 문항, 예: 국어 [1~4], 영어 장문 [41~42]) 리스트. 개별 문항의 passage 및 passage_range 필드로도 지정 가능",
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
