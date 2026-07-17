# Kevin's List — Web / PWA version

Same CRT terminal look and feel as the Tkinter app, ported to the browser so
it can run on Android (and anywhere else) with real cloud saving.

## What changed vs. the desktop app

- **Storage**: tasks are saved to a real hosted **Postgres database**
  (falls back to a local SQLite file automatically when `DATABASE_URL`
  isn't set, so local dev needs no setup). This matters specifically
  because a free-tier host's own disk isn't guaranteed to persist — a
  separate database keeps your data safe independent of the app service
  sleeping, waking, or getting redeployed.
- **UI**: the Tkinter widgets are now HTML/CSS/JS, styled to match — black
  background, `#FC6A03` orange, scanline overlay, boot-sequence typing intro,
  and the matrix rain celebration when every task is checked off.
- **Installable**: it's a Progressive Web App (PWA). On Android, open it in
  Chrome and use "Add to Home Screen" to get an app icon and full-screen
  window like a native app.

## Run it locally

```bash
cd kevins_list_web
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000` in a browser. No database setup needed —
without a `DATABASE_URL` set, it automatically uses a local `tasks.db`
SQLite file, which is fine for testing.

## Deploy with real, persistent cloud storage (Render)

1. **Push this folder to a GitHub repo** and connect it to Render as a Web
   Service. This repo includes a `.python-version` file pinning Python to
   `3.12.3` — Render reads this automatically, which matters because
   `psycopg2-binary`'s precompiled wheel isn't yet built for very new Python
   releases. As a belt-and-suspenders backup, you can also set an
   environment variable `PYTHON_VERSION` = `3.12.3` on the service itself
   (Render's dashboard → Environment) — either one should pin it.
2. **Create a Postgres database on Render** (Render dashboard → New →
   Postgres, free tier is fine). Render gives you an **Internal Database
   URL** — copy it.
3. On your **web service**, go to Environment and add:
   - Key: `DATABASE_URL`
   - Value: the Postgres connection string from step 2
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `gunicorn app:app`
6. Deploy. On first request, the app automatically creates the `tasks`
   table if it doesn't exist yet.

From then on, your task data lives in the Postgres database, not on the web
service's disk — so the web service sleeping, waking, restarting, or even
being redeployed from scratch won't touch your saved tasks. Once deployed,
open the URL (e.g. `https://kevins-list.onrender.com`) on your phone or PC
and install it as an app.

## Notes / next steps

- **No login yet** — anyone with the URL can see and edit the list. Fine for
  personal use on an unlisted URL; if you want it locked down, the next step
  is adding a simple password gate or real user accounts.
- **Free-tier Postgres databases usually expire after a set period** (check
  Render's current free-tier terms) — for a truly long-lived personal app,
  budget for the small paid tier eventually, or migrate to another free
  Postgres provider (e.g. Supabase, Neon) if that happens.
- If this ever needs multiple users with separate lists, add a `user_id`
  column to the `tasks` table and filter queries by it.
- The matrix-rain "all done" celebration and scanline effect are preserved
  from the original app.
