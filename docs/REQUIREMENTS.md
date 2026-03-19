---
title: "shellScripts Requirements"
description: Software requirements specification
version: "0.1.1"
date: "2026-03-19"
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
shellScripts is a Python CLI package that dispatches utility subcommands for AI tool bootstrapping, PDF operations, DICOM operations, Double Commander integrations, project environment management, and editor/theme helpers.

Repository structure (evidence-oriented view, depth-limited):

```text
.
├── .github/
│   └── workflows/
│       └── release.yml
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
│   │       ├── bin_links.py
│   │       ├── clean.py
│   │       ├── cli_*.py
│   │       ├── dc_*.py
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
| GitHub Actions release pipeline | CI/CD component | `.github/workflows/release.yml` |
| External CLI tools (e.g., qpdf, pdftk, gs, doxygen, java, plakativ) | System dependencies invoked by subprocess/exec | direct imports and command invocations in `src/shell_scripts/commands/*.py` |

## 2. Project Requirements

### 2.1 Project Functions
- **PRJ-001**: MUST parse CLI arguments and route execution to management flags or registered subcommands with explicit process return codes.
- **PRJ-002**: MUST provide global help and command-specific help outputs through text-based terminal UI.
- **PRJ-003**: MUST expose subcommands for AI CLI installation/launch, PDF utilities, DICOM utilities, Double Commander dispatching, environment/test management, editor launchers, theme application, symlink maintenance, and cache cleanup.
- **PRJ-004**: MUST perform startup version-update checks against GitHub releases with cooldown caching.
- **PRJ-005**: MUST publish package releases through a GitHub Actions workflow triggered by version tag pushes.

### 2.2 Project Constraints
- **CTN-001**: MUST target Python runtime version 3.11 or newer.
- **CTN-002**: MUST expose console scripts `shellscripts` and `s` mapped to `shell_scripts.core:main`.
- **CTN-003**: MUST depend on external system executables for multiple subcommands and MUST fail fast when required executables are unavailable.
- **CTN-004**: MUST restrict automatic self-upgrade and self-uninstall actions to Linux platforms and MUST print manual fallback commands on non-Linux platforms.
- **CTN-005**: MUST treat Git repository root detection as a hard prerequisite for project-context commands.

## 3. Requirements

### 3.1 Design and Implementation
- **DES-001**: MUST implement command discovery with a static command-to-module mapping and lazy module imports.
- **DES-002**: MUST execute update-check logic before normal CLI argument dispatch.
- **DES-003**: MUST persist update-check cooldown state in `~/.cache/shellscripts/check_version_idle-time.json`.
- **DES-004**: MUST apply a minimum cooldown of 300 seconds after successful update checks and after HTTP 403 responses.
- **DES-005**: MUST apply HTTP 429 `Retry-After` cooldown when larger than default and MUST preserve a longer existing cooldown value.
- **DES-006**: MUST suppress non-HTTP update-check exceptions without aborting command execution.
- **DES-007**: MUST implement `double-commander-*` commands as wrappers around shared MIME-based dispatch logic in `_dc_common`.
- **DES-008**: MUST expose command modules with `DESCRIPTION`, `print_help(version)`, and `run(args)` call patterns.
- **DES-009**: MUST recreate `.venv` whenever `.venv` already exists in `venv` command execution and `--force` MUST NOT change this behavior.
- **DES-010**: MUST request deletion confirmation in `clean` unless `--yes` is provided.
- **DES-011**: MUST define the release workflow trigger on push events for tags matching `v*`.
- **DES-012**: MUST execute release workflow steps in order: checkout, Python setup, build dependency installation, package build, version extraction, and GitHub release creation.
- **DES-013**: MUST derive release display version by removing prefix `refs/tags/v` from `GITHUB_REF` and exporting it through step outputs.

No explicit performance optimizations identified.

### 3.2 Functions
- **REQ-001**: MUST print global help and return code `0` when invoked without CLI arguments.
- **REQ-002**: MUST print an error plus global help and return code `1` when the first argument is an unknown command.
- **REQ-003**: MUST print the package version and return code `0` for `--version` and `--ver`.
- **REQ-004**: MUST run `uv tool install shellscripts --force --from git+https://github.com/Ogekuri/shellScripts.git` for `--upgrade` on Linux.
- **REQ-005**: MUST run `uv tool uninstall shellscripts` for `--uninstall` on Linux.
- **REQ-006**: MUST execute all AI installers by default in `ai-install` when no selector options are provided.
- **REQ-007**: MUST reject unknown `ai-install` selector options with return code `1`.
- **REQ-008**: MUST install Codex, Copilot, Gemini, and OpenCode CLIs via `sudo npm install -g` commands.
- **REQ-009**: MUST install Claude CLI by downloading `latest` version metadata and installing an executable binary at `~/.claude/bin/claude`.
- **REQ-010**: MUST install Kiro CLI by downloading a ZIP archive, extracting binaries, and copying `kiro-cli*` executables into `~/.local/bin` with executable permissions.
- **REQ-011**: MUST create destination directory in `bin-links` and strip `.sh` suffixes when generating symlink names.
- **REQ-012**: MUST update mismatched existing symlinks in `bin-links` and MUST NOT overwrite regular files at destination paths.
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
- **REQ-023**: MUST return code `2` in `double-commander-*` commands when required file argument is missing.
- **REQ-024**: MUST classify files by MIME and extension in `_dc_common.categorize` and dispatch execution to category-specific command mappings.
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
- **REQ-039**: MUST run release workflow on `ubuntu-latest` with `permissions.contents` set to `write`.
- **REQ-040**: MUST install build dependencies with `python -m pip install --upgrade pip` and `pip install setuptools wheel build`, then execute `python -m build`.
- **REQ-041**: MUST create a GitHub release with `softprops/action-gh-release@v2`, attaching `dist/*.whl` and `dist/*.tar.gz`, and enabling generated release notes.
- **REQ-042**: MUST set release body install command to `uv tool install shellscripts --from git+https://github.com/Ogekuri/shellScripts.git@${{ github.ref_name }}` and upgrade command to `shellscripts --upgrade`.

## 4. Test Requirements

### 4.1 Coverage Summary
No unit test source files were found under `tests/` at generation time.
Implemented verification support exists via the `tests` command (`tests_cmd.py`), which executes pytest in `.venv` with `PYTHONPATH` set to `src`.
High-risk areas without observed unit-test evidence are PDF transformation pipelines, TOC rewriting logic, and subprocess/`os.execvp` integrations with system tools.

### 4.2 Verification Requirements
- **TST-001**: MUST verify REQ-001 and REQ-002 by invoking `shell_scripts.core.main` with empty and unknown arguments, passing only if return codes and help/error outputs match specified behavior.
- **TST-002**: MUST verify REQ-004 and REQ-005 on Linux by monkeypatching `subprocess.run` and asserting exact generated `uv tool` commands and propagated return codes.
- **TST-003**: MUST verify REQ-006 through REQ-010 by monkeypatching installer call sites and passing only if option parsing selects expected installer sets and unknown options return code `1`.
- **TST-004**: MUST verify REQ-011 through REQ-013 using temporary directories, passing only if symlink update rules and cache-deletion confirmation gates behave exactly as specified.
- **TST-005**: MUST verify REQ-014 through REQ-021 by monkeypatching `os.execvp` and environment state, passing only if executables, arguments, and `CODEX_HOME` assignments match requirements.
- **TST-006**: MUST verify REQ-023 and REQ-024 with file fixtures and mocked MIME detection, passing only if missing-file-argument status is `2` and category dispatch selects mapped commands.
- **TST-007**: MUST verify REQ-030 through REQ-035 by monkeypatching subprocess calls, passing only if expected qpdf/pdftk/gs invocation sequences and page-range validation outcomes are observed.
- **TST-008**: MUST verify REQ-036 through REQ-038 using isolated project roots, passing only if `.venv` lifecycle and conditional `requirements.txt` installation behavior match specified logic.
- **TST-009**: MUST verify REQ-039 through REQ-042 by parsing `.github/workflows/release.yml` and asserting trigger, runner, release action configuration, artifact globs, and release body command strings.

## 5. Evidence

| Requirement IDs | File Path | Symbol / Function | Short Evidence Excerpt |
|---|---|---|---|
| PRJ-001, PRJ-002, REQ-001, REQ-002, REQ-003 | `src/shell_scripts/core.py` | `main`, `print_help` | `if not args: print_help(); return 0`, unknown command path returns `1`, `--version` and `--ver` print `__version__`. |
| PRJ-003, DES-001, DES-008 | `src/shell_scripts/commands/__init__.py` | `_COMMAND_MODULES`, `get_command`, `get_all_commands` | Static mapping, lazy `importlib.import_module`, descriptions sourced from module `DESCRIPTION`. |
| PRJ-004, DES-002..DES-006 | `src/shell_scripts/version_check.py`; `src/shell_scripts/core.py` | `check_for_updates`, `_write_idle_config`, `_should_check` | Uses GitHub latest release API, 300s cooldown, 429/403 handling, cache path under `~/.cache/shellscripts`. |
| PRJ-005, DES-011, DES-012, DES-013, REQ-039, REQ-040, REQ-041, REQ-042 | `.github/workflows/release.yml` | `jobs.release`, `steps.version`, `steps.Create GitHub Release` | Tag trigger `v*`, ordered build-and-release steps, version output extraction from `GITHUB_REF`, release action, artifact globs, and release body install/upgrade commands. |
| CTN-001 | `pyproject.toml` | `[project].requires-python` | `requires-python = ">=3.11"`. |
| CTN-002 | `pyproject.toml` | `[project.scripts]` | `shellscripts = "shell_scripts.core:main"`, `s = "shell_scripts.core:main"`. |
| CTN-003 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/*.py` | `require_commands`, command `run` functions | Multiple commands call `require_commands(...)` and terminate on missing tools. |
| CTN-004, REQ-004, REQ-005 | `src/shell_scripts/core.py`; `src/shell_scripts/utils.py` | `do_upgrade`, `do_uninstall`, `is_linux` | Linux executes `uv tool ...`; non-Linux prints manual command text and returns `0`. |
| CTN-005 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/cli_*.py` | `require_project_root`, `run` | Project-context commands call `require_project_root()` and exit on missing Git root. |
| DES-007, REQ-023, REQ-024 | `src/shell_scripts/commands/dc_*.py`; `src/shell_scripts/commands/_dc_common.py` | `run`, `dispatch`, `categorize` | `double-commander-*` wrappers call shared dispatch; missing file argument returns `2`; category routes by MIME/extension. |
| DES-009, REQ-038 | `src/shell_scripts/commands/venv_cmd.py` | `run` | `.venv` is removed in both `if force` and `else` branches; `--force` currently does not alter behavior. |
| DES-010, REQ-013 | `src/shell_scripts/commands/clean.py` | `run` | Prompts user before deletion unless `--yes`; deletes only confirmed directories. |
| REQ-006, REQ-007, REQ-008, REQ-009, REQ-010 | `src/shell_scripts/commands/ai_install.py` | `run`, `_install_npm_tool`, `_install_claude`, `_install_kiro` | Default installer selection is all tools; unknown options fail; npm/Claude/Kiro installers implemented via subprocess/download/extract/copy. |
| REQ-011, REQ-012 | `src/shell_scripts/commands/bin_links.py` | `run` | Creates destination directory, strips `.sh` suffix, updates mismatched symlinks, skips regular files to avoid data loss. |
| REQ-014 | `src/shell_scripts/commands/cli_codex.py` | `run` | Sets `CODEX_HOME=<project>/.codex`; executes `/usr/bin/codex --yolo`. |
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
| TST-001..TST-008 | `src/shell_scripts/core.py`; `src/shell_scripts/commands/*.py`; `src/shell_scripts/version_check.py`; `tests/` | multiple | Existing code paths define verifiable behaviors; no unit test files currently exist under `tests/` directory. |
