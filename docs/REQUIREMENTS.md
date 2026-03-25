---
title: "shellScripts Requirements"
description: Software requirements specification
version: "0.3.0"
date: "2026-03-24"
author: "Auto-generated from repository evidence"
scope:
  paths:
    - "src/**/*.py"
    - "scripts/**/*.sh"
    - ".github/workflows/**/*.yml"
    - "pyproject.toml"
  excludes:
    - ".*/**"
    - "node_modules/**"
    - "dist/**"
    - "build/**"
    - "target/**"
    - ".venv/**"
    - ".git/**"
visibility: "draft"
tags: ["requirements", "srs", "llm-first"]
---

# shellScripts Requirements

## 1. Introduction

### 1.1 Document Rules
This document MUST be written and maintained in English.
This document MUST use RFC 2119 keywords exclusively (MUST, MUST NOT, SHOULD, SHOULD NOT, MAY) and MUST NOT use "shall".
Requirement IDs MUST be unique and stable and MUST NOT be renumbered or reused outside a dedicated renumbering workflow.
Every requirement line MUST use this exact format: `- **<ID>**: <RFC2119 keyword> <single-sentence requirement>.`
Each requirement MUST be atomic, single-sentence, testable, and targeted to automated parsing; target length MUST be 35 words or fewer.
Requirement ID prefixes used in this document are `PRJ`, `CTN`, `DES`, `REQ`, and `TST`.
On every modification, YAML front matter `date` and `version` MUST be updated and in-body revision history MUST NOT be added.

### 1.2 Project Scope
shellScripts is a Python CLI package that dispatches utility subcommands for AI tool bootstrapping, PDF operations, DICOM operations, generic file diff/edit/view dispatching, project environment management, and editor/theme helpers.

Repository structure (evidence-oriented view, depth-limited):

```text
.
├── .github/
│   └── workflows/
│       └── release-uvx.yml
├── docs/
├── scripts/
│   └── s.sh
├── src/
│   ├── shell_scripts/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── core.py
│   │   ├── utils.py
│   │   ├── version_check.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── ai_install.py
│   │       ├── clean.py
│   │       ├── cli_*.py
│   │       ├── {diff,edit,view}_cmd.py
│   │       ├── dicom*.py
│   │       ├── doxygen_cmd.py
│   │       ├── pdf_*.py
│   │       ├── tests_cmd.py
│   │       ├── ubuntu_dark_theme.py
│   │       ├── venv_cmd.py
│   │       ├── vscode_cmd.py
│   │       └── vsinsider_cmd.py
│   └── shellscripts.egg-info/
├── tests/
├── pyproject.toml
└── README.md
```

### 1.3 Implemented Components and Libraries
| Component | Classification | Evidence |
|---|---|---|
| Python 3.11+ | Runtime constraint | `pyproject.toml` `requires-python = ">=3.11"` |
| setuptools, wheel, build | Packaging toolchain | `pyproject.toml` `[build-system].requires` |
| pytest | Development dependency | `pyproject.toml` `[dependency-groups].dev = ["pytest"]` |
| GitHub automation workflow script | CI/CD component | `.github/workflows/release-uvx.yml` |
| External CLI tools (e.g., qpdf, pdftk, gs, doxygen, java, plakativ) | System dependencies invoked by subprocess/exec | direct imports and command invocations in `src/shell_scripts/commands/*.py` |

## 2. Project Requirements

### 2.1 Project Functions
- **PRJ-001**: MUST parse CLI arguments and route execution to management flags (`--version`, `--ver`, `--upgrade`, `--uninstall`, `--write-config`) or registered subcommands with explicit process return codes.
- **PRJ-002**: MUST provide global help and command-specific help outputs through text-based terminal UI.
- **PRJ-003**: MUST expose subcommands for AI CLI installation/launch, PDF utilities, DICOM utilities, generic file diff/edit/view dispatching, `req` bootstrap orchestration, environment/test management, editor launchers, theme application, and cache cleanup.
- **PRJ-004**: MUST perform startup version-update checks against GitHub releases with cooldown caching.
- **PRJ-005**: MUST include a GitHub automation workflow script at `.github/workflows/release-uvx.yml`.

