# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sqlite3
from typing import List, Dict, Any, Optional

class DatabaseAdapter:
    """
    Adapter to switch database backends dynamically.
    If DATABASE_URL environment variable is set, routes queries to PostgreSQL.
    Otherwise, defaults to local SQLite file system.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.use_postgres = False
        self.db_url = os.environ.get("DATABASE_URL")
        if self.db_url:
            try:
                import psycopg2
                import psycopg2.extras
                self.use_postgres = True
            except ImportError:
                pass

    def get_connection(self):
        if self.use_postgres:
            import psycopg2
            import psycopg2.extras
            # Configure psycopg2 to use RealDictCursor natively on all connections
            conn = psycopg2.connect(self.db_url, cursor_factory=psycopg2.extras.RealDictCursor)
            return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def get_cursor(self, conn):
        if self.use_postgres:
            import psycopg2.extras
            return conn.cursor()
        else:
            return conn.cursor()

    def execute(self, cursor, query: str, params: tuple = ()) -> None:
        """
        Executes query on the cursor.
        Translates SQLite syntax to PostgreSQL syntax at runtime.
        """
        if self.use_postgres:
            # Translate positional parameters from '?' (SQLite) to '%s' (PostgreSQL)
            query = query.replace("?", "%s")
            # Translate SQLite functions
            query = query.replace("date('now')", "CURRENT_DATE")
        cursor.execute(query, params)

def get_connection(db_path: str):
    """Global backward-compatible connection factory helper."""
    adapter = DatabaseAdapter(db_path)
    return adapter.get_connection()

def init_db(db_path: str) -> None:
    """Initializes schema tables on the active database engine."""
    adapter = DatabaseAdapter(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        
        if adapter.use_postgres:
            # PostgreSQL Syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    academic_level TEXT NOT NULL,
                    mastery_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS academic_milestones (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    grade REAL DEFAULT 0.0,
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS athletic_metrics (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    session_type TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    intensity_rpe INTEGER NOT NULL,
                    recovery_score REAL DEFAULT 100.0,
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_conversations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    agent_role TEXT NOT NULL,
                    message_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS flashcards (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    ease_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 1,
                    next_review_date DATE DEFAULT CURRENT_DATE,
                    consecutive_correct INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
        else:
            # SQLite Syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    academic_level TEXT NOT NULL,
                    mastery_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS academic_milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    grade REAL DEFAULT 0.0,
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS athletic_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_type TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    intensity_rpe INTEGER NOT NULL,
                    recovery_score REAL DEFAULT 100.0,
                    recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    agent_role TEXT NOT NULL,
                    message_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    ease_factor REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 1,
                    next_review_date TEXT DEFAULT (date('now')),
                    consecutive_correct INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
        conn.commit()

def add_user(db_path: str, name: str, role: str, academic_level: str) -> int:
    """Inserts a new user and returns the auto-generated user ID."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            "INSERT INTO users (name, role, academic_level) VALUES (?, ?, ?)",
            (name, role, academic_level)
        )
        conn.commit()
        if adapter.use_postgres:
            cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1")
            return cursor.fetchone()["id"]
        else:
            return cursor.lastrowid

def get_user(db_path: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a user profile by ID."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(cursor, "SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_mastery_score(db_path: str, user_id: int, score: float) -> None:
    """Updates the user's overall mastery score."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            "UPDATE users SET mastery_score = ? WHERE id = ?",
            (score, user_id)
        )
        conn.commit()

def add_academic_milestone(
    db_path: str, user_id: int, subject: str, topic: str, status: str, grade: float
) -> None:
    """Logs an academic milestone achieved by a user."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            """INSERT INTO academic_milestones (user_id, subject, topic, status, grade) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, subject, topic, status, grade)
        )
        conn.commit()

def add_athletic_metric(
    db_path: str, user_id: int, session_type: str, duration_minutes: int, intensity_rpe: int, recovery_score: float
) -> None:
    """Logs a training session's athletic load metrics."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            """INSERT INTO athletic_metrics (user_id, session_type, duration_minutes, intensity_rpe, recovery_score) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, session_type, duration_minutes, intensity_rpe, recovery_score)
        )
        conn.commit()

def log_conversation(db_path: str, user_id: int, agent_role: str, message_role: str, message_content: str) -> None:
    """Appends conversational dialogue to the history log."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            """INSERT INTO agent_conversations (user_id, agent_role, message_role, message_content) 
               VALUES (?, ?, ?, ?)""",
            (user_id, agent_role, message_role, message_content)
        )
        conn.commit()

def get_conversation_history(db_path: str, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent dialogue transcripts for session context reconstruction."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            """SELECT agent_role, message_role, message_content, timestamp 
               FROM agent_conversations 
               WHERE user_id = ? 
               ORDER BY timestamp ASC LIMIT ?""",
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

# Spaced Repetition CRUD Methods
def add_flashcard(db_path: str, user_id: int, question: str, answer: str) -> None:
    """Creates a new flashcard for Spaced Repetition review."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            "INSERT INTO flashcards (user_id, question, answer) VALUES (?, ?, ?)",
            (user_id, question, answer)
        )
        conn.commit()

def get_due_flashcards(db_path: str, user_id: int) -> List[Dict[str, Any]]:
    """Retrieves flashcards currently due for review."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            "SELECT * FROM flashcards WHERE user_id = ? AND next_review_date <= date('now')",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def update_flashcard_review(
    db_path: str, card_id: int, ease_factor: float, interval_days: int, next_review_date: str, consecutive_correct: int
) -> None:
    """Updates review tracking details of a flashcard."""
    adapter = DatabaseAdapter(db_path)
    with adapter.get_connection() as conn:
        cursor = adapter.get_cursor(conn)
        adapter.execute(
            cursor,
            """UPDATE flashcards 
               SET ease_factor = ?, interval_days = ?, next_review_date = ?, consecutive_correct = ? 
               WHERE id = ?""",
            (ease_factor, interval_days, next_review_date, consecutive_correct, card_id)
        )
        conn.commit()
