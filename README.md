# s/shellScripts (0.21.0)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
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
- Single CLI entrypoint with command dispatch and grouped built-in help (`shellscripts` and alias `s`).
- AI tooling bootstrap command (`ai-install`) with per-tool selectors for Codex, Copilot, Gemini, OpenCode, Claude, and Kiro.
- Project-context launchers for AI CLIs (`claude`, `codex`, `copilot`, `gemini`, `kiro`, `opencode`, `pi`) and IDEs (`vscode`, `vsinsider`).
- PDF workflow commands for crop, merge, split, TOC cleanup, and tiling.
- DICOM helpers (`dicom2jpg`, `dicomviewer`) and video transcoders (`video2h264`, `video2h265`).
- Project maintenance and automation commands (`req`, `clean`, `venv`, `tests`, `doxygen`, `ubuntu-dark-theme`).
- Startup update notification with rate-limited checks against GitHub Releases.


## Requirements

- Python `>=3.11`.
- Astral `uv` is required for install and runtime flows (`uv tool install`, `uvx`, `uv run`).
- Git is required for commands that enforce repository-root execution (`claude`, `codex`, `copilot`, `gemini`, `kiro`, `opencode`, `pi`, `clean`, `venv`, `tests`, `doxygen`, `vscode`, `vsinsider`).
- Command-specific external tools are required only for related commands:
  - `npm` (and `sudo` on non-Windows) for npm-based `ai-install` targets.
  - `req` for the `req` command.
  - `doxygen` (plus optional `make` and `pdflatex`) for `doxygen`.
  - `gs`, `pdfinfo`, `qpdf`, `pdftk`, `plakativ` for PDF commands.
  - `ffmpeg` for `video2h264` and `video2h265`.
  - Java runtime + PixelMed jars (+ `java-wrappers`) for DICOM commands.


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
shellscripts [command] [options]
# or
s [command] [options]
```

Built-in management flags:

- `--help` : show full help or command help (`shellscripts --help <command>`).
- `--version` / `--ver` : print installed version.
- `--upgrade` : run configured upgrade command automatically on Linux, otherwise print the manual command.
- `--uninstall` : run configured uninstall command automatically on Linux, otherwise print the manual command.
- `--write-config` : write the default runtime configuration file.

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
  - `upgrade`: command string executed by `--upgrade`.
  - `uninstall`: command string executed by `--uninstall`.
- `dispatch`
  - `diff`, `edit`, `view`: each command supports `categories` and `fallback` command vectors.
- `req`
  - `providers`: provider list forwarded to external `req`.
  - `static_checks`: static-check entries forwarded to external `req`.


## Shell Scripts

### Command List

| Command | Purpose |
|---|---|
| `ai-install` | Install AI CLIs (all or selected tools). |
| `claude` | Launch Claude CLI in project context. |
| `codex` | Launch Codex CLI in project context with auth sync and `CODEX_HOME`. |
| `copilot` | Launch Copilot CLI in project context. |
| `gemini` | Launch Gemini CLI in project context. |
| `kiro` | Launch Kiro CLI in project context. |
| `opencode` | Launch OpenCode CLI in project context. |
| `pi` | Launch pi.dev CLI in project context (adds default `--tools` when missing). |
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

Install all AI CLIs (default behavior):

```bash
s ai-install
```

Install only selected AI tools:

```bash
s ai-install --codex --gemini --claude
```

Run pi.dev with default tools injected automatically:

```bash
s pi
```

Override pi tools explicitly:

```bash
s pi --tools read,bash,grep,find
```

Run useReq bootstrap on first-level child directories:

```bash
s req --dirs
```

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


## Acknowledgments