### 2.2 Project Constraints
- **CTN-001**: MUST target Python runtime version 3.11 or newer.
- **CTN-002**: MUST expose console scripts `shellscripts` and `s` mapped to `shell_scripts.core:main`.
- **CTN-003**: MUST depend on external system executables for multiple subcommands and MUST fail fast when required executables are unavailable.
- **CTN-004**: MUST restrict automatic self-upgrade and self-uninstall actions to Linux platforms and MUST print manual fallback commands on non-Linux platforms.
- **CTN-005**: MUST treat Git repository root detection as a hard prerequisite for project-context commands.

## 3. Requirements

### 3.1 Design and Implementation
- **DES-001**: MUST implement command discovery with a static command-to-module mapping and lazy module imports.
- **DES-002**: MUST execute runtime OS detection and update-check logic before normal CLI argument dispatch.
- **DES-003**: MUST persist update-check cooldown state in `~/.cache/shellscripts/check_version_idle-time.json`.
- **DES-004**: MUST apply a minimum cooldown of 300 seconds after successful update checks and after HTTP 403 responses.
- **DES-005**: MUST apply HTTP 429 `Retry-After` cooldown when larger than default and MUST preserve a longer existing cooldown value.
- **DES-006**: MUST suppress non-HTTP update-check exceptions without aborting command execution.
- **DES-007**: MUST implement `diff`, `edit`, and `view` commands as wrappers around shared MIME-based dispatch logic in `_dc_common` and runtime-configurable command profiles.
- **DES-008**: MUST expose command modules with `DESCRIPTION`, `print_help(version)`, and `run(args)` call patterns.
- **DES-009**: MUST recreate `.venv` whenever `.venv` already exists in `venv` command execution and `--force` MUST NOT change this behavior.
- **DES-010**: MUST request deletion confirmation in `clean` unless `--yes` is provided.
- **DES-011**: MUST implement centralized runtime configuration loading from `~/.config/shellScripts/config.json` with recursive merge semantics where missing keys preserve hardcoded defaults, including `req` providers and static checks.
- **DES-012**: MUST provide a management operation that writes default runtime configuration JSON to `~/.config/shellScripts/config.json`, creating parent directories when absent.
- **DES-013**: MUST resolve `ai-install` npm command prefixes from detected runtime OS, omitting `sudo` on Windows and using `sudo` on non-Windows systems.

No explicit performance optimizations identified.

