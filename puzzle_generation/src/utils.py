"""Utility functions for the werewolf puzzle generator."""

from .truth_cache import assignment_to_index, index_to_assignment


# Default villager names for N=6
DEFAULT_NAMES = [
    "Alchemist Alice",
    "Baker Bob",
    "Captain Charlie",
    "Doctor Doris",
    "Elder Edith",
    "Farmer Frank",
]


def get_default_names(N: int) -> list[str]:
    """Get default villager names, extending if needed.

    Args:
        N: Number of villagers

    Returns:
        List of N villager names
    """
    if N <= len(DEFAULT_NAMES):
        return DEFAULT_NAMES[:N]

    # Extend with generic names
    names = DEFAULT_NAMES.copy()
    for i in range(len(DEFAULT_NAMES), N):
        names.append(f"Villager {i}")
    return names
