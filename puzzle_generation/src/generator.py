"""Puzzle generation using greedy bitmask-based algorithm."""

import random
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .statements import Statement
    from .models import GenerationConfig, Puzzle
    from .truth_cache import StatementTruthTableCache

from .statements import (
    AtLeastKWerewolves,
    AtLeastOne,
    AtMostKWerewolves,
    BothOrNeither,
    ExactlyKWerewolves,
    ExactlyOne,
    EvenNumberOfWerewolves,
    IfAThenB,
    Neither,
    OddNumberOfWerewolves,
)
from .models import GenerationConfig, Puzzle, Villager
from .truth_cache import (
    StatementTruthTableCache,
    assignment_to_index,
    compute_human_wolf_masks,
    compute_shill_masks,
    index_to_assignment,
)
from .utils import get_default_names


def statement_contains_other(
    statement_a: "Statement",
    statement_b: "Statement",
    truth_cache: StatementTruthTableCache,
) -> bool:
    """Check if statement A logically contains statement B.

    Statement A contains statement B if: whenever A is true, B is also true (A => B).
    This means A's truth mask must be a subset of B's truth mask.

    Args:
        statement_a: The potentially containing statement
        statement_b: The potentially contained statement
        truth_cache: Truth table cache

    Returns:
        True if statement_a contains statement_b, False otherwise
    """
    if statement_a == statement_b:
        return False  # A statement doesn't contain itself (avoid removing duplicates)

    mask_a = truth_cache.get_truth_mask(statement_a)
    mask_b = truth_cache.get_truth_mask(statement_b)

    # A contains B if: whenever A is true, B is also true
    # This means: (mask_a & ~mask_b) == 0
    # In other words: all bits set in mask_a must also be set in mask_b
    return (mask_a & ~mask_b) == 0


def statements_are_contradictory(
    statement_a: "Statement",
    statement_b: "Statement",
    truth_cache: StatementTruthTableCache,
) -> bool:
    """Check if two statements are contradictory.

    Two statements are contradictory if they can never both be true simultaneously.
    This means their truth masks have no overlap (intersection is empty).

    Args:
        statement_a: First statement
        statement_b: Second statement
        truth_cache: Truth table cache

    Returns:
        True if the statements are contradictory, False otherwise
    """
    if statement_a == statement_b:
        return False  # A statement is not contradictory with itself

    mask_a = truth_cache.get_truth_mask(statement_a)
    mask_b = truth_cache.get_truth_mask(statement_b)

    # Statements are contradictory if their truth masks have no overlap
    return (mask_a & mask_b) == 0


def bundle_has_contradictory_statements(
    bundle: list["Statement"],
    truth_cache: StatementTruthTableCache,
) -> bool:
    """Check if a bundle contains any pair of contradictory statements.

    Args:
        bundle: List of statements to check
        truth_cache: Truth table cache

    Returns:
        True if the bundle contains contradictory statements, False otherwise
    """
    if len(bundle) <= 1:
        return False

    for i, statement_a in enumerate(bundle):
        for j, statement_b in enumerate(bundle):
            if i < j:  # Check each pair only once
                if statements_are_contradictory(statement_a, statement_b, truth_cache):
                    return True

    return False


def filter_redundant_statements(
    bundle: list["Statement"],
    truth_cache: StatementTruthTableCache,
) -> list["Statement"]:
    """Remove redundant statements from a bundle.

    If statement A contains statement B, remove statement B (the weaker statement).
    If statement B contains statement A, remove statement A (the weaker statement).

    Args:
        bundle: List of statements to filter
        truth_cache: Truth table cache

    Returns:
        Filtered list of statements with redundancies removed
    """
    if len(bundle) <= 1:
        return bundle

    # Build a list of statements to keep
    # We'll check each statement against all others
    to_remove = set()

    for i, statement_a in enumerate(bundle):
        if i in to_remove:
            continue

        for j, statement_b in enumerate(bundle):
            if i == j or j in to_remove:
                continue

            # Check if statement_a contains statement_b
            if statement_contains_other(statement_a, statement_b, truth_cache):
                # statement_a contains statement_b, so remove statement_b (the weaker one)
                to_remove.add(j)
            # Check if statement_b contains statement_a
            elif statement_contains_other(statement_b, statement_a, truth_cache):
                # statement_b contains statement_a, so remove statement_a (the weaker one)
                to_remove.add(i)
                break  # No need to check further for statement_a

    # Return filtered bundle
    return [statement for idx, statement in enumerate(bundle) if idx not in to_remove]