### 3.2 Functions
- **REQ-001**: MUST print global help and return code `0` when invoked without CLI arguments.
- **REQ-002**: MUST print an error plus global help and return code `1` when the first argument is an unknown command.
- **REQ-003**: MUST print the package version and return code `0` for `--version` and `--ver`.
- **REQ-004**: MUST execute the Linux `--upgrade` command from runtime config key `management.upgrade`, using default `uv tool install shellscripts --force --from git+https://github.com/Ogekuri/shellScripts.git` when unset.
- **REQ-005**: MUST execute the Linux `--uninstall` command from runtime config key `management.uninstall`, using default `uv tool uninstall shellscripts` when unset.
- **REQ-006**: MUST execute all AI installers by default in `ai-install` when no selector options are provided.
- **REQ-007**: MUST reject unknown `ai-install` selector options with return code `1`.
- **REQ-008**: MUST install Codex, Copilot, Gemini, and OpenCode CLIs via `npm install -g` commands without `sudo` on Windows and with `sudo` on non-Windows systems.
- **REQ-009**: MUST install Claude CLI by downloading `latest` version metadata and installing an executable binary at `~/.claude/bin/claude`.
- **REQ-010**: MUST install Kiro CLI by downloading a ZIP archive, extracting binaries, and copying `kiro-cli*` executables into `~/.local/bin` with executable permissions.
- **REQ-013**: MUST discover predefined cache directory names and delete them only after explicit confirmation or `--yes`.
- **REQ-014**: MUST execute `/usr/bin/codex --yolo` in `cli-codex` and MUST set `CODEX_HOME` to `<project-root>/.codex` before execution.
- **REQ-015**: MUST execute `/usr/bin/copilot --yolo --allow-all-tools` in `cli-copilot`.
- **REQ-016**: MUST execute `/usr/bin/gemini --yolo` in `cli-gemini`.
- **REQ-017**: MUST execute `~/.claude/bin/claude --dangerously-skip-permissions` in `cli-claude`.
- **REQ-018**: MUST execute `/usr/bin/opencode` in `cli-opencode`.
- **REQ-019**: MUST execute `~/.local/bin/kiro-cli` in `cli-kiro`.
- **REQ-020**: MUST open the project root in VS Code or VS Code Insiders commands and append the project path as final argument.
- **REQ-021**: MUST set `CODEX_HOME` to `<project-root>/.codex` before VS Code and VS Code Insiders command execution.
- **REQ-022**: MUST attempt GNOME GTK dark theme configuration via `gsettings` and MAY launch `gtk-chtheme`, `qt5ct`, and `qt6ct` when available.
- **REQ-023**: MUST print help using `diff`/`edit`/`view` command names and return code `2` when the required file argument is missing.
- **REQ-024**: MUST classify files by MIME and extension in `_dc_common.categorize` and dispatch execution using runtime-configured `diff`/`edit`/`view` command mappings with hardcoded defaults for missing keys.
- **REQ-025**: MUST execute PixelMed `DicomImageViewer` with discovered Java classpath in `dicomviewer` when `java-wrappers` and Java runtime are available.
- **REQ-026**: MUST execute PixelMed `ConsumerFormatImageMaker` in `dicom2jpg` using provided input DICOM and output JPEG paths.
- **REQ-027**: MUST regenerate Doxygen outputs under `<project-root>/doxygen` and remove preexisting html, markdown, pdf, latex, and xml output directories before generation.
- **REQ-028**: MUST build Doxygen PDF output only when both `make` and `pdflatex` are available and MUST log skip information otherwise.
- **REQ-029**: MUST run `plakativ` with A4 output and `_tiled-A4.pdf` naming in both `pdf-tiler-090` and `pdf-tiler-100` commands.
- **REQ-030**: MUST merge PDFs by decompressing inputs, concatenating pages, rebuilding deduplicated bookmark metadata with page offsets, and linearizing final output.
- **REQ-031**: MUST split PDFs by level-1 TOC entries in `pdf-split-by-toc` and rebase retained bookmark page numbers for each generated chunk.
- **REQ-032**: MUST split PDFs by page-format transitions in `pdf-split-by-format` and reapply in-range TOC entries when source TOC data is available.
- **REQ-033**: MUST generate `<basename>_toc-clean.pdf` outputs in `pdf-toc-clean` with bookmark entries outside valid page ranges removed.
- **REQ-034**: MUST support `pdf-crop` options `--bbox`, `--margins`, `--analyze-pages`, and `--pages` to compute final crop geometry prior to Ghostscript conversion.
- **REQ-035**: MUST parse page-range expressions in `pdf-crop` using exactly `N`, `N-`, `-N`, or `N-M` formats and MUST reject invalid ranges.
- **REQ-036**: MUST run pytest through `.venv/bin/python3` in `tests` and MUST prepend `<project-root>/src` to `PYTHONPATH`.
- **REQ-037**: MUST create `.venv` in `tests` when missing and MUST install `requirements.txt` only when that file exists.
- **REQ-038**: MUST recreate `.venv` in `venv` and MUST install `requirements.txt` when present; otherwise it MUST skip pip installation and continue successfully.
- **REQ-043**: MUST ensure `<project-root>/.codex/auth.json` is a symlink to `~/.codex/auth.json` before `cli-codex` executes `/usr/bin/codex --yolo`.
- **REQ-044**: MUST create the symlink and print an informational message when `<project-root>/.codex/auth.json` is not already that exact symlink.
- **REQ-045**: MUST load runtime configuration from `~/.config/shellScripts/config.json` during CLI startup, and MUST keep hardcoded defaults for missing file, missing keys, or invalid value types.
- **REQ-046**: MUST write the default runtime configuration JSON to `~/.config/shellScripts/config.json` and return code `0` when invoked with `--write-config`.
- **REQ-047**: MUST determine and cache the runtime operating system at CLI startup before command dispatch.
- **REQ-048**: MUST implement `req` command that removes predefined AI-integration directories and creates `guidelines`, `docs`, `tests`, `src`, `scripts`, and `.github/workflows` for each selected target directory.
- **REQ-049**: MUST invoke external `req` once per target directory using hardcoded arguments `--base`, `--docs-dir`, `--guidelines-dir`, three `--src-dir`, `--tests-dir`, and `--upgrade-guidelines`.
- **REQ-050**: MUST source repeated `--provider` and `--enable-static-check` arguments for `req` from runtime config and MUST use hardcoded defaults when config keys are missing or invalid.
- **REQ-051**: MUST target current directory when `req` is invoked without selector options.
- **REQ-052**: MUST make `req --dirs` target only first-level child directories and MUST exclude the current directory.
- **REQ-053**: MUST make `req --recursive` target all descendant directories and MUST exclude the current directory.
- **REQ-054**: MUST reject simultaneous `--dirs` and `--recursive` options in `req` with return code `1`.
- **REQ-055**: MUST expose a Linux-only `dng2hdr2jpg` command that accepts `dng2hdr2jpg <input.dng> <output.jpg>` and returns non-zero when required positional arguments are missing.
- **REQ-056**: MUST parse optional `--ev=<value>` and `--ev <value>` in `dng2hdr2jpg`, default EV to `2.0`, and reject unsupported or non-numeric EV values with return code `1`.
- **REQ-057**: MUST generate exactly three exposure images from one DNG input using `raw.postprocess(bright=<2^(-ev)|1.0|2^(ev)>, output_bps=16, use_camera_wb=True, no_auto_bright=True, gamma=<selected_gamma>)` before HDR merge.
- **REQ-058**: MUST execute HDR merge via `enfuse` over three generated exposure files when `--enable-enfuse` is selected, MUST persist an intermediate 16-bit TIFF, and MUST use lossless TIFF compression before JPG conversion.
- **REQ-059**: MUST print a non-Linux unavailability message that includes target OS label (`Windows` or `MacOS`) in `dng2hdr2jpg`, and MUST return non-zero while preserving Linux temporary-file cleanup and dependency-failure behavior.
- **REQ-060**: MUST require exactly one backend selector in `dng2hdr2jpg` (`--enable-enfuse` or `--enable-luminance`) and MUST return `1` when neither or both selectors are provided.
- **REQ-061**: MUST parse `--luminance-hdr-model`, `--luminance-hdr-weight`, `--luminance-hdr-response-curve`, and `--luminance-tmo` in assignment or split form, default `--luminance-hdr-weight` to `flat` and `--luminance-tmo` to `reinhard02`, and return `1` for malformed values.
- **REQ-062**: MUST execute `luminance-hdr-cli` with `-e <-ev,0,+ev>`, `--hdrModel`, `--hdrWeight`, `--hdrResponseCurve`, `--tmo`, `--ldrTiff 16b`, and ordered inputs `<ev_minus.tif> <ev_zero.tif> <ev_plus.tif>` writing `<merged_hdr.tif>`.
- **REQ-063**: MUST document required backend selectors, luminance controls, `--gamma`, postprocess controls, `--magic-retouch` controls, generic passthrough `--tmo*` options, and control-table rows only for operators with exposed CLI controls.
- **REQ-070**: MUST render in `dng2hdr2jpg` help two aligned Unicode box-drawing tables where the operators table uses three columns, two-line headers, and two physical lines per operator row.
- **REQ-064**: MUST parse optional `--gamma=<a,b>` and `--gamma <a,b>` in `dng2hdr2jpg`, default gamma to `(2.222,4.5)`, and reject malformed, non-numeric, or non-positive gamma values with return code `1`.
- **REQ-065**: MUST parse optional `--post-gamma=<value>`, `--brightness=<value>`, `--contrast=<value>`, `--saturation=<value>`, and `--jpg-compression=<0..100>`, and MUST default `--jpg-compression` to `15`.
- **REQ-066**: MUST execute `--post-gamma`, `--brightness`, `--contrast`, and `--saturation` before JPG conversion as an in-memory 16-bit-per-channel lossless postprocess stage, and MUST convert output to uint8 using deterministic rounded ordered dithering.
- **REQ-067**: MUST parse explicit CLI options starting with `--tmo` in assignment or split form when `--enable-luminance` is set, preserve CLI order, and return `1` for missing or empty values.
- **REQ-068**: MUST pass only `--hdrModel`, `--hdrWeight`, `--hdrResponseCurve`, `--tmo`, and `--ldrTiff 16b` by default, forwarding additional `--tmo*` options only when explicitly provided on CLI.
- **REQ-069**: MUST default luminance-mode postprocess factors to `post-gamma=1.0`, `brightness=1.25`, `contrast=0.85`, and `saturation=0.55` when `--luminance-tmo` is `reinhard02` and no explicit postprocess overrides are provided.
- **REQ-071**: MUST default luminance-mode postprocess factors to `1.0` for `post-gamma`, `brightness`, `contrast`, and `saturation` when `--luminance-tmo` is not `reinhard02` and no explicit postprocess overrides are provided.
- **REQ-072**: MUST default enfuse-mode postprocess factors to `1.0` for `post-gamma`, `brightness`, `contrast`, and `saturation` when no explicit postprocess overrides are provided.
- **REQ-073**: MUST parse `--magic-retouch`, `--magic-denoise-strength`, `--magic-gamma-bias`, `--magic-clahe-clip-limit`, `--magic-vibrance-strength`, `--magic-sharpen-strength`, and `--magic-sharpen-threshold` options in assignment or split form.
- **REQ-074**: MUST execute `magic_retouch` only when `--magic-retouch` is enabled, positioned after 16-bit postprocess and before JPG encoding, and MUST bypass it when the flag is omitted.
- **REQ-075**: MUST implement `magic_retouch` as deterministic adaptive OpenCV processing on RGB float payloads with ordered stages: parameterized denoise, luminance-aware gamma, optional local contrast enhancement, conditional vibrance, and conditional edge-masked sharpening; denoise MUST always be computed when `--magic-denoise-strength>0` and MUST be bypassed when `--magic-denoise-strength=0`.
- **REQ-076**: MUST execute `magic_retouch` in-memory on lossless 16-bit-per-channel image data and forward its output directly to the JPG conversion/compression stage.
- **REQ-077**: MUST declare Linux runtime dependencies `opencv-python` and `numpy` in package metadata so Astral `uv` installations include required `magic_retouch` runtime modules.
- **REQ-078**: MUST default `magic_retouch` options to neutral values and MUST reject removed legacy magic options (pre-refactor and filter-based controls) with return code `1`.
- **REQ-079**: MUST encode final JPEG with `optimize=True`, `progressive=True`, and `subsampling=0` (`4:4:4`) while preserving `--jpg-compression` quality mapping to minimize visible compression artifacts.

