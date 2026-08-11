# Auto-Verify Fix — Analysis & Plan

## 🔍 Analisa Kekurangan (terverifikasi, bukan asumsi)

**1. `_overall()` = DEAD CODE** — didefinisikan (line 161) tapi **gak pernah dipanggil**. Rencananya buat rekap count tapi nggak kepake.

**2. HTTP 200 ≠ beneran bener (limitasi konseptual terbesar)**
Hook cuma cek status code via curl. Service bisa return 200 tapi logic rusak. Ini batas desain "smoke test" — gak bisa jadi functional check tanpa effort besar.

**3. Deteksi project lewat nama doang**
Cuma nangkep kalau task nyebut nama project. `"gas beresin bug itu"` (tanpa nama) → fallback cek ≤5 project dengan port (shotgun, bukan presisi).

**4. Alias matching kelonggaran → false positive**
`_discover_projects()` nambah tiap part slug ≥3 huruf jadi alias. `"skill-arena"` → alias `skill`, `arena`. Bisa ke-match kata gak nyambung.

**5. Log scan global, gak per-project**
Scan seluruh `agent.log` 2 jam, gak filter per project. Error project lain ikut ke-flag.

**6. Pesan dev-only ngasumsi waktu** — `"off malam ini — normal"` ngasumsi lagi malam. Seharusnya netral.

**7. Test cuma cek source text, gak test behavior**
Test cek substring (`_discover_projects` ada di source), gak verify `_detect_targets()`/`_check_project()` beneran menghasilkan output yang bener.

---

## 🛠️ Rencana Perbaikan (urutan prioritas)

### Fix 1 — Behavior tests (priority: HIGH)
Bikin test yang **jalankan fungsi beneran**, bukan cek source text:
- `_detect_targets()` — kasih message nyebut project → harus balik project itu
- `_detect_targets()` — message gak nyebut → balik kosong (fallback)
- `_check_project()` — pastiin bikin output (ok/warn) yang valid
- Cooldown logic
- Hapus test substring yang gak bermakna, ganti behavior test yang konkret

**Riset:** apakah handler bisa di-import test (dependencies = os, re, httpx hanya di handle). Verify `_detect_targets` dan `_check_project` bisa di-unit-test tanpa network.

### Fix 2 — Hapus dead code `_overall()` (priority: MEDIUM)
- Hapus fungsi `_overall()` yang gak dipakai.
- Kalau mau rekap count, inisert langsung di `handle()` (satu baris, bukan fungsi terpisah).

### Fix 3 — Rapikan pesan & alias (priority: MEDIUM)
- **Pesan dev-only netral:** `"off (dev-only — normal)"` — buang asumsi "malam ini".
- **Tighten alias:** jangan nambah tiap part ≥3 huruf. Cuma nama project + slug penuh + nama dari collector (bukan part per-part). Kurangi false positive.

### Fix 4 — Log scan per-project (priority: LOW, butuh design)
- Filter log error biar relevan ke project target. Tapi format `agent.log` gak selalu nyebut project → ini limitasi. Opsi: scan global tapi tampilkan ringkas (tetap sebagai "overall health", orang tau itu global).

### Fix 5 — Functional check (priority: TIDAK DILAKUKAN sekarang)
- Ini butuh effort besar (browser/visual/unit-test per project) & gak masuk scope "auto-verify hook". Dicatat sebagai batas desain di README, bukan dibangun sekarang.

---

## 📋 Approval Gate

Nunggu ACC user sebelum eksekusi. Scope yang di-eksekusi:
- ✅ Fix 1 (behavior tests)
- ✅ Fix 2 (buang dead code)
- ✅ Fix 3 (rapikan pesan + alias)
- ⏸️ Fix 4 (log per-project — cuma rapikan framing, bukan rewrite)
- ❌ Fix 5 (functional check — TIDAK, dicatat sebagai batas)

Setelah fix: run `python3 -m unittest discover tests`, sync live handler, commit repo.
