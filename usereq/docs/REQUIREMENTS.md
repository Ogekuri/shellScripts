---
title: "shellScripts Requirements"
description: Software requirements specification
version: "0.6.29"
date: "2026-11-08T16:19:16Z"
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
│       └── release-pypi.yml
├── docs/
├── scripts/
│   ├── pre-release-check.sh
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
│   │       ├── {claude,codex,copilot,gemini,kiro,opencode,pi}.py
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
| GitHub automation workflow script (PyPI OIDC Trusted Publishing) | CI/CD component | `.github/workflows/release-pypi.yml` |
| PyPI registry | Distribution channel and version-check source | `https://pypi.org/pypi/shellscripts/json`; `src/shell_scripts/version_check.py` |
| External CLI tools (e.g., qpdf, pdftk, gs, doxygen, java, plakativ) | System dependencies invoked by subprocess/exec | direct imports and command invocations in `src/shell_scripts/commands/*.py` |

## 2. Project Requirements

### 2.1 Project Functions
- **PRJ-001**: MUST parse CLI arguments and route execution to management flags (`--version`, `--ver`, `--upgrade`, `--uninstall`, `--write-config`) or registered subcommands with explicit process return codes.
- **PRJ-002**: MUST provide global help and command-specific help outputs through text-based terminal UI.
- **PRJ-003**: MUST expose subcommands for AI CLI installation/launch, PDF utilities, DICOM utilities, generic file diff/edit/view dispatching, `req` bootstrap orchestration, environment/test management, editor launchers, theme application, and cache cleanup.
- **PRJ-004**: MUST perform startup version-update checks against the PyPI registry with cooldown caching.
- **PRJ-005**: MUST include a GitHub automation workflow script at `.github/workflows/release-pypi.yml`.
- **PRJ-007**: MUST publish built distributions to PyPI via OIDC Trusted Publishing when a tagged version is committed on branch `master`.
- **PRJ-006**: MUST expose video conversion subcommands that transcode one input video into H.264 or H.265 MP4 outputs using FFmpeg.

### 2.2 Project Constraints
- **CTN-001**: MUST target Python runtime version 3.11 or newer.
- **CTN-002**: MUST expose console scripts `shellscripts` and `s` mapped to `shell_scripts.core:main`.
- **CTN-003**: MUST depend on external system executables for multiple subcommands and MUST fail fast when required executables are unavailable.
- **CTN-004**: MUST restrict automatic self-upgrade and self-uninstall actions to Linux platforms and MUST print manual fallback commands on non-Linux platforms.
- **CTN-005**: MUST treat Git repository root detection as a hard prerequisite for project-context commands.
- **CTN-006**: MUST execute all GitHub Actions JavaScript action runtimes in `.github/workflows/release-pypi.yml` on Node24 or newer.

## 3. Requirements

