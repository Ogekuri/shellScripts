#!/usr/bin/env python3
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

PROGRAM = "shellscripts"
OWNER = "Ogekuri"
REPOSITORY = "shellScripts"
IDLE_DELAY = 300
HTTP_TIMEOUT = 2
GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"
CACHE_DIR = Path.home() / ".cache" / PROGRAM
IDLE_TIME_FILE = CACHE_DIR / "check_version_idle-time.json"

BRIGHT_GREEN = "\033[92m"
BRIGHT_RED = "\033[91m"
RESET = "\033[0m"


def _read_idle_config():
    if not IDLE_TIME_FILE.exists():
        return None
    try:
        with open(IDLE_TIME_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_idle_config(last_check_ts, idle_until_ts):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "last_check_timestamp": last_check_ts,
        "last_check_human": datetime.fromtimestamp(
            last_check_ts, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "idle_until_timestamp": idle_until_ts,
        "idle_until_human": datetime.fromtimestamp(
            idle_until_ts, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    with open(IDLE_TIME_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _should_check():
    config = _read_idle_config()
    if config is None:
        return True
    idle_until = config.get("idle_until_timestamp", 0)
    return time.time() >= idle_until


def _compare_versions(current, latest):
    def parse(v):
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    try:
        return parse(latest) > parse(current)
    except (ValueError, AttributeError):
        return False


def check_for_updates(current_version):
    if not _should_check():
        return

    now = time.time()

    try:
        req = urllib.request.Request(GITHUB_API_URL)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", f"{PROGRAM}/{current_version}")
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            latest = data.get("tag_name", "").lstrip("v")

            if latest and _compare_versions(current_version, latest):
                print(
                    f"{BRIGHT_GREEN}A new version of {PROGRAM} is available: "
                    f"{latest} (installed: {current_version}). "
                    f"Run '{PROGRAM} --upgrade' to update.{RESET}"
                )

            _write_idle_config(now, now + IDLE_DELAY)

    except urllib.error.HTTPError as e:
        if e.code == 429:
            retry_after = IDLE_DELAY
            ra_header = e.headers.get("Retry-After")
            if ra_header:
                try:
                    retry_after = int(ra_header)
                except ValueError:
                    pass
            idle_until = now + max(retry_after, IDLE_DELAY)
            config = _read_idle_config()
            if config:
                existing_idle = config.get("idle_until_timestamp", 0)
                if existing_idle > idle_until:
                    idle_until = existing_idle
            _write_idle_config(now, idle_until)
            print(
                f"{BRIGHT_RED}Update check failed: rate limit exceeded "
                f"(HTTP 429). Retrying after cooldown.{RESET}"
            )
        elif e.code == 403:
            _write_idle_config(now, now + IDLE_DELAY)
            print(
                f"{BRIGHT_RED}Update check failed: rate limit exceeded "
                f"(HTTP 403).{RESET}"
            )
        else:
            _write_idle_config(now, now + IDLE_DELAY)
            print(f"{BRIGHT_RED}Update check failed: HTTP {e.code}.{RESET}")
    except Exception:
        pass
