#!/usr/bin/env python3
import os
import subprocess
import shutil

from shell_scripts.utils import print_error

PROGRAM = "shellscripts"
DESCRIPTION = "Launch PixelMed DICOM image viewer."

JAVA_WRAPPERS = "/usr/lib/java-wrappers/java-wrappers.sh"


def print_help(version):
    print(f"Usage: {PROGRAM} dicomviewer [files...] ({version})")
    print()
    print("dicomviewer options:")
    print("  [files...]  - DICOM files to view.")
    print("  --help      - Show this help message.")


def _find_java():
    for java in ("java", "/usr/bin/java"):
        if shutil.which(java):
            return java
    return None


def _find_jars(*jar_names):
    jar_dirs = ["/usr/share/java", "/usr/local/share/java"]
    found = []
    for name in jar_names:
        for d in jar_dirs:
            jar_path = os.path.join(d, f"{name}.jar")
            if os.path.exists(jar_path):
                found.append(jar_path)
                break
    return found


def run(args):
    if not os.path.exists(JAVA_WRAPPERS):
        print_error(
            "java-wrappers not found. Install the 'java-wrappers' package."
        )
        return 1

    java = _find_java()
    if not java:
        print_error("Java runtime not found.")
        return 1

    jars = _find_jars(
        "pixelmed", "hsqldb", "vecmath", "jmdns",
        "commons-codec", "jai_imageio", "clibwrapper_jiio"
    )
    classpath = ":".join(jars) if jars else ""

    cmd = [
        java, "-Djava.awt.headless=true",
        "-cp", classpath,
        "com.pixelmed.display.DicomImageViewer",
    ] + args

    result = subprocess.run(cmd)
    return result.returncode
