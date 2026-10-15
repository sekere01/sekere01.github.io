# Portfolio Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a single-page security portfolio at `https://sekere01.github.io` that serves recruiters, freelance clients and readers.

**Architecture:** Hand-written `index.html` + `styles.css` in a `site/` folder (the only folder published). Two stdlib-only Python check scripts enforce the security and privacy rules (no external resource loads, no inline script/style, CSP present, no phone numbers). A GitHub Actions workflow runs those checks plus a link checker and secret scan, then deploys `site/` with GitHub's official Pages actions.

**Tech Stack:** HTML5, CSS (no framework), Python 3 standard library (`html.parser`, `re`, `unittest`), GitHub Actions, GitHub Pages, lychee (link check), gitleaks (secret scan).

**Spec:** `docs/specs/2026-10-15-portfolio-design.md`

## Global Constraints

- Published files live only in `site/`; nothing outside it is deployed.
- No build step, no npm/Ruby/pip dependencies. Check scripts use the Python standard library only and must run on Python 3.12 (GitHub `ubuntu-latest`) as well as local Python 3.15.
- CSP (exact): `default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'`
- No inline `<script>`, `<style>`, `style=` attributes or `on*=` handlers in published HTML.
- No resource loaded from any external origin; outbound `<a href>` links are allowed.
- No phone number in any published file, including the CV PDF.
- No analytics, trackers or third-party embeds. No web fonts.
- Handi Digital Solutions: generic wording only — no tool names tied to Handi production, no architecture, no internal repo names.
- Every claim matches the corrected CV (Google Doc ID `1gFmOWSUQdJp8ytX0i11K9CX1kwEDdryd0A_I10SumL4`). UBI = "Advanced Stage 8 … (cohort of 2,828 narrowed to 22); 84% average across nine assessed stages". DVWA = "medium-level input-filter bypass (lab)". Reyts = "authorised, in-scope under Amdari hackathon rules of engagement".
- Contact: email `oluwafisayomiadekoya1038@gmail.com`, LinkedIn `https://www.linkedin.com/in/oluwafisayomi-adekoya`, GitHub `https://github.com/sekere01`.
- Every GitHub Action pinned to a full commit SHA (verified 2026-10-15 via `git ls-remote` against the official repos; all are lightweight tags, so the SHA is the commit):

  | Action | Version | Commit SHA |
  |---|---|---|
  | `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
  | `actions/configure-pages` | v6.0.0 | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` |
  | `actions/upload-pages-artifact` | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
  | `actions/deploy-pages` | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |
  | `lycheeverse/lychee-action` | v2.9.0 | `e7477775783ea5526144ba13e8db5eec57747ce8` |
  | `gitleaks/gitleaks-action` | v3.0.0 | `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e` |

  gitleaks-action needs no `GITLEAKS_LICENSE` for a personal account (per its README at that SHA).
- Commit messages carry no AI/Claude attribution.

## Review Focus

1. **SVG and CSS number runs read as phone numbers.** A favicon path like `C50 43 42 51 32 55` is 12 digits separated by spaces and would fail the phone check. Expected: real assets pass. Write SVG coordinates comma-separated, and Task 1 has a test that `M32,10 L50,17 V31 C50,43 42,51 32,55` passes.
2. **CV PDF still contains the phone number.** The regex check cannot read PDF text. Expected: the downloadable CV has no phone. Task 5 verifies the exported PDF by reading its text, and checks for the phone number's digit groups and `+234`.
3. **Link checker fails on the first deploy and on LinkedIn.** `og:image`/`canonical` point at `https://sekere01.github.io/…`, which 404s before the first deploy, and LinkedIn answers bots with HTTP 999. Expected: CI stays green for valid links. Task 6 excludes both patterns, and Task 7 confirms the first run passes.
4. **Header nav overflows a phone screen.** Five nav links don't fit in 360 px. Expected: there's no horizontal scroll on the page; the nav row scrolls on its own. Task 4 checks a 360 px viewport.
5. **A `target="_blank"` link added later without `rel`.** Expected: the check fails the build. Task 2 has a test for it.

---

## File structure

```
sekere01.github.io/
├── site/                         # published — the only folder deployed
│   ├── index.html                # all page content (Task 3)
│   ├── styles.css                # all styling, light/dark tokens (Task 4)
│   └── assets/
│       ├── favicon.svg           # (Task 5)
│       ├── og.png                # 1200×630 link-preview image (Task 5)
│       └── Oluwafisayomi_Adekoya_CV.pdf   # public CV, no phone (Task 5)
├── assets-src/
│   └── og.html                   # source for og.png, not published (Task 5)
├── scripts/checks/
│   ├── check_pii.py              # phone-number scan (Task 1)
│   ├── test_check_pii.py
│   ├── check_html.py             # CSP / external-resource / inline-code policy (Task 2)
│   └── test_check_html.py
├── .github/
│   ├── workflows/deploy.yml      # check → deploy (Task 6)
│   └── dependabot.yml            # (Task 6)
├── .gitignore                    # (Task 1)
├── README.md                     # (Task 1)
└── docs/{specs,plans}/
```

Spec refinements made while planning (spec updated to match):
- Published files sit in `site/` rather than the repo root, so `docs/` and `scripts/` are never deployed.
- On narrow screens the nav becomes a horizontally scrollable row instead of a toggled menu, because a toggle would need JavaScript.

All commands run from the repo root `~/Documents/sekere01.github.io` unless stated.

---

### Task 1: Repo basics and the phone-number check

**Files:**
- Create: `.gitignore`, `README.md`
- Create: `scripts/checks/check_pii.py`
- Test: `scripts/checks/test_check_pii.py`

**Interfaces:**
- Produces: `find_phone_numbers(text: str) -> list[str]`; CLI `python3 scripts/checks/check_pii.py <site_dir>` → exit 0 and prints `OK: phone check passed (N files)`, or exit 1 and prints `<path>: possible phone number: <match>` per hit.

- [ ] **Step 1: Write `.gitignore` and `README.md`**

`.gitignore`:
```
.DS_Store
__pycache__/
*.pyc
lychee/
```

`README.md`:
```markdown
# sekere01.github.io

Source for the portfolio site at https://sekere01.github.io.

- `site/` is the only folder that gets published.
- `scripts/checks/` holds the build checks CI runs before every deploy.
- Preview locally: `python3 -m http.server 8000 -d site`, then open http://localhost:8000
- Run checks locally:
  `python3 -m unittest discover -s scripts/checks -p 'test_*.py' -v && python3 scripts/checks/check_html.py site && python3 scripts/checks/check_pii.py site`
```

