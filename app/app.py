from graph_db import FamilyTree, RelationshipType

# Test Implementation

with FamilyTree("family.db") as tree:
    tree.add_relationship("Parent", {"Alice", "David"}, {"Bob", "Charlie"})
    tree.add_relationship("Sibling", "Bob", "Charlie")
    tree.add_relationship("Partner", "Alice", "David")

    print(tree.parents_of("Bob"))
    print(tree.children_of("Alice"))
    print(tree.siblings_of("Bob"))
    print(tree.partner_of("Alice"))
