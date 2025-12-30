"""Check for duplicate games that are identical under permutation of villager indices."""

import argparse
import json
import sys
from collections import Counter
from itertools import permutations
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Puzzle


def get_statement_signature(stmt_dict: dict) -> tuple:
    """Get a signature for a statement that captures its structure.
    
    Returns a tuple that uniquely identifies the statement type and its parameters
    (excluding specific indices, which will be permuted).
    """
    stmt_type = stmt_dict["type"]
    
    if stmt_type in ("IfAThenB", "IfNotAThenB"):
        # These are directional, so we need to preserve the direction
        return (stmt_type, "pair")
    elif stmt_type in ("BothOrNeither", "AtLeastOne", "ExactlyOne", "Neither"):
        # These are symmetric, so order doesn't matter
        return (stmt_type, "pair")
    elif stmt_type in ("ExactlyKWerewolves", "AtMostKWerewolves", "AtLeastKWerewolves"):
        return (stmt_type, len(stmt_dict["scope_indices"]), stmt_dict.get("count"))
    elif stmt_type in ("EvenNumberOfWerewolves", "OddNumberOfWerewolves"):
        return (stmt_type, len(stmt_dict["scope_indices"]))
    else:
        return (stmt_type,)


def get_game_signature(puzzle: Puzzle) -> tuple:
    """Get a signature for a game that captures its structure.
    
    Returns a tuple that can be used to quickly filter out games that
    can't possibly be duplicates.
    """
    # Count werewolves
    if puzzle.solution_assignment is None:
        return None
    
    werewolf_count = sum(1 for w in puzzle.solution_assignment if w)
    
    # Get multiset of statement signatures
    statement_signatures = []
    for statements in puzzle.statements_by_speaker:
        for stmt in statements:
            stmt_dict = stmt.to_dict()
            statement_signatures.append(get_statement_signature(stmt_dict))
    
    # Sort to make comparison order-independent
    statement_signatures.sort()
    
    return (werewolf_count, tuple(statement_signatures))


def apply_permutation_to_statement(stmt_dict: dict, perm: list[int]) -> dict:
    """Apply a permutation to a statement's indices.
    
    Args:
        stmt_dict: Statement dictionary
        perm: Permutation list where perm[i] is the new index for old index i
    
    Returns:
        New statement dictionary with permuted indices
    """
    new_stmt = stmt_dict.copy()
    stmt_type = stmt_dict["type"]
    
    if stmt_type in ("IfAThenB", "IfNotAThenB", "BothOrNeither", "AtLeastOne", 
                     "ExactlyOne", "Neither"):
        new_stmt["a_index"] = perm[stmt_dict["a_index"]]
        new_stmt["b_index"] = perm[stmt_dict["b_index"]]
    elif stmt_type in ("ExactlyKWerewolves", "AtMostKWerewolves", "AtLeastKWerewolves",
                       "EvenNumberOfWerewolves", "OddNumberOfWerewolves"):
        new_stmt["scope_indices"] = sorted([perm[i] for i in stmt_dict["scope_indices"]])
    
    return new_stmt


def normalize_statement_for_comparison(stmt_dict: dict) -> tuple:
    """Normalize a statement to a canonical form for comparison.
    
    For symmetric statements, normalizes indices to be in sorted order.
    For directional statements, preserves order.
    """
    stmt_type = stmt_dict["type"]
    
    if stmt_type in ("BothOrNeither", "AtLeastOne", "ExactlyOne", "Neither"):
        # These are symmetric, normalize indices
        a, b = stmt_dict["a_index"], stmt_dict["b_index"]
        return (stmt_type, min(a, b), max(a, b))
    elif stmt_type in ("IfAThenB", "IfNotAThenB"):
        # These are directional, preserve order
        return (stmt_type, stmt_dict["a_index"], stmt_dict["b_index"])
    elif stmt_type in ("ExactlyKWerewolves", "AtMostKWerewolves", "AtLeastKWerewolves"):
        scope = tuple(sorted(stmt_dict["scope_indices"]))
        return (stmt_type, scope, stmt_dict.get("count"))
    elif stmt_type in ("EvenNumberOfWerewolves", "OddNumberOfWerewolves"):
        scope = tuple(sorted(stmt_dict["scope_indices"]))
        return (stmt_type, scope)
    else:
        return (stmt_type,)


def get_normalized_statements(puzzle: Puzzle) -> list[tuple]:
    """Get normalized statements from a puzzle."""
    normalized = []
    for statements in puzzle.statements_by_speaker:
        for stmt in statements:
            stmt_dict = stmt.to_dict()
            normalized.append(normalize_statement_for_comparison(stmt_dict))
    return sorted(normalized)


