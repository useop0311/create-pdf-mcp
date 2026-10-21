import re


KNOWN_TYPST_MATH = {
    # Trigonometry and hyperbolic
    "sin", "cos", "tan", "sec", "csc", "cot", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh",
    # Logarithms and exponentials
    "ln", "log", "exp",
    # Calculus and algebra
    "lim", "min", "max", "inf", "sup", "det", "gcd", "lcm", "dim", "ker", "hom",
    "dif", "integral", "sum", "product", "root", "sqrt", "frac",
    "overline", "underline", "arrow", "hat", "dot",
    # Symbols and units
    "degree", "infinity", "plus", "minus", "times", "parallel", "approx", "tilde",
    "acute", "arc", "scripts", "triangle", "square", "angle",
    # Greek letters
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    "Delta", "Gamma", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega",
}


def _split_unknown_math_identifiers(text: str) -> str:
    """
    In Typst math mode, multi-character sequences like 'mg', 'ma', 'AB' are treated
    as undefined variables rather than product of symbols.
    This splits unknown multi-character variable clusters (e.g. 'mg' -> 'm g', 'dx' -> 'dif x').
    """
    def repl(m: re.Match) -> str:
        word = m.group(0)
        if word in KNOWN_TYPST_MATH:
            return word
        if word.startswith("d") and len(word) == 2 and word[1] in "xyztsuvw":
            return f"dif {word[1]}"
        return " ".join(word)

    # Do not split inside quoted strings (e.g. "text")
    parts = re.split(r'("[^"]*")', text)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"\b[a-zA-Z]{2,}\b", repl, parts[i])
    return "".join(parts)


def _format_overline(match: re.Match) -> str:
    content = match.group(1).strip()
    if content.isupper() and len(content) > 1:
        return f"overline({' '.join(content)})"
    return f"overline({content})"


def _format_underline(match: re.Match) -> str:
    content = match.group(1).strip()
    if content.isupper() and len(content) > 1:
        return f"underline({' '.join(content)})"
    return f"underline({content})"


