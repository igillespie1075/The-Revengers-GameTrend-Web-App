"""Account storage using the survey application's MySQL connection."""
from __future__ import annotations

from typing import Any
import mysql.connector
from ProjectBe import get_db


def initialize_account_tables():
    cursor = get_db().cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(32) NOT NULL UNIQUE,
                email VARCHAR(254) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                session_version INT NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_submissions (
                user_id INT NOT NULL,
                submission_id INT NOT NULL UNIQUE,
                PRIMARY KEY (user_id, submission_id),
                FOREIGN KEY (user_id) REFERENCES app_users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (submission_id) REFERENCES submissions(submission_id) ON DELETE CASCADE
            )
        """)
        get_db().commit()
    finally:
        cursor.close()


def find_user_by_id(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM app_users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def find_user_by_login(login):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM app_users WHERE username = %s OR email = %s", (login, login))
        return cursor.fetchone()
    finally:
        cursor.close()


def create_user(username, email, password_hash):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO app_users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash),
        )
        user_id = cursor.lastrowid
        db.commit()
        return user_id
    except mysql.connector.Error:
        db.rollback()
        raise
    finally:
        cursor.close()


def update_profile(user_id: int, username: str, email: str) -> None:
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE app_users SET username = %s, email = %s WHERE user_id = %s",
            (username, email, user_id),
        )
        db.commit()
    except mysql.connector.Error:
        db.rollback()
        raise
    finally:
        cursor.close()


def change_password(user_id: int, password_hash: str) -> int:
    """Change password and revoke other browser sessions via version increment."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE app_users SET password_hash = %s, "
            "session_version = session_version + 1 WHERE user_id = %s",
            (password_hash, user_id),
        )
        cursor.execute(
            "SELECT session_version FROM app_users WHERE user_id = %s",
            (user_id,),
        )
        version = cursor.fetchone()[0]
        db.commit()
        return version
    except mysql.connector.Error:
        db.rollback()
        raise
    finally:
        cursor.close()


def delete_user(user_id: int) -> None:
    """Remove account and ownership links; preserve anonymous survey totals."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
        db.commit()
    except mysql.connector.Error:
        db.rollback()
        raise
    finally:
        cursor.close()


def link_submission(user_id: int, submission_id: int) -> None:
    """Associate a successful submission with the authenticated account."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO account_submissions (user_id, submission_id) VALUES (%s, %s)",
            (user_id, submission_id),
        )
        db.commit()
    except mysql.connector.Error:
        db.rollback()
        raise
    finally:
        cursor.close()


def submission_history(user_id: int) -> list[dict[str, Any]]:
    """Return up to 100 latest owned surveys with original game choices."""
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.submission_id, s.created_at, p.platform_name AS platform,
                MAX(CASE WHEN r.response_type = 'favorite'
                    THEN gm.game_name END) AS favorite,
                MAX(CASE WHEN r.response_type = 'most_played'
                    THEN gm.game_name END) AS most_played,
                MAX(CASE WHEN r.response_type = 'currently_playing'
                    THEN gm.game_name END) AS currently_playing
            FROM account_submissions AS a
            JOIN submissions AS s ON a.submission_id = s.submission_id
            JOIN platforms AS p ON s.platform_id = p.platform_id
            LEFT JOIN responses AS r ON s.submission_id = r.submission_id
            LEFT JOIN games AS gm ON r.game_id = gm.game_id
            WHERE a.user_id = %s
            GROUP BY s.submission_id, s.created_at, p.platform_name
            ORDER BY s.created_at DESC, s.submission_id DESC
            LIMIT 100
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()