def choose_target_assignment(
    config: GenerationConfig,
) -> tuple[tuple[bool, ...], tuple[bool, ...]]:
    """Choose a random target assignment W_star and M_star.

    Args:
        config: Generation configuration

    Returns:
        Tuple of (W_star, M_star) where:
        - W_star: Tuple of booleans representing W[0..N-1] (werewolf assignment)
        - M_star: Tuple of booleans representing M[0..N-1] (shill assignment)
    """
    N = config.N

    # If shills are enabled, cap max_werewolves at N-1 (need at least one non-werewolf for shill)
    effective_max_werewolves = config.max_werewolves
    if config.has_shill:
        if effective_max_werewolves is not None:
            effective_max_werewolves = min(effective_max_werewolves, N - 1)
        else:
            effective_max_werewolves = N - 1

    # If constraints on werewolf count, filter assignments
    if config.min_werewolves is not None or effective_max_werewolves is not None:
        valid_assignments = []
        min_wolves = config.min_werewolves if config.min_werewolves is not None else 0
        max_wolves = (
            effective_max_werewolves if effective_max_werewolves is not None else N
        )

        for assignment_idx in range(1 << N):
            assignment = index_to_assignment(assignment_idx, N)
            werewolf_count = sum(assignment)
            if min_wolves <= werewolf_count <= max_wolves:
                valid_assignments.append(assignment)

        if valid_assignments:
            W_star = random.choice(valid_assignments)
        else:
            # Fallback: choose uniformly at random
            assignment_idx = random.randint(0, (1 << N) - 1)
            W_star = index_to_assignment(assignment_idx, N)
    else:
        # Otherwise, choose uniformly at random
        assignment_idx = random.randint(0, (1 << N) - 1)
        W_star = index_to_assignment(assignment_idx, N)

    # Generate shill assignment if enabled
    if config.has_shill:
        # Select exactly one non-werewolf to be the shill
        non_werewolves = [i for i in range(N) if not W_star[i]]
        if not non_werewolves:
            # No non-werewolves available, return all False for shills
            M_star = tuple(False for _ in range(N))
        else:
            shill_index = random.choice(non_werewolves)
            M_star = tuple(i == shill_index for i in range(N))
    else:
        M_star = tuple(False for _ in range(N))

    return (W_star, M_star)


def build_statement_library(config: GenerationConfig) -> list["Statement"]:
    """Build a library of all allowed statements.

    Args:
        config: Generation configuration

    Returns:
        List of all allowed statements
    """
    N = config.N
    statements = []

    # Relationship statements
    # Symmetrical relationships: only create one instance per unordered pair
    symmetrical_classes = [
        BothOrNeither,
        AtLeastOne,
        ExactlyOne,
        Neither,
    ]

    # Non-symmetrical relationships: create for all ordered pairs
    # Note: IfNotAThenB is excluded because it's logically equivalent to AtLeastOne
    # ((NOT W[a]) => W[b] ≡ W[a] OR W[b])
    non_symmetrical_classes = [
        IfAThenB,
    ]

    # Create symmetrical relationship statements (only a <= b to avoid duplicates)
    for a in range(N):
        for b in range(a, N):
            if a == b and config.forbid_self_reference:
                continue

            for statement_class in symmetrical_classes:
                statements.append(statement_class(a, b))

    # Create non-symmetrical relationship statements (all ordered pairs)
    for a in range(N):
        for b in range(N):
            if a == b and config.forbid_self_reference:
                continue

            for statement_class in non_symmetrical_classes:
                statements.append(statement_class(a, b))

    # Count statements (if allowed)
    if config.allow_count_statements:
        all_indices = tuple(range(N))

        # Exactly K werewolves (for various K, minimum 1)
        for k in range(1, N + 1):
            statements.append(ExactlyKWerewolves(all_indices, k))

        # At most/at least K werewolves
        for k in range(N + 1):
            statements.append(AtMostKWerewolves(all_indices, k))
            statements.append(AtLeastKWerewolves(all_indices, k))

        # Parity statements
        statements.append(EvenNumberOfWerewolves(all_indices))
        statements.append(OddNumberOfWerewolves(all_indices))

        # Scoped statements (all except speaker)
        for speaker in range(N):
            scope = tuple(i for i in range(N) if i != speaker)
            if len(scope) > 0:
                # Exactly K in scope (minimum 1)
                for k in range(1, len(scope) + 1):
                    statements.append(ExactlyKWerewolves(scope, k))
                # Parity in scope
                statements.append(EvenNumberOfWerewolves(scope))
                statements.append(OddNumberOfWerewolves(scope))

    return statements


