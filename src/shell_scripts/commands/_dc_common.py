#!/usr/bin/env python3
"""@brief Shared MIME-based dispatcher primitives for diff/edit/view commands.

@details Provides extension and MIME classification plus external executable
resolution and blocking subprocess invocation for generic file tool wrappers.
@satisfies DES-007, REQ-024, REQ-055, REQ-056, REQ-064
"""

import os
import subprocess

from shell_scripts.utils import is_executable_command, print_error

CODE_EXTENSIONS = {
    "c", "h", "cc", "cpp", "cxx", "hpp", "hh", "hxx", "rs", "go",
    "java", "kt", "kts", "cs", "swift", "php", "rb", "py", "js",
    "mjs", "cjs", "ts", "tsx", "jsx", "vue", "svelte", "sh", "bash",
    "zsh", "lua", "pl", "pm", "sql", "yaml", "yml", "toml", "ini",
    "cfg", "conf", "json", "xml", "gradle", "mk", "cmake", "dockerfile",
}

MARKDOWN_EXTENSIONS = {"md", "markdown", "mdown", "mkd"}
HTML_EXTENSIONS = {"html", "htm", "xhtml"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "svg"}


def get_extension(filepath):
    name = os.path.basename(filepath)
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[1].lower()


def detect_mime(filepath):
    """@brief Detect file MIME type with external tools.

    @details Probes MIME by trying `mimetype` then `file --mime-type`, using
    executable availability checks before subprocess invocation.
    @param filepath {str} Target file path.
    @return {str} MIME type string or empty string on detection failure.
    @satisfies REQ-024, REQ-056
    """

    if not os.path.exists(filepath):
        return ""
    for cmd in ["mimetype", "file"]:
        if is_executable_command(cmd):
            try:
                result = subprocess.run(
                    [cmd if cmd == "mimetype" else "file", "-b", "--mime-type", filepath]
                    if cmd == "file" else ["mimetype", "-b", filepath],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    return ""


def categorize(filepath):
    ext = get_extension(filepath)
    mime = detect_mime(filepath)

    if mime.startswith("image/"):
        return "image"
    if mime == "application/pdf":
        return "pdf"
    if mime == "text/html":
        return "html"

    if (mime.startswith("text/") or mime in (
        "application/json", "application/xml", "application/x-shellscript", ""
    )):
        if ext in MARKDOWN_EXTENSIONS:
            return "markdown"
        if ext in HTML_EXTENSIONS:
            return "html"
        if ext in CODE_EXTENSIONS:
            return "code"
        return "text"

    if not os.path.exists(filepath):
        if ext in MARKDOWN_EXTENSIONS:
            return "markdown"
        if ext in HTML_EXTENSIONS:
            return "html"
        if ext == "pdf":
            return "pdf"
        if ext in IMAGE_EXTENSIONS:
            return "image"
        if ext in CODE_EXTENSIONS:
            return "code"
        return "text"

    return "other"


def pick_cmd(primary, fallback):
    """@brief Select primary command when executable, else fallback.

    @details Uses shared executable-check helper on first token of primary
    command vector.
    @param primary {list[str]} Preferred command vector.
    @param fallback {list[str]} Fallback command vector.
    @return {list[str]} Selected executable command vector.
    @satisfies REQ-024, REQ-055
    """

    if primary and is_executable_command(primary[0]):
        return primary
    return fallback


def dispatch(category_cmds, fallback_cmd, filepath, extra_args):
    """@brief Dispatch diff/edit/view command by detected file category.

    @details Resolves category-specific command vector, validates executable
    availability, and executes selected command via blocking subprocess run.
    @param category_cmds {dict[str, list[str]]} Category-to-command mapping.
    @param fallback_cmd {list[str]} Fallback command vector.
    @param filepath {str} Target file path.
    @param extra_args {list[str]} Additional arguments forwarded to executable.
    @return {int} `1` when executable is unavailable; child return code otherwise.
    @satisfies REQ-024, REQ-055, REQ-056, REQ-064
    """

    category = categorize(filepath)
    cmd_list = category_cmds.get(category, fallback_cmd)
    cmd = pick_cmd(cmd_list, fallback_cmd)

    if not is_executable_command(cmd[0]):
        print_error(f"Command not executable: {cmd[0]}")
        return 1

    full_cmd = cmd + [filepath] + extra_args
    result = subprocess.run(full_cmd)
    return result.returncode