def create_canonical_representation(puzzle: Puzzle) -> tuple | None:
    """Create a canonical representation of a puzzle that is invariant under permutation.
    
    This representation can be used to quickly identify duplicates without
    checking all permutations. However, it may have false positives, so we
    still need to verify with permutation checking.
    
    Returns:
        Canonical tuple representation, or None if puzzle is invalid
    """
    if puzzle.solution_assignment is None:
        return None
    
    N = len(puzzle.villagers)
    werewolf_count = sum(1 for w in puzzle.solution_assignment if w)
    
    # Create a representation based on statement patterns per speaker
    # Group speakers by: werewolf status, number of statements, statement types
    speaker_profiles = []
    for speaker_idx, statements in enumerate(puzzle.statements_by_speaker):
        is_werewolf = puzzle.solution_assignment[speaker_idx]
        stmt_types = sorted([stmt.to_dict()["type"] for stmt in statements])
        # Also capture the structure (pair vs count, scope sizes, etc.)
        stmt_structures = []
        for stmt in statements:
            stmt_dict = stmt.to_dict()
            stmt_type = stmt_dict["type"]
            if stmt_type in ("IfAThenB", "IfNotAThenB", "BothOrNeither", "AtLeastOne", 
                           "ExactlyOne", "Neither"):
                stmt_structures.append(("pair", stmt_type))
            elif stmt_type in ("ExactlyKWerewolves", "AtMostKWerewolves", "AtLeastKWerewolves"):
                stmt_structures.append(("count", stmt_type, len(stmt_dict["scope_indices"]), 
                                      stmt_dict.get("count")))
            elif stmt_type in ("EvenNumberOfWerewolves", "OddNumberOfWerewolves"):
                stmt_structures.append(("count", stmt_type, len(stmt_dict["scope_indices"])))
        
        stmt_structures.sort()
        speaker_profiles.append((is_werewolf, tuple(stmt_types), tuple(stmt_structures)))
    
    # Sort speaker profiles to make order-independent
    speaker_profiles.sort()
    
    return (werewolf_count, tuple(speaker_profiles))


def are_games_duplicates(puzzle1: Puzzle, puzzle2: Puzzle) -> tuple[bool, list[int] | None]:
    """Check if two games are duplicates under permutation.
    
    Returns:
        (is_duplicate, permutation) where permutation is the mapping from
        puzzle1 indices to puzzle2 indices, or None if not duplicates
    """
    # Quick check: same signature
    sig1 = get_game_signature(puzzle1)
    sig2 = get_game_signature(puzzle2)
    
    if sig1 != sig2:
        return False, None
    
    if sig1 is None:
        return False, None
    
    # Check werewolf assignment
    if puzzle1.solution_assignment is None or puzzle2.solution_assignment is None:
        return False, None
    
    werewolves1 = {i for i, w in enumerate(puzzle1.solution_assignment) if w}
    werewolves2 = {i for i, w in enumerate(puzzle2.solution_assignment) if w}
    
    if len(werewolves1) != len(werewolves2):
        return False, None
    
    N = len(puzzle1.villagers)
    
    # Try all permutations that map werewolves to werewolves
    werewolf_list1 = sorted(werewolves1)
    werewolf_list2 = sorted(werewolves2)
    
    # Generate permutations that preserve werewolf assignment
    non_werewolves1 = sorted(set(range(N)) - werewolves1)
    non_werewolves2 = sorted(set(range(N)) - werewolves2)
    
    # Try permutations of werewolves and non-werewolves separately
    for ww_perm in permutations(werewolf_list2):
        ww_map = {werewolf_list1[i]: ww_perm[i] for i in range(len(werewolf_list1))}
        
        for nw_perm in permutations(non_werewolves2):
            nw_map = {non_werewolves1[i]: nw_perm[i] for i in range(len(non_werewolves1))}
            
            # Combine into full permutation
            perm = [0] * N
            for i in range(N):
                if i in werewolves1:
                    perm[i] = ww_map[i]
                else:
                    perm[i] = nw_map[i]
            
            # Apply permutation to puzzle1 and check if it matches puzzle2
            # Under permutation π, speaker i's statements become speaker π(i)'s statements
            # and all indices in those statements are permuted by π
            
            # Build permuted statements_by_speaker
            permuted_by_speaker = [[] for _ in range(N)]
            for speaker_idx, statements in enumerate(puzzle1.statements_by_speaker):
                new_speaker_idx = perm[speaker_idx]
                for stmt in statements:
                    stmt_dict = stmt.to_dict()
                    permuted_dict = apply_permutation_to_statement(stmt_dict, perm)
                    permuted_by_speaker[new_speaker_idx].append(
                        normalize_statement_for_comparison(permuted_dict)
                    )
            
            # Normalize each speaker's statements
            for speaker_statements in permuted_by_speaker:
                speaker_statements.sort()
            
            # Get normalized statements for puzzle2
            norm2_by_speaker = [[] for _ in range(N)]
            for speaker_idx, statements in enumerate(puzzle2.statements_by_speaker):
                for stmt in statements:
                    stmt_dict = stmt.to_dict()
                    norm2_by_speaker[speaker_idx].append(
                        normalize_statement_for_comparison(stmt_dict)
                    )
                norm2_by_speaker[speaker_idx].sort()
            
            # Check if they match
            if permuted_by_speaker == norm2_by_speaker:
                # Also verify werewolf assignment matches
                matches = all(
                    puzzle1.solution_assignment[i] == puzzle2.solution_assignment[perm[i]]
                    for i in range(N)
                )
                
                if matches:
                    return True, perm
    
    return False, None


