"""
Kevin's List - web backend
Simple Flask + SQLite API so the task list can be saved to a server
(the "cloud") instead of a local save.json file, and read back from
any device - including a phone browser / installed PWA.

Run locally:
    pip install -r requirements.txt
    python app.py
Then visit http://localhost:5000

Deploy anywhere that runs Python (Render, Railway, Fly.io, PythonAnywhere,
a $5 VPS, etc.) to get real cloud saving reachable from your Android phone.
"""

from flask import Flask, jsonify, request, send_from_directory
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "tasks.db"

app = Flask(__name__, static_folder="static", template_folder="templates")


# -------------------------
# DATABASE
# -------------------------

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
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
    rows = conn.execute(
        "SELECT id, text, checked FROM tasks ORDER BY position ASC"
    ).fetchall()
    conn.close()

    return jsonify(
        [{"id": r["id"], "text": r["text"], "checked": bool(r["checked"])} for r in rows]
    )


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    conn = get_db()
    max_pos = conn.execute("SELECT COALESCE(MAX(position), -1) AS m FROM tasks").fetchone()["m"]
    cur = conn.execute(
        "INSERT INTO tasks (text, checked, position) VALUES (?, 0, ?)",
        (text, max_pos + 1),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"id": new_id, "text": text, "checked": False}), 201


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json(force=True)
    conn = get_db()

    if "text" in data:
        conn.execute("UPDATE tasks SET text = ? WHERE id = ?", (data["text"], task_id))

    if "checked" in data:
        conn.execute(
            "UPDATE tasks SET checked = ? WHERE id = ?",
            (1 if data["checked"] else 0, task_id),
        )

    conn.commit()
    row = conn.execute(
        "SELECT id, text, checked FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify({"id": row["id"], "text": row["text"], "checked": bool(row["checked"])})


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return "", 204


@app.route("/api/tasks/reset", methods=["POST"])
def reset_tasks():
    conn = get_db()
    conn.execute("UPDATE tasks SET checked = 0")
    conn.commit()
    conn.close()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
else:
    init_db()
