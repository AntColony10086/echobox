# Codex visual deliverables — echobox

> **REQUIRED MODEL: GPT-5.5 high (high-reasoning tier).** Do not switch to a smaller / faster model — visual quality is the priority.

This brief defines the visual assets Codex needs to produce for the echobox open-source release. Drop deliverables into the paths shown; the rest of the project (README, CI, push) is already wired up to consume them at those exact paths.

## Project context (read first)

- **Name:** echobox (lowercase, one word)
- **Tagline (en):** "One box → all the boxes."
- **Tagline (zh):** "画一框，框出全图。"
- **What it is:** Multimodal annotation agent. User draws one bounding box on an image; a LangGraph agent + GECO2 exemplar detector returns every similar object. Tool for ML / dataset prep.
- **Primary brand color:** `#3182ce` (blue, matches in-app accent)
- **Secondary palette:** neutral grays — `#2d3748` (dark text), `#718096` (mid), `#e2e8f0` (light)
- **Aesthetic:** clean, technical, restrained. Vercel / Linear / Resend tier — not playful, not corporate.

## Deliverable 1 — Logo

A wordmark designed as **letter transformation of "echobox"**. Concept: the inner "o" (or "b") morphs into a box-with-echo motif — concentric squares fading outward, evoking "one box → many boxes / echoes". All lowercase.

Drop into `assets/logo/`:

| File | Format | Size | Notes |
|---|---|---|---|
| `logo.svg` | SVG | scales | Full wordmark with mark embedded |
| `logo-mark.svg` | SVG | scales | Just the box-echo glyph, no text |
| `logo.png` | PNG | 1024×256 transparent | README header fallback |
| `logo-dark.png` | PNG | 1024×256 | For light backgrounds — colored or black wordmark |
| `logo-light.png` | PNG | 1024×256 | For dark backgrounds — white wordmark |
| `favicon.svg` | SVG | square | Browser tab |
| `favicon.ico` | ICO | bundles 16, 32, 48 | Legacy support |

Color spec: monochrome variants in pure `#1a202c` (near-black) and pure white. Color variant uses `#3182ce` for the box-echo glyph and `#1a202c` for the rest of the wordmark.

## Deliverable 2 — UI screenshots

Take the raw screenshots Claude provides (one per scene listed below) and beautify each:

- Wrap in a **light browser chrome frame** (no real OS chrome — a stylized minimal frame: 3 colored dots top-left, address bar showing `localhost:5173`, single-pixel border)
- Add a **soft drop shadow** (offset 0 12, blur 32, opacity 12%)
- Place on a **white background**, output 1600px wide

Drop into `assets/screenshots/`:

| File | Scene description |
|---|---|
| `01-home.png` | Project list home page with at least 3 sample projects, "+ 新建项目" button visible |
| `02-setup-modal.png` | SetupModal open showing all 5 setup cards filled in |
| `03-annotate.png` | Annotation page with image loaded, several bboxes drawn (mix of accepted solid + pending dashed), class picker on right showing 2 classes |
| `04-chat.png` | Chat modal mid-conversation with user + assistant + tool messages |
| `05-export.png` | Export panel inside SetupModal showing successful export result |
| `06-image-list-detail.png` (optional) | Close-up of left ImageList showing per-row index + split dot + filename |

## Deliverable 3 — Social card

`assets/social-card.png` — 1200×630 PNG (Open Graph + Twitter card spec).

Layout: logo center-left at ~280px wide, tagline below logo ("One box → all the boxes."), one screenshot thumbnail (use `03-annotate.png`) center-right at ~600px wide, soft shadow. White background with a subtle blue gradient strip on the left edge.

## Constraints

- **No emoji**, no "AI" buzzwords in the visuals
- **Don't invent screenshots** — use the source captures Claude provides; only beautify (frame + shadow)
- **Vector-first** for the logo — PNG exports are derived from the SVG, not redrawn
- **Maintain consistency** — all screenshots use the same browser chrome and shadow

## Drop-off

Place files at exactly the paths above and commit with message `assets: logo + screenshots + social card`. Claude will pick them up in Phase 5 of the open-source-readiness plan.
