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
    "overline", "underline", "arrow", "hat", "dot", "ddot", "tilde",
    "abs", "norm", "floor", "ceil", "round", "sign", "arg", "mod", "op",
    # Typst functions and keywords
    "display", "inline", "scripts", "limits", "mat", "vec", "cases",
    "bold", "cal", "bb", "frak", "mono", "sans", "delim",
    "rect", "box", "hide", "wide", "filled", "stroke", "inset", "baseline", "width", "height",
    "pt", "mm", "cm", "em",
    # Symbols and units
    "degree", "infinity", "plus", "minus", "times", "div", "parallel", "approx", "equiv",
    "acute", "arc", "triangle", "square", "angle", "perp", "bot", "inter", "union",
    "without", "emptyset", "forall", "exists", "dots", "compose", "prop",
    "partial", "nabla", "planck", "ell", "chevron", "bullet", "star", "ast",
    "subset", "supset",
    # Modifiers and modifier fields
    "double", "triple", "quad", "cont", "alt", "rev", "big", "neq", "not", "eq",
    "top", "bottom", "left", "right", "c", "h", "v", "down",
    # Greek letters
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    "Delta", "Gamma", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega",
}


def _extract_braced_content(s: str, start_pos: int) -> tuple[str, int] | None:
    """Finds the content of a balanced { ... } starting at start_pos."""
    if start_pos >= len(s) or s[start_pos] != "{":
        return None
    depth = 0
    for i in range(start_pos, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start_pos + 1:i], i + 1
    return None


def _replace_fractions(text: str) -> str:
    r"""
    Replaces \frac{num}{den}, \dfrac{num}{den}, \tfrac{num}{den}, \cfrac{num}{den}
    supporting arbitrarily nested braces in num and den.
    """
    pattern = re.compile(r"\\(?:frac|dfrac|tfrac|cfrac)\s*\{")
    while True:
        m = pattern.search(text)
        if not m:
            break
        start_idx = m.start()
        num_start = m.end() - 1
        num_res = _extract_braced_content(text, num_start)
        if not num_res:
            break
        num_content, den_start_pos = num_res
        while den_start_pos < len(text) and text[den_start_pos].isspace():
            den_start_pos += 1
        den_res = _extract_braced_content(text, den_start_pos)
        if not den_res:
            break
        den_content, end_idx = den_res
        num_converted = _replace_fractions(num_content)
        den_converted = _replace_fractions(den_content)
        replacement = f"({num_converted}) / ({den_converted})"
        text = text[:start_idx] + replacement + text[end_idx:]
    return text


def _replace_roots(text: str) -> str:
    r"""
    Replaces \sqrt{x} and \sqrt[n]{x} with root(n, x) or sqrt(x)
    supporting arbitrarily nested braces.
    """
    while True:
        m = re.search(r"\\sqrt\s*\[(.*?)\]\s*\{", text)
        if not m:
            break
        deg = m.group(1).strip()
        start_idx = m.start()
        res = _extract_braced_content(text, m.end() - 1)
        if not res:
            break
        content, end_idx = res
        text = text[:start_idx] + f"root({deg}, {_replace_roots(content)})" + text[end_idx:]

    while True:
        m = re.search(r"\\sqrt\s*\{", text)
        if not m:
            break
        start_idx = m.start()
        res = _extract_braced_content(text, m.end() - 1)
        if not res:
            break
        content, end_idx = res
        text = text[:start_idx] + f"sqrt({_replace_roots(content)})" + text[end_idx:]
    return text


