#!/usr/bin/env python3
"""@brief Schema-driven command-line configuration manager.

@details Implements the management flags `--print-raw`, `--print`, `--params`,
`--get`, `--set`, and `--unset` over the canonical runtime configuration file
`$HOME/.config/shellScripts/config.json`. All rendering, path resolution, and
validation is derived from the declarative `CONFIG_SCHEMA` registry that MUST
mirror `DEFAULT_RUNTIME_CONFIG` (DES-032, DES-033); divergence fails every
configuration command at dispatch time (DES-034). Existing configuration
load, merge, normalization, and accessor logic is not modified (DES-035).
@satisfies DES-032, DES-033, DES-034, DES-035, REQ-094, REQ-095, REQ-096,
REQ-097, REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-103, REQ-104,
REQ-105, REQ-106, REQ-107, REQ-108, REQ-109
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
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
#  @brief Root node label rendered by `--print` and `--params` trees.
ROOT_LABEL = "Configurazione_shellScripts"

## @var NAME_COLUMN_WIDTH
#  @brief Fixed option-name column width for tree rendering.
#  @details Leaves and groups are left-justified to this width so every `=`
#  value marker and `-` annotation marker starts at the same output column.
NAME_COLUMN_WIDTH = 24

## @var PATH_SEPARATOR
#  @brief Hierarchical path separator accepted by `--get`/`--set`/`--unset`.
PATH_SEPARATOR = ":"

## @var MASKED_SECRET
#  @brief Mask rendered in place of secret option values.
MASKED_SECRET = "********"

## @var KIND_LABELS
#  @brief Schema kind to `--params` type label mapping.
#  @details Keys are OptionSpec kind tokens; values are labels rendered as
#  `[<label>]` prefixes in `--params` option descriptions.
KIND_LABELS = {
    "stringa": "Stringa",
    "intero": "Intero",
    "booleano": "Booleano",
    "selezione": "Selezione",
    "elenco": "Elenco",
    "oggetto": "Oggetto",
}

## @var _MISSING
#  @brief Sentinel for absent values during hierarchical path resolution.
_MISSING = object()


@dataclass(frozen=True)
class ChoiceSpec:
    """@brief One allowed value of a selection-type option.

    @details Immutable registry record pairing an accepted value token with
    its meaning, rendered in `Sel`/`Valore` and `Valore`/`Significato`
    tables by `--print` and `--params`.
    @satisfies REQ-097, REQ-108
    """

    value: str
    meaning: str


@dataclass(frozen=True)
class OptionSpec:
    """@brief Declarative metadata of one configurable leaf option.

    @details Binds one configuration key to its value kind, short
    description, optional allowed choices, and secret flag; drives `--params`
    rendering, `--print` value rendering, `--get` masking, and `--set`
    coercion plus choice validation.
    @satisfies DES-032, REQ-096, REQ-097, REQ-098, REQ-101, REQ-102, REQ-107
    """

    kind: str
    description: str
    choices: tuple[ChoiceSpec, ...] = ()
    secret: bool = False


@dataclass(frozen=True)
class GroupSpec:
    """@brief Declarative metadata of one configuration subtree group.

    @details Orders child schema nodes and carries the group description
    rendered by `--params` and the tree structure rendered by `--print`.
    @satisfies DES-032, REQ-095, REQ-107
    """

    description: str
    children: tuple[tuple[str, "OptionSpec | GroupSpec"], ...] = ()


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
            "Comandi di gestione del pacchetto shellscripts.",
            (
                (
                    "upgrade",
                    OptionSpec(
                        "stringa",
                        "Comando Linux per l'aggiornamento da PyPI.",
                    ),
                ),
                (
                    "upgrade_develop",
                    OptionSpec(
                        "stringa",
                        "Template del comando di upgrade dal tag GitHub "
                        "({tag} sostituito a runtime).",
                    ),
                ),
                (
                    "uninstall",
                    OptionSpec(
                        "stringa",
                        "Comando Linux per la disinstallazione.",
                    ),
                ),
            ),
        ),
    ),
    (
        "dispatch",
        GroupSpec(
            "Profili dei comandi per diff, edit e view.",
            (
                (
                    "diff",
                    GroupSpec(
                        "Comandi per il confronto di file per categoria.",
                        (
                            (
                                "categories",
                                OptionSpec(
                                    "oggetto",
                                    "Mappatura categoria-comando per il diff.",
                                ),
                            ),
                            (
                                "fallback",
                                OptionSpec(
                                    "elenco",
                                    "Vettore comando di fallback per il diff.",
                                ),
                            ),
                        ),
                    ),
                ),
                (
                    "edit",
                    GroupSpec(
                        "Comandi per la modifica di file per categoria.",
                        (
                            (
                                "categories",
                                OptionSpec(
                                    "oggetto",
                                    "Mappatura categoria-comando per l'editor.",
                                ),
                            ),
                            (
                                "fallback",
                                OptionSpec(
                                    "elenco",
                                    "Vettore comando di fallback per l'editor.",
                                ),
                            ),
                        ),
                    ),
                ),
                (
                    "view",
                    GroupSpec(
                        "Comandi per la visualizzazione di file per categoria.",
                        (
                            (
                                "categories",
                                OptionSpec(
                                    "oggetto",
                                    "Mappatura categoria-comando per il viewer.",
                                ),
                            ),
                            (
                                "fallback",
                                OptionSpec(
                                    "elenco",
                                    "Vettore comando di fallback per il viewer.",
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
            "Parametri del comando req.",
            (
                (
                    "providers",
                    OptionSpec(
                        "elenco",
                        "Provider ripetuti passati a req con --provider.",
                    ),
                ),
                (
                    "static_checks",
                    OptionSpec(
                        "elenco",
                        "Controlli statici ripetuti passati a req con "
                        "--enable-static-check.",
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


def _find_schema_node(parts: list[str]) -> "OptionSpec | GroupSpec | None":
    """@brief Resolve one path against the schema registry.

    @details Walks `CONFIG_SCHEMA` by segments and returns the matching leaf
    or group record, or `None` for unknown or non-configurable paths.
    Time complexity O(n*m) over path depth and sibling count.
    @param parts {list[str]} Non-empty path segments from `_split_path`.
    @return {OptionSpec|GroupSpec|None} Schema record or `None` when absent.
    @satisfies DES-032, REQ-100
    """

    children = CONFIG_SCHEMA
    node: "OptionSpec | GroupSpec | None" = None
    for part in parts:
        found: "OptionSpec | GroupSpec | None" = None
        for key, child in children:
            if key == part:
                found = child
                break
        if found is None:
            return None
        node = found
        children = found.children if isinstance(found, GroupSpec) else ()
    return node


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
    @satisfies REQ-101, REQ-103
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
        "Schema di configurazione non allineato ai default: "
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
    @satisfies REQ-097, REQ-108
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
    @satisfies REQ-096
    """

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _mask_secrets(node: "OptionSpec | GroupSpec | None", value: Any) -> Any:
    """@brief Replace secret leaf values with the mask constant.

    @details Recursively walks schema groups and returns `MASKED_SECRET` for
    secret leaf values, leaving non-secret data unchanged. Time complexity
    O(n) over subtree size.
    @param node {OptionSpec|GroupSpec|None} Schema record for `value`.
    @param value {Any} Configuration value to mask.
    @return {Any} Masked copy of `value`.
    @satisfies REQ-098
    """

    if isinstance(node, OptionSpec):
        return MASKED_SECRET if node.secret else value
    if isinstance(node, GroupSpec) and isinstance(value, dict):
        return {
            key: _mask_secrets(child, value.get(key))
            for key, child in node.children
        }
    return value