- [ ] **Step 2: Write the failing test** — `scripts/checks/test_check_pii.py`

```python
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_pii import find_phone_numbers, scan_dir  # noqa: E402


class FindPhoneNumbersTest(unittest.TestCase):
    def test_detects_nigerian_international_format(self):
        self.assertEqual(find_phone_numbers("Call +234 800 000 0000 today"), ["+234 800 000 0000"])

    def test_detects_local_format(self):
        self.assertEqual(len(find_phone_numbers("tel 08000000000")), 1)

    def test_detects_compact_international(self):
        self.assertEqual(len(find_phone_numbers("+2348000000000")), 1)

    def test_detects_us_style(self):
        self.assertEqual(len(find_phone_numbers("(555) 010-0199")), 1)

    def test_ignores_cv_numbers_and_dates(self):
        text = (
            "Mar 2020 – Jun 2021. Cohort of 2,828 narrowed to 22; 84% average. "
            "GPA 3.80/4.0. NGN 700K–1.2M. Issued Sep 2026. 2026-10-15. CVSS v3.1"
        )
        self.assertEqual(find_phone_numbers(text), [])

    def test_ignores_svg_viewbox_and_comma_paths(self):
        svg = '<svg viewBox="0 0 1200 630"><path d="M32,10 L50,17 V31 C50,43 42,51 32,55 Z"/></svg>'
        self.assertEqual(find_phone_numbers(svg), [])


class ScanDirTest(unittest.TestCase):
    def test_reports_file_with_phone_and_skips_binary(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                f.write("<p>+234 800 000 0000</p>")
            with open(os.path.join(d, "og.png"), "wb") as f:
                f.write(b"\x89PNG 0800 000 0000")
            hits, checked = scan_dir(d)
            self.assertEqual(checked, 1)
            self.assertEqual(len(hits), 1)
            self.assertTrue(hits[0][0].endswith("index.html"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it and confirm it fails**

Run: `python3 -m unittest discover -s scripts/checks -p 'test_check_pii.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'check_pii'`

- [ ] **Step 4: Implement** — `scripts/checks/check_pii.py`

```python
"""Fail if anything that looks like a phone number appears in published text files."""

import os
import re
import sys

# A run of digits, spaces, brackets and hyphens, optionally starting with "+".
# It counts as a phone number when it holds 10–15 digits. Dots are not separators,
# so "Sep 2026. 2026-10-15" is not read as one long number.
_CANDIDATE = re.compile(r"\+?\d[\d\s()-]{8,}\d")
TEXT_EXTENSIONS = {".html", ".css", ".svg", ".txt", ".xml", ".json", ".md", ".webmanifest"}


def find_phone_numbers(text: str) -> list[str]:
    hits = []
    for match in _CANDIDATE.finditer(text):
        candidate = match.group().strip()
        digits = sum(ch.isdigit() for ch in candidate)
        if 10 <= digits <= 15:
            hits.append(candidate)
    return hits


def scan_dir(root: str) -> tuple[list[tuple[str, str]], int]:
    hits = []
    checked = 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() not in TEXT_EXTENSIONS:
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            checked += 1
            hits.extend((path, number) for number in find_phone_numbers(text))
    return hits, checked


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_pii.py <site_dir>", file=sys.stderr)
        return 2
    hits, checked = scan_dir(argv[1])
    for path, number in hits:
        print(f"{path}: possible phone number: {number}")
    if hits:
        return 1
    print(f"OK: phone check passed ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `python3 -m unittest discover -s scripts/checks -p 'test_check_pii.py' -v`
Expected: 7 tests, `OK`

- [ ] **Step 6: Commit**

```bash
git add .gitignore README.md scripts/checks/check_pii.py scripts/checks/test_check_pii.py
git commit -m "build: add phone-number check for published files"
```

---

### Task 2: HTML/CSS policy check

**Files:**
- Create: `scripts/checks/check_html.py`
- Test: `scripts/checks/test_check_html.py`

**Interfaces:**
- Produces: `EXPECTED_CSP: str`; `check_html(text: str) -> list[str]`; `check_css(text: str) -> list[str]`; CLI `python3 scripts/checks/check_html.py <site_dir>` → exit 0 with `OK: HTML/CSS policy check passed (N files)`, or exit 1 with `<path>: <problem>` lines.

- [ ] **Step 1: Write the failing test** — `scripts/checks/test_check_html.py`

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_html import EXPECTED_CSP, check_css, check_html  # noqa: E402

CSP_META = f'<meta http-equiv="Content-Security-Policy" content="{EXPECTED_CSP}">'


def page(head_extra: str = "", body: str = "<p>hi</p>") -> str:
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">{CSP_META}'
        f'<link rel="stylesheet" href="styles.css">{head_extra}</head><body>{body}</body></html>'
    )


class CheckHtmlTest(unittest.TestCase):
    def test_clean_page_passes(self):
        self.assertEqual(check_html(page()), [])

    def test_outbound_links_are_allowed(self):
        self.assertEqual(check_html(page(body='<a href="https://github.com/sekere01">GitHub</a>')), [])

    def test_missing_csp_fails(self):
        html = '<html><head><link rel="stylesheet" href="styles.css"></head><body></body></html>'
        self.assertTrue(any("CSP" in e for e in check_html(html)))

    def test_wrong_csp_fails(self):
        html = page().replace("default-src 'none'", "default-src *")
        self.assertTrue(any("CSP" in e for e in check_html(html)))

    def test_resource_before_csp_fails(self):
        html = (
            '<html><head><link rel="stylesheet" href="styles.css">'
            f"{CSP_META}</head><body></body></html>"
        )
        self.assertTrue(any("before the CSP" in e for e in check_html(html)))

    def test_external_stylesheet_fails(self):
        errors = check_html(page('<link rel="stylesheet" href="https://fonts.googleapis.com/css2">'))
        self.assertTrue(any("external" in e for e in errors))

    def test_protocol_relative_image_fails(self):
        errors = check_html(page(body='<img src="//cdn.example.com/a.png" alt="a">'))
        self.assertTrue(any("external" in e for e in errors))

    def test_external_srcset_fails(self):
        errors = check_html(page(body='<img src="a.png" srcset="https://x.example/a.png 2x" alt="a">'))
        self.assertTrue(any("external" in e for e in errors))

    def test_canonical_link_is_not_a_resource(self):
        self.assertEqual(check_html(page('<link rel="canonical" href="https://sekere01.github.io/">')), [])

    def test_inline_script_fails(self):
        self.assertTrue(any("inline <script>" in e for e in check_html(page(body="<script>alert(1)</script>"))))

    def test_external_script_fails(self):
        errors = check_html(page(body='<script src="https://evil.example/x.js"></script>'))
        self.assertTrue(any("external" in e for e in errors))

    def test_style_element_fails(self):
        self.assertTrue(any("<style>" in e for e in check_html(page("<style>p{}</style>"))))

    def test_style_attribute_fails(self):
        self.assertTrue(any("style=" in e for e in check_html(page(body='<p style="color:red">x</p>'))))

    def test_event_handler_fails(self):
        self.assertTrue(any("onclick" in e for e in check_html(page(body='<a href="#" onclick="x()">x</a>'))))

    def test_javascript_url_fails(self):
        self.assertTrue(any("javascript:" in e for e in check_html(page(body='<a href="javascript:x()">x</a>'))))

    def test_target_blank_without_rel_fails(self):
        errors = check_html(page(body='<a href="https://x.example" target="_blank">x</a>'))
        self.assertTrue(any("noopener" in e for e in errors))

    def test_target_blank_with_rel_passes(self):
        body = '<a href="https://x.example" target="_blank" rel="noopener noreferrer">x</a>'
        self.assertEqual(check_html(page(body=body)), [])

    def test_img_without_alt_fails(self):
        self.assertTrue(any("alt" in e for e in check_html(page(body='<img src="a.png">'))))


class CheckCssTest(unittest.TestCase):
    def test_local_url_passes(self):
        self.assertEqual(check_css("a { background: url('assets/x.png'); }"), [])

    def test_external_url_fails(self):
        self.assertTrue(check_css('a { background: url("https://x.example/a.png"); }'))

    def test_external_import_fails(self):
        self.assertTrue(check_css('@import url("https://fonts.googleapis.com/css2");'))

    def test_bare_external_import_fails(self):
        self.assertTrue(check_css('@import "//cdn.example.com/x.css";'))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `python3 -m unittest discover -s scripts/checks -p 'test_check_html.py' -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'check_html'`

- [ ] **Step 3: Implement** — `scripts/checks/check_html.py`

```python
"""Enforce the site's CSP-related rules on published HTML and CSS files."""

