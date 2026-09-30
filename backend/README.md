# Backend

Flask backend for the gaming trends site. Votes get saved in a sqlite file (votes.db) that gets made the first time you run it, with some fake votes in it for now.

## How to run

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then go to http://localhost:5000/api/results

If you want to reset the votes just delete votes.db and run it again.

## Routes

- `/api/results` - top 3 games for each category
- `/api/results/favorite` - top 3 for one category (can also be `most_played` or `currently_playing`)
- add `?limit=5` to the end to get more than 3
- `POST /api/votes` - adds a vote, send json like `{"category": "favorite", "game": "Minecraft"}`