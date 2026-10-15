"""Enforce the site's CSP-related rules on published HTML, CSS and SVG files."""

import os
import re
import sys
from html.parser import HTMLParser

EXPECTED_CSP = (
    "default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; "
    "base-uri 'none'; form-action 'none'"
)

# <link rel=...> values that make the browser fetch something or open a connection.
LOADING_LINK_RELS = {"stylesheet", "icon", "apple-touch-icon", "preload", "modulepreload",
                     "manifest", "prefetch", "mask-icon", "preconnect", "dns-prefetch",
                     "prerender"}
# tag -> attributes that load a resource
RESOURCE_ATTRS = {
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "script": ("src",),
    "iframe": ("src",),
    "frame": ("src",),
    "embed": ("src",),
    "object": ("data",),
    "video": ("src", "poster"),
    "audio": ("src",),
    "track": ("src",),
    "input": ("src",),
    # SVG elements, inline in HTML or in a standalone .svg file
    "image": ("href", "xlink:href"),
    "feimage": ("href", "xlink:href"),
    "use": ("href", "xlink:href"),
}


def _normalise_csp(value: str) -> str:
    return " ".join(value.split()).rstrip(";").strip()


def _is_external(url: str) -> bool:
    # Browsers drop tabs and newlines inside a URL and read "\\" as "/".
    u = re.sub(r"[\t\n\r]", "", url).strip().replace("\\", "/").lower()
    return u.startswith(("http://", "https://", "//", "data:"))


def _srcset_urls(value: str) -> list[str]:
    return [part.strip().split()[0] for part in value.split(",") if part.strip()]


class _Checker(HTMLParser):
    def __init__(self, svg: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        # A standalone SVG has no CSP of its own, so CSP and inline-style rules don't apply,
        # but scripts, event handlers and external loads are still errors.
        self.svg = svg
        self.errors: list[str] = []
        self.saw_csp = False
        self._in_head = False
        self._in_script = False
        self._script_has_src = False
        self._script_text = ""
        self._in_style = False
        self._style_text = ""

    def _resource(self, tag: str, attr: str, url: str) -> None:
        if not self.svg and not self.saw_csp:
            self.errors.append(f"<{tag} {attr}={url!r}> loads before the CSP meta tag")
        if _is_external(url):
            self.errors.append(f"<{tag} {attr}={url!r}> loads an external resource")

    def handle_starttag(self, tag, attrs):
        names = [k.lower() for k, _v in attrs]
        for name in sorted({n for n in names if names.count(n) > 1}):
            self.errors.append(f"<{tag}> has duplicate {name}= attributes")
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "head":
            self._in_head = True
        elif tag == "body":
            self._in_head = False
        for name in a:
            if name.startswith("on"):
                self.errors.append(f"<{tag}> has inline event handler {name}=")
        if "style" in a and not self.svg:
            self.errors.append(f"<{tag}> has inline style= attribute")
        if tag == "style":
            if self.svg:
                self._in_style = True
                self._style_text = ""
            else:
                self.errors.append("<style> element (inline CSS is blocked by the CSP)")
        if tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            self.errors.append("<meta http-equiv=refresh> (redirects are not allowed)")
        if tag == "meta" and a.get("http-equiv", "").lower() == "content-security-policy":
            if not self._in_head:
                self.errors.append("CSP meta tag is outside <head> (browsers ignore it there)")
            self.saw_csp = True
            if _normalise_csp(a.get("content", "")) != _normalise_csp(EXPECTED_CSP):
                self.errors.append(f"CSP does not match the expected policy: {a.get('content')!r}")
        if tag == "link":
            rels = set(a.get("rel", "").lower().split())
            if rels & LOADING_LINK_RELS and a.get("href"):
                self._resource(tag, "href", a["href"])
        for attr in RESOURCE_ATTRS.get(tag, ()):
            if attr in a and a[attr]:
                urls = _srcset_urls(a[attr]) if attr == "srcset" else [a[attr]]
                for url in urls:
                    self._resource(tag, attr, url)
        if tag == "script" and self.svg:
            self.errors.append("<script> in an SVG file")
        if tag == "script":
            self._in_script = True
            self._script_has_src = bool(a.get("src"))
            self._script_text = ""
        if tag in ("a", "area"):
            if a.get("href", "").strip().lower().startswith("javascript:"):
                self.errors.append(f"<{tag}> uses a javascript: URL")
            if a.get("target", "").lower() == "_blank":
                rels = set(a.get("rel", "").lower().split())
                if not {"noopener", "noreferrer"} <= rels:
                    self.errors.append(f"<{tag} href={a.get('href')!r} target=_blank> needs rel=\"noopener noreferrer\"")
        if tag == "img" and "alt" not in a:
            self.errors.append(f"<img src={a.get('src')!r}> has no alt attribute")

    def handle_data(self, data):
        if self._in_script:
            self._script_text += data
        if self._in_style:
            self._style_text += data

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
        if tag == "style" and self._in_style:
            self.errors.extend(check_css(self._style_text))
            self._in_style = False
        if tag == "script" and self._in_script:
            if not self._script_has_src and not self.svg:
                self.errors.append("inline <script> (blocked by the CSP)")
            self._in_script = False


def check_html(text: str) -> list[str]:
    checker = _Checker()
    checker.feed(text)
    checker.close()
    if not checker.saw_csp:
        checker.errors.append("no CSP meta tag found")
    return checker.errors


def check_svg(text: str) -> list[str]:
    checker = _Checker(svg=True)
    checker.feed(text)
    checker.close()
    return checker.errors


_CSS_URL = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""", re.IGNORECASE)
_CSS_IMPORT = re.compile(r"""@import\s+(['"])(.*?)\1""", re.IGNORECASE)
# image-set() and -webkit-image-set() also accept bare strings as URLs.
_CSS_IMAGE_SET = re.compile(r"image-set\((.*?)\)\s*[;}]", re.IGNORECASE | re.DOTALL)
_CSS_STRING = re.compile(r"""(['"])(.*?)\1""")


def check_css(text: str) -> list[str]:
    urls = []
    for pattern in (_CSS_URL, _CSS_IMPORT):
        urls.extend(match.group(2) for match in pattern.finditer(text))
    for image_set in _CSS_IMAGE_SET.finditer(text):
        urls.extend(match.group(2) for match in _CSS_STRING.finditer(image_set.group(1)))
    return [f"CSS loads an external resource: {url!r}" for url in urls if _is_external(url)]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_html.py <site_dir>", file=sys.stderr)
        return 2
    problems = []
    checked = 0
    for dirpath, _dirnames, filenames in os.walk(argv[1]):
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ext not in (".html", ".css", ".svg"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            checked += 1
            checker = {".html": check_html, ".css": check_css, ".svg": check_svg}[ext]
            found = checker(text)
            problems.extend(f"{path}: {p}" for p in found)
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"OK: HTML/CSS/SVG policy check passed ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
