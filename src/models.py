"""Core data models for the werewolf puzzle generator."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .statements import Statement


@dataclass
class Villager:
    """Represents a villager in the puzzle."""

    index: int
    name: str


@dataclass
class Puzzle:
    """Represents a complete werewolf puzzle."""

    villagers: list[Villager]
    statements_by_speaker: list[list["Statement"]]
    difficulty_score: float = 0.0
    solution_assignment: tuple[bool, ...] | None = None
    minion_assignment: tuple[bool, ...] | None = None


@dataclass
class GenerationConfig:
    """Configuration for puzzle generation."""

    N: int = 6
    statements_per_speaker_min: int = 2
    statements_per_speaker_max: int = 2
    require_unique_solution: bool = True

    forbid_self_reference: bool = True
    allow_count_statements: bool = True
    max_count_statements_total: int | None = None
    complexity_budget: int | None = None

    # Selection / search
    max_attempts: int = 100
    greedy_candidate_pool_size: int = 50

    # Optional constraints on target assignment
    min_werewolves: int | None = None
    max_werewolves: int | None = None
    has_minion: bool = False
