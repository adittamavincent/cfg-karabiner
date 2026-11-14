# AGENTS.md — cfg-karabiner

Vincent's own Karabiner-Elements rules. This is a config repository (`cfg-<target-program>` naming), not a native app, so the `app-*` template in `../AGENTS.md` does not apply. Renamed from `eezaatee-fav-karabiner` on 2026-11-14 (local folder and GitHub).

- One rule per file in `rules/`. The descriptions start with `eezaatee ·`. `dist/` is generated with `sync_karabiner.py build`; never edit it by hand.
- Never put app presets (for example Caps Lock → Hyper) into `rules/`. The live profile mixes app rules and repository rules; the sync touches only rules it owns and must keep the app's `enabled` toggles.
- Never write `~/.config/karabiner/karabiner.json` by hand or copy a full config over it. Use `sync_karabiner.py sync` (it backs up first). Run `status` and `sync --dry-run` before a real sync.
- Checks before commit: `uv run --no-project python -m unittest discover -s tests` and `karabiner_cli --lint-complex-modifications dist/*.json`.
- Stack: Python 3.12+ standard library only, run with `uv run --no-project`. Branches use `codex/`. Remote: `adittamavincent/cfg-karabiner` (account `adittamavincent`). Do not push unless Vincent asks.
- Older copies are on the external volume `/Volumes/Meaw` (as `eezaatee-fav-karabiner` in `code-repos/tools/`, `code-repos-25-10-2026/projects/`, `code-repos-old-25-oct-2026/my-tools/`). This folder is the working copy since 2026-11-14.
