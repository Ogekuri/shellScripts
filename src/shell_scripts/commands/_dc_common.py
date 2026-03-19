#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

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
    if not os.path.exists(filepath):
        return ""
    for cmd in ["mimetype", "file"]:
        if shutil.which(cmd):
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
    if primary and shutil.which(primary[0]):
        return primary
    return fallback


def dispatch(category_cmds, fallback_cmd, filepath, extra_args):
    category = categorize(filepath)
    cmd_list = category_cmds.get(category, fallback_cmd)
    cmd = pick_cmd(cmd_list, fallback_cmd)

    if not shutil.which(cmd[0]):
        print(f"Error: command '{cmd[0]}' not found.", file=sys.stderr)
        return 1

    full_cmd = cmd + [filepath] + extra_args
    os.execvp(full_cmd[0], full_cmd)