## 4. Test Requirements

### 4.1 Coverage Summary
No unit test source files were found under `tests/` at generation time.
Implemented verification support exists via the `tests` command (`tests_cmd.py`), which executes pytest in `.venv` with `PYTHONPATH` set to `src`.
High-risk areas without observed unit-test evidence are PDF transformation pipelines, TOC rewriting logic, and subprocess/`os.execvp` integrations with system tools.

### 4.2 Verification Requirements
- **TST-001**: MUST verify REQ-001, REQ-002, and REQ-047 by invoking `shell_scripts.core.main`, passing only if return codes, help/error outputs, and startup OS-detection invocation match specified behavior.
- **TST-002**: MUST verify REQ-004 and REQ-005 on Linux by monkeypatching `subprocess.run` and asserting command values resolved from runtime config with default command fallback and propagated return codes.
- **TST-003**: MUST verify REQ-006 through REQ-010 by monkeypatching installer call sites and passing only if selector parsing is correct, unknown options return code `1`, and REQ-008 `sudo` usage changes by runtime OS.
- **TST-004**: MUST verify REQ-013 using temporary directories, passing only if cache-deletion confirmation gates behave exactly as specified.
- **TST-005**: MUST verify REQ-014 through REQ-021 and REQ-043 through REQ-044 by monkeypatching `os.execvp` and filesystem/environment state, passing only if executable args, `CODEX_HOME`, and codex auth symlink behavior match requirements.
- **TST-006**: MUST verify REQ-023 and REQ-024, passing only if help output uses `diff`/`edit`/`view`, missing-file-argument status is `2`, and runtime-configured category dispatch selects mapped commands.
- **TST-009**: MUST verify REQ-045 and REQ-046 by monkeypatching config I/O boundaries and asserting startup load invocation plus `--write-config` success behavior.
- **TST-010**: MUST verify REQ-048 through REQ-054 by monkeypatching filesystem and subprocess boundaries, passing only if target selection and generated `req` argument vectors match required behavior.
- **TST-007**: MUST verify REQ-030 through REQ-035 by monkeypatching subprocess calls, passing only if expected qpdf/pdftk/gs invocation sequences and page-range validation outcomes are observed.
- **TST-008**: MUST verify REQ-036 through REQ-038 using isolated project roots, passing only if `.venv` lifecycle and conditional `requirements.txt` installation behavior match specified logic.
- **TST-011**: MUST verify REQ-055 through REQ-077 by monkeypatching RAW decode, image writes, and HDR subprocess calls, passing only if backend selection, parsing, help formatting, postprocess/magic flow, TIFF merge flow, and cleanup behavior match requirements.

