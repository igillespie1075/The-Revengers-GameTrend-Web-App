"""Drop-in launcher for The-Revengers-GameTrend-Web-App.

Place alongside ProjectBe.py and run THIS file instead of ProjectBe.py:
    python run_with_accounts.py

The original ProjectBe.py, templates, static assets and survey APIs are unchanged.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from ProjectBe import app  # noqa: E402 (load .env before importing the app)
from account_db import initialize_account_tables  # noqa: E402
from account_routes import register_account_features  # noqa: E402

register_account_features(app)


def initialize():
    # Use the same database connection/settings as ProjectBe.py.
    with app.app_context():
        initialize_account_tables()


if __name__ == "__main__":
    initialize()
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
