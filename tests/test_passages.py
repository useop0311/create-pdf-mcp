import pytest
from create_pdf_mcp.models.exam import ExamPDFRequest, PassageGroup, ProblemItem
from create_pdf_mcp.processors.math_text import markdown_to_typst
from create_pdf_mcp.server import create_exam_pdf
from create_pdf_mcp.typst_engine import (
    compile_typst_to_pdf,
    generate_typst_document,
    get_pdf_page_count,
)


def test_markdown_to_typst_underlines_blanks_footnotes_and_currency():
    """Verifies that underlines, blanks, footnote asterisks, URLs, and currency compile cleanly in Typst."""
    raw = (
        "Admission is $20 for adults and $10 for children (https://museum.example.org/info).\n"
        "In addition, <u>sustainable development</u> requires __________ in our daily lives.\n"
        "__밑줄 강조__ 텍스트와 수식 $f(x) = x^2$도 정상 작동한다.\n"
        "* resilient: 회복력 있는\n"
        "** paradigm: 패러다임"
    )
    typ = markdown_to_typst(raw)
    assert "#underline[sustainable development]" in typ
    assert "#underline[밑줄 강조]" in typ
    assert r"\$20" in typ
    assert r"\$10" in typ
    assert "#box(width:" in typ  # blank line generated from __________
    pdf_bytes = compile_typst_to_pdf(f"[{typ}]")
    assert pdf_bytes.startswith(b"%PDF-")


def test_korean_csat_exam_with_shared_passage_groups():
    """Tests Korean (국어 영역) CSAT exam with [1~3] composite reading passage, <u>underlines</u>, source, footnotes, and paragraph <보기>."""
    req = ExamPDFRequest(
        title="2027학년도 대학수학능력시험 모의평가 문제지",
        subtitle="제 1 교시",
        subject_badge="국어 영역 (홀수형)",
        footer_text="한국교육과정평가원 스타일 모의평가",
        footer_note="* 이 문제지에 관한 저작권은 출제자에게 있습니다.",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        passage_groups=[
            PassageGroup(
                problem_numbers=[1, 2, 3],
                header="[1~3] 다음 글을 읽고 물음에 답하시오.",
                title="독서(인문·철학) 복합 지문",
                passage=[
                    "**(가)** 조선 후기 실학자들은 성리학적 세계관의 한계를 극복하고 당대의 사회적 모순을 해결하기 위해 "
                    "㉠ <u>경세치용(經世致用)</u>과 이용후생(利用厚生)의 학문을 주창하였다. 이들은 공리공담에 치우친 당시의 학풍을 비판하며, "
                    "백성의 삶에 실질적인 도움이 되는 제도 개혁과 기술 수용을 강조하였다.\n"
                    "특히 북학파 지식인들은 청나라의 선진 문물을 적극적으로 수용할 것을 주장하며, 소비가 생산을 촉진한다는 경제관을 제시하였다. "
                    "이는 당시 지배층이 고수하던 절약 중심의 통념에 경종을 울리는 ㉡ <u>발상의 전환</u>이었다.",
                    "**(나)** 모든 인식은 경험에서 시작되지만, 경험 그 자체가 보편타당한 지식을 보장하는 것은 아니다. "
                    "칸트는 감성을 통해 받아들인 직관의 자료가 지성의 선험적 범주에 의해 종합될 때 비로소 객관적 인식이 성립한다고 보았다. "
                    "즉, [A] <u>‘내용 없는 사유는 공허하고, 개념 없는 직관은 맹목적이다’</u>라는 그의 명제는 경험론과 합리론의 대립을 "
                    "종합하려는 비판철학의 핵심을 잘 보여 준다.",
                ],
                source="박지원 외, 「북학의」 / 임마누엘 칸트, 「순수이성비판」 재구성",
                footnotes=[
                    "* 경세치용: 세상을 다스리고 실생활에 쓰임이 있게 함.",
                    "** 선험적: 경험에 앞서 인식의 주관적 조건으로 존재하는 것.",
                ],
            )
        ],
        problems=[
            ProblemItem(
                number=1,
                points=2,
                topic_tag="독서 - 내용 일치",
                stem="(가)와 (나)에 대한 이해로 가장 적절한 것은?",
                choices=[
                    "(가)의 북학파는 소비를 억제해야 생산력이 향상된다고 보았다.",
                    "(가)의 실학자들은 성리학적 명분론을 강화하는 데 주력하였다.",
                    "(나)의 칸트는 감성적 직관만으로도 보편적 지식이 성립한다고 보았다.",
                    "(나)의 칸트는 경험론과 합리론의 한계를 종합적으로 극복하고자 하였다.",
                    "(가)와 (나) 모두 전통적 권위를 절대적 진리의 기준으로 삼았다.",
                ],
                answer="④",
                solution="(나)에서 칸트는 감성의 직관과 지성의 범주가 결합해야 인식이 성립한다고 보아 경험론과 합리론을 종합하였다.",
            ),
            ProblemItem(
                number=2,
                points=3,
                topic_tag="독서 - 어휘 및 문맥 추론",
                stem="윗글의 ㉠, ㉡에 대한 설명으로 적절하지 <u>않은</u> 것은?",
                choices=[
                    "㉠은 공리공담에서 벗어나 현실 문제 해결을 중시하는 태도를 뜻한다.",
                    "㉡은 청의 문물을 배척하던 기존 통념에서 벗어난 관점을 의미한다.",
                    "㉠과 ㉡은 모두 당대 사회의 개선을 지향한다는 점에서 공통적이다.",
                    "㉠은 ㉡과 달리 백성의 삶과 무관한 형이상학적 탐구를 지향한다.",
                    "㉡은 유통과 소비의 활성화를 긍정적으로 바라본 경제관과 연결된다.",
                ],
                answer="④",
                solution="㉠(경세치용)은 백성의 삶에 실질적 도움이 되는 학문을 지향하므로 형이상학적 탐구만을 지향한다는 설명은 틀렸다.",
            ),
            ProblemItem(
                number=3,
                points=3,
                topic_tag="독서 - <보기> 적용",
                stem="[A]의 관점에서 <보기>의 ‘갑’에게 해 줄 수 있는 조언으로 가장 적절한 것은?",
                bogi=(
                    "갑은 수많은 역사적 사료와 통계 데이터만을 끝없이 수집하면 역사 발전의 보편 법칙이 저절로 드러날 것이라고 믿고, "
                    "이론적 개념이나 분석 틀을 세우는 일을 전혀 하지 않고 있다."
                ),
                choices=[
                    "감성적 직관의 자료를 수집하는 일을 즉시 중단해야 합니다.",
                    "개념적 분석 틀이 없는 단순한 자료 수집만으로는 체계적 인식에 도달할 수 없습니다.",
                    "경험적 자료 없이 순수한 사유만으로 역사 법칙을 연역해야 합니다.",
                    "선험적 범주를 버리고 개별 사료의 특수성에만 집중해야 합니다.",
                    "모든 이론적 개념은 경험적 관찰 이후에 자동으로 생성됨을 기억해야 합니다.",
                ],
                answer="②",
                solution="‘개념 없는 직관은 맹목적이다’라는 [A]의 명제에 따라, 분석 개념 없이 자료만 모으는 갑에게는 개념적 틀의 필요성을 조언해야 한다.",
            ),
        ],
    )

    for mode in ("exam_2col", "pad_1p1q", "workbook"):
        req.layout_mode = mode
        src = generate_typst_document(req)
        pdf_bytes = compile_typst_to_pdf(src)
        assert pdf_bytes.startswith(b"%PDF-")
        assert get_pdf_page_count(pdf_bytes) >= 1


