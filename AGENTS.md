# Project AGENTS.md

## Commands

- Run: `npm start` → <http://localhost:8000>
- Test: `npm test` (bank validator + Playwright E2E)
- Bank only: `python3 tests/validate_bank.py`
- E2E only: `./tests/run_e2e.sh`
- Setup: `npm install`, then `npx playwright install chromium`
- Lint: none
- Typecheck: none
- Build: none
- Deploy: GitHub Pages from `main` `/`; live at <https://teterkin.ru/ugadai-epokhu/>

`npm test` must print `PASS: 60 questions...` and `E2E: PASS ...`.

## Branching and commits

- Trunk is `main`; work lives in `feat/<slug>`, `fix/<slug>`, `docs/<slug>` or `chore/<slug>`.
- Commit only on an explicit request; do not commit or push unprompted.
- Keep one focused change per commit.

## Project map

- `index.html` — the only runtime file: CSS, question bank JSON, game logic, Telegram guards.
- `tests/validate_bank.py` — stdlib validator for the bank and its xlsx sources.
- `tests/e2e.html` — browser scenario harness; `tests/e2e.mjs` — Playwright runner; `tests/run_e2e.sh` — server + runner.
- `docs/prd/ugaday-epohu.md` — confirmed PRD.
- `russia_encyclopedia_1980_2026.xlsx` — source workbook (do not edit to make a test pass).

## Invariants

- `index.html` is the only runtime file. No external scripts, styles, fonts, images or CDNs; no network requests during play.
- Exactly 6 eras and 5 categories. Exactly 60 questions, 2 per category/era pair.
- Every question's `quote` is an exact substring of the cited `source.sheet!source.cell`; the source row `A` must match the question era.
- A round is 10 questions, 4 era options, exactly one correct. Mixed mode gives 2 questions per category and at most 2 per era.
- Do not reveal the correct era before the player answers.
- No `alert`, `confirm` or `prompt`. Telegram WebApp is optional; the game must work as a plain page.
- `localStorage` failure must not break the game; best score is an enhancement.
- Playwright is pinned exactly to `1.65.1`. Do not float dependencies.

## Secrets

None. Do not add credentials, tokens or `.env`-style files to the repository.
