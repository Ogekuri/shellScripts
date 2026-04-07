#!/usr/bin/env python3
"""@brief AI CLI installers dispatcher with OS-aware package resolution.

@details Provides selector-based installation flows for npm-distributed tools
and direct-download installers. Npm command prefix and direct-download package
sources are resolved from detected runtime OS to keep installer payloads
aligned with Linux, Windows, and macOS targets.
@satisfies PRJ-003, DES-013, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-047, REQ-056
"""

import os
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path

from shell_scripts.utils import (
    get_runtime_os,
    is_windows,
    print_info,
    print_error,
    print_success,
    require_commands,
)

PROGRAM = "shellscripts"
DESCRIPTION = "Install AI CLI tools (Codex, Copilot, Gemini, OpenCode, Claude, Kiro)."

TOOLS = {
    "codex": {
        "name": "OpenAI Codex CLI",
        "install": ["npm", "install", "-g", "@openai/codex"],
    },
    "copilot": {
        "name": "GitHub Copilot CLI",
        "install": ["npm", "install", "-g", "@github/copilot"],
    },
    "gemini": {
        "name": "Google Gemini CLI",
        "install": ["npm", "install", "-g", "@google/gemini-cli"],
    },
    "opencode": {
        "name": "OpenCode CLI",
        "install": ["npm", "install", "-g", "opencode-ai"],
    },
}

CLAUDE_BUCKET = (
    "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819"
    "/claude-code-releases"
)
CLAUDE_ARTIFACT_CANDIDATES = {
    "linux": ("linux-x64/claude",),
    "windows": ("windows-x64/claude.exe", "win32-x64/claude.exe"),
    "darwin": ("darwin-arm64/claude", "darwin-x64/claude"),
}
KIRO_BASE_URL = "https://desktop-release.q.us-east-1.amazonaws.com/latest"
KIRO_ARCHIVE_CANDIDATES = {
    "linux": ("kirocli-x86_64-linux.zip",),
    "windows": ("kirocli-x86_64-windows.zip",),
    "darwin": ("kirocli-aarch64-macos.zip", "kirocli-x86_64-macos.zip"),
}


def print_help(version):
    """@brief Render command help for `ai-install`.

    @details Prints supported selectors and execution contract for installer
    dispatch.
    @param version {str} CLI version string appended in usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008
    """

    print(f"Usage: {PROGRAM} ai-install [options] ({version})")
    print()
    print("ai-install options:")
    print("  --all        - Install all AI CLI tools (default).")
    print("  --codex      - Install OpenAI Codex CLI only.")
    print("  --copilot    - Install GitHub Copilot CLI only.")
    print("  --gemini     - Install Google Gemini CLI only.")
    print("  --opencode   - Install OpenCode CLI only.")
    print("  --claude     - Install Claude CLI only.")
    print("  --kiro       - Install Kiro CLI only.")
    print("  --help       - Show this help message.")


def _install_npm_tool(tool_key):
    """@brief Execute npm-based installer command for selected tool.

    @details Resolves base npm command from static tool mapping, prepends
    `sudo` when runtime OS is not Windows, and uses resolved `npm.cmd` path on
    Windows when available to avoid process-launch failures. Executes subprocess
    and emits status messages.
    @param tool_key {str} Tool identifier key from `TOOLS`.
    @return {None} Executes side effects and prints result messages.
    @satisfies DES-013, REQ-008, REQ-047, REQ-056
    """

    info = TOOLS[tool_key]
    command = list(info["install"])
    if is_windows():
        npm_cmd_path = shutil.which("npm.cmd")
        if npm_cmd_path:
            command[0] = npm_cmd_path
    else:
        require_commands("sudo")
        command = ["sudo"] + command
    require_commands(command[0])
    print_info(f"Installing {info['name']}...")
    result = subprocess.run(command)
    if result.returncode != 0:
        print_error(f"Failed to install {info['name']}.")
    else:
        print_success(f"{info['name']} installed.")
    print()


