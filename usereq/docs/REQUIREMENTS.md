---
title: "shellScripts Requirements"
description: Software requirements specification
version: "0.28.0"
date: "2026-11-27T10:12:12Z"
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
shellScripts is a Python CLI package that dispatches utility subcommands for AI CLI launching, PDF operations, DICOM operations, generic file diff/edit/view dispatching, project environment management, and editor/theme helpers.

Repository structure (evidence-oriented view, depth-limited):

```text
.
├── .github/
│   └── workflows/
│       └── release-pypi.yml
├── docs/
├── scripts/
│   ├── build.sh
│   ├── pre-release-check.sh
│   └── s.sh
├── src/
│   ├── shell_scripts/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── config.py
│   │   ├── config_cli.py
│   │   ├── core.py
│   │   ├── utils.py
│   │   ├── version_check.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── clean.py
│   │       ├── {agy,claude,codex,copilot,opencode}.py
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
- **PRJ-001**: MUST parse CLI arguments and route execution to management flags (`--version`, `--ver`, `--upgrade`, `--uninstall`, `--write-config`, `--print-raw`, `--print`, `--info`, `--get`, `--set`, `--unset`) or registered subcommands with explicit process return codes.
- **PRJ-002**: MUST provide global help and command-specific help outputs through text-based terminal UI.
- **PRJ-003**: MUST expose subcommands for AI CLI launch, PDF utilities, DICOM utilities, generic file diff/edit/view dispatching, environment/test management, editor launchers, theme application, and cache cleanup.
- **PRJ-004**: MUST perform startup version-update checks against the PyPI registry with cooldown caching.
- **PRJ-005**: MUST include a GitHub automation workflow script at `.github/workflows/release-pypi.yml`.
- **PRJ-007**: MUST publish built distributions to PyPI via OIDC Trusted Publishing when a tagged version is committed on branch `master`.
- **PRJ-006**: MUST expose video conversion subcommands that transcode one input video into H.264 or H.265 MP4 outputs using FFmpeg.
- **PRJ-008**: MUST expose subcommands `meld-highlight-theme`, `chrome-debug`, `net`, and `npm-bootstrap-trust` as Python ports of the legacy bash scripts with equivalent generations and behavior.
- **PRJ-009**: MUST expose subcommand `cargo-bootstrap-trust` that bootstraps a placeholder crates.io crate and registers its GitHub trusted publisher through the same five-phase fail-fast pipeline philosophy as `npm-bootstrap-trust`.

### 2.2 Project Constraints
- **CTN-001**: MUST target Python runtime version 3.11 or newer.
- **CTN-002**: MUST expose console scripts `shellscripts` and `s` mapped to `shell_scripts.core:main`.
- **CTN-003**: MUST depend on external system executables for multiple subcommands and MUST fail fast when required executables are unavailable.
- **CTN-004**: MUST restrict automatic self-upgrade and self-uninstall actions to Linux platforms and MUST print manual fallback commands on non-Linux platforms.
- **CTN-005**: MUST treat Git repository root detection as a hard prerequisite for project-context commands, excluding YOLO AI CLI launch commands (`agy`, `claude`, `codex`, `copilot`, `opencode`).
- **CTN-006**: MUST execute all GitHub Actions JavaScript action runtimes in `.github/workflows/release-pypi.yml` on Node24 or newer.
- **CTN-007**: MUST write every user-visible CLI message, help text, evidence token, and schema label in English.

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
- **DES-011**: MUST implement centralized runtime configuration loading from `~/.config/shellScripts/config.json` with recursive merge semantics where missing keys preserve hardcoded defaults.
- **DES-012**: MUST provide a management operation that writes default runtime configuration JSON to `~/.config/shellScripts/config.json`, creating parent directories when absent.
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
- **DES-024**: MUST delegate the pre-release distribution build to `scripts/build.sh` with a `mktemp -d` temporary output directory and MUST NOT duplicate build-tool selection logic inside the pre-release script.
- **DES-025**: MUST fail the artifact check when the temporary build directory lacks at least one non-empty sdist archive and one non-empty wheel artifact with readable archive structure.
- **DES-026**: MUST remove the `build`, `.pytest_cache`, and `src/shellscripts.egg-info` paths and every `__pycache__` directory under `src` and `tests` before script termination.
- **DES-027**: MUST register artifact cleanup as an EXIT trap executed on success and failure paths and MUST print one `clean` evidence line listing the removed artifact groups.
- **DES-030**: MUST implement YOLO CLI launching as a shared registry-based launcher module where each CLI is defined by one declarative record containing command token, executable token, executed option, and option note.
- **DES-031**: MUST make integrating a new YOLO CLI require only one registry record plus one thin command module exposing `DESCRIPTION`, `print_help(version)`, and `run(args)`.
- **DES-032**: MUST implement the configuration CLI surface (`--print-raw`, `--print`, `--info`, `--get`, `--set`, `--unset`) as views over one declarative schema registry co-located with runtime configuration defaults.
- **DES-033**: MUST update the schema registry, and thereby `--info`, `--print`, `--get`, `--set`, and `--unset`, in the same change whenever any configuration option, default, type, or allowed value is added, removed, or modified.
- **DES-034**: MUST fail every configuration CLI command with an explicit error when the schema registry and `DEFAULT_RUNTIME_CONFIG` paths diverge.
- **DES-035**: MUST implement configuration CLI mutations in a dedicated module without altering existing configuration load, merge, normalization, or accessor logic.
- **DES-036**: MUST declare one input-example token in every `OptionSpec` schema record consumed by `--info` command-template rendering.
- **DES-037**: MUST implement every `--set` and `--unset` persistence as a write to a temporary file in the configuration directory followed by flush and atomic rename onto `config.json`.
- **DES-038**: MUST perform all array and map manipulations exclusively through `:`-separated path tokens accepted by `--get`, `--set`, and `--unset`.
- **DES-039**: MUST apply array and map manipulations to the effective configuration, defaults merged with overrides, and persist the resulting collection as one override value.
- **DES-040**: MUST implement the reproducible distribution build pipeline as an executable Bash script at `scripts/build.sh`.
- **DES-041**: MUST remove every distribution archive stored in `dist/` regardless of version number or Git tracking status, preserving only non-generated `dist` entries.
- **DES-042**: MUST preserve the exhaustive `.gitignore` exclusion strategy by re-including `dist/` traversal and all `dist/` files without any ignore rule targeting `dist/` entries.
- **DES-043**: MUST abort the pre-release pipeline before destructive operations when `build`, `.pytest_cache`, or `src/shellscripts.egg-info` contain tracked files.
- **DES-044**: MUST capture pre-run tracked and non-managed untracked repository state and fail when post-cleanup state diverges from that baseline.
- **DES-045**: MUST handle `EXIT`, `INT`, and `TERM` conditions so generated-artifact cleanup runs on every termination path without overriding a failed check result.
- **DES-046**: MUST validate generated archive readability and required archive members in `scripts/build.sh` and print one summary listing every deliverable stored in the resolved output directory.
- **DES-047**: MUST print phase headers, `PASS`/`FAIL`/`SKIP` evidence lines, and a final summary naming the failed check or confirming success.
- **DES-048**: MUST exclude the `tests/` tree from the sdist via a repository-root `MANIFEST.in`.
- **DES-049**: MUST retain `pyproject.toml`, `README.md`, `LICENSE`, `PKG-INFO`, and `src/shell_scripts/` sources in the sdist.
- **DES-050**: MUST restrict wheel contents to the `shell_scripts` package, the `*.dist-info/` directory, and the `shellscripts` and `s` console entry points.
- **DES-051**: MUST declare `setuptools>=77.0.0` as the lower bound in `[build-system].requires`, the minimum version supporting the PEP 639 `license` and `license-files` fields.
- **DES-052**: MUST remove `src/shellscripts.egg-info/` and intermediate `build/` trees in `scripts/build.sh` after packaging, leaving no generated metadata residue in the working tree.
- **DES-053**: MUST remove the `setup.cfg`, `MANIFEST.in`, and `src/shellscripts.egg-info/` members from each sdist archive in `scripts/build.sh` after packaging.
- **DES-057**: MUST NOT execute a distribution build command, `scripts/build.sh`, or `scripts/pre-release-check.sh` anywhere in `.github/workflows/release-pypi.yml`.
- **DES-058**: MUST execute the release job only for tag refs and check out the exact commit identified by `github.sha`.
- **DES-060**: MUST consolidate previous-build cleanup and distribution building into the single executable pipeline `scripts/build.sh`.
- **DES-061**: MUST execute a post-build repository-hygiene phase in `scripts/build.sh` that removes every intermediate artifact produced by the build before the deliverable summary.
- **DES-062**: MUST restrict every `.github/workflows/release-pypi.yml` job to consuming distribution archives produced by `scripts/build.sh`.
- **DES-063**: MUST read the archive timestamp epoch from the version-controlled repository file `.build-epoch`.
- **DES-064**: MUST track `.build-epoch` and re-include it in `.gitignore` while preserving the default-exclusion strategy.
- **DES-065**: MUST resolve the `scripts/build.sh` output directory from environment variable `BUILD_DIST_DIR` and MUST default to `dist` when the variable is unset or empty.
- **DES-066**: MUST create the pre-release build output inside a `mktemp -d` temporary directory located outside the repository working tree.
- **DES-067**: MUST pass the temporary build output directory to `scripts/build.sh` through `BUILD_DIST_DIR` and MUST validate generated archives inside it.
- **DES-068**: MUST remove the temporary build output directory on success, failure, and signal termination paths.
- **DES-069**: MUST register command tokens `meld-highlight-theme`, `chrome-debug`, `net`, and `npm-bootstrap-trust` in the static command registry mapping to modules `meld_highlight_theme`, `chrome_debug`, `net_cmd`, and `npm_bootstrap_trust` with lazy imports.
- **DES-070**: MUST register command token `cargo-bootstrap-trust` in the static command registry mapping to module `cargo_bootstrap_trust` with lazy import.

No explicit performance optimizations identified.

### 3.2 Functions
- **REQ-001**: MUST print global help and return code `0` when invoked without CLI arguments.
- **REQ-002**: MUST print an error plus global help and return code `1` when the first argument is an unknown command.
- **REQ-003**: MUST force PyPI and GitHub remote lookups, print installed and latest versions, and return code `0` for `--version` and `--ver`.
- **REQ-075**: MUST print `--version` output as exactly three lines on successful remote lookups: the `Current Installed` installed-version line, the `Latest @ PyPI` line, and the `Latest @ GitHub` line.
- **REQ-004**: MUST execute the Linux `--upgrade` command from runtime config key `management.upgrade`, using default `uv tool install shellscripts` when unset.
- **REQ-076**: MUST make `--upgrade --develop` and `--upgrade --dev` upgrade from the latest GitHub release tag regardless of its source branch.
- **REQ-077**: MUST reject `--develop` and `--dev` flags passed without `--upgrade` with an error line and return code `1`.
- **REQ-078**: MUST make develop upgrade fail with a bright-red error line and return code `1` when the GitHub latest-tag resolution fails.
- **REQ-087**: MUST resolve the develop upgrade command from runtime config key `management.upgrade_develop`, using default `uv tool install shellscripts --from git+https://github.com/Ogekuri/shellScripts.git@{tag}` when unset.
- **REQ-088**: MUST make `--upgrade --force` append ` --force --reinstall --refresh` to the resolved `management.upgrade` command before execution.
- **REQ-089**: MUST make develop upgrade invoked with `--force` append ` --force --reinstall --refresh` to the resolved develop upgrade command before execution.
- **REQ-090**: MUST reject `--force` passed without `--upgrade` with an error line and return code `1`.
- **REQ-091**: MUST left-justify every `--version` report label (`Current Installed`, `Latest @ PyPI`, `Latest @ GitHub`) to fixed width 18 followed by `: ` and the version token.
- **REQ-005**: MUST execute the Linux `--uninstall` command from runtime config key `management.uninstall`, using default `uv tool uninstall shellscripts` when unset.
- **REQ-013**: MUST discover predefined cache directory names and delete them only after explicit confirmation or `--yes`.
- **REQ-014**: MUST execute `codex --yolo` in `codex` through the shared YOLO CLI launcher via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-015**: MUST execute `copilot --yolo` in `copilot` through the shared YOLO CLI launcher via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-017**: MUST execute the PATH-resolved `claude --dangerously-skip-permissions` in `claude` through the shared YOLO CLI launcher with inherited stdio and blocking wait.
- **REQ-018**: MUST execute `opencode --auto` in `opencode` through the shared YOLO CLI launcher via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-020**: MUST open the project root in VS Code and VS Code Insiders commands, append the project path as final argument, and execute each launcher via `subprocess.run` with inherited stdio and blocking wait.
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
- **REQ-045**: MUST load runtime configuration from `~/.config/shellScripts/config.json` during CLI startup, and MUST keep hardcoded defaults for missing file, missing keys, or invalid value types.
- **REQ-046**: MUST write the default runtime configuration JSON to `~/.config/shellScripts/config.json` and return code `0` when invoked with `--write-config`.
- **REQ-047**: MUST determine and cache the runtime operating system at CLI startup before command dispatch.
- **REQ-055**: MUST provide a shared OS-aware executable-check function that returns `true` only when a command token or executable path is runnable on the current runtime platform and `false` otherwise.
- **REQ-056**: MUST make each command runner validate all external executables required by the actually activated option path before execution, print `Command not executable: <command>` on failure, and terminate with non-zero status.
- **REQ-057**: MUST implement `video2h264` using `subprocess.run` with inherited stdio and blocking wait for `ffmpeg -i <input> -c:v libx264 -profile:v high -level 4.1 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k <input>.mp4`.
- **REQ-058**: MUST implement `video2h265` using `subprocess.run` with inherited stdio and blocking wait for `ffmpeg -i <input> -c:v libx265 -crf 23 -tag:v hvc1 -pix_fmt yuv420p -c:a aac -b:a 192k <input>.mp4`.
- **REQ-059**: MUST skip the version-check HTTP request when the cooldown file exists, the persisted idle delay is active, and neither `--version` nor `--ver` is passed.
- **REQ-060**: MUST print a bright-green line containing `Update Available` and `Installed Version` when the latest release version differs from the installed version.
- **REQ-061**: MUST print a bright-red error line and apply an 86400-second cooldown when the version-check request returns an HTTP error response or raises a non-HTTP exception.
- **REQ-064**: MUST execute delegated external system commands through `subprocess.run` with inherited stdin/stdout/stderr and MUST wait for child termination.
- **REQ-065**: MUST disable raw mouse capture before wrapper exit by writing `\x1b[?9l\x1b[?1000l\x1b[?1001l\x1b[?1002l\x1b[?1003l\x1b[?1004l\x1b[?1005l\x1b[?1006l\x1b[?1007l\x1b[?1015l\x1b[?1016l` to TTY stdout.
- **REQ-066**: MUST render global help command sections in this order: Edit/View, PDF, AI, Develop, Image, Video, OS, and list command descriptions exactly as registered command `DESCRIPTION` values.
- **REQ-079**: MUST abort all remaining checks at the first failed pre-release check, print a `FAIL` evidence line naming that check, and exit with return code `1`.
- **REQ-080**: MUST print a `PASS` evidence line for every passed pre-release check and MUST exit with return code `0` only when every mandatory check passes.
- **REQ-081**: MUST terminate with no generated build, test, or packaging artifacts present in the repository working tree on success and failure paths.
- **REQ-082**: MUST NOT remove any Git-tracked file during pre-release artifact cleanup.
- **REQ-084**: MUST print each failed remote-source lookup during `--version` as the aligned `Latest @ <source>` label followed by `: unknown (<reason>)` where `<reason>` describes the actual request failure.
- **REQ-085**: MUST execute `agy --dangerously-skip-permissions` in `agy` through the shared YOLO CLI launcher via `subprocess.run` with inherited stdio and blocking wait.
- **REQ-086**: MUST print every registered YOLO CLI command token with its executed option in alphabetical command order in each YOLO CLI inline help output.
- **REQ-092**: MUST document the executed YOLO option and its behavioral note for every registered YOLO CLI inside each YOLO CLI inline help output.
- **REQ-093**: MUST document the accepted alternative `--allow-all` Copilot option in the `copilot` inline help without appending it to the executed command vector.
- **REQ-094**: MUST implement `--print-raw` to bootstrap the configuration file when missing and print the on-disk `~/.config/shellScripts/config.json` content verbatim, returning code `0`.
- **REQ-095**: MUST implement `--print [Optional:Sub:Path]` rendering the effective configuration or the addressed subtree as a tree using `├──`, `└──`, and `│` connectors.
- **REQ-096**: MUST render `--print` scalar leaves as `= <JSON-encoded value>` followed by `(default)` or `(custom | default: <Default_Value>)`, names left-justified to a fixed column width.
- **REQ-097**: MUST render `--print` selection leaves with the active value plus a `Sel`/`Value` table marking the active choice `[*]` and inactive choices `[ ]`.
- **REQ-098**: MUST display every configuration value, including credentials and API keys, in plain text without masking or obfuscation in `--print-raw`, `--print`, and `--get` outputs.
- **REQ-099**: MUST implement `--get <path>` resolving `:`-separated hierarchical paths against the effective configuration and printing scalar values as clean single-line JSON.
- **REQ-100**: MUST make `--get` print object and array subtrees as indented JSON and fail with a stderr error and code `1` for unknown or non-configurable paths.
- **REQ-101**: MUST implement `--set <path> <value>` coercing string arguments into strict schema types (`string`, `integer`, `float`, `boolean`, `selection`, `array`, `map`, `object`) before persisting.
- **REQ-102**: MUST validate `--set` values against schema constraints and abort with a stderr error and code `1` without writing when validation or JSON parsing fails.
- **REQ-103**: MUST make successful `--set` persist sorted-key, two-space-indented JSON preserving unrelated keys, print a confirmation, and return code `0`.
- **REQ-104**: MUST make `--set` value tokens starting with `$` resolve from the named environment variable and print environment-acquisition evidence; missing variables MUST fail with return code `1`.
- **REQ-105**: MUST implement `--unset <path>` removing the override key or applying the array/map removal encoded by trailing path tokens, then persisting atomically.
- **REQ-106**: MUST make `--unset` print `WARNING: Removed all parameters for <path>.` when resetting a subtree and a stderr error with code `1` for invalid removals.
- **REQ-107**: MUST implement `--info [Optional:Sub:Path]` rendering the schema hierarchy or the addressed subtree with per-option type labels and short descriptions.
- **REQ-108**: MUST render `--info` selection options with allowed-value tables using `Value`, `Default`, and `Meaning` columns.
- **REQ-109**: MUST make `--get`, `--set`, and `--unset` print command-specific inline usage help and return `1` when required path or value arguments are missing.
- **REQ-110**: MUST render every `--info` scalar option with a `Default : <Default_Value> (restored via '--unset <Full:Path>')` line and a full-path `--set` command line.
- **REQ-111**: MUST print full-path `--set` and `--unset` command lines after each `--info` selection allowed-value table.
- **REQ-112**: MUST render `--info` `object` options with full-path full-overwrite and reset-block command lines above nested field documentation.
- **REQ-113**: MUST render `--info` array options with add, insert, update, delete, full-overwrite, and clear command lines using complete canonical paths.
- **REQ-114**: MUST fail `--print-raw` with a stderr error naming the configuration path and code `1` when the file exists but is unreadable.
- **REQ-115**: MUST render `--print` selection leaves with an inline `set: <Full:Path> <Value>` action hint appended to the default or custom indicator.
- **REQ-116**: MUST create missing configuration parent directories and initialize `~/.config/shellScripts/config.json` with system defaults before executing any configuration management command.
- **REQ-117**: MUST render `[Path: <Full:Path>]` on every `--print` and `--info` section node using exact CLI path tokens.
- **REQ-118**: MUST render `--print` map leaves as `(<N> entries | key target: <Full:Path>:<Key>)` followed by a `Key`/`Value` box table with one row per entry.
- **REQ-119**: MUST render `--print` primitive-array leaves as `(<N> items | row target: <Full:Path>:<Idx> | add: :+)` followed by a 0-based `Idx`/`Value` box table.
- **REQ-120**: MUST render `--print` object-array leaves as `(<N> rows | cell target: <Full:Path>:<Idx>:<Field> | add: :+)` followed by an `Idx` plus field-columns box table.
- **REQ-121**: MUST render empty arrays as `= (empty list — add row with: --set <Full:Path>:+ <value>)` and empty maps as `= (empty map — set key with: --set <Full:Path>:<Key> <value>)`.
- **REQ-122**: MUST make `--get <Path>:<Idx>` print the 0-based array element and fail with a stderr error stating the valid index range when out of bounds.
- **REQ-123**: MUST make `--get <Path>:<Idx>:<Field>` print the row-cell JSON value and `--get <Path>:<Key>` print the map value for `<Key>`.
- **REQ-124**: MUST make `--set <Path>:append` and `--set <Path>:+` validate the item against the array schema, append it, print the assigned index, and persist atomically.
- **REQ-125**: MUST make `--set <Path>:insert:<Idx>` place the validated item at `<Idx>`, shift subsequent items by one, and treat `<Idx>` equal to array length as append.
- **REQ-126**: MUST make `--set <Path>:<Idx>` replace the targeted row and fail with a stderr error stating the valid index range when out of bounds.
- **REQ-127**: MUST make `--set <Path>:<Idx>:<Field>` update only that row field and `--set <Path>:<Key>` add or update one map entry with schema-typed values.
- **REQ-128**: MUST make `--set <Path>` carrying a JSON array or JSON object token overwrite the entire array or map after schema validation.
- **REQ-129**: MUST make `--unset <Path>:<Idx>` remove the row and immediately compact the array to contiguous 0-based indices without gaps or null holes.
- **REQ-130**: MUST make `--unset <Path>:<Idx>:<Field>` restore the declared field default or remove the undeclared key, and `--unset <Path>:<Key>` remove one map key.
- **REQ-131**: MUST print array index errors to stderr stating the valid index range and the `:append` alternative, and return code `1`.
- **REQ-132**: MUST print valid `--get`, `--print`, `--print-raw`, and `--info` output to stdout, errors to stderr with code `1`, and successes with code `0`.
- **REQ-133**: MUST render every `--print` and `--info` node name identical to its CLI path token and use complete canonical paths in all hints and examples.
- **REQ-134**: MUST make `scripts/build.sh` resolve the repository root, validate Python 3.11 or newer plus one available build tool, and build sdist and wheel packages into the resolved output directory defaulting to `dist/`.
- **REQ-135**: MUST make `scripts/build.sh` verify that generated sdist and wheel archives are non-empty, readable, and compliant with REQ-145 and REQ-146, and print a summary of every deliverable in the resolved output directory.
- **REQ-136**: MUST make `scripts/pre-release-check.sh` execute project-structure, toolchain, script-executable, Bash-syntax, Python-compilation, unit-test, `scripts/build.sh`, and artifact-validation checks.
- **REQ-137**: MUST make `scripts/pre-release-check.sh` remove all generated artifacts on every termination path and exit non-zero when cleanup fails after all checks passed.
- **REQ-138**: MUST make `scripts/pre-release-check.sh` compare post-cleanup tracked modifications and non-managed untracked files with the pre-run baseline and fail on divergence.
- **REQ-139**: MUST make `scripts/pre-release-check.sh` abort before destructive operations when `build`, `.pytest_cache`, or `src/shellscripts.egg-info` contain tracked files.
- **REQ-140**: MUST make `.gitignore` keep the default-exclusion strategy and re-include `dist/` and `dist/**/*` without any ignore rule targeting `dist/` entries.
- **REQ-141**: MUST make `scripts/build.sh` delete every `dist/` entry matching `*.tar.gz`, `*.whl`, `*.zip`, or `*.egg`, regardless of version, before invoking the build tool.
- **REQ-142**: MUST make `scripts/pre-release-check.sh` print phase headers, `PASS`/`FAIL`/`SKIP` evidence lines, and a final success or failure summary naming the failed check.
- **REQ-143**: MUST make `scripts/pre-release-check.sh` report non-applicable formatter, linter, type-checker, security, integration, and end-to-end checks as `SKIP` without counting them as `PASS`.
- **REQ-144**: MUST make `scripts/pre-release-check.sh` verify that `scripts/pre-release-check.sh` and `scripts/build.sh` are executable files.
- **REQ-145**: MUST make `scripts/build.sh` verify that the wheel contains `*.dist-info/licenses/LICENSE` and `*.dist-info/entry_points.txt` declaring `shellscripts` and `s`, and no member outside `shell_scripts/` or `*.dist-info/`.
- **REQ-146**: MUST make `scripts/build.sh` verify that the sdist contains `pyproject.toml` and `src/shell_scripts/__init__.py` and no `tests/`, `src/shellscripts.egg-info/`, `setup.cfg`, or `MANIFEST.in` member.
- **REQ-148**: MUST make `scripts/build.sh` remove `build/`, `src/shellscripts.egg-info/`, the build-tool `.gitignore` metadata in the resolved output directory, output-directory `*.tmp` files, and `src/**/__pycache__/` after packaging and before script termination.
- **REQ-149**: MUST make `scripts/build.sh` resolve `SOURCE_DATE_EPOCH` from `.build-epoch` when the variable is unset and honor an explicitly supplied value.
- **REQ-150**: MUST make `scripts/build.sh` exit non-zero when `.build-epoch` is missing, empty, or not a non-negative decimal integer.
- **REQ-151**: MUST make `scripts/build.sh` print `SOURCE_DATE_EPOCH: <value> (<source>)` with source token `environment` or `.build-epoch`.
- **REQ-152**: MUST make `scripts/pre-release-check.sh` perform no read, verification, cleanup, or deletion operation on `dist/` entries.
- **REQ-153**: MUST make `scripts/pre-release-check.sh` remove its temporary build output directory on success, failure, and signal termination paths.
- **REQ-154**: MUST make `scripts/pre-release-check.sh` validate generated sdist and wheel archives inside the temporary build output directory.
- **REQ-155**: MUST make `scripts/build.sh` print one `clean` evidence line reporting the number of removed `dist/` archives and preserve every non-generated `dist` entry.
- **REQ-156**: MUST expose `meld-highlight-theme` with mutually exclusive `--dark` and `--light` palette flags plus `--only-meld-base`, rejecting their combination and unsupported arguments.
- **REQ-157**: MUST discover candidate schemes from `*.xml` files in meld and gtksourceview style directories under `/usr/share`, `$HOME/.local/share`, and `$HOME/.var/app/org.gnome.meld/data`, keeping only parseable `style-scheme` roots with valid ids.
- **REQ-158**: MUST exclude schemes whose id ends with `-highlight`, whose name ends with ` Highlight`, or whose id starts with `texthighlight`.
- **REQ-159**: MUST generate for every selected scheme an `<id>-highlight` XML root declaring parent-scheme `<id>`, version `1.0`, author `Custom Script`, and display name `<name> Highlight`.
- **REQ-160**: MUST add to every generated scheme a `<_description>` element `<name> con evidenziazione inline rossa` and a `meld:inline` style with background `#cc0000` and foreground `#ffffff`.
- **REQ-161**: MUST inherit for `meld-base` under the dark palette the `meld:*` and `map-overlay` styles except `meld:inline` from `meld-dark` and copy every referenced `meld-dark` color.
- **REQ-162**: MUST fail generation when the dark palette lacks `meld:insert`, `meld:replace`, `meld:conflict`, `meld:current-line-highlight`, or `meld:current-chunk-highlight`.
- **REQ-163**: MUST select the dark palette when `--dark` is set, the light palette when `--light` is set, and otherwise detect darkness from meld preference, display-server GTK lookup, desktop color-scheme, and GTK theme names.
- **REQ-164**: MUST fail fast when `--only-meld-base` finds no `meld-base` scheme or when the dark palette applies while `meld-dark` is missing.
- **REQ-165**: MUST reject generated XML that loses `parent-scheme` inheritance or contains a `text` style.
- **REQ-166**: MUST write each scheme as `<id>-highlight.xml` into every target style directory and skip destinations whose bytes already equal the generated content.
- **REQ-167**: MUST back up each overwritten highlight file as `<file>.bak-<timestamp>` and replace it atomically through a same-directory temporary file.
- **REQ-168**: MUST print an English summary reporting processed variant count, written file count, and backup count, plus a Meld restart hint.
- **REQ-169**: MUST launch `google-chrome --remote-debugging-port=9222 --user-data-dir=<HOME>/.config/google-chrome` detached from the terminal session with both output streams suppressed.
- **REQ-170**: MUST validate the `google-chrome` executable before launch, print English progress messages, and return code `0` after spawning the detached browser.
- **REQ-171**: MUST dispatch `net status` printing boxed English headers followed by `nmcli device status`, `nmcli -f NAME,TYPE,AUTOCONNECT,DEVICE connection show`, `resolvectl status`, `ip route`, and the last 15 `journalctl -b -u networking.service --no-pager` lines.
- **REQ-172**: MUST dispatch `net vlan <id> up|down` to `sudo nmcli connection up|down vlan<id>` and print current VLAN addresses after successful activation.
- **REQ-173**: MUST fail `net` with return code `1`, printing English usage, on missing `vlan` arguments, invalid actions, or unknown subcommands.
- **REQ-174**: MUST accept required `-p <package>`, `-r <owner/repo>`, and `-f <workflow>` options plus `-h` help, failing with return code `1` on missing values, unknown arguments, or missing options.
- **REQ-175**: MUST validate the npm name against unscoped or scoped conservative lowercase syntax with a 214-character limit, `owner/repo` syntax with owner length at most 39 and no trailing `-`, and a bare workflow filename ending `.yml` or `.yaml`.
- **REQ-176**: MUST fail fast when `node` or `npm` is not executable or reports versions older than Node 22.14.0 or npm 11.15.0.
- **REQ-177**: MUST verify npmjs authentication via `npm whoami --registry=https://registry.npmjs.org/` before any mutating step and abort with a login hint on failure.
- **REQ-178**: MUST abort when `npm view <package>@*` reports existing versions and when the availability check fails without an `E404` marker.
- **REQ-179**: MUST publish a temporary placeholder package at version `0.0.0` with dist-tag `bootstrap`, public access, and the configured repository URL, removing the temporary directory on every exit path.
- **REQ-180**: MUST create the GitHub trusted publisher via `npm trust github <package> --repo <repo> --file <workflow> --allow-publish`, print the resulting trust list, and report publication-without-trust as a distinct failure.
- **REQ-181**: MUST complete by warning that the trust validates only after a successful OIDC publish from the workflow within two days.
- **REQ-182**: MUST accept required `-p <package>`, `-r <owner/repo>`, and `-f <workflow>` options plus `-h` help, failing with return code `1` on missing values, unknown arguments, or missing options.
- **REQ-183**: MUST validate the crate name against conservative lowercase syntax `^[a-z0-9][a-z0-9_-]*$` with a 64-character limit.
- **REQ-184**: MUST validate the `owner/repo` token with owner length at most 39 and no trailing `-`, and the workflow filename as a bare name ending `.yml` or `.yaml`.
- **REQ-185**: MUST fail fast when `rustc` or `cargo` is not executable or reports versions older than rustc 1.89.0 or cargo 1.89.0.
- **REQ-186**: MUST resolve the crates.io token by checking, in order, environment variable `CARGO_REGISTRIES_CRATES_IO_TOKEN`, `$CARGO_HOME/credentials.toml` keys `registry.token` then `registries.crates-io.token`, and legacy JSON `$CARGO_HOME/credentials` key `registry.crates.io-token`.
- **REQ-187**: MUST probe crates.io authentication via `GET https://crates.io/api/v1/me` with the resolved token before any mutating step, treating HTTP 403 carrying detail `this action can only be performed on the crates.io website` as authenticated.
- **REQ-188**: MUST abort when the crates.io crate lookup reports existing versions and when the availability check fails without an HTTP 404 response.
- **REQ-189**: MUST create the temporary placeholder crate via `cargo init --name <package> --vcs none` and write a `Cargo.toml` declaring version `0.0.0`, a placeholder description, and repository URL `https://github.com/<repo>`.
- **REQ-190**: MUST publish the placeholder crate via `cargo publish` from the temporary directory and MUST remove the temporary directory on every exit path.
- **REQ-191**: MUST create the GitHub trusted publisher via `PUT https://crates.io/api/v1/crates/<package>/trusted_publishing/github_actions_config` carrying `repository` and `workflow` fields, print the resulting trust configuration, and report publication-without-trust as a distinct failure.
- **REQ-192**: MUST complete by warning that the trust validates only after a successful OIDC publish from the workflow within two days.
- **REQ-193**: MUST abort with a `cargo login` hint on missing token and on every `GET /api/v1/me` outcome other than HTTP 200 or the authenticated HTTP 403 website-only detail.

