"""Puzzle generation using greedy bitmask-based algorithm."""

import random
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .claims import Claim
    from .models import GenerationConfig, Puzzle
    from .truth_cache import ClaimTruthTableCache

from .claims import (
    AtLeastKWerewolves,
    AtLeastOne,
    AtMostKWerewolves,
    BothOrNeither,
    CountClaim,
    ExactlyKWerewolves,
    ExactlyOne,
    EvenNumberOfWerewolves,
    IfAThenB,
    IfNotAThenB,
    Neither,
    OddNumberOfWerewolves,
    RelationshipClaim,
)
from .models import GenerationConfig, Puzzle, Villager
from .truth_cache import (
    ClaimTruthTableCache,
    assignment_to_index,
    compute_human_wolf_masks,
    index_to_assignment,
)
from .utils import get_default_names


def choose_target_assignment(config: GenerationConfig) -> tuple[bool, ...]:
    """Choose a random target assignment W_star.
    
    Args:
        config: Generation configuration
        
    Returns:
        Tuple of booleans representing W[0..N-1]
    """
    N = config.N
    
    # If constraints on werewolf count, filter assignments
    if config.min_werewolves is not None or config.max_werewolves is not None:
        valid_assignments = []
        min_wolves = config.min_werewolves if config.min_werewolves is not None else 0
        max_wolves = config.max_werewolves if config.max_werewolves is not None else N
        
        for assignment_idx in range(1 << N):
            assignment = index_to_assignment(assignment_idx, N)
            werewolf_count = sum(assignment)
            if min_wolves <= werewolf_count <= max_wolves:
                valid_assignments.append(assignment)
        
        if valid_assignments:
            return random.choice(valid_assignments)
    
    # Otherwise, choose uniformly at random
    assignment_idx = random.randint(0, (1 << N) - 1)
    return index_to_assignment(assignment_idx, N)


def build_claim_library(config: GenerationConfig) -> list["Claim"]:
    """Build a library of all allowed claims.
    
    Args:
        config: Generation configuration
        
    Returns:
        List of all allowed claims
    """
    N = config.N
    claims = []
    
    # Relationship claims (all pairs)
    relationship_classes = [
        IfAThenB,
        BothOrNeither,
        AtLeastOne,
        ExactlyOne,
        IfNotAThenB,
        Neither,
    ]
    
    for a in range(N):
        for b in range(N):
            if a == b and config.forbid_self_reference:
                continue
            
            for claim_class in relationship_classes:
                claims.append(claim_class(a, b))
    
    # Count claims (if allowed)
    if config.allow_count_claims:
        all_indices = tuple(range(N))
        
        # Exactly K werewolves (for various K)
        for k in range(N + 1):
            claims.append(ExactlyKWerewolves(all_indices, k))
        
        # At most/at least K werewolves
        for k in range(N + 1):
            claims.append(AtMostKWerewolves(all_indices, k))
            claims.append(AtLeastKWerewolves(all_indices, k))
        
        # Parity claims
        claims.append(EvenNumberOfWerewolves(all_indices))
        claims.append(OddNumberOfWerewolves(all_indices))
        
        # Scoped claims (all except speaker)
        for speaker in range(N):
            scope = tuple(i for i in range(N) if i != speaker)
            if len(scope) > 0:
                # Exactly K in scope
                for k in range(len(scope) + 1):
                    claims.append(ExactlyKWerewolves(scope, k))
                # Parity in scope
                claims.append(EvenNumberOfWerewolves(scope))
                claims.append(OddNumberOfWerewolves(scope))
    
    return claims


def list_candidate_bundles_for_speaker(
    speaker_index: int,
    W_star: tuple[bool, ...],
    claim_library: list["Claim"],
    truth_cache: ClaimTruthTableCache,
    config: GenerationConfig,
) -> list[list["Claim"]]:
    """List candidate claim bundles for a speaker consistent with W_star.
    
    Args:
        speaker_index: Index of the speaker
        W_star: Target assignment
        claim_library: Library of available claims
        truth_cache: Truth table cache
        config: Generation configuration
        
    Returns:
        List of claim bundles (each bundle is a list of claims)
    """
    # Filter claims that don't violate self-reference rule
    if config.forbid_self_reference:
        available_claims = [
            c for c in claim_library
            if speaker_index not in c.variables_involved()
        ]
    else:
        available_claims = claim_library
    
    # Determine what the bundle must satisfy
    # If speaker is human: all claims must be true
    # If speaker is wolf: at least one claim must be false
    is_wolf = W_star[speaker_index]
    
    candidate_bundles = []
    min_claims = config.claims_per_speaker_min
    max_claims = config.claims_per_speaker_max
    
    # Generate bundles of size min_claims to max_claims
    for bundle_size in range(min_claims, max_claims + 1):
        # Sample combinations (don't enumerate all if too many)
        if len(available_claims) < 20:
            # Small library: enumerate all combinations
            for bundle in combinations(available_claims, bundle_size):
                bundle_list = list(bundle)
                # Check consistency with W_star
                all_true = all(
                    claim.evaluate_on_assignment(W_star)
                    for claim in bundle_list
                )
                
                if is_wolf:
                    # Wolf: at least one must be false
                    if not all_true:
                        candidate_bundles.append(bundle_list)
                else:
                    # Human: all must be true
                    if all_true:
                        candidate_bundles.append(bundle_list)
        else:
            # Large library: sample randomly
            for _ in range(config.greedy_candidate_pool_size):
                bundle = random.sample(available_claims, bundle_size)
                bundle_list = list(bundle)
                all_true = all(
                    claim.evaluate_on_assignment(W_star)
                    for claim in bundle_list
                )
                
                if is_wolf:
                    if not all_true:
                        candidate_bundles.append(bundle_list)
                else:
                    if all_true:
                        candidate_bundles.append(bundle_list)
    
    return candidate_bundles


