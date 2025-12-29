"""Tests for statement serialization (to_dict/from_dict round-trips)."""

import json

from src.statements import (
    AtLeastKWerewolves,
    AtLeastOne,
    AtMostKWerewolves,
    BothOrNeither,
    ExactlyKWerewolves,
    ExactlyOne,
    EvenNumberOfWerewolves,
    IfAThenB,
    IfNotAThenB,
    Neither,
    OddNumberOfWerewolves,
    Statement,
)


def test_if_a_then_b_round_trip():
    """Test IfAThenB round-trip serialization."""
    stmt = IfAThenB(0, 1)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.a_index == stmt_reconstructed.a_index
    assert stmt.b_index == stmt_reconstructed.b_index
    assert stmt == stmt_reconstructed


def test_both_or_neither_round_trip():
    """Test BothOrNeither round-trip serialization."""
    stmt = BothOrNeither(2, 3)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.a_index == stmt_reconstructed.a_index
    assert stmt.b_index == stmt_reconstructed.b_index
    assert stmt == stmt_reconstructed


def test_at_least_one_round_trip():
    """Test AtLeastOne round-trip serialization."""
    stmt = AtLeastOne(0, 1)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.a_index == stmt_reconstructed.a_index
    assert stmt.b_index == stmt_reconstructed.b_index
    assert stmt == stmt_reconstructed


def test_exactly_one_round_trip():
    """Test ExactlyOne round-trip serialization."""
    stmt = ExactlyOne(2, 3)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.a_index == stmt_reconstructed.a_index
    assert stmt.b_index == stmt_reconstructed.b_index
    assert stmt == stmt_reconstructed


def test_if_not_a_then_b_round_trip():
    """Test IfNotAThenB round-trip serialization."""
    stmt = IfNotAThenB(0, 1)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.a_index == stmt_reconstructed.a_index
    assert stmt.b_index == stmt_reconstructed.b_index
    assert stmt == stmt_reconstructed


def test_neither_round_trip():
    """Test Neither round-trip serialization."""
    stmt = Neither(2, 3)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.a_index == stmt_reconstructed.a_index
    assert stmt.b_index == stmt_reconstructed.b_index
    assert stmt == stmt_reconstructed


def test_exactly_k_werewolves_round_trip():
    """Test ExactlyKWerewolves round-trip serialization."""
    stmt = ExactlyKWerewolves((0, 1, 2), 2)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.scope_indices == stmt_reconstructed.scope_indices
    assert stmt.count == stmt_reconstructed.count
    assert stmt == stmt_reconstructed


def test_at_most_k_werewolves_round_trip():
    """Test AtMostKWerewolves round-trip serialization."""
    stmt = AtMostKWerewolves((0, 1), 1)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.scope_indices == stmt_reconstructed.scope_indices
    assert stmt.count == stmt_reconstructed.count
    assert stmt == stmt_reconstructed


def test_at_least_k_werewolves_round_trip():
    """Test AtLeastKWerewolves round-trip serialization."""
    stmt = AtLeastKWerewolves((0, 1, 2, 3), 2)
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.scope_indices == stmt_reconstructed.scope_indices
    assert stmt.count == stmt_reconstructed.count
    assert stmt == stmt_reconstructed


def test_even_number_of_werewolves_round_trip():
    """Test EvenNumberOfWerewolves round-trip serialization."""
    stmt = EvenNumberOfWerewolves((0, 1, 2))
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.scope_indices == stmt_reconstructed.scope_indices
    assert stmt == stmt_reconstructed


def test_odd_number_of_werewolves_round_trip():
    """Test OddNumberOfWerewolves round-trip serialization."""
    stmt = OddNumberOfWerewolves((0, 1))
    stmt_dict = stmt.to_dict()
    stmt_reconstructed = Statement.from_dict(stmt_dict)

    assert stmt.statement_id == stmt_reconstructed.statement_id
    assert stmt.scope_indices == stmt_reconstructed.scope_indices
    assert stmt == stmt_reconstructed


def test_all_relationship_statements_json_serializable():
    """Test that all relationship statements are JSON-serializable."""
    statements = [
        IfAThenB(0, 1),
        BothOrNeither(2, 3),
        AtLeastOne(0, 1),
        ExactlyOne(2, 3),
        IfNotAThenB(0, 1),
        Neither(2, 3),
    ]

    for stmt in statements:
        stmt_dict = stmt.to_dict()
        json_str = json.dumps(stmt_dict)
        assert json_str is not None
        # Verify we can parse it back
        parsed_dict = json.loads(json_str)
        reconstructed = Statement.from_dict(parsed_dict)
        assert stmt.statement_id == reconstructed.statement_id


