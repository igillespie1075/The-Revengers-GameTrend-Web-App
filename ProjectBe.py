import os
import uuid

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

CATEGORIES = {
    "favorite": "Favorite Games",
    "most_played": "Most Played",
    "currently_playing": "Currently Playing",
}

PLATFORMS = {
    "PC",
    "PlayStation",
    "Xbox",
    "Nintendo Switch",
    "Mobile",
}


# ---------- Database helpers ----------

def get_db():
    """Open one MySQL connection per request and reuse it."""
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "gaming_trends"),
        )

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None and db.is_connected():
        db.close()


def read_limit():
    """Read ?limit= from the URL; default 3, minimum 1, maximum 50."""
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        limit = 3

    return max(1, min(limit, 50))


def top_games(category, limit, platform=None):
    """Return the ranked games for one category."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT game, COUNT(*) AS votes
        FROM votes
        WHERE category = %s
    """

    parameters = [category]

    if platform:
        sql += " AND platform = %s"
        parameters.append(platform)

    sql += """
        GROUP BY game
        ORDER BY votes DESC, game ASC
        LIMIT %s
    """

    parameters.append(limit)

    cursor.execute(sql, tuple(parameters))
    rows = cursor.fetchall()
    cursor.close()

    return [
        {
            "rank": index + 1,
            "game": row["game"],
            "votes": row["votes"],
        }
        for index, row in enumerate(rows)
    ]


# ---------- API routes ----------

@app.get("/")
def home():
    return render_template("index.html")


@app.get("/results")
def results_page():
    return render_template("results.html")


@app.get("/api/categories")
def list_categories():
    return jsonify([
        {"id": key, "title": title}
        for key, title in CATEGORIES.items()
    ])


@app.get("/api/platforms")
def list_platforms():
    return jsonify(sorted(PLATFORMS))


@app.get("/api/results")
def all_results():
    limit = read_limit()
    platform = request.args.get("platform", "").strip() or None

    if platform and platform not in PLATFORMS:
        return jsonify({"error": "Unknown platform"}), 400

    results = [
        {
            "category": key,
            "title": title,
            "results": top_games(key, limit, platform),
        }
        for key, title in CATEGORIES.items()
    ]

    return jsonify({
        "platform": platform or "All platforms",
        "categories": results,
    })


@app.get("/api/results/<category>")
def one_result(category):
    if category not in CATEGORIES:
        return jsonify({
            "error": f"Unknown category '{category}'"
        }), 404

    platform = request.args.get("platform", "").strip() or None

    if platform and platform not in PLATFORMS:
        return jsonify({"error": "Unknown platform"}), 400

    return jsonify({
        "category": category,
        "title": CATEGORIES[category],
        "platform": platform or "All platforms",
        "results": top_games(
            category,
            read_limit(),
            platform,
        ),
    })


@app.post("/api/responses")
def add_response():
    """Save platform and three game selections as one submission."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    platform = str(data.get("platform", "")).strip()

    choices = {
        "favorite": str(data.get("favorite", "")).strip(),
        "most_played": str(data.get("most_played", "")).strip(),
        "currently_playing": str(
            data.get("currently_playing", "")
        ).strip(),
    }

    if platform not in PLATFORMS:
        return jsonify({
            "error": "Please select a valid platform"
        }), 400

    for category, game in choices.items():
        if not game:
            return jsonify({
                "error": f"{category} is required"
            }), 400

        if len(game) > 100:
            return jsonify({
                "error": f"{category} cannot exceed 100 characters"
            }), 400

    submission_id = str(uuid.uuid4())

    rows = [
        (submission_id, platform, category, game)
        for category, game in choices.items()
    ]

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.executemany(
            """
            INSERT INTO votes (
                submission_id,
                platform,
                category,
                game
            )
            VALUES (%s, %s, %s, %s)
            """,
            rows,
        )

        db.commit()

    except mysql.connector.Error:
        db.rollback()

        return jsonify({
            "error": "The response could not be saved"
        }), 500

    finally:
        cursor.close()

    return jsonify({
        "message": "Response recorded",
        "submission_id": submission_id,
    }), 201


# This is acceptable for a local class prototype.
# Restrict the permitted origin before publicly deploying it.
@app.after_request
def allow_frontend(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)