def list_candidate_bundles_for_speaker(
    speaker_index: int,
    W_star: tuple[bool, ...],
    M_star: tuple[bool, ...],
    statement_library: list["Statement"],
    truth_cache: StatementTruthTableCache,
    config: GenerationConfig,
) -> list[list["Statement"]]:
    """List candidate statement bundles for a speaker consistent with W_star and M_star.

    Args:
        speaker_index: Index of the speaker
        W_star: Target werewolf assignment
        M_star: Target shill assignment
        statement_library: Library of available statements
        truth_cache: Truth table cache
        config: Generation configuration

    Returns:
        List of statement bundles (each bundle is a list of statements)
    """

    def _bundle_reuses_same_two_people(bundle: list["Statement"]) -> bool:
        """Return True if bundle's first two statements involve the exact same pair of people.

        We keep this narrowly focused (size==2 variable sets) so we don't overly
        constrain count-statements, while still improving dialogue variety.
        """
        if len(bundle) < 2:
            return False
        v0 = bundle[0].variables_involved()
        v1 = bundle[1].variables_involved()
        return len(v0) == 2 and v0 == v1

    # Filter statements that don't violate self-reference rule
    if config.forbid_self_reference:
        available_statements = [
            c for c in statement_library if speaker_index not in c.variables_involved()
        ]
    else:
        available_statements = statement_library

    # Determine what the bundle must satisfy
    # If speaker is human: all statements must be true
    # If speaker is wolf or shill: at least one statement must be false
    is_wolf = W_star[speaker_index]
    is_shill = M_star[speaker_index]
    can_lie = is_wolf or is_shill

    candidate_bundles = []
    min_statements = config.statements_per_speaker_min
    max_statements = config.statements_per_speaker_max

    # Generate bundles of size min_statements to max_statements
    for bundle_size in range(min_statements, max_statements + 1):
        # Sample combinations (don't enumerate all if too many)
        if len(available_statements) < 20:
            # Small library: enumerate all combinations
            for bundle in combinations(available_statements, bundle_size):
                bundle_list = list(bundle)
                # Check consistency with W_star
                all_true = all(
                    statement.evaluate_on_assignment(W_star)
                    for statement in bundle_list
                )

                if can_lie:
                    # Wolf or shill: at least one must be false
                    if not all_true:
                        # Filter out bundles with contradictory statements (would make it obvious they're a werewolf/shill)
                        if bundle_has_contradictory_statements(
                            bundle_list, truth_cache
                        ):
                            continue
                        # Filter redundant statements before adding
                        filtered_bundle = filter_redundant_statements(
                            bundle_list, truth_cache
                        )
                        # Only add if bundle meets minimum size requirement after filtering
                        if len(filtered_bundle) >= min_statements:
                            candidate_bundles.append(filtered_bundle)
                else:
                    # Human: all must be true
                    if all_true:
                        # Filter redundant statements before adding
                        filtered_bundle = filter_redundant_statements(
                            bundle_list, truth_cache
                        )
                        # Only add if bundle meets minimum size requirement after filtering
                        if len(filtered_bundle) >= min_statements:
                            candidate_bundles.append(filtered_bundle)
        else:
            # Large library: sample randomly
            for _ in range(config.greedy_candidate_pool_size):
                bundle = random.sample(available_statements, bundle_size)
                bundle_list = list(bundle)
                all_true = all(
                    statement.evaluate_on_assignment(W_star)
                    for statement in bundle_list
                )

                if can_lie:
                    if not all_true:
                        # Filter out bundles with contradictory statements (would make it obvious they're a werewolf/shill)
                        if bundle_has_contradictory_statements(
                            bundle_list, truth_cache
                        ):
                            continue
                        # Filter redundant statements before adding
                        filtered_bundle = filter_redundant_statements(
                            bundle_list, truth_cache
                        )
                        # Only add if bundle meets minimum size requirement after filtering
                        if len(filtered_bundle) >= min_statements:
                            candidate_bundles.append(filtered_bundle)
                else:
                    if all_true:
                        # Filter redundant statements before adding
                        filtered_bundle = filter_redundant_statements(
                            bundle_list, truth_cache
                        )
                        # Only add if bundle meets minimum size requirement after filtering
                        if len(filtered_bundle) >= min_statements:
                            candidate_bundles.append(filtered_bundle)

    # Preference: if we have enough options, avoid bundles where statement 1 and statement 2
    # talk about the exact same two people (better narrative variety).
    if min_statements >= 2 and candidate_bundles:
        good = [b for b in candidate_bundles if not _bundle_reuses_same_two_people(b)]
        if good:
            return good

    return candidate_bundles


