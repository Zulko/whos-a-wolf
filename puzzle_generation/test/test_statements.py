"""Tests for statement serialization (to_dict/from_dict round-trips)."""

import json

from src.models import Puzzle, Villager
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

    # Count statement with count (now uses unified CountWerewolves)
    count_stmt = ExactlyKWerewolves((0, 1, 2), 2)
    count_dict = count_stmt.to_dict()
    assert "type" in count_dict
    assert count_dict["type"] == "CountWerewolves"
    assert "scope_indices" in count_dict
    assert "count" in count_dict
    assert "comparison" in count_dict
    assert count_dict["scope_indices"] == [0, 1, 2]  # Should be list, not tuple
    assert count_dict["count"] == 2
    assert count_dict["comparison"] == "exactly"

    # Count statement with parity (now uses unified CountWerewolves)
    parity_stmt = EvenNumberOfWerewolves((0, 1, 2))
    parity_dict = parity_stmt.to_dict()
    assert "type" in parity_dict
    assert parity_dict["type"] == "CountWerewolves"
    assert "scope_indices" in parity_dict
    assert "count" in parity_dict
    assert parity_dict["count"] == "even"
    assert "comparison" not in parity_dict  # No comparison for parity
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


def test_if_a_then_b_short_string_round_trip():
    """Test IfAThenB short string round-trip."""
    stmt = IfAThenB(5, 7)
    short_str = stmt.to_short_string()
    assert short_str == "I-5-7"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.a_index == reconstructed.a_index
    assert stmt.b_index == reconstructed.b_index


def test_both_or_neither_short_string_round_trip():
    """Test BothOrNeither short string round-trip."""
    stmt = BothOrNeither(3, 4)
    short_str = stmt.to_short_string()
    assert short_str == "B-3-4"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.a_index == reconstructed.a_index
    assert stmt.b_index == reconstructed.b_index


def test_at_least_one_short_string_round_trip():
    """Test AtLeastOne short string round-trip."""
    stmt = AtLeastOne(0, 1)
    short_str = stmt.to_short_string()
    assert short_str == "A-0-1"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.a_index == reconstructed.a_index
    assert stmt.b_index == reconstructed.b_index


def test_exactly_one_short_string_round_trip():
    """Test ExactlyOne short string round-trip."""
    stmt = ExactlyOne(2, 3)
    short_str = stmt.to_short_string()
    assert short_str == "X-2-3"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.a_index == reconstructed.a_index
    assert stmt.b_index == reconstructed.b_index


def test_if_not_a_then_b_short_string_round_trip():
    """Test IfNotAThenB short string round-trip."""
    stmt = IfNotAThenB(0, 1)
    short_str = stmt.to_short_string()
    assert short_str == "F-0-1"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.a_index == reconstructed.a_index
    assert stmt.b_index == reconstructed.b_index


def test_neither_short_string_round_trip():
    """Test Neither short string round-trip."""
    stmt = Neither(3, 4)
    short_str = stmt.to_short_string()
    assert short_str == "N-3-4"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.a_index == reconstructed.a_index
    assert stmt.b_index == reconstructed.b_index


def test_exactly_k_werewolves_short_string_round_trip():
    """Test ExactlyKWerewolves short string round-trip."""
    stmt = ExactlyKWerewolves((0, 1, 2), 2)
    short_str = stmt.to_short_string()
    assert short_str == "E-0.1.2-2"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.scope_indices == reconstructed.scope_indices
    assert stmt.count == reconstructed.count


def test_at_most_k_werewolves_short_string_round_trip():
    """Test AtMostKWerewolves short string round-trip."""
    stmt = AtMostKWerewolves((0, 1), 1)
    short_str = stmt.to_short_string()
    assert short_str == "M-0.1-1"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.scope_indices == reconstructed.scope_indices
    assert stmt.count == reconstructed.count