def _install_claude():
    """@brief Install Claude CLI by direct binary download.

    @details Downloads latest version metadata from configured bucket, resolves
    OS-specific Claude artifact candidates from runtime OS token, downloads the
    first available artifact, writes executable into `~/.claude/bin/claude`,
    and sets execute permissions on non-Windows runtimes.
    @return {None} Executes side effects and prints result messages.
    @throws {RuntimeError} When runtime OS has no configured package candidates.
    @throws {urllib.error.URLError} When metadata or artifact download fails.
    @throws {OSError} When destination write or permission update fails.
    @satisfies DES-013, REQ-009
    """

    import urllib.error
    import urllib.request

    print_info("Installing Claude CLI...")
    install_dir = Path.home() / ".claude" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        runtime_os = get_runtime_os()
        artifact_candidates = CLAUDE_ARTIFACT_CANDIDATES.get(runtime_os)
        if not artifact_candidates:
            raise RuntimeError(f"Unsupported runtime OS for Claude installer: {runtime_os}")

        version_url = f"{CLAUDE_BUCKET}/latest"
        with urllib.request.urlopen(version_url, timeout=15) as resp:
            version = resp.read().decode().strip()

        print_info(f"Downloading Claude CLI version {version}...")
        download_error = None
        dest = install_dir / "claude"
        for artifact_path in artifact_candidates:
            binary_url = f"{CLAUDE_BUCKET}/{version}/{artifact_path}"
            try:
                urllib.request.urlretrieve(binary_url, str(dest))
                break
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                download_error = error
        else:
            raise RuntimeError(
                f"No Claude artifact candidate was downloadable for OS {runtime_os}"
            ) from download_error

        if runtime_os != "windows":
            dest.chmod(0o755)
        print_success(f"Claude CLI installed to {dest}")
    except (OSError, RuntimeError, urllib.error.HTTPError, urllib.error.URLError) as e:
        print_error(f"Failed to install Claude CLI: {e}")
    print()


def _install_kiro():
    """@brief Install Kiro CLI binaries by ZIP extraction flow.

    @details Resolves runtime-OS archive candidates, downloads first available
    Kiro ZIP package, extracts binaries, copies `kiro-cli*` executables into
    `~/.local/bin`, and applies executable mode on non-Windows runtimes.
    @return {None} Executes side effects and prints result messages.
    @throws {RuntimeError} When runtime OS has no configured package candidates.
    @throws {urllib.error.URLError} When archive download fails.
    @throws {zipfile.BadZipFile} When downloaded archive is invalid.
    @throws {OSError} When extraction/copy/permission updates fail.
    @satisfies DES-013, REQ-010
    """

    import urllib.error
    import urllib.request

    print_info("Installing Kiro CLI...")
    install_dir = Path.home() / ".local" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        runtime_os = get_runtime_os()
        archive_candidates = KIRO_ARCHIVE_CANDIDATES.get(runtime_os)
        if not archive_candidates:
            raise RuntimeError(f"Unsupported runtime OS for Kiro installer: {runtime_os}")

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "kiro.zip")
            print_info("Downloading Kiro CLI...")
            download_error = None
            for archive_name in archive_candidates:
                archive_url = f"{KIRO_BASE_URL}/{archive_name}"
                try:
                    urllib.request.urlretrieve(archive_url, zip_path)
                    break
                except (urllib.error.HTTPError, urllib.error.URLError) as error:
                    download_error = error
            else:
                raise RuntimeError(
                    f"No Kiro archive candidate was downloadable for OS {runtime_os}"
                ) from download_error

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmpdir)

            copied_binaries = []
            for src in Path(tmpdir).rglob("kiro-cli*"):
                if src.is_file():
                    dest = install_dir / src.name
                    shutil.copy2(src, str(dest))
                    if runtime_os != "windows":
                        dest.chmod(0o755)
                    copied_binaries.append(dest.name)

            if not copied_binaries:
                raise RuntimeError("No kiro-cli* binaries found in extracted archive")

            print_success(f"Kiro CLI installed to {install_dir}")
    except (
        OSError,
        RuntimeError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        zipfile.BadZipFile,
    ) as e:
        print_error(f"Failed to install Kiro CLI: {e}")
    print()


ALL_INSTALLERS = {
    "codex": lambda: _install_npm_tool("codex"),
    "copilot": lambda: _install_npm_tool("copilot"),
    "gemini": lambda: _install_npm_tool("gemini"),
    "opencode": lambda: _install_npm_tool("opencode"),
    "claude": _install_claude,
    "kiro": _install_kiro,
}


def run(args):
    """@brief Parse selectors and execute selected AI installer routines.

    @details Accepts explicit selectors or defaults to full installer set when
    omitted; rejects unknown selectors with return code `1`.
    @param args {list[str]} CLI selector tokens for installer filtering.
    @return {int} `0` on successful dispatch; `1` on unknown selector.
    @satisfies REQ-006, REQ-007
    """

    selected = []
    for arg in args:
        key = arg.lstrip("-")
        if key == "all":
            selected = list(ALL_INSTALLERS.keys())
            break
        elif key in ALL_INSTALLERS:
            selected.append(key)
        else:
            print_error(f"Unknown option: {arg}")
            return 1

    if not selected:
        selected = list(ALL_INSTALLERS.keys())

    print_info(f"Starting AI CLI tools installation ({len(selected)} tools)...")
    print()

    for key in selected:
        ALL_INSTALLERS[key]()

    print_success("AI CLI tools installation complete.")
    return 0
