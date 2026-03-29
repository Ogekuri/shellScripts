#!/usr/bin/env python3
"""@brief GNOME/Qt dark-theme configurator.

@details Conditionally executes available theme helper executables and validates
each executable immediately before invocation.
@satisfies REQ-022, REQ-055, REQ-056
"""
import subprocess

from shell_scripts.utils import print_info, command_exists, print_error, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Apply GNOME and Qt dark theme settings."


def print_help(version):
    print(f"Usage: {PROGRAM} ubuntu-dark-theme ({version})")
    print()
    print("ubuntu-dark-theme options:")
    print("  --help  - Show this help message.")
    print()
    print("Applies Adwaita-dark GTK theme via gsettings, then launches")
    print("gtk-chtheme, qt5ct, and qt6ct for further customization.")


def run(args):
    """@brief Apply dark-theme settings with conditional executable checks.

    @details For each available theme tool (`gsettings`, `gtk-chtheme`, `qt5ct`,
    `qt6ct`), validates command executability before subprocess invocation.
    @param args {list[str]} Unused command arguments.
    @return {int} `0` on completion.
    @satisfies REQ-022, REQ-055, REQ-056
    """

    print_info("Configure Adwaita-dark")

    if command_exists("gsettings"):
        require_commands("gsettings")
        subprocess.run([
            "gsettings", "set", "org.gnome.desktop.interface",
            "gtk-theme", "Adwaita-dark",
        ])
    else:
        print_error("gsettings not found.")

    if command_exists("gtk-chtheme"):
        require_commands("gtk-chtheme")
        subprocess.run(["gtk-chtheme"])

    import os
    env5 = os.environ.copy()
    env5["QT_QPA_PLATFORMTHEME"] = "qt5ct"
    if command_exists("qt5ct"):
        require_commands("qt5ct")
        subprocess.run(["qt5ct"], env=env5)

    env6 = os.environ.copy()
    env6["QT_QPA_PLATFORMTHEME"] = "qt6ct"
    if command_exists("qt6ct"):
        require_commands("qt6ct")
        subprocess.run(["qt6ct"], env=env6)

    return 0
