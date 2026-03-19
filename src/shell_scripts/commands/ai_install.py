#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path

from shell_scripts.utils import print_info, print_error, print_success

PROGRAM = "shellscripts"
DESCRIPTION = "Install AI CLI tools (Codex, Copilot, Gemini, OpenCode, Claude, Kiro)."

TOOLS = {
    "codex": {
        "name": "OpenAI Codex CLI",
        "install": ["sudo", "npm", "i", "-g", "@openai/codex"],
    },
    "copilot": {
        "name": "GitHub Copilot CLI",
        "install": ["sudo", "npm", "install", "-g", "@github/copilot"],
    },
    "gemini": {
        "name": "Google Gemini CLI",
        "install": ["sudo", "npm", "install", "-g", "@google/gemini-cli"],
    },
    "opencode": {
        "name": "OpenCode CLI",
        "install": ["sudo", "npm", "install", "-g", "opencode-ai"],
    },
}

CLAUDE_BUCKET = (
    "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819"
    "/claude-code-releases"
)
KIRO_URL = "https://desktop-release.q.us-east-1.amazonaws.com/latest/kirocli-x86_64-linux.zip"


def print_help(version):
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
    info = TOOLS[tool_key]
    print_info(f"Installing {info['name']}...")
    result = subprocess.run(info["install"])
    if result.returncode != 0:
        print_error(f"Failed to install {info['name']}.")
    else:
        print_success(f"{info['name']} installed.")
    print()


def _install_claude():
    import urllib.request
    print_info("Installing Claude CLI...")
    install_dir = Path.home() / ".claude" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        version_url = f"{CLAUDE_BUCKET}/latest"
        with urllib.request.urlopen(version_url, timeout=15) as resp:
            version = resp.read().decode().strip()

        print_info(f"Downloading Claude CLI version {version}...")
        binary_url = f"{CLAUDE_BUCKET}/{version}/linux-x64/claude"
        dest = install_dir / "claude"
        urllib.request.urlretrieve(binary_url, str(dest))
        dest.chmod(0o755)
        print_success(f"Claude CLI installed to {dest}")
    except Exception as e:
        print_error(f"Failed to install Claude CLI: {e}")
    print()


def _install_kiro():
    import urllib.request
    print_info("Installing Kiro CLI...")
    install_dir = Path.home() / ".local" / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "kiro.zip")
            print_info("Downloading Kiro CLI...")
            urllib.request.urlretrieve(KIRO_URL, zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmpdir)

            kiro_bin_dir = os.path.join(tmpdir, "kirocli", "bin")
            for binary in ("kiro-cli", "kiro-cli-chat", "kiro-cli-term"):
                src = os.path.join(kiro_bin_dir, binary)
                if os.path.exists(src):
                    dest = install_dir / binary
                    shutil.copy2(src, dest)
                    dest.chmod(0o755)

            print_success(f"Kiro CLI installed to {install_dir}")
    except Exception as e:
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