def _render_print_children(
    prefix: str,
    children: "tuple[tuple[str, OptionSpec | GroupSpec], ...]",
    values: Any,
    lines: list[str],
) -> None:
    """@brief Render one `--print` tree level.

    @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
    connectors, left-justified names, `= <JSON>` scalar leaves, `Sel`/`Valore`
    selection tables for choice leaves with the active choice marked `[*]`,
    `Chiave`/`Valore` box tables for object-shaped leaves (one sorted row per
    entry, JSON-encoded cell values), and `#`/`Valore` box tables for
    list-shaped leaves (one row per element, JSON-encoded cell values).
    Table lines carry the `│` tree continuation of `node_prefix` for
    non-final siblings. Masked secrets bypass table rendering and fall
    back to the scalar line.
    Time complexity O(n) over subtree node count.
    @param prefix {str} Ancestor connector prefix for this level.
    @param children {tuple} Sibling schema nodes being rendered.
    @param values {Any} Effective configuration subtree for this level.
    @param lines {list[str]} Output accumulator mutated in place.
    @return {None} Appends rendered lines to `lines`.
    @satisfies DES-032, REQ-095, REQ-096, REQ-097, REQ-098
    """

    total = len(children)
    for index, (key, node) in enumerate(children):
        last = index == total - 1
        branch = "└── " if last else "├── "
        node_prefix = prefix + ("    " if last else "│   ")
        name = key.ljust(NAME_COLUMN_WIDTH)
        if isinstance(node, GroupSpec):
            lines.append(f"{prefix}│")
            lines.append(f"{prefix}{branch}{name}".rstrip())
            child_values = (
                values.get(key) if isinstance(values, dict) else _MISSING
            )
            _render_print_children(
                node_prefix, node.children, child_values, lines
            )
            continue
        value = (
            values.get(key, _MISSING) if isinstance(values, dict) else _MISSING
        )
        if value is _MISSING:
            value = None
        if node.choices:
            lines.append(f"{prefix}{branch}{name}=")
            active = value if isinstance(value, str) else ""
            rows = [
                ["[*]" if choice.value == active else "[ ]", choice.value]
                for choice in node.choices
            ]
            indent = node_prefix + " " * (NAME_COLUMN_WIDTH + 2)
            lines.extend(_render_box_table(["Sel", "Valore"], rows, indent))
            continue
        rendered = (
            MASKED_SECRET if node.secret and value is not None else value
        )
        if isinstance(rendered, dict):
            lines.append(f"{prefix}{branch}{name}=")
            rows = [
                [entry_key, _render_json(entry_value)]
                for entry_key, entry_value in sorted(rendered.items())
            ]
            indent = node_prefix + " " * (NAME_COLUMN_WIDTH + 2)
            lines.extend(
                _render_box_table(["Chiave", "Valore"], rows, indent)
            )
            continue
        if isinstance(rendered, list):
            lines.append(f"{prefix}{branch}{name}=")
            rows = [
                [str(position), _render_json(item)]
                for position, item in enumerate(rendered, start=1)
            ]
            indent = node_prefix + " " * (NAME_COLUMN_WIDTH + 2)
            lines.extend(_render_box_table(["#", "Valore"], rows, indent))
            continue
        lines.append(f"{prefix}{branch}{name}= {_render_json(rendered)}")


