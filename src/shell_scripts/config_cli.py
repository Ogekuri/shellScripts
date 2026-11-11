#!/usr/bin/env python3
"""@brief Schema-driven command-line configuration manager.

@details Implements the management flags `--print-raw`, `--print`,
`--info`, `--get`, `--set`, and `--unset` over the canonical runtime
configuration file `$HOME/.config/shellScripts/config.json`. All rendering,
path resolution, validation, and persistence is derived from the declarative
`CONFIG_SCHEMA` registry that MUST mirror `DEFAULT_RUNTIME_CONFIG`
(DES-032, DES-033); divergence fails every configuration command at dispatch
time (DES-034). Commands bootstrap a missing configuration file with system
defaults (REQ-116), persist every mutation atomically through a
same-directory temporary file and rename (DES-037, REQ-102, REQ-103),
coerce string arguments into strict JSON schema types (REQ-101), expose
array and map manipulation exclusively through `:`-separated path tokens
(DES-038, REQ-122 through REQ-131), apply collection mutations to the
effective configuration and persist the resulting collection as one override
value (DES-039), and display every value unmasked in plain text (REQ-098).
Existing configuration load, merge, normalization, and accessor logic is not
modified (DES-035).
@satisfies DES-032, DES-033, DES-034, DES-035, DES-036, DES-037, DES-038,
DES-039, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099, REQ-100,
REQ-101, REQ-102, REQ-103, REQ-104, REQ-105, REQ-106, REQ-107, REQ-108,
REQ-109, REQ-110, REQ-111, REQ-112, REQ-113, REQ-114, REQ-115, REQ-116,
REQ-117, REQ-118, REQ-119, REQ-120, REQ-121, REQ-122, REQ-123, REQ-124,
REQ-125, REQ-126, REQ-127, REQ-128, REQ-129, REQ-130, REQ-131, REQ-132,
REQ-133
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shell_scripts.config import (
    DEFAULT_RUNTIME_CONFIG,
    get_config_path,
    load_runtime_config,
)
from shell_scripts.utils import print_error, print_info, print_success

## @var PROGRAM
#  @brief CLI program token used in inline usage help output.
PROGRAM = "shellscripts"

## @var ROOT_LABEL
#  @brief Visual-only root label rendered by `--print` and `--info` trees.
#  @details Omitted from every CLI path token; paths address children of the
#  root directly (REQ-133).
ROOT_LABEL = "shellScripts_Configuration"

## @var NAME_COLUMN_WIDTH
#  @brief Fixed option-name column width for tree rendering.
#  @details Leaves and groups are left-justified to this width so every `=`
#  value marker and `-` annotation marker starts at the same output column.
NAME_COLUMN_WIDTH = 24

## @var VALUE_COLUMN_WIDTH
#  @brief Minimum value column width before default/custom indicators.
#  @details Pads JSON-encoded leaf values so `(default)` and
#  `(custom | default: ...)` indicators align across consecutive lines.
VALUE_COLUMN_WIDTH = 34

## @var PATH_SEPARATOR
#  @brief Hierarchical path separator accepted by the configuration commands.
PATH_SEPARATOR = ":"

## @var APPEND_TOKENS
#  @brief Reserved array path tokens that append one validated item.
APPEND_TOKENS = ("append", "+")

## @var INSERT_TOKEN
#  @brief Reserved array path token introducing an insert index.
INSERT_TOKEN = "insert"

## @var INDEX_TOKEN_RE
#  @brief Pattern matching one optional-sign decimal integer path token.
INDEX_TOKEN_RE = re.compile(r"^-?[0-9]+$")

## @var SCALAR_KINDS
#  @brief Schema kinds whose JSON value is a scalar.
SCALAR_KINDS = ("string", "integer", "float", "boolean", "selection")

## @var _MISSING
#  @brief Sentinel for absent values during hierarchical path resolution.
_MISSING = object()


@dataclass(frozen=True)
class ChoiceSpec:
    """@brief One allowed value of a selection-type option.

    @details Immutable registry record pairing an accepted value token with
    its meaning, rendered in `Sel`/`Value` and `Value`/`Default`/`Meaning`
    tables by `--print` and `--info`.
    @satisfies REQ-097, REQ-108
    """

    value: str
    meaning: str


@dataclass(frozen=True)
class FieldSpec:
    """@brief One declared field of an object-row item schema.

    @details Describes one column of an `Array[Dictionary]` option consumed
    by row validation, cell coercion, cell reset, `--print` row tables, and
    the `--info` Item Schema table.
    @satisfies REQ-120, REQ-127, REQ-130
    """

    name: str
    kind: str
    description: str = ""
    required: bool = False
    has_default: bool = False
    default: Any = None


@dataclass(frozen=True)
class OptionSpec:
    """@brief Declarative metadata of one configurable leaf option.

    @details Binds one configuration key to its value kind, short
    description, optional allowed choices, input-example token, constraint
    label, array item kind, object-row item fields, and dynamic map value
    kind; drives `--info` rendering, `--print` value rendering, `--get`
    resolution, and `--set`/`--unset` coercion plus validation.
    @satisfies DES-032, DES-036, DES-038, REQ-096, REQ-097, REQ-098,
      REQ-101, REQ-102, REQ-107, REQ-110, REQ-118, REQ-119, REQ-120
    """

    kind: str
    description: str
    choices: tuple[ChoiceSpec, ...] = ()
    example: str = ""
    constraints: str = ""
    item_kind: str = "string"
    item_fields: tuple[FieldSpec, ...] = ()
    value_kind: str = "string"


@dataclass(frozen=True)
class GroupSpec:
    """@brief Declarative metadata of one configuration subtree group.

    @details Orders child schema nodes and carries the group description
    rendered by `--info` and the tree structure rendered by `--print`.
    @satisfies DES-032, REQ-095, REQ-107, REQ-117
    """

    description: str
    children: tuple[tuple[str, "OptionSpec | GroupSpec"], ...] = ()


@dataclass(frozen=True)
class TargetSpec:
    """@brief One resolved CLI path target.

    @details Encodes the schema node addressed by the static path prefix and
    the operation selected by the trailing dynamic tokens: `value` reads or
    replaces the whole option, `append`/`insert` add array rows, `row`
    targets one 0-based array row, `cell` targets one field of an object
    row, `key` targets one dynamic map key, `field` targets one field of a
    fixed object, and `group` addresses a whole schema subtree.
    @satisfies DES-038, REQ-122, REQ-124, REQ-125, REQ-126, REQ-127
    """

    path: str
    base_parts: tuple[str, ...]
    node: "OptionSpec | GroupSpec | None"
    op: str
    index: int | None = None
    token: str | None = None


## @var CONFIG_SCHEMA
#  @brief Declarative configuration schema registry.
#  @details Single source of truth for the configuration CLI surface; mirrors
#  the `DEFAULT_RUNTIME_CONFIG` tree and MUST be updated in the same change
#  whenever any configuration option, default, type, or allowed value changes
#  (DES-033). Parity with defaults is verified at import time by
#  `find_schema_mismatches` and enforced per command (DES-034).
#  @satisfies DES-032, DES-033, DES-034
CONFIG_SCHEMA: tuple[tuple[str, "OptionSpec | GroupSpec"], ...] = (
    (
        "management",
        GroupSpec(
            "Management commands for the shellscripts package.",
            (
                (
                    "upgrade",
                    OptionSpec(
                        "string",
                        "Linux command for upgrading from PyPI.",
                        constraints="shell command",
                        example='"uv tool install shellscripts"',
                    ),
                ),
                (
                    "upgrade_develop",
                    OptionSpec(
                        "string",
                        "Upgrade-command template from the GitHub tag "
                        "({tag} substituted at runtime).",
                        constraints="shell command template",
                        example=(
                            '"uv tool install shellscripts --from '
                            'git+https://github.com/Ogekuri/shellScripts.git@{tag}"'
                        ),
                    ),
                ),
                (
                    "uninstall",
                    OptionSpec(
                        "string",
                        "Linux command for uninstalling.",
                        constraints="shell command",
                        example='"uv tool uninstall shellscripts"',
                    ),
                ),
            ),
        ),
    ),
    (
        "dispatch",
        GroupSpec(
            "Command profiles for diff, edit, and view.",
            (
                (
                    "diff",
                    GroupSpec(
                        "File-diff commands by category.",
                        (
                            (
                                "categories",
                                OptionSpec(
                                    "map",
                                    "Category-to-command mapping for diff.",
                                    value_kind="list",
                                    example='{"code": ["bcompare"], '
                                            '"pdf": ["okular"]}',
                                ),
                            ),
                            (
                                "fallback",
                                OptionSpec(
                                    "list",
                                    "Fallback command vector for diff.",
                                    item_kind="string",
                                    example='["bcompare"]',
                                ),
                            ),
                        ),
                    ),
                ),
                (
                    "edit",
                    GroupSpec(
                        "File-edit commands by category.",
                        (
                            (
                                "categories",
                                OptionSpec(
                                    "map",
                                    "Category-to-command mapping for the "
                                    "editor.",
                                    value_kind="list",
                                    example='{"image": ["gimp"], '
                                            '"pdf": ["okular"]}',
                                ),
                            ),
                            (
                                "fallback",
                                OptionSpec(
                                    "list",
                                    "Fallback command vector for the editor.",
                                    item_kind="string",
                                    example='["gedit", "-w"]',
                                ),
                            ),
                        ),
                    ),
                ),
                (
                    "view",
                    GroupSpec(
                        "File-view commands by category.",
                        (
                            (
                                "categories",
                                OptionSpec(
                                    "map",
                                    "Category-to-command mapping for the "
                                    "viewer.",
                                    value_kind="list",
                                    example='{"image": ["sushi"], '
                                            '"pdf": ["sushi"]}',
                                ),
                            ),
                            (
                                "fallback",
                                OptionSpec(
                                    "list",
                                    "Fallback command vector for the viewer.",
                                    item_kind="string",
                                    example='["sushi"]',
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
    (
        "req",
        GroupSpec(
            "Parameters of the req command.",
            (
                (
                    "providers",
                    OptionSpec(
                        "list",
                        "Repeated providers passed to req with --provider.",
                        item_kind="string",
                        example='["codex:skills", "pi:prompts"]',
                    ),
                ),
                (
                    "static_checks",
                    OptionSpec(
                        "list",
                        "Repeated static checks passed to req with "
                        "--enable-static-check.",
                        item_kind="string",
                        example='["Python=Ruff"]',
                    ),
                ),
            ),
        ),
    ),
)


def _split_path(path: str) -> list[str] | None:
    """@brief Split one hierarchical configuration path.

    @details Splits by `PATH_SEPARATOR` and rejects empty paths and empty
    segments, returning `None` for malformed input so callers can emit inline
    usage help. Time complexity O(n) over path length.
    @param path {str} Raw path token, for example `management:upgrade`.
    @return {list[str]|None} Non-empty path segments or `None` when malformed.
    @satisfies REQ-099, REQ-109
    """

    if not path or not path.strip():
        return None
    parts = path.split(PATH_SEPARATOR)
    if any(not part for part in parts):
        return None
    return parts


def _walk_schema(parts: list[str]) -> "tuple[OptionSpec | GroupSpec | None, int]":
    """@brief Walk the schema registry along a path prefix.

    @details Consumes the longest prefix of `parts` that matches schema node
    names and returns the reached node plus the consumed depth; stops at the
    first unmatched segment so trailing tokens stay available for dynamic
    resolution. Time complexity O(n*m) over path depth and sibling count.
    @param parts {list[str]} Non-empty path segments.
    @return {tuple} `(node, depth)` where `node` is `None` when no segment
      matches.
    @satisfies DES-038
    """

    children = CONFIG_SCHEMA
    node: "OptionSpec | GroupSpec | None" = None
    depth = 0
    for part in parts:
        found: "OptionSpec | GroupSpec | None" = None
        for key, child in children:
            if key == part:
                found = child
                break
        if found is None:
            break
        node = found
        depth += 1
        children = found.children if isinstance(found, GroupSpec) else ()
    return node, depth


def _find_schema_node(parts: list[str]) -> "OptionSpec | GroupSpec | None":
    """@brief Resolve one full path against the schema registry.

    @details Returns the schema record only when every segment matches the
    registry, or `None` for unknown or non-configurable paths.
    Time complexity O(n*m) over path depth and sibling count.
    @param parts {list[str]} Non-empty path segments from `_split_path`.
    @return {OptionSpec|GroupSpec|None} Schema record or `None` when absent.
    @satisfies DES-032, REQ-100
    """

    node, depth = _walk_schema(parts)
    if node is None or depth != len(parts):
        return None
    return node


def _is_index_token(token: str) -> bool:
    """@brief Test whether one path token is a decimal integer index.

    @details Accepts an optional leading minus sign so negative indexes
    reach bounds checking and produce explicit out-of-bounds errors.
    Time complexity O(1).
    @param token {str} Path token candidate.
    @return {bool} `True` when the token parses as a decimal integer.
    @satisfies DES-038, REQ-122
    """

    return INDEX_TOKEN_RE.match(token) is not None


def _resolve_target(path: str) -> "tuple[TargetSpec | None, str | None]":
    """@brief Resolve one CLI path into a typed operation target.

    @details Splits the path, walks the schema for the static prefix, and
    classifies trailing tokens per option kind: array kinds accept
    `append`/`+`, `insert:<Idx>`, `<Idx>`, and `<Idx>:<Field>`; map kinds
    accept exactly one `<Key>`; object kinds accept exactly one `<Field>`;
    scalar kinds accept no trailing tokens. Time complexity O(n*m) over path
    depth and sibling count.
    @param path {str} Raw hierarchical path token.
    @return {tuple} `(TargetSpec, None)` on success or `(None, error_message)`
      for unknown or malformed paths.
    @satisfies DES-038, REQ-122, REQ-123, REQ-124, REQ-125, REQ-126,
      REQ-127, REQ-128
    """

    parts = _split_path(path)
    if parts is None:
        return None, f"Unknown configuration path: {path}."
    node, depth = _walk_schema(parts)
    if node is None or depth == 0:
        return None, f"Unknown configuration path: {path}."
    base_parts = tuple(parts[:depth])
    extra = parts[depth:]
    if isinstance(node, GroupSpec):
        if extra:
            return None, f"Unknown configuration path: {path}."
        return TargetSpec(path, base_parts, node, "group"), None
    kind = node.kind
    if not extra:
        return TargetSpec(path, base_parts, node, "value"), None
    if kind == "list":
        head = extra[0]
        if head in APPEND_TOKENS:
            if len(extra) != 1:
                return None, (
                    f"Invalid array path '{path}'. Append accepts no "
                    "additional tokens."
                )
            return TargetSpec(path, base_parts, node, "append"), None
        if head == INSERT_TOKEN:
            if len(extra) != 2 or not _is_index_token(extra[1]):
                return None, (
                    f"Invalid insert path '{path}'. Expected "
                    f"'{path}:insert:<Idx>' with an integer index."
                )
            return (
                TargetSpec(path, base_parts, node, "insert", int(extra[1])),
                None,
            )
        if _is_index_token(head):
            if len(extra) == 1:
                return (
                    TargetSpec(path, base_parts, node, "row", int(head)),
                    None,
                )
            if len(extra) == 2:
                return (
                    TargetSpec(
                        path, base_parts, node, "cell", int(head), extra[1]
                    ),
                    None,
                )
            return None, (
                f"Invalid array path '{path}'. Valid forms: <path>:append, "
                "<path>:+, <path>:insert:<Idx>, <path>:<Idx>, "
                "<path>:<Idx>:<Field>."
            )
        return None, (
            f"Invalid array path '{path}'. Valid forms: <path>:append, "
            "<path>:+, <path>:insert:<Idx>, <path>:<Idx>, "
            "<path>:<Idx>:<Field>."
        )
    if kind == "map":
        if len(extra) == 1:
            return TargetSpec(path, base_parts, node, "key", None, extra[0]), None
        return None, (
            f"Invalid map path '{path}'. Append exactly one ':<Key>' token."
        )
    if kind == "object":
        if len(extra) == 1:
            return (
                TargetSpec(path, base_parts, node, "field", None, extra[0]),
                None,
            )
        return None, (
            f"Invalid object path '{path}'. Append exactly one ':<Field>' "
            "token."
        )
    return None, f"Scalar option '{path}' accepts no extra path tokens."


def _resolve_value(container: Any, parts: list[str]) -> Any:
    """@brief Navigate a nested mapping by path segments.

    @details Returns `_MISSING` when any segment is absent or crosses a
    non-mapping value. Time complexity O(n) over path depth.
    @param container {Any} Nested mapping candidate, usually a config dict.
    @param parts {list[str]} Non-empty path segments.
    @return {Any} Resolved value or the `_MISSING` sentinel.
    @satisfies REQ-099
    """

    current = container
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _set_nested(container: dict[str, Any], parts: list[str], value: Any) -> None:
    """@brief Write one value into a nested mapping by path segments.

    @details Creates intermediate mappings for absent parents, replacing
    non-mapping parents with fresh mappings. Time complexity O(n) over depth.
    @param container {dict[str,Any]} Target mapping mutated in place.
    @param parts {list[str]} Non-empty path segments ending at the leaf key.
    @param value {Any} Coerced value to persist.
    @return {None} Mutates `container` in place.
    @satisfies REQ-101, REQ-103, DES-039
    """

    current = container
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def _pop_nested(container: dict[str, Any], parts: list[str]) -> Any:
    """@brief Remove one key from a nested mapping by path segments.

    @details Returns the removed value or `_MISSING` when any segment is
    absent or crosses a non-mapping value. Time complexity O(n) over depth.
    @param container {dict[str,Any]} Target mapping mutated in place.
    @param parts {list[str]} Non-empty path segments ending at the target key.
    @return {Any} Removed value or the `_MISSING` sentinel.
    @satisfies REQ-105, REQ-106
    """

    current = container
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            return _MISSING
        current = child
    if parts[-1] not in current:
        return _MISSING
    return current.pop(parts[-1])


def _iter_schema_leaf_paths(
    children: "tuple[tuple[str, OptionSpec | GroupSpec], ...]" = CONFIG_SCHEMA,
    prefix: tuple[str, ...] = (),
):
    """@brief Enumerate every schema leaf path.

    @details Depth-first recursion yielding tuples of path segments for every
    `OptionSpec` node. Time complexity O(n) over schema node count.
    @param children {tuple} Sibling nodes being expanded.
    @param prefix {tuple[str,...]} Parent path segments.
    @return {Iterator[tuple[str,...]]} Leaf path segment tuples.
    @satisfies DES-034
    """

    for key, node in children:
        path = prefix + (key,)
        if isinstance(node, GroupSpec):
            yield from _iter_schema_leaf_paths(node.children, path)
        else:
            yield path


def _iter_default_leaf_paths(
    node: dict[str, Any] = DEFAULT_RUNTIME_CONFIG,
    prefix: tuple[str, ...] = (),
):
    """@brief Enumerate every default configuration leaf path.

    @details Depth-first recursion yielding tuples of path segments for every
    non-mapping value, expanding nested mappings as intermediate groups.
    Time complexity O(n) over default node count.
    @param node {dict[str,Any]} Mapping being expanded.
    @param prefix {tuple[str,...]} Parent path segments.
    @return {Iterator[tuple[str,...]]} Leaf path segment tuples.
    @satisfies DES-034
    """

    for key, value in node.items():
        path = prefix + (key,)
        if isinstance(value, dict):
            yield from _iter_default_leaf_paths(value, path)
        else:
            yield path


def find_schema_mismatches() -> list[str]:
    """@brief Verify schema registry parity with configuration defaults.

    @details Fails when any default leaf is not covered by a schema leaf
    (equal path or schema-leaf prefix) or when any schema leaf path cannot be
    resolved inside `DEFAULT_RUNTIME_CONFIG`. Time complexity O(n*m) over
    default leaves and schema leaves.
    @return {list[str]} Human-readable divergence descriptions; empty when
      the registry and defaults are aligned.
    @satisfies DES-033, DES-034
    """

    schema_paths = [":".join(leaf) for leaf in _iter_schema_leaf_paths()]
    issues: list[str] = []
    for default_leaf in _iter_default_leaf_paths():
        joined = ":".join(default_leaf)
        covered = any(
            joined == schema_path or joined.startswith(schema_path + ":")
            for schema_path in schema_paths
        )
        if not covered:
            issues.append(f"default '{joined}' is not covered by CONFIG_SCHEMA")
    for schema_path in schema_paths:
        if _resolve_value(DEFAULT_RUNTIME_CONFIG, schema_path.split(":")) is _MISSING:
            issues.append(
                f"CONFIG_SCHEMA leaf '{schema_path}' is missing in "
                "DEFAULT_RUNTIME_CONFIG"
            )
    return issues


## @var _SCHEMA_MISMATCHES
#  @brief Import-time snapshot of schema/defaults divergence descriptions.
_SCHEMA_MISMATCHES = find_schema_mismatches()


def _fail_on_schema_mismatch() -> bool:
    """@brief Enforce schema parity before configuration command execution.

    @details Prints one bright-red error describing every divergence detected
    at import time and reports whether the calling command must abort.
    Time complexity O(n) over mismatch count.
    @return {bool} `True` when the caller must fail with return code `1`.
    @satisfies DES-034
    """

    if not _SCHEMA_MISMATCHES:
        return False
    print_error(
        "Configuration schema not aligned with defaults: "
        + "; ".join(_SCHEMA_MISMATCHES)
    )
    return True


def _render_box_table(
    headers: list[str], rows: list[list[str]], indent: str
) -> list[str]:
    """@brief Render one box-drawing table.

    @details Builds column widths from headers and rows, then emits top,
    header, separator, body, and bottom lines using `┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘ ─`
    and `│` glyphs, prefixing every line with `indent`. Time complexity
    O(n*m) over table cells.
    @param headers {list[str]} Column header cells.
    @param rows {list[list[str]]} Body rows with one cell per column.
    @param indent {str} Left padding applied to every rendered line.
    @return {list[str]} Fully rendered table lines.
    @satisfies REQ-097, REQ-108, REQ-118, REQ-119, REQ-120
    """

    widths = [
        max([len(header)] + [len(row[column]) for row in rows])
        for column, header in enumerate(headers)
    ]

    def _row(cells: list[str]) -> str:
        """@brief Render one padded table row line.

        @param cells {list[str]} Cell texts for the row.
        @return {str} Indented line framed by `│` glyphs.
        """

        body = "│".join(
            f" {cell.ljust(width)} " for cell, width in zip(cells, widths)
        )
        return f"{indent}│{body}│"

    top = f"{indent}┌" + "┬".join("─" * (width + 2) for width in widths) + "┐"
    separator = f"{indent}├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
    bottom = f"{indent}└" + "┴".join("─" * (width + 2) for width in widths) + "┘"
    lines = [top, _row(headers), separator]
    lines.extend(_row(row) for row in rows)
    lines.append(bottom)
    return lines


def _render_json(value: Any) -> str:
    """@brief Render one configuration value as compact JSON.

    @details Scalars, lists, and mappings serialize deterministically with
    sorted keys and no ASCII escaping. Time complexity O(n) over value size.
    @param value {Any} Configuration value to serialize.
    @return {str} Single-line JSON representation.
    @satisfies REQ-096, REQ-099
    """

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _render_default_value(parts: tuple[str, ...]) -> Any:
    """@brief Resolve one schema default value by path segments.

    @details Navigates `DEFAULT_RUNTIME_CONFIG` by the supplied tuple and
    returns `None` when the path is absent, so rendering always has a
    comparable default. Time complexity O(n) over path depth.
    @param parts {tuple[str,...]} Canonical path segments of one option.
    @return {Any} Declared default value or `None`.
    @satisfies REQ-096
    """

    value = _resolve_value(DEFAULT_RUNTIME_CONFIG, list(parts))
    return None if value is _MISSING else value


def _render_indicator(parts: tuple[str, ...], value: Any) -> str:
    """@brief Render the default or custom indicator for one leaf value.

    @details Emits `(default)` when the active value equals the schema
    default and `(custom | default: <Default_Value>)` otherwise.
    Time complexity O(1) plus default resolution.
    @param parts {tuple[str,...]} Canonical path segments of one option.
    @param value {Any} Active effective value of the option.
    @return {str} Indicator token without surrounding parentheses content
      markers.
    @satisfies REQ-096
    """

    default = _render_default_value(parts)
    if value == default:
        return "(default)"
    return f"(custom | default: {_render_json(default)})"


def _render_print_leaf(
    prefix: str,
    branch: str,
    node_prefix: str,
    key: str,
    node: OptionSpec,
    value: Any,
    lines: list[str],
    parts: tuple[str, ...],
) -> None:
    """@brief Render one `--print` leaf option block.

    @details Emits the leaf line with the `= <JSON>` value, the default or
    custom indicator, the selection action hint, and the collection summary
    headers; appends the selection `Sel`/`Value` table, map `Key`/`Value`
    table, primitive-array `Idx`/`Value` table, or object-array
    `Idx`-plus-field-columns table, and renders explicit empty-collection
    hints for zero-length collections. Time complexity O(n) over rendered
    collection size.
    @param prefix {str} Ancestor connector prefix for this level.
    @param branch {str} Branch connector (`├── ` or `└── `).
    @param node_prefix {str} Tree continuation prefix for child lines.
    @param key {str} Schema node name printed verbatim.
    @param node {OptionSpec} Schema record of the leaf.
    @param value {Any} Effective value of the leaf.
    @param lines {list[str]} Output accumulator mutated in place.
    @param parts {tuple[str,...]} Canonical path segments of the leaf.
    @return {None} Appends rendered lines to `lines`.
    @satisfies REQ-096, REQ-097, REQ-115, REQ-118, REQ-119, REQ-120,
      REQ-121, REQ-133
    """

    name = key.ljust(NAME_COLUMN_WIDTH)
    path = PATH_SEPARATOR.join(parts)
    indent = node_prefix + " " * (NAME_COLUMN_WIDTH + 4)
    if node.choices:
        active = value if isinstance(value, str) else None
        indicator = _render_indicator(parts, value)
        hint = f"{indicator[:-1]} | set: {path} <Value>)"
        lines.append(
            f"{prefix}{branch}{name} = "
            f"{_render_json(value).ljust(VALUE_COLUMN_WIDTH)} {hint}"
        )
        rows = [
            ["[*]" if choice.value == active else "[ ]", choice.value]
            for choice in node.choices
        ]
        lines.extend(_render_box_table(["Sel", "Value"], rows, indent))
        return
    if node.kind in ("map", "object"):
        if not isinstance(value, dict) or not value:
            lines.append(
                f"{prefix}{branch}{name} = (empty map — set key with: "
                f"--set {path}:<Key> <value>)"
            )
            return
        lines.append(
            f"{prefix}{branch}{name} = ({len(value)} entries | key target: "
            f"{path}:<Key>)"
        )
        rows = [
            [entry_key, _render_json(entry_value)]
            for entry_key, entry_value in sorted(value.items())
        ]
        lines.extend(_render_box_table(["Key", "Value"], rows, indent))
        return
    if node.kind == "list":
        if not isinstance(value, list) or not value:
            lines.append(
                f"{prefix}{branch}{name} = (empty list — add row with: "
                f"--set {path}:+ <value>)"
            )
            return
        if node.item_fields:
            fields = [field.name for field in node.item_fields]
            lines.append(
                f"{prefix}{branch}{name} = ({len(value)} rows | cell target: "
                f"{path}:<Idx>:<Field> | add: :+)"
            )
            rows = [
                [str(index)]
                + [
                    _render_json(row.get(field)) if isinstance(row, dict) else ""
                    for field in fields
                ]
                for index, row in enumerate(value)
            ]
            lines.extend(
                _render_box_table(["Idx"] + fields, rows, indent)
            )
            return
        lines.append(
            f"{prefix}{branch}{name} = ({len(value)} items | row target: "
            f"{path}:<Idx> | add: :+)"
        )
        rows = [
            [str(index), _render_json(item)]
            for index, item in enumerate(value)
        ]
        lines.extend(_render_box_table(["Idx", "Value"], rows, indent))
        return
    indicator = _render_indicator(parts, value)
    lines.append(
        f"{prefix}{branch}{name} = "
        f"{_render_json(value).ljust(VALUE_COLUMN_WIDTH)} {indicator}"
    )


def _render_print_children(
    prefix: str,
    children: "tuple[tuple[str, OptionSpec | GroupSpec], ...]",
    values: Any,
    lines: list[str],
    base_parts: tuple[str, ...] = (),
) -> None:
    """@brief Render one `--print` tree level.

    @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
    connectors, node names printed verbatim as CLI path tokens, and the
    `[Path: ...]` badge on every group; delegates leaf rendering to
    `_render_print_leaf`. Time complexity O(n) over subtree node count.
    @param prefix {str} Ancestor connector prefix for this level.
    @param children {tuple} Sibling schema nodes being rendered.
    @param values {Any} Effective configuration subtree for this level.
    @param lines {list[str]} Output accumulator mutated in place.
    @param base_parts {tuple[str,...]} Canonical path segments of this level.
    @return {None} Appends rendered lines to `lines`.
    @satisfies REQ-095, REQ-096, REQ-097, REQ-098, REQ-115, REQ-117,
      REQ-118, REQ-119, REQ-120, REQ-121, REQ-133
    """

    total = len(children)
    for index, (key, node) in enumerate(children):
        last = index == total - 1
        branch = "└── " if last else "├── "
        node_prefix = prefix + ("    " if last else "│   ")
        node_parts = base_parts + (key,)
        name = key.ljust(NAME_COLUMN_WIDTH)
        if isinstance(node, GroupSpec):
            path = PATH_SEPARATOR.join(node_parts)
            lines.append(f"{prefix}│")
            lines.append(f"{prefix}{branch}{name}- [Path: {path}]")
            child_values = (
                values.get(key) if isinstance(values, dict) else _MISSING
            )
            _render_print_children(
                node_prefix, node.children, child_values, lines, node_parts
            )
            continue
        value = (
            values.get(key, _MISSING) if isinstance(values, dict) else _MISSING
        )
        if value is _MISSING:
            value = None
        _render_print_leaf(
            prefix, branch, node_prefix, key, node, value, lines, node_parts
        )


def _plain_kind_label(kind: str) -> str:
    """@brief Render one capitalized schema kind label.

    @details Maps internal kind tokens to the capitalized labels used inside
    composite type labels. Time complexity O(1).
    @param kind {str} Internal schema kind token.
    @return {str} Capitalized kind label.
    @satisfies REQ-107
    """

    labels = {
        "string": "String",
        "integer": "Integer",
        "float": "Float",
        "boolean": "Boolean",
        "selection": "Selection",
    }
    return labels.get(kind, kind)


def _render_kind_label(node: OptionSpec) -> str:
    """@brief Render the composite `--info` type label of one option.

    @details Produces `[String]`, `[Integer]`, `[Float]`, `[Boolean]`,
    `[Selection]`, `[Array[<Item>]]`, `[Array[Dictionary]]`,
    `[Map[String, <Value>]]`, and `[Dictionary]` labels, appending the
    schema-declared constraint after a colon when declared.
    Time complexity O(1).
    @param node {OptionSpec} Schema record of the option.
    @return {str} Bracketed type label without the surrounding brackets
      content markers applied by the caller.
    @satisfies REQ-107, REQ-112, REQ-113
    """

    if node.kind in SCALAR_KINDS:
        label = _plain_kind_label(node.kind)
    elif node.kind == "list":
        label = (
            "Array[Dictionary]"
            if node.item_fields
            else f"Array[{_plain_kind_label(node.item_kind)}]"
        )
    elif node.kind == "map":
        value_label = (
            f"Array[{_plain_kind_label('string')}]"
            if node.value_kind == "list"
            else _plain_kind_label(node.value_kind)
        )
        label = f"Map[String, {value_label}]"
    else:
        label = "Dictionary"
    if node.constraints:
        return f"{label}: {node.constraints}"
    return label


def _first_default_collection_sample(node: OptionSpec, parts: tuple[str, ...]) -> tuple[str, str]:
    """@brief Derive one concrete copy-pasteable collection sample.

    @details Reads the schema default collection and returns the first list
    element JSON token or the first map key and JSON value token, falling
    back to placeholder tokens when the default collection is empty.
    Time complexity O(1) over the first entry.
    @param node {OptionSpec} Schema record of the collection option.
    @param parts {tuple[str,...]} Canonical path segments of the option.
    @return {tuple[str,str]} `(item_or_key_token, value_token)`.
    @satisfies REQ-110, REQ-113, REQ-133
    """

    default = _render_default_value(parts)
    if node.kind == "list" and isinstance(default, list):
        if default:
            return _render_json(default[0]), _render_json(default[0])
        return '"value"', '"value"'
    if node.kind == "map" and isinstance(default, dict) and default:
        first_key = sorted(default.keys())[0]
        return first_key, _render_json(default[first_key])
    return "<KEY>", "<value>"


def _render_info_leaf(
    prefix: str,
    branch: str,
    node_prefix: str,
    key: str,
    node: OptionSpec,
    lines: list[str],
    parts: tuple[str, ...],
) -> None:
    """@brief Render one `--info` leaf option block.

    @details Emits the `[<Type>] <description>` header line and the
    structured multi-line metadata: `Default` and `Set cmd` lines for
    scalars, the `Value`/`Default`/`Meaning` allowed-value table plus
    `Set cmd`/`Reset cmd` lines for selections, add/insert/update/delete/
    overwrite/clear command lines for arrays, set/remove/overwrite/clear
    command lines for maps, and full-overwrite/reset lines for objects.
    Time complexity O(n) over declared choices and item fields.
    @param prefix {str} Ancestor connector prefix for this level.
    @param branch {str} Branch connector (`├── ` or `└── `).
    @param node_prefix {str} Tree continuation prefix for child lines.
    @param key {str} Schema node name printed verbatim.
    @param node {OptionSpec} Schema record of the leaf.
    @param lines {list[str]} Output accumulator mutated in place.
    @param parts {tuple[str,...]} Canonical path segments of the leaf.
    @return {None} Appends rendered lines to `lines`.
    @satisfies REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113,
      REQ-117, REQ-133
    """

    name = key.ljust(NAME_COLUMN_WIDTH)
    path = PATH_SEPARATOR.join(parts)
    indent = node_prefix + " " * (NAME_COLUMN_WIDTH + 2)
    header = f"{prefix}{branch}{name}- [{_render_kind_label(node)}] "
    header += node.description
    lines.append(header)
    if node.choices:
        default = _render_default_value(parts)
        rows = [
            [
                choice.value,
                "Yes" if choice.value == default else "No",
                choice.meaning,
            ]
            for choice in node.choices
        ]
        lines.append(f"{indent}├── Allowed Values :")
        lines.extend(
            _render_box_table(
                ["Value", "Default", "Meaning"], rows, indent + "│   "
            )
        )
        set_example = node.example or _render_json(node.choices[0].value)
        lines.append(f"{indent}├── Set cmd   : --set {path} {set_example}")
        lines.append(f"{indent}└── Reset cmd : --unset {path}")
        return
    if node.kind == "list" and node.item_fields:
        rows = []
        for field in node.item_fields:
            if field.required:
                default_cell = "REQUIRED"
            elif field.has_default:
                default_cell = _render_json(field.default)
            else:
                default_cell = "optional"
            rows.append(
                [
                    field.name,
                    f"[{_plain_kind_label(field.kind)}]",
                    default_cell,
                    field.description,
                ]
            )
        lines.append(f"{indent}├── Item Schema    :")
        lines.extend(
            _render_box_table(
                ["Field", "Type", "Default", "Description & Example"],
                rows,
                indent + "│   ",
            )
        )
        template = _render_object_row_template(node)
        lines.append(
            f"{indent}├── Add new row    : --set {path}:+ '{template}' "
            "(or :append)"
        )
        lines.append(
            f"{indent}├── Insert row idx : --set {path}:insert:0 '{template}'"
        )
        lines.append(
            f"{indent}├── Update cell    : --set {path}:0:"
            f"{node.item_fields[0].name} {node.item_fields[0].description}"
        )
        lines.append(
            f"{indent}├── Reset cell     : --unset {path}:0:"
            f"{node.item_fields[0].name}"
        )
        lines.append(
            f"{indent}├── Replace row    : --set {path}:0 '{template}'"
        )
        lines.append(
            f"{indent}├── Delete row idx : --unset {path}:0 "
            "(auto re-indexes list)"
        )
        lines.append(
            f"{indent}├── Full overwrite : --set {path} '[{template}]'"
        )
        lines.append(f"{indent}└── Clear all rows : --unset {path}")
        return
    if node.kind == "list":
        sample, _ = _first_default_collection_sample(node, parts)
        lines.append(f"{indent}├── Add new row    : --set {path}:+ {sample} (or :append)")
        lines.append(f"{indent}├── Insert row idx : --set {path}:insert:0 {sample}")
        lines.append(f"{indent}├── Update row idx : --set {path}:0 {sample}")
        lines.append(
            f"{indent}├── Delete row idx : --unset {path}:0 "
            "(auto re-indexes list)"
        )
        lines.append(f"{indent}├── Full overwrite : --set {path} '{node.example}'")
        lines.append(f"{indent}└── Clear all rows : --unset {path}")
        return
    if node.kind == "map":
        sample_key, sample_value = _first_default_collection_sample(node, parts)
        lines.append(f"{indent}├── Set/Add key    : --set {path}:{sample_key} {sample_value}")
        lines.append(f"{indent}├── Remove key     : --unset {path}:{sample_key}")
        lines.append(f"{indent}├── Full overwrite : --set {path} '{node.example}'")
        lines.append(f"{indent}└── Clear map      : --unset {path}")
        return
    if node.kind == "object":
        lines.append(f"{indent}├── Full overwrite : --set {path} '{node.example}'")
        lines.append(f"{indent}└── Reset block    : --unset {path}")
        return
    default = _render_default_value(parts)
    lines.append(
        f"{indent}├── Default : {_render_json(default)} "
        f"(restored via: --unset {path})"
    )
    lines.append(f"{indent}└── Set cmd : --set {path} {node.example}")


def _render_object_row_template(node: OptionSpec) -> str:
    """@brief Build one ready-to-use JSON row template for an object array.

    @details Emits required fields as uppercase placeholder tokens and
    optional fields as their schema defaults, producing a complete
    copy-pasteable JSON object template. Time complexity O(n) over item
    fields.
    @param node {OptionSpec} Schema record of the `Array[Dictionary]` option.
    @return {str} Compact JSON object template token.
    @satisfies REQ-112, REQ-133
    """

    payload: dict[str, Any] = {}
    for field in node.item_fields:
        if field.required:
            payload[field.name] = field.name.upper()
        elif field.has_default:
            payload[field.name] = field.default
        else:
            payload[field.name] = None
    return _render_json(payload)


def _render_info_children(
    prefix: str,
    children: "tuple[tuple[str, OptionSpec | GroupSpec], ...]",
    lines: list[str],
    base_parts: tuple[str, ...] = (),
) -> None:
    """@brief Render one `--info` hierarchy level.

    @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
    connectors, node names printed verbatim as CLI path tokens, and the
    `[Path: ...]` badge on every group; delegates leaf rendering to
    `_render_info_leaf`. Time complexity O(n) over subtree node count.
    @param prefix {str} Ancestor connector prefix for this level.
    @param children {tuple} Sibling schema nodes being rendered.
    @param lines {list[str]} Output accumulator mutated in place.
    @param base_parts {tuple[str,...]} Canonical path segments of this level.
    @return {None} Appends rendered lines to `lines`.
    @satisfies REQ-107, REQ-108, REQ-110, REQ-111, REQ-112, REQ-113,
      REQ-117, REQ-133
    """

    total = len(children)
    for index, (key, node) in enumerate(children):
        last = index == total - 1
        branch = "└── " if last else "├── "
        node_prefix = prefix + ("    " if last else "│   ")
        node_parts = base_parts + (key,)
        name = key.ljust(NAME_COLUMN_WIDTH)
        if isinstance(node, GroupSpec):
            path = PATH_SEPARATOR.join(node_parts)
            lines.append(f"{prefix}│")
            lines.append(f"{prefix}{branch}{name}- {node.description} [Path: {path}]")
            _render_info_children(node_prefix, node.children, lines, node_parts)
            continue
        _render_info_leaf(
            prefix, branch, node_prefix, key, node, lines, node_parts
        )


def _atomic_write_text(target: Path, content: str) -> None:
    """@brief Write one text file atomically via a same-directory temporary.

    @details Creates the parent directory, writes `content` into a temporary
    file in the target directory, flushes and fsyncs the stream, then
    atomically renames the temporary onto the target so crashes never leave
    truncated or partial JSON content. The temporary file is removed when
    any step fails. Time complexity O(n) over content size.
    @param target {Path} Destination file path.
    @param content {str} Full file content to persist.
    @return {None} Applies the destination filesystem mutation.
    @throws {OSError} Propagated when directory creation, writing, flushing,
      or the atomic replacement fails.
    @satisfies DES-037, REQ-103, REQ-105
    """

    directory = target.parent
    directory.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary_path = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def _render_default_config_text() -> str:
    """@brief Render the system default configuration file content.

    @details Serializes `DEFAULT_RUNTIME_CONFIG` with sorted keys, two-space
    indentation, and a trailing newline for deterministic bootstrapped
    content. Time complexity O(n) over configuration size.
    @return {str} Canonical default configuration JSON text.
    @satisfies REQ-116
    """

    return (
        json.dumps(
            DEFAULT_RUNTIME_CONFIG, indent=2, sort_keys=True, ensure_ascii=False
        )
        + "\n"
    )


def _ensure_bootstrap() -> bool:
    """@brief Initialize the configuration file with defaults when missing.

    @details Creates the configuration parent directory and writes the
    default JSON payload when `config.json` does not exist, so every
    configuration command executes against an initialized file; existing
    files are left untouched. Time complexity O(n) over configuration size
    on the initialization path, O(1) otherwise.
    @return {bool} `True` when the configuration file exists or was
      initialized; `False` when initialization failed.
    @satisfies REQ-116
    """

    target = get_config_path()
    if target.exists():
        return True
    try:
        _atomic_write_text(target, _render_default_config_text())
    except OSError as err:
        print_error(f"Cannot initialize configuration file '{target}': {err}.")
        return False
    return True


def _load_overrides() -> "tuple[dict[str, Any] | None, str | None]":
    """@brief Load on-disk configuration overrides.

    @details Reads the canonical config file and returns its object payload;
    a missing file yields an empty mapping, while unreadable files, invalid
    JSON, and non-object roots yield an error message. Time complexity O(n)
    over file size.
    @return {tuple[dict|None, str|None]} `(payload, None)` on success or
      `(None, error_message)` on failure.
    @satisfies REQ-101, REQ-103, REQ-105
    """

    target = get_config_path()
    if not target.exists():
        return {}, None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except OSError as err:
        return None, f"Cannot read '{target}': {err}."
    except json.JSONDecodeError as err:
        return None, f"Invalid JSON in '{target}': {err}."
    if not isinstance(payload, dict):
        return None, f"File '{target}' must contain a JSON object."
    return payload, None


def _write_overrides(payload: dict[str, Any]) -> None:
    """@brief Persist configuration overrides to the canonical config file.

    @details Writes sorted-key, two-space-indented JSON with a trailing
    newline through the atomic same-directory temporary-file write.
    Time complexity O(n) over payload size.
    @param payload {dict[str,Any]} Full on-disk override mapping.
    @return {None} Applies destination filesystem mutation.
    @throws {OSError} Propagated when the atomic write fails.
    @satisfies DES-037, REQ-103, REQ-105
    """

    target = get_config_path()
    _atomic_write_text(
        target,
        f"{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)}\n",
    )


def _validate_scalar_kind(value: Any, kind: str, spec: OptionSpec) -> str | None:
    """@brief Validate one already-typed scalar against a schema kind.

    @details Enforces strict Python/JSON type separation: booleans are not
    integers, integers are not floats, strings are non-empty, and selection
    values must be declared choices when choices exist. Time complexity O(1).
    @param value {Any} Typed candidate value.
    @param kind {str} Schema kind token.
    @param spec {OptionSpec} Owning schema record providing choices.
    @return {str|None} `None` when valid; the error explanation otherwise.
    @satisfies REQ-101, REQ-102
    """

    if kind == "string":
        if isinstance(value, str) and value:
            return None
        return "expected a non-empty string"
    if kind == "integer":
        if isinstance(value, int) and not isinstance(value, bool):
            return None
        return "expected an integer"
    if kind == "float":
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        ):
            return None
        return "expected a finite number"
    if kind == "boolean":
        if isinstance(value, bool):
            return None
        return "expected a boolean"
    if kind == "selection":
        if not isinstance(value, str) or not value:
            return "expected a non-empty selection value"
        if spec.choices and value not in (
            choice.value for choice in spec.choices
        ):
            return "value is not a declared choice"
        return None
    return None


def _validate_array_payload(payload: Any, spec: OptionSpec) -> str | None:
    """@brief Validate one decoded array payload against its item schema.

    @details For object arrays validates every row as a dictionary whose
    present fields match the declared `FieldSpec` kinds and whose required
    fields are present; for primitive arrays validates every element against
    the declared item kind. Time complexity O(n) over array length.
    @param payload {Any} Decoded JSON array candidate.
    @param spec {OptionSpec} Schema record of the array option.
    @return {str|None} `None` when valid; the error explanation otherwise.
    @satisfies REQ-102, REQ-124, REQ-128
    """

    if not isinstance(payload, list):
        return "expected a JSON array"
    for index, item in enumerate(payload):
        if spec.item_fields:
            error = _validate_object_row(item, index, spec)
        else:
            error = _validate_scalar_kind(item, spec.item_kind, spec)
        if error:
            return f"invalid item at index {index}: {error}"
    return None


def _validate_object_row(item: Any, index: int, spec: OptionSpec) -> str | None:
    """@brief Validate one object-array row against its declared fields.

    @details Requires a dictionary, rejects undeclared keys when fields are
    declared, enforces required-field presence, and validates each present
    field kind. Time complexity O(n) over row field count.
    @param item {Any} Decoded row candidate.
    @param index {int} 0-based row position used in error messages.
    @param spec {OptionSpec} Schema record declaring `item_fields`.
    @return {str|None} `None` when valid; the error explanation otherwise.
    @satisfies REQ-102, REQ-124, REQ-128
    """

    if not isinstance(item, dict):
        return f"expected a JSON object row at index {index}"
    declared = {field.name for field in spec.item_fields}
    for key in item:
        if key not in declared:
            return f"undeclared field '{key}' in row {index}"
    for field in spec.item_fields:
        if field.name not in item:
            if field.required:
                return f"missing required field '{field.name}' in row {index}"
            continue
        error = _validate_scalar_kind(item[field.name], field.kind, spec)
        if error:
            return f"field '{field.name}' in row {index}: {error}"
    return None


def _validate_map_payload(payload: Any, spec: OptionSpec) -> str | None:
    """@brief Validate one decoded map payload against its value kind.

    @details Requires a JSON object with non-empty string keys and validates
    every value against the declared map value kind; `list` value kinds
    denote vectors of non-empty strings. Time complexity O(n) over entry
    count.
    @param payload {Any} Decoded JSON object candidate.
    @param spec {OptionSpec} Schema record of the map option.
    @return {str|None} `None` when valid; the error explanation otherwise.
    @satisfies REQ-102, REQ-127, REQ-128
    """

    if not isinstance(payload, dict):
        return "expected a JSON object"
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            return "map keys must be non-empty strings"
        if spec.value_kind == "list":
            error = _validate_string_vector(value)
        else:
            error = _validate_scalar_kind(value, spec.value_kind, spec)
        if error:
            return f"invalid value for key '{key}': {error}"
    return None


def _validate_string_vector(value: Any) -> str | None:
    """@brief Validate one vector of non-empty strings.

    @details Accepts only JSON arrays whose elements are non-empty strings,
    matching the runtime command-vector normalization contract.
    Time complexity O(n) over vector length.
    @param value {Any} Decoded JSON array candidate.
    @return {str|None} `None` when valid; the error explanation otherwise.
    @satisfies REQ-102, REQ-127
    """

    if isinstance(value, list) and all(
        isinstance(item, str) and item for item in value
    ):
        return None
    return "expected a JSON array of non-empty strings"


def _coerce_token(raw: str, kind: str, spec: OptionSpec) -> "tuple[bool, Any, str | None]":
    """@brief Coerce one raw CLI token into a strict schema-typed value.

    @detailss Maps `boolean` tokens to JSON booleans, `integer` tokens to
    JSON numbers, `float` tokens to finite JSON numbers, `selection` and
    `string` tokens to non-empty strings, and JSON-parses `list`, `map`,
    and `object` tokens before payload validation. Time complexity O(n) over
    token length.
    @param raw {str} Raw value token from the CLI.
    @param kind {str} Target schema kind token.
    @param spec {OptionSpec} Owning schema record providing choices, item
      kinds, and value kinds.
    @return {tuple[bool, Any, str|None]} `(ok, value, error)` triple.
    @satisfies REQ-101, REQ-102
    """

    if kind == "boolean":
        lowered = raw.lower()
        if lowered == "true":
            return True, True, None
        if lowered == "false":
            return True, False, None
        return False, None, "expected true or false"
    if kind == "integer":
        try:
            return True, int(raw), None
        except ValueError:
            return False, None, "expected an integer value"
    if kind == "float":
        try:
            parsed_float = float(raw)
        except ValueError:
            return False, None, "expected a numeric value"
        if not math.isfinite(parsed_float):
            return False, None, "expected a finite numeric value"
        return True, parsed_float, None
    if kind in ("list", "map", "object"):
        try:
            parsed_payload = json.loads(raw)
        except json.JSONDecodeError:
            return False, None, "expected a valid JSON value"
        if kind == "list":
            error = _validate_array_payload(parsed_payload, spec)
            if error:
                return False, None, error
            return True, parsed_payload, None
        if kind == "map":
            error = _validate_map_payload(parsed_payload, spec)
            if error:
                return False, None, error
            return True, parsed_payload, None
        if not isinstance(parsed_payload, dict):
            return False, None, "expected a JSON object"
        return True, parsed_payload, None
    if not raw.strip():
        return False, None, "expected a non-empty string"
    return True, raw, None


def _coerce_value(raw: str, spec: OptionSpec) -> "tuple[bool, Any, str | None]":
    """@brief Coerce one raw CLI token by the option schema kind.

    @details Thin adapter delegating to `_coerce_token` with the option's
    own kind. Time complexity O(n) over token length.
    @param raw {str} Raw value token from the CLI.
    @param spec {OptionSpec} Target option schema record.
    @return {tuple[bool, Any, str|None]} `(ok, value, error)` triple.
    @satisfies REQ-101, REQ-102
    """

    return _coerce_token(raw, spec.kind, spec)


def _ensure_choice_allowed(path: str, spec: OptionSpec, value: Any) -> str | None:
    """@brief Validate one value against declared selection choices.

    @details Returns an explanatory error listing every allowed choice when
    the value is not declared and choices exist. Time complexity O(n) over
    choice count.
    @param path {str} Raw CLI path used in the error message.
    @param spec {OptionSpec} Schema record providing choices.
    @param value {Any} Coerced candidate value.
    @return {str|None} `None` when allowed; the error explanation otherwise.
    @satisfies REQ-102
    """

    if not spec.choices:
        return None
    allowed = [choice.value for choice in spec.choices]
    if value in allowed:
        return None
    return (
        f"Disallowed value for {path}. Allowed values: "
        + ", ".join(allowed)
        + "."
    )


def _index_out_of_bounds_message(
    index: int, length: int, leaf_name: str, insert_mode: bool = False
) -> str:
    """@brief Build one explicit out-of-bounds index error message.

    @details States the valid index range and the `:append` alternative for
    row operations; insert operations state the valid insert-position range
    `0..length`. Time complexity O(1).
    @param index {int} Rejected 0-based index.
    @param length {int} Current array length.
    @param leaf_name {str} Schema leaf name used in the message.
    @param insert_mode {bool} Selects the insert-position wording.
    @return {str} Complete error message without severity decoration.
    @satisfies REQ-122, REQ-126, REQ-131
    """

    if insert_mode:
        return (
            f"Index {index} out of bounds. Valid insert positions for "
            f"{leaf_name} are 0..{length}."
        )
    return (
        f"Index {index} out of bounds. Valid indices for {leaf_name} are "
        f"0..{length - 1}. Use ':append' to add a new item."
    )


def _find_item_field(node: OptionSpec, name: str) -> "FieldSpec | None":
    """@brief Locate one declared item field by name.

    @details Performs a linear scan over the declared `item_fields` of an
    object-array schema record. Time complexity O(n) over field count.
    @param node {OptionSpec} Schema record of the `Array[Dictionary]` option.
    @param name {str} Field name token from the CLI path.
    @return {FieldSpec|None} Declared field record or `None` when undeclared.
    @satisfies REQ-127, REQ-130
    """

    for field in node.item_fields:
        if field.name == name:
            return field
    return None


def _coerce_array_item(
    raw: str, node: OptionSpec
) -> "tuple[bool, Any, str | None]":
    """@brief Coerce one raw CLI token as one array item.

    @details For object arrays JSON-parses the token and validates the row
    against the declared item fields; for primitive arrays coerces the token
    against the declared item kind. Time complexity O(n) over token length.
    @param raw {str} Raw item token from the CLI.
    @param node {OptionSpec} Schema record of the array option.
    @return {tuple[bool, Any, str|None]} `(ok, item, error)` triple.
    @satisfies REQ-124, REQ-125, REQ-126
    """

    if node.item_fields:
        try:
            parsed_row = json.loads(raw)
        except json.JSONDecodeError:
            return False, None, "expected a valid JSON object row"
        if not isinstance(parsed_row, dict):
            return False, None, "expected a JSON object row"
        error = _validate_object_row(parsed_row, -1, node)
        if error:
            return False, None, error.replace("row -1", "row")
        return True, parsed_row, None
    return _coerce_token(raw, node.item_kind, node)


def _overwrite_message_array(leaf_name: str, items: Any) -> str:
    """@brief Build the whole-array overwrite confirmation message.

    @details Reports the new item count and the covered 0-based index range;
    omits the range when the array is empty. Time complexity O(1).
    @param leaf_name {str} Schema leaf name used in the message.
    @param items {Any} Persisted replacement array.
    @return {str} Complete confirmation message.
    @satisfies REQ-128
    """

    count = len(items) if isinstance(items, list) else 0
    if count:
        return (
            f"Array {leaf_name} overwritten with {count} items "
            f"(indices 0..{count - 1})."
        )
    return f"Array {leaf_name} overwritten with 0 items."


def _append_message(leaf_name: str, item: Any, index: int) -> str:
    """@brief Build the append confirmation message with the assigned index.

    @details Object rows use the object wording; primitive items embed the
    JSON-encoded value. Time complexity O(n) over item size.
    @param leaf_name {str} Schema leaf name used in the message.
    @param item {Any} Validated appended item.
    @param index {int} Assigned 0-based index.
    @return {str} Complete confirmation message.
    @satisfies REQ-124
    """

    if isinstance(item, dict):
        return f"Object appended to {leaf_name} at index {index}."
    return f"Item {_render_json(item)} appended to {leaf_name} at index {index}."


def print_config_cli_help(command: str) -> None:
    """@brief Print command-specific inline usage help.

    @details Documents the `:` hierarchical path syntax, the array and map
    path tokens, accepted value formats, environment acquisition, and
    per-command examples for one of `--get`, `--set`, or `--unset`.
    Time complexity O(1).
    @param command {str} Command token requesting inline help.
    @return {None} Writes help text to stdout.
    @satisfies REQ-109, DES-038
    """

    if command == "--set":
        print(f"Usage: {PROGRAM} --set <path> <value>")
        print(
            "Sets one option or collection element, writing only the target "
            "key into the configuration file."
        )
        print("The path uses ':' as the hierarchical option separator.")
        print("Array and map operations use reserved path tokens:")
        print("  <path>:append | <path>:+    append one validated item")
        print("  <path>:insert:<Idx>         insert at 0-based Idx, shifting rows")
        print("  <path>:<Idx>                replace the row at 0-based Idx")
        print("  <path>:<Idx>:<Field>        update one field of an object row")
        print("  <path>:<Key>                add or update one dynamic map key")
        print(
            "Booleans: true/false; numbers: integer or float; arrays and "
            "maps: JSON."
        )
        print("A '$NAME' value is acquired from environment variable NAME.")
        print("Examples:")
        print(
            f'  {PROGRAM} --set management:upgrade '
            '"uv tool install shellscripts"'
        )
        print(f'  {PROGRAM} --set req:providers:+ "codex:skills"')
        print(f"  {PROGRAM} --set req:providers:insert:0 'claude:prompts'")
        print(f'  {PROGRAM} --set dispatch:diff:categories:code \'["bcompare"]\'')
        print(f"  {PROGRAM} --set req:providers $REQ_PROVIDERS")
        return
    if command == "--unset":
        print(f"Usage: {PROGRAM} --unset <path>")
        print(
            "Removes one override key, array row, map key, or row field, "
            "reactivating the default."
        )
        print("The path uses ':' as the hierarchical option separator.")
        print("Array and map removals use reserved path tokens:")
        print("  <path>:<Idx>          delete the row at 0-based Idx (auto re-index)")
        print("  <path>:<Idx>:<Field>  reset one row field to its default")
        print("  <path>:<Key>          remove one dynamic map key")
        print("  <path>                reset the whole option, array, or branch")
        print("Examples:")
        print(f"  {PROGRAM} --unset management:upgrade")
        print(f"  {PROGRAM} --unset req:providers:0")
        print(f"  {PROGRAM} --unset dispatch:diff:categories:code")
        print(f"  {PROGRAM} --unset dispatch:diff")
        return
    print(f"Usage: {PROGRAM} --get <path>")
    print("Reads one value from the effective configuration (defaults plus file).")
    print("The path uses ':' as the hierarchical option separator.")
    print("Array and map reads use path tokens:")
    print("  <path>:<Idx>          read the row at 0-based Idx")
    print("  <path>:<Idx>:<Field>  read one field of an object row")
    print("  <path>:<Key>          read one dynamic map key")
    print("Examples:")
    print(f"  {PROGRAM} --get management:upgrade")
    print(f"  {PROGRAM} --get req:providers:0")
    print(f"  {PROGRAM} --get dispatch:diff:categories:code")
    print(f"  {PROGRAM} --get dispatch:diff:categories")


def _resolve_subtree_node(
    path: str,
) -> "tuple[tuple[tuple[str, OptionSpec | GroupSpec], ...] | None, str | None]":
    """@brief Resolve one `--print`/`--info` sub-path into a render unit.

    @details Walks the schema by the full path and wraps the reached node as
    a single-child render tuple so subtree rendering reuses the standard
    level renderers. Time complexity O(n*m) over path depth and sibling
    count.
    @param path {str} Raw hierarchical sub-path token.
    @return {tuple} `(children, None)` on success where `children` is the
      one-entry render tuple, or `(None, error_message)` on failure.
    @satisfies REQ-095, REQ-107
    """

    parts = _split_path(path)
    if parts is None:
        return None, f"Unknown configuration path: {path}."
    node = _find_schema_node(parts)
    if node is None:
        return None, f"Unknown configuration path: {path}."
    return ((parts[-1], node),), None


def do_print_raw() -> int:
    """@brief Print the on-disk configuration file verbatim.

    @details Enforces schema registry parity with `DEFAULT_RUNTIME_CONFIG`
    before emitting output (DES-034), bootstraps the missing configuration
    file (REQ-116), then emits the raw bytes of the canonical config file
    without parsing, or a bright-red error naming the path when the file is
    unreadable. Time complexity O(n) over file size.
    @return {int} `0` on success; `1` on schema divergence or when the file
      is unreadable.
    @satisfies DES-032, DES-034, REQ-094, REQ-098, REQ-114, REQ-116,
      REQ-132
    """

    if _fail_on_schema_mismatch():
        return 1
    if not _ensure_bootstrap():
        return 1
    target = get_config_path()
    try:
        content = target.read_text(encoding="utf-8")
    except OSError as err:
        print_error(f"Cannot read '{target}': {err}.")
        return 1
    print(content, end="")
    return 0


def do_print(path: str | None = None) -> int:
    """@brief Render the effective configuration as an options tree.

    @details Bootstraps the missing configuration file, deep-merges on-disk
    overrides onto hardcoded defaults, then renders the schema-ordered tree
    with branch connectors, `[Path: ...]` badges, `= <JSON>` scalar leaves
    carrying default or custom indicators, selection tables with action
    hints, and collection summary tables; an optional `:`-separated sub-path
    restricts rendering to that subtree or leaf. The root annotation reports
    `ACTIVE` when the config file exists and `DEFAULT` otherwise.
    Time complexity O(n) over configuration size.
    @param path {str|None} Optional sub-path restricting the rendered
      subtree, for example `dispatch:diff`.
    @return {int} `0` on success; `1` on schema divergence or unknown paths.
    @satisfies DES-034, REQ-095, REQ-096, REQ-097, REQ-098, REQ-115,
      REQ-116, REQ-117, REQ-118, REQ-119, REQ-120, REQ-121, REQ-132,
      REQ-133
    """

    if _fail_on_schema_mismatch():
        return 1
    if not _ensure_bootstrap():
        return 1
    effective = load_runtime_config()
    state = "ACTIVE" if get_config_path().exists() else "DEFAULT"
    lines = [f"{ROOT_LABEL} - [State: {state}]"]
    if path is None:
        _render_print_children("", CONFIG_SCHEMA, effective, lines)
    else:
        unit, error = _resolve_subtree_node(path)
        if unit is None:
            print_error(error or f"Unknown configuration path: {path}.")
            return 1
        parts = _split_path(path) or []
        parent_parts = tuple(parts[:-1])
        ((name, node),) = unit
        if isinstance(node, GroupSpec):
            value = _resolve_value(effective, parts)
            _render_print_children(
                "", unit, value if isinstance(value, dict) else {}, lines, parent_parts
            )
        else:
            leaf_value = _resolve_value(effective, parts)
            if leaf_value is _MISSING:
                leaf_value = None
            _render_print_children(
                "", unit, {name: leaf_value}, lines, parent_parts
            )
    print("\n".join(lines))
    return 0


def do_info(path: str | None = None) -> int:
    """@brief Render the configurable parameter hierarchy with descriptions.

    @details Emits the schema-ordered tree with per-group descriptions and
    `[Path: ...]` badges, per-option type labels and short descriptions,
    `Default` and full-path `Set cmd` lines for scalars,
    `Value`/`Default`/`Meaning` allowed-value tables with `Set cmd` and
    `Reset cmd` lines for selections, add/insert/update/delete/overwrite/
    clear command lines for arrays, set/remove/overwrite/clear command lines
    for maps, and full-overwrite/reset lines for objects; an optional
    `:`-separated sub-path restricts rendering to that subtree or leaf.
    Time complexity O(n) over schema node count.
    @param path {str|None} Optional sub-path restricting the rendered
      documentation subtree, for example `req`.
    @return {int} `0` on success; `1` on schema divergence or unknown paths.
    @satisfies DES-034, DES-036, REQ-107, REQ-108, REQ-110, REQ-111,
      REQ-112, REQ-113, REQ-116, REQ-117, REQ-132, REQ-133
    """

    if _fail_on_schema_mismatch():
        return 1
    if not _ensure_bootstrap():
        return 1
    lines = [f"{ROOT_LABEL} - Root of the {PROGRAM} settings."]
    if path is None:
        _render_info_children("", CONFIG_SCHEMA, lines)
    else:
        unit, error = _resolve_subtree_node(path)
        if unit is None:
            print_error(error or f"Unknown configuration path: {path}.")
            return 1
        parts = _split_path(path) or []
        _render_info_children("", unit, lines, tuple(parts[:-1]))
    print("\n".join(lines))
    return 0


def do_get(path: str | None) -> int:
    """@brief Read one configuration value by hierarchical path.

    @details Bootstraps the missing configuration file, resolves the
    `:`-separated path against the schema registry and the effective
    configuration, supports array rows by 0-based index, object-row cells by
    field name, and dynamic map keys by key token, prints scalars as
    clean single-line JSON and object or array subtrees as indented JSON,
    and fails with explicit stderr errors for unknown paths, out-of-bounds
    indexes, and missing keys or fields. Time complexity O(n) over subtree
    size.
    @param path {str|None} Hierarchical path token, for example
      `management:upgrade` or `req:providers:0`.
    @return {int} `0` on success; `1` for missing arguments, unknown paths,
      out-of-bounds indexes, or absent values, keys, or fields.
    @satisfies DES-034, DES-038, REQ-098, REQ-099, REQ-100, REQ-109,
      REQ-116, REQ-122, REQ-123, REQ-131, REQ-132
    """

    if _fail_on_schema_mismatch():
        return 1
    if not _ensure_bootstrap():
        return 1
    parts = _split_path(path or "")
    if parts is None:
        print_config_cli_help("--get")
        return 1
    target, error = _resolve_target(path or "")
    if target is None:
        print_error(error or f"Unknown configuration path: {path}.")
        return 1
    effective = load_runtime_config()
    base_value = _resolve_value(effective, list(target.base_parts))
    if base_value is _MISSING:
        print_error(f"Parameter not found in configuration: {path}.")
        return 1
    leaf_name = target.base_parts[-1]
    out_value: Any
    if target.op in ("group", "value"):
        out_value = base_value
    elif target.op == "row":
        if not isinstance(base_value, list):
            print_error(f"Configuration value at {path} is not an array.")
            return 1
        index = target.index or 0
        if index < 0 or index >= len(base_value):
            print_error(
                _index_out_of_bounds_message(index, len(base_value), leaf_name)
            )
            return 1
        out_value = base_value[index]
    elif target.op == "cell":
        if not isinstance(base_value, list):
            print_error(f"Configuration value at {path} is not an array.")
            return 1
        index = target.index or 0
        if index < 0 or index >= len(base_value):
            print_error(
                _index_out_of_bounds_message(index, len(base_value), leaf_name)
            )
            return 1
        row = base_value[index]
        token = target.token or ""
        if not isinstance(row, dict) or token not in row:
            print_error(f"Field '{token}' not found in row {index} of {path}.")
            return 1
        out_value = row[token]
    elif target.op == "key":
        if not isinstance(base_value, dict):
            print_error(f"Configuration value at {path} is not an object.")
            return 1
        token = target.token or ""
        if token not in base_value:
            print_error(f"Map key '{token}' not found under {path}.")
            return 1
        out_value = base_value[token]
    else:
        if not isinstance(base_value, dict):
            print_error(f"Configuration value at {path} is not an object.")
            return 1
        token = target.token or ""
        if token not in base_value:
            print_error(f"Field '{token}' not found in {path}.")
            return 1
        out_value = base_value[token]
    if isinstance(out_value, (dict, list)):
        print(
            json.dumps(out_value, indent=2, ensure_ascii=False, sort_keys=True)
        )
        return 0
    print(json.dumps(out_value, ensure_ascii=False))
    return 0


def do_set(path: str | None, value: str | None) -> int:
    """@brief Set one configuration value by hierarchical path.

    @details Bootstraps the missing configuration file, resolves the target
    operation from the path tokens, resolves `$NAME` tokens from the
    environment, coerces the value to the strict schema type, validates
    schema constraints, applies the mutation to the effective configuration
    (defaults merged with overrides), persists the resulting collection or
    scalar as one override value through the atomic write, and prints an
    operation-specific confirmation. Time complexity O(n) over configuration
    size.
    @param path {str|None} Hierarchical path token optionally ending with
      array or map operation tokens.
    @param value {str|None} Raw value token or `$NAME` environment token.
    @return {int} `0` on success; `1` for missing arguments, unknown paths,
      invalid values, disallowed choices, out-of-bounds indexes, undefined
      environment variables, or unreadable config files.
    @satisfies DES-034, DES-037, DES-038, DES-039, REQ-101, REQ-102,
      REQ-103, REQ-104, REQ-109, REQ-116, REQ-124, REQ-125, REQ-126,
      REQ-127, REQ-128, REQ-131, REQ-132
    """

    if _fail_on_schema_mismatch():
        return 1
    if not _ensure_bootstrap():
        return 1
    if _split_path(path or "") is None or value is None:
        print_config_cli_help("--set")
        return 1
    target, error = _resolve_target(path or "")
    if target is None:
        print_error(error or f"Unknown configuration path: {path}.")
        return 1
    if target.op == "group":
        print_error(f"Cannot set a configuration group: {path}.")
        return 1
    raw = value
    from_environment = False
    if raw.startswith("$") and len(raw) > 1:
        env_name = raw[1:]
        if env_name not in os.environ:
            print_error(f"Environment variable not defined: {env_name}.")
            return 1
        raw = os.environ[env_name]
        from_environment = True
    node = target.node
    assert isinstance(node, OptionSpec)
    effective = load_runtime_config()
    base_value = _resolve_value(effective, list(target.base_parts))
    leaf_name = target.base_parts[-1]
    new_value: Any
    message: str
    if target.op == "value":
        ok, coerced, coerce_error = _coerce_value(raw, node)
        if not ok:
            print_error(
                f"Invalid value for {path} [{node.kind}]: {coerce_error}."
            )
            return 1
        choice_error = _ensure_choice_allowed(path or "", node, coerced)
        if choice_error:
            print_error(choice_error)
            return 1
        new_value = coerced
        if node.kind == "list":
            message = _overwrite_message_array(leaf_name, coerced)
        elif node.kind == "map":
            message = f"Map {leaf_name} overwritten with {len(coerced)} entries."
        else:
            message = "Value saved successfully."
    elif target.op in ("append", "insert", "row", "cell"):
        if not isinstance(base_value, list):
            print_error(f"Configuration value at {path} is not an array.")
            return 1
        working_list = list(base_value)
        if target.op == "append":
            ok, coerced, coerce_error = _coerce_array_item(raw, node)
            if not ok:
                print_error(
                    f"Invalid value for {path} [{node.kind}]: {coerce_error}."
                )
                return 1
            working_list.append(coerced)
            new_value = working_list
            message = _append_message(leaf_name, coerced, len(working_list) - 1)
        elif target.op == "insert":
            index = target.index or 0
            if index < 0 or index > len(working_list):
                print_error(
                    _index_out_of_bounds_message(
                        index, len(working_list), leaf_name, insert_mode=True
                    )
                )
                return 1
            ok, coerced, coerce_error = _coerce_array_item(raw, node)
            if not ok:
                print_error(
                    f"Invalid value for {path} [{node.kind}]: {coerce_error}."
                )
                return 1
            working_list.insert(index, coerced)
            new_value = working_list
            message = (
                f"Item {_render_json(coerced)} inserted at index {index}. "
                "Subsequent items shifted."
            )
        elif target.op == "row":
            index = target.index or 0
            if index < 0 or index >= len(working_list):
                print_error(
                    _index_out_of_bounds_message(
                        index, len(working_list), leaf_name
                    )
                )
                return 1
            ok, coerced, coerce_error = _coerce_array_item(raw, node)
            if not ok:
                print_error(
                    f"Invalid value for {path} [{node.kind}]: {coerce_error}."
                )
                return 1
            working_list[index] = coerced
            new_value = working_list
            message = f"Row at index {index} updated successfully."
        else:
            index = target.index or 0
            if index < 0 or index >= len(working_list):
                print_error(
                    _index_out_of_bounds_message(
                        index, len(working_list), leaf_name
                    )
                )
                return 1
            row = working_list[index]
            if not isinstance(row, dict):
                print_error(
                    f"Row at index {index} of {path} is not an object; use "
                    f"'{path}:{index}' to replace the whole row."
                )
                return 1
            token = target.token or ""
            field = _find_item_field(node, token)
            if field is None:
                print_error(
                    f"Field '{token}' is not declared in the item schema of "
                    f"{path}."
                )
                return 1
            ok, coerced, coerce_error = _coerce_token(raw, field.kind, node)
            if not ok:
                print_error(
                    f"Invalid value for {path} [{field.kind}]: {coerce_error}."
                )
                return 1
            choice_error = _ensure_choice_allowed(path or "", node, coerced)
            if choice_error:
                print_error(choice_error)
                return 1
            updated_row = dict(row)
            updated_row[token] = coerced
            working_list[index] = updated_row
            new_value = working_list
            message = (
                f"Property '{token}' at index {index} updated to "
                f"{_render_json(coerced)}."
            )
    else:
        if not isinstance(base_value, dict):
            print_error(f"Configuration value at {path} is not an object.")
            return 1
        token = target.token or ""
        ok, coerced, coerce_error = _coerce_token(raw, node.value_kind, node)
        if not ok:
            print_error(
                f"Invalid value for {path} [{node.value_kind}]: {coerce_error}."
            )
            return 1
        working_map = dict(base_value)
        working_map[token] = coerced
        new_value = working_map
        message = f"Key '{token}' saved under {path}."
    overrides, load_error = _load_overrides()
    if overrides is None:
        print_error(load_error)
        return 1
    _set_nested(overrides, list(target.base_parts), new_value)
    try:
        _write_overrides(overrides)
    except OSError as err:
        print_error(f"Cannot write '{get_config_path()}': {err}.")
        return 1
    if from_environment:
        print_success("Value acquired from environment and saved successfully.")
    print_success(message)
    return 0


def do_unset(path: str | None) -> int:
    """@brief Remove one configuration override by hierarchical path.

    @details Bootstraps the missing configuration file, resolves the target
    operation from the path tokens, removes the override key (leaf or
    subtree), deletes one array row with immediate contiguous re-indexing,
    resets one object-row field to its declared default or removes the
    undeclared key, removes one dynamic map key, persists atomically, and
    prints the operation-specific confirmation. Time complexity O(n) over
    configuration size.
    @param path {str|None} Hierarchical path token optionally ending with
      array or map removal tokens.
    @return {int} `0` on success; `1` for missing arguments, unknown paths,
      out-of-bounds indexes, absent overrides, keys, or fields, or unreadable
      config files.
    @satisfies DES-034, DES-037, DES-038, DES-039, REQ-105, REQ-106,
      REQ-109, REQ-116, REQ-129, REQ-130, REQ-131, REQ-132
    """

    if _fail_on_schema_mismatch():
        return 1
    if not _ensure_bootstrap():
        return 1
    if _split_path(path or "") is None:
        print_config_cli_help("--unset")
        return 1
    target, error = _resolve_target(path or "")
    if target is None:
        print_error(error or f"Unknown configuration path: {path}.")
        return 1
    effective = load_runtime_config()
    base_value = _resolve_value(effective, list(target.base_parts))
    if base_value is _MISSING:
        print_error(f"No parameter to remove for: {path}.")
        return 1
    leaf_name = target.base_parts[-1]
    message: str
    if target.op in ("group", "value"):
        overrides, load_error = _load_overrides()
        if overrides is None:
            print_error(load_error)
            return 1
        removed = _pop_nested(overrides, list(target.base_parts))
        if removed is _MISSING:
            print_error(f"No parameter to remove for: {path}.")
            return 1
        try:
            _write_overrides(overrides)
        except OSError as err:
            print_error(f"Cannot write '{get_config_path()}': {err}.")
            return 1
        if isinstance(removed, dict):
            print(f"WARNING: Removed all parameters for {path}.")
        else:
            print_info(f"Parameter removed and default restored: {path}.")
        return 0
    if target.op == "key":
        if not isinstance(base_value, dict):
            print_error(f"Configuration value at {path} is not an object.")
            return 1
        token = target.token or ""
        if token not in base_value:
            print_error(f"Map key '{token}' not found under {path}.")
            return 1
        working_map = {k: v for k, v in base_value.items() if k != token}
        new_value: Any = working_map
        message = f"Key '{token}' removed from {path}."
    elif target.op == "row":
        if not isinstance(base_value, list):
            print_error(f"Configuration value at {path} is not an array.")
            return 1
        index = target.index or 0
        if index < 0 or index >= len(base_value):
            print_error(
                _index_out_of_bounds_message(index, len(base_value), leaf_name)
            )
            return 1
        working_list = list(base_value)
        del working_list[index]
        new_value = working_list
        remaining = len(working_list)
        if remaining:
            message = (
                f"Item at index {index} removed. Array re-indexed "
                f"({remaining} items remaining, indices 0..{remaining - 1})."
            )
        else:
            message = f"Item at index {index} removed. Array re-indexed (0 items remaining)."
    else:
        if not isinstance(base_value, list):
            print_error(f"Configuration value at {path} is not an array.")
            return 1
        index = target.index or 0
        if index < 0 or index >= len(base_value):
            print_error(
                _index_out_of_bounds_message(index, len(base_value), leaf_name)
            )
            return 1
        row = base_value[index]
        token = target.token or ""
        if not isinstance(row, dict) or token not in row:
            print_error(f"Field '{token}' not found in row {index} of {path}.")
            return 1
        node = target.node
        assert isinstance(node, OptionSpec)
        updated_row = dict(row)
        field = _find_item_field(node, token)
        if field is not None and field.has_default:
            updated_row[token] = field.default
        else:
            del updated_row[token]
        working_list = list(base_value)
        working_list[index] = updated_row
        new_value = working_list
        message = f"Property '{token}' at index {index} restored to default."
    overrides, load_error = _load_overrides()
    if overrides is None:
        print_error(load_error)
        return 1
    _set_nested(overrides, list(target.base_parts), new_value)
    try:
        _write_overrides(overrides)
    except OSError as err:
        print_error(f"Cannot write '{get_config_path()}': {err}.")
        return 1
    print_success(message)
    return 0


__all__ = [
    "CONFIG_SCHEMA",
    "ChoiceSpec",
    "FieldSpec",
    "GroupSpec",
    "OptionSpec",
    "TargetSpec",
    "do_get",
    "do_info",
    "do_print",
    "do_print_raw",
    "do_set",
    "do_unset",
    "find_schema_mismatches",
    "print_config_cli_help",
]
