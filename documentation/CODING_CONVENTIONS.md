# Coding Conventions — pdf2vid

This document describes the conventions in this codebase. Architecture and rationale live in [ARCHITECTURE.md](./ARCHITECTURE.md); this document focuses on code style and recurring patterns.

Each convention is marked with its scope:

- **(project-wide)** — used consistently across all applicable files
- **(area: `…`)** — used consistently only within a specific module or directory

Things that are *not* consistent are listed in [Inconsistencies — not conventions](#inconsistencies--not-conventions), and anything proposed as an improvement is clearly labeled in [Recommendations](#recommendations).

## 1. Project shape (context for the conventions below)

pdf2vid is a single-process Python 3.12 CLI. A tree of JSON configs (video → chapter → scene) drives a layered pipeline:

```
tools/generate.py   CLI layer (argparse, top-level error handling)
tools/flows/        orchestration, one module per hierarchy level (video, chapter, scene)
tools/tasks/        atomic operations, one module per operation, each wrapping one external tool
tools/models/       frozen dataclasses (the only classes in the codebase)
tools/utils/        small stateless helpers (config I/O, filesystem, hashing)
```

There is no web framework, no database, no DI container, and no test suite. The requested "controller / service / repository" roles are mapped to these layers in section 5.

## 2. Naming conventions

### Functions and variables — `snake_case` (project-wide)

All functions, variables, and arguments use `snake_case`, including boolean flags which use descriptive compound names (`*_updated`, `*_changed`, `already_existed`):

```python
def file_hash_changed(file_path, hash_path):        # tools/utils/hashing.py
def _assure_folders(config):                         # tools/flows/scene.py
    already_existed = _assure_folders(config)
scenes_changed = cached_config["scenes"] != config.scenes   # tools/flows/chapter.py
```

### Private helpers — `_` prefix (project-wide)

Anything not part of the public surface of a module is underscore-prefixed. Flow modules have exactly **one public function** (the entry point); everything else is private:

```python
def generate_scene(chapter_id, scene_id, config_file, output_folder):  # public
def _create_config(...):      # tools/flows/scene.py — all other helpers private
def _generate_file_hash(file_path):   # tools/utils/hashing.py
def _add_delay(audio, duration):      # tools/tasks/generate_voice.py
```

### Module-level constants — `SCREAMING_SNAKE_CASE`, at the top of the file (project-wide)

Every module-level constant is `SCREAMING_SNAKE_CASE` and sits directly above the functions that use it. There are two distinct flavors:

1. **Config defaults** — named after the config key, suffixed `_DEFAULT` (scalar) or `_DEFAULTS` (dict/list), placed in a `DEFAULTS` section:

    ```python
    CHAPTER_DEFAULT = "C1"                       # tools/flows/chapter.py
    DESCRIPTION_DEFAULT = ""
    SCENES_DEFAULT = []
    VOICE_DEFAULTS = { "speed": 1.0, "delay": 0.0 }      # tools/flows/scene.py
    FRAMES_DEFAULTS = { "start": None, "end": None, "duplications": "", "rate": 10 }
    ```

2. **Tuning/setting constants** in tasks and utils — plain descriptive names, no `DEFAULT` marker:

    ```python
    RESOLUTION = 200        # DPI, tools/tasks/extract_frames.py
    THREAD_COUNT = 4
    VOICE = "af_heart"      # tools/tasks/generate_voice.py
    SAMPLE_RATE = 24000
    CHUNK_SIZE = 4096       # tools/utils/hashing.py
    DEFAULT_FRAMERATE = 10  # tools/tasks/create_video.py (prefix form — the one exception)
    ```

### Classes — `PascalCase` (project-wide; models only)

All class names are `PascalCase` and all live in `tools/models/`: `Config`, `FolderPaths`, `FilePaths`, `VoiceOptions`, `FrameOptions`. There are no classes anywhere else in the codebase.

### Modules — one module per concept, `snake_case` (project-wide)

- `flows/` and `models/` mirror the content hierarchy: `video.py`, `chapter.py`, `scene.py`.
- `tasks/` are named after the operation they perform, and the **public function name equals the module name**: `extract_frames.py` → `extract_frames()`, `stitch_videos.py` → `stitch_videos()`.
- Flow entry points follow `generate_<level>`: `generate_video`, `generate_chapter`, `generate_scene`.
- Utils functions are `verb_noun` / `noun_verb` phrases: `read_config`, `join_paths`, `write_file_hash`.

### IDs and user-facing content

Chapter/scene identifiers follow `C1`, `S1` style (defaults `CHAPTER_DEFAULT = "C1"`, `SCENE_DEFAULT = "S1"`). Cross-level messages render them as `{chapter_id}:{scene_id}` (e.g. `"Unknown scene C1:S2"`).

## 3. Package and class organization

### One file per concept, per layer (project-wide)

| Layer | File layout | Public surface per file |
|---|---|---|
| `flows/` | one file per hierarchy level | exactly one function: `generate_<level>` |
| `tasks/` | one file per operation | exactly one function (plus `_`-prefixed helpers) |
| `models/` | one file per hierarchy level | 2–5 dataclasses |
| `utils/` | one file per concern (`config`, `filesystem`, `hashing`) | several small public functions — the one exception to "one public function" |

### Models: duplicated per level, never shared (project-wide)

Each model file redefines `Config`, `FolderPaths`, and `FilePaths` with the fields that level needs; there is no shared base class and no common module:

```python
# tools/models/chapter.py
@dataclass(frozen=True)
class FolderPaths:
    config: str
    output: str
    cache: str
    chapter: str

# tools/models/scene.py — different fields, same class name
@dataclass(frozen=True)
class FolderPaths:
    config: str
    chapter: str
    scene: str
    frames: str
    duplications: str
```

Scene is the only level that adds option classes (`VoiceOptions`, `FrameOptions`). Every flow imports its own level's models — e.g. `from ..models.chapter import FolderPaths, FilePaths, Config`.

## 4. Formatting and code organization

### File scaffolding (project-wide)

- **Every `.py` file begins with a blank line** (byte-verified: line 1 is empty in all 14 code files; `README.md` does the same). The `pdf2vid` entry script obviously starts with its shebang. The cause is not documented anywhere — it looks like a uniform editor setting rather than a deliberate style choice.
- **LF line endings, UTF-8**, single trailing newline at end of file.
- **4-space indentation**, no tabs.
- **No docstrings and no explanatory comments anywhere** in the code (verified: zero `"""` occurrences). The only comments are the section banners below.

### Section banners — `###` uppercase headers (area: `flows/`)

Flow modules are divided into sections using a banner of the exact form `### NAME ` followed by **26 `#` characters** (measured in all 14 banners):

```python
### DEFAULTS ##########################
### PROCESS ##########################
### CONFIG ##########################
### INITIALIZE ##########################
### GENERATE ##########################
### FINALIZE ##########################
```

Observed section sets:

- `video.py` / `chapter.py`: `DEFAULTS`, `PROCESS`, `CONFIG`, `PROCESS` (reappears for the internal processing steps)
- `scene.py`: `DEFAULTS`, `PROCESS`, `CONFIG`, `INITIALIZE`, `GENERATE`, `FINALIZE`

Sections are ordered as a template: defaults first, then the public entry point, then config construction, then the processing steps in execution order. `tasks/`, `models/`, and `utils/` do **not** use banners (utils modules are short enough that they are unnecessary).

### Function-body layout (project-wide)

- A **blank line follows every `def` line** (and every `for` line in flow loops) before the body starts:

    ```python
    def read_config(config_file):

        if not os.path.exists(config_file):
            return None
    ```

- A blank line typically precedes `return` statements in multi-line functions.
- Long multi-line calls list **one argument per line with no trailing commas** (e.g. the `Config(...)` constructions in all flows, the `ffmpeg...output(...)` blocks in `stitch_videos.py`).
- Default parameters are written **with spaces around `=`** — `def extract_frames(pdf_file, output_folder, start = None, end = None):` — which deviates from PEP 8 but is used consistently in both places that occur (`extract_frames`, `create_video`).
- `None` is compared with `==` / `!=`, never `is` / `is not` — 11 occurrences, all of the form `if data == None:` / `if scene_id != None:`.

### Imports (project-wide)

- **Relative imports** everywhere inside the package: `from ..models.scene import …`, `from ..utils.filesystem import …`, `from .flows.video import …`. The only absolute import is `import tools.generate` in the entry script, which is outside the package.
- Top-of-file imports are ordered: third-party imports first (in `tasks/`), then relative imports; within a file, model imports precede utils imports.
- **Lazy imports for heavy dependencies** — task and sub-flow modules are imported *inside the function* that calls them, after the artifact-existence check:

    ```python
    def _voiceover(config):
        ...
        if path_exists(files.voice):
            return

        print("  ⧗ Generating voice", end="\r", flush=True)

        from ..tasks.generate_voice import generate_voice   # kokoro/PyTorch loaded only if needed
        generate_voice(options.text, options.speed, options.delay, files.voice)
    ```

    This is deliberate (see "Lazy imports for heavy dependencies" in ARCHITECTURE.md): PyTorch/Kokoro and the FFmpeg bindings are only imported when work will actually happen. Light dependencies (`models`, `utils`) are imported at top of file. One task goes one level further: `import torch` inside `_add_delay` in `tools/tasks/generate_voice.py`.
- No `if __name__ == "__main__"` guards anywhere; the `pdf2vid` script is the only executable (`rwxr-xr-x`; all `.py` files are 644).

### Quotes (project-wide)

Double quotes are used everywhere — no exceptions.

## 5. "Controller / service / repository" patterns

There is no web framework, so these roles map to the project's four layers. The pattern for each is consistent:

### Controller → `tools/generate.py` (CLI)

Module-level, script-style code (not a class): build the `argparse.ArgumentParser`, add `--config` / `--output` (required) and `--chapter` / `--scene` (optional) arguments, `parse_args()`, call the single flow entry point, and catch `RuntimeError`:

```python
parser = argparse.ArgumentParser(description="Generates a scene from configuration.")
parser.add_argument("--config", type=str, required=True, help="The video configuration.")
...
args = parser.parse_args()

from .flows.video import generate_video

try:
    generate_video(args.config, args.output, args.chapter, args.scene)
except RuntimeError as error:
    print(f"✘ {error}")
```

Note the flow import happens *after* `parse_args()` — invalid arguments exit before any flow code is loaded.

### Service → `tools/flows/*.py`

Each flow module implements one level of the hierarchy with a fixed internal template:

1. **Entry point** `generate_<level>(…)` — builds the level's `Config`, then branches: if a child id (`--chapter` / `--scene`) was given, delegate to exactly one child; otherwise run the whole level.
2. **Config construction** — `_create_config` plus `_create_folder_paths` / `_create_file_paths` (and per-level `_create_*_options` at scene level) turn the raw JSON dict + CLI args into a frozen `Config`.
3. **Initialize** — `_assure_folders` (create if missing) then `_update_cache` (diff cached config against source; delete stale artifacts in a cascade).
4. **Generate** — recursively delegate to the flow one level below (imported lazily), or run the scene's five-step pipeline (`_voiceover`, `_frames`, `_duplications`, `_video`, `_result`), then `_chapter` / `_video` to stitch with `stitch_videos`.
5. **Finalize** — `_finalize` copies the source config to the cache `config.json` for the next run's change detection.

The uniform return contract is a **boolean `updated` flag** propagated scene → chapter → video, so parent stitching re-runs only when a child actually changed:

```python
def _generate_video(config):
    config_updated = _initialize(config)
    chapters_updated = _chapters(config)
    updated = config_updated or chapters_updated
    if not updated:
        print(f"✔ VIDEO UP-TO-DATE")
        return False
    _video(config)
    _finalize(config)
    return True
```

### Repository / adapter → `tools/tasks/*.py`

Each task is a **stateless function wrapping exactly one external tool** (FFmpeg via `ffmpeg-python`, poppler via `pdf2image`, Kokoro + `soundfile` for TTS) or one plain file operation. Tasks:

- receive **all paths as arguments** and know nothing about the output tree layout;
- never import flows (verified: no such imports exist);
- produce the artifact and nothing else — no printing, no change detection, no retries.

```python
def add_audio(video_file, audio_file, output_file):      # tools/tasks/add_audio.py
    video_input = ffmpeg.input(video_file)
    audio_input = ffmpeg.input(audio_file)
    (
        ffmpeg
        .output(video_input, audio_input, output_file)
        .run(overwrite_output=True, quiet=True)
    )
```

`stitch_videos` is the one task reused at two levels (chapter and video) — same concat, different inputs.

### Data access → `tools/utils/*.py`

Small stateless helpers; no classes. `read_config` is the single JSON entry point and returns `None` for a missing file instead of raising. `hashing.py` is the only utils module that imports a sibling (`from .filesystem import read_file, write_file`).

## 6. Dependency injection

**There is no dependency injection.** No DI framework, no constructor injection, no global singletons, no registries. The two mechanisms that play that role:

1. **Plain function arguments** — every function receives everything it needs (paths, options, the `Config`) as explicit parameters. This is what keeps tasks swappable and utils stateless.
2. **The threaded `Config` object** — each flow builds one frozen `Config` (data + `FolderPaths` + `FilePaths`) and passes that single object to every private helper, instead of passing many individual arguments:

    ```python
    config = _create_config(config_file, output_folder)   # build once
    ...
    _initialize(config)    # every helper takes `config`
    _finalize(config)
    ```

Module imports are the only other "wiring" — and the lazy-import pattern (section 4) is how heavy dependencies are deferred.

## 7. Exception handling

Minimal, by design (the README states the tool has "minimal" error handling on purpose):

- **Only `RuntimeError` is raised**, only in `flows/`, only for user-facing configuration problems:

    ```python
    raise RuntimeError(f"Configuration not found for chapter {chapter_id}!")   # tools/flows/chapter.py
    raise RuntimeError(f"Unknown chapter {chapter_id}")                         # tools/flows/video.py
    ```

- **Exactly one catch site** in the whole codebase — the CLI entry (`tools/generate.py`), which prints `✘ {error}`.
- **No custom exception classes, no `try/except` anywhere else, no `logging`.** Failures from external tools (FFmpeg, poppler, Kokoro) propagate uncaught and crash with a traceback.
- Missing *files* are not errors at the utils level: `read_config` and `read_file` return `None`, and existence checks return early (`if path_exists(...): return`) — the "not there" state is handled by the incremental-build logic, not by exceptions.

## 8. Validation strategy

No validation library and no runtime type checks — the strategy is **defaults plus lenient access**:

1. **Top-level config keys** fall back to module constants via `dict.get(key, DEFAULT)`:

    ```python
    description = data.get("description", DESCRIPTION_DEFAULT)
    scenes = data.get("scenes", SCENES_DEFAULT)
    ```

2. **Scene sub-objects** are shallow-merged with default dicts using the `|` operator, so any key present in the file wins:

    ```python
    data["voice"] = VOICE_DEFAULTS | data["voice"]
    data["frames"] = FRAMES_DEFAULTS | data["frames"]
    ```

3. **No required-key enforcement and no type checks** — a missing nested key simply yields `None` inside the frozen dataclass (the annotations are not enforced).
4. **The only hard validation** is `argparse` (`required=True` for `--config` / `--output`) and the `RuntimeError`s for missing/unknown configs (section 7).
5. **Order is part of the data contract**: chapter/scene lists are `dict[str, str]` ID → config-file mappings whose *insertion order* is the render order — no separate ordering field.

## 9. Logging strategy

There is no `logging` module — **all output is `print()` to stdout**, including the single error case. The convention is a small set of **Unicode status symbols** with a consistent message shape:

| Symbol | Meaning | Example |
|---|---|---|
| `‣` | scene start (level headline) | `‣ GENERATING SCENE C1:S1` |
| `⧗` | step in progress — printed with `end="\r", flush=True` so it is overwritten in place | `⧗ GENERATING CHAPTER C1` |
| `✔` | success / up-to-date — replaces the `⧗` line | `✔ GENERATED CHAPTER C1 -> /path/C1.mp4` |
| `✘` | error (CLI only) | `✘ Configuration not found for chapter C1!` |

Style details, consistent across `flows/` and `generate.py` (and **nowhere else** — tasks and utils print nothing):

- Level events use **uppercase action phrases**: `⧗ GENERATING VIDEO`, `✔ GENERATED VIDEO -> <path>`, `✔ SCENE C1:S1 UP-TO-DATE`.
- Scene sub-steps (the deepest level) are **indented two spaces and lowercased**: `  ⧗ Generating voice`, `  ✔ Generated voice -> <path>`.
- Every `⧗` line is paired with a terminal `✔` line on the same console row (`end="\r"` overwrites).
- No log levels, timestamps, or stderr separation.
- One module-level side effect: `warnings.filterwarnings("ignore")` at import time in `tools/tasks/generate_voice.py` silences Kokoro/PyTorch warnings.

## 10. DTOs and entity handling

There is no database, so "entities" are the JSON config tree and its in-memory representation:

- **Source of truth** = the JSON config files (video/chapter/scene). They are read-only inputs; the tool never writes back to a source config.
- **In-memory DTO** = the frozen dataclasses in `tools/models/`. Every flow converts its JSON dict into one `Config` value object that is the *only* object threaded through its private helpers; raw dicts are not passed to pipeline steps.
- **`FolderPaths` / `FilePaths` encapsulate the output layout** — the tree shape (`chapters/<C>/<scenes>/<S>/…`) exists only inside flow `_create_*_paths` functions and the model fields. Tasks receive flat paths and never learn the layout.
- **Immutability is total** — `@dataclass(frozen=True)` everywhere, construction with keyword arguments, no mutation, no update methods. Invalidation is expressed as *deleting artifacts from disk* (cascade invalidation), never as changing model state.
- **The filesystem is the state store**: cached `config.json` copies (one per level, written by every `_finalize`), the `frames.md5` PDF hash, and artifact existence checks are the entire persistence layer.

## 11. Testing patterns

**There are no tests.** No test files exist anywhere in the repository, no test framework appears in `requirements.txt`, and there is no CI configuration. Nothing in the codebase establishes a testing convention (no naming, layout, or fixture patterns to document). See [Recommendations](#recommendations).

## 12. Area-specific patterns (not project-wide)

- **Section banners** — `flows/` only (section 4).
- **Module-level `warnings.filterwarnings("ignore")`** — `tasks/generate_voice.py` only.
- **Deep lazy import** (`import torch` inside a function) — `tasks/generate_voice.py` only; every other heavy import sits at task-module level.
- **Frame numbering** — tasks that touch PNG frames use zero-padded 3-digit names: `f"{index + 1:03}.png"` (extract), `str(offset).zfill(3)` (duplicate), `join_paths(input_folder, "%03d.png")` (create).
- **Chunked file reading** — `utils/hashing.py` reads in `CHUNK_SIZE = 4096` blocks so large PDFs are not loaded whole.
- **Per-step existence guards** (`if path_exists(…): return` at the top of each scene pipeline step) — `flows/scene.py` only; the other flows use the coarser cached-config diff.

## 13. Inconsistencies — not conventions

The following do **not** qualify as established conventions and should not be followed as if they were:

None currently — all previously listed items have been fixed (see git history).

## 14. Recommendations

These are **suggestions, not current conventions**, and are not followed today:

1. The uniform leading blank line in every file looks like an editor artifact; if it is not intentional, it can be dropped without changing any code.
2. The "one module per concept, one public function" rule is a strong, easily-extended structure — new operations should keep following it (a new task = a new file with one public function that shadows the module name).

## Appendix: observed repository conventions (non-code)

- **Commit messages** (from `git log`): one short line, verb-led, sentence case, no trailing period — e.g. `Added basic error detection`, `Cleaned up error message`, `Fixed audio sync issue`.
- **`.gitignore`** ignores only `__pycache__` — no venv, no output directories (generated output is expected to live outside the repo, e.g. `dist`).
- **`README.md`** documents user-facing behavior (config schemas, CLI usage) and explicitly states the "works for us" minimal-validation stance; `documentation/` holds deep-dive docs (ARCHITECTURE.md, this file).
