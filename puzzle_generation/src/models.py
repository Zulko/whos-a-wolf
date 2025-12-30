"""Core data models for the werewolf puzzle generator."""

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .statements import Statement

from .statements import Statement  # Import for runtime use in from_dict


@dataclass
class Villager:
    """Represents a villager in the puzzle."""

    index: int
    name: str

    def to_dict(self) -> dict:
        """Convert villager to dictionary.

        Returns:
            Dictionary representation of the villager
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Villager":
        """Create villager from dictionary.

        Args:
            data: Dictionary with 'index' and 'name' keys

        Returns:
            Villager instance
        """
        return cls(**data)


@dataclass
class Puzzle:
    """Represents a complete werewolf puzzle."""

    villagers: list[Villager]
    statements_by_speaker: list[list["Statement"]]
    difficulty_score: float = 0.0
    solution_assignment: tuple[bool, ...] | None = None
    shill_assignment: tuple[bool, ...] | None = None

    def to_short_statements_string(self) -> str:
        """Return a short string representation of all statements.

        Returns:
            String like "I-5-7_N-3-4_B-0-1" where statements are separated by underscores
        """
        all_statements = []
        for bundle in self.statements_by_speaker:
            for stmt in bundle:
                all_statements.append(stmt.to_short_string())
        return "_".join(all_statements)

    def to_dict(self) -> dict:
        """Convert puzzle to dictionary.

        Converts Statement objects to dictionaries and
        converts tuples to lists for JSON compatibility.

        Returns:
            Dictionary representation of the puzzle
        """
        data = asdict(self)
        # Convert villagers using their to_dict method
        data["villagers"] = [v.to_dict() for v in self.villagers]
        # Convert Statement objects to dictionaries
        data["statements_by_speaker"] = [
            [stmt.to_dict() for stmt in bundle] for bundle in self.statements_by_speaker
        ]
        # Convert tuples to lists for JSON compatibility
        if self.solution_assignment is not None:
            data["solution_assignment"] = list(self.solution_assignment)
        if self.shill_assignment is not None:
            data["shill_assignment"] = list(self.shill_assignment)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Puzzle":
        """Create puzzle from dictionary.

        Args:
            data: Dictionary with puzzle data

        Returns:
            Puzzle instance
        """
        # Reconstruct villagers
        villagers = [Villager.from_dict(v_data) for v_data in data["villagers"]]
        # Reconstruct statements from dictionaries
        statements_by_speaker = [
            [Statement.from_dict(stmt_dict) for stmt_dict in bundle]
            for bundle in data["statements_by_speaker"]
        ]
        # Convert lists back to tuples
        solution_assignment = (
            tuple(data["solution_assignment"])
            if data.get("solution_assignment") is not None
            else None
        )
        shill_assignment = (
            tuple(data["shill_assignment"])
            if data.get("shill_assignment") is not None
            else None
        )
        return cls(
            villagers=villagers,
            statements_by_speaker=statements_by_speaker,
            difficulty_score=data.get("difficulty_score", 0.0),
            solution_assignment=solution_assignment,
            shill_assignment=shill_assignment,
        )


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
    has_shill: bool = False
    diverse_statements: bool = False

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationConfig":
        """Create configuration from dictionary.

        Args:
            data: Dictionary with configuration data

        Returns:
            GenerationConfig instance
        """
        return cls(**data)
