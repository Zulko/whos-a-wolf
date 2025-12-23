"""Tests for symmetrical relationship claim behavior."""

from src.claims import (
    BothOrNeither,
    AtLeastOne,
    ExactlyOne,
    Neither,
    IfAThenB,
    IfNotAThenB,
)
from src.generator import build_claim_library
from src.models import GenerationConfig


def test_both_or_neither_normalizes_indices():
    """Test that BothOrNeither normalizes indices correctly."""
    claim1 = BothOrNeither(0, 1)
    claim2 = BothOrNeither(1, 0)
    
    # Both should have normalized indices
    assert claim1.a_index == 0
    assert claim1.b_index == 1
    assert claim2.a_index == 0
    assert claim2.b_index == 1
    
    # They should be equal
    assert claim1 == claim2
    assert hash(claim1) == hash(claim2)
    
    # They should have the same claim_id
    assert claim1.claim_id == claim2.claim_id
    assert claim1.claim_id == "EQ(0,1)"


def test_at_least_one_normalizes_indices():
    """Test that AtLeastOne normalizes indices correctly."""
    claim1 = AtLeastOne(2, 3)
    claim2 = AtLeastOne(3, 2)
    
    # Both should have normalized indices
    assert claim1.a_index == 2
    assert claim1.b_index == 3
    assert claim2.a_index == 2
    assert claim2.b_index == 3
    
    # They should be equal
    assert claim1 == claim2
    assert hash(claim1) == hash(claim2)
    
    # They should have the same claim_id
    assert claim1.claim_id == claim2.claim_id
    assert claim1.claim_id == "OR(2,3)"


def test_exactly_one_normalizes_indices():
    """Test that ExactlyOne normalizes indices correctly."""
    claim1 = ExactlyOne(4, 5)
    claim2 = ExactlyOne(5, 4)
    
    # Both should have normalized indices
    assert claim1.a_index == 4
    assert claim1.b_index == 5
    assert claim2.a_index == 4
    assert claim2.b_index == 5
    
    # They should be equal
    assert claim1 == claim2
    assert hash(claim1) == hash(claim2)
    
    # They should have the same claim_id
    assert claim1.claim_id == claim2.claim_id
    assert claim1.claim_id == "XOR(4,5)"


def test_neither_normalizes_indices():
    """Test that Neither normalizes indices correctly."""
    claim1 = Neither(1, 2)
    claim2 = Neither(2, 1)
    
    # Both should have normalized indices
    assert claim1.a_index == 1
    assert claim1.b_index == 2
    assert claim2.a_index == 1
    assert claim2.b_index == 2
    
    # They should be equal
    assert claim1 == claim2
    assert hash(claim1) == hash(claim2)
    
    # They should have the same claim_id
    assert claim1.claim_id == claim2.claim_id
    assert claim1.claim_id == "NEITHER(1,2)"


def test_symmetrical_claims_in_sets():
    """Test that symmetrical claims work correctly in sets (no duplicates)."""
    # Create claims with reversed indices
    claims = {
        BothOrNeither(0, 1),
        BothOrNeither(1, 0),
        AtLeastOne(2, 3),
        AtLeastOne(3, 2),
        ExactlyOne(4, 5),
        ExactlyOne(5, 4),
        Neither(1, 2),
        Neither(2, 1),
    }
    
    # Should only have 4 unique claims (one of each type)
    assert len(claims) == 4
    
    # Verify each type is present
    claim_ids = {c.claim_id for c in claims}
    assert "EQ(0,1)" in claim_ids
    assert "OR(2,3)" in claim_ids
    assert "XOR(4,5)" in claim_ids
    assert "NEITHER(1,2)" in claim_ids


def test_non_symmetrical_claims_not_normalized():
    """Test that non-symmetrical claims do NOT normalize indices."""
    claim1 = IfAThenB(0, 1)
    claim2 = IfAThenB(1, 0)
    
    # They should have different indices
    assert claim1.a_index == 0
    assert claim1.b_index == 1
    assert claim2.a_index == 1
    assert claim2.b_index == 0
    
    # They should NOT be equal
    assert claim1 != claim2
    assert hash(claim1) != hash(claim2)
    
    # They should have different claim_ids
    assert claim1.claim_id == "IMP(0,1)"
    assert claim2.claim_id == "IMP(1,0)"


