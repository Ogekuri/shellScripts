#!/usr/bin/env python3
"""@brief AI CLI installers dispatcher with OS-aware package resolution.

@details Provides selector-based installation flows for npm-distributed tools
and direct-download installers. Npm command prefix and installer payload
sources are resolved from detected runtime OS. Kiro package resolution is
manifest-driven on Linux and explicitly unsupported on Windows/macOS.
@satisfies PRJ-003, DES-013, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-047, REQ-056, REQ-067
"""

import json
import os
import platform
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
KIRO_CHANNEL_BASE_URL = "https://prod.download.cli.kiro.dev/stable"
KIRO_MANIFEST_URL = f"{KIRO_CHANNEL_BASE_URL}/latest/manifest.json"
KIRO_LINUX_VARIANT = "headless"


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
    Windows when available to avoid process-launch failures. For Windows
    Copilot installs, retries once after a non-zero first attempt to mitigate
    transient file-lock failures during binary replacement.
    @param tool_key {str} Tool identifier key from `TOOLS`.
    @return {None} Executes side effects and prints result messages.
    @satisfies DES-013, REQ-008, REQ-047, REQ-056
    """

    info = TOOLS[tool_key]
    command = list(info["install"])
    windows_runtime = is_windows()
    if windows_runtime:
        npm_cmd_path = shutil.which("npm.cmd")
        if npm_cmd_path:
            command[0] = npm_cmd_path
    else:
        require_commands("sudo")
        command = ["sudo"] + command
    require_commands(command[0])
    print_info(f"Installing {info['name']}...")
    max_attempts = 2 if windows_runtime and tool_key == "copilot" else 1
    result = None
    for attempt_idx in range(max_attempts):
        result = subprocess.run(command)
        if result.returncode == 0:
            break
        if attempt_idx + 1 < max_attempts:
            print_info(
                "Retrying GitHub Copilot CLI installation after transient Windows file lock..."
            )
    assert result is not None
    if result.returncode != 0:
        print_error(f"Failed to install {info['name']}.")
    else:
        print_success(f"{info['name']} installed.")
    print()


def _normalize_kiro_linux_arch(machine_token):
    """@brief Normalize machine architecture token for Kiro Linux packages.

    @details Maps runtime machine names into manifest architecture keys accepted
    by Kiro headless Linux ZIP entries. Raises explicit error for unknown
    architecture to avoid ambiguous package selection.
    @param machine_token {str} Raw `platform.machine()` token.
    @return {str} Normalized architecture token (`x86_64` or `aarch64`).
    @throws {RuntimeError} When architecture is not supported by Kiro installer.
    @satisfies REQ-010, REQ-067
    """

    normalized = machine_token.strip().lower()
    if normalized in ("x86_64", "amd64"):
        return "x86_64"
    if normalized in ("aarch64", "arm64"):
        return "aarch64"
    raise RuntimeError(
        f"Unsupported Linux architecture for Kiro installer: {machine_token}"
    )


def _detect_kiro_linux_libc():
    """@brief Detect Linux libc class token for Kiro package selection.

    @details Uses `platform.libc_ver()` to classify runtime libc as `musl` or
    `gnu`. Unknown or empty values default to `gnu` to keep deterministic
    package selection for glibc environments.
    @return {str} libc class token (`musl` or `gnu`).
    @satisfies REQ-010
    """

    libc_name, _ = platform.libc_ver()
    if "musl" in libc_name.lower():
        return "musl"
    return "gnu"


def _resolve_kiro_linux_download_path(manifest, arch_token, libc_token):
    """@brief Resolve Kiro Linux ZIP download path from manifest metadata.

    @details Filters manifest packages by Linux OS, headless ZIP variant,
    runtime architecture, and runtime libc class reflected in target triple.
    Returns first matching `download` path and fails explicitly when no match
    exists.
    @param manifest {dict[str, object]} Parsed Kiro manifest JSON payload.
    @param arch_token {str} Normalized architecture token (`x86_64|aarch64`).
    @param libc_token {str} Normalized libc token (`gnu|musl`).
    @return {str} Relative download path from manifest `packages[].download`.
    @throws {RuntimeError} When no manifest package matches runtime filters.
    @satisfies DES-013, REQ-010
    """

    if libc_token not in ("gnu", "musl"):
        raise RuntimeError(f"Unsupported Linux libc class for Kiro installer: {libc_token}")

    target_suffix = "linux-musl" if libc_token == "musl" else "linux-gnu"
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise RuntimeError("Invalid Kiro manifest format: missing packages list")

    for package in packages:
        if not isinstance(package, dict):
            continue
        if package.get("os") != "linux":
            continue
        if package.get("fileType") != "zip":
            continue
        if package.get("variant") != KIRO_LINUX_VARIANT:
            continue
        if package.get("architecture") != arch_token:
            continue
        target_triple = str(package.get("targetTriple", ""))
        if target_suffix not in target_triple:
            continue
        download_path = package.get("download")
        if isinstance(download_path, str) and download_path:
            return download_path

    raise RuntimeError(
        "No Kiro Linux package matched runtime architecture/libc in manifest"
    )


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

    @details Rejects unsupported runtime OS values (`windows`, `darwin`) with
    explicit errors. On Linux, resolves runtime architecture/libc package from
    official stable manifest, downloads selected ZIP archive, extracts
    `kiro-cli*` binaries, and installs them into `~/.local/bin`.
    @return {None} Executes side effects and prints result messages.
    @throws {RuntimeError} When runtime OS is unsupported or manifest has no
      matching package.
    @throws {urllib.error.URLError} When archive download fails.
    @throws {json.JSONDecodeError} When manifest payload is malformed.
    @throws {zipfile.BadZipFile} When downloaded archive is invalid.
    @throws {OSError} When extraction/copy/permission updates fail.
    @satisfies DES-013, REQ-010, REQ-067
    """

    import urllib.error
    import urllib.request

    print_info("Installing Kiro CLI...")
    runtime_os = get_runtime_os()
    if runtime_os == "windows":
        print_error("Failed to install Kiro CLI: unsupported runtime OS windows.")
        print()
        return
    if runtime_os == "darwin":
        print_error("Failed to install Kiro CLI: unsupported runtime OS darwin.")
        print()
        return
    if runtime_os != "linux":
        print_error(f"Failed to install Kiro CLI: unsupported runtime OS {runtime_os}.")
        print()
        return

    install_dir = Path.home() / ".local" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        machine_arch = _normalize_kiro_linux_arch(platform.machine())
        libc_token = _detect_kiro_linux_libc()
        with urllib.request.urlopen(KIRO_MANIFEST_URL, timeout=15) as response:
            manifest_payload = json.loads(response.read().decode())
        download_path = _resolve_kiro_linux_download_path(
            manifest_payload,
            machine_arch,
            libc_token,
        )
        archive_url = f"{KIRO_CHANNEL_BASE_URL}/{download_path}"

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "kiro.zip")
            print_info("Downloading Kiro CLI...")
            urllib.request.urlretrieve(archive_url, zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmpdir)

            copied_binaries = []
            for src in Path(tmpdir).rglob("kiro-cli*"):
                if src.is_file():
                    dest = install_dir / src.name
                    shutil.copy2(src, str(dest))
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
