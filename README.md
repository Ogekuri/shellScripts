> [!CAUTION]
> ### 🚨 STRICTLY EXPERIMENTAL — PROOF OF CONCEPT (PRE-ALPHA)
> 
> ![Status: Proof of Concept](https://img.shields.io/badge/Status-Proof_of_Concept-red?style=flat-square) ![Stage: Pre-Alpha](https://img.shields.io/badge/Stage-Pre--Alpha-critical?style=flat-square) ![Maintenance: Personal Use Only](https://img.shields.io/badge/Scope-Personal_Use_Only-important?style=flat-square) ![Issues: Closed](https://img.shields.io/badge/Issues_%26_PRs-Not_Accepted-inactive?style=flat-square)
>
> **PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE:**
> 
> * **Very Early Stage:** This project is currently a raw **Proof of Concept (PoC)** in a **pre-alpha** state. It is nowhere near production-ready and may contain severe bugs, breaking changes, or incomplete logic.
> * **Personal Use Only:** This repository is developed, maintained, and shared strictly for **personal use**. 
> * **No Support or Feature Requests:** Please **do not** open issues, bug reports, or feature requests. They will not be addressed or accepted at this stage of development.
> * **No Warranty:** This software is provided **"AS IS"**, without warranty of any kind, express or implied. You may use it strictly for **testing and evaluation purposes** at your own sole risk.

# s/shellScripts (0.26.3)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>
<p align="center">
<strong>Execute useful shell scripts via an uvx-compatible CLI interface.</strong><br>
<code>shellscripts</code> is a Linux-first command collection for project automation, AI CLI launchers,
PDF/DICOM utilities, development helpers, and editor integrations, exposed through a single command.
<br>
</p>


<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#feature-highlights">Feature Highlights</a> |
  <a href="#management-commands">Upgrading or Removing</a> |
  <a href="#shell-scripts">Shell Scripts</a>
</p>

<p align="center">
<br>
🚧 <strong>DRAFT:</strong> Proof-of-Concept (PoC) Version 📝 - Work in Progress 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://www.npmjs.com/package/pi-usereq"><strong>PI-useReq/pi-usereq</strong></a> 🤖✨ ⚠️<br>
<br>
</p>


## Feature Highlights
- Single CLI entrypoint with command dispatch and grouped built-in help (`shellscripts` and alias `s`).
- YOLO-mode launchers for AI CLIs (`agy`, `claude`, `codex`, `copilot`, `opencode`) and project-root IDE launchers (`vscode`, `vsinsider`).
- PDF workflow commands for crop, merge, split, TOC cleanup, and tiling.
- DICOM helpers (`dicom2jpg`, `dicomviewer`) and video transcoders (`video2h264`, `video2h265`).
- Project maintenance and automation commands (`req`, `clean`, `venv`, `tests`, `doxygen`, `ubuntu-dark-theme`).
- Startup update notification with rate-limited checks against the PyPI registry.


## Requirements

- Python `>=3.11`.
- Astral `uv` is the supported install and launcher tool (`uv tool install`, `uvx`, `uv run`); the package also runs as `python -m shell_scripts`.
- Git is required for project-root commands (`clean`, `venv`, `tests`, `doxygen`, `vscode`, `vsinsider`).
- AI CLI launchers (`agy`, `claude`, `codex`, `copilot`, `opencode`) execute in the current directory without Git root validation; `req` skips targets that are not Git repository roots in its current-directory and `--dirs` modes.
- Command-specific external tools are required only for related commands:
  - `req` for the `req` command.
  - `doxygen` (plus optional `make` and `pdflatex`) for `doxygen`.
  - `gs`, `pdfinfo`, `qpdf`, `pdftk`, `plakativ` for PDF commands.
  - `ffmpeg` for `video2h264` and `video2h265`.
  - Java runtime + PixelMed jars (+ `java-wrappers`) for DICOM commands.


## Quick Start

### Prerequisites

- Install `uv`: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)


### Install / Upgrade

Install from PyPI (primary distribution channel):

```bash
uv tool install shellscripts
```

Upgrade to the latest published PyPI release:

```bash
s --upgrade
```

Force a complete re-download and reinstallation by appending the forced-reinstall options (`--force --reinstall --refresh`) to the configured upgrade command:

```bash
s --upgrade --force
```


### Run Without Installing (uvx)

```bash
uvx shellscripts <command> [args...]
```


### Run From a Local Clone

```bash
./scripts/s.sh <command> [args...]
```

or

```bash
uv run --project . python -m shell_scripts <command> [args...]
```


## Install from GitHub (Alternative)

PyPI is the primary distribution channel. As an alternative, the package can be installed from GitHub Releases, which also hosts intermediate and test releases that are not published on PyPI:

```bash
uv tool install shellscripts --force --from git+https://github.com/Ogekuri/shellScripts.git@vX.Y.Z
```