### 3.1 Design and Implementation
- **DES-001**: MUST implement command discovery with a static command-to-module mapping and lazy module imports.
- **DES-002**: MUST execute runtime OS detection and update-check logic before normal CLI argument dispatch.
- **DES-003**: MUST persist update-check cooldown state for every version-check request outcome in `~/.cache/shellscripts/check_version_idle-time.json`.
- **DES-004**: MUST apply a 3600-second cooldown after successful update checks.
- **DES-005**: MUST apply a fixed 86400-second cooldown after version-check request errors.
- **DES-006**: MUST suppress propagation of non-HTTP update-check exceptions without aborting command execution.
- **DES-007**: MUST implement `diff`, `edit`, and `view` commands as wrappers around shared MIME-based dispatch logic in `_dc_common` and runtime-configurable command profiles.
- **DES-008**: MUST expose command modules with `DESCRIPTION`, `print_help(version)`, and `run(args)` call patterns.
- **DES-009**: MUST recreate `.venv` whenever `.venv` already exists in `venv` command execution and `--force` MUST NOT change this behavior.
- **DES-010**: MUST request deletion confirmation in `clean` unless `--yes` is provided.
- **DES-011**: MUST implement centralized runtime configuration loading from `~/.config/shellScripts/config.json` with recursive merge semantics where missing keys preserve hardcoded defaults, including `req` providers and static checks.
- **DES-012**: MUST provide a management operation that writes default runtime configuration JSON to `~/.config/shellScripts/config.json`, creating parent directories when absent.
- **DES-013**: MUST resolve `ai-install` installer payload sources from detected runtime OS, including Linux npm no-`sudo` policy and Kiro package resolution via `https://prod.download.cli.kiro.dev/stable/latest/manifest.json`.
- **DES-014**: MUST generate global help command listing from a fixed section-to-command mapping preserving section order and per-section command order.
- **DES-015**: MUST pin every action referenced by `.github/workflows/release-pypi.yml` to a major version whose declared runtime is Node24 or newer.
- **DES-016**: MUST gate PyPI publication in `release-pypi.yml` on tag membership of branch `master` while executing all other release steps for any tagged branch.
- **DES-017**: MUST authenticate PyPI publication via OIDC Trusted Publishing and MUST NOT embed PyPI credentials or API tokens in `.github/workflows/release-pypi.yml`.
- **DES-018**: MUST resolve startup update-check latest versions from PyPI JSON API `https://pypi.org/pypi/shellscripts/json` field `info.version`.
- **DES-019**: MUST resolve develop upgrade tags and GitHub display versions from `https://api.github.com/repos/Ogekuri/shellScripts/releases/latest` field `tag_name`.
- **DES-020**: MUST print a bright-red error line for each failed remote source lookup during `--version` and continue with the remaining source.
- **DES-021**: MUST implement the official-release pre-check pipeline as an executable Bash script at `scripts/pre-release-check.sh`.
- **DES-022**: MUST resolve the Git repository root from the pre-release script location and MUST execute every check from that root directory.
- **DES-023**: MUST run the pytest suite in pre-release check with `<project-root>/src` prepended to `PYTHONPATH`, using `.venv/bin/python3` when present and `python3` otherwise.
- **DES-024**: MUST remove a preexisting `dist` directory and build sdist and wheel with `uv build` when `uv` is executable and `python3 -m build` otherwise.
- **DES-025**: MUST fail the build check when the rebuilt `dist` directory does not contain at least one sdist archive and one wheel artifact.
- **DES-026**: MUST remove the `dist`, `build`, `.pytest_cache`, and `src/shellscripts.egg-info` paths plus every `__pycache__` directory under `src` and `tests` before script termination.
- **DES-027**: MUST register artifact cleanup as an EXIT trap executed on success and failure paths and MUST print one `clean` evidence line listing the removed artifact groups.
- **DES-028**: MUST execute `scripts/pre-release-check.sh` in a dedicated pre-release job within `.github/workflows/release-pypi.yml` before any release artifact creation step.
- **DES-029**: MUST declare the pre-release job in the `needs` list of the `build-release` job in `.github/workflows/release-pypi.yml`.

No explicit performance optimizations identified.

