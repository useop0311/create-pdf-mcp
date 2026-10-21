# CreatePDFMCP

> **Gemini 및 LLM이 출제한 수학·물리 문제를 iPad/태블릿 풀이에 최적화된 고품질 벡터 PDF로 조판하고 다운로드 링크 및 QR 코드를 반환하는 독자 컨테이너 MCP 서버**

---

## ✨ 핵심 기능

1. **Typst 기반 초고속 벡터 조판**
   - 0.05초 이내 컴파일 (TeX Live 불필요, 250MB 이하의 경량 컨테이너)
   - 표준 Markdown 및 LaTeX 수식(`$...$`, `$$...$$`) 자동 전처리
   - 한국어 수능 시험지 전용 폰트(Noto Serif CJK KR / Noto Sans CJK KR) 및 컴퓨터 모던 수식 폰트 탑재

2. **3계층 하이브리드 수식 그래프 & 다이어그램 엔진**
   - **`function_plot`**: SymPy + NumPy 기반 함수 수식 계산, 한국 교과서/수능 스타일($O, x, y$ 축, 화살표, 점선 가이드라인, 적분 색칠 구간) 벡터 SVG 생성
   - **`geometry_physics`**: 선언형 기하(직각 마커, 각도 호 $\theta$, 선분 길이, 외심/내심) 및 물리 역학(빗면, 물체 블록, 도르래, 용수철, 힘 벡터 화살표 $\vec{F}, mg$) SVG 생성
   - **`raw_svg`**: Gemini가 직접 생성한 자유 형식 SVG를 살균/정규화하여 삽입

3. **3가지 시험지 레이아웃 프리셋**
   - **`exam_2col`**: 수능/모의고사형 2단 칼럼 (상단 시험지 헤더, 중앙 세로선, 문제 분할 방지 및 하단 풀이 여백)
   - **`pad_1p1q`**: 패드 필기 특화 **1페이지 1문항** (상단 문제 + 하단 70% 필기 공간: 모눈/도트/줄노트/2분할/백지)
   - **`workbook`**: 일반 1단 워크북/학습지 레이아웃

4. **스마트 정답 및 해설지 시스템**
   - `append`: 같은 PDF 뒷부분에 빠른 정답표 + 상세 해설 합본 생성
   - `separate`: 문제지 PDF와 해설지 PDF 2개의 독립 파일 링크 분리 생성
   - `none`: 문제지만 생성

5. **유연한 듀얼 스토리지 지원**
   - **Cloudflare R2**: S3 호환 API를 통한 퍼블릭 도메인 또는 Presigned URL (무료 티어 10GB, 트래픽 비용 0원)
   - **컨테이너 자체 서빙**: `/files/{id}.pdf` 및 `/files/{id}_qr.png` 직접 호스팅 + 24시간 TTL 자동 삭제

---

## 🚀 빠른 시작

### 1. 로컬 환경 실행
```bash
# 가상환경 생성 및 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# 로컬 서버 실행 (FastAPI + FastMCP)
python -m create_pdf_mcp.server
```
서버가 기동되면 `http://localhost:8000/health`에서 상태를 확인하고, `http://localhost:8000/files/...`로 PDF를 다운로드할 수 있습니다.

### 2. Docker / Docker Compose 실행
```bash
# .env 설정 (Cloudflare R2 사용 시)
cp .env.example .env

# 컨테이너 빌드 및 백그라운드 실행
docker compose up -d --build
```

---

## 🔌 MCP 클라이언트 연결 설정

### A. 원격 Streamable HTTP 연결 (추천)
컨테이너를 서버에 띄운 경우:
```json
{
  "mcpServers": {
    "create-pdf": {
      "url": "http://your-server-ip:8000/mcp"
    }
  }
}
```

