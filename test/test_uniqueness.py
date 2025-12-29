"""Tests for puzzle uniqueness verification."""

from src.generator import (
    generate_puzzle,
    build_statement_library,
    statement_contains_other,
)
from src.models import GenerationConfig
from src.solver import PuzzleSolver
from src.truth_cache import StatementTruthTableCache


def test_generated_puzzle_has_unique_solution():
    """Test that a generated puzzle has exactly one solution."""
    config = GenerationConfig(
        N=6,
        statements_per_speaker_min=2,
        statements_per_speaker_max=2,
        max_attempts=100,
    )

    # Build truth cache
    statement_library = build_statement_library(config)
    truth_cache = StatementTruthTableCache.build_for_statement_library(
        statement_library, config.N
    )

    # Generate puzzle
    puzzle = generate_puzzle(config, truth_cache)

    # Assert puzzle was generated
    assert puzzle is not None, "Failed to generate puzzle"

    # Assert all villagers have statements
    assert len(puzzle.villagers) == config.N
    for i, statements in enumerate(puzzle.statements_by_speaker):
        assert len(statements) > 0, (
            f"Villager {i} ({puzzle.villagers[i].name}) has no statements"
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
        statements_per_speaker_min=2,
        statements_per_speaker_max=2,
        max_attempts=100,
    )

    # Build truth cache
    statement_library = build_statement_library(config)
    truth_cache = StatementTruthTableCache.build_for_statement_library(
        statement_library, config.N
    )

    # Generate multiple puzzles
    for run in range(5):
        puzzle = generate_puzzle(config, truth_cache)

        assert puzzle is not None, f"Failed to generate puzzle on run {run + 1}"
        assert PuzzleSolver.is_uniquely_satisfiable(puzzle), (
            f"Puzzle from run {run + 1} does not have a unique solution"
        )

        # Verify all villagers have statements
        for i, statements in enumerate(puzzle.statements_by_speaker):
            assert len(statements) > 0, (
                f"Run {run + 1}: Villager {i} ({puzzle.villagers[i].name}) has no statements"
            )


def test_different_puzzle_sizes():
    """Test uniqueness for puzzles of different sizes."""
    sizes = [4, 5, 6]

    for N in sizes:
        config = GenerationConfig(
            N=N,
            statements_per_speaker_min=2,
            statements_per_speaker_max=2,
            max_attempts=50,  # Fewer attempts for smaller puzzles
        )

        # Build truth cache
        statement_library = build_statement_library(config)
        truth_cache = StatementTruthTableCache.build_for_statement_library(
            statement_library, config.N
        )

        # Generate puzzle
        puzzle = generate_puzzle(config, truth_cache)

        assert puzzle is not None, f"Failed to generate puzzle for N={N}"
        assert PuzzleSolver.is_uniquely_satisfiable(puzzle), (
            f"Puzzle with N={N} does not have a unique solution"
        )

        # Verify all villagers have statements
        assert len(puzzle.villagers) == N
        for i, statements in enumerate(puzzle.statements_by_speaker):
            assert len(statements) > 0, (
                f"N={N}: Villager {i} ({puzzle.villagers[i].name}) has no statements"
            )


def test_solver_uniqueness_check():
    """Test that the solver correctly identifies unique vs non-unique puzzles."""
    from src.models import Puzzle, Villager
    from src.statements import IfAThenB, BothOrNeither

    # Create a simple puzzle that should have a unique solution
    # This is a minimal test case
    villagers = [
        Villager(0, "Alice"),
        Villager(1, "Bob"),
    ]

    # Simple puzzle: Alice says "If Bob is wolf, then I am wolf"
    # Bob says "We are both wolves or neither"
    # This should have a unique solution
    statements_by_speaker = [
        [IfAThenB(1, 0)],  # Alice: If Bob is wolf, then I am wolf
        [BothOrNeither(0, 1)],  # Bob: Both or neither
    ]

    puzzle = Puzzle(
        villagers=villagers,
        statements_by_speaker=statements_by_speaker,
        solution_assignment=None,
    )

    # Check if it's uniquely satisfiable
    is_unique = PuzzleSolver.is_uniquely_satisfiable(puzzle)

    # This specific puzzle should have a unique solution
    # (Both are humans: Alice's statement is true, Bob's statement is true)
    assert is_unique, "Expected this simple puzzle to have a unique solution"

    # Verify we can find the solution
    solution = PuzzleSolver.find_one_solution(puzzle)
    assert solution is not None, "Puzzle should be satisfiable"


def test_generated_puzzle_no_redundant_statements():
    """Test that generated puzzles don't contain redundant/equivalent statements."""
    config = GenerationConfig(
        N=6,
        statements_per_speaker_min=2,
        statements_per_speaker_max=3,
        max_attempts=100,
    )

    # Build truth cache
    statement_library = build_statement_library(config)
    truth_cache = StatementTruthTableCache.build_for_statement_library(
        statement_library, config.N
    )

    # Generate multiple puzzles to increase chance of catching redundancy
    for run in range(10):
        puzzle = generate_puzzle(config, truth_cache)

        assert puzzle is not None, f"Failed to generate puzzle on run {run + 1}"

        # Check each speaker's bundle for redundant statements
        for speaker_idx, statements in enumerate(puzzle.statements_by_speaker):
            if len(statements) <= 1:
                continue  # No redundancy possible with 0 or 1 statement

            # Check all pairs of statements in the bundle
            for i, statement_a in enumerate(statements):
                for j, statement_b in enumerate(statements):
                    if i >= j:
                        continue  # Only check each pair once

                    # Verify that neither statement contains the other
                    a_contains_b = statement_contains_other(
                        statement_a, statement_b, truth_cache
                    )
                    b_contains_a = statement_contains_other(
                        statement_b, statement_a, truth_cache
                    )

                    assert not a_contains_b, (
                        f"Run {run + 1}, Speaker {speaker_idx} ({puzzle.villagers[speaker_idx].name}): "
                        f"Statement {i} ({statement_a.statement_id}) contains statement {j} ({statement_b.statement_id})"
                    )

                    assert not b_contains_a, (
                        f"Run {run + 1}, Speaker {speaker_idx} ({puzzle.villagers[speaker_idx].name}): "
                        f"Statement {j} ({statement_b.statement_id}) contains statement {i} ({statement_a.statement_id})"
                    )


def test_generated_puzzle_minimum_statements_per_speaker():
    """Test that all villagers have at least the minimum number of statements."""
    config = GenerationConfig(
        N=6,
        statements_per_speaker_min=2,
        statements_per_speaker_max=3,
        max_attempts=100,
    )

    # Build truth cache
    statement_library = build_statement_library(config)
    truth_cache = StatementTruthTableCache.build_for_statement_library(
        statement_library, config.N
    )

    # Generate multiple puzzles to increase chance of catching issues
    for run in range(10):
        puzzle = generate_puzzle(config, truth_cache)

        assert puzzle is not None, f"Failed to generate puzzle on run {run + 1}"

        # Verify all villagers have at least the minimum number of statements
        min_statements = config.statements_per_speaker_min
        for i, statements in enumerate(puzzle.statements_by_speaker):
            assert len(statements) >= min_statements, (
                f"Run {run + 1}: Villager {i} ({puzzle.villagers[i].name}) has only {len(statements)} "
                f"statement(s), but minimum is {min_statements}"
            )