@pytest.mark.asyncio
async def test_english_csat_exam_all_passage_types():
    """Tests English (영어 영역) exam with single passages, blank inference (______), sentence insertion (given_box), and [41~42] long passage set."""
    req = ExamPDFRequest(
        title="2027학년도 대학수학능력시험 문제지",
        subtitle="제 3 교시",
        subject_badge="영어 영역",
        footer_text="CreatePDFMCP English Test",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        problems=[
            # 1. 빈칸 추론 (Inline passage + blank line ______ + footnotes + currency)
            ProblemItem(
                number=31,
                points=2,
                topic_tag="영어 - 빈칸 추론",
                stem="다음 빈칸에 들어갈 말로 가장 적절한 것을 고르시오.",
                passage=(
                    "In modern behavioral economics, researchers have repeatedly found that consumers rarely make decisions "
                    "in a vacuum. When a store offers a basic subscription for $10 and a premium package for $25, adding a "
                    "decoy option priced at $24 can dramatically shift consumer preference toward the premium tier. "
                    "This phenomenon demonstrates that human judgment of value is fundamentally __________ rather than absolute."
                ),
                passage_footnotes=[
                    "* decoy: 미끼 상품",
                    "** vacuum: 진공, 고립된 상태",
                ],
                choices=[
                    "comparative",
                    "innate",
                    "permanent",
                    "random",
                    "independent",
                ],
                answer="①",
                solution="소비자는 절대적 기준이 아니라 주변 선택지($10, $24, $25)와의 비교를 통해 가치를 판단하므로 빈칸에는 comparative(비교적인)가 적절하다.",
            ),
            # 2. 문장 삽입 (given_box + main passage with ( ① ) ~ ( ⑤ ))
            ProblemItem(
                number=38,
                points=3,
                topic_tag="영어 - 문장 삽입",
                stem="글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?",
                given_box=(
                    "However, when those same algorithms are trained exclusively on historical data, they risk "
                    "amplifying existing social biases under the guise of objectivity."
                ),
                given_box_title="주어진 문장",
                passage=(
                    "Automated decision-making systems are increasingly deployed in hiring, lending, and healthcare. "
                    "( ① ) Proponents argue that algorithmic evaluations eliminate human fatigue and emotional prejudice. "
                    "( ② ) In many routine tasks, statistical models do outperform individual human judges in consistency. "
                    "( ③ ) This occurs because past records often reflect institutional inequalities rather than pure merit. "
                    "( ④ ) Consequently, engineers must actively audit training datasets before deploying models at scale. "
                    "( ⑤ ) Without such oversight, automation merely codifies past unfairness into future policy."
                ),
                passage_footnotes=["* guise: 외관, 구실  ** codify: 체계화하다"],
                choices=["①", "②", "③", "④", "⑤"],
                answer="③",
                solution="주어진 문장은 알고리즘이 과거 데이터로만 학습될 때 기존 편향을 증폭시킬 위험이 있다는 내용이며, ( ③ ) 뒤의 'This occurs because past records...'가 그 원인을 설명하므로 ③에 들어가야 한다.",
            ),
            # 3. 장문 독해 세트 [41~42] (passage_range on first problem of the set)
            ProblemItem(
                number=41,
                points=2,
                topic_tag="영어 - 장문 독해 (제목)",
                passage_range="[41~42] 다음 글을 읽고, 물음에 답하시오.",
                passage=[
                    "Throughout history, the architecture of libraries has reflected society's evolving relationship with knowledge. "
                    "In ancient times, scrolls were stored in restricted temple archives, accessible only to a small scribal elite. "
                    "Knowledge was treated as a (a) <u>scarce</u> treasure that required physical fortification to prevent loss.",
                    "With the invention of the printing press and the rise of public education, libraries transformed into civic "
                    "monuments. Grand reading rooms with high ceilings invited citizens to gather and read silently side by side. "
                    "Yet the core function remained centered on the (b) <u>preservation</u> of physical volumes. Today, as digital networks "
                    "make texts (c) <u>instantaneously</u> available on personal screens, the modern library is reinventing itself once more. "
                    "Rather than acting merely as a warehouse for books, it now serves as a collaborative community hub where people "
                    "(d) <u>isolate</u> themselves from civic life and engage in shared workshops, digital literacy training, and public dialogue. "
                    "Ultimately, the physical space of the library endures because human learning is inherently (e) <u>social</u>.",
                ],
                stem="윗글의 제목으로 가장 적절한 것은?",
                choices=[
                    "From Silent Vaults to Living Community Spaces: The Evolution of Libraries",
                    "Why Digital Books Will Completely Replace Physical Architecture",
                    "Ancient Scroll Preservation Techniques in Modern Museums",
                    "The Economic Cost of Maintaining Public Reading Rooms",
                    "How Printing Presses Ended the Era of Public Libraries",
                ],
                answer="①",
                solution="도서관이 고대의 폐쇄적 보관소에서 오늘날의 열린 공동체 학습 공간으로 진화해 왔음을 설명하는 글이므로 ①이 가장 적절하다.",
            ),
            ProblemItem(
                number=42,
                points=3,
                topic_tag="영어 - 장문 독해 (어휘)",
                stem="밑줄 친 (a)~(e) 중에서 문맥상 낱말의 쓰임이 적절하지 <u>않은</u> 것은?",
                choices=["(a)", "(b)", "(c)", "(d)", "(e)"],
                answer="④",
                solution="현대 도서관은 시민들이 모여 협업하고 소통하는 공간이므로 시민 생활로부터 스스로를 고립시킨다(isolate)는 (d)는 문맥상 부적절하다.",
            ),
        ],
    )

    resp = await create_exam_pdf(req)
    assert resp.pdf_url.endswith(".pdf")
    assert resp.problem_count == 4
    assert resp.page_count >= 1