def compute_bundle_all_true_mask(
    bundle: list["Claim"],
    truth_cache: ClaimTruthTableCache,
) -> int:
    """Compute the bitmask of assignments where all claims in bundle are true.
    
    Args:
        bundle: List of claims
        truth_cache: Truth table cache
        
    Returns:
        Bitmask where bit i is set if all claims are true under assignment i
    """
    N = truth_cache.N
    num_assignments = 1 << N  # 2^N assignments
    
    if not bundle:
        # Empty bundle: all assignments satisfy (all true)
        return (1 << num_assignments) - 1  # All bits set for 2^N assignments
    
    # Start with all assignments
    all_assignments_mask = (1 << num_assignments) - 1
    result_mask = all_assignments_mask
    
    # Intersect with truth mask of each claim
    for claim in bundle:
        truth_mask = truth_cache.get_truth_mask(claim)
        result_mask &= truth_mask
    
    return result_mask


def compute_speaker_compatibility_mask(
    speaker_index: int,
    bundle: list["Claim"],
    human_mask: int,
    wolf_mask: int,
    truth_cache: ClaimTruthTableCache,
) -> int:
    """Compute compatibility mask for a speaker with a given bundle.
    
    An assignment is compatible if it satisfies the truthfulness rule:
    AND(claims) == NOT(W[speaker])
    
    Args:
        speaker_index: Index of the speaker
        bundle: List of claims made by the speaker
        human_mask: Precomputed mask of assignments where speaker is human
        wolf_mask: Precomputed mask of assignments where speaker is wolf
        truth_cache: Truth table cache
        
    Returns:
        Bitmask of compatible assignments
    """
    bundle_all_true_mask = compute_bundle_all_true_mask(bundle, truth_cache)
    N = truth_cache.N
    num_assignments = 1 << N
    all_assignments_mask = (1 << num_assignments) - 1
    
    # Humans: must be in bundle_all_true_mask
    # Wolves: must be in NOT bundle_all_true_mask
    compat_mask = (
        (human_mask & bundle_all_true_mask) |
        (wolf_mask & (all_assignments_mask & (~bundle_all_true_mask)))
    )
    
    return compat_mask


def greedy_assign_claims_until_unique(
    W_star: tuple[bool, ...],
    candidate_bundles_by_speaker: list[list[list["Claim"]]],
    truth_cache: ClaimTruthTableCache,
    config: GenerationConfig,
) -> Puzzle | None:
    """Greedily assign claim bundles until uniqueness is achieved.
    
    Args:
        W_star: Target assignment
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
    
    # Track remaining possible assignments
    remaining_mask = all_assignments_mask
    
    # Track assigned bundles
    assigned_bundles: list[list["Claim"] | None] = [None] * N
    unassigned_speakers = list(range(N))
    
    # Greedy assignment loop
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
                    candidate_bundles,
                    config.greedy_candidate_pool_size
                )
            
            # Try each candidate bundle
            for bundle in candidate_bundles:
                compat_mask = compute_speaker_compatibility_mask(
                    speaker_idx,
                    bundle,
                    human_mask_by_speaker[speaker_idx],
                    wolf_mask_by_speaker[speaker_idx],
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
    
    # Check if we achieved uniqueness (only W_star_index bit set)
    if remaining_mask != (1 << W_star_index):
        return None  # Not unique yet
    
    # Build puzzle
    names = get_default_names(N)
    villagers = [Villager(i, names[i]) for i in range(N)]
    
    # Filter out None bundles (shouldn't happen, but safety check)
    claims_by_speaker = [
        bundle if bundle is not None else []
        for bundle in assigned_bundles
    ]
    
    puzzle = Puzzle(
        villagers=villagers,
        claims_by_speaker=claims_by_speaker,
        solution_assignment=W_star,
    )
    
    return puzzle


def generate_puzzle(
    config: GenerationConfig,
    truth_cache: ClaimTruthTableCache,
) -> Puzzle | None:
    """Generate a puzzle with unique solution.
    
    Args:
        config: Generation configuration
        truth_cache: Truth table cache
        
    Returns:
        Puzzle if successful, None if generation failed after max_attempts
    """
    for attempt in range(config.max_attempts):
        # Step 1: Choose target assignment
        W_star = choose_target_assignment(config)
        
        # Step 2: Build claim library
        claim_library = build_claim_library(config)
        
        # Step 3: Generate candidate bundles for each speaker
        candidate_bundles_by_speaker = []
        for speaker_idx in range(config.N):
            bundles = list_candidate_bundles_for_speaker(
                speaker_idx,
                W_star,
                claim_library,
                truth_cache,
                config,
            )
            candidate_bundles_by_speaker.append(bundles)
        
        # Step 4: Greedy assignment
        puzzle = greedy_assign_claims_until_unique(
            W_star,
            candidate_bundles_by_speaker,
            truth_cache,
            config,
        )
        
        if puzzle is None:
            continue  # Try again
        
        # Step 5: Verify with Z3 (sanity check)
        from .solver import PuzzleSolver
        if PuzzleSolver.is_uniquely_satisfiable(puzzle):
            return puzzle
    
    return None  # Failed after max_attempts