## 4. Test Requirements

### 4.1 Coverage Summary
Unit test source files exist under `tests/` and provide coverage for core CLI flows, environment commands, YOLO-mode AI CLI launches, command dispatch wrappers, PDF pipelines, release-workflow Node24 runtime pinning, PyPI release gating, and PyPI version-source flows.
Implemented verification support exists via the `tests` command (`tests_cmd.py`), which executes pytest in `.venv` with `PYTHONPATH` set to `src`.
High-risk areas without exhaustive unit-test evidence are FFmpeg runtime integration and command-launch paths that depend on external binaries.
The configuration CLI management flags introduced by DES-032 are covered by `tests/test_tst_018_config_cli.py` covering bootstrap, atomic persistence, path-token array/map manipulation, and rendering contracts.
The release workflow consumes only the `dist/` archives produced by `scripts/build.sh`, runs no distribution build and no build-preparatory verification job, and gates PyPI publication on `master` tag membership; static parsing tests cover these contracts.
The `scripts/build.sh` pipeline consolidates previous-build cleanup and packaging: its first data-mutating phase removes every `dist/` archive of any version plus the `build/` and `src/shellscripts.egg-info/` intermediate trees while preserving non-generated entries and printing one `clean` evidence line with the removed archive count, and its post-build hygiene phase removes generated metadata, temporary files, and `src` bytecode caches; the archive timestamp epoch `.build-epoch` is read from the tracked repository file, so tracked `dist/` archives are byte-identical to a rebuild of the commit that contains them; structure, epoch rules, tracked-guard behavior, Bash syntax, executable bit, and `.gitignore` re-inclusion are covered by static parsing tests.
The pre-release pipeline builds into a `mktemp -d` temporary directory outside the repository working tree, delegates that directory to `scripts/build.sh` through `BUILD_DIST_DIR`, validates the generated archives there, and remains independent from the `dist/` content: it never reads, verifies, cleans, or modifies `dist/` entries, so tracked and untracked `dist/` content cannot influence its result.
The four ported commands introduced by PRJ-008 are covered by `tests/test_tst_021_meld_highlight_theme.py`, which executes the `meld-highlight-theme` pipeline against fixture style directories and compares generated XML byte-for-byte with reference fixtures generated by `bin/Meld_Create_TextHighlight.sh`, and by `tests/test_tst_022_ported_commands.py`, which verifies `chrome-debug`, `net`, and `npm-bootstrap-trust` through monkeypatched subprocess and filesystem boundaries.
The `cargo-bootstrap-trust` pipeline introduced by PRJ-009 and DES-070 (REQ-182 through REQ-193) is covered by `tests/test_tst_023_cargo_bootstrap_trust.py`, which verifies the REQ-186 crates.io token-source resolution order (environment variable, TOML `credentials.toml`, legacy JSON `credentials`) on isolated `CARGO_HOME` fixture directories and the REQ-187 `/me` response classification (the upstream website-only 403 detail authenticates, HTTP 401 and other failures abort) through monkeypatched HTTP boundaries; its subprocess boundaries remain untested.