def latex_math_to_typst(math_str: str) -> str:
    """
    Convert common LaTeX math commands to native Typst math syntax.
    Enables native, fast, offline Typst compilation while allowing Gemini to write LaTeX.
    """
    s = math_str.strip()

    # Normalize primes: f'(x) or f''(x) -> f'(x)
    s = re.sub(r"\\prime", "'", s)

    # Overline and underline: \overline{AB} -> overline(A B)
    s = re.sub(r"\\overline\{([^{}]+)\}", _format_overline, s)
    s = re.sub(r"\\underline\{([^{}]+)\}", _format_underline, s)

    # Geometric angles & triangles: \angle -> angle.acute, \triangle -> triangle
    s = re.sub(r"\\angle(?![a-zA-Z])", "angle.acute ", s)
    s = re.sub(r"\\triangle(?![a-zA-Z])", "triangle ", s)

    # Common Greek letters
    greek = [
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
        "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
        "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
        "Delta", "Gamma", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega"
    ]
    for g in greek:
        s = re.sub(rf"\\{g}(?![a-zA-Z])", g, s)

    # Fractions: \frac{a}{b} -> (a)/(b)
    # Handle nested simple fractions by repeating
    for _ in range(3):
        s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1) / (\2)", s)

    # Square roots: \sqrt{x} -> sqrt(x), \sqrt[n]{x} -> root(n, x)
    s = re.sub(r"\\sqrt\[([^{}]+)\]\{([^{}]+)\}", r"root(\1, \2)", s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)

    # Text in math: \text{abc} -> "abc", \mathrm{abc} -> "abc"
    s = re.sub(r"\\(?:text|mathrm)\{([^{}]+)\}", r'"\1"', s)

    # Vector arrows: \vec{v} -> arrow(v)
    s = re.sub(r"\\vec\{([^{}]+)\}", r"arrow(\1)", s)

    # Integrals and limits
    s = re.sub(r"\\int(?![a-zA-Z])", "integral", s)
    s = re.sub(r"\\sum(?![a-zA-Z])", "sum", s)
    s = re.sub(r"\\lim(?![a-zA-Z])", "lim", s)
    s = re.sub(r"\\to(?![a-zA-Z])", "->", s)
    s = re.sub(r"\\infty(?![a-zA-Z])", "infinity", s)

    # Symbols and operators
    replacements = [
        (r"\\cdot(?![a-zA-Z])", "dot"),
        (r"\\times(?![a-zA-Z])", "times"),
        (r"\\pm(?![a-zA-Z])", "plus.minus"),
        (r"\\mp(?![a-zA-Z])", "minus.plus"),
        (r"\\leq?(?![a-zA-Z])", "<="),
        (r"\\geq?(?![a-zA-Z])", ">="),
        (r"\\neq(?![a-zA-Z])", "!="),
        (r"\\approx(?![a-zA-Z])", "approx"),
        (r"\\sim(?![a-zA-Z])", "tilde"),
        (r"\\degree(?![a-zA-Z])", "degree"),
        (r"\\circ(?![a-zA-Z])", "degree"),
        (r"\\parallel(?![a-zA-Z])", "parallel"),
        (r"\\perp(?![a-zA-Z])", "scripts.perp"),
        (r"\\left\(", "("),
        (r"\\right\)", ")"),
        (r"\\left\{", "{"),
        (r"\\right\}", "}"),
        (r"\\left\[", "["),
        (r"\\right\]", "]"),
        (r"\\left\|", "||"),
        (r"\\right\|", "||"),
        (r"\\{", "{"),
        (r"\\}", "}"),
        (r"\\quad(?![a-zA-Z])", "   "),
        (r"\\qquad(?![a-zA-Z])", "      "),
        (r"\\,", " "),
        (r"\\;", " "),
        (r"\\!", ""),
    ]
    for pat, rep in replacements:
        s = re.sub(pat, rep, s)

    # Strip unnecessary curly braces around single sub/superscripts: _{n} -> _n, ^{2} -> ^2
    s = re.sub(r"\_\{([^{}]+)\}", r"_(\1)", s)
    s = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", s)

    # Strip remaining backslashes before known words (e.g. \sin -> sin)
    s = re.sub(r"\\([a-zA-Z]+)", r"\1", s)

    # Split unknown multi-character sequences (like 'mg', 'dx', 'AB')
    s = _split_unknown_math_identifiers(s)

    return s


def markdown_to_typst(text: str) -> str:
    """
    Convert markdown with embedded LaTeX math ($...$, $$...$$) into Typst content syntax.
    Safely escapes Typst control characters in text while preserving math blocks.
    """
    if not text:
        return ""

    tokens = []
    # Pattern to match:
    # 1. Block math: $$ ... $$
    # 2. Inline math: $ ... $
    pattern = re.compile(r"(\$\$.*?\$\$|\$.*?\$)", re.DOTALL)
    parts = pattern.split(text)

    for part in parts:
        if not part:
            continue
        if part.startswith("$$") and part.endswith("$$") and len(part) >= 4:
            math_content = part[2:-2].strip()
            converted = latex_math_to_typst(math_content)
            tokens.append(f"\n$ {converted} $\n")
        elif part.startswith("$") and part.endswith("$") and len(part) >= 2:
            math_content = part[1:-1].strip()
            converted = latex_math_to_typst(math_content)
            tokens.append(f"${converted}$")
        else:
            # Regular text: escape Typst specials and convert Markdown formatting
            t = part
            # Escape Typst # and @
            t = t.replace("\\", "")  # remove leftover backslashes in plain text
            t = t.replace("#", r"\#")
            t = t.replace("@", r"\@")
            # Markdown bold: **text** -> *text* in Typst
            t = re.sub(r"\*\*(.+?)\*\*", r"*\1*", t)
            # Preserve newlines
            t = t.replace("\n\n", "\n#v(0.3em)\n")
            t = t.replace("\n", " \n")
            tokens.append(t)

    return "".join(tokens)
