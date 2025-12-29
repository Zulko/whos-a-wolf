"""Truth table caching using bitmask representation."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .statements import Statement


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


def compute_minion_masks(N: int, M_star: tuple[bool, ...]) -> list[int]:
    """Precompute masks for minion assignments per speaker.

    Args:
        N: Number of villagers
        M_star: Minion assignment tuple (M_star[i] = True means villager i is a minion)

    Returns:
        List of length N, where mask[i] is a bitmask of assignments
        where villager i is a minion according to M_star.

        Each mask is a bitmask where bit j is set if assignment j has
        villager i as a minion (based on M_star).

    Note:
        This function computes masks assuming M_star is fixed. The mask
        represents which assignments are compatible with villager i being
        a minion according to M_star.
    """
    num_assignments = 1 << N
    minion_mask_by_speaker = []

    for speaker_index in range(N):
        minion_mask = 0

        # If this speaker is a minion in M_star, all assignments are compatible
        # (since M_star is fixed, we're checking compatibility)
        if M_star[speaker_index]:
            # All assignments where this speaker is NOT a werewolf are compatible
            for assignment_idx in range(num_assignments):
                assignment = index_to_assignment(assignment_idx, N)
                if not assignment[speaker_index]:  # Not a werewolf
                    minion_mask |= 1 << assignment_idx
        else:
            # This speaker is not a minion, so no assignments have them as minion
            minion_mask = 0

        minion_mask_by_speaker.append(minion_mask)

    return minion_mask_by_speaker


class StatementTruthTableCache:
    """Cache of truth masks for statements."""

    def __init__(
        self, N: int, statement_id_to_truth_mask: dict[str, int] | None = None
    ):
        """Initialize a truth table cache.

        Args:
            N: Number of villagers
            statement_id_to_truth_mask: Dictionary mapping statement_id to truth mask
        """
        self.N = N
        self.statement_id_to_truth_mask = statement_id_to_truth_mask or {}

    @classmethod
    def build_for_statement_library(
        cls, statement_library: list["Statement"], N: int
    ) -> "StatementTruthTableCache":
        """Build a cache by evaluating all statements on all assignments.

        Args:
            statement_library: List of statements to cache
            N: Number of villagers

        Returns:
            StatementTruthTableCache with precomputed truth masks
        """
        statement_id_to_truth_mask = {}
        all_assignments_mask = (1 << N) - 1

        for statement in statement_library:
            truth_mask = 0

            # Evaluate statement on all 2^N assignments
            for assignment_idx in range(1 << N):
                assignment = index_to_assignment(assignment_idx, N)
                if statement.evaluate_on_assignment(assignment):
                    truth_mask |= 1 << assignment_idx

            statement_id_to_truth_mask[statement.statement_id] = truth_mask

        return cls(N, statement_id_to_truth_mask)

    def save_to_json(self, path: str) -> None:
        """Save the cache to a JSON file.

        Args:
            path: Path to save the JSON file
        """
        data = {
            "N": self.N,
            "statement_id_to_truth_mask": {
                statement_id: str(
                    mask
                )  # Convert to string for JSON (handles large integers)
                for statement_id, mask in self.statement_id_to_truth_mask.items()
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, path: str) -> "StatementTruthTableCache":
        """Load a cache from a JSON file.

        Args:
            path: Path to the JSON file

        Returns:
            StatementTruthTableCache loaded from file
        """
        with open(path, "r") as f:
            data = json.load(f)

        N = data["N"]
        statement_id_to_truth_mask = {
            statement_id: int(mask_str)  # Convert back from string
            for statement_id, mask_str in data["statement_id_to_truth_mask"].items()
        }

        return cls(N, statement_id_to_truth_mask)

    def get_truth_mask(self, statement: "Statement") -> int:
        """Get the truth mask for a statement.

        Args:
            statement: The statement to look up

        Returns:
            Truth mask (bitmask of assignments where statement is True)

        Raises:
            KeyError: If statement is not in cache
        """
        return self.statement_id_to_truth_mask[statement.statement_id]

    def get_false_mask(self, statement: "Statement") -> int:
        """Get the false mask for a statement (complement of truth mask).

        Args:
            statement: The statement to look up

        Returns:
            False mask (bitmask of assignments where statement is False)
        """
        num_assignments = 1 << self.N
        all_assignments_mask = (1 << num_assignments) - 1
        truth_mask = self.get_truth_mask(statement)
        return all_assignments_mask & (~truth_mask)