### 3.2 Functions
- **REQ-001**: MUST print global help and return code `0` when invoked without CLI arguments.
- **REQ-002**: MUST print an error plus global help and return code `1` when the first argument is an unknown command.
- **REQ-003**: MUST force PyPI and GitHub remote lookups, print installed and latest versions, and return code `0` for `--version` and `--ver`.
- **REQ-075**: MUST print `--version` output as exactly three lines on successful remote lookups: installed version, `PyPI latest: <version>`, and `GitHub latest: <version>`.
- **REQ-004**: MUST execute the Linux `--upgrade` command from runtime config key `management.upgrade`, using default `uv tool install shellscripts --force` when unset.
- **REQ-076**: MUST make `--upgrade --develop` and `--upgrade --dev` upgrade from the latest GitHub release tag regardless of its source branch.
- **REQ-077**: MUST reject `--develop` and `--dev` flags passed without `--upgrade` with an error line and return code `1`.
- **REQ-078**: MUST make develop upgrade fail with a bright-red error line and return code `1` when the GitHub latest-tag resolution fails.
- **REQ-005**: MUST execute the Linux `--uninstall` command from runtime config key `management.uninstall`, using default `uv tool uninstall shellscripts` when unset.
- **REQ-006**: MUST execute all configured AI installers, including pi.dev, by default in `ai-install` when no selector options are provided.
- **REQ-007**: MUST reject unknown `ai-install` selector options with return code `1`.
- **REQ-008**: MUST install Codex, Copilot, Gemini, and OpenCode CLIs via `npm install -g` without `sudo` on Linux and Windows, and with `sudo` on macOS.
- **REQ-009**: MUST install Claude CLI by downloading `latest` metadata, selecting runtime-OS binary package (`linux`, `windows`, `macos`), and installing the executable at `~/.claude/bin/claude`.
- **REQ-010**: MUST install Kiro CLI only on Linux by resolving a headless ZIP package from `https://prod.download.cli.kiro.dev/stable/latest/manifest.json` using runtime architecture (`x86_64|aarch64`) and libc class (`gnu|musl`).
- **REQ-072**: MUST install pi.dev CLI in `ai-install` via `npm install -g @mariozechner/pi-coding-agent` with the same runtime-OS sudo policy used for other npm-based AI installers.
- **REQ-073**: MUST execute `pi install git:github.com/ferologics/pi-notify` after successful pi.dev CLI installation in `ai-install`.
- **REQ-074**: MUST emit the same start/result installer output pattern for `pi install git:github.com/ferologics/pi-notify` as other `ai-install` tools.
- **REQ-067**: MUST reject Kiro installation on Windows and macOS with explicit unsupported-platform error output and without attempting package download or extraction.
- **REQ-013**: MUST discover predefined cache directory names and delete them only after explicit confirmation or `--yes`.
- **REQ-014**: MUST set `CODEX_HOME` to `<project-root>/.codex` and execute `codex --yolo` in `codex` via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-015**: MUST execute `copilot --yolo --allow-all-tools --no-auto-update` in `copilot` via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-016**: MUST execute `gemini --yolo` in `gemini` via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-017**: MUST execute `~/.claude/bin/claude --dangerously-skip-permissions` in `claude` via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-018**: MUST execute `opencode` in `opencode` via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-068**: MUST execute `pi` with all CLI arguments forwarded unchanged and inherited stdio blocking behavior.
- **REQ-069**: MUST NOT append, inject, or synthesize any implicit `--tools` argument during `pi` command execution.
- **REQ-070**: MUST make `req` skip cleanup and installation when current directory is not a Git repository root and MUST print one skip evidence line for that directory.
- **REQ-071**: MUST make `req --dirs` skip cleanup and installation per non-root child directory, print one skip evidence line per skipped directory, and continue remaining child-directory processing.
- **REQ-019**: MUST execute `kiro-cli` in `kiro` via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-020**: MUST open the project root in VS Code and VS Code Insiders commands, append the project path as final argument, and execute each launcher via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-021**: MUST set `CODEX_HOME` to `<project-root>/.codex` before VS Code and VS Code Insiders command execution.
- **REQ-022**: MUST attempt GNOME GTK dark theme configuration via `gsettings` and MAY launch `gtk-chtheme`, `qt5ct`, and `qt6ct` when available.
- **REQ-023**: MUST print help using `diff`/`edit`/`view` command names and return code `2` when the required file argument is missing.
- **REQ-024**: MUST classify files by MIME and extension in `_dc_common.categorize` and dispatch execution via `subprocess.run` using runtime-configured `diff`/`edit`/`view` mappings with hardcoded defaults, inherited stdio, and blocking wait.
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
- **REQ-043**: MUST copy `~/.codex/auth.json` to `<project-root>/.codex/auth.json` before `codex` executes `codex --yolo`, replacing any existing file or symlink at the project auth path, and MUST print one informational output line describing the copy operation.
- **REQ-044**: MUST copy `<project-root>/.codex/auth.json` to `~/.codex/auth.json` after `codex --yolo` terminates, replacing any existing file or symlink at the user-home auth path, and MUST print one informational output line describing the copy operation.
- **REQ-045**: MUST load runtime configuration from `~/.config/shellScripts/config.json` during CLI startup, and MUST keep hardcoded defaults for missing file, missing keys, or invalid value types.
- **REQ-046**: MUST write the default runtime configuration JSON to `~/.config/shellScripts/config.json` and return code `0` when invoked with `--write-config`.
- **REQ-047**: MUST determine and cache the runtime operating system at CLI startup before command dispatch.
- **REQ-048**: MUST implement `req` command that removes predefined AI-integration cleanup paths and creates `guidelines`, `docs`, `tests`, `src`, `scripts`, and `.github/workflows` for each selected target directory.
- **REQ-049**: MUST invoke external `req` once per target directory using hardcoded arguments `--base`, `--docs-dir`, `--guidelines-dir`, three `--src-dir`, `--tests-dir`, and `--upgrade-guidelines`.
- **REQ-050**: MUST source repeated `--provider` and `--enable-static-check` arguments for `req` from runtime config and MUST use hardcoded defaults containing providers `codex:skills` and `pi:prompts` when config keys are missing or invalid.
- **REQ-051**: MUST target current directory when `req` is invoked without selector options.
- **REQ-052**: MUST make `req --dirs` target only first-level child directories and MUST exclude the current directory.
- **REQ-053**: MUST make `req --recursive` target all descendant directories and MUST exclude the current directory.
- **REQ-054**: MUST reject simultaneous `--dirs` and `--recursive` options in `req` with return code `1`.
- **REQ-055**: MUST provide a shared OS-aware executable-check function that returns `true` only when a command token or executable path is runnable on the current runtime platform and `false` otherwise.
- **REQ-056**: MUST make each command runner validate all external executables required by the actually activated option path before execution, print `Command not executable: <command>` on failure, and terminate with non-zero status.
- **REQ-057**: MUST implement `video2h264` using `subprocess.run` with inherited stdio and blocking wait for `ffmpeg -i <input> -c:v libx264 -profile:v high -level 4.1 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k <input>.mp4`.
- **REQ-058**: MUST implement `video2h265` using `subprocess.run` with inherited stdio and blocking wait for `ffmpeg -i <input> -c:v libx265 -crf 23 -tag:v hvc1 -pix_fmt yuv420p -c:a aac -b:a 192k <input>.mp4`.
- **REQ-059**: MUST skip the version-check HTTP request when the cooldown file exists, the persisted idle delay is active, and neither `--version` nor `--ver` is passed.
- **REQ-060**: MUST print a bright-green line containing `Versione Disponibile` and `Versione Installata` when the latest release version differs from the installed version.
- **REQ-061**: MUST print a bright-red error line and apply an 86400-second cooldown when the version-check request returns an HTTP error response or raises a non-HTTP exception.
- **REQ-062**: MUST print one cleanup evidence line per predefined cleanup path using status `deleted` for removed filesystem entries and status `skip` for absent paths.
- **REQ-063**: MUST label each `deleted` cleanup evidence line with entry kind `file` or `dir` based on the removed filesystem entry type.
- **REQ-064**: MUST execute delegated external system commands through `subprocess.run` with inherited stdin/stdout/stderr and MUST wait for child termination.
- **REQ-065**: MUST disable raw mouse capture before wrapper exit by writing `\x1b[?9l\x1b[?1000l\x1b[?1001l\x1b[?1002l\x1b[?1003l\x1b[?1004l\x1b[?1005l\x1b[?1006l\x1b[?1007l\x1b[?1015l\x1b[?1016l` to TTY stdout.
- **REQ-066**: MUST render global help command sections in this order: Edit/View, PDF, AI, Develop, Image, Video, OS, and list command descriptions exactly as registered command `DESCRIPTION` values.
- **REQ-079**: MUST abort all remaining checks at the first failed pre-release check, print a `FAIL` evidence line naming that check, and exit with return code `1`.
- **REQ-080**: MUST print a `PASS` evidence line for every passed pre-release check and MUST exit with return code `0` only when every mandatory check passes.
- **REQ-081**: MUST terminate with no generated build or test intermediate artifacts present in the repository working tree on the success path.
- **REQ-082**: MUST NOT remove any Git-tracked file during pre-release artifact cleanup.
- **REQ-083**: MUST skip every release artifact creation, attestation, changelog, GitHub release, and PyPI publication step when the pre-release job fails.
- **REQ-084**: MUST print each failed remote-source lookup during `--version` as `<source> latest: unknown (<reason>)` where `<reason>` describes the actual request failure.