def test_at_least_k_werewolves_short_string_round_trip():
    """Test AtLeastKWerewolves short string round-trip."""
    stmt = AtLeastKWerewolves((0, 1, 2, 3), 2)
    short_str = stmt.to_short_string()
    assert short_str == "L-0.1.2.3-2"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.scope_indices == reconstructed.scope_indices
    assert stmt.count == reconstructed.count


def test_even_number_of_werewolves_short_string_round_trip():
    """Test EvenNumberOfWerewolves short string round-trip."""
    stmt = EvenNumberOfWerewolves((0, 1, 2))
    short_str = stmt.to_short_string()
    assert short_str == "V-0.1.2"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.scope_indices == reconstructed.scope_indices


def test_odd_number_of_werewolves_short_string_round_trip():
    """Test OddNumberOfWerewolves short string round-trip."""
    stmt = OddNumberOfWerewolves((0, 1))
    short_str = stmt.to_short_string()
    assert short_str == "O-0.1"
    reconstructed = Statement.from_short_string(short_str)
    assert stmt == reconstructed
    assert stmt.scope_indices == reconstructed.scope_indices


def test_all_statements_short_string_round_trip():
    """Test that all statement types support short string round-trip."""
    statements = [
        IfAThenB(0, 1),
        BothOrNeither(2, 3),
        AtLeastOne(0, 1),
        ExactlyOne(2, 3),
        IfNotAThenB(0, 1),
        Neither(2, 3),
        ExactlyKWerewolves((0, 1, 2), 2),
        AtMostKWerewolves((0, 1), 1),
        AtLeastKWerewolves((0, 1, 2, 3), 2),
        EvenNumberOfWerewolves((0, 1, 2)),
        OddNumberOfWerewolves((0, 1)),
    ]

    for stmt in statements:
        short_str = stmt.to_short_string()
        reconstructed = Statement.from_short_string(short_str)
        assert stmt == reconstructed, (
            f"Round-trip failed for {stmt.__class__.__name__}: "
            f"original={stmt.statement_id}, reconstructed={reconstructed.statement_id}"
        )
        # Verify evaluation is preserved
        test_assignment = (True, False, True, False)
        original_result = stmt.evaluate_on_assignment(test_assignment)
        reconstructed_result = reconstructed.evaluate_on_assignment(test_assignment)
        assert original_result == reconstructed_result, (
            f"Evaluation mismatch for {stmt.__class__.__name__}: "
            f"original={original_result}, reconstructed={reconstructed_result}"
        )


def test_from_short_string_invalid_format():
    """Test that from_short_string raises ValueError for invalid formats."""
    invalid_strings = [
        "X",  # Too short
        "I-5",  # Missing second index
        "E-0,1",  # Missing count
        "Z-5-7",  # Unknown code
        "",  # Empty string
    ]

    for invalid_str in invalid_strings:
        try:
            Statement.from_short_string(invalid_str)
            assert False, f"Should have raised ValueError for: {invalid_str}"
        except ValueError:
            pass  # Expected


def test_puzzle_to_short_statements_string():
    """Test Puzzle.to_short_statements_string() method."""
    villagers = [
        Villager(0, "Alice"),
        Villager(1, "Bob"),
        Villager(2, "Charlie"),
    ]
    statements_by_speaker = [
        [IfAThenB(5, 7)],  # Alice
        [Neither(3, 4)],  # Bob
        [BothOrNeither(0, 1), AtLeastOne(2, 3)],  # Charlie
    ]

    puzzle = Puzzle(
        villagers=villagers,
        statements_by_speaker=statements_by_speaker,
    )

    short_str = puzzle.to_short_statements_string()
    # Should be: I-5-7_N-3-4_B-0-1_A-2-3
    # Note: BothOrNeither normalizes indices, so 0,1 stays 0,1
    # AtLeastOne normalizes indices, so 2,3 stays 2,3
    expected_parts = ["I-5-7", "N-3-4", "B-0-1", "A-2-3"]
    actual_parts = short_str.split("_")
    assert len(actual_parts) == len(expected_parts)
    assert set(actual_parts) == set(expected_parts), (
        f"Expected {expected_parts}, got {actual_parts}"
    )

