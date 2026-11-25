# AGENTS.md — pdf2vid

Guidance for AI coding agents working in this repository. Read [README.md](README.md) for user-facing usage and the config schemas, then [documentation/ARCHITECTURE.md](documentation/ARCHITECTURE.md) and [documentation/CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md) before making changes — this file summarizes them; it does not replace them.

## Project context

pdf2vid is a single-process Python 3.12 CLI that turns a tree of JSON configs (video → chapter → scene) into an MP4: PDF pages become frames, local Kokoro TTS produces the voice-over, and FFmpeg assembles everything. It is fully local — no network services or API keys.

The content hierarchy is mirrored everywhere: config tree, flow modules (`tools/flows/`), model modules (`tools/models/`), and output folder layout. Each level can be generated independently via `--chapter` / `--scene` flags. See [README.md](README.md) for the full usage and result-tree layout.

## Important architectural constraints

These are load-bearing; do not violate them without an explicit request:

- **Strict layering, one-way dependencies** — flows → tasks → utils; models are pure frozen data with no dependencies. Tasks never import flows. See [ARCHITECTURE.md](documentation/ARCHITECTURE.md) (Dependency layering).
- **Tasks wrap exactly one external tool each** (FFmpeg via `ffmpeg-python`, poppler via `pdf2image`, Kokoro + `soundfile` for TTS) or one plain file operation. Tasks receive all paths as arguments and know nothing about the output layout.
- **Filesystem is the build state** — incremental regeneration relies on cached `config.json` copies (one per level), artifact existence checks, and MD5 of the source PDF (`frames.md5`). Do not add a database or build system; extend this mechanism instead.
- **Cascade invalidation + skip-on-exists** — config diffing decides what to delete; each pipeline step then skips if its artifact already exists. Preserve both mechanisms when touching flows.
- **Lazy imports for heavy dependencies** — task and sub-flow modules are imported inside the function that calls them, after artifact-existence checks (PyTorch/Kokoro and FFmpeg bindings load only when work will happen). Light deps (`models`, `utils`) import at top of file.
- **Order is part of the data contract** — chapter/scene lists are `dict[str, str]` ID → relative config-file mappings whose insertion order is the render order. Do not reorder or sort them.
- **Minimal error handling by design** — only `RuntimeError` in flows (user-facing config problems); exactly one catch site at the CLI entry. No custom exception classes, no logging. See [CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md) §7.
- **Script-style distribution** — no packaging, no `__init__.py`; the extensionless `pdf2vid` bash script activates `.venv` and runs `start.py` → `tools.generate` from the repo root so the `tools` namespace package resolves.

## Coding conventions

Full details in [documentation/CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md); key points:

- **Naming** — `snake_case` for functions/variables (boolean flags use descriptive compound names like `*_updated`, `already_existed`); private helpers are `_`-prefixed; module constants are `SCREAMING_SNAKE_CASE` at the top of file; classes are `PascalCase` and live only in `tools/models/`.
- **One module per concept** — flows/models mirror the hierarchy (`video.py`, `chapter.py`, `scene.py`); tasks are named after the operation and their public function name equals the module name (e.g. `stitch_videos.py` → `stitch_videos()`). Flow entry points follow `generate_<level>`.
- **Models** — frozen `@dataclass(frozen=True)`, duplicated per level (no shared base class); scene adds `VoiceOptions` / `FrameOptions`. Every flow builds one frozen `Config` and threads it through its private helpers instead of passing many individual arguments.
- **Formatting** — LF line endings, UTF-8, single trailing newline, 4-space indentation; double quotes everywhere; blank line after every `def` (and after `for` lines in flow loops); no docstrings or explanatory comments (only the `### SECTION ###` banners in flows).
- **Imports** — relative imports inside the package; third-party first, then relative; model imports precede utils imports. Heavy deps are lazy (see above). No `if __name__ == "__main__"` guards.
- **Output** — all output is `print()` to stdout with Unicode status symbols (`‣` scene start, `⧗` in progress overwritten via `end="\r"`, `✔` success/up-to-date, `✘` error at CLI only). Tasks and utils print nothing. See [CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md) §9.
- **Validation** — defaults + lenient access (`dict.get(key, DEFAULT)`; scene sub-objects shallow-merged with `|`); no required-key enforcement or type checks beyond argparse and the flows' `RuntimeError`s. See [CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md) §8.

## Development and testing commands

There is **no test suite** — no tests, framework, or CI exist (see [CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md) §11). Do not invent a test command; do not add one without being asked.

Setup (macOS, per README):

```bash
brew install ffmpeg poppler
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the tool (from the repo root, via the entry script):

```bash
path/to/pdf2vid --config "config.json" --output "dist"                       # full video
path/to/pdf2vid --config "config.json" --output "dist" --chapter "C1"        # one chapter
path/to/pdf2vid --config "config.json" --output "dist" --chapter "C1" --scene "S1"  # one scene
```

`--help` prints the CLI arguments (`--config`, `--output` required; `--chapter`, `--scene` optional). There is no linting or formatting tool configured — match surrounding style by hand.

## Rules for modifying the codebase

- Keep changes scoped to what was asked; do not refactor unrelated code, add features, or "improve" conventions that are intentionally minimal (e.g. error handling).
- Preserve the layered structure: flows orchestrate and build `Config`s; tasks stay stateless single-tool wrappers; utils stay small and stateless; models stay frozen dataclasses with no dependencies.
- Keep one public function per flow/task module (utils are the exception); keep private helpers `_`-prefixed.
- Do not add logging, custom exceptions, DI frameworks, or a database — extend the existing filesystem-as-build-state mechanism instead.
- Preserve lazy imports for heavy dependencies and the artifact-existence guards in scene steps.
- Keep config order (insertion order) intact; never sort or reorder chapter/scene mappings.
- Do not write back to source JSON configs — they are read-only inputs. Only cache copies under the output tree are written.
- Follow [documentation/CODING_CONVENTIONS.md](documentation/CODING_CONVENTIONS.md) for style; when in doubt, match the surrounding file exactly (banners, blank lines after `def`, double quotes, `== None` comparisons).

## Verification requirements before completing a task

There is no automated test suite, so verification is manual and must be stated honestly:

1. Confirm the CLI still parses arguments — run `path/to/pdf2vid --help` (or `python start.py --help` with the venv active) from the repo root. This exercises argparse without loading heavy dependencies.
2. For changes to flows, tasks, or models, actually exercise the changed path by running the tool against a real config if one is available in the working tree; otherwise state explicitly that no sample config exists and the change was not run end-to-end (full runs require `ffmpeg`/`poppler` installed and load PyTorch/Kokoro, which are slow).
3. Confirm incremental behavior still works where relevant: re-running with an unchanged config should print "UP-TO-DATE" / return without regenerating; changing a scene's voice text or PDF source should trigger cascade invalidation (voice → frames → _frames → video → result) and only the stale tail re-runs.
4. Do not claim a task is verified if it was not run — say what was checked and what was not.
