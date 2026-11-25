---
name: code-review
description: >-
  Review changes in this repository for correctness and potential bugs, architectural consistency, coding convention violations, error handling and edge cases, security concerns, test coverage, and potential regressions — prioritized findings with file/location, why it matters, and a suggested correction. Use when asked to review code or a diff; not for implementing features or one-off questions.
---

# Code Review

Review changes in this repository: correctness and potential bugs, architectural consistency, coding convention violations, error handling and edge cases, security concerns, test coverage, and potential regressions — reported as prioritized findings with file/location, why it matters, and a suggested correction. This skill is reusable across different review requests — read it as a checklist, not a script for one specific change.

Reviews are report-only by default: do not modify files during a review unless explicitly requested. Findings are reported; fixes are left to the author or an explicit follow-up request.

## Grounding documents

Read before starting — primarily use these as ground truth for what "correct" means here, and avoid excessive codebase scanning:

- `AGENTS.md` — project rules (layering, lazy imports, filesystem-as-build-state, minimal error handling).
- `documentation/ARCHITECTURE.md` — layered architecture, hierarchy mirroring, cascade invalidation + skip-on-exists, output layout, lazy imports for heavy dependencies.
- `documentation/CODING_CONVENTIONS.md` — naming, formatting, imports, validation strategy, logging symbols, error handling, testing reality (none).
- `README.md` — user-facing behavior; check that docs match what the code does when a change touches user-visible behavior.

## 1. Scope and inputs

Steps:

- Identify the review target explicitly: a diff/PR, specific files, or the whole tree. State it in one sentence before checking anything.
- List out-of-scope items (e.g. docs-only changes need no runtime verification; generated output is not source).
- Note what can and cannot be checked with available information — if an area cannot be verified, say so rather than guessing.

Result: a short scope statement — target, files/areas covered, anything excluded.

## 2. What "correct" means here (ground truth)

Summarize the load-bearing rules from the docs; every finding is judged against these:

- **Layering, one-way dependencies** — flows → tasks → utils; models are pure frozen data with no dependencies; tasks never import flows. Flows orchestrate and build `Config`s; tasks wrap exactly one external tool each (FFmpeg via `ffmpeg-python`, poppler via `pdf2image`, Kokoro + `soundfile` for TTS) or one plain file operation; utils stay small and stateless.
- **Filesystem is the build state** — cached configs + artifact existence checks + MD5 of the source PDF (`frames.md5`) drive incremental regeneration. Cascade invalidation deletes stale artifacts (voice → frames → _frames → video → result); each pipeline step then skips if its artifact exists. The `updated` flag propagates scene → chapter → video, so stitching only re-runs when something actually changed.
- **Lazy imports for heavy dependencies** — task and sub-flow modules are imported inside the function that calls them, after artifact-existence checks; PyTorch/Kokoro and FFmpeg bindings load only when work will happen. Light deps (models, utils) import at top of file; model imports precede utils imports.
- **Order is part of the data contract** — chapter/scene lists are `dict[str, str]` ID → relative config-file mappings whose insertion order is the render order. Never sort or reorder them.
- **Minimal error handling by design** — only `RuntimeError` in flows for user-facing configuration problems (unknown/missing chapter/scene); exactly one catch site at the CLI entry, which prints `✘ {error}`. No custom exception classes, no `try/except` elsewhere, no logging. Missing files return `None` / existence checks early-return rather than raising.
- **Validation = defaults + lenient access** — top-level keys via `dict.get(key, DEFAULT)`; scene sub-objects shallow-merged with the `|` operator (e.g. `VOICE_DEFAULTS | data["voice"]`); no required-key enforcement or type checks beyond argparse and flow `RuntimeError`s.
- **Output** — all output is `print()` to stdout with Unicode status symbols: `‣` scene start, `⧗` in progress overwritten via `end="\r"`, `✔` success/up-to-date, `✘` error at CLI only. Tasks and utils print nothing.
- **Models** — frozen `@dataclass(frozen=True)`, duplicated per level (no shared base class); scene adds `VoiceOptions` / `FrameOptions`; constructed with keyword arguments, no mutation. Invalidation is expressed as deleting artifacts from disk, never changing model state.
- **No test suite exists** — verification is manual and must be stated honestly. Do not invent a test command or demand tests that do not exist unless asked.

## 3. Review process — seven areas

Check each area against the scope statement. Include an area in the report only when it has findings or was explicitly checked; omit empty sections rather than padding them.

### Area 1 — Correctness and potential bugs

Steps:

- Verify logic in flows/tasks/utils against the documented pipeline order (voice → frames → _frames → video → result) and cascade invalidation rules: deletions must match what changed (e.g. a voice change deletes voice + result but keeps video; frame start/end/source changes delete the frames folder, force duplications re-creation, and downstream artifacts; rate changes affect only video + result). Flag any stale artifact that survives a change it depends on.
- Verify skip-on-exists guards do not mask staleness — an artifact must never be kept when its inputs changed without the cascade deleting it.
- Verify order preservation: chapter/scene mappings are iterated in insertion order; no sorting or reordering introduced anywhere (including `stitch_videos` input lists).
- Verify path resolution: relative config paths resolve against the config file's folder (`join_paths(config.folders.config, ...)`), never the cwd.
- Verify parsing of user input: duplications strings in `frame:amount` comma-separated format — `int()` conversions can raise on malformed or empty strings; optional start/end handling in frame extraction (None defaults); missing PDF source behavior.
- Verify change detection: the MD5 hash is written after extraction and compared against the cached file; a changed PDF must trigger re-extraction, not be silently skipped.
- Verify `updated` flag propagation: scene → chapter → video, so stitching re-runs only when something actually changed; `--chapter` / `--scene` delegation paths still work and return the right boolean.

Result: findings on logic errors, stale artifacts, order violations, path resolution bugs, or input-parsing crashes — each with file/location.

### Area 2 — Architectural consistency

Steps:

- Check import direction: flows import tasks/utils/models downward only; tasks never import flows; models have no dependencies; utils stay small and stateless. Flag any upward or sideways imports.
- Check module shape: exactly one public function per flow/task module (flow entry points `generate_<level>`); task public function name equals the module name; private helpers are `_`-prefixed; models live only in `tools/models/` and stay frozen dataclasses with keyword construction.
- Check that each flow builds one frozen `Config` and threads it through its private helpers instead of passing many individual arguments.
- Check lazy imports: heavy deps (Kokoro/PyTorch, FFmpeg bindings) are imported inside the function that calls them, after artifact-existence checks; sub-flow imports happen inside functions; light deps import at top of file with model imports preceding utils imports. Flag any heavy import pulled in before an existence check or at module top where it should be lazy.
- Check output layout knowledge stays in flows: `FolderPaths` / `FilePaths` are built only in flow `_create_*_paths` functions; tasks receive flat paths and never learn the tree shape (the documented exception is `stitch_videos` → `filesystem.join_paths`).
- Check that models remain duplicated per level with no shared base class, and scene adds `VoiceOptions` / `FrameOptions` only at scene level.

Result: findings on layering violations, wrong module shape, eager heavy imports, or layout knowledge leaking into tasks/utils — each with file/location.

### Area 3 — Coding convention violations

Steps:

- Check naming: `snake_case` functions/variables; boolean flags use descriptive compound names (`*_updated`, `already_existed`); private helpers are `_`-prefixed; module constants are `SCREAMING_SNAKE_CASE` at the top of file — config defaults suffixed `_DEFAULT` / `_DEFAULTS` in a `### DEFAULTS ###` section, tuning constants plain (e.g. `RESOLUTION = 200`).
- Check formatting: blank line after every `def` and after `for` lines in flow loops; double quotes everywhere; LF endings, UTF-8, single trailing newline, 4-space indentation; no docstrings or explanatory comments (only the section banners); flows use banners of the exact form `### NAME ` followed by 26 `#` characters (e.g. `### DEFAULTS ##########################`) — tasks/models/utils do not.
- Check imports: relative inside the package; third-party first then relative; model imports precede utils imports.
- Check comparisons: `None` compared with `==` / `!=`, never `is` / `is not`.
- Check output symbols: flows print with Unicode status symbols — `‣` scene start (uppercase action phrase), `⧗` in progress overwritten via `end="\r", flush=True`, `✔` success/up-to-date replacing the `⧗` line; scene sub-steps are indented two spaces and lowercased; tasks and utils print nothing.
- Check models: frozen dataclasses constructed with keyword arguments, no mutation.

Result: findings on deviations from documented conventions — each with file/location. Do not report PEP 8 nits or other undocumented style preferences as bugs.

### Area 4 — Error handling and edge cases

Steps:

- Check that only `RuntimeError` is raised, only in flows, only for user-facing configuration problems (unknown/missing chapter/scene); exactly one catch site at the CLI entry printing `✘ {error}`. Flag new exception classes, `try/except` elsewhere, or logging as findings — but do not flag the documented propagation of external tool failures (FFmpeg/poppler/Kokoro crash with a traceback) as a bug.
- Check that missing files return `None` / existence checks early-return rather than raising; `read_config` returns `None` for a missing file and flows raise `RuntimeError` on it.
- Probe edge cases: scene configs missing the `voice` or `frames` keys — shallow merge with `|` assumes the key exists (a missing nested key raises `KeyError`, not `RuntimeError`); malformed duplications strings (empty/garbage input to `int()`); optional start/end handling in frame extraction; empty chapters/scenes mappings (stitching zero inputs); chapter/scene ID mismatch between CLI argument and config.
- Check that cascade invalidation still deletes the right artifacts when a change is detected — e.g. voice text changes must not leave a stale result video behind, and frame changes must force downstream regeneration.

Result: findings on unhandled errors, wrong exception types, or edge cases that crash instead of degrading gracefully — each with file/location.

### Area 5 — Security concerns

Steps:

- Check user-controlled paths from JSON configs resolve relative to the config folder and cannot escape the intended tree via `../` segments in chapter/scene config-file references or PDF source paths (path traversal within the local filesystem).
- Check subprocess calls use no shell interpolation: FFmpeg/poppler invoked through `ffmpeg-python` / `pdf2image` with arguments passed as objects, never string-interpolated into a shell command; no `shell=True` anywhere.
- Note that MD5 is used for change detection only — it is not a security control and must not be presented as one.
- Check nothing writes outside the output tree or reads unintended files (source configs are read-only inputs; only cache copies under the output tree are written).

Result: findings on path traversal, shell injection, or unintended file access — each with file/location. This is a local CLI with no network surface; do not invent security issues beyond what the code actually does.

### Area 6 — Test coverage

Steps:

- Confirm there is no test suite (no framework, no CI, no test files) and report honestly that nothing is automated — do not demand tests be added unless asked; AGENTS.md explicitly says not to invent one.
- For changes with logic that can be exercised manually (cascade invalidation, duplications parsing, path resolution), note exactly what to run and what output to expect as the honest substitute for coverage.
- Flag untested paths as a Note/Low finding — informational, not blocking.

Result: findings on missing manual verification or logic that cannot be exercised at all — each with file/location.

### Area 7 — Potential regressions

Steps:

- Check incremental behavior end to end: re-running with an unchanged config prints UP-TO-DATE / returns without regenerating; changing a scene's voice text or PDF source triggers cascade invalidation (voice → frames → _frames → video → result) and only the stale tail re-runs.
- Check `updated` flag propagation: chapter/video stitching re-runs only when a child actually changed; `--chapter` / `--scene` delegation still returns the right boolean to its caller.
- Check order preservation across levels: chapters and scenes are processed in insertion order at every level, including the final stitch input list.
- Check CLI entry behavior: argparse required args (`--config`, `--output`) unchanged; optional `--chapter` / `--scene` still delegate correctly; `RuntimeError` is caught and printed as `✘ {error}` at exactly one site.

Result: findings on regressions to incremental builds, delegation, ordering, or CLI behavior — each with file/location.

## 4. Severity prioritization

Prioritize every finding by severity and order the report Critical → High → Medium → Low → Note:

- **Critical** — breaks correctness or data loss (e.g. cascade deletes wrong artifacts, insertion order reordered, writes outside the output tree).
- **High** — real bug affecting normal use (wrong artifact kept or deleted, stale cache not invalidated, crash on documented input).
- **Medium** — edge case that will bite later (malformed config handling, missing nested key raising `KeyError` instead of `RuntimeError`).
- **Low** — minor convention drift or inconsistency with the docs.
- **Note** — informational: no tests exist, manual verification gaps, non-blocking observations.

Do not pad the report with hypothetical problems to fill space; every finding must be actionable and tied to a specific file/location.

## 5. Output format (required for every finding)

Each finding must include:

- **Clear explanation** — what is wrong, in this project's terms.
- **Affected file and location** — path plus line or section (e.g. `tools/flows/scene.py`, `_update_cache`).
- **Why it matters** — impact on correctness, incremental builds, or user-facing behavior.
- **Suggested correction** — a concrete fix consistent with the project's conventions; do not redesign architecture or introduce new patterns.

Group findings by severity (not by area) and tag each finding with its area: correctness / architecture / conventions / error handling / security / tests / regressions. Omit areas with no findings rather than padding empty sections. End the report with a short verdict — ready to merge vs needs changes — plus an honest statement of what was not verified.

Illustrative example (format only, not a real finding):

```text
- Severity: High | Area: correctness
  Explanation: The chapter loop iterates a sorted copy of the chapters mapping instead of the original insertion order, changing render order.
  Location: tools/flows/video.py, _chapters (illustrative)
  Why it matters: Render order is part of the data contract; reordering changes which scenes appear first in the final video.
  Suggested correction: Iterate config.chapters directly and preserve insertion order — never sort or reorder chapter/scene mappings.
```

## 6. Rules for the reviewer

Steps:

- Report only — do not modify files during a review unless explicitly requested; if asked to fix, keep fixes scoped and say so.
- Focus on actionable findings; no long list of hypothetical problems; do not invent issues to fill space.
- Do not suggest architectural or coding convention improvements beyond flagging deviations from documented conventions — the docs are ground truth; anything undocumented is a preference, not a bug.
- Do not report stylistic preferences as bugs (e.g. PEP 8 nits); only documented conventions count.
- Use documentation primarily and avoid excessive codebase scanning — focus on the diff/files in scope.
- Stay within the project folder; do not go outside it.

Result: a report that is honest about what was checked, prioritized by severity, and free of invented problems.

## 7. Verification and honesty

Steps:

- If CLI behavior changed, run `path/to/pdf2vid --help` (or `python start.py --help` with the venv active) from the repo root to confirm argparse still parses — this exercises argument parsing without loading heavy dependencies.
- State what was checked versus what remains unverified; do not claim a review is complete if it was not run.

Result: an honest verification statement alongside the findings and verdict.