def compute_bundle_all_true_mask(
    bundle: list["Statement"],
    truth_cache: StatementTruthTableCache,
) -> int:
    """Compute the bitmask of assignments where all statements in bundle are true.

    Args:
        bundle: List of statements
        truth_cache: Truth table cache

    Returns:
        Bitmask where bit i is set if all statements are true under assignment i
    """
    N = truth_cache.N
    num_assignments = 1 << N  # 2^N assignments

    if not bundle:
        # Empty bundle: all assignments satisfy (all true)
        return (1 << num_assignments) - 1  # All bits set for 2^N assignments

    # Start with all assignments
    all_assignments_mask = (1 << num_assignments) - 1
    result_mask = all_assignments_mask

    # Intersect with truth mask of each statement
    for statement in bundle:
        truth_mask = truth_cache.get_truth_mask(statement)
        result_mask &= truth_mask

    return result_mask


def compute_speaker_compatibility_mask(
    speaker_index: int,
    bundle: list["Statement"],
    human_mask: int,
    wolf_mask: int,
    shill_mask: int | None,
    truth_cache: StatementTruthTableCache,
) -> int:
    """Compute compatibility mask for a speaker with a given bundle.

    An assignment is compatible if it satisfies the truthfulness rule:
    - Humans: AND(statements) == True
    - Werewolves and shills: AND(statements) == False
    - So: AND(statements) == NOT(W[speaker]) AND NOT(M[speaker])

    Args:
        speaker_index: Index of the speaker
        bundle: List of statements made by the speaker
        human_mask: Precomputed mask of assignments where speaker is human
        wolf_mask: Precomputed mask of assignments where speaker is wolf
        shill_mask: Precomputed mask of assignments where speaker is shill (None if shills disabled)
        truth_cache: Truth table cache

    Returns:
        Bitmask of compatible assignments
    """
    bundle_all_true_mask = compute_bundle_all_true_mask(bundle, truth_cache)
    N = truth_cache.N
    num_assignments = 1 << N
    all_assignments_mask = (1 << num_assignments) - 1

    if shill_mask is not None:
        # Humans: must be in bundle_all_true_mask
        # Wolves and shills: must be in NOT bundle_all_true_mask
        compat_mask = (human_mask & bundle_all_true_mask) | (
            (wolf_mask | shill_mask) & (all_assignments_mask & (~bundle_all_true_mask))
        )
    else:
        # Original logic: Humans tell truth, wolves lie
        compat_mask = (human_mask & bundle_all_true_mask) | (
            wolf_mask & (all_assignments_mask & (~bundle_all_true_mask))
        )

    return compat_mask


def get_statement_types(bundle: list["Statement"]) -> set[str]:
    """Extract the set of statement type names from a bundle.

    Args:
        bundle: List of statements

    Returns:
        Set of statement type names (class names)
    """
    return {type(stmt).__name__ for stmt in bundle}