Intermediate and test releases are available at: [https://github.com/Ogekuri/shellScripts/releases](https://github.com/Ogekuri/shellScripts/releases).

To upgrade to the newest tagged GitHub release, regardless of the branch that carries the tag, use the `--dev` (alias `--develop`) flag together with `--upgrade`:

```bash
s --upgrade --dev
# or
s --upgrade --develop
```

Add `--force` to force a complete re-download and reinstallation of the tagged release:

```bash
s --upgrade --develop --force
```


## Management Commands

Global syntax:

```bash
shellscripts [command] [options]
# or
s [command] [options]
```

Built-in management flags:

- `--help` : print the full help screen, or one command help with `s --help <command>` / `s <command> --help`.
- `--version` / `--ver` : print the installed version plus the latest versions available on PyPI and GitHub.
- `--upgrade` : run the configured upgrade command automatically on Linux (installs the latest PyPI release by default), otherwise print the manual command.
- `--upgrade --force` : force download and complete reinstallation by appending `--force --reinstall --refresh` to the `--upgrade` or `--upgrade --dev`/`--upgrade --develop` command.
- `--upgrade --dev` / `--upgrade --develop` : upgrade from the latest tagged GitHub release instead of PyPI, regardless of its source branch.
- `--uninstall` : run configured uninstall command automatically on Linux, otherwise print the manual command.
- `--write-config` : write the default runtime configuration file.
- `--print-raw` : print the on-disk configuration file content verbatim.
- `--print [Sub:Path]` : print the effective configuration, or the addressed subtree, as an options tree.
- `--info [Sub:Path]` : print the configurable parameters, or the addressed subtree, with types, descriptions, and copy-paste command lines.
- `--get <Path>` : read one configuration value.
- `--set <Path> <Value>` : set one configuration value or collection element.
- `--unset <Path>` : remove one configuration override and reactivate the default.

### Runtime Configuration

Generate a default config file:

```bash
s --write-config
```

Default location:

```text
~/.config/shellScripts/config.json
```

Top-level configuration keys:

- `management`
  - `upgrade`: command string executed by `--upgrade` (PyPI install by default).
  - `upgrade_develop`: command template executed by `--upgrade --dev`; the `{tag}` placeholder is replaced with the latest GitHub release tag.
  - `uninstall`: command string executed by `--uninstall`.
- `dispatch`
  - `diff`, `edit`, `view`: each command supports `categories` and `fallback` command vectors.
- `req`
  - `providers`: provider list forwarded to external `req`.
  - `static_checks`: static-check entries forwarded to external `req`.

### Configuration CLI

The configuration management flags operate on the effective configuration (hardcoded defaults merged with the file) and write only overrides:

- Paths use `:` as hierarchical separator (for example `management:upgrade`).
- `--get`, `--set`, and `--unset` support collection tokens:
  - `<Path>:<Idx>` : 0-based array row.
  - `<Path>:<Idx>:<Field>` : one field of an object row.
  - `<Path>:<Key>` : dynamic map key.
  - `--set` only: `<Path>:append` / `<Path>:+` (append), `<Path>:insert:<Idx>` (insert), JSON arrays/maps/objects (full overwrite).
- `--set` accepts `$NAME` value tokens and acquires the value from environment variable `NAME`.
- Array values are validated against the schema; row deletion re-indexes the array contiguously.
- Every configuration command bootstraps a missing `~/.config/shellScripts/config.json` with system defaults before running.
- Persistence is atomic (same-directory temporary file followed by rename) and keeps unrelated keys.
- Values are always displayed in plain text, including credentials and API keys.

Examples:

```bash
s --get management:upgrade
s --set management:upgrade "uv tool install shellscripts"
s --set req:providers:+ "codex:skills"
s --set req:providers:insert:0 "claude:prompts"
s --set req:providers "$REQ_PROVIDERS"
s --unset management:upgrade
s --print dispatch:diff
s --info req
```

`--print` renders default/custom indicators, selection tables, and collection tables with `[Path: ...]` badges; `--info` renders each option type plus full-path `--set`/`--unset` command templates.


## Shell Scripts

### Command List

| Command | Purpose |
|---|---|
| `agy` | Launch Antigravity CLI in YOLO mode (`agy --dangerously-skip-permissions`). |
| `claude` | Launch Claude CLI in YOLO mode (`claude --dangerously-skip-permissions`). |
| `codex` | Launch Codex CLI in YOLO mode (`codex --yolo`). |
| `copilot` | Launch Copilot CLI in YOLO mode (`copilot --yolo`; alternative `--allow-all` documented in help). |
| `opencode` | Launch OpenCode CLI in auto-approval mode (`opencode --auto`). |
| `clean` | Find and delete cache directories under the project root (or a passed directory). |
| `req` | Run useReq bootstrap on current directory, first-level dirs, or recursively. |
| `venv` | Recreate `.venv` and install `requirements.txt` if present. |
| `tests` | Ensure/create `.venv` and run pytest (arguments passed through). |
| `doxygen` | Generate HTML/XML/Markdown docs and optional PDF output. |
| `vscode` | Open project in VS Code with `CODEX_HOME` set. |
| `vsinsider` | Open project in VS Code Insiders with `CODEX_HOME` set. |
| `diff` | Dispatch file differ by MIME/category. |
| `edit` | Dispatch file editor by MIME/category. |
| `view` | Dispatch file viewer by MIME/category. |
| `pdf-crop` | Crop PDF pages with auto or manual bounding boxes. |
| `pdf-merge` | Merge multiple PDFs preserving/rebuilding bookmarks. |
| `pdf-split-by-format` | Split PDFs into parts when page format changes. |
| `pdf-split-by-toc` | Split PDF into chapter files from level-1 TOC entries. |
| `pdf-tiler-090` | Tile PDF to A4 at 90% scale. |
| `pdf-tiler-100` | Tile PDF to A4 at original A1 size. |
| `pdf-toc-clean` | Remove out-of-range TOC entries and write cleaned outputs. |
| `dicom2jpg` | Convert DICOM images to JPEG (PixelMed). |
| `dicomviewer` | Launch PixelMed DICOM viewer. |
| `video2h264` | Convert one video to H.264 MP4 via ffmpeg. |
| `video2h265` | Convert one video to H.265 MP4 via ffmpeg. |
| `ubuntu-dark-theme` | Apply GNOME and Qt dark-theme settings. |

### Selected Usage Examples

Launch Antigravity CLI in YOLO mode (each YOLO command help documents every registered YOLO CLI option in alphabetical order):

```bash
s agy
```

Run useReq bootstrap on first-level child directories:

```bash
s req --dirs
```

`req` skips every target that is not a Git repository root in current-directory and `--dirs` modes, emitting one skip evidence line per directory.

Clean caches without interactive confirmation:

```bash
s clean --yes
```

Crop PDF with automatic bbox over a page window:

```bash
s pdf-crop --in input.pdf --out cropped.pdf --analyze-pages 1-10 --pages 1-
```

Merge PDFs and choose output file:

```bash
s pdf-merge -o merged.pdf a.pdf b.pdf c.pdf
```

Split PDF by TOC chapters:

```bash
s pdf-split-by-toc document.pdf
```

Convert a video to H.264 MP4:

```bash
s video2h264 input.mov
```

Run tests and pass pytest options:

```bash
s tests -q -k "pdf"
```

Open current git project in VS Code / Insiders:

```bash
s vscode
s vsinsider
```


## Local Build and Release

Build validated sdist and wheel archives (requires Python `>=3.11` and `uv` or `build`):

```bash
./scripts/build.sh
```

- Removes every existing archive in the output directory (`*.tar.gz`, `*.whl`, `*.zip`, `*.egg`) of any version before building and preserves non-generated entries.
- Writes to `dist/` by default; set `BUILD_DIST_DIR` to use another output directory.
- Resolves the reproducible timestamp from a valid `SOURCE_DATE_EPOCH` environment value or from the tracked `.build-epoch` file; a missing or malformed epoch aborts the build.
- Validates archive readability and members: the sdist contains `pyproject.toml` and `src/shell_scripts/__init__.py` and excludes `tests/`, `src/shellscripts.egg-info/`, `setup.cfg`, and `MANIFEST.in`; the wheel contains the license and the `shellscripts`/`s` entry points.
- Removes intermediate build trees, generated metadata, temporary files, and `src` bytecode caches before printing `PASS`/`FAIL` phase evidence and a `BUILD SUMMARY` listing every deliverable.

Run the full pre-release verification before an official release:

```bash
./scripts/pre-release-check.sh
```

- Runs project-structure, executable-bit, toolchain, Bash/Python syntax, optional quality (`SKIP` when not configured), pytest, delegated build, artifact-validation, and repository-integrity checks in order.
- Builds inside a `mktemp -d` directory outside the working tree through `BUILD_DIST_DIR` and never reads, verifies, cleans, or modifies `dist/` entries.
- Removes generated artifacts and the temporary build directory on success, failure, and signal termination, then compares the repository state with the pre-run baseline.
- Stops at the first failed mandatory check with exit code `1` and prints `PASS`/`FAIL`/`SKIP` evidence plus a final summary.

Publishing: pushing a `vX.Y.Z` tag triggers `.github/workflows/release-pypi.yml`, which publishes the `dist/` archives present in the tagged commit to the GitHub Release and, only for tags reachable from `master`, to PyPI through OIDC Trusted Publishing. The workflow never builds distributions.


## Acknowledgments
