import sqlite3
import difflib
import re
import os
from datetime import date
from flask import Flask, render_template, jsonify, request, redirect, url_for, abort

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "trivia.db")

DEFAULT_CATEGORIES = [
    "History", "Science", "Geography", "Arts & Culture",
    "Entertainment", "Sports", "Literature", "Music", "Technology", "Nature",
]


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn):
    """Create missing tables and columns on startup."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily_sets (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            theme   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id      INTEGER NOT NULL REFERENCES daily_sets(id) ON DELETE CASCADE,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """)

    # Add category_id column to daily_sets if it doesn't exist yet
    cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_sets)")]
    if "category_id" not in cols:
        conn.execute("ALTER TABLE daily_sets ADD COLUMN category_id INTEGER REFERENCES categories(id)")

    # Seed default categories if the table is empty
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        conn.executemany(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            [(c,) for c in DEFAULT_CATEGORIES],
        )

    conn.commit()


def get_all_sets(conn):
    sets = conn.execute("""
        SELECT ds.id, ds.theme, ds.category_id, c.name AS category_name
        FROM daily_sets ds
        LEFT JOIN categories c ON c.id = ds.category_id
        ORDER BY ds.id
    """).fetchall()
    result = []
    for s in sets:
        questions = conn.execute(
            "SELECT * FROM questions WHERE set_id = ? ORDER BY sort_order",
            (s["id"],),
        ).fetchall()
        result.append({
            "id": s["id"],
            "theme": s["theme"],
            "category_id": s["category_id"],
            "category_name": s["category_name"],
            "questions": questions,
        })
    return result


def get_today_set(conn):
    count = conn.execute("SELECT COUNT(*) FROM daily_sets").fetchone()[0]
    if count == 0:
        return None
    today = date.today()
    index = (today.year * 366 + today.timetuple().tm_yday) % count
    row = conn.execute("""
        SELECT ds.id, ds.theme, c.name AS category_name
        FROM daily_sets ds
        LEFT JOIN categories c ON c.id = ds.category_id
        ORDER BY ds.id LIMIT 1 OFFSET ?
    """, (index,)).fetchone()
    if not row:
        return None
    questions = conn.execute(
        "SELECT question, answer FROM questions WHERE set_id = ? ORDER BY sort_order",
        (row["id"],),
    ).fetchall()
    return {
        "theme": row["theme"],
        "category": row["category_name"],
        "questions": [dict(q) for q in questions],
    }


# ── Fuzzy matching ─────────────────────────────────────────────────────────────

def normalize(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def fuzzy_match(user_answer, correct_answer, threshold=0.65):
    user = normalize(user_answer)
    correct = normalize(correct_answer)
    if not user:
        return False
    if user == correct:
        return True
    user_words = user.split()
    correct_words = correct.split()
    if len(user_words) == 1 and user_words[0] in correct_words and len(user_words[0]) >= 4:
        return True
    if len(user_words) >= 2 and all(w in correct_words for w in user_words):
        return True
    return difflib.SequenceMatcher(None, user, correct).ratio() >= threshold


# ── Game routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/daily")
def get_daily():
    conn = get_db()
    puzzle = get_today_set(conn)
    conn.close()
    if not puzzle:
        return jsonify({"error": "No questions in database"}), 503
    return jsonify({
        "date": date.today().isoformat(),
        "theme": puzzle["theme"],
        "category": puzzle["category"],
        "questions": [q["question"] for q in puzzle["questions"]],
        "count": len(puzzle["questions"]),
    })


@app.route("/api/submit", methods=["POST"])
def submit():
    data = request.get_json()
    answers = data.get("answers", [])
    elapsed = data.get("elapsed", 0)

    conn = get_db()
    puzzle = get_today_set(conn)
    conn.close()
    if not puzzle:
        return jsonify({"error": "No questions in database"}), 503

    results = []
    for i, q in enumerate(puzzle["questions"]):
        user_ans = answers[i] if i < len(answers) else ""
        correct = fuzzy_match(user_ans, q["answer"])
        results.append({
            "correct": correct,
            "correct_answer": q["answer"],
            "user_answer": user_ans,
        })

    return jsonify({
        "results": results,
        "score": sum(1 for r in results if r["correct"]),
        "total": len(puzzle["questions"]),
        "elapsed": elapsed,
    })


# ── Admin: categories ──────────────────────────────────────────────────────────

@app.route("/admin")
def admin():
    conn = get_db()
    sets = get_all_sets(conn)
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return render_template("admin.html", sets=sets, categories=categories)


@app.route("/admin/category/new", methods=["POST"])
def admin_new_category():
    name = request.form.get("name", "").strip()
    if not name:
        abort(400)
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin") + "#categories")


@app.route("/admin/category/<int:cat_id>/delete", methods=["POST"])
def admin_delete_category(cat_id):
    conn = get_db()
    # Unlink any sets using this category before deleting
    conn.execute("UPDATE daily_sets SET category_id = NULL WHERE category_id = ?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin") + "#categories")


