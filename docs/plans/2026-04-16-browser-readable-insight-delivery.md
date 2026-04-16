# Browser-readable insight delivery

- Status: completed
- Owner: maintainer
- Start date: 2026-04-16
- Last updated: 2026-04-16
- Related issue or PR: n/a
- Supersedes: none

## Goal

Let a user open the daily insight in a normal web browser through a stable local URL or static file path, while preserving the repository's deterministic `collect -> synthesize -> validate -> render` artifact model.

## Why now

The repository currently produces:

- `outputs/YYYY-MM-DD/digest.json`
- `outputs/YYYY-MM-DD/digest.md`

That is enough for automation and terminal review, but it is not the best reading experience for a human who wants to scan the digest in a browser, revisit prior dates, or share a stable internal link. The browser surface should improve readability without turning this repository into a dynamic web product.

## Context and orientation

- The repository runs on a dedicated Linux Codex machine with Python 3.12, `uv`, Typer, SQLite, Ruff, pytest, and `systemd`.
- The current canonical output is structured JSON validated by `schemas/daily_insight.schema.json`.
- Markdown is rendered deterministically from `digest.json` by `daily_insight/render.py`.
- Recent work added deterministic `source_summary` handling and explicit bucket-health states that must stay visible to browser readers.
- There is no existing HTML renderer, archive landing page, browser-serving config, or stable "latest digest" browser path.
- The project intentionally avoids a Node/frontend stack today, and there is no existing web framework in the repository.

## Best-practice recommendation

Use a static artifact model, not a dynamic web app:

- keep `digest.json` as the source of truth
- generate a self-contained `digest.html` for each date from the already-validated JSON
- generate a dedicated browser site root that contains only intended browser-facing artifacts derived from canonical `outputs/YYYY-MM-DD/`
- generate a small archive/index page and a stable `latest/` browser entrypoint inside that generated site root
- treat browser publication as an explicit `publish-site` step so human review can remain the boundary before a digest becomes the visible "latest" page
- serve the generated site root read-only through a static server or reverse proxy

This is the best fit for the current repository because it preserves deterministic outputs, avoids live reads from SQLite or `inputs/`, keeps the attack surface small, respects the existing review-before-delivery workflow, and stays compatible with the current `systemd` + Linux machine model.

## Scope

### In scope

- define the browser-readable digest contract and acceptance criteria
- add deterministic HTML rendering from `digest.json`
- add an archive index and a stable browser path for the latest digest
- generate a dedicated browser site root from canonical `outputs/`
- document the recommended static-serving pattern for the dedicated machine
- validate that a recent digest can be opened through a local browser-friendly HTTP path

### Out of scope

- building a multi-user authenticated web application
- adding live search, comments, editing, or admin workflows
- querying SQLite directly from browser code
- exposing `inputs/`, `state/`, or local config files over HTTP
- adding a Node, React, or SPA toolchain just to view the digest
- public internet publishing policy or SSO integration

## Constraints

- `digest.json` remains the canonical browser-render input; HTML must not become a second synthesis path.
- Browser rendering must preserve source metadata, confidence labels, action/watch separation, and `source_summary` bucket-health visibility.
- Historical date-scoped outputs must remain inspectable and reproducible.
- The browser surface should be static and read-only by default.
- The served browser root must be separate from raw `outputs/` so the server exposes only intended public artifacts.
- Prefer self-contained or versioned assets so older digests do not silently change appearance when new CSS is introduced.
- Keep the implementation compatible with the current Python-only stack and dedicated Linux machine.
- Do not require SQLite, live source access, or Codex at page-view time.
- If a date has sparse or degraded coverage, the browser view must surface that explicitly rather than hiding it behind a polished layout.
- `run` may generate browser-ready per-date files, but promotion of the visible `latest/` entrypoint must remain an explicit publish action unless the spec later approves a different reviewed boundary.
- Site publication must be atomic enough that readers never see a half-written `latest/` page or partially generated archive index.

