#!/usr/bin/env python3
import subprocess

from shell_scripts.utils import print_info, command_exists, print_error

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
    print_info("Configure Adwaita-dark")

    if command_exists("gsettings"):
        subprocess.run([
            "gsettings", "set", "org.gnome.desktop.interface",
            "gtk-theme", "Adwaita-dark",
        ])
    else:
        print_error("gsettings not found.")

    if command_exists("gtk-chtheme"):
        subprocess.run(["gtk-chtheme"])

    import os
    env5 = os.environ.copy()
    env5["QT_QPA_PLATFORMTHEME"] = "qt5ct"
    if command_exists("qt5ct"):
        subprocess.run(["qt5ct"], env=env5)

    env6 = os.environ.copy()
    env6["QT_QPA_PLATFORMTHEME"] = "qt6ct"
    if command_exists("qt6ct"):
        subprocess.run(["qt6ct"], env=env6)

    return 0