def main() -> None:
    """Check for duplicate games in JSONL file."""
    parser = argparse.ArgumentParser(
        description="Check for duplicate games that are identical under permutation"
    )
    parser.add_argument(
        "file",
        type=str,
        help="JSONL file to check",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information about duplicates",
    )
    
    args = parser.parse_args()
    
    jsonl_file = Path(args.file)
    if not jsonl_file.exists():
        print(f"Error: {jsonl_file} not found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading {jsonl_file}...", file=sys.stderr)
    puzzles = []
    
    with open(jsonl_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                puzzle_dict = json.loads(line)
                puzzle = Puzzle.from_dict(puzzle_dict)
                puzzles.append((line_num, puzzle))
            except json.JSONDecodeError as e:
                print(
                    f"Error parsing JSON at line {line_num} in {jsonl_file}: {e}",
                    file=sys.stderr,
                )
                continue
            except Exception as e:
                print(
                    f"Error processing puzzle at line {line_num} in {jsonl_file}: {e}",
                    file=sys.stderr,
                )
                continue
    
    print(f"Loaded {len(puzzles)} puzzles", file=sys.stderr)
    print("Checking for duplicates...", file=sys.stderr)
    
    # Group by signature for efficiency (first filter)
    signature_groups: dict[tuple, list[tuple[int, Puzzle]]] = {}
    for line_num, puzzle in puzzles:
        sig = get_game_signature(puzzle)
        if sig is None:
            continue
        if sig not in signature_groups:
            signature_groups[sig] = []
        signature_groups[sig].append((line_num, puzzle))
    
    # Further filter by canonical representation (second filter)
    canonical_groups: dict[tuple, list[tuple[int, Puzzle]]] = {}
    for sig, group in signature_groups.items():
        for line_num, puzzle in group:
            canon = create_canonical_representation(puzzle)
            if canon is None:
                continue
            if canon not in canonical_groups:
                canonical_groups[canon] = []
            canonical_groups[canon].append((line_num, puzzle))
    
    # Only check pairs within the same canonical group
    duplicates_found = []
    checked_pairs = 0
    
    for canon, group in canonical_groups.items():
        if len(group) < 2:
            continue
        
        # Check all pairs in this group
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                line_num1, puzzle1 = group[i]
                line_num2, puzzle2 = group[j]
                
                checked_pairs += 1
                if checked_pairs % 100 == 0:
                    print(f"Checked {checked_pairs} pairs...", file=sys.stderr)
                
                is_dup, perm = are_games_duplicates(puzzle1, puzzle2)
                if is_dup:
                    duplicates_found.append((line_num1, line_num2, perm))
    
    print(f"\nChecked {checked_pairs} pairs", file=sys.stderr)
    print(f"Found {len(duplicates_found)} duplicate pairs\n", file=sys.stderr)
    
    # Report results
    if duplicates_found:
        print(f"DUPLICATES FOUND: {len(duplicates_found)} pairs")
        print("=" * 60)
        
        # Group duplicates into equivalence classes
        equivalence_classes = []
        used = set()
        
        for line_num1, line_num2, perm in duplicates_found:
            if line_num1 in used or line_num2 in used:
                # Add to existing class
                for cls in equivalence_classes:
                    if line_num1 in cls or line_num2 in cls:
                        cls.update([line_num1, line_num2])
                        break
            else:
                # New equivalence class
                equivalence_classes.append({line_num1, line_num2})
            
            used.add(line_num1)
            used.add(line_num2)
        
        # Merge overlapping classes
        merged = True
        while merged:
            merged = False
            for i in range(len(equivalence_classes)):
                for j in range(i + 1, len(equivalence_classes)):
                    if equivalence_classes[i] & equivalence_classes[j]:
                        equivalence_classes[i] |= equivalence_classes[j]
                        equivalence_classes.pop(j)
                        merged = True
                        break
                if merged:
                    break
        
        print(f"\nEquivalence classes: {len(equivalence_classes)}")
        for idx, cls in enumerate(equivalence_classes, 1):
            cls_list = sorted(cls)
            print(f"\nClass {idx}: Lines {cls_list}")
            if args.verbose:
                for line_num in cls_list:
                    _, puzzle = puzzles[line_num - 1]  # line_num is 1-indexed
                    werewolf_count = sum(1 for w in puzzle.solution_assignment if w) if puzzle.solution_assignment else 0
                    print(f"  Line {line_num}: {werewolf_count} werewolves")
        
        # Show individual pairs
        if args.verbose:
            print("\n" + "=" * 60)
            print("Individual duplicate pairs:")
            for line_num1, line_num2, perm in duplicates_found:
                print(f"\nLines {line_num1} <-> {line_num2}")
                print(f"  Permutation: {perm}")
    else:
        print("No duplicates found! All games are unique under permutation.")


if __name__ == "__main__":
    main()

