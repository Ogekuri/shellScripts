#!/usr/bin/env python3
"""@brief Centralized runtime configuration loader and accessor surface.

@details Stores hardcoded defaults for configurable CLI behaviors and provides
deterministic runtime loading from `~/.config/shellScripts/config.json` with
recursive merge semantics. Missing files/keys preserve defaults; invalid value
types are ignored at accessor boundaries. Time complexity for load is O(N) over
JSON node count.
@satisfies DES-011, DES-012, REQ-004, REQ-005, REQ-024, REQ-045, REQ-046, REQ-050
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from shell_scripts.utils import print_warn

## @var DEFAULT_RUNTIME_CONFIG
#  @brief Hardcoded default runtime configuration payload.
#  @details Defines management command templates and dispatch command profiles
#  for `diff`, `edit`, and `view`. Serialized by `write_default_runtime_config`.
#  @satisfies DES-011, DES-012
DEFAULT_RUNTIME_CONFIG: dict[str, Any] = {
    "management": {
        "upgrade": (
            "uv tool install shellscripts --force "
            "--from git+https://github.com/Ogekuri/shellScripts.git"
        ),
        "uninstall": "uv tool uninstall shellscripts",
    },
    "dispatch": {
        "diff": {
            "categories": {
                "image": ["bcompare"],
                "pdf": ["bcompare"],
                "text": ["bcompare"],
                "code": ["bcompare"],
                "html": ["bcompare"],
                "markdown": ["bcompare"],
            },
            "fallback": ["bcompare"],
        },
        "edit": {
            "categories": {
                "image": ["gimp"],
                "pdf": ["okular"],
                "text": ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
                "code": ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
                "html": ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
                "markdown": ["/opt/sublime_text/sublime_text", "--launch-or-new-window", "-wait"],
            },
            "fallback": ["/opt/sublime_text/sublime_text", "-n", "-wait"],
        },
        "view": {
            "categories": {
                "image": ["sushi"],
                "pdf": ["sushi"],
                "text": ["sushi"],
                "code": ["sushi"],
                "html": ["sushi"],
                "markdown": ["typora"],
            },
            "fallback": ["sushi"],
        },
    },
    "req": {
        "providers": [
            "claude:prompts",
            "github:skills",
            "codex:skills",
            "opencode:prompts",
            "gemini:prompts",
            "kiro:agents",
        ],
        "static_checks": [
            "C=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c11",
            "C=Command,clang-format,--dry-run,--Werror",
            "C++=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c++20",
            "C++=Command,clang-format,--dry-run,--Werror",
            "Python=Pylance",
            "Python=Ruff",
            "JavaScript=Command,node,--check",
        ],
    },
}

## @var _runtime_config
#  @brief In-memory runtime configuration snapshot.
#  @details Initialized from defaults; updated only by `load_runtime_config`.
#  @satisfies DES-011, REQ-045
_runtime_config: dict[str, Any] = copy.deepcopy(DEFAULT_RUNTIME_CONFIG)


def get_config_path() -> Path:
    """@brief Return canonical runtime config location.

    @details Resolves path as `$HOME/.config/shellScripts/config.json` using
    `Path.home()` for user directory abstraction.
    @return {Path} Absolute config file path.
    @satisfies DES-011, DES-012, REQ-045, REQ-046
    """

    return Path.home() / ".config" / "shellScripts" / "config.json"


def get_default_runtime_config() -> dict[str, Any]:
    """@brief Return deep-copied default configuration payload.

    @details Produces an isolated copy to avoid external mutation of the global
    defaults constant and to keep write/load operations deterministic.
    @return {dict[str, Any]} Fresh deep copy of `DEFAULT_RUNTIME_CONFIG`.
    @satisfies DES-011, DES-012
    """

    return copy.deepcopy(DEFAULT_RUNTIME_CONFIG)


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """@brief Recursively merge nested mapping values.

    @details For keys where both base and override values are dictionaries,
    recursively merges child keys; otherwise replaces base value with override.
    Time complexity O(N) over override node count.
    @param base {dict[str, Any]} Target mapping mutated in place.
    @param override {dict[str, Any]} Source mapping with overriding values.
    @return {dict[str, Any]} The mutated `base` reference.
    @satisfies DES-011, REQ-045
    """

    for key, value in override.items():
        if isinstance(base.get(key), dict) and isinstance(value, dict):
            _deep_merge_dict(base[key], value)
            continue
        base[key] = value
    return base


def _normalize_command_vector(value: Any) -> list[str] | None:
    """@brief Validate and normalize an executable argv vector.

    @details Accepts only non-empty lists of non-empty strings and returns a
    cloned list for defensive immutability.
    @param value {Any} Candidate command vector.
    @return {list[str]|None} Sanitized vector or `None` if invalid.
    @satisfies DES-011, REQ-045
    """

    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(item, str) and item for item in value):
        return None
    return [item for item in value]


def _normalize_string_list(value: Any) -> list[str] | None:
    """@brief Validate and normalize a list of non-empty strings.

    @details Accepts only list payloads containing non-empty string elements and
    returns a cloned list for defensive immutability. Empty lists are valid.
    @param value {Any} Candidate list payload.
    @return {list[str]|None} Sanitized list or `None` if invalid.
    @satisfies DES-011, REQ-045, REQ-050
    """

    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) and item for item in value):
        return None
    return [item for item in value]


def _normalize_categories(value: Any) -> dict[str, list[str]] | None:
    """@brief Validate category-to-command mapping payload.

    @details Keeps only entries with string keys and valid command vectors.
    Invalid entries are dropped and can trigger fallback usage upstream.
    @param value {Any} Candidate category map payload.
    @return {dict[str, list[str]]|None} Sanitized category map or `None`.
    @satisfies DES-011, REQ-024, REQ-045
    """

    if not isinstance(value, dict):
        return None
    normalized: dict[str, list[str]] = {}
    for key, command in value.items():
        if not isinstance(key, str):
            continue
        command_vector = _normalize_command_vector(command)
        if command_vector is None:
            continue
        normalized[key] = command_vector
    return normalized


def load_runtime_config(path: Path | None = None) -> dict[str, Any]:
    """@brief Load runtime configuration file and merge into defaults.

    @details Resets in-memory state to defaults for each call, then attempts to
    read and parse JSON payload from target path and recursively merge override
    keys. Missing file, invalid JSON, non-object root, or read errors preserve
    defaults and emit warnings.
    @param path {Path|None} Optional override path; default is canonical path.
    @return {dict[str, Any]} Active in-memory runtime configuration snapshot.
    @exception {json.JSONDecodeError} Handled internally and downgraded to warn.
    @exception {OSError} Handled internally and downgraded to warn.
    @satisfies DES-011, REQ-045
    """

    global _runtime_config

    target = path or get_config_path()
    _runtime_config = get_default_runtime_config()
    if not target.exists():
        return _runtime_config

    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except OSError as err:
        print_warn(f"Cannot read runtime config '{target}': {err}. Using defaults.")
        return _runtime_config
    except json.JSONDecodeError as err:
        print_warn(f"Invalid JSON in runtime config '{target}': {err}. Using defaults.")
        return _runtime_config

    if not isinstance(payload, dict):
        print_warn(
            f"Runtime config '{target}' must be a JSON object. Using defaults."
        )
        return _runtime_config

    _deep_merge_dict(_runtime_config, payload)
    return _runtime_config


def get_management_command(name: str) -> str:
    """@brief Resolve management command string with safe default fallback.

    @details Reads runtime key under `management.<name>`; returns default value
    when key is absent or not a non-empty string.
    @param name {str} Management operation key (`upgrade` or `uninstall`).
    @return {str} Shell command string to execute.
    @satisfies REQ-004, REQ-005, REQ-045
    """

    runtime_value = _runtime_config.get("management", {}).get(name)
    if isinstance(runtime_value, str) and runtime_value.strip():
        return runtime_value
    default_value = DEFAULT_RUNTIME_CONFIG["management"][name]
    return default_value


def get_dispatch_profile(name: str) -> tuple[dict[str, list[str]], list[str]]:
    """@brief Resolve dispatch profile for diff/edit/view command wrappers.

    @details Builds profile from `dispatch.<name>` runtime payload with typed
    normalization and per-section fallback to hardcoded defaults for missing or
    invalid values.
    @param name {str} Dispatch command key (`diff`, `edit`, or `view`).
    @return {tuple[dict[str, list[str]], list[str]]} `(categories, fallback)`.
    @satisfies DES-007, REQ-024, REQ-045
    """

    default_profile = DEFAULT_RUNTIME_CONFIG["dispatch"][name]
    runtime_profile = _runtime_config.get("dispatch", {}).get(name, {})

    categories = _normalize_categories(runtime_profile.get("categories"))
    if categories is None:
        categories = _normalize_categories(default_profile["categories"])
    fallback = _normalize_command_vector(runtime_profile.get("fallback"))
    if fallback is None:
        fallback = _normalize_command_vector(default_profile["fallback"])

    if categories is None or fallback is None:
        raise ValueError("Default dispatch profile is invalid.")
    return categories, fallback


def get_req_profile() -> tuple[list[str], list[str]]:
    """@brief Resolve `req` providers and static checks from runtime config.

    @details Builds profile from `req.providers` and `req.static_checks` runtime
    payload with typed normalization and per-section fallback to hardcoded
    defaults for missing or invalid values.
    @return {tuple[list[str], list[str]]} `(providers, static_checks)`.
    @satisfies DES-011, REQ-045, REQ-050
    """

    default_profile = DEFAULT_RUNTIME_CONFIG["req"]
    runtime_profile = _runtime_config.get("req", {})
    if not isinstance(runtime_profile, dict):
        runtime_profile = {}

    providers = _normalize_string_list(runtime_profile.get("providers"))
    if providers is None:
        providers = _normalize_string_list(default_profile["providers"])

    static_checks = _normalize_string_list(runtime_profile.get("static_checks"))
    if static_checks is None:
        static_checks = _normalize_string_list(default_profile["static_checks"])

    if providers is None or static_checks is None:
        raise ValueError("Default req profile is invalid.")
    return providers, static_checks


def write_default_runtime_config(path: Path | None = None) -> Path:
    """@brief Write default runtime configuration file to disk.

    @details Creates parent directories when missing and writes canonical JSON
    payload using sorted keys and indentation for deterministic content.
    @param path {Path|None} Optional override path; default is canonical path.
    @return {Path} Path where the file has been written.
    @exception {OSError} Propagated when filesystem write fails.
    @satisfies DES-012, REQ-046
    """

    target = path or get_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"{json.dumps(DEFAULT_RUNTIME_CONFIG, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return target
