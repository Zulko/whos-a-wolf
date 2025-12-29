"""Statement classes representing boolean statements about werewolves."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from z3 import BoolRef


class Statement(ABC):
    """Abstract base class for all statements."""

    @property
    @abstractmethod
    def statement_id(self) -> str:
        """Return a stable canonical string identifier for this statement."""
        pass

    @abstractmethod
    def variables_involved(self) -> set[int]:
        """Return the set of villager indices referenced by this statement."""
        pass

    @abstractmethod
    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        """Evaluate this statement on a concrete assignment.

        Args:
            assignment: A tuple of booleans representing W[0..N-1]

        Returns:
            True if the statement is satisfied by this assignment, False otherwise
        """
        pass

    @abstractmethod
    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        """Convert this statement to a Z3 boolean expression.

        Args:
            W_vars: List of Z3 Bool variables, where W_vars[i] represents W[i]

        Returns:
            A Z3 BoolRef representing this statement
        """
        pass

    @abstractmethod
    def to_english(self, names: list[str]) -> str:
        """Convert this statement to English text.

        Args:
            names: List of villager names, where names[i] is the name of villager i

        Returns:
            English description of this statement
        """
        pass

    @abstractmethod
    def complexity_cost(self) -> int:
        """Return a complexity score for this statement (lower = simpler).

        Used to bias generation toward simpler puzzles.
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert statement to dictionary.

        Returns:
            Dictionary representation of the statement
        """
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Statement":
        """Create statement from dictionary.

        Args:
            data: Dictionary with statement data, must include 'type' field

        Returns:
            Statement instance

        Raises:
            ValueError: If the statement type is unknown
        """
        stmt_type = data.get("type")
        if stmt_type is None:
            raise ValueError("Statement dict must include 'type' field")

        if stmt_type == "IfAThenB":
            return IfAThenB(data["a_index"], data["b_index"])
        elif stmt_type == "BothOrNeither":
            return BothOrNeither(data["a_index"], data["b_index"])
        elif stmt_type == "AtLeastOne":
            return AtLeastOne(data["a_index"], data["b_index"])
        elif stmt_type == "ExactlyOne":
            return ExactlyOne(data["a_index"], data["b_index"])
        elif stmt_type == "IfNotAThenB":
            return IfNotAThenB(data["a_index"], data["b_index"])
        elif stmt_type == "Neither":
            return Neither(data["a_index"], data["b_index"])
        elif stmt_type == "ExactlyKWerewolves":
            scope = tuple(data["scope_indices"])
            return ExactlyKWerewolves(scope, data["count"])
        elif stmt_type == "AtMostKWerewolves":
            scope = tuple(data["scope_indices"])
            return AtMostKWerewolves(scope, data["count"])
        elif stmt_type == "AtLeastKWerewolves":
            scope = tuple(data["scope_indices"])
            return AtLeastKWerewolves(scope, data["count"])
        elif stmt_type == "EvenNumberOfWerewolves":
            scope = tuple(data["scope_indices"])
            return EvenNumberOfWerewolves(scope)
        elif stmt_type == "OddNumberOfWerewolves":
            scope = tuple(data["scope_indices"])
            return OddNumberOfWerewolves(scope)
        else:
            raise ValueError(f"Unknown statement type: {stmt_type}")

    def __hash__(self) -> int:
        """Hash based on statement_id for use in sets/dicts."""
        return hash(self.statement_id)

    def __eq__(self, other: object) -> bool:
        """Equality based on statement_id."""
        if not isinstance(other, Statement):
            return False
        return self.statement_id == other.statement_id


class RelationshipStatement(Statement):
    """Base class for statements involving two villagers."""

    def __init__(self, a_index: int, b_index: int):
        """Initialize a relationship statement.

        Args:
            a_index: Index of first villager
            b_index: Index of second villager
        """
        self.a_index = a_index
        self.b_index = b_index

    def variables_involved(self) -> set[int]:
        """Return the set of villager indices referenced."""
        return {self.a_index, self.b_index}

    def to_dict(self) -> dict:
        """Convert relationship statement to dictionary.

        Returns:
            Dictionary with 'type', 'a_index', and 'b_index' fields
        """
        return {
            "type": self.__class__.__name__,
            "a_index": self.a_index,
            "b_index": self.b_index,
        }


class CountStatement(Statement):
    """Base class for statements about counts of werewolves."""

    def __init__(self, scope_indices: tuple[int, ...]):
        """Initialize a count statement.

        Args:
            scope_indices: Tuple of villager indices in the scope
        """
        self.scope_indices = scope_indices

    def variables_involved(self) -> set[int]:
        """Return the set of villager indices referenced."""
        return set(self.scope_indices)

    def to_dict(self) -> dict:
        """Convert count statement to dictionary.

        Returns:
            Dictionary with 'type' and 'scope_indices' fields.
            Subclasses with 'count' should override to include it.
        """
        return {
            "type": self.__class__.__name__,
            "scope_indices": list(self.scope_indices),  # Convert tuple to list for JSON
        }


# Relationship Statement Subclasses


class IfAThenB(RelationshipStatement):
    """Semantics: W[a] => W[b]"""

    @property
    def statement_id(self) -> str:
        return f"IMP({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        # W[a] => W[b] is equivalent to NOT W[a] OR W[b]
        return not assignment[self.a_index] or assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # W[a] => W[b]
        return z3.Implies(W_vars[self.a_index], W_vars[self.b_index])

    def to_english(self, names: list[str]) -> str:
        return f"If {names[self.a_index]} is a werewolf, then {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1


class BothOrNeither(RelationshipStatement):
    """Semantics: W[a] == W[b]"""

    def __init__(self, a_index: int, b_index: int):
        """Initialize a BothOrNeither statement, normalizing indices for symmetry."""
        # Normalize: always store min(a, b) as a_index, max(a, b) as b_index
        super().__init__(min(a_index, b_index), max(a_index, b_index))

    @property
    def statement_id(self) -> str:
        return f"EQ({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        return assignment[self.a_index] == assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # W[a] == W[b]
        return W_vars[self.a_index] == W_vars[self.b_index]

    def to_english(self, names: list[str]) -> str:
        return f"{names[self.a_index]} and {names[self.b_index]} are both werewolves, or neither is."

    def complexity_cost(self) -> int:
        return 1


class AtLeastOne(RelationshipStatement):
    """Semantics: W[a] OR W[b]"""

    def __init__(self, a_index: int, b_index: int):
        """Initialize an AtLeastOne statement, normalizing indices for symmetry."""
        # Normalize: always store min(a, b) as a_index, max(a, b) as b_index
        super().__init__(min(a_index, b_index), max(a_index, b_index))

    @property
    def statement_id(self) -> str:
        return f"OR({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        return assignment[self.a_index] or assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # W[a] OR W[b]
        return z3.Or(W_vars[self.a_index], W_vars[self.b_index])

    def to_english(self, names: list[str]) -> str:
        return f"At least one of {names[self.a_index]} and {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1


class ExactlyOne(RelationshipStatement):
    """Semantics: W[a] XOR W[b] (i.e., W[a] != W[b])"""

    def __init__(self, a_index: int, b_index: int):
        """Initialize an ExactlyOne statement, normalizing indices for symmetry."""
        # Normalize: always store min(a, b) as a_index, max(a, b) as b_index
        super().__init__(min(a_index, b_index), max(a_index, b_index))

    @property
    def statement_id(self) -> str:
        return f"XOR({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        return assignment[self.a_index] != assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # W[a] != W[b]
        return W_vars[self.a_index] != W_vars[self.b_index]

    def to_english(self, names: list[str]) -> str:
        return f"Exactly one of {names[self.a_index]} and {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1


class IfNotAThenB(RelationshipStatement):
    """Semantics: (NOT W[a]) => W[b]"""

    @property
    def statement_id(self) -> str:
        return f"IMP_NOT({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        # (NOT W[a]) => W[b] is equivalent to W[a] OR W[b]
        return assignment[self.a_index] or assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # (NOT W[a]) => W[b]
        return z3.Implies(z3.Not(W_vars[self.a_index]), W_vars[self.b_index])

    def to_english(self, names: list[str]) -> str:
        return f"If {names[self.a_index]} is not a werewolf, then {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1


class Neither(RelationshipStatement):
    """Semantics: (NOT W[a]) AND (NOT W[b])"""

    def __init__(self, a_index: int, b_index: int):
        """Initialize a Neither statement, normalizing indices for symmetry."""
        # Normalize: always store min(a, b) as a_index, max(a, b) as b_index
        super().__init__(min(a_index, b_index), max(a_index, b_index))

    @property
    def statement_id(self) -> str:
        return f"NEITHER({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        return not assignment[self.a_index] and not assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # (NOT W[a]) AND (NOT W[b])
        return z3.And(z3.Not(W_vars[self.a_index]), z3.Not(W_vars[self.b_index]))

    def to_english(self, names: list[str]) -> str:
        return f"Neither {names[self.a_index]} nor {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 2  # Higher cost as this is a strong statement


# Count Statement Subclasses


class ExactlyKWerewolves(CountStatement):
    """Semantics: SUM(W[i] for i in scope) == count"""

    def __init__(self, scope_indices: tuple[int, ...], count: int):
        """Initialize an exactly-k statement.

        Args:
            scope_indices: Tuple of villager indices in the scope
            count: Exact number of werewolves required
        """
        super().__init__(scope_indices)
        self.count = count

    @property
    def statement_id(self) -> str:
        scope_str = ",".join(map(str, sorted(self.scope_indices)))
        return f"COUNT_EQ(scope=[{scope_str}],count={self.count})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        werewolf_count = sum(1 for i in self.scope_indices if assignment[i])
        return werewolf_count == self.count

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # SUM(W[i] for i in scope) == count
        total = sum(z3.If(W_vars[i], 1, 0) for i in self.scope_indices)
        return total == self.count

    def to_english(self, names: list[str]) -> str:
        scope_names = [names[i] for i in self.scope_indices]
        if len(scope_names) == 1:
            scope_desc = scope_names[0]
        elif len(scope_names) <= 3:
            scope_desc = ", ".join(scope_names[:-1]) + f", and {scope_names[-1]}"
        else:
            scope_desc = f"{len(scope_names)} villagers"
        return f"Exactly {self.count} werewolf{'ves' if self.count != 1 else ''} among {scope_desc}."

    def complexity_cost(self) -> int:
        # Higher cost for count statements, especially exact counts
        return 3

    def to_dict(self) -> dict:
        """Convert exactly-k statement to dictionary.

        Returns:
            Dictionary with 'type', 'scope_indices', and 'count' fields
        """
        return {
            "type": self.__class__.__name__,
            "scope_indices": list(self.scope_indices),  # Convert tuple to list for JSON
            "count": self.count,
        }


class AtMostKWerewolves(CountStatement):
    """Semantics: SUM(W[i] for i in scope) <= count"""

    def __init__(self, scope_indices: tuple[int, ...], count: int):
        """Initialize an at-most-k statement.

        Args:
            scope_indices: Tuple of villager indices in the scope
            count: Maximum number of werewolves allowed
        """
        super().__init__(scope_indices)
        self.count = count

    @property
    def statement_id(self) -> str:
        scope_str = ",".join(map(str, sorted(self.scope_indices)))
        return f"COUNT_LE(scope=[{scope_str}],count={self.count})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        werewolf_count = sum(1 for i in self.scope_indices if assignment[i])
        return werewolf_count <= self.count

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # SUM(W[i] for i in scope) <= count
        total = sum(z3.If(W_vars[i], 1, 0) for i in self.scope_indices)
        return total <= self.count

    def to_english(self, names: list[str]) -> str:
        scope_names = [names[i] for i in self.scope_indices]
        if len(scope_names) == 1:
            scope_desc = scope_names[0]
        elif len(scope_names) <= 3:
            scope_desc = ", ".join(scope_names[:-1]) + f", and {scope_names[-1]}"
        else:
            scope_desc = f"{len(scope_names)} villagers"
        return f"At most {self.count} werewolf{'ves' if self.count != 1 else ''} among {scope_desc}."

    def complexity_cost(self) -> int:
        return 2

    def to_dict(self) -> dict:
        """Convert at-most-k statement to dictionary.

        Returns:
            Dictionary with 'type', 'scope_indices', and 'count' fields
        """
        return {
            "type": self.__class__.__name__,
            "scope_indices": list(self.scope_indices),  # Convert tuple to list for JSON
            "count": self.count,
        }


class AtLeastKWerewolves(CountStatement):
    """Semantics: SUM(W[i] for i in scope) >= count"""

    def __init__(self, scope_indices: tuple[int, ...], count: int):
        """Initialize an at-least-k statement.

        Args:
            scope_indices: Tuple of villager indices in the scope
            count: Minimum number of werewolves required
        """
        super().__init__(scope_indices)
        self.count = count

    @property
    def statement_id(self) -> str:
        scope_str = ",".join(map(str, sorted(self.scope_indices)))
        return f"COUNT_GE(scope=[{scope_str}],count={self.count})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        werewolf_count = sum(1 for i in self.scope_indices if assignment[i])
        return werewolf_count >= self.count

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # SUM(W[i] for i in scope) >= count
        total = sum(z3.If(W_vars[i], 1, 0) for i in self.scope_indices)
        return total >= self.count

    def to_english(self, names: list[str]) -> str:
        scope_names = [names[i] for i in self.scope_indices]
        if len(scope_names) == 1:
            scope_desc = scope_names[0]
        elif len(scope_names) <= 3:
            scope_desc = ", ".join(scope_names[:-1]) + f", and {scope_names[-1]}"
        else:
            scope_desc = f"{len(scope_names)} villagers"
        return f"At least {self.count} werewolf{'ves' if self.count != 1 else ''} among {scope_desc}."

    def complexity_cost(self) -> int:
        return 2

    def to_dict(self) -> dict:
        """Convert at-least-k statement to dictionary.

        Returns:
            Dictionary with 'type', 'scope_indices', and 'count' fields
        """
        return {
            "type": self.__class__.__name__,
            "scope_indices": list(self.scope_indices),  # Convert tuple to list for JSON
            "count": self.count,
        }


class EvenNumberOfWerewolves(CountStatement):
    """Semantics: SUM(W[i] for i in scope) % 2 == 0"""

    @property
    def statement_id(self) -> str:
        scope_str = ",".join(map(str, sorted(self.scope_indices)))
        return f"COUNT_EVEN(scope=[{scope_str}])"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        werewolf_count = sum(1 for i in self.scope_indices if assignment[i])
        return werewolf_count % 2 == 0

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # SUM(W[i] for i in scope) % 2 == 0
        total = sum(z3.If(W_vars[i], 1, 0) for i in self.scope_indices)
        return total % 2 == 0

    def to_english(self, names: list[str]) -> str:
        scope_names = [names[i] for i in self.scope_indices]
        if len(scope_names) == 1:
            scope_desc = scope_names[0]
        elif len(scope_names) <= 3:
            scope_desc = ", ".join(scope_names[:-1]) + f", and {scope_names[-1]}"
        else:
            scope_desc = f"{len(scope_names)} villagers"
        return f"An even number of werewolves among {scope_desc}."

    def complexity_cost(self) -> int:
        return 2


class OddNumberOfWerewolves(CountStatement):
    """Semantics: SUM(W[i] for i in scope) % 2 == 1"""

    @property
    def statement_id(self) -> str:
        scope_str = ",".join(map(str, sorted(self.scope_indices)))
        return f"COUNT_ODD(scope=[{scope_str}])"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        werewolf_count = sum(1 for i in self.scope_indices if assignment[i])
        return werewolf_count % 2 == 1

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        import z3

        # SUM(W[i] for i in scope) % 2 == 1
        total = sum(z3.If(W_vars[i], 1, 0) for i in self.scope_indices)
        return total % 2 == 1

    def to_english(self, names: list[str]) -> str:
        scope_names = [names[i] for i in self.scope_indices]
        if len(scope_names) == 1:
            scope_desc = scope_names[0]
        elif len(scope_names) <= 3:
            scope_desc = ", ".join(scope_names[:-1]) + f", and {scope_names[-1]}"
        else:
            scope_desc = f"{len(scope_names)} villagers"
        return f"An odd number of werewolves among {scope_desc}."

    def complexity_cost(self) -> int:
        return 2