def test_all_count_statements_json_serializable():
    """Test that all count statements are JSON-serializable."""
    statements = [
        ExactlyKWerewolves((0, 1, 2), 2),
        AtMostKWerewolves((0, 1), 1),
        AtLeastKWerewolves((0, 1, 2, 3), 2),
        EvenNumberOfWerewolves((0, 1, 2)),
        OddNumberOfWerewolves((0, 1)),
    ]

    for stmt in statements:
        stmt_dict = stmt.to_dict()
        json_str = json.dumps(stmt_dict)
        assert json_str is not None
        # Verify we can parse it back
        parsed_dict = json.loads(json_str)
        reconstructed = Statement.from_dict(parsed_dict)
        assert stmt.statement_id == reconstructed.statement_id


def test_statement_dict_structure():
    """Test that statement dicts have the expected structure."""
    # Relationship statement
    rel_stmt = IfAThenB(0, 1)
    rel_dict = rel_stmt.to_dict()
    assert "type" in rel_dict
    assert rel_dict["type"] == "IfAThenB"
    assert "a_index" in rel_dict
    assert "b_index" in rel_dict
    assert rel_dict["a_index"] == 0
    assert rel_dict["b_index"] == 1

    # Count statement with count
    count_stmt = ExactlyKWerewolves((0, 1, 2), 2)
    count_dict = count_stmt.to_dict()
    assert "type" in count_dict
    assert count_dict["type"] == "ExactlyKWerewolves"
    assert "scope_indices" in count_dict
    assert "count" in count_dict
    assert count_dict["scope_indices"] == [0, 1, 2]  # Should be list, not tuple
    assert count_dict["count"] == 2

    # Count statement without count
    parity_stmt = EvenNumberOfWerewolves((0, 1, 2))
    parity_dict = parity_stmt.to_dict()
    assert "type" in parity_dict
    assert parity_dict["type"] == "EvenNumberOfWerewolves"
    assert "scope_indices" in parity_dict
    assert "count" not in parity_dict
    assert parity_dict["scope_indices"] == [0, 1, 2]  # Should be list, not tuple


def test_statement_from_dict_unknown_type():
    """Test that from_dict raises ValueError for unknown statement types."""
    invalid_dict = {"type": "UnknownStatement", "a_index": 0, "b_index": 1}

    try:
        Statement.from_dict(invalid_dict)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown statement type" in str(e) or "UnknownStatement" in str(e)


def test_statement_from_dict_missing_type():
    """Test that from_dict raises ValueError when type is missing."""
    invalid_dict = {"a_index": 0, "b_index": 1}

    try:
        Statement.from_dict(invalid_dict)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "type" in str(e).lower() or "must include" in str(e).lower()


def test_statement_round_trip_preserves_evaluation():
    """Test that round-trip serialization preserves statement evaluation."""
    statements = [
        IfAThenB(0, 1),
        BothOrNeither(0, 1),
        ExactlyKWerewolves((0, 1, 2), 2),
        EvenNumberOfWerewolves((0, 1, 2)),
    ]

    test_assignment = (True, False, True)

    for stmt in statements:
        stmt_reconstructed = Statement.from_dict(stmt.to_dict())
        original_result = stmt.evaluate_on_assignment(test_assignment)
        reconstructed_result = stmt_reconstructed.evaluate_on_assignment(test_assignment)
        assert original_result == reconstructed_result, (
            f"Evaluation mismatch for {stmt.__class__.__name__}: "
            f"original={original_result}, reconstructed={reconstructed_result}"
        )


def test_statement_round_trip_preserves_variables_involved():
    """Test that round-trip serialization preserves variables_involved."""
    statements = [
        IfAThenB(0, 1),
        BothOrNeither(2, 3),
        ExactlyKWerewolves((0, 1, 2), 2),
        EvenNumberOfWerewolves((0, 1, 2, 3)),
    ]

    for stmt in statements:
        stmt_reconstructed = Statement.from_dict(stmt.to_dict())
        original_vars = stmt.variables_involved()
        reconstructed_vars = stmt_reconstructed.variables_involved()
        assert original_vars == reconstructed_vars, (
            f"Variables mismatch for {stmt.__class__.__name__}: "
            f"original={original_vars}, reconstructed={reconstructed_vars}"
        )