## Done when

- a dedicated browser-delivery spec and test spec define:
  - where browser artifacts live
  - the exact generated site paths and URL shapes
  - what sections and metadata the browser page must show
  - how archive navigation and "latest" routing work
  - how degraded source coverage appears to readers
- a deterministic renderer can produce `digest.html` from `digest.json` without changing the JSON contract
- the generated site root includes a browser entrypoint for both:
  - a specific date
  - the latest available digest
- recent digests are discoverable through a simple archive index page
- maintainers have documented guidance for serving the rendered output read-only on the dedicated machine
- validation proves that a date-scoped digest can be generated, rendered to HTML, and fetched through a local HTTP path

## Milestones

1. Define the browser-delivery contract
   - Files/components: new `specs/browser-digest.md`, new `specs/browser-digest.test.md`, `specs/daily-digest.md`, `docs/workflows.md`
   - Dependencies: none
   - Risk: medium; if the HTML/archive contract stays implicit, implementation will drift between renderer, CLI, and serving docs
   - Work:
     - define the generated browser site root and exact path contract, including:
       - `site/index.html`
       - `site/latest/index.html`
       - `site/YYYY-MM-DD/index.html`
     - define whether raw `digest.json` and `digest.md` are linked from the browser page
     - define the publish boundary explicitly:
       - whether `run` emits per-date HTML only
       - whether `publish-site` is the only step allowed to update `latest/` and the archive landing page
       - whether degraded-but-successful days may update `latest/`
     - define the required browser-visible sections and metadata
     - define how `source_summary` and degraded bucket coverage appear in the browser surface
     - define semantic HTML, mobile-readability, and accessibility minimums
     - decide whether the HTML should be fully self-contained or use versioned static assets
     - state explicitly that the browser view is derived from `digest.json`, not live state
   - Validation commands:
     - spec review against `specs/browser-digest.md`
     - spec review against `specs/browser-digest.test.md`
   - Expected observable result: a new contributor can tell exactly what browser files must exist and what they must contain.

2. Implement deterministic HTML rendering
   - Files/components: `daily_insight/render.py`, `daily_insight/cli.py`, possibly a new `daily_insight/html_render.py`, `tests/test_render.py`, `tests/test_cli.py`, `examples/sample_digest.json`
   - Dependencies: Milestone 1
   - Risk: medium; a browser renderer can accidentally diverge from the Markdown/JSON contract or hide degraded coverage in presentation
   - Work:
     - add a deterministic HTML renderer from the existing digest JSON
     - keep the HTML readable without JavaScript
     - ensure the browser page preserves overview, top items, action now, watchlist, and source summary
     - surface bucket-health and coverage notes clearly
     - add tests for the rendered HTML structure and key content
   - Validation commands:
     - `uv run pytest -q tests/test_render.py tests/test_cli.py`
     - `uv run daily-insight render examples/sample_digest.json /tmp/digest.md`
     - `uv run daily-insight render-html examples/sample_digest.json /tmp/digest.html`
   - Expected observable result: a maintainer can render a sample digest into browser-readable HTML from the existing JSON contract alone.

3. Add publish contract and atomic promotion
   - Files/components: `daily_insight/cli.py`, possible new site-generation module, output-path helpers, new tests
   - Dependencies: Milestone 2
   - Risk: high; publication logic can expose half-written browser artifacts or collapse the review boundary if the promotion step is underspecified
   - Work:
     - implement the dedicated generated site root rather than serving raw `outputs/`
     - implement a staging/build directory and atomic promotion for `latest/` and archive entrypoints
     - ensure repeated publishing is idempotent and does not alter older JSON/Markdown artifacts unintentionally
     - preserve a last-known-good visible site state if a publish step fails midway
   - Validation commands:
     - `uv run pytest -q tests/test_cli.py tests/test_render.py tests/test_publish.py`
     - `uv run daily-insight render-html examples/sample_digest.json /tmp/digest.html`
     - `uv run daily-insight publish-site --source-root outputs --date 2026-04-16 --site-root /tmp/daily-insight-site`
     - `find /tmp/daily-insight-site -maxdepth 3 -name '*.html' | sort`
   - Expected observable result: publication updates the intended site root atomically and leaves prior visible content intact if a publish fails.

