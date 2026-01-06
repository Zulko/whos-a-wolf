"""Tests for symmetrical relationship statement behavior."""

from src.statements import (
    BothOrNeither,
    AtLeastOne,
    ExactlyOne,
    Neither,
    IfAThenB,
)
from src.generator import build_statement_library
from src.models import GenerationConfig


def test_both_or_neither_normalizes_indices():
    """Test that BothOrNeither normalizes indices correctly."""
    statement1 = BothOrNeither(0, 1)
    statement2 = BothOrNeither(1, 0)
    
    # Both should have normalized indices
    assert statement1.a_index == 0
    assert statement1.b_index == 1
    assert statement2.a_index == 0
    assert statement2.b_index == 1
    
    # They should be equal
    assert statement1 == statement2
    assert hash(statement1) == hash(statement2)
    
    # They should have the same statement_id
    assert statement1.statement_id == statement2.statement_id
    assert statement1.statement_id == "EQ(0,1)"


def test_at_least_one_normalizes_indices():
    """Test that AtLeastOne normalizes indices correctly."""
    statement1 = AtLeastOne(2, 3)
    statement2 = AtLeastOne(3, 2)
    
    # Both should have normalized indices
    assert statement1.a_index == 2
    assert statement1.b_index == 3
    assert statement2.a_index == 2
    assert statement2.b_index == 3
    
    # They should be equal
    assert statement1 == statement2
    assert hash(statement1) == hash(statement2)
    
    # They should have the same statement_id
    assert statement1.statement_id == statement2.statement_id
    assert statement1.statement_id == "OR(2,3)"


def test_exactly_one_normalizes_indices():
    """Test that ExactlyOne normalizes indices correctly."""
    statement1 = ExactlyOne(4, 5)
    statement2 = ExactlyOne(5, 4)
    
    # Both should have normalized indices
    assert statement1.a_index == 4
    assert statement1.b_index == 5
    assert statement2.a_index == 4
    assert statement2.b_index == 5
    
    # They should be equal
    assert statement1 == statement2
    assert hash(statement1) == hash(statement2)
    
    # They should have the same statement_id
    assert statement1.statement_id == statement2.statement_id
    assert statement1.statement_id == "XOR(4,5)"


def test_neither_normalizes_indices():
    """Test that Neither normalizes indices correctly."""
    statement1 = Neither(1, 2)
    statement2 = Neither(2, 1)
    
    # Both should have normalized indices
    assert statement1.a_index == 1
    assert statement1.b_index == 2
    assert statement2.a_index == 1
    assert statement2.b_index == 2
    
    # They should be equal
    assert statement1 == statement2
    assert hash(statement1) == hash(statement2)
    
    # They should have the same statement_id
    assert statement1.statement_id == statement2.statement_id
    assert statement1.statement_id == "NEITHER(1,2)"


def test_symmetrical_statements_in_sets():
    """Test that symmetrical statements work correctly in sets (no duplicates)."""
    # Create statements with reversed indices
    statements = {
        BothOrNeither(0, 1),
        BothOrNeither(1, 0),
        AtLeastOne(2, 3),
        AtLeastOne(3, 2),
        ExactlyOne(4, 5),
        ExactlyOne(5, 4),
        Neither(1, 2),
        Neither(2, 1),
    }
    
    # Should only have 4 unique statements (one of each type)
    assert len(statements) == 4
    
    # Verify each type is present
    statement_ids = {c.statement_id for c in statements}
    assert "EQ(0,1)" in statement_ids
    assert "OR(2,3)" in statement_ids
    assert "XOR(4,5)" in statement_ids
    assert "NEITHER(1,2)" in statement_ids


def test_non_symmetrical_statements_not_normalized():
    """Test that non-symmetrical statements do NOT normalize indices."""
    statement1 = IfAThenB(0, 1)
    statement2 = IfAThenB(1, 0)
    
    # They should have different indices
    assert statement1.a_index == 0
    assert statement1.b_index == 1
    assert statement2.a_index == 1
    assert statement2.b_index == 0
    
    # They should NOT be equal
    assert statement1 != statement2
    assert hash(statement1) != hash(statement2)
    
    # They should have different statement_ids
    assert statement1.statement_id == "IMP(0,1)"
    assert statement2.statement_id == "IMP(1,0)"


