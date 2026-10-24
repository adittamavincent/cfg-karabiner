#!/usr/bin/env python3
"""Install this repository's Hijo rule into the active Karabiner profile."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


DEFAULT_TARGET = Path("~/.config/karabiner/karabiner.json").expanduser()


def selected_profile(config: dict, label: str) -> dict:
    profiles = config.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError(f"{label} must contain a non-empty 'profiles' array")
    if any(not isinstance(profile, dict) for profile in profiles):
        raise ValueError(f"{label} contains an invalid profile entry")

    selected = [profile for profile in profiles if profile.get("selected") is True]
    if len(selected) != 1:
        raise ValueError(f"{label} must have exactly one selected profile")
    return selected[0]


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
    except OSError as error:
        raise ValueError(f"Cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_atomically(target: Path, content: str, mode: int) -> None:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.chmod(temp_path, mode)
        os.replace(temp_path, target)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Replace or add only this repository's Hijo rule in the active "
            "Karabiner profile."
        )
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Karabiner config to update (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show whether the Hijo rule would be added or replaced without writing",
    )
    args = parser.parse_args()

    repo_config = Path(__file__).with_name("karabiner.json")
    target = args.target.expanduser()

    try:
        if not target.is_file():
            raise ValueError(
                f"Target config not found: {target}. Create or select a Karabiner "
                "profile first; this script will not replace a missing full config."
            )

        source = load_json(repo_config)
        destination = load_json(target)
        source_profile = selected_profile(source, str(repo_config))
        target_profile = selected_profile(destination, str(target))

        source_mods = source_profile.get("complex_modifications", {})
        if not isinstance(source_mods, dict):
            raise ValueError(f"{repo_config} has invalid complex_modifications")
        source_rules = source_mods.get("rules", [])
        if not isinstance(source_rules, list):
            raise ValueError(f"{repo_config} has an invalid 'rules' array")
        if len(source_rules) != 1 or not isinstance(source_rules[0], dict):
            raise ValueError(
                f"{repo_config} must contain exactly one Hijo rule in its selected profile"
            )
        hijo_rule = source_rules[0]
        description = hijo_rule.get("description")
        if not isinstance(description, str) or not description:
            raise ValueError("The Hijo rule must have a non-empty description")

        target_mods = target_profile.setdefault("complex_modifications", {})
        if not isinstance(target_mods, dict):
            raise ValueError(f"The selected profile in {target} has invalid complex_modifications")
        target_rules = target_mods.setdefault("rules", [])
        if not isinstance(target_rules, list):
            raise ValueError(f"The selected profile in {target} has an invalid 'rules' array")

        matches = [
            index
            for index, rule in enumerate(target_rules)
            if isinstance(rule, dict) and rule.get("description") == description
        ]
        if len(matches) > 1:
            raise ValueError(
                f"Found {len(matches)} rules named {description!r} in the active profile; "
                "remove duplicates before syncing."
            )

        if matches:
            action = "replace"
            target_rules[matches[0]] = hijo_rule
        else:
            action = "add"
            target_rules.append(hijo_rule)

        if args.dry_run:
            print(f"Dry run: would {action} Hijo rule {description!r} in {target}.")
            return 0

        original_mode = target.stat().st_mode & 0o777
        backup = target.with_name(
            f"{target.name}.bak.{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
        )
        shutil.copy2(target, backup)
        serialized = json.dumps(destination, ensure_ascii=False, indent=2) + "\n"
        write_atomically(target, serialized, original_mode)
        result = "replaced" if action == "replace" else "added"
        print(f"Hijo rule {result} in {target}.")
        print(f"Backup: {backup}")
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