4. Add archive and latest generation
   - Files/components: `daily_insight/cli.py`, possible new site-generation module, new tests, `README.md`
   - Dependencies: Milestone 3
   - Risk: medium; archive/index logic can still create unstable links or misleading "latest" behavior if it does not reflect the approved publish contract
   - Work:
     - implement archive landing-page generation inside the dedicated site root
     - implement the stable `latest/` browser path according to the approved publication rule
     - ensure browser navigation makes the current date and archive relationship obvious
     - ensure degraded-but-successful days are handled according to the approved `latest/` policy
   - Validation commands:
     - `uv run pytest -q tests/test_cli.py tests/test_render.py tests/test_publish.py`
     - `uv run daily-insight publish-site --source-root outputs --date 2026-04-16 --site-root /tmp/daily-insight-site`
     - `find /tmp/daily-insight-site -maxdepth 3 -name '*.html' | sort`
   - Expected observable result: a browser user has both a date-specific page and a stable landing page for the latest/recent digests.

5. Document and harden read-only browser serving
   - Files/components: `README.md`, `docs/codex-machine-setup.md`, `docs/workflows.md`, optional sample config under `ops/`
   - Dependencies: Milestone 4
   - Risk: medium; weak serving guidance could accidentally expose local-only files or imply a production web app that the repo does not operate
   - Work:
     - document the recommended serving model: static read-only files rooted at the generated browser site
     - document `python -m http.server` as a smoke-test tool only, not a durable deployment option
     - document NGINX as the default durable Linux static-serving recommendation for the dedicated machine
     - state clearly that `inputs/`, `state/`, and `configs/sources.local.json` must not be served
   - Validation commands:
     - `uv run python -m http.server 8000 --directory /tmp/daily-insight-site`
     - `curl -I http://127.0.0.1:8000/`
     - `curl -I http://127.0.0.1:8000/latest/`
   - Expected observable result: a maintainer can serve the generated browser site locally without writing app code or exposing non-public repository files.

6. Validate the browser flow on the dedicated machine
   - Files/components: live operator config, `outputs/`, browser-site output root, docs
   - Dependencies: Milestone 5, live source access
   - Risk: medium; the browser surface is not done until it is validated against a real digest on the actual Codex machine
   - Work:
     - generate a real digest for an explicit date on the dedicated machine
     - build or publish the browser site from that digest
     - verify both the date page and latest/archive path over local HTTP
     - confirm that degraded source coverage remains visible in the browser surface for a thin day
     - verify that the browser page shows the expected date, top-level sections, and degraded coverage text rather than only returning `200 OK`
   - Validation commands:
     - `uv run daily-insight run --date YYYY-MM-DD --config configs/sources.local.json --state-db state/daily_insight.db`
     - `uv run daily-insight publish-site --source-root outputs --date YYYY-MM-DD --site-root /tmp/daily-insight-site`
     - `uv run python -m http.server 8000 --directory /tmp/daily-insight-site`
     - `curl http://127.0.0.1:8000/latest/`
     - `curl http://127.0.0.1:8000/YYYY-MM-DD/`
     - `curl http://127.0.0.1:8000/latest/ | rg 'Daily insight overview|Source summary|degraded|YYYY-MM-DD'`
   - Expected observable result: a user can read the latest insight in a browser on the dedicated machine without touching raw JSON or Markdown files.

## Progress

