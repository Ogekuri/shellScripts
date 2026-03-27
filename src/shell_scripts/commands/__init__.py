"""@brief Command registry and lazy command module resolver.

@details Defines a static command-to-module map consumed by the CLI dispatcher.
Dictionary lookup enforces deterministic command availability; missing keys
resolve to `None` to drive unknown-command error handling in the caller.
@satisfies PRJ-001, PRJ-002, PRJ-003, DES-001, DES-008
"""

import importlib
from types import ModuleType

## @var _COMMAND_MODULES
#  @brief Static map from CLI command names to importable module paths.
#  @details Enables lazy command loading and deterministic command exposure.
#  Removing an entry removes command discoverability and dispatch reachability.
#  @satisfies PRJ-003, DES-001
_COMMAND_MODULES = {
    "ai-install": "shell_scripts.commands.ai_install",
    "clean": "shell_scripts.commands.clean",
    "cli-claude": "shell_scripts.commands.cli_claude",
    "cli-codex": "shell_scripts.commands.cli_codex",
    "cli-copilot": "shell_scripts.commands.cli_copilot",
    "cli-gemini": "shell_scripts.commands.cli_gemini",
    "cli-kiro": "shell_scripts.commands.cli_kiro",
    "cli-opencode": "shell_scripts.commands.cli_opencode",
    "dicom2jpg": "shell_scripts.commands.dicom2jpg",
    "dng2hdr2jpg": "shell_scripts.commands.dng2hdr2jpg",
    "dicomviewer": "shell_scripts.commands.dicomviewer",
    "diff": "shell_scripts.commands.diff_cmd",
    "edit": "shell_scripts.commands.edit_cmd",
    "view": "shell_scripts.commands.view_cmd",
    "doxygen": "shell_scripts.commands.doxygen_cmd",
    "pdf-crop": "shell_scripts.commands.pdf_crop",
    "pdf-merge": "shell_scripts.commands.pdf_merge",
    "pdf-split-by-format": "shell_scripts.commands.pdf_split_by_format",
    "pdf-split-by-toc": "shell_scripts.commands.pdf_split_by_toc",
    "pdf-tiler-090": "shell_scripts.commands.pdf_tiler_090",
    "pdf-tiler-100": "shell_scripts.commands.pdf_tiler_100",
    "pdf-toc-clean": "shell_scripts.commands.pdf_toc_clean",
    "req": "shell_scripts.commands.req_cmd",
    "tests": "shell_scripts.commands.tests_cmd",
    "ubuntu-dark-theme": "shell_scripts.commands.ubuntu_dark_theme",
    "video2h264": "shell_scripts.commands.video2h264",
    "video2h265": "shell_scripts.commands.video2h265",
    "venv": "shell_scripts.commands.venv_cmd",
    "vscode": "shell_scripts.commands.vscode_cmd",
    "vsinsider": "shell_scripts.commands.vsinsider_cmd",
}


def get_command(name: str) -> ModuleType | None:
    """@brief Resolve one CLI command token to its command module.

    @details Performs O(1) dictionary lookup on `_COMMAND_MODULES`; returns
    `None` for unknown tokens; imports target module lazily only on hit.
    @param name {str} CLI command token.
    @return {ModuleType|None} Imported command module for known token; `None` otherwise.
    @throws {ImportError} If module path exists in map but import fails.
    @satisfies PRJ-001, DES-001, DES-008
    """
    module_path = _COMMAND_MODULES.get(name)
    if module_path is None:
        return None
    return importlib.import_module(module_path)


def get_all_commands() -> dict[str, str]:
    """@brief Build command-description index for help rendering.

    @details Iterates sorted command keys for stable output ordering; imports
    each module via `get_command`; extracts `DESCRIPTION` or empty string.
    Time complexity O(N log N) for N commands due to key sorting.
    @return {dict[str, str]} Mapping `command_name -> description`.
    @throws {ImportError} If any mapped command module import fails.
    @satisfies PRJ-002, DES-001, DES-008
    """
    result: dict[str, str] = {}
    for name in sorted(_COMMAND_MODULES):
        mod = get_command(name)
        result[name] = getattr(mod, "DESCRIPTION", "")
    return result
