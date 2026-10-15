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