def test_consecutive_identical_passages_deduplication():
    """Verifies that if an LLM repeats the exact same passage text on consecutive problems, it is deduplicated into a shared passage."""
    shared_text = (
        "이 글은 공통 지문 자동 병합 기능을 테스트하기 위한 국어 문학 지문입니다. "
        "연속된 두 문항에 동일한 지문이 입력되었을 때 시험지에는 한 번만 출력되어야 합니다."
    )
    req = ExamPDFRequest(
        title="국어 문학 테스트",
        subtitle="제 1 교시",
        layout_mode="exam_2col",
        problems=[
            ProblemItem(
                number=1,
                points=2,
                stem="윗글의 서술상 특징으로 가장 적절한 것은?",
                passage=shared_text,
                choices=["선택지 1", "선택지 2", "선택지 3", "선택지 4", "선택지 5"],
                answer="①",
            ),
            ProblemItem(
                number=2,
                points=3,
                stem="윗글의 주제로 가장 적절한 것은?",
                passage=shared_text,
                choices=["선택지 A", "선택지 B", "선택지 C", "선택지 D", "선택지 E"],
                answer="②",
            ),
        ],
    )
    src = generate_typst_document(req)
    assert "다음 글을 읽고 물음에 답하시오." in src
    assert "1" in src and "2" in src
    pdf_bytes = compile_typst_to_pdf(src)
    assert pdf_bytes.startswith(b"%PDF-")
