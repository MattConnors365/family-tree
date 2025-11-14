import sqlite3
from typing import Literal, Optional

RelationshipType = Literal["Parent", "Sibling", "Spouse"]

class FamilyTree:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_schema()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            self.conn.close()

    # schema
    def _create_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                name TEXT PRIMARY KEY
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                person_a TEXT NOT NULL,
                person_b TEXT NOT NULL,
                FOREIGN KEY(person_a) REFERENCES people(name) ON DELETE CASCADE,
                FOREIGN KEY(person_b) REFERENCES people(name) ON DELETE CASCADE,
                UNIQUE(type, person_a, person_b)
            );
        """)

    # internal helpers
    def _ensure_person_exists(self, name: str):
        self.cursor.execute("SELECT 1 FROM people WHERE name = ?", (name,))
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO people (name) VALUES (?)", (name,))

    def _delete_person_if_lonely(self, name: str):
        self.cursor.execute("""
            SELECT 1 FROM relationships
            WHERE person_a = ? OR person_b = ?
        """, (name, name))
        if not self.cursor.fetchone():
            self.cursor.execute("DELETE FROM people WHERE name = ?", (name,))

    def _add_people(self, *names: str):
        for name in names:
            self._ensure_person_exists(name)

    def _remove_people(self, *names: str):
        for name in names:
            self.cursor.execute("DELETE FROM people WHERE name = ?", (name,))

    # public relationship API
    def add_relationship(self, type: RelationshipType, a: str, b: str):
        # Ensure nodes exist
        self._ensure_person_exists(a)
        self._ensure_person_exists(b)

        if type in ("Sibling", "Spouse"):
            # For symmetric edges, store one row consistently: smallest name first
            person1, person2 = sorted([a, b])
        else:
            # Directed relationship: keep order
            person1, person2 = a, b

        # Insert edge
        self.cursor.execute("""
            INSERT OR IGNORE INTO relationships (type, person_a, person_b)
            VALUES (?, ?, ?)
        """, (type, person1, person2))

    def remove_relationship(self, a: str, b: str, type: Optional[RelationshipType] = None):
        # Determine which row to remove
        if type in ("Sibling", "Spouse"):
            person1, person2 = sorted([a, b])
        else:
            person1, person2 = a, b

        # Build query
        if type:
            self.cursor.execute("""
                DELETE FROM relationships
                WHERE type = ? AND person_a = ? AND person_b = ?
            """, (type, person1, person2))
        else:
            # Delete all types between these two
            self.cursor.execute("""
                DELETE FROM relationships
                WHERE (person_a = ? AND person_b = ?) OR (person_a = ? AND person_b = ?)
            """, (person1, person2, person2, person1))

        # Prune lonely nodes
        self._delete_person_if_lonely(a)
        self._delete_person_if_lonely(b)
