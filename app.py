"""
Kevin's List - web backend

Flask API backed by Postgres, so the task list is saved to a real hosted
database (the "cloud") instead of a file sitting on the web service's own
disk. That distinction matters on hosts like Render's free tier: the web
service's local disk is not guaranteed to survive restarts, redeploys, or
moving to a different host, but a separate Postgres database is - your
data stays put even if the app service sleeps, wakes, or gets redeployed.

Local development falls back to a SQLite file (tasks.db) automatically if
the DATABASE_URL environment variable isn't set, so you don't need Postgres
running on your laptop just to test changes.

Run locally:
    pip install -r requirements.txt
    python app.py
Then visit http://localhost:5000

Deploy: create a Postgres database (Render's free Postgres add-on works),
set the DATABASE_URL environment variable on your web service to its
connection string, and deploy as usual.
"""

import os
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).parent
DATABASE_URL = os.environ.get("DATABASE_URL")
USING_POSTGRES = bool(DATABASE_URL)

app = Flask(__name__, static_folder="static", template_folder="templates")


# -------------------------
# DATABASE
# -------------------------
# Two backends: Postgres (production/cloud, when DATABASE_URL is set) and
# SQLite (local dev fallback). PH is the correct parameter placeholder for
# whichever one is active, so the route handlers below can stay identical
# for both.

if USING_POSTGRES:
    import psycopg2

    PH = "%s"

    def get_db():
        return psycopg2.connect(DATABASE_URL)

    def init_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                checked BOOLEAN NOT NULL DEFAULT FALSE,
                position INTEGER NOT NULL
            )
            """
        )
        conn.commit()
        cur.close()
        conn.close()

else:
    import sqlite3

    DB_FILE = BASE_DIR / "tasks.db"
    PH = "?"

    def get_db():
        conn = sqlite3.connect(DB_FILE)
        return conn

    def init_db():
        conn = get_db()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                position INTEGER NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()


def fetchall_dicts(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetchone_dict(cur):
    cols = [c[0] for c in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else None


def as_task(row):
    return {"id": row["id"], "text": row["text"], "checked": bool(row["checked"])}


# -------------------------
# ROUTES - FRONTEND
# -------------------------

@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


# -------------------------
# ROUTES - API
# -------------------------

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, text, checked FROM tasks ORDER BY position ASC")
    rows = fetchall_dicts(cur)
    cur.close()
    conn.close()

    return jsonify([as_task(r) for r in rows])


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(MAX(position), -1) FROM tasks")
    max_pos = cur.fetchone()[0]

    if USING_POSTGRES:
        cur.execute(
            f"INSERT INTO tasks (text, checked, position) VALUES ({PH}, FALSE, {PH}) RETURNING id",
            (text, max_pos + 1),
        )
        new_id = cur.fetchone()[0]
    else:
        cur.execute(
            f"INSERT INTO tasks (text, checked, position) VALUES ({PH}, 0, {PH})",
            (text, max_pos + 1),
        )
        new_id = cur.lastrowid

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": new_id, "text": text, "checked": False}), 201


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.cursor()

    if "text" in data:
        cur.execute(f"UPDATE tasks SET text = {PH} WHERE id = {PH}", (data["text"], task_id))

    if "checked" in data:
        checked_val = data["checked"] if USING_POSTGRES else (1 if data["checked"] else 0)
        cur.execute(f"UPDATE tasks SET checked = {PH} WHERE id = {PH}", (checked_val, task_id))

    conn.commit()

    cur.execute(f"SELECT id, text, checked FROM tasks WHERE id = {PH}", (task_id,))
    row = fetchone_dict(cur)
    cur.close()
    conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(as_task(row))


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM tasks WHERE id = {PH}", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return "", 204


@app.route("/api/tasks/reset", methods=["POST"])
def reset_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET checked = " + ("FALSE" if USING_POSTGRES else "0"))
    conn.commit()
    cur.close()
    conn.close()
    return "", 204


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