- 2026-04-16: created this plan because the current repository stops at JSON plus Markdown, while the user explicitly needs a browser-readable delivery path.
- 2026-04-16: confirmed the current renderer is Python-only and deterministic, which makes static HTML generation a better fit than introducing a live web stack.
- 2026-04-16: revised the plan after plan review to require a dedicated generated site root, an explicit `publish-site` publication boundary, atomic `latest/` promotion, and stronger content-level browser validation.
- 2026-04-16: completed the Milestone 1 spec slice by adding `specs/browser-digest.md` and `specs/browser-digest.test.md`, and by updating `specs/daily-digest.md` and `docs/workflows.md` so browser publication is explicit and remains downstream of reviewed canonical outputs.
- 2026-04-16: completed the Milestone 2 rendering slice by adding deterministic self-contained HTML rendering, a new `daily-insight render-html` command, focused CLI/renderer regression tests, and the corresponding contract-level validation on sample digest artifacts.
- 2026-04-16: completed the Milestone 3 publish slice by adding `daily_insight.publish`, a new `daily-insight publish-site` command, focused publish/CLI regression tests, and staged backup-and-replace promotion so the visible site stays intact if a publish fails.
- 2026-04-16: completed the Milestone 4 archive/latest slice by proving that later publishes update `latest/`, keep archive dates in descending order, preserve older published pages byte-for-byte, and leave `run` unable to modify the visible published site.
- 2026-04-16: completed the Milestone 5 serving-doc slice by documenting the generated `site/` contract in `README.md` and `docs/codex-machine-setup.md`, and by adding an example NGINX config rooted only at `site/`.
- 2026-04-16: completed the Milestone 6 dedicated-machine validation slice by publishing the real `2026-04-16` digest into `/tmp/daily-insight-site`, serving it locally with `uv run python -m http.server`, and confirming the latest and date-scoped browser pages over HTTP with visible degraded coverage text.

## Decision log

- 2026-04-16: prefer static HTML generated from `digest.json` over a dynamic web app -> it preserves the deterministic artifact model and avoids introducing a live application tier just for reading.
- 2026-04-16: treat the served browser root as a dedicated generated site tree instead of serving raw `outputs/` -> this narrows the exposed surface and keeps browser publication separate from raw artifacts.
- 2026-04-16: keep `publish-site` as the explicit publication boundary for `latest/` and archive updates -> this preserves the existing review-before-delivery workflow and avoids auto-promoting every successful run into the visible latest page.
- 2026-04-16: keep the browser work as a new initiative instead of expanding the closed source-coverage plan -> the new problem is user-facing delivery, not source sufficiency.
- 2026-04-16: allow degraded-but-successful digests to become `latest/` after explicit publication -> degraded source coverage is already part of the visible contract and should not force maintainers into ad hoc unpublished workarounds for thin but still valid days.
- 2026-04-16: keep the initial browser renderer self-contained with inline CSS and no JavaScript dependency -> this satisfies the baseline readability and historical-stability requirements without introducing an asset pipeline before it is needed.
- 2026-04-16: publish the browser site by copying the current site tree into a staging directory and then promoting the whole site root with `os.replace` -> this keeps visible archive/latest pages stable during regeneration and provides a straightforward rollback point when promotion fails.
- 2026-04-16: keep the durable serving recommendation at NGINX and treat `uv run python -m http.server` strictly as smoke-test infrastructure -> the built-in server is enough for validation but not the right operational boundary for a persistent browser surface.

## Surprises and discoveries

