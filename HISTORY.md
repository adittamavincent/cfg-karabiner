# Riwayat cfg-karabiner

## 2026-11-14T10:50+07:00 — Shift + Caps Lock diverifikasi dengan tombol fisik

- **Permintaan:** Vincent menguji Shift + Caps Lock dan bertanya kenapa recorder Raycast menampilkan "Shift + L".
- **Hasil:** Karabiner-EventViewer (Capture Input Events) menunjukkan Shift dilepas, lalu ⌘ ⌥ ⌃ ditekan, dan `l` keluar dengan flags `left_command, left_control, left_option` tanpa Shift. Keyboard Viewer macOS juga menampilkan ⌃⌥⌘. Output aturan benar.
- **Catatan:** Tampilan "Shift + L" di recorder Raycast berasal dari Raycast, bukan dari aturan ini. Penyebab di Raycast belum dipastikan (kandidat: Hyper Key bawaan Raycast, lampu Caps Lock menyala, atau tampilan recorder).

## 2026-11-14T10:40+07:00 — Rename to cfg-karabiner

- **Permintaan:** Vincent meminta nama repo (lokal dan GitHub) mengikuti praktik baik dengan prefix yang menunjukkan ini konfigurasi untuk program lain.
- **Dikerjakan:** GitHub `adittamavincent/eezaatee-fav-karabiner` diganti nama menjadi `adittamavincent/cfg-karabiner` (GitHub mengalihkan URL lama). Folder lokal dipindah ke `TOOLS/I-Built/cfg-karabiner`, remote `origin` diperbarui. `dist/` dan file assets Karabiner diganti nama menjadi `cfg-karabiner.json`. Aturan penamaan `cfg-<target-program>` dicatat di `AGENTS.md` root, `TOOLS/I-Built/AGENTS.md` dan repo ini. Deskripsi aturan `eezaatee ·` tidak diubah agar toggle di app tetap cocok.
- **Hasil:** Test, lint dan `build --check` lulus; `sync --dry-run` hanya mengganti aturan sendiri. Branch belum di-push.

## 2026-11-14T10:25+07:00 — Modular rules, app-preset aware sync, Shift + Caps Lock

- **Permintaan:** Vincent meminta repo hjio dari Meaw dibangun ulang di `TOOLS/I-Built`, dengan aturan kustom terpisah yang menghormati preset bawaan app Karabiner (misalnya Hyper Key), plus fitur Shift + Caps Lock → Control + Option + Command.
- **Dikerjakan:** Clone dari `/Volumes/Meaw/code-repos-25-10-2026/projects/eezaatee-fav-karabiner` (HEAD `dc8a6b0`, sama dengan GitHub `origin/main`). `karabiner.json` penuh diganti `rules/*.json` (satu aturan per file). `sync_karabiner.py` ditulis ulang: subcommand `sync`, `remove`, `status`, `build`, `install-assets`; kepemilikan lewat deskripsi persis + `legacy_descriptions`; placement `before-overlaps` / `append`; toggle `enabled` dari app dipertahankan; backup sebelum menulis. Aturan baru `10-shift-caps-lock-ctrl-opt-cmd`. Aturan hjio diberi nama baru `eezaatee · Semicolon layer…` (nama lama dimigrasi).
- **Hasil:** 8 unit test lulus, `karabiner_cli --lint-complex-modifications` ok. Sync dijalankan pada config live: Shift + Caps Lock ditaruh sebelum preset Hyper app, hjio dimigrasi di tempat, preset Hyper tidak berubah. Backup: `~/.config/karabiner/karabiner.json.bak.20261114-102204-244867`. Log Karabiner memuat config tanpa error. Assets dipasang di `~/.config/karabiner/assets/complex_modifications/`.
- **Belum diverifikasi:** tekan tombol fisik (Shift + Caps Lock + tombol) belum diuji agent; cek di Karabiner-EventViewer.
