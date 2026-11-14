# cfg-karabiner

Vincent's own Karabiner-Elements rules, kept as separate modules. The sync script
merges them into the active Karabiner profile and leaves the rules you add in the
Karabiner app (for example the Hyper Key preset) untouched.

## Rules

Each file in `rules/` is one rule. In the Karabiner app each one appears as its own
entry with its own on/off toggle under **Complex Modifications**. Their names start
with `eezaatee ·`.

| File | What it does |
|---|---|
| `rules/10-shift-caps-lock-ctrl-opt-cmd.json` | **Shift + Caps Lock** → Control + Option + Command (Hyper without Shift). The held Shift is removed from the output. |
| `rules/20-hjio-vim-layer.json` | **Hold `;`** for the arrow layer: `h` ← `j` ↓ `i` ↑ `o` →. Tap `;` (under 500 ms) still types `;`. Held Shift, Command and Option still apply, so Cmd/Option + arrow and selection work. |

Verified on 2026-11-14 with Karabiner-EventViewer and the macOS Keyboard Viewer: the
output is ⌃⌥⌘ plus the key, with no Shift.

**Recording this shortcut in another app (found 2026-11-14).** Shortcut recorders that
accept a single modifier as a hotkey, such as Raycast's, stop too early. Karabiner
releases Shift the moment Caps Lock goes down, so the recorder sees Shift pressed and
released on its own and saves "Left Shift". To record, press the physical keys
Control + Option + Command + the letter instead. The saved shortcut then also fires
from Shift + Caps Lock + the letter. Delete any "Left Shift" hotkey a failed recording
left behind, because it fires on every Shift press. See `../cfg-raycast` for the
Raycast setup.

Caps Lock alone → full Hyper (Shift + Control + Option + Command) is **not** in this
repository. Use the app's own preset for it. The Shift + Caps Lock rule is built to
sit in front of that preset.

## How the sync respects the app's rules

- Rules owned by this repository are found by their exact description (plus the old
  names in `legacy_descriptions`). Every other rule belongs to the app or to you and
  is never edited, removed or reordered.
- Karabiner uses the first rule that matches. A rule with
  `"placement": "before-overlaps"` is put just in front of the first app rule that
  uses the same key. This is how Shift + Caps Lock wins over the Hyper Key preset.
  A rule with `"placement": "append"` keeps its place, or goes to the end when new.
  If an earlier app rule uses the same key, the script prints a warning and changes
  nothing.
- When you turn a rule off in the Karabiner app (`"enabled": false`), the sync keeps
  it off.
- Each write makes a timestamped backup next to `karabiner.json`. Duplicate copies of
  one rule stop the sync with an error.

## Commands

Run from this folder. Only the Python standard library is used.

```bash
uv run --no-project sync_karabiner.py status
```

```bash
uv run --no-project sync_karabiner.py sync --dry-run
```

```bash
uv run --no-project sync_karabiner.py sync
```

- `sync --only hjio-vim-layer` syncs one rule.
- `remove [--only ID] [--dry-run]` takes this repository's rules out of the profile.
- `install-assets` copies the rules into
  `~/.config/karabiner/assets/complex_modifications/`. They then show in the app under
  **Add predefined rule → eezaatee favorite rules**, next to the built-in presets.
- `build` regenerates `dist/cfg-karabiner.json` from `rules/`. `build --check`
  fails when it is stale.

## Adding a rule

1. Add `rules/NN-name.json` with `id`, `placement`, `legacy_descriptions` and `rule`.
   Start the description with `eezaatee ·`. Do not set `enabled`; the app toggle owns it.
2. Run `uv run --no-project sync_karabiner.py build` and the checks below.
3. Run `sync`.

## Checks

```bash
uv run --no-project python -m unittest discover -s tests
```

```bash
'/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli' --lint-complex-modifications dist/*.json
```