- 2026-04-16: the current Markdown renderer is simple enough that HTML rendering can likely stay in the existing Python stack without adding templating infrastructure immediately.
- 2026-04-16: the raw `outputs/` tree is a natural source for browser publishing, but it is not the right thing to serve directly because it contains more than the intended browser contract.
- 2026-04-16: the cleanest contract is to keep browser publication completely downstream of `outputs/YYYY-MM-DD/digest.json`; this avoids forcing Markdown presence or live state reads into the browser delivery path.
- 2026-04-16: the existing Markdown renderer could be extended directly for HTML without adding a template engine yet; a small deterministic Python renderer was enough to satisfy the browser contract for date pages.
- 2026-04-16: the CLI help test already expected `publish-site`, so the first Milestone 3 failing state was a clean missing-module failure rather than an ambiguous behavior mismatch.
- 2026-04-16: this shell exports `HTTP_PROXY` and `HTTPS_PROXY`, so local browser smoke-tests need `curl --noproxy '*'` to hit the loopback `http.server` directly instead of routing through the proxy.
- 2026-04-16: the repo’s supported runtime path matters for smoke-tests too; bare `python -m http.server` was unavailable on this PATH, while `uv run python -m http.server` matched the actual machine setup and worked.

## Validation and acceptance

- Milestone 1 is accepted when the browser-delivery contract is explicit enough that implementation can proceed without guessing paths, publication boundaries, or degraded-coverage behavior.
- Milestone 2 is accepted when a sample digest can be rendered into deterministic browser-readable HTML from JSON alone.
- Milestone 3 is accepted when the generated site root and `latest/` publication step are atomic enough that readers never see half-written browser output.
- Milestone 4 is accepted when the project has stable date and latest/archive browser paths that are safe to regenerate.
- Milestone 5 is accepted when a maintainer has clear documentation for serving only the intended browser artifacts with a smoke-test server and a durable Linux static-server recommendation.
- Milestone 6 is accepted when a real digest is fetchable over local HTTP on the dedicated machine and still surfaces degraded coverage accurately.

## Validation notes