def _replace_overline_underline(text: str, math_placeholders: list[str] | None = None) -> str:
    r"""
    Replaces \overline{...} and \underline{...} supporting nested \mathrm{...},
    multi-letter uppercase segments like \overline{AB} -> overline(A B),
    and blank underlines like \underline{\hspace{2cm}} or \underline{\quad}.
    """
    for cmd, typst_func in [("overline", "overline"), ("underline", "underline")]:
        while True:
            m = re.search(rf"\\{cmd}\s*\{{", text)
            if not m:
                break
            start_idx = m.start()
            res = _extract_braced_content(text, m.end() - 1)
            if not res:
                break
            content, end_idx = res
            raw_stripped = content.strip()
            if cmd == "underline" and math_placeholders is not None:
                hspace_m = re.fullmatch(r"\\hspace\s*\{([^{}]+)\}", raw_stripped)
                if hspace_m:
                    w_val = hspace_m.group(1).strip()
                    ph_idx = len(math_placeholders)
                    math_placeholders.append(
                        f'#box(width: {w_val}, height: 0.75em, baseline: 12%, stroke: (bottom: 0.6pt))[]'
                    )
                    text = text[:start_idx] + f"\x00MATHPH{ph_idx}\x00" + text[end_idx:]
                    continue
                if raw_stripped in ("", r"\quad", r"\qquad") or re.fullmatch(r"(?:\\quad|\\qquad|\\,|\\;|\\ |\s|_)+", raw_stripped):
                    w_em = 3.0 if "qquad" in raw_stripped else 2.2
                    ph_idx = len(math_placeholders)
                    math_placeholders.append(
                        f'#box(width: {w_em:.1f}em, height: 0.75em, baseline: 12%, stroke: (bottom: 0.6pt))[]'
                    )
                    text = text[:start_idx] + f"\x00MATHPH{ph_idx}\x00" + text[end_idx:]
                    continue

            clean = re.sub(r"\\(?:mathrm|text)\{([a-zA-Z]+)\}", r"\1", content).strip()
            if clean.isupper() and len(clean) > 1:
                spaced = " ".join(clean)
                replacement = f"{typst_func}({spaced})"
            else:
                replacement = f"{typst_func}({clean})"
            text = text[:start_idx] + replacement + text[end_idx:]
    return text


def _replace_boxed_and_phantom(text: str, math_placeholders: list[str]) -> str:
    r"""
    Replaces \boxed{...}, \phantom{...}, and \hspace{...} in LaTeX math mode
    using placeholders so Typst #box / #hide / #h expressions are preserved intact.
    """
    # 1. \boxed{...}
    while True:
        m = re.search(r"\\boxed\s*\{", text)
        if not m:
            break
        start_idx = m.start()
        res = _extract_braced_content(text, m.end() - 1)
        if not res:
            break
        content, end_idx = res
        raw_stripped = content.strip()
        ph_idx = len(math_placeholders)
        if not raw_stripped or re.fullmatch(r"(?:\\quad|\\qquad|\\,|\\;|\\ |\s)+", raw_stripped):
            math_placeholders.append(
                '#box(width: 2.2em, height: 1.1em, baseline: 18%, stroke: 0.6pt, radius: 1pt)[]'
            )
        else:
            inner_typ = latex_math_to_typst(raw_stripped)
            math_placeholders.append(
                f'#box(stroke: 0.6pt, inset: (x: 4pt, y: 2.5pt), baseline: 20%, radius: 1pt)[${inner_typ}$]'
            )
        text = text[:start_idx] + f" \x00MATHPH{ph_idx}\x00 " + text[end_idx:]

    # 2. \phantom{...}
    while True:
        m = re.search(r"\\phantom\s*\{", text)
        if not m:
            break
        start_idx = m.start()
        res = _extract_braced_content(text, m.end() - 1)
        if not res:
            break
        content, end_idx = res
        inner_typ = latex_math_to_typst(content.strip())
        ph_idx = len(math_placeholders)
        math_placeholders.append(f'#hide[$ {inner_typ} $]')
        text = text[:start_idx] + f" \x00MATHPH{ph_idx}\x00 " + text[end_idx:]

    # 3. \hspace{...}
    while True:
        m = re.search(r"\\hspace\*?\s*\{([^{}]+)\}", text)
        if not m:
            break
        w_val = m.group(1).strip()
        ph_idx = len(math_placeholders)
        math_placeholders.append(f"#h({w_val})")
        text = text[:m.start()] + f" \x00MATHPH{ph_idx}\x00 " + text[m.end():]

    return text


def _split_unknown_math_identifiers(text: str) -> str:
    """
    In Typst math mode, multi-character sequences like 'mg', 'ma', 'AB' are treated
    as undefined variables rather than product of symbols.
    This splits unknown multi-character variable clusters (e.g. 'mg' -> 'm g', 'dx' -> 'dif x').
    """
    def repl_single(w: str) -> str:
        if w in KNOWN_TYPST_MATH:
            return w
        if w.startswith("d") and len(w) == 2 and w[1] in "xyztsuvwr":
            return f"dif {w[1]}"
        # Defensive fallback against accidental concatenation of style or limit keywords
        for prefix in ("displaystyle", "textstyle", "scriptstyle", "scriptscriptstyle"):
            if w.startswith(prefix) and len(w) > len(prefix):
                return repl_single(w[len(prefix):])
        for suffix in ("limits", "nolimits"):
            if w.endswith(suffix) and len(w) > len(suffix):
                return repl_single(w[:-len(suffix)])
        return " ".join(w)

    def repl(m: re.Match) -> str:
        return repl_single(m.group(0))

    # Do not split inside quoted strings (e.g. "text") or \x00MATHPH...\x00 placeholders
    parts = re.split(r'("[^"]*"|\x00MATHPH\d+\x00)', text)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"(?<![a-zA-Z])[a-zA-Z]{2,}(?![a-zA-Z:])", repl, parts[i])
    return "".join(parts)


