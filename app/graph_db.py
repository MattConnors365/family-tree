import sqlite3
from typing import Literal, Optional

RelationshipType = Literal["Parent", "Sibling", "Partner"]

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
    def add_relationship(self, type: RelationshipType, a, b):
        # Normalize inputs: strings → singleton sets, iterables → sets
        set_a = {a} if isinstance(a, str) else set(a)
        set_b = {b} if isinstance(b, str) else set(b)

        # Ensure all people exist
        for person in set_a | set_b:
            self._ensure_person_exists(person)

        # Cartesian product insertion
        for pa in set_a:
            for pb in set_b:
                if pa == pb:
                    raise ValueError(f"Person '{pa}' can't have a relationship with themselves.")
                if type in ("Sibling", "Partner"):
                    person1, person2 = sorted([pa, pb])
                else:
                    person1, person2 = pa, pb

                self.cursor.execute("""
                    INSERT OR IGNORE INTO relationships (type, person_a, person_b)
                    VALUES (?, ?, ?)
                """, (type, person1, person2))

    def remove_relationship(self, a, b, type: Optional[RelationshipType] = None):
        # Normalize inputs
        set_a = {a} if isinstance(a, str) else set(a)
        set_b = {b} if isinstance(b, str) else set(b)

        for pa in set_a:
            for pb in set_b:
                if pa == pb:
                    raise ValueError(f"Cannot remove a relationship of a person '{pa}' with themselves.")
                if type in ("Sibling", "Partner"):
                    person1, person2 = sorted([pa, pb])
                else:
                    person1, person2 = pa, pb

                if type:
                    self.cursor.execute("""
                        DELETE FROM relationships
                        WHERE type = ? AND person_a = ? AND person_b = ?
                    """, (type, person1, person2))
                else:
                    # delete all relationship types between these two
                    self.cursor.execute("""
                        DELETE FROM relationships
                        WHERE (person_a = ? AND person_b = ?) OR (person_a = ? AND person_b = ?)
                    """, (person1, person2, person2, person1))

                # Prune lonely nodes
                self._delete_person_if_lonely(pa)
                self._delete_person_if_lonely(pb)

    # query helpers
    def parents_of(self, person: str | set[str]) -> dict[str, set[str]]:
        set_people = {person} if isinstance(person, str) else set(person)
        relationship_mapping: dict[str, set[str]] = {}
        for person in set_people:
            self.cursor.execute("""
                SELECT person_a FROM relationships
                WHERE type = 'Parent' AND person_b = ?
            """, (person,))
            relationship_mapping[person] = {row[0] for row in self.cursor.fetchall()}
        return relationship_mapping

    def children_of(self, person: str | set[str]) -> dict[str, set[str]]:
        set_people = {person} if isinstance(person, str) else set(person)
        relationship_mapping: dict[str, set[str]] = {}
        for person in set_people:
            self.cursor.execute("""
                SELECT person_b FROM relationships
                WHERE type = 'Parent' AND person_a = ?
            """, (person,))
            relationship_mapping[person] = {row[0] for row in self.cursor.fetchall()}
        return relationship_mapping

    def siblings_of(self, person: str | set[str]) -> dict[str, set[str]]:
        set_people = {person} if isinstance(person, str) else set(person)
        relationship_mapping: dict[str, set[str]] = {}

        for p in set_people:
            self.cursor.execute("""
                SELECT person_a, person_b
                FROM relationships
                WHERE type = 'Sibling' AND (person_a = ? OR person_b = ?)
            """, (p, p))

            rows = self.cursor.fetchall()
            result = set()

            for a, b in rows:
                result.add(b if a == p else a)

            relationship_mapping[p] = result

        return relationship_mapping

    def partner_of(self, person: str | set[str]) -> dict[str, set[str]]:
        set_people = {person} if isinstance(person, str) else set(person)
        relationship_mapping: dict[str, set[str]] = {}

        for p in set_people:
            self.cursor.execute("""
                SELECT person_a, person_b
                FROM relationships
                WHERE type = 'Partner' AND (person_a = ? OR person_b = ?)
            """, (p, p))

            rows = self.cursor.fetchall()
            result = set()

            for a, b in rows:
                result.add(b if a == p else a)

            relationship_mapping[p] = result

        return relationship_mapping