def _render_params_children(
    prefix: str,
    children: "tuple[tuple[str, OptionSpec | GroupSpec], ...]",
    lines: list[str],
) -> None:
    """@brief Render one `--params` hierarchy level.

    @details Emits a `│` bar line before each subgroup, `├──`/`└──` branch
    connectors, left-justified names with `-` annotations, kind labels for
    leaves, and `Valore`/`Significato` allowed-value tables for selection
    leaves. Time complexity O(n) over subtree node count.
    @param prefix {str} Ancestor connector prefix for this level.
    @param children {tuple} Sibling schema nodes being rendered.
    @param lines {list[str]} Output accumulator mutated in place.
    @return {None} Appends rendered lines to `lines`.
    @satisfies REQ-107, REQ-108
    """

    total = len(children)
    for index, (key, node) in enumerate(children):
        last = index == total - 1
        branch = "└── " if last else "├── "
        node_prefix = prefix + ("    " if last else "│   ")
        name = key.ljust(NAME_COLUMN_WIDTH)
        if isinstance(node, GroupSpec):
            lines.append(f"{prefix}│")
            lines.append(f"{prefix}{branch}{name}- {node.description}")
            _render_params_children(node_prefix, node.children, lines)
            continue
        kind_label = KIND_LABELS.get(node.kind, node.kind)
        if node.choices:
            lines.append(
                f"{prefix}{branch}{name}- [{kind_label}] {node.description} "
                "Valori ammessi:"
            )
            rows = [[choice.value, choice.meaning] for choice in node.choices]
            indent = node_prefix + " " * (NAME_COLUMN_WIDTH + 2)
            lines.extend(
                _render_box_table(["Valore", "Significato"], rows, indent)
            )
            continue
        lines.append(
            f"{prefix}{branch}{name}- [{kind_label}] {node.description}"
        )


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
        return None, f"Impossibile leggere '{target}': {err}."
    except json.JSONDecodeError as err:
        return None, f"JSON non valido in '{target}': {err}."
    if not isinstance(payload, dict):
        return None, f"Il file '{target}' deve contenere un oggetto JSON."
    return payload, None