def latex_math_to_typst(math_str: str) -> str:
    """
    Convert common LaTeX math commands to native Typst math syntax.
    Enables native, fast, offline Typst compilation while allowing models and users to write standard LaTeX.
    """
    s = math_str.strip()
    math_placeholders: list[str] = []

    # Normalize primes: f'(x) or f^{\prime}(x) -> f'(x)
    s = re.sub(r"\\prime", "'", s)

    # Separate adjacent backslash commands (e.g. \angle\mathrm -> \angle \mathrm, \displaystyle\int -> \displaystyle \int)
    s = re.sub(r"\\([a-zA-Z]+)(?=\\)", r"\\\1 ", s)

    # 0. Handle \boxed{...}, \phantom{...}, \hspace{...} and blank underlines first
    s = _replace_overline_underline(s, math_placeholders)
    s = _replace_boxed_and_phantom(s, math_placeholders)

    # Convert multiple consecutive underscores (e.g. ____) in math mode to a blank underline box
    def _repl_math_underscores(m: re.Match) -> str:
        w_em = max(2.0, min(len(m.group(0)) * 0.55, 7.0))
        ph_idx = len(math_placeholders)
        math_placeholders.append(
            f'#box(width: {w_em:.1f}em, height: 0.75em, baseline: 12%, stroke: (bottom: 0.6pt))[]'
        )
        return f" \x00MATHPH{ph_idx}\x00 "

    s = re.sub(r"_{2,}", _repl_math_underscores, s)

    # 1. Normalize omitted subscripts: \int{a}^{b} -> \int_{a}^{b}, \right]{a}^{b} -> \right]_{a}^{b}
    s = re.sub(r"(\\int|integral)\s*\{", r"\1_{", s)
    s = re.sub(r"(\\sum|sum)\s*\{", r"\1_{", s)
    s = re.sub(r"(\\prod|product)\s*\{", r"\1_{", s)
    s = re.sub(r"(\\right\]|\]|\))\s*\{([^{}]+)\}\s*\^", r"\1_(\2)^", s)

    # 2. LaTeX environments (matrices, cases, aligned)
    def repl_matrix(m: re.Match, delim: str = "") -> str:
        content = m.group(1).strip()
        rows = [r.strip() for r in re.split(r"\\\\", content) if r.strip()]
        formatted_rows = [", ".join(c.strip() for c in re.split(r"&", r)) for r in rows]
        body = "; ".join(formatted_rows)
        if delim:
            return f'mat(delim: "{delim}", {body})'
        return f"mat({body})"

    def repl_cases(m: re.Match) -> str:
        content = m.group(1).strip()
        rows = [r.strip() for r in re.split(r"\\\\", content) if r.strip()]
        body = ", ".join(rows)
        return f"cases({body})"

    s = re.sub(r"\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}", lambda m: repl_matrix(m, "("), s, flags=re.DOTALL)
    s = re.sub(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", lambda m: repl_matrix(m, "["), s, flags=re.DOTALL)
    s = re.sub(r"\\begin\{vmatrix\}(.*?)\\end\{vmatrix\}", lambda m: repl_matrix(m, "|"), s, flags=re.DOTALL)
    s = re.sub(r"\\begin\{matrix\}(.*?)\\end\{matrix\}", lambda m: repl_matrix(m, ""), s, flags=re.DOTALL)
    s = re.sub(r"\\begin\{cases\}(.*?)\\end\{cases\}", repl_cases, s, flags=re.DOTALL)
    s = re.sub(r"\\begin\{aligned\}(.*?)\\end\{aligned\}", r"\1", s, flags=re.DOTALL)
    s = re.sub(r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", r"\1", s, flags=re.DOTALL)

    # 3. Math styles: \displaystyle, \textstyle, \scriptstyle, \scriptscriptstyle
    s = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)(?![a-zA-Z])", " ", s)

    # 4. Limit controls: \limits, \nolimits
    s = re.sub(r"\\(?:limits|nolimits)(?![a-zA-Z])", " ", s)

    # 5. Delimiter sizing prefixes: \big, \Big, \bigg, \Bigg (and variants l, r, m)
    s = re.sub(r"\\(?:[bB]igg?[lmr]?)(?![a-zA-Z])", " ", s)

    # 6. Delimiters: \left and \right
    s = re.sub(r"\\(?:left|right)\.", "", s)
    s = re.sub(r"\\(?:left|right)\\\|", "||", s)
    s = re.sub(r"\\(?:left|right)\|", "|", s)
    s = re.sub(r"\\(?:left|right)\\\{", "{", s)
    s = re.sub(r"\\(?:left|right)\\\}", "}", s)
    s = re.sub(r"\\(?:left|right)\(", "(", s)
    s = re.sub(r"\\(?:left|right)\)", ")", s)
    s = re.sub(r"\\(?:left|right)\[", "[", s)
    s = re.sub(r"\\(?:left|right)\]", "]", s)
    s = re.sub(r"\\(?:left|right)(?![a-zA-Z])", "", s)
    s = re.sub(r"\\\|", "||", s)
    s = re.sub(r"\\langle(?![a-zA-Z])", "chevron.l ", s)
    s = re.sub(r"\\rangle(?![a-zA-Z])", "chevron.r ", s)

    # Vector arrows, dots, accents
    s = re.sub(r"\\vec\{([^{}]+)\}", r"arrow(\1)", s)
    s = re.sub(r"\\bar\{([^{}]+)\}", r"overline(\1)", s)
    s = re.sub(r"\\hat\{([^{}]+)\}", r"hat(\1)", s)
    s = re.sub(r"\\tilde\{([^{}]+)\}", r"tilde(\1)", s)
    s = re.sub(r"\\ddot\{([^{}]+)\}", r"dot.double(\1)", s)
    s = re.sub(r"\\dot\{([^{}]+)\}", r"dot(\1)", s)

    # 8. Text and font wrappers
    def repl_mathrm(m: re.Match) -> str:
        content = m.group(1).strip()
        if content.isupper() and len(content) > 1:
            return " ".join(content)
        return f'"{content}"'

    s = re.sub(r"\\mathrm\{([^{}]+)\}", repl_mathrm, s)
    s = re.sub(r"\\text\{([^{}]+)\}", r'"\1"', s)
    s = re.sub(r"\\(?:textbf)\{([^{}]+)\}", r'bold("\1")', s)
    s = re.sub(r"\\(?:mathbf|bm|boldsymbol)\{([^{}]+)\}", r"bold(\1)", s)
    s = re.sub(r"\\mathbb\{([^{}]+)\}", r"bb(\1)", s)
    s = re.sub(r"\\(?:mathcal|mathscr)\{([^{}]+)\}", r"cal(\1)", s)
    s = re.sub(r"\\mathsf\{([^{}]+)\}", r"sans(\1)", s)
    s = re.sub(r"\\mathtt\{([^{}]+)\}", r"mono(\1)", s)
    s = re.sub(r"\\mathit\{([^{}]+)\}", r"\1", s)
    s = re.sub(r"\\operatorname\*?\{([^{}]+)\}", r'op("\1")', s)

    # 9. Geometric angles & triangles & shapes
    s = re.sub(r"\\(?:measuredangle|sphericalangle)(?![a-zA-Z])", "angle.arc ", s)
    s = re.sub(r"\\angle(?![a-zA-Z])", "angle.acute ", s)
    s = re.sub(r"\\triangle(?![a-zA-Z])", "triangle ", s)
    s = re.sub(r"\\blacksquare(?![a-zA-Z])", "square.filled ", s)
    s = re.sub(r"\\(?:square|Box)(?![a-zA-Z])", "square ", s)

    # 10. Greek letters (variants first, then standard)
    var_greek = [
        ("varphi", "phi.alt"),
        ("varepsilon", "epsilon.alt"),
        ("vartheta", "theta.alt"),
        ("varpi", "pi.alt"),
        ("varrho", "rho.alt"),
        ("varsigma", "sigma.alt"),
    ]
    for vg, typ_g in var_greek:
        s = re.sub(rf"\\{vg}(?![a-zA-Z])", f"{typ_g} ", s)

    greek = [
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
        "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
        "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
        "Delta", "Gamma", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega"
    ]
    for g in greek:
        s = re.sub(rf"\\{g}(?![a-zA-Z])", g, s)

    # 11. Fractions: \frac, \dfrac, \tfrac, \cfrac (with nested balanced braces support)
    s = _replace_fractions(s)

    # 12. Square roots (with nested balanced braces support)
    s = _replace_roots(s)

    # 13. Calculus, integrals, sums, products, limits
    s = re.sub(r"\\iiint(?![a-zA-Z])", "integral.triple ", s)
    s = re.sub(r"\\iint(?![a-zA-Z])", "integral.double ", s)
    s = re.sub(r"\\oint(?![a-zA-Z])", "integral.cont ", s)
    s = re.sub(r"\\int(?![a-zA-Z])", "integral ", s)
    s = re.sub(r"\\coprod(?![a-zA-Z])", "product.co ", s)
    s = re.sub(r"\\prod(?![a-zA-Z])", "product ", s)
    s = re.sub(r"\\sum(?![a-zA-Z])", "sum ", s)
    s = re.sub(r"\\limsup(?![a-zA-Z])", 'limits(op("lim sup")) ', s)
    s = re.sub(r"\\liminf(?![a-zA-Z])", 'limits(op("lim inf")) ', s)
    s = re.sub(r"\\lim(?![a-zA-Z])", "lim ", s)

    # 14. Relations, logic, and set operations
    s = re.sub(r"\\(?:iff|Longleftrightarrow)(?![a-zA-Z])", "<=> ", s)
    s = re.sub(r"\\(?:implies|Longrightarrow)(?![a-zA-Z])", "=> ", s)
    s = re.sub(r"\\leftrightarrow(?![a-zA-Z])", "<-> ", s)
    s = re.sub(r"\\Leftarrow(?![a-zA-Z])", "arrow.l.double ", s)
    s = re.sub(r"\\Rightarrow(?![a-zA-Z])", "=> ", s)
    s = re.sub(r"\\longleftarrow(?![a-zA-Z])", "<- ", s)
    s = re.sub(r"\\longrightarrow(?![a-zA-Z])", "-> ", s)
    s = re.sub(r"\\leftarrow(?![a-zA-Z])", "<- ", s)
    s = re.sub(r"\\(?:to|rightarrow)(?![a-zA-Z])", "-> ", s)
    s = re.sub(r"\\mapsto(?![a-zA-Z])", "|-> ", s)

    s = re.sub(r"\\notin(?![a-zA-Z])", "in.not ", s)
    s = re.sub(r"\\in(?![a-zA-Z])", "in ", s)
    s = re.sub(r"\\(?:ni|owns)(?![a-zA-Z])", "in.rev ", s)
    s = re.sub(r"\\subsetneq(?![a-zA-Z])", "subset.neq ", s)
    s = re.sub(r"\\subseteq(?![a-zA-Z])", "subset.eq ", s)
    s = re.sub(r"\\supseteq(?![a-zA-Z])", "supset.eq ", s)
    s = re.sub(r"\\subset(?![a-zA-Z])", "subset ", s)
    s = re.sub(r"\\supset(?![a-zA-Z])", "supset ", s)
    s = re.sub(r"\\bigcap(?![a-zA-Z])", "inter.big ", s)
    s = re.sub(r"\\bigcup(?![a-zA-Z])", "union.big ", s)
    s = re.sub(r"\\cap(?![a-zA-Z])", "inter ", s)
    s = re.sub(r"\\cup(?![a-zA-Z])", "union ", s)
    s = re.sub(r"\\setminus(?![a-zA-Z])", "without ", s)
    s = re.sub(r"\\(?:emptyset|varnothing)(?![a-zA-Z])", "emptyset ", s)

    s = re.sub(r"\\forall(?![a-zA-Z])", "forall ", s)
    s = re.sub(r"\\exists(?![a-zA-Z])", "exists ", s)
    s = re.sub(r"\\nexists(?![a-zA-Z])", "exists.not ", s)

    # 15. Symbols and operators
    replacements = [
        (r"\\cdots(?![a-zA-Z])", "dots.c "),
        (r"\\ldots(?![a-zA-Z])", "dots.h "),
        (r"\\vdots(?![a-zA-Z])", "dots.v "),
        (r"\\ddots(?![a-zA-Z])", "dots.down "),
        (r"\\dots(?![a-zA-Z])", "dots "),
        (r"\\infty(?![a-zA-Z])", "infinity"),
        (r"\\cdot(?![a-zA-Z])", "dot "),
        (r"\\times(?![a-zA-Z])", "times "),
        (r"\\div(?![a-zA-Z])", "div "),
        (r"\\pm(?![a-zA-Z])", "plus.minus "),
        (r"\\mp(?![a-zA-Z])", "minus.plus "),
        (r"\\leq?(?![a-zA-Z])", "<="),
        (r"\\geq?(?![a-zA-Z])", ">="),
        (r"\\neq(?![a-zA-Z])", "!="),
        (r"\\equiv(?![a-zA-Z])", "equiv "),
        (r"\\cong(?![a-zA-Z])", "tilde.equiv "),
        (r"\\approx(?![a-zA-Z])", "approx "),
        (r"\\sim(?![a-zA-Z])", "tilde "),
        (r"\\propto(?![a-zA-Z])", "prop "),
        (r"\\ll(?![a-zA-Z])", "<< "),
        (r"\\gg(?![a-zA-Z])", ">> "),
        (r"\\degree(?![a-zA-Z])", "degree"),
        (r"\^\\circ(?![a-zA-Z])", "^degree"),
        (r"\\circ(?![a-zA-Z])", "degree"),
        (r"\\parallel(?![a-zA-Z])", "parallel "),
        (r"\\perp(?![a-zA-Z])", "perp "),
        (r"\\partial(?![a-zA-Z])", "partial "),
        (r"\\nabla(?![a-zA-Z])", "nabla "),
        (r"\\hbar(?![a-zA-Z])", "planck "),
        (r"\\ell(?![a-zA-Z])", "ell "),
        (r"\\\{", "{"),
        (r"\\\}", "}"),
        (r"\\quad(?![a-zA-Z])", "   "),
        (r"\\qquad(?![a-zA-Z])", "      "),
        (r"\\(?:enspace|thickspace|medspace|thinspace)(?![a-zA-Z])", " "),
        (r"\\,", " "),
        (r"\\;", " "),
        (r"\\:", " "),
        (r"\\ ", " "),
        (r"\\!", ""),
    ]
    for pat, rep in replacements:
        s = re.sub(pat, rep, s)

    # 16. Sub/superscript curly braces: _{n} -> _(n), ^{2} -> ^(2)
    s = re.sub(r"\_\{([^{}]+)\}", r"_(\1)", s)
    s = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", s)

    # 17. Strip remaining backslashes before known words
    s = re.sub(r"\\([a-zA-Z]+)", r"\1", s)

    # 18. Split unknown multi-character sequences
    s = _split_unknown_math_identifiers(s)

    # 19. Restore math placeholders (\boxed, \phantom, \hspace, blank underlines)
    for idx, ph_val in enumerate(math_placeholders):
        s = s.replace(f"\x00MATHPH{idx}\x00", ph_val)

    # 20. Clean up multiple spaces
    s = re.sub(r" +", " ", s)

    return s.strip()


_UL_START = "\uE001"
_UL_END = "\uE002"
_BOLD_START = "\uE003"
_BOLD_END = "\uE004"
_ESCAPED_DOLLAR = "\uE005"


def _format_plain_text_segment(part: str, has_inline_subquestions: bool = False) -> str:
    """
    Escapes Typst markup control characters in plain text while converting
    Markdown bold (**...**), underline (__...__), blank lines (____), [빈칸],
    parenthesized spaces, and newlines.
    """
    t = part
    txt_placeholders: list[str] = []

    def _add_txt_ph(val: str) -> str:
        idx = len(txt_placeholders)
        txt_placeholders.append(val)
        return f"\x00TXTPH{idx}\x00"

    # If inline sub-questions "(1) ... (2) ..." are present on the same line, break lines before (1), (2), ...
    if has_inline_subquestions:
        t = re.sub(r"(?<=[^\n])(?<![0-9a-zA-Z])\s+(\([1-9]\)\s+)", r"\n\1", t)
        t = re.sub(r"(?<=[.?!:])(\([1-9]\)\s+)", r"\n\1", t)

    # 1. [빈칸: 라벨] or [빈칸] / (빈칸)
    def _repl_labeled_blank(m: re.Match) -> str:
        lbl = m.group(1).strip().replace("#", r"\#").replace("@", r"\@").replace("<", r"\<").replace("_", r"\_")
        return _add_txt_ph(
            f'#box(stroke: 0.6pt + rgb("#333"), inset: (x: 6pt, y: 2pt), baseline: 20%, radius: 1.5pt)[{lbl}]'
        )

    t = re.sub(r"\[\s*빈칸\s*:\s*([^\]]+?)\s*\]", _repl_labeled_blank, t)
    t = re.sub(
        r"\[\s*빈칸\s*\]|\(\s*빈칸\s*\)",
        lambda _: _add_txt_ph(
            '#box(width: 3.5em, height: 1.05em, baseline: 18%, stroke: 0.6pt + rgb("#333"), radius: 1.5pt)[]'
        ),
        t,
    )

    # 2. Markdown double-underscore __text__ into underline placeholder before matching raw underscores
    t = re.sub(r"__([^_\n]+?)__", lambda m: f"{_UL_START}{m.group(1)}{_UL_END}", t)

    # 3. Underscore blanks: 2 or more consecutive underscores (e.g. ___, ____, ______)
    def _repl_underscore_blank(m: re.Match) -> str:
        count = len(m.group(0))
        width_em = max(3.0, min(10.0, count * 0.55))
        return _add_txt_ph(
            f'#box(width: {width_em:.1f}em, height: 0.8em, baseline: 12%, stroke: (bottom: 0.6pt + rgb("#222")))[#h({width_em:.1f}em)]'
        )

    t = re.sub(r"_{2,}", _repl_underscore_blank, t)

    # 4. Parentheses/brackets with multiple spaces: (      ) or [      ]
    def _repl_paren_blank(m: re.Match) -> str:
        w_em = max(2.0, min(len(m.group(1)) * 0.5, 8.0))
        return _add_txt_ph(f"(#h({w_em:.1f}em))")

    def _repl_bracket_blank(m: re.Match) -> str:
        w_em = max(2.0, min(len(m.group(1)) * 0.5, 8.0))
        return _add_txt_ph(f"[#h({w_em:.1f}em)]")

    t = re.sub(r"\(([ \t]{2,})\)", _repl_paren_blank, t)
    t = re.sub(r"\[([ \t]{2,})\]", _repl_bracket_blank, t)

    # 5. Parentheses/brackets with padded blank labels: (   가   ) or [   (가)   ]
    def _repl_padded_paren_label(m: re.Match) -> str:
        lbl = m.group(1).strip()
        return _add_txt_ph(f"(#h(1.0em){lbl}#h(1.0em))")

    def _repl_padded_bracket_label(m: re.Match) -> str:
        lbl = m.group(1).strip()
        return _add_txt_ph(f"[#h(1.0em){lbl}#h(1.0em)]")

    t = re.sub(r"\([ \t]{2,}(\(?[가-하A-Zㄱ-ㅎ0-9]+\)?)[ \t]{2,}\)", _repl_padded_paren_label, t)
    t = re.sub(r"\[[ \t]{2,}(\(?[가-하A-Zㄱ-ㅎ0-9]+\)?)[ \t]{2,}\]", _repl_padded_bracket_label, t)

    # 6. Convert Markdown bold **text** into bold placeholder
    t = re.sub(r"\*\*(.+?)\*\*", lambda m: f"{_BOLD_START}{m.group(1)}{_BOLD_END}", t)

    # 7. Escape Typst specials in remaining plain text
    t = t.replace("\\", "")  # remove leftover backslashes in plain text
    t = t.replace("#", r"\#")
    t = t.replace("@", r"\@")
    t = t.replace("$", r"\$")
    t = t.replace("<", r"\<")
    t = t.replace("~", r"\~")
    t = t.replace("*", r"\*")
    t = t.replace("_", r"\_")
    t = t.replace("//", r"\/")
    t = re.sub(r"(?m)^(\s*)=", r"\1\\=", t)

    # 8. Restore formatting placeholders
    t = t.replace(_BOLD_START, "*").replace(_BOLD_END, "*")
    t = t.replace(_UL_START, "#underline[").replace(_UL_END, "]")

    # Bold sub-question markers at start of lines when inline sub-questions exist
    if has_inline_subquestions:
        t = re.sub(r"(^|\n)(\([1-9]\))(\s+)", r"\1*\2*\3", t)

    # Preserve newlines
    t = re.sub(r"\n{2,}", "\n\n#v(0.25em)\n\n", t)
    t = re.sub(r"(?<!\n)\n(?!\n)", " \n", t)

    # Restore blank placeholders
    for idx, ph_val in enumerate(txt_placeholders):
        t = t.replace(f"\x00TXTPH{idx}\x00", ph_val)

    return t


def markdown_to_typst(text: str) -> str:
    r"""
    Convert markdown with embedded LaTeX math ($...$, $$...$$, \[...\], \(...\)),
    HTML underlines (<u>...</u>), and exam blanks (______, [빈칸], etc.) into Typst content syntax.
    Safely escapes Typst control characters in text while preserving math blocks.
    """
    if not text:
        return ""

    # Preserve explicitly escaped dollar signs \$
    text = text.replace(r"\$", _ESCAPED_DOLLAR)

    # Convert HTML <u>...</u> tags into underline placeholders before escaping '<' and '>'
    text = re.sub(
        r"<u>(.*?)</u>",
        lambda m: f"{_UL_START}{m.group(1)}{_UL_END}",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Normalize LaTeX display/inline math: \[ ... \] -> $$ ... $$, \( ... \) -> $ ... $
    text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text, flags=re.DOTALL)

    tokens = []
    # Pattern to match:
    # 1. Block math: $$ ... $$
    # 2. Inline math: $ ... $ (closing $ not immediately followed by ASCII digit/letter so currency like '$20 and $10' stays text)
    pattern = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+?\$(?![0-9a-zA-Z]))", re.DOTALL)
    parts = pattern.split(text)

    # Check if plain text parts contain inline sub-question sequences like "(1) ... (2) ..."
    plain_joined = " ".join(
        p for p in parts if p and not (p.startswith("$") and p.endswith("$"))
    )
    has_inline_subquestions = bool(
        re.search(r"(?:^|[\s.?!:])\(1\)\s+", plain_joined)
        and re.search(r"(?:^|[\s.?!:])\(2\)\s+", plain_joined)
    )

    for part in parts:
        if not part:
            continue
        if part.startswith("$$") and part.endswith("$$") and len(part) >= 4:
            math_content = part[2:-2].strip()
            converted = latex_math_to_typst(math_content)
            tokens.append(f"\n$ {converted} $\n")
        elif (
            part.startswith("$")
            and part.endswith("$")
            and len(part) >= 2
            and "\n" not in part
        ):
            math_content = part[1:-1].strip()
            converted = latex_math_to_typst(math_content)
            tokens.append(f"${converted}$")
        else:
            part = part.replace(_ESCAPED_DOLLAR, "$")
            tokens.append(_format_plain_text_segment(part, has_inline_subquestions=has_inline_subquestions))

    return "".join(tokens)


SVG_SUPERSCRIPTS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "i": "ⁱ", "x": "ˣ", "y": "ʸ", "k": "ᵏ", "m": "ᵐ"
}

