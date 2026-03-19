import importlib

_COMMAND_MODULES = {
    "ai-install": "shell_scripts.commands.ai_install",
    "bin-links": "shell_scripts.commands.bin_links",
    "clean": "shell_scripts.commands.clean",
    "cli-claude": "shell_scripts.commands.cli_claude",
    "cli-codex": "shell_scripts.commands.cli_codex",
    "cli-copilot": "shell_scripts.commands.cli_copilot",
    "cli-gemini": "shell_scripts.commands.cli_gemini",
    "cli-kiro": "shell_scripts.commands.cli_kiro",
    "cli-opencode": "shell_scripts.commands.cli_opencode",
    "dicom2jpg": "shell_scripts.commands.dicom2jpg",
    "dicomviewer": "shell_scripts.commands.dicomviewer",
    "double-commander-differ": "shell_scripts.commands.dc_differ",
    "double-commander-editor": "shell_scripts.commands.dc_editor",
    "double-commander-viewer": "shell_scripts.commands.dc_viewer",
    "doxygen": "shell_scripts.commands.doxygen_cmd",
    "pdf-crop": "shell_scripts.commands.pdf_crop",
    "pdf-merge": "shell_scripts.commands.pdf_merge",
    "pdf-split-by-format": "shell_scripts.commands.pdf_split_by_format",
    "pdf-split-by-toc": "shell_scripts.commands.pdf_split_by_toc",
    "pdf-tiler-090": "shell_scripts.commands.pdf_tiler_090",
    "pdf-tiler-100": "shell_scripts.commands.pdf_tiler_100",
    "pdf-toc-clean": "shell_scripts.commands.pdf_toc_clean",
    "tests": "shell_scripts.commands.tests_cmd",
    "ubuntu-dark-theme": "shell_scripts.commands.ubuntu_dark_theme",
    "venv": "shell_scripts.commands.venv_cmd",
    "vscode": "shell_scripts.commands.vscode_cmd",
    "vsinsider": "shell_scripts.commands.vsinsider_cmd",
}


def get_command(name):
    module_path = _COMMAND_MODULES.get(name)
    if module_path is None:
        return None
    return importlib.import_module(module_path)


def get_all_commands():
    result = {}
    for name in sorted(_COMMAND_MODULES):
        mod = get_command(name)
        result[name] = getattr(mod, "DESCRIPTION", "")
    return result