## 4. Test Requirements

### 4.1 Coverage Summary
Unit test source files exist under `tests/` and provide coverage for core CLI flows, environment commands, AI installers, command dispatch wrappers, PDF pipelines, release-workflow Node24 runtime pinning, PyPI release gating, and PyPI version-source flows.
Implemented verification support exists via the `tests` command (`tests_cmd.py`), which executes pytest in `.venv` with `PYTHONPATH` set to `src`.
High-risk areas without exhaustive unit-test evidence are FFmpeg runtime integration and command-launch paths that depend on external binaries.
The release workflow gates all release artifact creation and publication on a dedicated pre-release verification job covered by static parsing tests.
A pre-release verification shell script exists at `scripts/pre-release-check.sh`, and its mandatory structure, generated-artifact cleanup, and Bash syntax are covered by static parsing tests.

### 4.2 Verification Requirements
- **TST-001**: MUST verify REQ-001, REQ-002, REQ-047, and REQ-066 by invoking `shell_scripts.core.main`, passing only if return codes, grouped help/error outputs, and startup OS-detection invocation match specified behavior.
- **TST-002**: MUST verify REQ-004 and REQ-005 on Linux by monkeypatching `subprocess.run` and asserting command values resolved from runtime config with default command fallback and propagated return codes.
- **TST-003**: MUST verify REQ-006 through REQ-010, REQ-067, and REQ-072 through REQ-074 by monkeypatching installer call sites and passing only if selector parsing, npm sudo policy, pi notify install order, and Kiro platform gates are correct.
- **TST-004**: MUST verify REQ-013 using temporary directories, passing only if cache-deletion confirmation gates behave exactly as specified.
- **TST-005**: MUST verify REQ-014 through REQ-021, REQ-043 through REQ-044, and REQ-068 through REQ-069 by monkeypatching `subprocess.run` and filesystem/environment state, passing only if executable args, `CODEX_HOME`, codex auth synchronization, absence of implicit `--tools` injection, and propagated return codes match requirements.
- **TST-006**: MUST verify REQ-023 and REQ-024, passing only if help output uses `diff`/`edit`/`view`, missing-file-argument status is `2`, and runtime-configured category dispatch selects mapped commands.
- **TST-009**: MUST verify REQ-045 and REQ-046 by monkeypatching config I/O boundaries and asserting startup load invocation plus `--write-config` success behavior.
- **TST-010**: MUST verify REQ-048 through REQ-054, REQ-062 through REQ-063, and REQ-070 through REQ-071 by monkeypatching filesystem and subprocess boundaries, passing only if target selection, git-root skip behavior, cleanup evidence output, and generated `req` argument vectors match required behavior.
- **TST-007**: MUST verify REQ-030 through REQ-035 by monkeypatching subprocess calls, passing only if expected qpdf/pdftk/gs invocation sequences and page-range validation outcomes are observed.
- **TST-008**: MUST verify REQ-036 through REQ-038 using isolated project roots, passing only if `.venv` lifecycle and conditional `requirements.txt` installation behavior match specified logic.
- **TST-011**: MUST verify REQ-057 and REQ-058 by monkeypatching executable checks and `subprocess.run`, passing only if FFmpeg argv vectors, `<input>.mp4` output naming, and propagated return codes are exact.
- **TST-012**: MUST verify CTN-006 and DES-015 by parsing `.github/workflows/release-pypi.yml`, passing only if every referenced action runtime matches the approved Node24-native mapping and no Node20 compatibility override environment variables are present.
- **TST-013**: MUST verify PRJ-007, DES-016, and DES-017 by parsing `.github/workflows/release-pypi.yml`, passing only if the PyPI publish step is master-gated, OIDC-based without credential secrets, and all preexisting release steps are retained.
- **TST-014**: MUST verify REQ-003, REQ-075 through REQ-077, REQ-084, DES-018, and DES-019 via monkeypatched HTTP and subprocess boundaries, passing only if PyPI update checks, three-line version output, default upgrade, and develop upgrade behaviors match specifications.
- **TST-015**: MUST verify DES-021 through DES-027 and REQ-079 through REQ-082 by parsing `scripts/pre-release-check.sh`, passing only if mandatory commands, artifact gates, cleanup registration, failure semantics, and evidence lines are present.
- **TST-016**: MUST verify DES-028, DES-029, and REQ-083 by parsing `.github/workflows/release-pypi.yml`, passing only if the dedicated pre-release job runs `scripts/pre-release-check.sh` and `build-release` declares `needs` on it.