def test_generator_creates_no_duplicate_symmetrical_claims():
    """Test that build_claim_library creates no duplicate symmetrical claims."""
    config = GenerationConfig(N=4, forbid_self_reference=True, allow_count_claims=False)
    claims = build_claim_library(config)
    
    # Separate symmetrical and non-symmetrical claims
    symmetrical = [
        c for c in claims
        if isinstance(c, (BothOrNeither, AtLeastOne, ExactlyOne, Neither))
    ]
    non_symmetrical = [
        c for c in claims
        if isinstance(c, (IfAThenB, IfNotAThenB))
    ]
    
    # For N=4, forbid_self_reference=True:
    # - Symmetrical: 4 classes * (4 choose 2) = 4 * 6 = 24
    # - Non-symmetrical: 2 classes * (4 * 3) = 2 * 12 = 24
    assert len(symmetrical) == 24, f"Expected 24 symmetrical claims, got {len(symmetrical)}"
    assert len(non_symmetrical) == 24, f"Expected 24 non-symmetrical claims, got {len(non_symmetrical)}"
    
    # Check for duplicates in symmetrical claims
    symmetrical_ids = [c.claim_id for c in symmetrical]
    unique_symmetrical = set(symmetrical_ids)
    assert len(unique_symmetrical) == len(symmetrical_ids), (
        f"Found {len(symmetrical_ids) - len(unique_symmetrical)} duplicate symmetrical claims"
    )
    
    # Verify all symmetrical claims have normalized indices (a_index <= b_index)
    for claim in symmetrical:
        assert claim.a_index <= claim.b_index, (
            f"Symmetrical claim {claim.claim_id} has unnormalized indices: "
            f"a_index={claim.a_index}, b_index={claim.b_index}"
        )


def test_generator_creates_all_ordered_pairs_for_non_symmetrical():
    """Test that build_claim_library creates all ordered pairs for non-symmetrical claims."""
    config = GenerationConfig(N=3, forbid_self_reference=True, allow_count_claims=False)
    claims = build_claim_library(config)
    
    non_symmetrical = [
        c for c in claims
        if isinstance(c, (IfAThenB, IfNotAThenB))
    ]
    
    # For N=3, forbid_self_reference=True:
    # - Non-symmetrical: 2 classes * (3 * 2) = 2 * 6 = 12
    assert len(non_symmetrical) == 12
    
    # Collect all ordered pairs
    if_then_pairs = {(c.a_index, c.b_index) for c in non_symmetrical if isinstance(c, IfAThenB)}
    if_not_then_pairs = {(c.a_index, c.b_index) for c in non_symmetrical if isinstance(c, IfNotAThenB)}
    
    # Should have all 6 ordered pairs (0,1), (0,2), (1,0), (1,2), (2,0), (2,1)
    expected_pairs = {(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)}
    assert if_then_pairs == expected_pairs
    assert if_not_then_pairs == expected_pairs


def test_symmetrical_claims_evaluate_correctly():
    """Test that symmetrical claims evaluate correctly regardless of index order."""
    # Test BothOrNeither
    claim1 = BothOrNeither(0, 1)
    claim2 = BothOrNeither(1, 0)
    
    # Both should evaluate the same on any assignment
    assignments = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]
    
    for assignment in assignments:
        assert claim1.evaluate_on_assignment(assignment) == claim2.evaluate_on_assignment(assignment)
    
    # Test AtLeastOne
    claim3 = AtLeastOne(0, 1)
    claim4 = AtLeastOne(1, 0)
    
    for assignment in assignments:
        assert claim3.evaluate_on_assignment(assignment) == claim4.evaluate_on_assignment(assignment)
    
    # Test ExactlyOne
    claim5 = ExactlyOne(0, 1)
    claim6 = ExactlyOne(1, 0)
    
    for assignment in assignments:
        assert claim5.evaluate_on_assignment(assignment) == claim6.evaluate_on_assignment(assignment)
    
    # Test Neither
    claim7 = Neither(0, 1)
    claim8 = Neither(1, 0)
    
    for assignment in assignments:
        assert claim7.evaluate_on_assignment(assignment) == claim8.evaluate_on_assignment(assignment)

