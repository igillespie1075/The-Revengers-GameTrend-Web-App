"""
Gaming Trends - backend API (Flask + SQLite)

Run it:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000/api/results in your browser.

Endpoints:
    GET  /api/results                 -> top games for every category
    GET  /api/results/<category>      -> top games for one category
    POST /api/votes                   -> add a vote  (JSON: {"category": "...", "game": "..."})
    GET  /api/categories              -> list of valid categories

Optional query param on the results endpoints:  ?limit=5  (default 3)
"""

import os
import sqlite3

from flask import Flask, g, jsonify, request

app = Flask(__name__)

# The database is a single file that sits next to this script.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "votes.db")

# The three cards on the results page. Key = what the API uses, value = display title.
CATEGORIES = {
    "favorite": "Favorite Games",
    "most_played": "Most Played",
    "currently_playing": "Currently Playing",
}

# Sample votes so the API has something to show before real voting exists.
# Format: category -> {game: number_of_votes}
SAMPLE_VOTES = {
    "favorite": {"Roblox": 14, "Minecraft": 11, "Valorant": 8, "Fortnite": 5},
    "most_played": {"Minecraft": 17, "Fortnite": 12, "GTA V": 9, "Roblox": 6},
    "currently_playing": {"Fortnite": 13, "Minecraft": 10, "Valorant": 7, "Rocket League": 4},
}

# ---------- Database helpers ----------

def get_db():
    """Open one database connection per request and reuse it."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # lets us read columns by name
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Create the votes table, and fill it with sample data if it's empty."""
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            category   TEXT NOT NULL,
            game       TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    (count,) = db.execute("SELECT COUNT(*) FROM votes").fetchone()
    if count == 0:
        rows = [
            (category, game)
            for category, games in SAMPLE_VOTES.items()
            for game, n in games.items()
            for _ in range(n)
        ]
        db.executemany("INSERT INTO votes (category, game) VALUES (?, ?)", rows)
        print(f"Seeded database with {len(rows)} sample votes.")
    db.commit()
    db.close()

def top_games(category, limit):
    """Return [{rank, game, votes}, ...] for one category, most votes first."""
    rows = get_db().execute(
        """
        SELECT game, COUNT(*) AS votes
        FROM votes
        WHERE category = ?
        GROUP BY game
        ORDER BY votes DESC, game ASC
        LIMIT ?
        """,
        (category, limit),
    ).fetchall()
    return [
        {"rank": i + 1, "game": row["game"], "votes": row["votes"]}
        for i, row in enumerate(rows)
    ]

def read_limit():
    """Read ?limit= from the URL (default 3, between 1 and 50)."""
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        limit = 3
    return max(1, min(limit, 50))

# ---------- API routes ----------

@app.get("/api/categories")
def list_categories():
    return jsonify([{"id": k, "title": v} for k, v in CATEGORIES.items()])

@app.get("/api/results")
def all_results():
    limit = read_limit()
    return jsonify(
        [
            {"category": key, "title": title, "results": top_games(key, limit)}
            for key, title in CATEGORIES.items()
        ]
    )

@app.get("/api/results/<category>")
def one_result(category):
    if category not in CATEGORIES:
        return jsonify({"error": f"Unknown category '{category}'"}), 404
    return jsonify(
        {
            "category": category,
            "title": CATEGORIES[category],
            "results": top_games(category, read_limit()),
        }
    )

@app.post("/api/votes")
def add_vote():
    data = request.get_json(silent=True) or {}
    category = str(data.get("category", "")).strip()
    game = str(data.get("game", "")).strip()

    if category not in CATEGORIES:
        return jsonify({"error": "category must be one of: " + ", ".join(CATEGORIES)}), 400
    if not game or len(game) > 100:
        return jsonify({"error": "game is required (max 100 characters)"}), 400

    db = get_db()
    db.execute("INSERT INTO votes (category, game) VALUES (?, ?)", (category, game))
    db.commit()
    return jsonify({"message": "Vote recorded", "category": category, "game": game}), 201

# Allow the HTML page to call the API even if it's opened as a file or from another port.
@app.after_request
def allow_frontend(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)