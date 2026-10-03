import os

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, g, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

# Keys match the response_type ENUM in the responses table.
CATEGORIES = {
    "favorite": "Favorite Games",
    "most_played": "Most Played",
    "currently_playing": "Currently Playing",
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
            database=os.getenv("DB_NAME", "GamingTrends"),
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


def get_platform_names():
    """All platform names stored in the platforms table."""
    cursor = get_db().cursor()
    cursor.execute("SELECT platform_name FROM platforms ORDER BY platform_name")
    names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return names


def top_games(category, limit, platform=None):
    """Return the ranked games for one category (optionally for one platform)."""
    cursor = get_db().cursor(dictionary=True)

    sql = """
        SELECT g.game_name AS game, COUNT(*) AS votes
        FROM responses AS r
        JOIN games AS g
            ON r.game_id = g.game_id
        JOIN submissions AS s
            ON r.submission_id = s.submission_id
        JOIN platforms AS p
            ON s.platform_id = p.platform_id
        WHERE r.response_type = %s
    """

    parameters = [category]

    if platform:
        sql += " AND p.platform_name = %s"
        parameters.append(platform)

    sql += """
        GROUP BY g.game_id, g.game_name
        ORDER BY votes DESC, g.game_name ASC
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


# ---------- Page routes ----------

@app.get("/")
def home():
    return render_template("index.html")


@app.get("/results")
def results_page():
    return render_template("results.html")


# ---------- API routes ----------

@app.get("/api/categories")
def list_categories():
    return jsonify([
        {"id": key, "title": title}
        for key, title in CATEGORIES.items()
    ])


@app.get("/api/platforms")
def list_platforms():
    return jsonify(get_platform_names())


@app.get("/api/games")
def list_games():
    """Every game in the database; the survey page uses this for suggestions."""
    cursor = get_db().cursor()
    cursor.execute("SELECT game_name FROM games ORDER BY game_name")
    names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return jsonify(names)


@app.get("/api/results")
def all_results():
    limit = read_limit()
    platform = request.args.get("platform", "").strip() or None

    if platform and platform not in get_platform_names():
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

    if platform and platform not in get_platform_names():
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
    """Save one submission (platform) plus three responses (one per category).

    Every game must already exist in the games table, otherwise the
    submission is rejected with an error naming the offending field.
    """
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

    labels = {
        "favorite": "Favorite game",
        "most_played": "Most-played game",
        "currently_playing": "Currently playing",
    }

    if not platform:
        return jsonify({
            "error": "Please select a platform",
            "field": "platform",
        }), 400

    for category, game in choices.items():
        if not game:
            return jsonify({
                "error": f"{labels[category]} is required",
                "field": category,
            }), 400

        if len(game) > 100:
            return jsonify({
                "error": f"{labels[category]} cannot exceed 100 characters",
                "field": category,
            }), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # 1. Platform must exist.
        cursor.execute(
            "SELECT platform_id FROM platforms WHERE platform_name = %s",
            (platform,),
        )
        platform_row = cursor.fetchone()

        if platform_row is None:
            return jsonify({
                "error": "Please select a valid platform",
                "field": "platform",
            }), 400

        # 2. Every game must exist in the games table.
        game_ids = {}

        for category, game in choices.items():
            cursor.execute(
                "SELECT game_id FROM games WHERE game_name = %s",
                (game,),
            )
            game_row = cursor.fetchone()

            if game_row is None:
                return jsonify({
                    "error": (
                        f'"{game}" is not in our game list. '
                        "Please choose a game from the suggestions."
                    ),
                    "field": category,
                }), 400

            game_ids[category] = game_row["game_id"]

        # 3. Save the submission and its three responses together.
        cursor.execute(
            "INSERT INTO submissions (platform_id) VALUES (%s)",
            (platform_row["platform_id"],),
        )
        submission_id = cursor.lastrowid

        cursor.executemany(
            """
            INSERT INTO responses (submission_id, game_id, response_type)
            VALUES (%s, %s, %s)
            """,
            [
                (submission_id, game_ids[category], category)
                for category in choices
            ],
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
