# Portfolio site — design spec

- **Date:** 2026-10-15
- **Owner:** Oluwafisayomi Adekoya (github.com/sekere01)
- **Status:** Approved in brainstorming; awaiting spec review

## 1. Goal

One public page that does three jobs at once:

1. **Get hired** — recruiters and hiring managers arriving from the CV link.
2. **Win freelance work** — prospective clients for pentest, DevSecOps and detection engagements.
3. **Show write-ups** — readers looking for technical proof of work.

**Success:** within ~30 seconds a visitor can tell what Oluwafisayomi does, see evidence of it, and find how to make contact — on a phone as well as a desktop.

## 2. Decisions

| Topic | Decision |
|---|---|
| Format | Single page, sections reached by anchor links |
| Build | Hand-written HTML + CSS, no build step, no npm/Ruby toolchain |
| Hosting | GitHub Pages, repo `sekere01/sekere01.github.io`, address `https://sekere01.github.io` |
| Custom domain | Not now; can be added later without a rebuild |
| Write-ups | Project cards link to the existing GitHub repos; no posts hosted on the site |
| Contact | Email (`mailto:`) + LinkedIn + GitHub links; no form, no booking widget |
| Content source of truth | The corrected CV (Google Doc "Oluwafisayomi_Adekoya CV latest (corrected)"). Every claim on the site must match it. |

Rejected alternatives: Astro (npm dependency tree is too much overhead for one page), Jekyll (Ruby toolchain, limited plugin and header control), no-code builders (less technical proof, recurring cost).

## 3. Page structure and content

Sticky top bar: name + anchor links — Services · Projects · Experience · Certs · Contact.

1. **Hero**
   - Name; headline "Penetration Tester | Security Engineer | Purple Team"; one-line pitch taken from the CV tagline.
   - Three calls to action: **See my work** (→ Projects), **Work with me** (→ Contact), **Download CV** (PDF in the repo).
2. **What I do** — three cards, phrased to suit employers and clients alike:
   - Penetration testing — web, Active Directory, network.
   - DevSecOps pipelines — CI/CD security gating, SBOM/CVE tracking.
   - Detection engineering — Wazuh/Splunk rules and tuning, mapped to MITRE ATT&CK.
3. **Projects & write-ups** — ~6 cards, highest impact first. Each card: title, date, one-line outcome, tool tags, a descriptive link to the GitHub repo ("Read the Reyts write-up on GitHub").
   1. Black-Box Penetration Test: Reyts Fintech — authorised, in-scope under Amdari hackathon rules of engagement.
   2. Active Directory Attack Lab: Full Domain Compromise.
   3. KYC Fraud & Threat Intelligence Analysis: Reyts Fintech.
   4. Web Application Security Assessments — DVWA medium-level input-filter bypass (lab) and IDOR access-control audit.
   5. Enterprise Security Operations Lab — Splunk/Sophos SIEM and PKI/TLS.
   6. TryHackMe Practical Labs — 48 rooms, 30-day streak (no repo link).
4. **Experience** — compact timeline, one line per role: Handi Digital Solutions → T.R.A.N (UBI Ethical Hacking Track, Advanced Stage 8) → Expadox Lab → Levi's Acre Farms and Foods → Grola Tech → Tenece. Detail stays on the CV.
5. **Certifications** — CPENT v2 (highlighted), OSCP+ (planned), Google Cybersecurity, Palo Alto PSE, AltSchool Diploma; Forage simulations on one line.
6. **Contact** — "Open to full-time roles and freelance engagements", then email, LinkedIn (`linkedin.com/in/oluwafisayomi-adekoya`), GitHub.

### Content rules

- **No phone number** anywhere on the site or in the downloadable CV PDF (scraping, spam, SIM-swap targeting). The full CV with phone is sent directly on request.
- **Current employer (Handi):** keep to the generic level of the CV bullets. No tool names tied to Handi production, no architecture details, no internal repo names.
- Use the corrected CV's framing verbatim in substance: "Advanced Stage 8" for UBI, lab-scoped DVWA wording, "authorised, in-scope" for Reyts.