# ── Admin: sets ────────────────────────────────────────────────────────────────

@app.route("/admin/set/new", methods=["POST"])
def admin_new_set():
    theme = request.form.get("theme", "").strip()
    category_id = request.form.get("category_id") or None
    if not theme:
        abort(400)
    conn = get_db()
    conn.execute(
        "INSERT INTO daily_sets (theme, category_id) VALUES (?, ?)",
        (theme, category_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/set/<int:set_id>/edit", methods=["POST"])
def admin_edit_set(set_id):
    theme = request.form.get("theme", "").strip()
    category_id = request.form.get("category_id") or None
    if not theme:
        abort(400)
    conn = get_db()
    conn.execute(
        "UPDATE daily_sets SET theme = ?, category_id = ? WHERE id = ?",
        (theme, category_id, set_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin") + f"#set-{set_id}")


@app.route("/admin/set/<int:set_id>/delete", methods=["POST"])
def admin_delete_set(set_id):
    conn = get_db()
    conn.execute("DELETE FROM daily_sets WHERE id = ?", (set_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


# ── Admin: questions ───────────────────────────────────────────────────────────

@app.route("/admin/set/<int:set_id>/question/new", methods=["POST"])
def admin_new_question(set_id):
    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()
    if not question or not answer:
        abort(400)
    conn = get_db()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) FROM questions WHERE set_id = ?", (set_id,)
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO questions (set_id, sort_order, question, answer) VALUES (?, ?, ?, ?)",
        (set_id, max_order + 1, question, answer),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin") + f"#set-{set_id}")


@app.route("/admin/question/<int:q_id>/edit", methods=["POST"])
def admin_edit_question(q_id):
    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()
    if not question or not answer:
        abort(400)
    conn = get_db()
    row = conn.execute("SELECT set_id FROM questions WHERE id = ?", (q_id,)).fetchone()
    conn.execute(
        "UPDATE questions SET question = ?, answer = ? WHERE id = ?",
        (question, answer, q_id),
    )
    conn.commit()
    set_id = row["set_id"]
    conn.close()
    return redirect(url_for("admin") + f"#set-{set_id}")


@app.route("/admin/question/<int:q_id>/delete", methods=["POST"])
def admin_delete_question(q_id):
    conn = get_db()
    row = conn.execute("SELECT set_id FROM questions WHERE id = ?", (q_id,)).fetchone()
    conn.execute("DELETE FROM questions WHERE id = ?", (q_id,))
    conn.commit()
    set_id = row["set_id"] if row else None
    conn.close()
    return redirect(url_for("admin") + (f"#set-{set_id}" if set_id else ""))


# ── Startup ────────────────────────────────────────────────────────────────────

with app.app_context():
    conn = get_db()
    migrate(conn)
    # Auto-seed if database is empty
    if conn.execute("SELECT COUNT(*) FROM daily_sets").fetchone()[0] == 0:
        import seed as _seed
        _seed.seed(conn)
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)