## 5. Evidence

| Requirement IDs | File Path | Symbol / Function | Short Evidence Excerpt |
|---|---|---|---|
| PRJ-001, PRJ-002, REQ-001, REQ-002, REQ-003, REQ-047, REQ-064, REQ-065, REQ-066 | `src/shell_scripts/core.py`; `src/shell_scripts/utils.py` | `main`, `capture_terminal_state`, `reset_terminal_state`, `print_help` | Startup detects runtime OS before dispatch; empty args print grouped help and return `0`; unknown command path returns `1`; `--version`/`--ver` print `__version__`; wrapper exit restores saved TTY attributes and writes full mouse-off escape sequence including `?9l` through `?1016l`. |
| PRJ-003, DES-001, DES-008 | `src/shell_scripts/commands/__init__.py` | `_COMMAND_MODULES`, `get_command`, `get_all_commands` | Static mapping, lazy `importlib.import_module`, descriptions sourced from module `DESCRIPTION`. |
| PRJ-004, DES-002..DES-006, DES-018, DES-019, DES-020, REQ-003, REQ-075, REQ-084, REQ-059, REQ-060, REQ-061 | `src/shell_scripts/version_check.py`; `src/shell_scripts/core.py` | `check_for_updates`, `fetch_pypi_latest_version`, `fetch_github_latest_release`, `print_remote_latest_versions`, `_write_idle_config`, `_should_check` | Startup update check queries the PyPI JSON API; `--version` prints installed, PyPI latest, and GitHub latest lines; forces HTTP checks for `--version`/`--ver`, skips active cooldown otherwise, updates cache JSON for every outcome, applies 3600s success and 86400s error cooldowns, prints colored update/error lines, and renders failed source lines as `<source> latest: unknown (<reason>)`. |
| PRJ-005, PRJ-007, DES-016, DES-017 | `.github/workflows/release-pypi.yml` | `jobs.check-branch`, `jobs.build-release`, `jobs.build-release.steps.Publish` | Workflow script is present at required path, retains check-branch/build/attest/changelog/GitHub-release steps, and publishes to PyPI via `pypa/gh-action-pypi-publish@release/v1` gated on `origin/master` tag membership with workflow-level `id-token: write` and no credential secrets. |
| CTN-006, DES-015 | `.github/workflows/release-pypi.yml`; `tests/test_tst_012_workflow_runtime.py` | `jobs.check-branch.steps`, `jobs.build-release.steps`, `NODE24_NATIVE_ACTION_RUNTIMES` | Every `uses` reference pins a Node24-native runtime (`checkout@v7`, `setup-python@v7`, `setup-uv@v10`, `attest-build-provenance@v4`, `release-changelog-builder-action@v6`, `action-gh-release@v3`, `gh-action-pypi-publish@release/v1`); static test asserts full mapping coverage and absence of Node20 compatibility override variables. |
| REQ-004, REQ-076, REQ-077, REQ-078, CTN-004 | `src/shell_scripts/core.py`; `src/shell_scripts/config.py`; `tests/test_tst_014_pypi_version_source.py` | `do_upgrade`, `_build_develop_upgrade_command`, `main`, `DEFAULT_RUNTIME_CONFIG` | Default upgrade resolves `management.upgrade` to `uv tool install shellscripts --force` (PyPI); `--upgrade --develop`/`--dev` resolves the latest GitHub release tag and upgrades from `git+...@<tag>`; bare `--develop`/`--dev` is rejected with code `1`; tag-resolution failure emits a bright-red error and code `1`. |
| PRJ-006, REQ-057, REQ-058, REQ-064 | `src/shell_scripts/commands/video2h264.py`; `src/shell_scripts/commands/video2h265.py`; `src/shell_scripts/commands/__init__.py` | `run`, `_COMMAND_MODULES` | Command registry exposes `video2h264`/`video2h265`; runners launch fixed FFmpeg argv vectors via `subprocess.run` and output `<input>.mp4` in the input directory. |
| CTN-001 | `pyproject.toml` | `[project].requires-python` | `requires-python = ">=3.11"`. |
| CTN-002 | `pyproject.toml` | `[project.scripts]` | `shellscripts = "shell_scripts.core:main"`, `s = "shell_scripts.core:main"`. |
| CTN-003 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/*.py` | `require_commands`, command `run` functions | Multiple commands call `require_commands(...)` and terminate on missing tools. |
| CTN-004, REQ-004, REQ-005 | `src/shell_scripts/core.py`; `src/shell_scripts/utils.py` | `do_upgrade`, `do_uninstall`, `is_linux` | Linux executes `uv tool ...`; non-Linux prints manual command text and returns `0`. |
| CTN-005 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/{claude,codex,copilot,gemini,kiro,opencode}.py` | `require_project_root`, `run` | Project-context commands call `require_project_root()` and exit on missing Git root. |
| DES-007, REQ-023, REQ-024, REQ-064 | `src/shell_scripts/commands/diff_cmd.py`; `src/shell_scripts/commands/edit_cmd.py`; `src/shell_scripts/commands/view_cmd.py`; `src/shell_scripts/commands/_dc_common.py` | `run`, `dispatch`, `categorize` | `diff`/`edit`/`view` wrappers call shared dispatch; missing file argument returns `2`; selected external command is launched via `subprocess.run` with inherited stdio and blocking wait. |
| DES-009, REQ-038 | `src/shell_scripts/commands/venv_cmd.py` | `run` | `.venv` is removed in both `if force` and `else` branches; `--force` currently does not alter behavior. |
| DES-010, REQ-013 | `src/shell_scripts/commands/clean.py` | `run` | Prompts user before deletion unless `--yes`; deletes only confirmed directories. |
| REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-067, REQ-072, REQ-073, REQ-074 | `src/shell_scripts/commands/ai_install.py` | `run`, `_install_npm_tool`, `_install_claude`, `_install_kiro`, `_install_pi` | Default installer selection is all tools including pi.dev; unknown options fail; npm install command omits `sudo` on Linux and Windows and uses `sudo` on macOS; pi installer always installs CLI and then installs `pi install git:github.com/ferologics/pi-notify`; Kiro installer resolves Linux headless ZIP package from official stable manifest and rejects Windows/macOS with explicit unsupported-platform errors. |
| REQ-014, REQ-043, REQ-044, REQ-064 | `src/shell_scripts/commands/codex.py` | `run` | Sets `CODEX_HOME=<project>/.codex`; copies `~/.codex/auth.json` into `<project>/.codex/auth.json` before launch and copies back after process termination, replacing existing file or symlink targets; emits one informational output line for each copy operation; executes `codex --yolo` via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-015, REQ-064 | `src/shell_scripts/commands/copilot.py` | `run` | Executes `copilot --yolo --allow-all-tools --no-auto-update` via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-016, REQ-064 | `src/shell_scripts/commands/gemini.py` | `run` | Executes `gemini --yolo` via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-017, REQ-064 | `src/shell_scripts/commands/claude.py` | `run` | Executes `~/.claude/bin/claude --dangerously-skip-permissions` via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-018, REQ-064 | `src/shell_scripts/commands/opencode.py` | `run` | Executes `opencode` via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-019, REQ-064 | `src/shell_scripts/commands/kiro.py` | `run` | Executes `kiro-cli` via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-020, REQ-021, REQ-064 | `src/shell_scripts/commands/vscode_cmd.py`; `src/shell_scripts/commands/vsinsider_cmd.py` | `run` | Commands set `CODEX_HOME`, append project path, and execute Code binaries via `subprocess.run` with inherited stdio and blocking wait. |
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
| REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-062, REQ-063 | `src/shell_scripts/commands/req_cmd.py`; `src/shell_scripts/config.py` | `run`, `_prepare_target_directory`, `_build_req_args`, `get_req_profile` | `req` command resolves targets by selector mode, removes predefined cleanup paths, emits `deleted`/`skip` cleanup evidence with file-or-dir labels for removals, and executes external `req` with hardcoded base args plus runtime-configured providers/static checks. |
| TST-001..TST-014 | `tests/test_tst_*.py`; `src/shell_scripts/core.py`; `src/shell_scripts/commands/*.py`; `src/shell_scripts/version_check.py` | multiple | Unit tests exist under `tests/`; `test_tst_011_video_commands.py` verifies FFmpeg argv construction, output naming, and help exposure for REQ-057/REQ-058. |
| DES-021..DES-027, REQ-079..REQ-082, TST-015 | `scripts/pre-release-check.sh`; `tests/test_tst_015_pre_release_check.py` | `run_check`, `check_artifacts`, `cleanup_artifacts`, `fail_fast` | Script resolves the repository root, runs pytest with `PYTHONPATH=src` via `.venv/bin/python3` or `python3`, removes `dist`, builds via `uv build` or `python3 -m build`, verifies sdist and wheel artifacts, removes `dist`, `build`, `.pytest_cache`, `src/shellscripts.egg-info`, and `__pycache__` directories via an EXIT trap on success and failure paths, prints `PASS`/`FAIL`/`clean` evidence lines, exits `1` on first failure and `0` on full success; tests assert script structure and Bash syntax. |
| DES-028, DES-029, REQ-083, TST-016 | `.github/workflows/release-pypi.yml`; `tests/test_tst_016_release_precheck_gating.py` | `jobs.pre-release-check`, `jobs.build-release.needs` | Workflow runs `scripts/pre-release-check.sh` in a dedicated `pre-release-check` job (checkout, `setup-uv@v10.3.3`, `uv sync`, script execution) and declares `needs: [check-branch, pre-release-check]` on `build-release`, so any check failure skips artifact creation, attestation, changelog, GitHub release, and PyPI publication steps; tests assert job presence, script invocation, and needs declaration. |
