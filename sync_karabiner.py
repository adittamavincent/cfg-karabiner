#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Merge this repository's own Karabiner rules into the active profile.

Every rule in ``rules/*.json`` is owned by this repository. All other rules in
the profile (for example the Hyper Key preset added from the Karabiner app) are
foreign: the script never edits, removes or reorders them. It only adds,
replaces, moves or removes its own rules, keeps the per-rule ``enabled`` toggle
set in the Karabiner app, and writes a timestamped backup before each write.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parent
RULES_DIR = REPO / "rules"
DIST_FILE = REPO / "dist" / "eezaatee-fav-karabiner.json"
ASSET_TITLE = "eezaatee favorite rules"
DEFAULT_TARGET = Path("~/.config/karabiner/karabiner.json").expanduser()
DEFAULT_ASSETS_DIR = Path("~/.config/karabiner/assets/complex_modifications").expanduser()
PLACEMENTS = {"append", "before-overlaps"}
FROM_KEYS = ("key_code", "consumer_key_code", "pointing_button", "apple_vendor_keyboard_key_code")


@dataclass
class OwnedRule:
    id: str
    placement: str
    rule: dict
    names: set[str]  # current description plus legacy descriptions

    @property
    def description(self) -> str:
        return self.rule["description"]


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


def load_owned_rules(rules_dir: Path = RULES_DIR, only: list[str] | None = None) -> list[OwnedRule]:
    owned: list[OwnedRule] = []
    for path in sorted(rules_dir.glob("*.json")):
        doc = load_json(path)
        rule = doc.get("rule")
        if not isinstance(rule, dict) or not isinstance(rule.get("manipulators"), list):
            raise ValueError(f"{path}: 'rule' must be a Karabiner rule with manipulators")
        description = rule.get("description")
        if not isinstance(description, str) or not description:
            raise ValueError(f"{path}: rule needs a non-empty description")
        if "enabled" in rule:
            raise ValueError(f"{path}: leave 'enabled' to the Karabiner app toggle")
        placement = doc.get("placement", "append")
        if placement not in PLACEMENTS:
            raise ValueError(f"{path}: placement must be one of {sorted(PLACEMENTS)}")
        legacy = doc.get("legacy_descriptions", [])
        owned.append(OwnedRule(str(doc.get("id") or path.stem), placement, rule, {description, *legacy}))

    ids = [rule.id for rule in owned]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate rule ids in rules/")
    all_names = [name for rule in owned for name in rule.names]
    if len(all_names) != len(set(all_names)):
        raise ValueError("Two rule files claim the same description")
    if only:
        unknown = set(only) - set(ids)
        if unknown:
            raise ValueError(f"Unknown rule id(s): {', '.join(sorted(unknown))}. Known: {', '.join(ids)}")
        owned = [rule for rule in owned if rule.id in only]
    if not owned:
        raise ValueError(f"No rules selected from {rules_dir}")
    return owned


def selected_profile(config: dict, label: str) -> dict:
    profiles = config.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError(f"{label} must contain a non-empty 'profiles' array")
    selected = [p for p in profiles if isinstance(p, dict) and p.get("selected") is True]
    if len(selected) != 1:
        raise ValueError(f"{label} must have exactly one selected profile")
    return selected[0]


def profile_rules(profile: dict, label: str) -> list:
    mods = profile.setdefault("complex_modifications", {})
    if not isinstance(mods, dict):
        raise ValueError(f"{label}: selected profile has invalid complex_modifications")
    rules = mods.setdefault("rules", [])
    if not isinstance(rules, list):
        raise ValueError(f"{label}: selected profile has an invalid 'rules' array")
    return rules


def trigger_keys(rule: dict) -> set[str]:
    keys: set[str] = set()
    for manipulator in rule.get("manipulators", []):
        source = manipulator.get("from", {}) if isinstance(manipulator, dict) else {}
        for field in FROM_KEYS:
            if field in source:
                keys.add(f"{field}:{source[field]}")
        for item in source.get("simultaneous", []) if isinstance(source, dict) else []:
            for field in FROM_KEYS:
                if field in item:
                    keys.add(f"{field}:{item[field]}")
    return keys


def describe(rule: object) -> str:
    if isinstance(rule, dict):
        if rule.get("description"):
            return str(rule["description"])
        # App presets such as Hyper Key may only describe their manipulators.
        first = (rule.get("manipulators") or [{}])[0]
        inner = first.get("description") if isinstance(first, dict) else None
        return f"(rule without description: {inner})" if inner else "(rule without description)"
    return "(invalid rule)"


def merge(rules: list, owned: list[OwnedRule], all_owned_names: set[str]) -> tuple[list[str], list[str]]:
    """Merge owned rules into ``rules`` in place. Returns (actions, warnings)."""
    actions: list[str] = []
    warnings: list[str] = []

    def is_foreign(rule: object) -> bool:
        return describe(rule) not in all_owned_names

    for item in owned:
        matches = [i for i, rule in enumerate(rules) if describe(rule) in item.names]
        if len(matches) > 1:
            raise ValueError(
                f"Found {len(matches)} copies of {item.description!r} in the active profile; "
                "remove the duplicates in the Karabiner app, then sync again."
            )
        new_rule = json.loads(json.dumps(item.rule))
        if matches:
            index = matches[0]
            old = rules.pop(index)
            if isinstance(old, dict) and "enabled" in old:
                new_rule["enabled"] = old["enabled"]  # keep the app toggle
            verb = "replace" if describe(old) == item.description else f"migrate {describe(old)!r} to"
        else:
            index = len(rules)
            verb = "add"

        keys = trigger_keys(new_rule)
        overlaps = [i for i, rule in enumerate(rules) if is_foreign(rule) and trigger_keys(rule) & keys]
        if item.placement == "before-overlaps" and overlaps and overlaps[0] < index:
            first = overlaps[0]
            actions.append(f"{verb} {item.description!r}, placed before foreign rule {describe(rules[first])!r}")
            index = first
        else:
            actions.append(f"{verb} {item.description!r}")
            earlier = [i for i in overlaps if i < index]
            if earlier:
                shared = ", ".join(sorted(k.split(":", 1)[1] for k in trigger_keys(rules[earlier[0]]) & keys))
                warnings.append(
                    f"foreign rule {describe(rules[earlier[0]])!r} runs earlier and also uses {shared}; "
                    f"it can take those keys before {item.description!r}"
                )
        rules.insert(index, new_rule)
        if new_rule.get("enabled") is False:
            warnings.append(f"{item.description!r} is turned off in the Karabiner app; the toggle was kept")
    return actions, warnings


def write_atomically(target: Path, content: str, mode: int) -> None:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=target.parent,
            prefix=f".{target.name}.", suffix=".tmp", delete=False,
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


def save_config(target: Path, config: dict) -> Path:
    mode = target.stat().st_mode & 0o777
    backup = target.with_name(f"{target.name}.bak.{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}")
    shutil.copy2(target, backup)
    write_atomically(target, json.dumps(config, ensure_ascii=False, indent=4) + "\n", mode)
    return backup


def open_target(path: Path) -> tuple[Path, dict, list]:
    target = path.expanduser()
    if not target.is_file():
        raise ValueError(
            f"Target config not found: {target}. Open Karabiner-Elements once so it creates "
            "the config; this script never writes a full config from scratch."
        )
    config = load_json(target)
    return target, config, profile_rules(selected_profile(config, str(target)), str(target))


def cmd_sync(args: argparse.Namespace) -> int:
    every = load_owned_rules()
    owned = load_owned_rules(only=args.only)
    target, config, rules = open_target(args.target)
    actions, warnings = merge(rules, owned, {n for r in every for n in r.names})
    prefix = "Dry run: would " if args.dry_run else ""
    for action in actions:
        print(f"{prefix}{action}")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if args.dry_run:
        return 0
    backup = save_config(target, config)
    print(f"Updated {target}\nBackup: {backup}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    owned = load_owned_rules(only=args.only)
    names = {n for r in owned for n in r.names}
    target, config, rules = open_target(args.target)
    removed = [describe(r) for r in rules if describe(r) in names]
    if not removed:
        print("Nothing to remove.")
        return 0
    rules[:] = [r for r in rules if describe(r) not in names]
    for name in removed:
        print(f"{'Dry run: would remove' if args.dry_run else 'Remove'} {name!r}")
    if args.dry_run:
        return 0
    print(f"Updated {target}\nBackup: {save_config(target, config)}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    owned = load_owned_rules()
    by_name = {n: r for r in owned for n in r.names}
    target, _config, rules = open_target(args.target)
    print(f"Active profile rules in {target} (first match wins):")
    for i, rule in enumerate(rules, 1):
        state = "off" if isinstance(rule, dict) and rule.get("enabled") is False else "on "
        mine = by_name.get(describe(rule))
        if mine is None:
            tag = "app/other  "
        elif describe(rule) == mine.description:
            tag = f"repo:{mine.id}" if json.dumps({k: v for k, v in rule.items() if k != "enabled"}, sort_keys=True) == json.dumps(mine.rule, sort_keys=True) else f"repo:{mine.id} (outdated)"
        else:
            tag = f"repo:{mine.id} (legacy)"
        print(f"{i:>2}. [{state}] {describe(rule)}  <{tag}>")
    present = {describe(r) for r in rules}
    for rule in owned:
        if rule.description not in present and not (rule.names & present):
            print(f"    missing: {rule.description}  <repo:{rule.id}>")
    return 0


def asset_document() -> dict:
    return {"title": ASSET_TITLE, "rules": [r.rule for r in load_owned_rules()]}


def cmd_build(args: argparse.Namespace) -> int:
    content = json.dumps(asset_document(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not DIST_FILE.is_file() or DIST_FILE.read_text(encoding="utf-8") != content:
            print(f"{DIST_FILE.relative_to(REPO)} is stale; run: uv run sync_karabiner.py build", file=sys.stderr)
            return 1
        print(f"{DIST_FILE.relative_to(REPO)} is up to date")
        return 0
    DIST_FILE.parent.mkdir(exist_ok=True)
    DIST_FILE.write_text(content, encoding="utf-8")
    print(f"Wrote {DIST_FILE.relative_to(REPO)}")
    return 0


def cmd_install_assets(args: argparse.Namespace) -> int:
    folder = args.assets_dir.expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / DIST_FILE.name
    content = json.dumps(asset_document(), ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print(f"Dry run: would write {target}")
        return 0
    write_atomically(target, content, 0o644)
    print(f"Wrote {target}\nKarabiner app: Complex Modifications → Add predefined rule → {ASSET_TITLE!r}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")

    def with_target(p: argparse.ArgumentParser) -> None:
        p.add_argument("--target", type=Path, default=DEFAULT_TARGET, help=f"Karabiner config (default: {DEFAULT_TARGET})")

    p = sub.add_parser("sync", help="add or update this repo's rules; leave all other rules untouched")
    with_target(p)
    p.add_argument("--only", nargs="+", metavar="ID", help="sync only these rule ids")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("remove", help="remove only this repo's rules from the active profile")
    with_target(p)
    p.add_argument("--only", nargs="+", metavar="ID")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_remove)

    p = sub.add_parser("status", help="list active profile rules and which ones this repo owns")
    with_target(p)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("build", help=f"write {DIST_FILE.relative_to(REPO)} for the Karabiner app")
    p.add_argument("--check", action="store_true", help="fail when the dist file is stale")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("install-assets", help="copy the rules into Karabiner's 'Add predefined rule' list")
    p.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_install_assets)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
