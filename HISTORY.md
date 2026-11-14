# Riwayat eezaatee-fav-karabiner

## 2026-11-14T10:25+07:00 — Modular rules, app-preset aware sync, Shift + Caps Lock

- **Permintaan:** Vincent meminta repo hjio dari Meaw dibangun ulang di `TOOLS/I-Built`, dengan aturan kustom terpisah yang menghormati preset bawaan app Karabiner (misalnya Hyper Key), plus fitur Shift + Caps Lock → Control + Option + Command.
- **Dikerjakan:** Clone dari `/Volumes/Meaw/code-repos-25-10-2026/projects/eezaatee-fav-karabiner` (HEAD `dc8a6b0`, sama dengan GitHub `origin/main`). `karabiner.json` penuh diganti `rules/*.json` (satu aturan per file). `sync_karabiner.py` ditulis ulang: subcommand `sync`, `remove`, `status`, `build`, `install-assets`; kepemilikan lewat deskripsi persis + `legacy_descriptions`; placement `before-overlaps` / `append`; toggle `enabled` dari app dipertahankan; backup sebelum menulis. Aturan baru `10-shift-caps-lock-ctrl-opt-cmd`. Aturan hjio diberi nama baru `eezaatee · Semicolon layer…` (nama lama dimigrasi).
- **Hasil:** 8 unit test lulus, `karabiner_cli --lint-complex-modifications` ok. Sync dijalankan pada config live: Shift + Caps Lock ditaruh sebelum preset Hyper app, hjio dimigrasi di tempat, preset Hyper tidak berubah. Backup: `~/.config/karabiner/karabiner.json.bak.20261114-102204-244867`. Log Karabiner memuat config tanpa error. Assets dipasang di `~/.config/karabiner/assets/complex_modifications/`.
- **Belum diverifikasi:** tekan tombol fisik (Shift + Caps Lock + tombol) belum diuji agent; cek di Karabiner-EventViewer.
