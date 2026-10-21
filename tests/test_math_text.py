import pytest
from create_pdf_mcp.processors.math_text import latex_math_to_typst, markdown_to_typst


def test_latex_fractions_and_roots():
    raw = r"\frac{x^2 + 1}{2x} + \sqrt{x} + \sqrt[3]{8}"
    typst_math = latex_math_to_typst(raw)
    assert "(x^2 + 1) / (2x)" in typst_math
    assert "sqrt(x)" in typst_math
    assert "root(3, 8)" in typst_math


def test_latex_greek_and_symbols():
    raw = r"\alpha + \beta + \theta \le \pi \neq \infty"
    typst_math = latex_math_to_typst(raw)
    assert "alpha" in typst_math
    assert "beta" in typst_math
    assert "theta" in typst_math
    assert "<=" in typst_math
    assert "!=" in typst_math
    assert "infinity" in typst_math


def test_latex_primes_and_integrals():
    raw = r"f'(x) + f^{\prime}(x) + \int_0^1 x dx"
    typst_math = latex_math_to_typst(raw)
    assert "f'(x)" in typst_math
    assert "integral" in typst_math


def test_markdown_with_math():
    text = "함수 $f(x) = x^2$에 대하여 **다음**을 구하시오.\n$$ \\int_0^1 f(x) dx $$"
    result = markdown_to_typst(text)
    assert "$f(x) = x^2$" in result
    assert "*다음*" in result
    assert "integral" in result
