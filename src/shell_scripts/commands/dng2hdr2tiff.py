#!/usr/bin/env python3
"""@brief Convert one DNG file into one HDR-merged lossless 16-bit TIFF output.

@details Thin command wrapper around shared DNG-to-HDR pipeline implemented in
`dng2hdr2jpg`; preserves identical preprocessing/options/backend behavior and
switches only final encoding stage to lossless uint16 TIFF write.
@satisfies DES-008, REQ-055, REQ-059, REQ-063, REQ-066, REQ-070, REQ-080, REQ-081, REQ-082
"""

from shell_scripts.commands import dng2hdr2jpg

PROGRAM = dng2hdr2jpg.PROGRAM
DESCRIPTION = "Convert DNG to HDR-merged lossless 16-bit TIFF with optional luminance-hdr-cli backend."


def print_help(version):
    """@brief Print help text for the `dng2hdr2tiff` command.

    @details Delegates to shared TIFF help renderer defined in shared DNG/HDR
    implementation module.
    @param version {str} CLI version label.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-063, REQ-070, REQ-082
    """

    dng2hdr2jpg.print_help_tiff(version)


def run(args):
    """@brief Execute `dng2hdr2tiff` command pipeline.

    @details Delegates to shared TIFF pipeline runner with lossless uint16 final
    encoding and shared option/backend semantics.
    @param args {list[str]} Command argument vector excluding command token.
    @return {int} `0` on success; `1` on failure.
    @satisfies REQ-055, REQ-059, REQ-066, REQ-073, REQ-074, REQ-075, REQ-076, REQ-080, REQ-081
    """

    return dng2hdr2jpg.run_tiff(args)
