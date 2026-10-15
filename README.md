# sekere01.github.io

Source for the portfolio site at https://sekere01.github.io.

- `site/` is the only folder that gets published.
- `scripts/checks/` holds the build checks CI runs before every deploy.
- Preview locally: `python3 -m http.server 8000 -d site`, then open http://localhost:8000
- Run checks locally:
  `python3 -m unittest discover -s scripts/checks -p 'test_*.py' -v && python3 scripts/checks/check_html.py site && python3 scripts/checks/check_pii.py site`

## Known limitation

GitHub Pages cannot send custom HTTP headers, so the CSP is set with a `<meta>` tag. That means `frame-ancestors`, `X-Frame-Options` and a custom HSTS policy are unavailable, so there is no clickjacking protection. This is accepted because the page has no logins, forms or state-changing actions. Moving hosting to Cloudflare Pages would allow these headers.
