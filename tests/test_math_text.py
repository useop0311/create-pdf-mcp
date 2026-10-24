import pytest
from create_pdf_mcp.processors.math_text import latex_math_to_typst, markdown_to_typst
from create_pdf_mcp.typst_engine.compiler import compile_typst_to_pdf


def test_latex_fractions_and_roots():
    raw = r"\frac{x^2 + 1}{2x} + \sqrt{x} + \sqrt[3]{8}"
    typst_math = latex_math_to_typst(raw)
    assert "(x^2 + 1) / (2x)" in typst_math
    assert "sqrt(x)" in typst_math
    assert "root(3, 8)" in typst_math
    assert compile_typst_to_pdf(f"$ {typst_math} $")


def test_latex_greek_and_symbols():
    raw = r"\alpha + \beta + \theta \le \pi \neq \infty"
    typst_math = latex_math_to_typst(raw)
    assert "alpha" in typst_math
    assert "beta" in typst_math
    assert "theta" in typst_math
    assert "<=" in typst_math
    assert "!=" in typst_math
    assert "infinity" in typst_math
    assert compile_typst_to_pdf(f"$ {typst_math} $")


def test_latex_primes_and_integrals():
    raw = r"f'(x) + f^{\prime}(x) + \int_0^1 x dx"
    typst_math = latex_math_to_typst(raw)
    assert "f'(x)" in typst_math
    assert "integral" in typst_math
    assert compile_typst_to_pdf(f"$ {typst_math} $")


def test_displaystyle_and_limits_normalization():
    """Tests the resolution of the 'TypstError: unknown variable: displaystyleintegral' issue."""
    # 1. Without space between \displaystyle and \int
    t1 = latex_math_to_typst(r"\displaystyle\int_0^1 x dx")
    assert "displaystyle" not in t1
    assert "integral" in t1
    assert compile_typst_to_pdf(f"$ {t1} $")

    # 2. With space
    t2 = latex_math_to_typst(r"\displaystyle \int_0^1 x dx")
    assert "displaystyle" not in t2
    assert "integral" in t2
    assert compile_typst_to_pdf(f"$ {t2} $")

    # 3. Sum and lim with displaystyle
    t3 = latex_math_to_typst(r"\displaystyle\sum_{n=1}^\infty \frac{1}{n^2}")
    assert "displaystyle" not in t3
    assert "sum" in t3
    assert compile_typst_to_pdf(f"$ {t3} $")

    t4 = latex_math_to_typst(r"\displaystyle\lim_{x\to 0} \frac{\sin x}{x}")
    assert "displaystyle" not in t4
    assert "lim" in t4
    assert compile_typst_to_pdf(f"$ {t4} $")

    # 4. Limits modifier
    t5 = latex_math_to_typst(r"\int\limits_0^1 x dx + \lim\limits_{x\to 0} f(x) + \sum\limits_{k=1}^n k")
    assert "limits" not in t5
    assert compile_typst_to_pdf(f"$ {t5} $")


def test_advanced_delimiters_and_environments():
    # Matrices and cases
    mat_tex = r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}"
    res_mat = latex_math_to_typst(mat_tex)
    assert "mat(" in res_mat
    assert compile_typst_to_pdf(f"$ {res_mat} $")

    cases_tex = r"\begin{cases} x + 1 & x > 0 \\ -x & x \le 0 \end{cases}"
    res_cases = latex_math_to_typst(cases_tex)
    assert "cases(" in res_cases
    assert compile_typst_to_pdf(f"$ {res_cases} $")

    # Delimiters and norms
    delim_tex = r"\left| x \right| + \left\| \mathbf{v} \right\| + \left. \frac{df}{dx} \right|_{x=1}"
    res_delim = latex_math_to_typst(delim_tex)
    assert "left" not in res_delim
    assert compile_typst_to_pdf(f"$ {res_delim} $")


def test_markdown_with_math_and_korean_labels():
    text = (
        "다음 <그림 1>과 같이 함수 $f(x) = x^2$에 대하여 **다음**을 구하시오.\n"
        r"\[ \displaystyle\int_0^1 f(x) dx \]"
        "\n<보기>\nㄱ. $f'(1) = 2$\nㄴ. $\\varphi > 0$"
    )
    result = markdown_to_typst(text)
    assert "integral" in result
    assert "displaystyle" not in result
    assert "*다음*" in result
    assert r"\<그림 1>" in result
    assert compile_typst_to_pdf(f"[{result}]")


def test_blank_expressions_and_inline_subquestions():
    # 1. Plain-text blanks: underscores (even and odd counts), [빈칸], [빈칸: (가)], wide parens/brackets
    blank_text = (
        "[4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오.\n"
        "다음 문장의 빈칸 _____ 또는 ____ 에 들어갈 알맞은 표현과 "
        "[빈칸], [빈칸: (가)], (        ), [        ], (   나   )를 채우시오."
    )
    res_blank = markdown_to_typst(blank_text)
    assert "#box(" in res_blank
    assert "#h(" in res_blank
    assert compile_typst_to_pdf(f"[{res_blank}]")

    # 2. Math-mode blanks: \boxed, \underline{\hspace{2cm}}, \underline{\quad}, \phantom, ____
    math_blank = (
        r"f(x) = \boxed{\text{(가)}} + \boxed{\quad} + \underline{\hspace{2cm}} + \underline{\quad} + \phantom{x^2} + ____"
    )
    res_math_blank = latex_math_to_typst(math_blank)
    assert "#box(" in res_math_blank
    assert "#hide[" in res_math_blank
    assert compile_typst_to_pdf(f"$ {res_math_blank} $")

    # 3. Inline sub-questions "(1) ~~~ (2) ~~~" on a single line
    inline_sub = "6번. 물음에 답하시오. (1) 함수 $f(x)$의 도함수를 구하시오. (2) $f'(1)$의 값을 구하시오."
    res_sub = markdown_to_typst(inline_sub)
    assert "*(1)*" in res_sub
    assert "*(2)*" in res_sub
    assert compile_typst_to_pdf(f"[{res_sub}]")