## 5. Evidence

| Requirement IDs | File Path | Symbol / Function | Short Evidence Excerpt |
|---|---|---|---|
| PRJ-001, PRJ-002, REQ-001, REQ-002, REQ-003, REQ-047 | `src/shell_scripts/core.py` | `main`, `print_help` | Startup path detects runtime OS before dispatch; empty args print help and return `0`; unknown command path returns `1`; `--version` and `--ver` print `__version__`. |
| PRJ-003, DES-001, DES-008 | `src/shell_scripts/commands/__init__.py` | `_COMMAND_MODULES`, `get_command`, `get_all_commands` | Static mapping, lazy `importlib.import_module`, descriptions sourced from module `DESCRIPTION`. |
| PRJ-004, DES-002..DES-006 | `src/shell_scripts/version_check.py`; `src/shell_scripts/core.py` | `check_for_updates`, `_write_idle_config`, `_should_check` | Uses GitHub latest release API, 300s cooldown, 429/403 handling, cache path under `~/.cache/shellscripts`. |
| PRJ-005 | `.github/workflows/release-uvx.yml` | `jobs.check-branch`, `jobs.build-release` | Workflow script is present at required path and defines release automation jobs. |
| CTN-001 | `pyproject.toml` | `[project].requires-python` | `requires-python = ">=3.11"`. |
| CTN-002 | `pyproject.toml` | `[project.scripts]` | `shellscripts = "shell_scripts.core:main"`, `s = "shell_scripts.core:main"`. |
| CTN-003 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/*.py` | `require_commands`, command `run` functions | Multiple commands call `require_commands(...)` and terminate on missing tools. |
| CTN-004, REQ-004, REQ-005 | `src/shell_scripts/core.py`; `src/shell_scripts/utils.py` | `do_upgrade`, `do_uninstall`, `is_linux` | Linux executes `uv tool ...`; non-Linux prints manual command text and returns `0`. |
| CTN-005 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/cli_*.py` | `require_project_root`, `run` | Project-context commands call `require_project_root()` and exit on missing Git root. |
| DES-007, REQ-023, REQ-024 | `src/shell_scripts/commands/diff_cmd.py`; `src/shell_scripts/commands/edit_cmd.py`; `src/shell_scripts/commands/view_cmd.py`; `src/shell_scripts/commands/_dc_common.py` | `run`, `dispatch`, `categorize` | `diff`/`edit`/`view` wrappers call shared dispatch; missing file argument returns `2`; category routes by MIME/extension. |
| DES-009, REQ-038 | `src/shell_scripts/commands/venv_cmd.py` | `run` | `.venv` is removed in both `if force` and `else` branches; `--force` currently does not alter behavior. |
| DES-010, REQ-013 | `src/shell_scripts/commands/clean.py` | `run` | Prompts user before deletion unless `--yes`; deletes only confirmed directories. |
| REQ-006, REQ-007, REQ-008, REQ-009, REQ-010 | `src/shell_scripts/commands/ai_install.py` | `run`, `_install_npm_tool`, `_install_claude`, `_install_kiro` | Default installer selection is all tools; unknown options fail; npm install command omits `sudo` on Windows and uses `sudo` on non-Windows; Claude/Kiro installers use download/extract/copy flows. |
| REQ-014, REQ-043, REQ-044 | `src/shell_scripts/commands/cli_codex.py` | `run` | Sets `CODEX_HOME=<project>/.codex`; ensures `.codex/auth.json` symlink target `~/.codex/auth.json`; prints creation info when symlink is created; executes `/usr/bin/codex --yolo`. |
| REQ-015 | `src/shell_scripts/commands/cli_copilot.py` | `run` | Executes `/usr/bin/copilot --yolo --allow-all-tools`. |
| REQ-016 | `src/shell_scripts/commands/cli_gemini.py` | `run` | Executes `/usr/bin/gemini --yolo`. |
| REQ-017 | `src/shell_scripts/commands/cli_claude.py` | `run` | Executes `~/.claude/bin/claude --dangerously-skip-permissions`. |
| REQ-018 | `src/shell_scripts/commands/cli_opencode.py` | `run` | Executes `/usr/bin/opencode`. |
| REQ-019 | `src/shell_scripts/commands/cli_kiro.py` | `run` | Executes `~/.local/bin/kiro-cli`. |
| REQ-020, REQ-021 | `src/shell_scripts/commands/vscode_cmd.py`; `src/shell_scripts/commands/vsinsider_cmd.py` | `run` | Commands set `CODEX_HOME`, change to project root, and execute Code binaries with project path appended. |
| REQ-022 | `src/shell_scripts/commands/ubuntu_dark_theme.py` | `run` | Applies `gsettings ... gtk-theme Adwaita-dark` and conditionally launches `gtk-chtheme`, `qt5ct`, `qt6ct`. |
| REQ-025 | `src/shell_scripts/commands/dicomviewer.py` | `run`, `_find_jars` | Requires `java-wrappers` and Java runtime; executes `com.pixelmed.display.DicomImageViewer`. |
| REQ-026 | `src/shell_scripts/commands/dicom2jpg.py` | `run`, `_find_jars` | Requires two args, `java-wrappers`, Java runtime; executes `ConsumerFormatImageMaker` with input/output files. |
| REQ-027, REQ-028 | `src/shell_scripts/commands/doxygen_cmd.py` | `run`, `_write_doxyfile` | Clears existing output dirs, runs doxygen, optionally builds/refiles PDF when `make` and `pdflatex` exist. |
| REQ-029 | `src/shell_scripts/commands/pdf_tiler_090.py`; `src/shell_scripts/commands/pdf_tiler_100.py` | `run` | Both commands require `plakativ` and write `<stem>_tiled-A4.pdf`. |
| REQ-030 | `src/shell_scripts/commands/pdf_merge.py` | `run`, `_parse_bookmarks` | Decompresses with qpdf, merges via pdftk, rebuilds deduplicated bookmarks with offsets, linearizes output. |
| REQ-031 | `src/shell_scripts/commands/pdf_split_by_toc.py` | `run`, `_parse_level1_toc`, `_extract_toc_for_range` | Splits by level-1 TOC entries and rebases TOC pages in each extracted chunk. |
| REQ-032 | `src/shell_scripts/commands/pdf_split_by_format.py` | `run`, `_get_page_formats`, `_extract_toc_for_range` | Splits when page format changes and conditionally reapplies range-filtered TOC data. |
| REQ-033 | `src/shell_scripts/commands/pdf_toc_clean.py` | `run`, `_filter_bookmarks` | Outputs `_toc-clean.pdf` with bookmark entries filtered to valid page range. |
| REQ-034, REQ-035 | `src/shell_scripts/commands/pdf_crop.py` | `run`, `_parse_page_range`, `_compute_auto_bbox` | Supports bbox/margins/analyze-pages/pages options and validates range syntax `N`, `N-`, `-N`, `N-M`. |
| REQ-036, REQ-037 | `src/shell_scripts/commands/tests_cmd.py` | `run` | Creates `.venv` if missing, conditionally installs `requirements.txt`, runs pytest with `PYTHONPATH` prefixed by `src`. |
| REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054 | `src/shell_scripts/commands/req_cmd.py`; `src/shell_scripts/config.py` | `run`, `_build_req_args`, `get_req_profile` | `req` command resolves targets by selector mode, applies cleanup/scaffold operations, and executes external `req` with hardcoded base args plus runtime-configured providers/static checks. |
| TST-001..TST-008 | `src/shell_scripts/core.py`; `src/shell_scripts/commands/*.py`; `src/shell_scripts/version_check.py`; `tests/` | multiple | Existing code paths define verifiable behaviors; no unit test files currently exist under `tests/` directory. |
