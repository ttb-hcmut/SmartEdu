import sqlite3
import os
import hashlib
from typing import Dict, Any, Optional

class SQL_DB:
    def __init__(self, db_path: str = "core/repo/sql/student.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Added password field for authentication
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE,
                    name TEXT,
                    email TEXT,
                    password TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None

    def get_student_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None

    def create_student(self, student_id: str, username: str = "", name: str = "", email: str = "", password: str = ""):
        # Hash password simply (In production, use bcrypt)
        hashed_pw = hashlib.sha256(password.encode()).hexdigest() if password else ""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO students (id, username, name, email, password) VALUES (?, ?, ?, ?, ?)",
                (student_id, username, name, email, hashed_pw)
            )
            conn.commit()
            
    def authenticate(self, username: str, password: str) -> bool:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM students WHERE username = ? AND password = ?", (username, hashed_pw))
            if cursor.fetchone():
                return True
            return False
