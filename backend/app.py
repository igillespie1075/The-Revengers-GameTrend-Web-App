# backend for gaming trends site
# run with: python app.py
# then go to http://localhost:5000/api/results

import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

DB = "votes.db"

categories = {
    "favorite": "Favorite Games",
    "most_played": "Most Played",
    "currently_playing": "Currently Playing",
}

# fake votes so theres something to show for now
sample_votes = {
    "favorite": {"Roblox": 14, "Minecraft": 11, "Valorant": 8, "Fortnite": 5},
    "most_played": {"Minecraft": 17, "Fortnite": 12, "GTA V": 9, "Roblox": 6},
    "currently_playing": {"Fortnite": 13, "Minecraft": 10, "Valorant": 7, "Rocket League": 4},
}


def setup_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS votes (id INTEGER PRIMARY KEY, category TEXT, game TEXT)")

    # only add the fake votes if the table is empty
    count = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    if count == 0:
        for category in sample_votes:
            for game in sample_votes[category]:
                for i in range(sample_votes[category][game]):
                    conn.execute("INSERT INTO votes (category, game) VALUES (?, ?)", (category, game))
        print("added sample votes")

    conn.commit()
    conn.close()


def get_top_games(category, limit):
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT game, COUNT(*) FROM votes WHERE category = ? GROUP BY game ORDER BY COUNT(*) DESC LIMIT ?",
        (category, limit),
    ).fetchall()
    conn.close()

    results = []
    rank = 1
    for row in rows:
        results.append({"rank": rank, "game": row[0], "votes": row[1]})
        rank += 1
    return results


# lets the html page call the api without getting blocked
@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# top games for every category
@app.route("/api/results")
def all_results():
    limit = int(request.args.get("limit", 3))
    data = []
    for category in categories:
        data.append({
            "category": category,
            "title": categories[category],
            "results": get_top_games(category, limit),
        })
    return jsonify(data)


# top games for just one category
@app.route("/api/results/<category>")
def one_result(category):
    if category not in categories:
        return jsonify({"error": "category not found"}), 404
    limit = int(request.args.get("limit", 3))
    return jsonify({
        "category": category,
        "title": categories[category],
        "results": get_top_games(category, limit),
    })


# add a vote, send json like {"category": "favorite", "game": "Minecraft"}
@app.route("/api/votes", methods=["POST"])
def add_vote():
    data = request.get_json()
    category = data.get("category")
    game = data.get("game")

    if category not in categories or not game:
        return jsonify({"error": "need a valid category and game"}), 400

    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO votes (category, game) VALUES (?, ?)", (category, game))
    conn.commit()
    conn.close()
    return jsonify({"message": "vote added"}), 201


if __name__ == "__main__":
    setup_db()
    app.run(debug=True)