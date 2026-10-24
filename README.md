# Favorite Karabiner Configuration (`eezaatee-fav-karabiner`)

Personal Karabiner-Elements configuration file (`karabiner.json`) optimized for macOS navigation and custom key bindings.

## Features

- **Semicolon (`;`) Dual-Role Key**:
  - **Tap (press & release)**: Types `;` normally (or `:` with Shift).
  - **Hold down**: Activates the VIM navigation layer.
- **VIM Arrow Keys** (Hold `;`):
  - `; + H` → Left Arrow
  - `; + J` → Down Arrow
  - `; + I` → Up Arrow
  - `; + O` → Right Arrow
- Navigation mappings preserve held modifiers and apply only while `vim_layer = 1`.

## Installation

1. Install [Karabiner-Elements](https://karabiner-elements.pqrs.org/) on macOS.
2. Merge only the Hijo rule into the active Karabiner profile:

```bash
uv run sync_karabiner.py --dry-run
uv run sync_karabiner.py
```

The script replaces the rule with the same description, or adds it if missing. Other
rules and settings are retained. Before writing, it saves a timestamped backup next
to `~/.config/karabiner/karabiner.json`. Karabiner-Elements should detect the change.