SVG_SUBSCRIPTS = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "o": "ₒ", "x": "ₓ", "n": "ₙ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ"
}

SVG_GREEK_AND_SYMBOLS = [
    (r"\^\s*\\circ", "°"),
    (r"\\circ", "°"),
    (r"\\theta", "θ"), (r"\\pi", "π"), (r"\\alpha", "α"), (r"\\beta", "β"),
    (r"\\gamma", "γ"), (r"\\delta", "δ"), (r"\\epsilon", "ε"), (r"\\lambda", "λ"),
    (r"\\mu", "μ"), (r"\\sigma", "σ"), (r"\\omega", "ω"), (r"\\Omega", "Ω"),
    (r"\\Delta", "Δ"), (r"\\times", "×"), (r"\\div", "÷"), (r"\\pm", "±"),
    (r"\\leq?", "≤"), (r"\\geq?", "≥"), (r"\\neq?", "≠"), (r"\\approx", "≈"),
    (r"\\infty", "∞"), (r"\\prime", "′"), (r"'", "′"),
    (r"\\vec\{([^{}]+)\}", r"\1⃗"),
    (r"\\sqrt\{([^{}]+)\}", r"√(\1)"),
    (r"\\frac\{1\}\{2\}", "½"),
    (r"\\frac\{1\}\{3\}", "⅓"),
    (r"\\frac\{2\}\{3\}", "⅔"),
    (r"\\frac\{1\}\{4\}", "¼"),
    (r"\\frac\{3\}\{4\}", "¾"),
]