def test_generator_creates_no_duplicate_symmetrical_statements():
    """Test that build_statement_library creates no duplicate symmetrical statements."""
    config = GenerationConfig(N=4, forbid_self_reference=True, allow_count_statements=False)
    statements = build_statement_library(config)
    
    # Separate symmetrical and non-symmetrical statements
    symmetrical = [
        c for c in statements
        if isinstance(c, (BothOrNeither, AtLeastOne, ExactlyOne, Neither))
    ]
    non_symmetrical = [
        c for c in statements
        if isinstance(c, IfAThenB)
    ]
    
    # For N=4, forbid_self_reference=True:
    # - Symmetrical: 4 classes * (4 choose 2) = 4 * 6 = 24
    # - Non-symmetrical: 1 class * (4 * 3) = 12
    assert len(symmetrical) == 24, f"Expected 24 symmetrical statements, got {len(symmetrical)}"
    assert len(non_symmetrical) == 12, f"Expected 12 non-symmetrical statements, got {len(non_symmetrical)}"
    
    # Check for duplicates in symmetrical statements
    symmetrical_ids = [c.statement_id for c in symmetrical]
    unique_symmetrical = set(symmetrical_ids)
    assert len(unique_symmetrical) == len(symmetrical_ids), (
        f"Found {len(symmetrical_ids) - len(unique_symmetrical)} duplicate symmetrical statements"
    )
    
    # Verify all symmetrical statements have normalized indices (a_index <= b_index)
    for statement in symmetrical:
        assert statement.a_index <= statement.b_index, (
            f"Symmetrical statement {statement.statement_id} has unnormalized indices: "
            f"a_index={statement.a_index}, b_index={statement.b_index}"
        )


def test_generator_creates_all_ordered_pairs_for_non_symmetrical():
    """Test that build_statement_library creates all ordered pairs for non-symmetrical statements."""
    config = GenerationConfig(N=3, forbid_self_reference=True, allow_count_statements=False)
    statements = build_statement_library(config)
    
    non_symmetrical = [
        c for c in statements
        if isinstance(c, IfAThenB)
    ]
    
    # For N=3, forbid_self_reference=True:
    # - Non-symmetrical: 1 class * (3 * 2) = 6
    assert len(non_symmetrical) == 6
    
    # Collect all ordered pairs
    if_then_pairs = {(c.a_index, c.b_index) for c in non_symmetrical}
    
    # Should have all 6 ordered pairs (0,1), (0,2), (1,0), (1,2), (2,0), (2,1)
    expected_pairs = {(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)}
    assert if_then_pairs == expected_pairs


def test_symmetrical_statements_evaluate_correctly():
    """Test that symmetrical statements evaluate correctly regardless of index order."""
    # Test BothOrNeither
    statement1 = BothOrNeither(0, 1)
    statement2 = BothOrNeither(1, 0)
    
    # Both should evaluate the same on any assignment
    assignments = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]
    
    for assignment in assignments:
        assert statement1.evaluate_on_assignment(assignment) == statement2.evaluate_on_assignment(assignment)
    
    # Test AtLeastOne
    statement3 = AtLeastOne(0, 1)
    statement4 = AtLeastOne(1, 0)
    
    for assignment in assignments:
        assert statement3.evaluate_on_assignment(assignment) == statement4.evaluate_on_assignment(assignment)
    
    # Test ExactlyOne
    statement5 = ExactlyOne(0, 1)
    statement6 = ExactlyOne(1, 0)
    
    for assignment in assignments:
        assert statement5.evaluate_on_assignment(assignment) == statement6.evaluate_on_assignment(assignment)
    
    # Test Neither
    statement7 = Neither(0, 1)
    statement8 = Neither(1, 0)
    
    for assignment in assignments:
        assert statement7.evaluate_on_assignment(assignment) == statement8.evaluate_on_assignment(assignment)