- `sed -n '1,240p' AGENTS.md` -> reviewed repository planning rules, contract/update expectations, and done criteria before creating this initiative.
- `sed -n '1,260p' docs/workflows.md` -> confirmed the current pipeline ends at JSON plus Markdown and has no browser publication step yet.
- `sed -n '1,220p' docs/plan.md` -> confirmed there were no active plans before starting this initiative.
- `sed -n '1,260p' daily_insight/render.py` -> confirmed the current human-readable output is Markdown-only and renderer logic is simple enough to extend in Python.
- `sed -n '1,260p' README.md` and `sed -n '1,240p' docs/codex-machine-setup.md` -> confirmed docs currently stop at CLI/systemd usage and do not document browser delivery.
- `sed -n '1,260p' specs/daily-digest.md` and `sed -n '1,260p' specs/daily-digest.test.md` -> confirmed the current output contract does not yet define any browser artifact.
- `rg -n "html|http|browser|serve|web|portal|index\\.html|Flask|FastAPI|static" -S daily_insight docs ops scripts tests README.md` -> found no existing browser surface or web framework to extend.
- Python `http.server` documentation -> confirms the built-in server is not recommended for production and should stay a smoke-test tool, not the durable serving recommendation.
- Milestone 1 is spec-and-doc work only; no repository tests or runtime validation commands were run in this turn beyond reading the existing plan, workflow, renderer, and digest-contract files before drafting the new browser-delivery spec and test spec.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_render.py tests/test_cli.py` -> initially failed during Milestone 2 because `daily_insight.render` did not yet expose `render_html`, which confirmed the new renderer path was not already present.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_render.py tests/test_cli.py` -> passed (`10 passed`) after adding deterministic HTML rendering and the `render-html` CLI command.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/digest.md` -> passed after Milestone 2 and still rendered the canonical Markdown output unchanged.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render-html examples/sample_digest.json /tmp/digest.html` -> passed and produced the first self-contained browser-readable HTML artifact from canonical digest JSON.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check daily_insight/render.py daily_insight/cli.py tests/test_render.py tests/test_cli.py` -> passed after the final import-order and line-length cleanup on the new browser renderer/CLI path.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed (`32 passed`) after the Milestone 2 changes, confirming the new HTML path did not regress the existing repository test suite.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py tests/test_publish.py` -> initially failed during Milestone 3 with `ModuleNotFoundError: No module named 'daily_insight.publish'`, which confirmed the publish path was not already implemented.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py tests/test_render.py tests/test_publish.py` -> passed (`16 passed`) after adding the publish module, CLI command, and atomic promotion logic.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check daily_insight/cli.py daily_insight/publish.py tests/test_cli.py tests/test_publish.py` -> passed after the Milestone 3 implementation.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight publish-site --source-root outputs --date 2026-04-16 --site-root /tmp/daily-insight-site` -> passed and published the browser site into a dedicated generated root.
- `find /tmp/daily-insight-site -maxdepth 3 -name '*.html' | sort` -> listed `/tmp/daily-insight-site/index.html`, `/tmp/daily-insight-site/latest/index.html`, and `/tmp/daily-insight-site/2026-04-16/index.html`, confirming the expected published path contract.
- `rg -n "2026-04-16|Daily insight archive|Latest published digest|Daily insight for" /tmp/daily-insight-site -g '*.html'` -> confirmed the generated archive and latest pages expose the expected digest date and browser-visible headings after publication.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q tests/test_cli.py tests/test_publish.py` -> passed (`14 passed`) after adding Milestone 4 coverage for archive ordering, historical page stability, and `run` preserving the visible published site.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run pytest -q` -> passed (`39 passed`) after the Milestone 4/5 documentation and test additions.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run ruff check .` -> passed after the final browser-delivery changes.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m json.tool schemas/daily_insight.schema.json > /dev/null` -> passed during the final browser-delivery close-out.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight collect --dry-run --config configs/sources.example.json` -> passed during the final browser-delivery close-out.
- `UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run daily-insight render examples/sample_digest.json /tmp/digest.md` -> passed during the final browser-delivery close-out.
- `env UV_PROJECT_ENVIRONMENT=/tmp/daily-insight-venv ~/.local/bin/uv run python -m http.server 8000 --directory /tmp/daily-insight-site` -> served the published browser site successfully during Milestone 6 when kept alive in a PTY session.
- `curl --noproxy '*' --max-time 10 -I http://127.0.0.1:8000/` -> returned `HTTP/1.0 200 OK` for the archive landing page during Milestone 6.
- `curl --noproxy '*' --max-time 10 -I http://127.0.0.1:8000/latest/` -> returned `HTTP/1.0 200 OK` for the stable latest page during Milestone 6.
- `curl --noproxy '*' --max-time 10 -s http://127.0.0.1:8000/latest/ | rg 'Daily insight for 2026-04-16|Source summary|degraded'` -> confirmed the latest page exposed the expected digest date, source-summary heading, and degraded bucket text during Milestone 6.
- `curl --noproxy '*' --max-time 10 -s http://127.0.0.1:8000/2026-04-16/ | rg 'Daily insight for 2026-04-16|Source summary|degraded'` -> confirmed the date-scoped page exposed the same required browser-visible content during Milestone 6.

## Idempotence and recovery

- Keep `digest.json` as the source of truth; if browser rendering fails, recover by re-rendering from JSON rather than re-running live collection.
- Do not rewrite old `inputs/YYYY-MM-DD/` artifacts as part of browser delivery work.
- Preserve historical date directories even if the archive/index generation changes later.
- If a latest/archive page becomes stale, rebuild it from existing `outputs/YYYY-MM-DD/` artifacts instead of recollecting sources.
- Never serve `inputs/`, `state/`, or `configs/sources.local.json`; if a sample server config risks exposing them, fix the generated site root or server root before rollout.
- Build browser publication into a staging directory first, and only then promote it into the visible site root so `latest/` keeps the last-known-good state if publishing fails.

## Outcomes and retrospective

- Pending implementation.
- The best-practice direction is clear: deterministic static HTML plus a read-only archive, not a live application. The remaining work is to define the exact contract and integrate it cleanly into the current artifact pipeline.
