"""Tests for puzzle uniqueness verification."""

import pytest
from src.generator import generate_puzzle, build_claim_library
from src.models import GenerationConfig
from src.solver import PuzzleSolver
from src.truth_cache import ClaimTruthTableCache


def test_generated_puzzle_has_unique_solution():
    """Test that a generated puzzle has exactly one solution."""
    config = GenerationConfig(
        N=6,
        claims_per_speaker_min=2,
        claims_per_speaker_max=2,
        max_attempts=100,
    )

    # Build truth cache
    claim_library = build_claim_library(config)
    truth_cache = ClaimTruthTableCache.build_for_claim_library(claim_library, config.N)

    # Generate puzzle
    puzzle = generate_puzzle(config, truth_cache)

    # Assert puzzle was generated
    assert puzzle is not None, "Failed to generate puzzle"

    # Assert all villagers have claims
    assert len(puzzle.villagers) == config.N
    for i, claims in enumerate(puzzle.claims_by_speaker):
        assert len(claims) > 0, (
            f"Villager {i} ({puzzle.villagers[i].name}) has no claims"
        )

    # Verify uniqueness using Z3 solver
    assert PuzzleSolver.is_uniquely_satisfiable(puzzle), (
        "Generated puzzle does not have a unique solution"
    )

    # Verify the solution matches the stored solution assignment
    if puzzle.solution_assignment:
        found_solution = PuzzleSolver.find_one_solution(puzzle)
        assert found_solution is not None, "Puzzle should be satisfiable"
        assert found_solution == puzzle.solution_assignment, (
            f"Found solution {found_solution} does not match stored solution {puzzle.solution_assignment}"
        )


def test_generated_puzzle_uniqueness_multiple_runs():
    """Test that multiple generated puzzles all have unique solutions."""
    config = GenerationConfig(
        N=6,
        claims_per_speaker_min=2,
        claims_per_speaker_max=2,
        max_attempts=100,
    )

    # Build truth cache
    claim_library = build_claim_library(config)
    truth_cache = ClaimTruthTableCache.build_for_claim_library(claim_library, config.N)

    # Generate multiple puzzles
    for run in range(5):
        puzzle = generate_puzzle(config, truth_cache)

        assert puzzle is not None, f"Failed to generate puzzle on run {run + 1}"
        assert PuzzleSolver.is_uniquely_satisfiable(puzzle), (
            f"Puzzle from run {run + 1} does not have a unique solution"
        )

        # Verify all villagers have claims
        for i, claims in enumerate(puzzle.claims_by_speaker):
            assert len(claims) > 0, (
                f"Run {run + 1}: Villager {i} ({puzzle.villagers[i].name}) has no claims"
            )


def test_different_puzzle_sizes():
    """Test uniqueness for puzzles of different sizes."""
    sizes = [4, 5, 6]

    for N in sizes:
        config = GenerationConfig(
            N=N,
            claims_per_speaker_min=2,
            claims_per_speaker_max=2,
            max_attempts=50,  # Fewer attempts for smaller puzzles
        )

        # Build truth cache
        claim_library = build_claim_library(config)
        truth_cache = ClaimTruthTableCache.build_for_claim_library(
            claim_library, config.N
        )

        # Generate puzzle
        puzzle = generate_puzzle(config, truth_cache)

        assert puzzle is not None, f"Failed to generate puzzle for N={N}"
        assert PuzzleSolver.is_uniquely_satisfiable(puzzle), (
            f"Puzzle with N={N} does not have a unique solution"
        )

        # Verify all villagers have claims
        assert len(puzzle.villagers) == N
        for i, claims in enumerate(puzzle.claims_by_speaker):
            assert len(claims) > 0, (
                f"N={N}: Villager {i} ({puzzle.villagers[i].name}) has no claims"
            )


def test_solver_uniqueness_check():
    """Test that the solver correctly identifies unique vs non-unique puzzles."""
    from src.models import Puzzle, Villager
    from src.claims import IfAThenB, BothOrNeither

    # Create a simple puzzle that should have a unique solution
    # This is a minimal test case
    villagers = [
        Villager(0, "Alice"),
        Villager(1, "Bob"),
    ]

    # Simple puzzle: Alice says "If Bob is wolf, then I am wolf"
    # Bob says "We are both wolves or neither"
    # This should have a unique solution
    claims_by_speaker = [
        [IfAThenB(1, 0)],  # Alice: If Bob is wolf, then I am wolf
        [BothOrNeither(0, 1)],  # Bob: Both or neither
    ]

    puzzle = Puzzle(
        villagers=villagers,
        claims_by_speaker=claims_by_speaker,
        solution_assignment=None,
    )

    # Check if it's uniquely satisfiable
    is_unique = PuzzleSolver.is_uniquely_satisfiable(puzzle)

    # This specific puzzle should have a unique solution
    # (Both are humans: Alice's claim is true, Bob's claim is true)
    assert is_unique, "Expected this simple puzzle to have a unique solution"

    # Verify we can find the solution
    solution = PuzzleSolver.find_one_solution(puzzle)
    assert solution is not None, "Puzzle should be satisfiable"
