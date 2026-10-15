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

    def test_detects_dotted_format(self):
        self.assertEqual(len(find_phone_numbers("tel 0800.000.0000")), 1)

    def test_detects_en_dash_format(self):
        self.assertEqual(len(find_phone_numbers("tel 0800\u2013000\u20130000")), 1)

    def test_detects_html_encoded_plus(self):
        self.assertEqual(len(find_phone_numbers("<p>&#43;234 800 000 0000</p>")), 1)

    def test_detects_html_encoded_digits(self):
        self.assertEqual(len(find_phone_numbers("<p>&#48;800&nbsp;000&nbsp;0000</p>")), 1)

    def test_ignores_ip_addresses_and_versions(self):
        self.assertEqual(find_phone_numbers("host 192.168.100.200, version 1.22.333"), [])

    def test_ignores_year_ranges(self):
        self.assertEqual(find_phone_numbers("2019\u20132021, 2021 \u2013 2023"), [])


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