### 4.2 Verification Requirements
- **TST-001**: MUST verify REQ-001, REQ-002, REQ-047, and REQ-066 by invoking `shell_scripts.core.main`, passing only if return codes, grouped help/error outputs, and startup OS-detection invocation match specified behavior.
- **TST-002**: MUST verify REQ-004 and REQ-005 on Linux by monkeypatching `subprocess.run` and asserting command values resolved from runtime config with default command fallback and propagated return codes.
- **TST-004**: MUST verify REQ-013 using temporary directories, passing only if cache-deletion confirmation gates behave exactly as specified.
- **TST-005**: MUST verify REQ-014, REQ-015, REQ-017, REQ-018, and REQ-020 by monkeypatching `subprocess.run` and filesystem/environment state, passing only if executable args, absence of Codex auth synchronization, and propagated return codes match requirements.
- **TST-006**: MUST verify REQ-023 and REQ-024, passing only if help output uses `diff`/`edit`/`view`, missing-file-argument status is `2`, and runtime-configured category dispatch selects mapped commands.
- **TST-009**: MUST verify REQ-045 and REQ-046 by monkeypatching config I/O boundaries and asserting startup load invocation plus `--write-config` success behavior.
- **TST-007**: MUST verify REQ-030 through REQ-035 by monkeypatching subprocess calls, passing only if expected qpdf/pdftk/gs invocation sequences and page-range validation outcomes are observed.
- **TST-008**: MUST verify REQ-036 through REQ-038 using isolated project roots, passing only if `.venv` lifecycle and conditional `requirements.txt` installation behavior match specified logic.
- **TST-011**: MUST verify REQ-057 and REQ-058 by monkeypatching executable checks and `subprocess.run`, passing only if FFmpeg argv vectors, `<input>.mp4` output naming, and propagated return codes are exact.
- **TST-012**: MUST verify CTN-006 and DES-015 by parsing `.github/workflows/release-pypi.yml`, passing only if every referenced action runtime matches the approved Node24-native mapping and no Node20 compatibility override environment variables are present.
- **TST-013**: MUST verify PRJ-007, DES-016, and DES-017 by parsing `.github/workflows/release-pypi.yml`, passing only if PyPI publication is master-gated, uses OIDC without embedded credentials, and non-build release steps remain present.
- **TST-014**: MUST verify REQ-003, REQ-075 through REQ-078, REQ-084, REQ-087 through REQ-091, DES-018, and DES-019 via monkeypatched HTTP and subprocess boundaries, passing only if PyPI update checks, three-line version output, default upgrade, forced-reinstall upgrade, and develop upgrade behaviors match specifications.
- **TST-015**: MUST verify DES-021 through DES-027, DES-040 through DES-047, DES-060, DES-061, DES-063 through DES-068, and REQ-079 through REQ-082 plus REQ-134 through REQ-155 by parsing both scripts and probing `.gitignore` plus `.build-epoch`, passing only if mandatory commands, temporary build directory usage, `dist/` independence, artifact gates, epoch rules, cleanup registration, integrity checks, failure semantics, and evidence lines are present.
- **TST-017**: MUST verify REQ-085, REQ-086, REQ-092, and REQ-093 by monkeypatching `subprocess.run` and capturing YOLO CLI help outputs, passing only if each YOLO argv vector, stdio inheritance, registry exposure, alphabetical YOLO CLI help listing, per-CLI option documentation, and the Copilot `--allow-all` alternative note match specifications.
- **TST-018**: MUST verify REQ-114 and REQ-116 through REQ-133, DES-037, DES-038, and DES-039 on isolated HOME directories, passing only if bootstrap, atomic persistence, path-token manipulation, rendering contracts, and error semantics match specifications.
- **TST-020**: MUST verify DES-057, DES-058, and DES-062 by parsing the release workflow and asserting tag-only execution, exact-commit checkout, absence of build and build-preparatory jobs, and `dist/` inputs to both publication actions.
- **TST-021**: MUST verify REQ-156 through REQ-168 by executing the `meld-highlight-theme` pipeline against fixture style directories and comparing generated XML byte-for-byte with `bin/Meld_Create_TextHighlight.sh`-generated reference fixtures.
- **TST-022**: MUST verify REQ-169 through REQ-181 and DES-069 by monkeypatching subprocess and filesystem boundaries, passing only if argv vectors, validation gates, file operations, and return codes match specifications.
- **TST-023**: MUST verify REQ-186 on isolated `CARGO_HOME` fixture directories, passing only if the environment-variable, TOML `credentials.toml`, and legacy JSON sources resolve in the declared order and absent sources yield no token.
- **TST-024**: MUST verify REQ-187 via monkeypatched crates.io HTTP boundaries, passing only if HTTP 403 carrying the website-only detail authenticates, HTTP 401 and any other failure abort with the cargo login hint.