def _write_overrides(payload: dict[str, Any]) -> None:
    """@brief Persist configuration overrides to the canonical config file.

    @details Creates parent directories when missing and writes sorted-key,
    two-space-indented JSON with a trailing newline for deterministic
    content. Time complexity O(n) over payload size.
    @param payload {dict[str,Any]} Full on-disk override mapping.
    @return {None} Applies destination filesystem mutation.
    @throws {OSError} Propagated when filesystem write fails.
    @satisfies REQ-103, REQ-105
    """

    target = get_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)}\n",
        encoding="utf-8",
    )


def _coerce_value(
    raw: str, spec: OptionSpec
) -> "tuple[bool, Any, str | None]":
    """@brief Coerce one raw CLI token by schema kind.

    @details Maps `booleano` tokens to `true`/`false` (case-insensitive),
    `intero` tokens to `int`, `elenco` tokens to JSON arrays of non-empty
    strings, `oggetto` tokens to JSON objects, and leaves `stringa` and
    `selezione` tokens as non-empty strings. Time complexity O(n) over token
    length.
    @param raw {str} Raw value token from the CLI.
    @param spec {OptionSpec} Target option schema record.
    @return {tuple[bool, Any, str|None]} `(ok, value, error)` triple.
    @satisfies REQ-101
    """

    if spec.kind == "booleano":
        lowered = raw.lower()
        if lowered == "true":
            return True, None, None
        if lowered == "false":
            return False, None, None
        return False, None, "attesi true oppure false"
    if spec.kind == "intero":
        try:
            return True, int(raw), None
        except ValueError:
            return False, None, "atteso un valore intero"
    if spec.kind in ("elenco", "oggetto"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return False, None, "atteso un valore JSON valido"
        if spec.kind == "elenco":
            valid = isinstance(parsed, list) and all(
                isinstance(item, str) and item for item in parsed
            )
            if not valid:
                return False, None, "atteso un elenco JSON di stringhe"
            return True, parsed, None
        if not isinstance(parsed, dict):
            return False, None, "atteso un oggetto JSON"
        return True, parsed, None
    if not raw.strip():
        return False, None, "attesa una stringa non vuota"
    return True, raw, None


def print_config_cli_help(command: str) -> None:
    """@brief Print command-specific inline usage help.

    @details Documents the `:` hierarchical path syntax, accepted value
    formats, environment acquisition, and per-command examples for one of
    `--get`, `--set`, or `--unset`. Time complexity O(1).
    @param command {str} Command token requesting inline help.
    @return {None} Writes help text to stdout.
    @satisfies REQ-109
    """

    if command == "--set":
        print(f"Usage: {PROGRAM} --set <percorso> <valore>")
        print("Imposta un'opzione scrivendo solo la chiave nel file di configurazione.")
        print("Il percorso usa ':' come separatore gerarchico delle opzioni.")
        print("Valori booleani: true/false; elenchi e oggetti: JSON.")
        print("Un valore '$NOME' viene acquisito dalla variabile d'ambiente NOME.")
        print("Esempi:")
        print(f'  {PROGRAM} --set management:upgrade "uv tool install shellscripts"')
        print(f"  {PROGRAM} --set dispatch:diff:fallback '[\"bcompare\"]'")
        print(f"  {PROGRAM} --set req:providers $REQ_PROVIDERS")
        return
    if command == "--unset":
        print(f"Usage: {PROGRAM} --unset <percorso>")
        print("Rimuove una chiave dal file di configurazione riattivando il default.")
        print("Il percorso usa ':' come separatore gerarchico delle opzioni.")
        print("Esempi:")
        print(f"  {PROGRAM} --unset management:upgrade")
        print(f"  {PROGRAM} --unset dispatch:diff")
        return
    print(f"Usage: {PROGRAM} --get <percorso>")
    print("Legge un valore dalla configurazione effettiva (default piu' file).")
    print("Il percorso usa ':' come separatore gerarchico delle opzioni.")
    print("Esempi:")
    print(f"  {PROGRAM} --get management:upgrade")
    print(f"  {PROGRAM} --get dispatch:diff:categories")
    print(f"  {PROGRAM} --get req:providers")


def do_print_raw() -> int:
    """@brief Print the on-disk configuration file verbatim.

    @details Enforces schema registry parity with `DEFAULT_RUNTIME_CONFIG`
    before emitting output (DES-034, DES-032 surface membership), then emits
    the raw bytes of the canonical config file without parsing, or a
    bright-red error naming the path when the file is missing or unreadable.
    Time complexity O(n) over file size.
    @return {int} `0` on success; `1` on schema divergence or when the file
      is missing or unreadable.
    @satisfies DES-032, DES-034, REQ-094
    """

    if _fail_on_schema_mismatch():
        return 1
    target = get_config_path()
    if not target.exists():
        print_error(f"File di configurazione non trovato: {target}.")
        return 1
    try:
        content = target.read_text(encoding="utf-8")
    except OSError as err:
        print_error(f"Impossibile leggere '{target}': {err}.")
        return 1
    print(content, end="")
    return 0


def do_print() -> int:
    """@brief Render the effective configuration as an options tree.

    @details Deep-merges on-disk overrides onto hardcoded defaults, then
    renders the schema-ordered tree with branch connectors, `= <JSON>` scalar
    leaves, masked secrets, and `Sel`/`Valore` selection tables. The root
    annotation reports `ATTIVA` when the config file exists and
    `PREDEFINITA` otherwise. Time complexity O(n) over configuration size.
    @return {int} `0` on success; `1` on schema divergence.
    @satisfies REQ-095, REQ-096, REQ-097, REQ-098, DES-034
    """

    if _fail_on_schema_mismatch():
        return 1
    effective = load_runtime_config()
    state = "ATTIVA" if get_config_path().exists() else "PREDEFINITA"
    lines = [f"{ROOT_LABEL} - [Stato: {state}]"]
    _render_print_children("", CONFIG_SCHEMA, effective, lines)
    print("\n".join(lines))
    return 0


def do_params() -> int:
    """@brief Render the configurable parameter hierarchy with descriptions.

    @details Emits the schema-ordered tree with per-group descriptions,
    per-option kind labels and short descriptions, and `Valore`/`Significato`
    allowed-value tables for selection options. Time complexity O(n) over
    schema node count.
    @return {int} `0` on success; `1` on schema divergence.
    @satisfies REQ-107, REQ-108, DES-034
    """

    if _fail_on_schema_mismatch():
        return 1
    lines = [f"{ROOT_LABEL} - Radice delle impostazioni di {PROGRAM}."]
    _render_params_children("", CONFIG_SCHEMA, lines)
    print("\n".join(lines))
    return 0


def do_get(path: str | None) -> int:
    """@brief Read one configuration value by hierarchical path.

    @details Resolves the `:`-separated path against the schema registry and
    the effective configuration, masks secret leaves, prints scalars and
    lists as single-line JSON and object subtrees as indented JSON. Time
    complexity O(n) over subtree size.
    @param path {str|None} Hierarchical path token, for example
      `management:upgrade`.
    @return {int} `0` on success; `1` for missing arguments, unknown paths,
      or absent values.
    @satisfies REQ-098, REQ-099, REQ-100, REQ-109, DES-034
    """

    if _fail_on_schema_mismatch():
        return 1
    parts = _split_path(path or "")
    if parts is None:
        print_config_cli_help("--get")
        return 1
    node = _find_schema_node(parts)
    if node is None:
        print_error(f"Percorso di configurazione sconosciuto: {path}.")
        return 1
    value = _resolve_value(load_runtime_config(), parts)
    if value is _MISSING:
        print_error(f"Parametro non trovato nella configurazione: {path}.")
        return 1
    value = _mask_secrets(node, value)
    if isinstance(value, dict):
        print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    print(json.dumps(value, ensure_ascii=False))
    return 0


def do_set(path: str | None, value: str | None) -> int:
    """@brief Set one configuration value by hierarchical path.

    @details Resolves `$NAME` tokens from the environment, coerces the value
    by schema kind, validates schema-allowed choices, then loads the on-disk
    overrides, writes only the target key, and persists sorted-key indented
    JSON without touching unrelated keys. Time complexity O(n) over
    configuration size.
    @param path {str|None} Hierarchical path token ending at a schema leaf.
    @param value {str|None} Raw value token or `$NAME` environment token.
    @return {int} `0` on success; `1` for missing arguments, unknown paths,
      invalid values, disallowed choices, undefined environment variables, or
      unreadable config files.
    @satisfies REQ-101, REQ-102, REQ-103, REQ-104, REQ-109, DES-034
    """

    if _fail_on_schema_mismatch():
        return 1
    parts = _split_path(path or "")
    if parts is None or value is None:
        print_config_cli_help("--set")
        return 1
    node = _find_schema_node(parts)
    if not isinstance(node, OptionSpec):
        print_error(f"Percorso di configurazione sconosciuto: {path}.")
        return 1
    raw = value
    from_environment = False
    if raw.startswith("$") and len(raw) > 1:
        env_name = raw[1:]
        if env_name not in os.environ:
            print_error(f"Variabile d'ambiente non definita: {env_name}.")
            return 1
        raw = os.environ[env_name]
        from_environment = True
    ok, coerced, error = _coerce_value(raw, node)
    if not ok:
        print_error(f"Valore non valido per {path} [{node.kind}]: {error}.")
        return 1
    if node.choices:
        allowed = [choice.value for choice in node.choices]
        if coerced not in allowed:
            print_error(
                f"Valore non ammesso per {path}. Valori ammessi: "
                + ", ".join(allowed)
                + "."
            )
            return 1
    overrides, load_error = _load_overrides()
    if overrides is None:
        print_error(load_error)
        return 1
    _set_nested(overrides, parts, coerced)
    _write_overrides(overrides)
    if from_environment:
        print_success("Valore acquisito dall'ambiente e salvato con successo.")
    else:
        print_success("Valore salvato con successo.")
    return 0


def do_unset(path: str | None) -> int:
    """@brief Remove one configuration override by hierarchical path.

    @details Loads the on-disk overrides, removes the target key (leaf or
    object subtree), persists the result so hardcoded defaults reactivate,
    and prints the subtree-removal warning for object payloads. Time
    complexity O(n) over configuration size.
    @param path {str|None} Hierarchical path token to remove.
    @return {int} `0` on success; `1` for missing arguments, unknown paths,
      absent overrides, or unreadable config files.
    @satisfies REQ-105, REQ-106, REQ-109, DES-034
    """

    if _fail_on_schema_mismatch():
        return 1
    parts = _split_path(path or "")
    if parts is None:
        print_config_cli_help("--unset")
        return 1
    if _find_schema_node(parts) is None:
        print_error(f"Percorso di configurazione sconosciuto: {path}.")
        return 1
    overrides, load_error = _load_overrides()
    if overrides is None:
        print_error(load_error)
        return 1
    removed = _pop_nested(overrides, parts)
    if removed is _MISSING:
        print_error(f"Nessun parametro da rimuovere per: {path}.")
        return 1
    _write_overrides(overrides)
    if isinstance(removed, dict):
        print(f"ATTENZIONE: Rimossi tutti i parametri per {path}.")
    else:
        print_info(f"Parametro rimosso e default ripristinato: {path}.")
    return 0


__all__ = [
    "CONFIG_SCHEMA",
    "ChoiceSpec",
    "GroupSpec",
    "OptionSpec",
    "do_get",
    "do_params",
    "do_print",
    "do_print_raw",
    "do_set",
    "do_unset",
    "find_schema_mismatches",
    "print_config_cli_help",
]