### B. 로컬 Stdio 연결
```json
{
  "mcpServers": {
    "create-pdf": {
      "command": "/path/to/CreatePDFMCP/.venv/bin/python",
      "args": ["-m", "create_pdf_mcp.server"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "STORAGE_MODE": "local",
        "PUBLIC_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

---

## 🛠️ MCP 도구 (Tools) 가이드

### 1. `create_exam_pdf`
시험지 생성 메인 도구입니다.

#### 요청 예시 (JSON)
```json
{
  "title": "2027학년도 대학수학능력시험 실전 모의평가",
  "subtitle": "제 2 교시",
  "subject_badge": "수학 및 물리학",
  "footer_text": "대구일과학고등학교 (제작: 송우섭)",
  "footer_note": "* 본 문제지의 저작권은 출제자에게 있습니다.",
  "layout_mode": "exam_2col",
  "answer_sheet_mode": "append",
  "problems": [
    {
      "number": 1,
      "points": 4,
      "topic_tag": "수학Ⅱ - 미적분",
      "stem": "함수 $f(x) = x^3 - 3x$의 그래프와 $x$축으로 둘러싸인 부분 중 $x \\ge 0$인 영역의 넓이를 $S$라 하자.",
      "conditions": [
        "(가) $f(0) = 0$, $f(\\sqrt{3}) = 0$",
        "(나) $x = 1$에서 극솟값 $-2$를 갖는다."
      ],
      "bogi": [
        "ㄱ. $f'(1) = 0$",
        "ㄴ. $S = \\frac{9}{4}$",
        "ㄷ. 방정식 $f(x)=0$의 실근은 3개이다."
      ],
      "figures": [
        {
          "type": "function_plot",
          "x_range": [-0.5, 2.5],
          "y_range": [-3.0, 3.0],
          "functions": [{ "expr": "x**3 - 3*x", "label": "y=f(x)" }],
          "points": [{ "x": 1.0, "y": -2.0, "label": "(1, -2)", "show_projection": "both" }],
          "shaded_areas": [{ "expr1": "x**3 - 3*x", "expr2": "0", "x_range": [0.0, 1.732] }]
        }
      ],
      "choices": ["ㄱ", "ㄱ, ㄴ", "ㄱ, ㄷ", "ㄴ, ㄷ", "ㄱ, ㄴ, ㄷ"],
      "answer": "⑤",
      "solution": "$\\int_0^{\\sqrt{3}} (3x - x^3) dx = \\frac{9}{4}$이다."
    },
    {
      "number": 2,
      "points": 4,
      "topic_tag": "기하 - 단답형",
      "stem": "그림과 같은 직각삼각형에서 $10 \\cos \\theta$의 값을 구하시오.",
      "choices": [],
      "subjective_type": "short_answer",
      "subjective_box_height": "auto",
      "answer": "8",
      "solution": "$\\cos \\theta = 4/5$이므로 답은 8이다."
    },
    {
      "number": 3,
      "points": 7,
      "topic_tag": "물리학Ⅰ - 서술형",
      "stem": "빗면 위 물체의 가속도 $a$를 구하는 풀이 과정과 답을 서술하시오.",
      "choices": [],
      "subjective_type": "descriptive",
      "subjective_box_height": "medium",
      "subjective_label": "풀이 과정 및 정답",
      "answer": "$a = g \\sin \\theta$",
      "solution": "알짜힘 $F = mg \\sin \\theta = ma$에 의해 $a = g \\sin \\theta$이다."
    }
  ]
}
```

#### 반환값 (JSON)
```json
{
  "pdf_url": "http://localhost:8000/files/c8973d9382bf_2027학년도_대학수학능력시험_실전_모의평가.pdf",
  "qr_code_url": "http://localhost:8000/files/c8973d9382bf_qr.png",
  "solution_pdf_url": null,
  "page_count": 2,
  "problem_count": 1,
  "layout_mode": "exam_2col",
  "summary_markdown": "### 📄 문제지 PDF 생성이 완료되었습니다! ..."
}
```

### 2. `preview_figure`
복잡한 수식 그래프나 물리 다이어그램을 시험지에 넣기 전 단독으로 렌더링 검증할 수 있는 도구입니다.

---

## 🧪 테스트 실행
```bash
.venv/bin/pytest -v
```
전체 16개 유닛/통합/E2E 테스트가 100% 통과합니다.

## 📄 라이선스
MIT License
