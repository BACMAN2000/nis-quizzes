# NIS English — Quizzes

Cambridge-format practice quizzes for Nordic International School of Lima (A2 · B1 · B2 · C1), styled like the Inspera test player.

## Apps
- **`quizzes.html`** — hub linking the three quizzes.
- **`listening-quiz.html`** — Listening (A2/B1 browser voice, B2/C1 real audio in `mp3/`).
- **`reading-quiz.html`** — Reading (KET/PET/FCE/CAE format) with timer; A2 also includes Writing Parts 6/7.
- **`writing-quiz.html`** — Writing (B1/B2/C1): Part 1 compulsory + Part 2 choose-one, with offline rubric auto-assessment.

## Live (GitHub Pages)
https://bacman2000.github.io/nis-quizzes/

## Deploy
Push to `main` → GitHub Pages rebuilds (~1–2 min). **Bump the `version` in `version.json`** (format `YYYY-MM-DD-N`) on every deploy so students auto-load the latest version without clearing their cache.

## Notes
- Writing is auto-assessed offline (Content / Organisation / Language, each 0–5). It's an estimate; the teacher may adjust it.
- Results post to the configured Apps Script webhook and can be downloaded as PDF.
