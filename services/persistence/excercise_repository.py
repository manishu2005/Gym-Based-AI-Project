import sqlite3
import streamlit as st
from pathlib import Path

__DB_PATH = str(Path(__file__).parent.parent.parent / "data.db")


@st.cache_resource
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(__DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db()-> None:
    conn = _get_connection()

    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE NOT NULL,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )
""")

        user_columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "name" in user_columns and "username" not in user_columns:
            conn.execute("ALTER TABLE users RENAME COLUMN name TO username")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS excercises(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER NOT NULL REFERENCES users(id),
                     excercise_name TEXT NOT NULL,
                     reps INTEGER NOT NULL DEFAULT 0,
                     sets INTEGER NOT NULL DEFAULT 0,
                     time INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )
""")
        

def get_user(username)->sqlite3.Row:
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM users WHERE username = ?
""", (username,)).fetchone()

def create_user(username)->sqlite3.Row:
    conn = _get_connection()

    with conn:
        conn.execute("""
        INSERT INTO users (username) VALUES (?)
""", (username,))
        
        return get_user(username)


def get_or_create_user(username)->sqlite3.Row:
    user = get_user(username)

    if user is None:
        user = create_user(username)
    
    return user


def add_excercise(user_id, excercise_name, reps, sets, time):
    conn = _get_connection()

    with conn:
        existing = conn.execute("""
        SELECT * FROM excercises
        WHERE user_id = ? AND excercise_name = ? AND DATE(created_at) = DATE('now')
""", (user_id, excercise_name)).fetchone()
        
        if existing:
            conn.execute("""
            UPDATE excercises
            SET reps = reps + ?, sets = sets + ?, time = time + ?
            WHERE id = ?
""", (reps, sets, time, existing["id"]))
            
        else:
            conn.execute("""
            INSERT INTO excercises (user_id, excercise_name, reps, sets, time)
                         VALUES (?,?,?,?,?)
""", (user_id, excercise_name, reps, sets, time))
            

def _get_users_excercises(user_id):
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM excercises
        WHERE user_id = ?
""", (user_id,)).fetchall()