import os
import re
import sys
from html.parser import HTMLParser

EXPECTED_CSP = (
    "default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; "
    "base-uri 'none'; form-action 'none'"
)

# <link rel=...> values that make the browser fetch something.
LOADING_LINK_RELS = {"stylesheet", "icon", "apple-touch-icon", "preload", "modulepreload",
                     "manifest", "prefetch", "mask-icon"}
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
}


def _normalise_csp(value: str) -> str:
    return " ".join(value.split()).rstrip(";").strip()


def _is_external(url: str) -> bool:
    u = url.strip().lower()
    return u.startswith(("http://", "https://", "//", "data:"))


def _srcset_urls(value: str) -> list[str]:
    return [part.strip().split()[0] for part in value.split(",") if part.strip()]


class _Checker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.saw_csp = False
        self._in_script = False
        self._script_has_src = False
        self._script_text = ""

    def _resource(self, tag: str, attr: str, url: str) -> None:
        if not self.saw_csp:
            self.errors.append(f"<{tag} {attr}={url!r}> loads before the CSP meta tag")
        if _is_external(url):
            self.errors.append(f"<{tag} {attr}={url!r}> loads an external resource")

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        for name in a:
            if name.startswith("on"):
                self.errors.append(f"<{tag}> has inline event handler {name}=")
        if "style" in a:
            self.errors.append(f"<{tag}> has inline style= attribute")
        if tag == "style":
            self.errors.append("<style> element (inline CSS is blocked by the CSP)")
        if tag == "meta" and a.get("http-equiv", "").lower() == "content-security-policy":
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

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            if not self._script_has_src:
                self.errors.append("inline <script> (blocked by the CSP)")
            self._in_script = False


def check_html(text: str) -> list[str]:
    checker = _Checker()
    checker.feed(text)
    checker.close()
    if not checker.saw_csp:
        checker.errors.append("no CSP meta tag found")
    return checker.errors