def greedy_assign_statements_until_unique(
    W_star: tuple[bool, ...],
    M_star: tuple[bool, ...],
    candidate_bundles_by_speaker: list[list[list["Statement"]]],
    truth_cache: StatementTruthTableCache,
    config: GenerationConfig,
) -> Puzzle | None:
    """Greedily assign statement bundles until uniqueness is achieved.

    Args:
        W_star: Target werewolf assignment
        M_star: Target shill assignment
        candidate_bundles_by_speaker: List of candidate bundles for each speaker
        truth_cache: Truth table cache
        config: Generation configuration

    Returns:
        Puzzle if successful, None if failed
    """
    N = config.N
    W_star_index = assignment_to_index(W_star)
    num_assignments = 1 << N
    all_assignments_mask = (1 << num_assignments) - 1

    # Precompute human/wolf masks
    human_mask_by_speaker, wolf_mask_by_speaker = compute_human_wolf_masks(N)

    # Precompute shill masks if shills are enabled
    shill_mask_by_speaker = None
    if config.has_shill:
        shill_mask_by_speaker = compute_shill_masks(N, M_star)

    # Track remaining possible assignments
    remaining_mask = all_assignments_mask

    # Track assigned bundles
    assigned_bundles: list[list["Statement"] | None] = [None] * N
    unassigned_speakers = list(range(N))

    # Track claimed statement types for diversity enforcement
    claimed_statement_types: set[str] = set()

    # Phase 1: Greedy assignment until uniqueness is achieved
    while unassigned_speakers and remaining_mask != (1 << W_star_index):
        best_speaker = None
        best_bundle = None
        best_new_mask = None
        best_eliminations = -1

        # Try each unassigned speaker
        for speaker_idx in unassigned_speakers:
            candidate_bundles = candidate_bundles_by_speaker[speaker_idx]

            # Sample a subset if too many
            if len(candidate_bundles) > config.greedy_candidate_pool_size:
                candidate_bundles = random.sample(
                    candidate_bundles, config.greedy_candidate_pool_size
                )

            # Try each candidate bundle
            for bundle in candidate_bundles:
                # Ensure bundle meets minimum size requirement
                if len(bundle) < config.statements_per_speaker_min:
                    continue

                # Enforce diversity: bundle must contain at least one unclaimed statement type
                if config.diverse_statements:
                    bundle_types = get_statement_types(bundle)
                    # Check if bundle has at least one unclaimed type
                    if not (bundle_types - claimed_statement_types):
                        continue  # All types in bundle are already claimed, skip it

                shill_mask = (
                    shill_mask_by_speaker[speaker_idx]
                    if shill_mask_by_speaker is not None
                    else None
                )
                compat_mask = compute_speaker_compatibility_mask(
                    speaker_idx,
                    bundle,
                    human_mask_by_speaker[speaker_idx],
                    wolf_mask_by_speaker[speaker_idx],
                    shill_mask,
                    truth_cache,
                )

                # New remaining mask after adding this bundle
                new_mask = remaining_mask & compat_mask

                # Check if W_star is still possible
                if not (new_mask & (1 << W_star_index)):
                    continue  # This bundle eliminates W_star, skip it

                # Count how many assignments this eliminates
                eliminations = bin(remaining_mask).count("1") - bin(new_mask).count("1")

                if eliminations > best_eliminations:
                    best_speaker = speaker_idx
                    best_bundle = bundle
                    best_new_mask = new_mask
                    best_eliminations = eliminations

        # If no bundle found that keeps W_star, fail
        if best_speaker is None:
            return None

        # Assign the best bundle
        assigned_bundles[best_speaker] = best_bundle
        remaining_mask = best_new_mask
        unassigned_speakers.remove(best_speaker)
        # Mark statement types as claimed for diversity enforcement
        if config.diverse_statements:
            claimed_statement_types.update(get_statement_types(best_bundle))

    # Check if we achieved uniqueness (only W_star_index bit set)
    if remaining_mask != (1 << W_star_index):
        return None  # Not unique yet

    # Phase 2: Assign bundles to remaining speakers while maintaining uniqueness
    # Once uniqueness is achieved, any bundle consistent with W_star will maintain it
    while unassigned_speakers:
        best_speaker = None
        best_bundle = None

        # Try each unassigned speaker
        for speaker_idx in unassigned_speakers:
            candidate_bundles = candidate_bundles_by_speaker[speaker_idx]

            # Sample a subset if too many
            if len(candidate_bundles) > config.greedy_candidate_pool_size:
                candidate_bundles = random.sample(
                    candidate_bundles, config.greedy_candidate_pool_size
                )

            # Try each candidate bundle
            for bundle in candidate_bundles:
                # Ensure bundle meets minimum size requirement
                if len(bundle) < config.statements_per_speaker_min:
                    continue

                # Enforce diversity: bundle must contain at least one unclaimed statement type
                if config.diverse_statements:
                    bundle_types = get_statement_types(bundle)
                    # Check if bundle has at least one unclaimed type
                    if not (bundle_types - claimed_statement_types):
                        continue  # All types in bundle are already claimed, skip it

                shill_mask = (
                    shill_mask_by_speaker[speaker_idx]
                    if shill_mask_by_speaker is not None
                    else None
                )
                compat_mask = compute_speaker_compatibility_mask(
                    speaker_idx,
                    bundle,
                    human_mask_by_speaker[speaker_idx],
                    wolf_mask_by_speaker[speaker_idx],
                    shill_mask,
                    truth_cache,
                )

                # New remaining mask after adding this bundle
                new_mask = remaining_mask & compat_mask

                # Check if W_star is still possible (this maintains uniqueness since
                # remaining_mask already only contains W_star_index)
                if new_mask & (1 << W_star_index):
                    # This bundle is consistent with W_star, use it
                    best_speaker = speaker_idx
                    best_bundle = bundle
                    remaining_mask = new_mask
                    break  # Found a valid bundle for this speaker

            if best_speaker is not None:
                break  # Found a bundle, assign it

        # If no bundle found that keeps W_star, fail
        if best_speaker is None:
            return None

        # Assign the bundle
        assigned_bundles[best_speaker] = best_bundle
        unassigned_speakers.remove(best_speaker)
        # Mark statement types as claimed for diversity enforcement
        if config.diverse_statements:
            claimed_statement_types.update(get_statement_types(best_bundle))

    # Final check: ensure uniqueness is maintained
    if remaining_mask != (1 << W_star_index):
        return None  # Uniqueness lost

    # Build puzzle
    names = get_default_names(N)
    villagers = [Villager(i, names[i]) for i in range(N)]

    # Filter out None bundles and redundant statements (shouldn't happen, but safety check)
    statements_by_speaker = []
    min_statements = config.statements_per_speaker_min
    for bundle in assigned_bundles:
        if bundle is None:
            # This shouldn't happen, but if it does, we can't meet the minimum requirement
            return None
        else:
            # Filter redundant statements one more time before finalizing
            filtered_bundle = filter_redundant_statements(bundle, truth_cache)
            # Ensure bundle still meets minimum size requirement after filtering
            if len(filtered_bundle) < min_statements:
                return None  # Bundle doesn't meet minimum requirement
            statements_by_speaker.append(filtered_bundle)

    # Final verification: ensure all villagers have at least min_statements
    for i, statements in enumerate(statements_by_speaker):
        if len(statements) < min_statements:
            return None  # Villager doesn't meet minimum requirement

    puzzle = Puzzle(
        villagers=villagers,
        statements_by_speaker=statements_by_speaker,
        solution_assignment=W_star,
        shill_assignment=M_star if config.has_shill else None,
    )

    return puzzle