## 5. Evidence

| Requirement IDs | File Path | Symbol / Function | Short Evidence Excerpt |
|---|---|---|---|
| PRJ-001, PRJ-002, REQ-001, REQ-002, REQ-003, REQ-047, REQ-064, REQ-065, REQ-066 | `src/shell_scripts/core.py`; `src/shell_scripts/utils.py` | `main`, `capture_terminal_state`, `reset_terminal_state`, `print_help` | Startup detects runtime OS before dispatch; empty args print grouped help and return `0`; unknown command path returns `1`; `--version`/`--ver` print the aligned `Current Installed` line; wrapper exit restores saved TTY attributes and writes full mouse-off escape sequence including `?9l` through `?1016l`. |
| PRJ-003, DES-001, DES-008 | `src/shell_scripts/commands/__init__.py` | `_COMMAND_MODULES`, `get_command`, `get_all_commands` | Static mapping, lazy `importlib.import_module`, descriptions sourced from module `DESCRIPTION`. |
| PRJ-004, DES-002..DES-006, DES-018, DES-019, DES-020, REQ-003, REQ-075, REQ-084, REQ-091, REQ-059, REQ-060, REQ-061 | `src/shell_scripts/version_check.py`; `src/shell_scripts/core.py` | `check_for_updates`, `fetch_pypi_latest_version`, `fetch_github_latest_release`, `print_remote_latest_versions`, `_write_idle_config`, `_should_check` | Startup update check queries the PyPI JSON API; `--version` prints aligned `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub` lines; forces HTTP checks for `--version`/`--ver`, skips active cooldown otherwise, updates cache JSON for every outcome, applies 3600s success and 86400s error cooldowns, prints colored update/error lines, and renders failed source lines as aligned `Latest @ <source>` labels with `unknown (<reason>)` values. |
| PRJ-005, PRJ-007, DES-016, DES-017, DES-057, DES-058, DES-062, TST-013, TST-020 | `.github/workflows/release-pypi.yml`; `tests/test_tst_013_release_pypi_gating.py`; `tests/test_tst_020_release_committed_artifacts.py` | `jobs.check-branch`, `jobs.build-release` | Workflow is present; tag-gates release on `github.sha`, runs no build and no build-preparatory job, retains attestation/changelog/release actions, and publishes the `dist/` archives to GitHub Release and OIDC PyPI gated on `origin/master`. |
| CTN-006, DES-015 | `.github/workflows/release-pypi.yml`; `tests/test_tst_012_workflow_runtime.py` | `jobs.check-branch.steps`, `jobs.build-release.steps`, `NODE24_NATIVE_ACTION_RUNTIMES` | Every `uses` reference pins a Node24-native runtime (`checkout@v7`, `setup-python@v7`, `attest-build-provenance@v4`, `release-changelog-builder-action@v6`, `action-gh-release@v3`, `gh-action-pypi-publish@release/v1`); static test asserts full mapping coverage and absence of Node20 compatibility override variables. |
| REQ-004, REQ-076, REQ-077, REQ-078, REQ-087, REQ-088, REQ-089, REQ-090, CTN-004 | `src/shell_scripts/core.py`; `src/shell_scripts/config.py`; `tests/test_tst_014_pypi_version_source.py` | `do_upgrade`, `_build_develop_upgrade_command`, `main`, `DEFAULT_RUNTIME_CONFIG` | Default upgrade resolves `management.upgrade` to `uv tool install shellscripts` (PyPI); `--upgrade --develop`/`--dev` resolves the latest GitHub release tag and upgrades from `git+...@<tag>`; `--force` appends ` --force --reinstall --refresh` to both upgrade modes; bare `--develop`/`--dev` and bare `--force` are rejected with code `1`; tag-resolution failure emits a bright-red error and code `1`. |
| PRJ-006, REQ-057, REQ-058, REQ-064 | `src/shell_scripts/commands/video2h264.py`; `src/shell_scripts/commands/video2h265.py`; `src/shell_scripts/commands/__init__.py` | `run`, `_COMMAND_MODULES` | Command registry exposes `video2h264`/`video2h265`; runners launch fixed FFmpeg argv vectors via `subprocess.run` and output `<input>.mp4` in the input directory. |
| CTN-001 | `pyproject.toml` | `[project].requires-python` | `requires-python = ">=3.11"`. |
| CTN-002 | `pyproject.toml` | `[project.scripts]` | `shellscripts = "shell_scripts.core:main"`, `s = "shell_scripts.core:main"`. |
| CTN-003 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/*.py` | `require_commands`, command `run` functions | Multiple commands call `require_commands(...)` and terminate on missing tools. |
| CTN-004, REQ-004, REQ-005 | `src/shell_scripts/core.py`; `src/shell_scripts/utils.py` | `do_upgrade`, `do_uninstall`, `is_linux` | Linux executes `uv tool ...`; non-Linux prints manual command text and returns `0`. |
| CTN-005 | `src/shell_scripts/utils.py`; `src/shell_scripts/commands/{clean,doxygen_cmd,tests_cmd,venv_cmd,vscode_cmd,vsinsider_cmd}.py` | `require_project_root`, `run` | Project-context commands call `require_project_root()` and exit on missing Git root; YOLO AI CLI launch commands perform no Git root validation and execute only the registry-defined command vector. |
| DES-007, REQ-023, REQ-024, REQ-064 | `src/shell_scripts/commands/diff_cmd.py`; `src/shell_scripts/commands/edit_cmd.py`; `src/shell_scripts/commands/view_cmd.py`; `src/shell_scripts/commands/_dc_common.py` | `run`, `dispatch`, `categorize` | `diff`/`edit`/`view` wrappers call shared dispatch; missing file argument returns `2`; selected external command is launched via `subprocess.run` with inherited stdio and blocking wait. |
| DES-009, REQ-038 | `src/shell_scripts/commands/venv_cmd.py` | `run` | `.venv` is removed in both `if force` and `else` branches; `--force` currently does not alter behavior. |
| DES-010, REQ-013 | `src/shell_scripts/commands/clean.py` | `run` | Prompts user before deletion unless `--yes`; deletes only confirmed directories. |
| REQ-014, REQ-064 | `src/shell_scripts/commands/codex.py`; `src/shell_scripts/commands/_yolo_common.py` | `run`, `run_yolo_cli` | `codex` delegates to the shared YOLO CLI launcher and executes `codex --yolo` plus pass-through args via `subprocess.run` with inherited stdio and blocking wait; no auth-file synchronization and no copy evidence output. |
| REQ-015, REQ-064 | `src/shell_scripts/commands/copilot.py`; `src/shell_scripts/commands/_yolo_common.py` | `run`, `run_yolo_cli` | Executes `copilot --yolo` plus pass-through args via `subprocess.run` with inherited stdio and blocking wait; inline help documents the accepted alternative `--allow-all` option. |
| REQ-017, REQ-064 | `src/shell_scripts/commands/claude.py`; `src/shell_scripts/commands/_yolo_common.py` | `run`, `run_yolo_cli` | Executes the PATH-resolved `claude --dangerously-skip-permissions` plus pass-through args via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-018, REQ-064 | `src/shell_scripts/commands/opencode.py`; `src/shell_scripts/commands/_yolo_common.py` | `run`, `run_yolo_cli` | Executes `opencode --auto` plus pass-through args via `subprocess.run` with inherited stdio and blocking wait. |
| REQ-085, REQ-086, REQ-092, REQ-093, DES-030, DES-031, TST-017 | `src/shell_scripts/commands/_yolo_common.py`; `src/shell_scripts/commands/{agy,claude,codex,copilot,opencode}.py`; `tests/test_tst_017_agy_command.py` | `YOLO_CLI_REGISTRY`, `run_yolo_cli`, `print_yolo_help`, `run`, `print_help` | Shared declarative registry defines command token, executable, executed option, and behavioral note per YOLO CLI; thin command modules delegate to the shared launcher, which executes each CLI with its YOLO option via `subprocess.run` with inherited stdio and blocking wait; every YOLO inline help prints the alphabetical registry with executed options plus the Copilot `--allow-all` alternative note. |
| REQ-020, REQ-064 | `src/shell_scripts/commands/vscode_cmd.py`; `src/shell_scripts/commands/vsinsider_cmd.py` | `run` | Commands append project path and execute Code binaries via `subprocess.run` with inherited stdio and blocking wait. |
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
| TST-001..TST-002, TST-004..TST-014 | `tests/test_tst_*.py`; `src/shell_scripts/core.py`; `src/shell_scripts/commands/*.py`; `src/shell_scripts/version_check.py` | multiple | Unit tests exist under `tests/`; `test_tst_011_video_commands.py` verifies FFmpeg argv construction, output naming, and help exposure for REQ-057/REQ-058. |
| DES-021..DES-027, DES-040..DES-047, DES-060, DES-061, DES-063..DES-068, REQ-079..REQ-082, REQ-134..REQ-155, TST-015 | `scripts/pre-release-check.sh`; `scripts/build.sh`; `.build-epoch`; `.gitignore`; `tests/test_tst_015_pre_release_check.py` | `run_check`, `skip_check`, `create_temp_build_dir`, `check_artifacts`, `check_repository_integrity`, `collect_tracked_nonmanaged`, `cleanup_artifacts`, `fail_fast`, `on_exit`, `clean_previous_builds`, `clean_build_residue`, `resolve_source_date_epoch`, `resolve_build_tool`, `verify_artifacts`, `print_summary` | Pre-release resolves the repository root, validates project structure, toolchain and executable bits, runs Bash/Python syntax checks, pytest with `PYTHONPATH=src`, creates a `mktemp -d` temporary build output directory outside the working tree, delegates distribution building to `scripts/build.sh` through `BUILD_DIST_DIR`, validates the sdist and wheel archives inside that directory, never reads, verifies, or modifies `dist/` entries, runs cleanup and full-state baseline repository-integrity checks, and reports `PASS`/`FAIL`/`SKIP` plus a final summary; cleanup is registered on `EXIT`/`INT`/`TERM`, removes the temporary build directory, and preserves the original failure result. Build script deletes every `dist` archive of any version in its first data-mutating phase, resolves the archive epoch from the tracked `.build-epoch` file (honoring an explicit `SOURCE_DATE_EPOCH`), builds via `uv build` or `python3 -m build`, then runs a post-build hygiene phase removing intermediate trees, generated metadata, temporary files, and `src` bytecode caches before validating readability and summarizing deliverables. `.gitignore` re-includes `dist/`, `dist/**/*`, and `.build-epoch` without dist-targeting ignore rules. Tests assert both script structures, epoch rules, Bash syntax, executable bits, and real `git check-ignore` behavior. |
| REQ-094 through REQ-133, DES-032 through DES-039 | `src/shell_scripts/config_cli.py`; `src/shell_scripts/core.py` | `CONFIG_SCHEMA`, `find_schema_mismatches`, `_ensure_bootstrap`, `_resolve_target`, `_write_overrides`, `do_print_raw`, `do_print`, `do_info`, `do_get`, `do_set`, `do_unset`, `main` | Declarative schema registry mirrors `DEFAULT_RUNTIME_CONFIG` leaves with parity enforcement that fails configuration commands on divergence; management flags bootstrap the missing config file, print the raw file verbatim, render trees with `[Path: ...]` badges, default/custom indicators, `Sel`/`Value` and collection tables with box-drawing characters, resolve `:`-separated paths including `:append`/`:+`/`:insert:<Idx>`/`:<Idx>`/`:<Idx>:<Field>`/`:<Key>` tokens, coerce strict JSON types, validate, and persist atomically via same-directory temporary-file rename with environment acquisition. |
| PRJ-009, DES-070, REQ-182 through REQ-192 | `src/shell_scripts/commands/cargo_bootstrap_trust.py`; `src/shell_scripts/commands/__init__.py`; `src/shell_scripts/core.py` | `_COMMAND_MODULES`, `HELP_SECTION_COMMANDS`, `run`, `_validate_inputs`, `_require_toolchain`, `_resolve_registry_token`, `_read_toml_credentials_token`, `_read_legacy_json_token`, `_is_website_only_auth_probe`, `_verify_crates_io_auth`, `_check_crate_availability`, `_write_placeholder_crate`, `print_help` | Static registry maps `cargo-bootstrap-trust` to `cargo_bootstrap_trust` with lazy import and lists it in the Develop help section; the five-phase pipeline validates inputs and the rustc/cargo 1.89.0 toolchain, resolves the crates.io token from the environment variable, the TOML `credentials.toml`, or the legacy JSON `credentials` file, verifies authentication via `GET /api/v1/me` classifying the upstream website-only 403 detail as authenticated, aborts on taken names or non-404 lookup failures, creates and publishes the `0.0.0` placeholder crate from a temporary directory removed on every exit path, registers the GitHub trusted publishing config through the crates.io API, prints the trust configuration, and warns about the two-day validation window. |
