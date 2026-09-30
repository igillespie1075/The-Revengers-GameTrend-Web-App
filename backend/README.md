# Gaming Trends – Backend

A small Python/Flask API that stores votes in SQLite (`votes.db`, created automatically with sample data on first run).

## Run it

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000/api/results

To reset the data, stop the server, delete `votes.db`, and start it again.

## Endpoints

| Method | URL | What it does |
|---|---|---|
| GET | `/api/results` | Top 3 games for every category |
| GET | `/api/results/<category>` | Top 3 for one category (`favorite`, `most_played`, `currently_playing`) |
| GET | `/api/categories` | List of categories |
| POST | `/api/votes` | Add a vote. Body: `{"category": "favorite", "game": "Minecraft"}` |

Add `?limit=5` to either results URL to get more than 3.

Example response from `/api/results/favorite`:

```json
{
  "category": "favorite",
  "title": "Favorite Games",
  "results": [
    {"rank": 1, "game": "Roblox", "votes": 14},
    {"rank": 2, "game": "Minecraft", "votes": 11},
    {"rank": 3, "game": "Valorant", "votes": 8}
  ]
}
```

## Hooking up the results page

Add this before `</body>` in the results HTML. It replaces the hardcoded cards with live data (keep the server running):

```html
<script>
  fetch("http://localhost:5000/api/results")
    .then(res => res.json())
    .then(categories => {
      const container = document.querySelector(".mock_results");
      container.innerHTML = categories.map(cat => `
        <div class="card">
          <h2>${cat.title}</h2>
          ${cat.results.map(r => `
            <div class="game">
              <span class="rank">${r.rank}. ${r.game}</span>
              <span class="count">${r.votes} votes</span>
            </div>`).join("")}
        </div>`).join("");
    });
</script>
```