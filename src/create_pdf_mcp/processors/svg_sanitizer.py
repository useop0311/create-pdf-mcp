import re
import xml.etree.ElementTree as ET


def sanitize_raw_svg(svg_code: str, width_cm: float = 6.5) -> str:
    """
    Sanitizes and normalizes raw SVG code:
    - Strips malicious tags/attributes
    - Ensures viewBox exists for responsive vector scaling in Typst
    - Sets appropriate width/height dimensions
    - Injects default Korean/Math font-family
    """
    s = svg_code.strip()
    if not s:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_cm}cm" height="2cm"></svg>'

    # Remove script tags
    s = re.sub(r"<script.*?>.*?</script>", "", s, flags=re.DOTALL | re.IGNORECASE)
    # Remove javascript event handlers
    s = re.sub(r'\bon\w+\s*=\s*["\'].*?["\']', "", s, flags=re.IGNORECASE)

    try:
        # Parse XML
        root = ET.fromstring(s)
        # Ensure root tag is svg
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if tag.lower() != "svg":
            raise ValueError("Root element is not SVG")

        # Check viewBox
        viewbox = root.attrib.get("viewBox")
        width = root.attrib.get("width")
        height = root.attrib.get("height")

        if not viewbox and width and height:
            # Clean pt/px suffix if present
            w_val = re.sub(r"[^\d.]", "", width)
            h_val = re.sub(r"[^\d.]", "", height)
            if w_val and h_val:
                root.attrib["viewBox"] = f"0 0 {w_val} {h_val}"

        # Set physical width in cm for Typst embedding
        root.attrib["width"] = f"{width_cm}cm"
        if "height" in root.attrib and not viewbox:
            del root.attrib["height"]

        # Ensure font-family styling
        existing_style = root.attrib.get("style", "")
        font_style = "font-family: 'AppleMyungjo', 'Apple SD Gothic Neo', 'Noto Serif CJK KR', 'Noto Serif KR', serif;"
        root.attrib["style"] = f"{font_style} {existing_style}".strip()

        # Re-serialize
        return ET.tostring(root, encoding="unicode")
    except Exception:
        # If XML parsing fails, fallback with regex normalization
        if "<svg" in s:
            s = re.sub(r'<svg\b([^>]*)>', rf'<svg \1 width="{width_cm}cm" style="font-family: \'AppleMyungjo\', \'Apple SD Gothic Neo\', \'Noto Serif KR\', serif;">', s, count=1)
            return s
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_cm}cm" height="2cm"><text x="10" y="20" fill="red">Invalid SVG</text></svg>'
