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