def format_svg_math_label(text: str) -> str:
    """
    Converts LaTeX math expressions and ASCII math (e.g. 'y=-x^2+4x', '\\theta=30^\\circ', 'P(x_1, y_1)')
    into beautiful, standard vector SVG typography using unicode math and tspan scripts.
    """
    if not text:
        return ""
    s = text.strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()

    # Pre-escape XML special characters
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for pat, rep in SVG_GREEK_AND_SYMBOLS:
        s = re.sub(pat + r"(?![a-zA-Z])", rep, s)

    # Convert ^(...) or ^{...} or ^char to superscripts
    def repl_sup(m: re.Match) -> str:
        content = m.group(1) or m.group(2)
        if all(c in SVG_SUPERSCRIPTS for c in content):
            return "".join(SVG_SUPERSCRIPTS[c] for c in content)
        return f'<tspan baseline-shift="super" font-size="72%">{content}</tspan>'

    s = re.sub(r"\^\{([^}]+)\}|\^([0-9a-zA-Z+-])", repl_sup, s)

    # Convert _{...} or _char to subscripts
    def repl_sub(m: re.Match) -> str:
        content = m.group(1) or m.group(2)
        if all(c in SVG_SUBSCRIPTS for c in content):
            return "".join(SVG_SUBSCRIPTS[c] for c in content)
        return f'<tspan baseline-shift="sub" font-size="72%">{content}</tspan>'

    s = re.sub(r"\_\{([^}]+)\}|\_([0-9a-zA-Z+-])", repl_sub, s)
    s = re.sub(r"\\(?:mathrm|text)\{([^}]+)\}", r"\1", s)
    s = s.replace(r"\,", " ").replace(r"\;", " ").replace(r"\quad", "   ")
    return s
