# s/shellScripts (0.5.0)

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
🚧 <strong>DRAFT:</strong> Preliminary Version 📝 - Work in Progress 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://github.com/Ogekuri/useReq"><strong>useReq/req</strong></a> 🤖✨ ⚠️<br>
<br>
</p>


## Feature Highlights
- Single CLI entrypoint with command dispatch and built-in command help.
- AI tooling bootstrap command (`ai-install`) for Codex, Copilot, Gemini, OpenCode, Claude, and Kiro CLIs.
- Project-context launchers for AI CLIs, VS Code, and VS Code Insiders.
- PDF workflow commands for crop, merge, split, TOC cleanup, and tiling.
- DICOM helpers for image conversion (`dicom2jpg`) and viewer launch (`dicomviewer`).
- Project maintenance commands (`clean`, `venv`, `tests`, `bin-links`, `ubuntu-dark-theme`, `doxygen`).
- Startup update notification with rate-limited checks against GitHub Releases.


## Requirements

- Linux environment is the supported platform.
- Python `>=3.11`.
- Astral `uv` is required for install and runtime flows (`uv tool install`, `uvx`, `uv run`).
- Command-specific external tools are required only for related commands:
  - `npm`/`sudo` for `ai-install` npm-based installers.
  - `doxygen` (plus optional `make` and `pdflatex`) for `doxygen`.
  - `gs`, `pdfinfo`, `qpdf`, `pdftk`, `plakativ` for PDF commands.
  - Java runtime + PixelMed jars for DICOM commands.


## Quick Start

### Prerequisites

- Install `uv`: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)


### Install / Upgrade

```bash
uv tool install shellscripts --force --from git+https://github.com/Ogekuri/shellScripts.git
```


### Run Without Installing (uvx)

```bash
uvx --from git+https://github.com/Ogekuri/shellScripts.git shellscripts <command> [args...]
```


### Run From a Local Clone

```bash
./scripts/s.sh <command> [args...]
```

or

```bash
uv run --project . python -m shell_scripts <command> [args...]
```


## Management Commands

Global syntax:

```bash
shellscripts/s [command] [options]
```

Built-in management flags:

- `--help` : show full help or command help (`shellscripts --help <command>`).
- `--version` / `--ver` : print installed version.
- `--upgrade` : reinstall via `uv tool install ... --force` (automatic on Linux).
- `--uninstall` : uninstall via `uv tool uninstall` (automatic on Linux).


## Shell Scripts

### Command List

| Command | Purpose |
|---|---|
| `ai-install` | Install AI CLIs (all or selected tools). |
| `bin-links` | Create/update symlinks from a source directory into a destination bin dir. |
| `clean` | Find and delete cache directories under a target path (default: git root). |
| `cli-claude` | Launch Claude CLI in git-project context. |
| `cli-codex` | Launch Codex CLI in git-project context with `CODEX_HOME=.codex`. |
| `cli-copilot` | Launch Copilot CLI in git-project context. |
| `cli-gemini` | Launch Gemini CLI in git-project context. |
| `cli-kiro` | Launch Kiro CLI in git-project context. |
| `cli-opencode` | Launch OpenCode CLI in git-project context. |
| `dicom2jpg` | Convert one DICOM file to JPEG. |
| `dicomviewer` | Open DICOM viewer for one or more DICOM files. |
| `diff` | Dispatch file differ by MIME/category. |
| `edit` | Dispatch file editor by MIME/category. |
| `view` | Dispatch file viewer by MIME/category. |
| `doxygen` | Generate HTML/XML/Markdown docs (and optional PDF). |
| `pdf-crop` | Crop PDF pages with auto or manual bounding boxes. |
| `pdf-merge` | Merge multiple PDFs and preserve/rebuild TOC bookmarks. |
| `pdf-split-by-format` | Split PDFs into parts when page format changes. |
| `pdf-split-by-toc` | Split a PDF into chapter files using level-1 TOC entries. |
| `pdf-tiler-090` | Tile PDF to A4 at 90% scale. |
| `pdf-tiler-100` | Tile PDF to A4 from A1 source size. |
| `pdf-toc-clean` | Remove out-of-range TOC entries and write cleaned files. |
| `tests` | Ensure/create `.venv` then run pytest (arguments passed through). |
| `ubuntu-dark-theme` | Apply GNOME/Qt dark theme commands. |
| `venv` | Recreate `.venv` and install `requirements.txt` if present. |
| `vscode` | Open project in VS Code with `CODEX_HOME` set. |
| `vsinsider` | Open project in VS Code Insiders with `CODEX_HOME` set. |

### Selected Usage Examples

Install all AI CLIs (default behavior):

```bash
s ai-install
```

Install only selected AI tools:

```bash
s ai-install --codex --gemini --claude
```

Clean caches without interactive confirmation:

```bash
s clean --yes
```

Create symlinks from `scripts/` into `~/bin`:

```bash
s bin-links scripts/
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

Run tests and pass pytest options:

```bash
s tests -q -k "pdf"
```

Open current git project in VS Code / Insiders:

```bash
s vscode
s vsinsider
```


## Acknowledgments
