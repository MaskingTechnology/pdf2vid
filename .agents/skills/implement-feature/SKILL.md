---
name: implement-feature
description: >-
  Implement a feature or change in this repository end to end — understand the request, map affected components, inspect existing patterns, plan, implement incrementally, update relevant documentation, verify honestly, and summarize. Use when asked to add or change behavior (new task, new option, flow/model changes); not for one-off questions or pure exploration.
---

# Implement Feature

Implement a feature in this repository end to end: understand the request, map affected components, inspect existing patterns, plan, implement incrementally, update relevant documentation, verify honestly, and summarize. This skill is reusable across different feature requests — read it as a checklist, not a script for one specific change.

## Grounding documents

Read before starting:

- `AGENTS.md` — project rules (layering, lazy imports, filesystem-as-build-state, minimal error handling).
- `documentation/ARCHITECTURE.md` — layered architecture, hierarchy mirroring, cascade invalidation + skip-on-exists, output layout.
- `documentation/CODING_CONVENTIONS.md` — naming, formatting, imports, validation, logging symbols.
- `README.md` — user-facing behavior (config schemas, CLI usage); update it when a feature changes what users see.

## 1. Understanding the feature request

Steps:

- Restate the goal in one or two sentences. Identify what kind of change this is — new capability, modification to existing behavior, or fix — and which hierarchy level(s) it touches (video / chapter / scene).
- List the constraints that apply before writing any code: strict layering (flows → tasks → utils; models are pure frozen data with no dependencies), lazy imports for heavy deps, order preservation in `dict[str, str]` ID → config-file mappings, minimal error handling (only `RuntimeError` in flows, one catch site at the CLI entry), and "no test suite" reality.
- Ask only genuinely blocking questions — anything answerable by reading the repo is looked up, not asked. Note out-of-scope items explicitly so they are not silently absorbed into the change.

Result: a short feature statement plus an explicit scope boundary (what is in and what is out).

## 2. Identifying affected components

Steps:

- Map the request onto the layers: flows orchestrate, tasks wrap exactly one external tool each, utils are small stateless helpers, models are frozen dataclasses (duplicated per level — no shared base class).
- Decide which files change and why: a new operation = a new task file with one public function whose name equals the module name; model changes = edits to that level's `Config` / `FolderPaths` / `FilePaths` (and scene adds `VoiceOptions` / `FrameOptions`); flow changes = orchestration only, never media-tool calls; utils additions = small stateless functions.
- Check whether the change is user-facing — new config keys, CLI flags, or output layout all require documentation updates in the same change (see section 6).

Result: an ordered list of files to touch and which layers/levels are affected.

## 3. Inspecting existing implementation patterns

Steps:

- Read the relevant flow / task / model / utils files before writing anything, and note the conventions they follow — do not invent new ones:
  - `snake_case` functions/variables; boolean flags use descriptive compound names (`*_updated`, `already_existed`). Private helpers are `_`-prefixed; flow modules have exactly one public function.
  - Module constants are `SCREAMING_SNAKE_CASE` at the top of file — config defaults suffixed `_DEFAULT` / `_DEFAULTS` in a `### DEFAULTS ###` section, tuning constants plain (e.g. `RESOLUTION = 200`).
  - Flows use `### SECTION ###` banners; tasks/models/utils do not. No docstrings or explanatory comments anywhere.
  - Double quotes everywhere; blank line after every `def` and after `for` lines in flow loops; LF endings, UTF-8, single trailing newline, 4-space indentation.
  - Models: frozen `@dataclass(frozen=True)`, constructed with keyword arguments, no mutation — invalidation is expressed as deleting artifacts from disk, never changing model state.
  - Validation is defaults + lenient access: top-level keys via `dict.get(key, DEFAULT)`; scene sub-objects shallow-merged with the `|` operator (e.g. `VOICE_DEFAULTS | data["voice"]`). No required-key enforcement or type checks beyond argparse and flow `RuntimeError`s.
  - Lazy imports for heavy dependencies inside the function that calls them, after artifact-existence checks — PyTorch/Kokoro and FFmpeg bindings load only when work will happen. Light deps (models, utils) import at top of file; model imports precede utils imports.
  - Output is `print()` to stdout with Unicode status symbols: `‣` scene start, `⧗` in progress overwritten via `end="\r"`, `✔` success/up-to-date, `✘` error at CLI only. Tasks and utils print nothing.
  - Scene steps use per-step existence guards (`if path_exists(...): return`); other flows use the coarser cached-config diff. Both compose so only the stale tail of the pipeline re-runs.

Result: a short list of patterns to mirror — and confirmation that no new conventions are needed.

## 4. Creating an implementation plan

Steps:

- Order steps in dependency order: models → utils → tasks → flows → CLI/docs (last). Each step should be small enough to verify on its own.
- Call out risks up front: cascade invalidation must still delete the right artifacts; insertion order of chapter/scene mappings is part of the data contract and must not change; lazy imports must stay inside functions after existence checks; source configs are read-only inputs — never write back to them (only cache copies under the output tree).
- Define verification up front: what command exercises the changed path, and whether a real sample config exists in the working tree.

