# Cron template — the self-improving daily briefing

> A cron job that reads real work, identifies gaps, and patches skills. Replace
> the schedule and collector path with yours.

## Schedule

```
0 7 * * *    # every day at 07:00
```

## Prompt (self-contained — cron runs without chat context)

```
Buat daily briefing persiapan kerja. Ini briefing yang BIKIN AGENT MAKIN PINTER
(self-improving loop).

LANGKAH DATA GATHERING:
1. Jalankan telemetry collector: `bash ~/.hermes/scripts/work_prep_collector.sh`
   — git log 24 jam per repo, dirty WIP, server status, tunnel status. GUNAKAN DATA INI.
2. Jalankan session search (recent, newest) — konteks kerjaan 1-2 hari terakhir.
3. Cek skill library — apa yang ada, apa yang bisa di-improve.

STRUKTUR OUTPUT:
☀️ DAILY BRIEFING — [Hari, Tanggal]
**KEMAREN**
  • Rekap kerjaan REAL (git log 24h + sessions). 3-5 bullet.
**HARI INI**
  • Rencana kerja nyata. 3-4 bullet.
**SARAN (AGENTIC + SELF-IMPROVING)**
  • [P1] Task konkret hari ini — command exact, alasan, "tinggal bilang gas"
  • [P2] Skill/knowledge upgrade — apa yang agent kurang
  • [P3] Fix broken tooling — e.g. stale repo list di collector

SELF-IMPROVING ACTION:
- Kalau ketemu pelajaran/pola baru, PATCH skill yang relevan langsung.
- JANGAN klaim beres tanpa verifikasi (lihat auto-verify).
```

## Delivery

- Deliver to the owner's chat (Telegram/Discord).
- **Pin the job to a reliable provider + fallback** so it doesn't silently fail
  on a flaky default (see `patterns/model-routing.md`).

## Notes

- The collector `cron/scripts/work_prep_collector.sh` must point `ACTIVE_REPOS`
  at your repos.
- The briefing is allowed to act on its own suggestions (patch skills) — that's
  the self-improving loop.