## 4. Visual design and accessibility

- Dark theme by default, matching light theme via `prefers-color-scheme`. One accent colour (security teal/green) for links, buttons, tags. Monospace only for tags and section labels.
- System font stack; no web fonts or other external requests.
- Mobile-first grid: 1 column on phone, 2 on tablet, 3 on desktop. On small screens the nav becomes a horizontally scrollable row (no JavaScript toggle).
- Images: none required. Optional headshot served from the repo. One Open Graph image (`og.png`) and `og:`/`twitter:` meta tags so shared links render a preview card. Favicon.
- Accessibility: WCAG 2.2 AA contrast in both themes; semantic landmarks (`header`, `nav`, `main`, `section`, `footer`); skip-to-content link; visible focus styles; `prefers-reduced-motion` disables animation; descriptive link text.
- Performance budget: page + CSS ≈ 50 KB or less, excluding the CV PDF and OG image.

## 5. Security

GitHub Pages does not allow custom HTTP response headers. Controls are therefore:

- **CSP via `<meta http-equiv="Content-Security-Policy">`**: `default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'`. No inline scripts or styles. If a small script is ever added it is served as a file from `'self'`.
- **Known gap (accepted residual risk):** a meta CSP cannot set `frame-ancestors`, and Pages cannot send `X-Frame-Options` or a custom HSTS policy, so anti-clickjacking protection is unavailable. Risk is low: the page has no logins, forms or state-changing actions. Mitigation path if needed later: move hosting to Cloudflare Pages and set headers there.
- "Enforce HTTPS" enabled in Pages settings.
- `rel="noopener noreferrer"` on every link that opens a new tab.
- No analytics, trackers or third-party embeds.
- Email published as a plain `mailto:` link; extra spam is accepted rather than adding obfuscation JavaScript.

## 6. Repository and deployment

```
sekere01.github.io/
├── site/              # the only folder published
│   ├── index.html
│   ├── styles.css
│   └── assets/        # og.png, favicon, optional headshot, CV PDF (no phone number)
├── scripts/checks/    # local + CI check scripts (not published)
├── docs/specs/        # this spec
└── .github/
    ├── workflows/deploy.yml
    └── dependabot.yml
```

**Workflow (`deploy.yml`)** on push to `main` (and `workflow_dispatch`):

1. **check** job — must pass before deploy:
   - Link checker over `index.html` (every write-up link resolves).
   - Secret scan of the repo.
   - Script that fails if the HTML/CSS references any external origin for a loaded resource (`src`, `href` on `link`, CSS `url()`); outbound `<a href>` links are allowed.
   - Script that fails if a phone-number pattern appears in any published file.
2. **deploy** job (`needs: check`) — GitHub's official Pages upload and deploy actions, publishing `site/` only.

**Hardening:**

- Every action pinned to a full commit SHA with a version comment.
- Workflow-level `permissions: contents: read`; only the deploy job gets `pages: write` and `id-token: write`.
- Dependabot for the `github-actions` ecosystem.
- Branch protection on `main`.
- Exact action and tool versions/SHAs are looked up against their official sources when the implementation plan is written — not taken from memory.

## 7. Verification

- Local preview: `python3 -m http.server 8000 -d site`.
- Lighthouse: ≥ 95 for Accessibility, Best Practices and SEO.
- Keyboard-only walkthrough; phone-width check; both colour themes.
- Share the URL on LinkedIn and confirm the preview card renders.
- Content audit: every claim on the page checked against the corrected CV.
- CI checks green on the first deploy.

## 8. Out of scope (for now)

Custom domain, hosted blog posts, contact form, booking link, analytics. Each can be added later; moving to hosted posts would be the trigger to reconsider Astro.
