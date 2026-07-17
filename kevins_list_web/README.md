# Kevin's List — Web / PWA version

Same CRT terminal look and feel as the Tkinter app, ported to the browser so
it can run on Android (and anywhere else) with real cloud saving.

## What changed vs. the desktop app

- **Storage**: tasks now live in a SQLite database on the server (`tasks.db`)
  instead of a local `save.json`. Any device that opens the site sees the
  same list.
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

Visit `http://localhost:5000` in a browser. On your phone, if it's on the
same Wi-Fi as your computer, visit `http://<your-computer's-LAN-IP>:5000`.

## Get real cloud saving (reachable from your phone anywhere)

Right now the server only runs on your machine. To access it from your phone
over the internet (not just local Wi-Fi), you need to host it somewhere.
Easiest free/cheap options, roughly in order of simplicity:

1. **Render.com** — connect a GitHub repo with these files, it detects Flask
   automatically. Free tier available (may sleep when idle).
2. **Railway.app** — similar one-click deploy from GitHub, free trial credit.
3. **PythonAnywhere** — free tier, good for small always-on Flask apps.
4. **Fly.io** — a bit more setup but a generous free tier and stays fast.

For any of these:
1. Push this folder to a GitHub repo.
2. Connect that repo to the host.
3. Set the start command to `python app.py` (or `gunicorn app:app` for a more
   production-ready server — `pip install gunicorn` and add it to
   `requirements.txt` if you go this route).
4. Once deployed, you'll get a URL like `https://kevins-list.onrender.com` —
   open that on your phone and "Add to Home Screen."

## Notes / next steps

- **No login yet** — anyone with the URL can see and edit the list. Fine for
  personal use on an unlisted URL; if you want it locked down, the next step
  is adding a simple password gate or real user accounts.
- **SQLite is fine for one person.** If this ever needs multiple users with
  separate lists, swap in Postgres (Render/Railway both offer free Postgres)
  and add a `user_id` column to the `tasks` table.
- The matrix-rain "all done" celebration and scanline effect are preserved
  from the original app.