Result: a numbered plan with files and a check per step.

## 5. Implementing the feature incrementally

Steps:

- Implement in dependency order (models first, then utils, tasks, flows, CLI/docs last); keep each change scoped to what was asked — no unrelated refactors or "improvements" of intentionally minimal conventions.
- Preserve layering: tasks never import flows; models have no dependencies; utils stay small and stateless. A new task is a new file with one public function that shadows the module name (e.g. `tools/tasks/extract_frames.py` → `extract_frames()`).
- Keep config order intact — never sort or reorder chapter/scene mappings; insertion order is the render order.
- If user-facing behavior changed, update the docs in the same change — see section 6.

Example of a new task following the pattern:

```python
import ffmpeg

from ..utils.filesystem import join_paths

def stitch_videos(input_folder, video_names, output_file):

    inputs = []

    for video_name in video_names:
        full_path = join_paths(input_folder, f"{video_name}.mp4")
        inputs.append(ffmpeg.input(full_path))

    stream_pairs = []

    for inp in inputs:
        stream_pairs.extend([inp.video, inp.audio])

    joined = ffmpeg.concat(*stream_pairs, v=1, a=1)
    joined = joined.filter("setpts", "PTS-STARTPTS")

    joined.output(
        output_file,
        vcodec="libx264",
        acodec="aac",
        strict="experimental",
        movflags="+faststart"
    ).run(overwrite_output=True, quiet=True)
```

Example of a flow step with lazy import and existence guard:

```python
def _voiceover(config):

    files = config.files
    options = config.voice

    if path_exists(files.voice):
        return

    print("  ⧗ Generating voice", end="\r", flush=True)

    from ..tasks.generate_voice import generate_voice   # kokoro/PyTorch loaded only if needed
    generate_voice(options.text, options.speed, options.delay, files.voice)

    print(f"  ✔ Generated voice -> {files.voice}")
```

Result: working code that follows the conventions and layering rules.

## 6. Updating relevant documentation

Steps:

- Identify which docs describe what changed, and update them in the same change as the code — never a separate pass or commit:
  - `README.md` documents user-facing behavior (config schemas, CLI usage, output layout). It must move whenever a feature changes what users see: new config keys, CLI flags, new levels/tasks visible to users, or output layout changes. Keep its style — short prose plus example configs and commands.
  - `documentation/ARCHITECTURE.md` documents the structural design (layering, hierarchy mirroring, cascade invalidation + skip-on-exists, folder structure). Update it when a feature adds or changes a structural concept: a new task module, a new flow step, a new hierarchy level, or a changed data contract — keep its component descriptions and folder tree accurate.
  - `documentation/CODING_CONVENTIONS.md` documents conventions, not features. Do not rewrite it for one feature's implementation details; touch it only if the change genuinely establishes a new convention (rare).
  - `AGENTS.md` holds project rules — update it only if those rules themselves changed, which is usually out of scope for a feature request.
- Document stable contracts, not internal implementation details that will drift: config schemas and CLI usage in README; architecture and data flow in ARCHITECTURE.md. Skip anything the repo does not already cover — do not invent new doc sections to fill space.
- Verify the docs match reality before finishing: run `--help` to confirm documented flags exist, check output layout against actual behavior, and re-read the changed section for stale claims. A stale doc is worse than none.

Result: README (and ARCHITECTURE.md when structural) updated in the same change as the code, with every claim verified against the running tool.

## 7. Writing or updating tests

Steps:

- Check for a test suite — none exists in this repository (no framework, no CI, no test files). Do not invent one, add a test command, or write tests without being asked; AGENTS.md explicitly says not to.
- If the feature adds logic that can be exercised manually, note exactly what to run and what output to expect — this is the honest substitute for automated coverage here.
- State plainly what was verified versus what remains untested (e.g. a new task path that needs ffmpeg/poppler installed).

Result: an explicit statement of what was checked and what was not.

## 8. Running relevant verification commands

Steps:

- Run `path/to/pdf2vid --help` (or `python start.py --help` with the venv active) from the repo root — this exercises argparse without loading heavy dependencies.
- For changes to flows, tasks, or models, actually exercise the changed path by running the tool against a real config if one is available in the working tree; otherwise state explicitly that no sample config exists and the change was not run end-to-end (full runs require `ffmpeg`/`poppler` installed and load PyTorch/Kokoro, which are slow).
- Confirm incremental behavior where relevant: re-running with an unchanged config should print "UP-TO-DATE" / return without regenerating; changing a scene's voice text or PDF source should trigger cascade invalidation (voice → frames → _frames → video → result) and only the stale tail re-runs.

Result: verification results stated honestly, including what was not run.

## 9. Summarizing the changes

Steps:

- List files changed and why; describe the behavior change in one or two sentences.
- Note anything not verified or not done (e.g. no sample config, heavy deps not exercised) — do not claim a task is verified if it was not run.
- Mention documentation updates (README / ARCHITECTURE.md) if any were made — see section 6.

Result: a concise summary of the diff plus its verification status.
