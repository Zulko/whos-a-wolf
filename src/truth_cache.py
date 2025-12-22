"""Truth table caching using bitmask representation."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .claims import Claim


def assignment_to_index(assignment: tuple[bool, ...]) -> int:
    """Convert an assignment tuple to a bitmask index.
    
    Args:
        assignment: Tuple of booleans representing W[0..N-1]
        
    Returns:
        Integer index where bit i is set if assignment[i] is True
    """
    index = 0
    for i, is_werewolf in enumerate(assignment):
        if is_werewolf:
            index |= 1 << i
    return index


def index_to_assignment(index: int, N: int) -> tuple[bool, ...]:
    """Convert a bitmask index to an assignment tuple.
    
    Args:
        index: Integer index (bitmask)
        N: Number of villagers
        
    Returns:
        Tuple of booleans representing W[0..N-1]
    """
    return tuple(bool(index & (1 << i)) for i in range(N))


def compute_human_wolf_masks(N: int) -> tuple[list[int], list[int]]:
    """Precompute masks for human/wolf assignments per speaker.
    
    Args:
        N: Number of villagers
        
    Returns:
        Tuple of (human_mask_by_speaker, wolf_mask_by_speaker)
        Each is a list of length N, where mask[i] is a bitmask of assignments
        where villager i is human/wolf respectively.
        
        Each mask is a bitmask where bit j is set if assignment j has
        villager i as human/wolf.
    """
    num_assignments = 1 << N
    human_mask_by_speaker = []
    wolf_mask_by_speaker = []
    
    for speaker_index in range(N):
        human_mask = 0
        wolf_mask = 0
        
        for assignment_idx in range(num_assignments):
            assignment = index_to_assignment(assignment_idx, N)
            if not assignment[speaker_index]:  # Human
                human_mask |= 1 << assignment_idx
            else:  # Wolf
                wolf_mask |= 1 << assignment_idx
        
        human_mask_by_speaker.append(human_mask)
        wolf_mask_by_speaker.append(wolf_mask)
    
    return human_mask_by_speaker, wolf_mask_by_speaker


class ClaimTruthTableCache:
    """Cache of truth masks for claims."""
    
    def __init__(self, N: int, claim_id_to_truth_mask: dict[str, int] | None = None):
        """Initialize a truth table cache.
        
        Args:
            N: Number of villagers
            claim_id_to_truth_mask: Dictionary mapping claim_id to truth mask
        """
        self.N = N
        self.claim_id_to_truth_mask = claim_id_to_truth_mask or {}
    
    @classmethod
    def build_for_claim_library(cls, claim_library: list["Claim"], N: int) -> "ClaimTruthTableCache":
        """Build a cache by evaluating all claims on all assignments.
        
        Args:
            claim_library: List of claims to cache
            N: Number of villagers
            
        Returns:
            ClaimTruthTableCache with precomputed truth masks
        """
        claim_id_to_truth_mask = {}
        all_assignments_mask = (1 << N) - 1
        
        for claim in claim_library:
            truth_mask = 0
            
            # Evaluate claim on all 2^N assignments
            for assignment_idx in range(1 << N):
                assignment = index_to_assignment(assignment_idx, N)
                if claim.evaluate_on_assignment(assignment):
                    truth_mask |= 1 << assignment_idx
            
            claim_id_to_truth_mask[claim.claim_id] = truth_mask
        
        return cls(N, claim_id_to_truth_mask)
    
    def save_to_json(self, path: str) -> None:
        """Save the cache to a JSON file.
        
        Args:
            path: Path to save the JSON file
        """
        data = {
            "N": self.N,
            "claim_id_to_truth_mask": {
                claim_id: str(mask)  # Convert to string for JSON (handles large integers)
                for claim_id, mask in self.claim_id_to_truth_mask.items()
            }
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_json(cls, path: str) -> "ClaimTruthTableCache":
        """Load a cache from a JSON file.
        
        Args:
            path: Path to the JSON file
            
        Returns:
            ClaimTruthTableCache loaded from file
        """
        with open(path, "r") as f:
            data = json.load(f)
        
        N = data["N"]
        claim_id_to_truth_mask = {
            claim_id: int(mask_str)  # Convert back from string
            for claim_id, mask_str in data["claim_id_to_truth_mask"].items()
        }
        
        return cls(N, claim_id_to_truth_mask)
    
    def get_truth_mask(self, claim: "Claim") -> int:
        """Get the truth mask for a claim.
        
        Args:
            claim: The claim to look up
            
        Returns:
            Truth mask (bitmask of assignments where claim is True)
            
        Raises:
            KeyError: If claim is not in cache
        """
        return self.claim_id_to_truth_mask[claim.claim_id]
    
    def get_false_mask(self, claim: "Claim") -> int:
        """Get the false mask for a claim (complement of truth mask).
        
        Args:
            claim: The claim to look up
            
        Returns:
            False mask (bitmask of assignments where claim is False)
        """
        num_assignments = 1 << self.N
        all_assignments_mask = (1 << num_assignments) - 1
        truth_mask = self.get_truth_mask(claim)
        return all_assignments_mask & (~truth_mask)

