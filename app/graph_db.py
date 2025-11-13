import sqlcipher3
from typing import Literal
from functools import partial

class FamilyTree:
    def __init__(self) -> None:
        ...
    def add_people(self, *people) -> None:
        ...
    def remove_people(self, *people) -> None:
        ...
    RelationshipType = Literal["Parent", "Child", "Sibling", "Spouse", "Other"]
    def is_directed_relationship(self, relationship: RelationshipType) -> bool:
        return relationship in {
            "Parent",
            "Child"
        }
    def add_relationship(self, type: RelationshipType, person_a, person_b) -> None:
        ...
    def remove_relationship(self, source, other) -> None:
        ...