_CSS_URL = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""", re.IGNORECASE)
_CSS_IMPORT = re.compile(r"""@import\s+(['"])(.*?)\1""", re.IGNORECASE)


def check_css(text: str) -> list[str]:
    errors = []
    for pattern in (_CSS_URL, _CSS_IMPORT):
        for match in pattern.finditer(text):
            url = match.group(2)
            if _is_external(url):
                errors.append(f"CSS loads an external resource: {url!r}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_html.py <site_dir>", file=sys.stderr)
        return 2
    problems = []
    checked = 0
    for dirpath, _dirnames, filenames in os.walk(argv[1]):
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ext not in (".html", ".css"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            checked += 1
            found = check_html(text) if ext == ".html" else check_css(text)
            problems.extend(f"{path}: {p}" for p in found)
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"OK: HTML/CSS policy check passed ({checked} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python3 -m unittest discover -s scripts/checks -p 'test_*.py' -v`
Expected: 29 tests (22 html/css + 7 pii), `OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/checks/check_html.py scripts/checks/test_check_html.py
git commit -m "build: add HTML/CSS policy check (CSP, external loads, inline code)"
```

---

### Task 3: Page content (`site/index.html`)

**Files:**
- Create: `site/index.html`

**Interfaces:**
- Consumes: `check_html.py`, `check_pii.py` (Tasks 1–2).
- Produces: class names that Task 4 styles: `skip-link`, `site-header`, `header-inner`, `brand`, `nav-list`, `container`, `hero`, `headline`, `pitch`, `cta-row`, `button`, `button-primary`, `button-secondary`, `section-label`, `grid`, `card`, `cert-featured`, `meta`, `tags`, `card-links`, `timeline`, `cert-list`, `contact-lead`, `contact-links`, `site-footer`. Asset paths that Task 5 creates: `assets/favicon.svg`, `assets/og.png`, `assets/Oluwafisayomi_Adekoya_CV.pdf`.

- [ ] **Step 1: Confirm every linked repo is public**

Run:
```bash
for r in Black-Box_Pentest_Reyts_Fintech active-directory-attack-lab KYC_FRAUD_REPORT DVWA-Medium-Level-SQL-Injection-Assessment internal-portal-access-control-audit splunk-siem-sophos-integration enterprise-pki-tls-ssh-security-lab; do printf "%s " $r; curl -s -o /dev/null -w "%{http_code}\n" https://github.com/sekere01/$r; done
```
Expected: `200` for all seven (confirmed 2026-10-15). If any is not 200, stop and ask whether to make it public or drop its link.

- [ ] **Step 2: Write `site/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Oluwafisayomi Adekoya — Penetration Tester &amp; Security Engineer</title>
  <meta name="description" content="Penetration tester, security engineer and purple teamer. Full attack chains, CVSS-scored reports and SIEM detection rules. Open to full-time roles and freelance engagements.">
  <link rel="canonical" href="https://sekere01.github.io/">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="styles.css">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Oluwafisayomi Adekoya — Penetration Tester &amp; Security Engineer">
  <meta property="og:description" content="Offensive security and detection engineering: full attack chains, CVSS-scored reports, and SIEM detection rules.">
  <meta property="og:url" content="https://sekere01.github.io/">
  <meta property="og:image" content="https://sekere01.github.io/assets/og.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Oluwafisayomi Adekoya — Penetration Tester, Security Engineer, Purple Team">
  <meta name="twitter:card" content="summary_large_image">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="#top">Oluwafisayomi Adekoya</a>
      <nav aria-label="Sections">
        <ul class="nav-list">
          <li><a href="#services">Services</a></li>
          <li><a href="#projects">Projects</a></li>
          <li><a href="#experience">Experience</a></li>
          <li><a href="#certifications">Certs</a></li>
          <li><a href="#contact">Contact</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main id="main">
    <section id="top" class="hero" aria-labelledby="hero-title">
      <div class="container">
        <h1 id="hero-title">Oluwafisayomi Adekoya</h1>
        <p class="headline">Penetration Tester | Security Engineer | Purple Team</p>
        <p class="pitch">Offensive security and detection engineering: full attack chains, CVSS-scored reports, and SIEM detection rules.</p>
        <div class="cta-row">
          <a class="button button-primary" href="#projects">See my work</a>
          <a class="button button-secondary" href="#contact">Work with me</a>
          <a class="button button-secondary" href="assets/Oluwafisayomi_Adekoya_CV.pdf" download>Download CV (PDF)</a>
        </div>
      </div>
    </section>

    <section id="services" aria-labelledby="services-title">
      <div class="container">
        <p class="section-label">01 / Services</p>
        <h2 id="services-title">What I do</h2>
        <div class="grid">
          <article class="card">
            <h3>Penetration testing</h3>
            <p>Black-box and internal testing of web applications, Active Directory and networks, from recon to full attack chain, delivered as CVSS v3.1-scored reports with a prioritised remediation roadmap.</p>
          </article>
          <article class="card">
            <h3>DevSecOps pipelines</h3>
            <p>CI/CD pipeline security: SAST, SCA, secret and DAST gating with Semgrep, Trivy, Gitleaks and OWASP ZAP, plus SBOM and CVE tracking.</p>
          </article>
          <article class="card">
            <h3>Detection engineering</h3>
            <p>Wazuh and Splunk detection rules, tuned for false positives and negatives, with attacker techniques mapped to MITRE ATT&amp;CK and fed back into detection.</p>
          </article>
        </div>
      </div>
    </section>

    <section id="projects" aria-labelledby="projects-title">
      <div class="container">
        <p class="section-label">02 / Proof of work</p>
        <h2 id="projects-title">Projects &amp; write-ups</h2>
        <div class="grid">
          <article class="card">
            <h3>Black-Box Penetration Test: Reyts Fintech</h3>
            <p class="meta">Mar 2026 · Hackathon, live target</p>
            <p>Black-box test of a live fintech target (authorised, in-scope under Amdari hackathon rules of engagement). Found 7 vulnerabilities (2 Critical, 3 High, 1 Medium, 1 Low) across DNS, email infrastructure and Active Directory, delivered in a CVSS v3.1-scored report.</p>
            <ul class="tags" aria-label="Techniques">
              <li>Recon</li><li>SPF/DMARC</li><li>Active Directory</li><li>CVSS v3.1</li>
            </ul>
            <div class="card-links">
              <a href="https://github.com/sekere01/Black-Box_Pentest_Reyts_Fintech">Read the Reyts write-up on GitHub</a>
            </div>
          </article>
          <article class="card">
            <h3>Active Directory Attack Lab: Full Domain Compromise</h3>
            <p class="meta">2026 · Lab</p>
            <p>Simulated an internal attacker against a Windows Server 2025 AD environment: AS-REP Roasting, Pass-the-Hash lateral movement and BloodHound path analysis, ending in domain-level access via NTDS.dit extraction.</p>
            <ul class="tags" aria-label="Techniques">
              <li>AS-REP Roasting</li><li>Pass-the-Hash</li><li>BloodHound</li><li>Impacket</li>
            </ul>
            <div class="card-links">
              <a href="https://github.com/sekere01/active-directory-attack-lab">Read the AD attack lab write-up on GitHub</a>
            </div>
          </article>
          <article class="card">
            <h3>KYC Fraud &amp; Threat Intelligence Analysis: Reyts Fintech</h3>
            <p class="meta">Mar 2026 · Threat intelligence</p>
            <p>Analysed KYC anomaly logs to cluster suspicious IPs and detect device-fingerprint reuse, matched attacker infrastructure to Tor exit-node IoC feeds, and mapped TTPs to MITRE ATT&amp;CK.</p>
            <ul class="tags" aria-label="Techniques">
              <li>Fraud analysis</li><li>IoC matching</li><li>MITRE ATT&amp;CK</li>
            </ul>
            <div class="card-links">
              <a href="https://github.com/sekere01/KYC_FRAUD_REPORT">Read the KYC fraud report on GitHub</a>
            </div>
          </article>
          <article class="card">
            <h3>Web Application Security Assessments</h3>
            <p class="meta">2026 · Lab</p>
            <p>SQL injection via a medium-level input-filter bypass (lab) in DVWA, using manual techniques and SQLMap. Broken Access Control (IDOR, OWASP A01:2021) in a simulated internal portal, found with Burp Suite.</p>
            <ul class="tags" aria-label="Techniques">
              <li>SQL injection</li><li>IDOR</li><li>Burp Suite</li><li>SQLMap</li>
            </ul>
            <div class="card-links">
              <a href="https://github.com/sekere01/DVWA-Medium-Level-SQL-Injection-Assessment">Read the DVWA SQL injection write-up on GitHub</a>
              <a href="https://github.com/sekere01/internal-portal-access-control-audit">Read the access-control audit on GitHub</a>
            </div>
          </article>
          <article class="card">
            <h3>Enterprise Security Operations Lab</h3>
            <p class="meta">2025 · Lab</p>
            <p>Deployed Splunk SIEM with Sophos Central and tuned detection rules to cut false positives by approximately 65%. Designed a 4-phase PKI environment and validated TLS 1.3 forward secrecy in Wireshark.</p>
            <ul class="tags" aria-label="Techniques">
              <li>Splunk</li><li>Sophos Central</li><li>PKI</li><li>TLS 1.3</li>
            </ul>
            <div class="card-links">
              <a href="https://github.com/sekere01/splunk-siem-sophos-integration">Read the Splunk and Sophos write-up on GitHub</a>
              <a href="https://github.com/sekere01/enterprise-pki-tls-ssh-security-lab">Read the PKI and TLS lab write-up on GitHub</a>
            </div>
          </article>
          <article class="card">
            <h3>TryHackMe Practical Labs</h3>
            <p class="meta">2026 · 30-day streak, 48 rooms</p>
            <p>48 rooms across offensive and defensive tracks: SSRF, PHP backdoor exploitation, XOR cryptanalysis, SQL injection, SUID/sudo privilege escalation, and multi-stage CTF chains (Olympus, Overpass, Mr. Robot, Lookup).</p>
            <ul class="tags" aria-label="Techniques">
              <li>SSRF</li><li>Privilege escalation</li><li>CTF</li>
            </ul>
          </article>
        </div>
      </div>
    </section>

    <section id="experience" aria-labelledby="experience-title">
      <div class="container">
        <p class="section-label">03 / Experience</p>
        <h2 id="experience-title">Experience</h2>
        <ol class="timeline">
          <li>
            <h3>Security Engineer · Handi Digital Solutions LTD</h3>
            <p class="meta">Jul 2026 – Present · Hybrid</p>
            <p>Building CI/CD pipeline security, centralised monitoring and detection, and infrastructure hardening.</p>
          </li>
          <li>
            <h3>Ethical Hacking Track · The Root Access Network (T.R.A.N)</h3>
            <p class="meta">May 2026 – Sep 2026 · Remote</p>
            <p>Reached Advanced Stage 8 of the UBI Ethical Hacking Track (cohort of 2,828 narrowed to 22); 84% average across nine assessed stages.</p>
          </li>
          <li>
            <h3>Cybersecurity Intern, Security Team · Expadox Lab</h3>
            <p class="meta">May 2026 – Jul 2026 · Remote</p>
            <p>STRIDE threat modelling, application security scanning and Wazuh SIEM detection rules for the OpsShield capstone product.</p>
          </li>
          <li>
            <h3>Security &amp; IT Operations Lead · Levi's Acre Farms and Foods</h3>
            <p class="meta">Mar 2023 – Feb 2026 · Lagos</p>
            <p>Web application vulnerability mitigation and least-privilege IAM governance.</p>
          </li>
          <li>
            <h3>IT Support Specialist · Grola Tech Limited</h3>
            <p class="meta">Mar 2020 – Jun 2021 · Lagos</p>
            <p>Endpoint security and system hardening across 30+ Windows and Linux systems.</p>
          </li>
          <li>
            <h3>IT Infrastructure Intern · Tenece Professional Services</h3>
            <p class="meta">Aug 2017 – Aug 2018 · Lagos</p>
            <p>Enterprise server maintenance and client-side infrastructure security.</p>
          </li>
        </ol>
      </div>
    </section>

    <section id="certifications" aria-labelledby="certifications-title">
      <div class="container">
        <p class="section-label">04 / Certifications</p>
        <h2 id="certifications-title">Certifications &amp; training</h2>
        <div class="grid">
          <article class="card cert-featured">
            <h3>Certified Penetration Testing Professional (CPENT) v2</h3>
            <p class="meta">EC-Council · Issued Sep 2026</p>
          </article>
          <article class="card">
            <h3>OSCP+</h3>
            <p class="meta">OffSec · Planned</p>
          </article>
        </div>
        <ul class="cert-list">
          <li>Google Professional Certificate in Cybersecurity (SQL, Linux, Python)</li>
          <li>Palo Alto Networks PSE: Endpoint, Platform &amp; Foundation</li>
          <li>Diploma in Cybersecurity (GPA 3.80/4.0), AltSchool Africa</li>
          <li>Introduction to Cybersecurity (Cisco) · ManageEngine UEM Technical Training · Certified Cybersecurity Educator Professional (CCEP)</li>
          <li>Industry simulations (Forage): Datacom · AIG · Mastercard · Deloitte Australia · Telstra · Tata Group</li>
        </ul>
      </div>
    </section>

    <section id="contact" aria-labelledby="contact-title">
      <div class="container">
        <p class="section-label">05 / Contact</p>
        <h2 id="contact-title">Work with me</h2>
        <p class="contact-lead">Open to full-time roles and freelance engagements in penetration testing, DevSecOps and detection engineering.</p>
        <ul class="contact-links">
          <li><a href="mailto:oluwafisayomiadekoya1038@gmail.com">Email: oluwafisayomiadekoya1038@gmail.com</a></li>
          <li><a href="https://www.linkedin.com/in/oluwafisayomi-adekoya">LinkedIn: /in/oluwafisayomi-adekoya</a></li>
          <li><a href="https://github.com/sekere01">GitHub: sekere01</a></li>
        </ul>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <p>© 2026 Oluwafisayomi Adekoya</p>
      <p>No trackers, no third-party scripts. <a href="https://github.com/sekere01/sekere01.github.io">View this site's source on GitHub</a></p>
    </div>
  </footer>
</body>
</html>
```

- [ ] **Step 3: Run both checks against `site/`**

Run: `python3 scripts/checks/check_html.py site && python3 scripts/checks/check_pii.py site`
Expected:
```
OK: HTML/CSS policy check passed (1 files)
OK: phone check passed (1 files)
```

- [ ] **Step 4: Content audit against the corrected CV**

Read the corrected CV with Google Drive `read_file_content` (file ID `1gFmOWSUQdJp8ytX0i11K9CX1kwEDdryd0A_I10SumL4`). For every number, date, title and claim in `site/index.html`, confirm it appears in the CV with the same meaning. Pay particular attention to:
- 7 vulnerabilities (2 Critical, 3 High, 1 Medium, 1 Low)
- ~65%
- 30+ systems
- 48 rooms
- 2,828 → 22, 84%
- GPA 3.80
- every date range

Confirm the Handi line names no tools or systems. Expected: no mismatches. Fix any mismatch in the HTML (never in the CV) and rerun Step 3.

- [ ] **Step 5: Commit**

```bash
git add site/index.html
git commit -m "feat: add portfolio page content"
```

---

### Task 4: Styling, themes and responsive layout (`site/styles.css`)

**Files:**
- Create: `site/styles.css`

**Interfaces:**
- Consumes: class names listed in Task 3's Produces.

- [ ] **Step 1: Write `site/styles.css`**

```css
:root {
  color-scheme: dark light;
  --bg: #0d1117;
  --surface: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #9da7b3;
  --accent: #2dd4bf;
  --accent-contrast: #0d1117;
  --tag-bg: #1f2a2e;
  --radius: 10px;
  --max: 72rem;
  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #ffffff;
    --surface: #f6f8fa;
    --border: #d0d7de;
    --text: #1f2328;
    --muted: #57606a;
    --accent: #0f766e;
    --accent-contrast: #ffffff;
    --tag-bg: #e6f4f1;
  }
}

*, *::before, *::after { box-sizing: border-box; }

html { scroll-behavior: smooth; scroll-padding-top: 5rem; }

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { transition: none !important; animation: none !important; }
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 1.0625rem;
  line-height: 1.6;
}

img { max-width: 100%; height: auto; }

a { color: var(--accent); text-underline-offset: 0.2em; }
a:hover { text-decoration-thickness: 2px; }

:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; border-radius: 4px; }

.container { width: 100%; max-width: var(--max); margin: 0 auto; padding: 0 1rem; }

.skip-link {
  position: absolute;
  left: 1rem;
  top: -4rem;
  z-index: 100;
  padding: 0.5rem 1rem;
  background: var(--accent);
  color: var(--accent-contrast);
  border-radius: var(--radius);
}
.skip-link:focus { top: 1rem; }

.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}
.header-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.25rem 1.5rem;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}
.header-inner nav { min-width: 0; max-width: 100%; }
.brand { color: var(--text); font-weight: 700; text-decoration: none; }
.nav-list {
  display: flex;
  gap: 1.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
  overflow-x: auto;
}
.nav-list a {
  display: inline-block;
  padding: 0.25rem 0;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  text-decoration: none;
  white-space: nowrap;
}
.nav-list a:hover { color: var(--text); }

section { padding: 4rem 0; }
h1, h2, h3 { line-height: 1.2; }
h2 { font-size: clamp(1.5rem, 1.2rem + 1.2vw, 2rem); margin: 0 0 1.5rem; }

.section-label {
  margin: 0 0 0.5rem;
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero { padding: 5rem 0 4rem; }
.hero h1 { font-size: clamp(2.25rem, 1.5rem + 3vw, 3.5rem); margin: 0 0 0.5rem; }
.headline { margin: 0 0 1rem; color: var(--accent); font-family: var(--font-mono); }
.pitch { max-width: 40rem; margin: 0 0 2rem; color: var(--muted); font-size: 1.125rem; }

.cta-row { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.button {
  display: inline-block;
  padding: 0.75rem 1.25rem;
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  font-weight: 600;
  text-decoration: none;
}
.button-primary { background: var(--accent); color: var(--accent-contrast); }
.button-secondary { color: var(--accent); }

.grid { display: grid; gap: 1rem; grid-template-columns: 1fr; }
@media (min-width: 40rem) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 64rem) { .grid { grid-template-columns: repeat(3, 1fr); } }

.card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.card h3 { margin: 0; font-size: 1.125rem; }
.card p { margin: 0; }
.cert-featured { border-color: var(--accent); }

.meta { color: var(--muted); font-family: var(--font-mono); font-size: 0.8125rem; }

.tags { display: flex; flex-wrap: wrap; gap: 0.375rem; margin: 0; padding: 0; list-style: none; }
.tags li {
  padding: 0.125rem 0.625rem;
  background: var(--tag-bg);
  color: var(--text);
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.card-links { display: flex; flex-direction: column; gap: 0.25rem; margin-top: auto; }

.timeline { margin: 0; padding: 0; list-style: none; border-left: 2px solid var(--border); }
.timeline li { position: relative; padding: 0 0 1.5rem 1.25rem; }
.timeline li::before {
  content: "";
  position: absolute;
  left: -7px;
  top: 0.4rem;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent);
}
.timeline h3 { margin: 0; font-size: 1.0625rem; }
.timeline p { margin: 0.25rem 0 0; }
.timeline p:last-child { color: var(--muted); }

.cert-list { margin: 1.5rem 0 0; padding-left: 1.25rem; color: var(--muted); }
.cert-list li + li { margin-top: 0.25rem; }

.contact-lead { max-width: 40rem; margin: 0; color: var(--muted); }
.contact-links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 1.5rem 0 0;
  padding: 0;
  list-style: none;
  font-size: 1.125rem;
}
.contact-links a { overflow-wrap: anywhere; }

.site-footer { padding: 2rem 0; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.875rem; }
.site-footer p { margin: 0 0 0.25rem; }
```

- [ ] **Step 2: Run the checks**

Run: `python3 -m unittest discover -s scripts/checks -p 'test_*.py' && python3 scripts/checks/check_html.py site && python3 scripts/checks/check_pii.py site`
Expected: tests `OK`; `OK: HTML/CSS policy check passed (2 files)`; `OK: phone check passed (2 files)`

- [ ] **Step 3: Visual and accessibility check in the browser**

Run `python3 -m http.server 8000 -d site` (leave it running) and open http://localhost:8000 in Chrome. Check:
1. **DevTools Console:** no CSP violation errors. The favicon/og/PDF 404s are expected until Task 5.
2. **Device toolbar at 360 px wide:**
   - no horizontal page scroll (`document.documentElement.scrollWidth <= 360` in the Console)
   - the nav row scrolls on its own
   - the email address wraps
3. **Keyboard:** the first Tab shows "Skip to content"; Enter jumps to main; focus outlines are visible on every link.
4. **Lighthouse (Navigation, Mobile)** in the default dark theme: Accessibility, Best Practices and SEO all ≥ 95.
5. **Light theme:** Rendering panel → "Emulate CSS media feature prefers-color-scheme: light", then rerun Lighthouse Accessibility. Expected ≥ 95 with no contrast failures.
6. **Reduced motion:** Rendering panel → `prefers-reduced-motion: reduce`, then click a nav link. Expected: it jumps without smooth scrolling.

If any check fails, fix `styles.css` (not the colours' roles) and repeat Steps 2–3.

- [ ] **Step 4: Commit**

```bash
git add site/styles.css
git commit -m "feat: add site styles with dark/light themes and responsive grid"
```

---

### Task 5: Assets — favicon, link-preview image, public CV PDF

**Files:**
- Create: `site/assets/favicon.svg`
- Create: `assets-src/og.html`, `site/assets/og.png`
- Create: `site/assets/Oluwafisayomi_Adekoya_CV.pdf`

**Interfaces:**
- Consumes: asset paths referenced in `site/index.html` (Task 3).

- [ ] **Step 1: Write `site/assets/favicon.svg`** (comma-separated coordinates — see Review Focus #1)

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0d1117"/><path d="M32,10 L50,17 V31 C50,43 42,51 32,55 C22,51 14,43 14,31 V17 Z" fill="none" stroke="#2dd4bf" stroke-width="4" stroke-linejoin="round"/></svg>
```

- [ ] **Step 2: Write `assets-src/og.html`** (not published, so inline styles are fine here)

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; }
    body {
      display: flex; flex-direction: column; justify-content: center; padding: 0 96px; box-sizing: border-box;
      background: #0d1117; color: #e6edf3; font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      border-left: 16px solid #2dd4bf;
    }
    h1 { font-size: 72px; line-height: 1.1; margin: 0 0 24px; }
    p { margin: 0; }
    .role { font-family: ui-monospace, Menlo, Consolas, monospace; color: #2dd4bf; font-size: 34px; margin-bottom: 32px; }
    .pitch { color: #9da7b3; font-size: 30px; max-width: 900px; line-height: 1.4; }
    .url { position: absolute; bottom: 48px; right: 96px; font-family: ui-monospace, Menlo, Consolas, monospace; color: #9da7b3; font-size: 26px; }
  </style>
</head>
<body>
  <h1>Oluwafisayomi Adekoya</h1>
  <p class="role">Penetration Tester | Security Engineer | Purple Team</p>
  <p class="pitch">Full attack chains, CVSS-scored reports, and SIEM detection rules.</p>
  <p class="url">sekere01.github.io</p>
</body>
</html>
```

- [ ] **Step 3: Render `og.png` with headless Chrome and check its size**

```bash
mkdir -p site/assets
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --hide-scrollbars \
  --window-size=1200,630 --screenshot="$PWD/site/assets/og.png" "file://$PWD/assets-src/og.html"
sips -g pixelWidth -g pixelHeight site/assets/og.png
```
Expected: `pixelWidth: 1200`, `pixelHeight: 630`. Open the PNG and check the text isn't cut off. If the height is off, retry with `--window-size=1200,630 --force-device-scale-factor=1`.

- [ ] **Step 4: Make a public copy of the CV without the phone number**

Using the Google Drive and Google Docs connectors (load the `anthropic-skills:google-workspace` skill first):
1. `copy_file` the corrected CV (`1gFmOWSUQdJp8ytX0i11K9CX1kwEDdryd0A_I10SumL4`) with title `Oluwafisayomi_Adekoya CV (public, no phone)`.
2. On the new copy only, `update_doc` with one `replaceAllText`: find the phone number together with the `  |  ` separator after it (match case, copy it exactly from the doc), replace with an empty string.
3. `read_file_content` on the copy. Confirm the contact line reads `Lagos, Nigeria  |  oluwafisayomiadekoya1038@gmail.com  |  linkedin.com/in/oluwafisayomi-adekoya  |  github.com/sekere01`.

If the connectors are unavailable, ask Oluwafisayomi to make the copy and delete the phone number by hand. Never edit the corrected CV itself.

- [ ] **Step 5: Export the public copy to PDF**

`download_file_content` on the public copy with `exportMimeType: "application/pdf"`, then decode the base64 into `site/assets/Oluwafisayomi_Adekoya_CV.pdf`. If the result is saved to a file, decode with `base64 -D -i <saved-file> -o site/assets/Oluwafisayomi_Adekoya_CV.pdf`, extracting the base64 field first if the file is JSON.
Check: `head -c 5 site/assets/Oluwafisayomi_Adekoya_CV.pdf` prints `%PDF-`.

- [ ] **Step 6: Verify the PDF has no phone number** (Review Focus #2)

Read `site/assets/Oluwafisayomi_Adekoya_CV.pdf` with the Read tool, or open it in Preview and search with ⌘F. Search for each digit group of the phone number and for `+234`. Expected: none found. Confirm the PDF content matches the corrected CV apart from the phone number.

- [ ] **Step 7: Run checks and look at the page again**

Run: `python3 scripts/checks/check_html.py site && python3 scripts/checks/check_pii.py site`
Expected: `OK: HTML/CSS policy check passed (2 files)`; `OK: phone check passed (3 files)` (index.html, styles.css, favicon.svg)
Reload http://localhost:8000. Expected:
- the favicon shows in the tab
- no 404s in the Network panel
- "Download CV (PDF)" downloads the PDF

- [ ] **Step 8: Commit**

```bash
git add site/assets/favicon.svg site/assets/og.png site/assets/Oluwafisayomi_Adekoya_CV.pdf assets-src/og.html
git commit -m "feat: add favicon, link-preview image and public CV"
```

---

### Task 6: CI workflow and Dependabot

**Files:**
- Create: `.github/workflows/deploy.yml`
- Create: `.github/dependabot.yml`

**Interfaces:**
- Consumes: `scripts/checks/*.py` CLIs (Tasks 1–2), `site/` (Tasks 3–5).
- Produces: job ids `check` and `deploy`. Task 7's branch protection requires the status check named `check`.

- [ ] **Step 1: Write `.github/workflows/deploy.yml`**

```yaml
name: Check and deploy

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: pages-${{ github.ref }}
  cancel-in-progress: false

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0 # full history for the secret scan
          persist-credentials: false

      - name: Unit tests for the check scripts
        run: python3 -m unittest discover -s scripts/checks -p 'test_*.py' -v

      - name: HTML/CSS policy check
        run: python3 scripts/checks/check_html.py site

      - name: Phone-number check
        run: python3 scripts/checks/check_pii.py site

      - name: Link check
        uses: lycheeverse/lychee-action@e7477775783ea5526144ba13e8db5eec57747ce8 # v2.9.0
        with:
          # LinkedIn answers bots with HTTP 999; the site's own URL 404s until the first deploy.
          args: >-
            --no-progress
            --exclude 'linkedin\.com'
            --exclude '^https://sekere01\.github\.io'
            'site/**/*.html'
          fail: true

      - name: Secret scan
        uses: gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e # v3.0.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  deploy:
    needs: check
    if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false

      - uses: actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0

      - uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: site

      - id: deployment
        uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1
```

- [ ] **Step 2: Write `.github/dependabot.yml`**

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

- [ ] **Step 3: Validate both files parse as YAML and every `uses:` is SHA-pinned**

```bash
ruby -ryaml -e 'ARGV.each { |f| YAML.load_file(f); puts "parsed #{f}" }' .github/workflows/deploy.yml .github/dependabot.yml
grep -nE '^\s*-?\s*uses:' .github/workflows/deploy.yml | grep -vE '@[0-9a-f]{40} # v[0-9.]+$' && echo "UNPINNED ACTION FOUND" || echo "all actions SHA-pinned"
```
Expected: `parsed …` for both files, then `all actions SHA-pinned`.

- [ ] **Step 4: Re-confirm the pinned SHAs still match their tags** (they may have moved since planning)

```bash
check(){ printf "%s %s -> " "$1" "$2"; git ls-remote "https://github.com/$1.git" "refs/tags/$2" | cut -f1; }
check actions/checkout v7.0.1; check actions/configure-pages v6.0.0; check actions/upload-pages-artifact v5.0.0
check actions/deploy-pages v5.0.1; check lycheeverse/lychee-action v2.9.0; check gitleaks/gitleaks-action v3.0.0
```
Expected: each SHA equals the one in Global Constraints. If a tag now points elsewhere, stop and report it. A moved tag is a supply-chain warning sign, not something to "fix" by updating the pin.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/deploy.yml .github/dependabot.yml
git commit -m "ci: add check-then-deploy workflow with SHA-pinned actions and Dependabot"
```

---

### Task 7: Publish to GitHub and enable Pages

**This task is outward-facing. It creates a public repo and publishes the site. Ask Oluwafisayomi for an explicit go-ahead before Step 2.**

**Files:** none (repository settings only)

**Interfaces:**
- Consumes: the `check` job name (Task 6).

- [ ] **Step 1: Final local gate**

```bash
python3 -m unittest discover -s scripts/checks -p 'test_*.py' && python3 scripts/checks/check_html.py site && python3 scripts/checks/check_pii.py site && git status --short
```
Expected: all `OK`, and `git status` prints nothing (clean tree). Run `git log --format='%an <%ae>%n%B' | grep -iE 'claude|co-authored|anthropic'`. Expected: no output.

- [ ] **Step 2: Create the public repo (after go-ahead) and turn on Pages with the Actions source**

```bash
gh repo create sekere01/sekere01.github.io --public --source=. --remote=origin --description "Portfolio: penetration testing, DevSecOps and detection engineering"
gh api -X POST repos/sekere01/sekere01.github.io/pages -f build_type=workflow
```
Expected: the repo is created; the Pages API returns JSON with `"build_type": "workflow"`. If the Pages call fails because the repo is empty, push first (Step 3), run this call, then `gh run rerun --failed`.

- [ ] **Step 3: Push and watch the first run**

```bash
git push -u origin main
gh run watch --exit-status "$(gh run list --workflow deploy.yml --limit 1 --json databaseId -q '.[0].databaseId')"
```
Expected: `check` and `deploy` both succeed. If lychee fails, read which URL failed. A real dead link means fixing the HTML; never widen `--exclude` to hide it.

- [ ] **Step 4: Protect `main`**

```bash
gh api -X PUT repos/sekere01/sekere01.github.io/branches/main/protection --input - <<'EOF'
{
  "required_status_checks": { "strict": false, "contexts": ["check"] },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```
Expected: JSON echoing the protection. From now on, changes go through a pull request whose `check` job passes.

- [ ] **Step 5: Confirm HTTPS and the live site**

```bash
gh api repos/sekere01/sekere01.github.io/pages -q '{url: .html_url, https: .https_enforced, build: .build_type}'
curl -sI https://sekere01.github.io/ | head -1
curl -s http://sekere01.github.io/ -o /dev/null -w "%{http_code} -> %{redirect_url}\n"
```
Expected:
- `https: true`
- `HTTP/2 200`
- the http request returns `301 -> https://sekere01.github.io/`

If `https_enforced` is false, run `gh api -X PUT repos/sekere01/sekere01.github.io/pages -F https_enforced=true`.

- [ ] **Step 6: Live checks**
  1. Open https://sekere01.github.io on a phone. All sections render, and the CV downloads.
  2. Run Lighthouse on the live URL. Accessibility, Best Practices and SEO are all ≥ 95.
  3. Paste the URL into LinkedIn's Post Inspector (https://www.linkedin.com/post-inspector/). The preview shows `og.png`, the title and the description.
  4. View source on the live page. The CSP meta tag is present, and the DevTools Console shows no CSP violations.

- [ ] **Step 7: Record the accepted residual risk in the repo README**

Append to `README.md`:
```markdown

## Known limitation

GitHub Pages cannot send custom HTTP headers, so the CSP is set with a `<meta>` tag. That means `frame-ancestors`, `X-Frame-Options` and a custom HSTS policy are unavailable, so there is no clickjacking protection. This is accepted because the page has no logins, forms or state-changing actions. Moving hosting to Cloudflare Pages would allow these headers.
```
Commit on a branch, open a PR, and merge once `check` passes:
```bash
git switch -c docs/residual-risk
git add README.md && git commit -m "docs: record the accepted framing-protection gap"
git push -u origin docs/residual-risk && gh pr create --fill && gh pr checks --watch && gh pr merge --squash --delete-branch
```
Expected: the PR is merged and the deploy run succeeds on `main`.