def generate_puzzle(
    config: GenerationConfig,
    truth_cache: StatementTruthTableCache,
) -> Puzzle | None:
    """Generate a puzzle with unique solution.

    Args:
        config: Generation configuration
        truth_cache: Truth table cache

    Returns:
        Puzzle if successful, None if generation failed after max_attempts
    """
    for attempt in range(config.max_attempts):
        # Step 1: Choose target assignment (both werewolf and shill)
        W_star, M_star = choose_target_assignment(config)

        # Step 2: Build statement library
        statement_library = build_statement_library(config)

        # Step 3: Generate candidate bundles for each speaker
        candidate_bundles_by_speaker = []
        for speaker_idx in range(config.N):
            bundles = list_candidate_bundles_for_speaker(
                speaker_idx,
                W_star,
                M_star,
                statement_library,
                truth_cache,
                config,
            )
            candidate_bundles_by_speaker.append(bundles)

        # Step 4: Greedy assignment
        puzzle = greedy_assign_statements_until_unique(
            W_star,
            M_star,
            candidate_bundles_by_speaker,
            truth_cache,
            config,
        )

        if puzzle is None:
            continue  # Try again

        # Step 5: Verify with Z3 (sanity check) and compute difficulty
        from .solver import PuzzleSolver

        if PuzzleSolver.is_uniquely_satisfiable(puzzle):
            # Compute and store difficulty score
            puzzle.difficulty_score = PuzzleSolver.estimate_difficulty(
                puzzle, truth_cache
            )
            return puzzle

    return None  # Failed after max_attempts
