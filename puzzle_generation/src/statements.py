"""Statement classes representing boolean statements about werewolves."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import z3

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

    @abstractmethod
    def to_short_string(self) -> str:
        """Return a short string representation of this statement.

        Returns:
            Short string like "I-5-7" for IfAThenB(5,7) or "N-3-4" for Neither(3,4)
        """
        pass

    @abstractmethod
    def get_accusations(self) -> set[tuple[int, int]]:
        """Return set of (accuser, accused) tuples implied by this statement.

        An accusation (a, b) means the statement implies a negative relationship
        where a's innocence implies b's guilt, or where a and b are in opposition.

        Returns:
            Set of (a, b) tuples representing accusations
        """
        pass

    @abstractmethod
    def get_vouchings(self) -> set[tuple[int, int]]:
        """Return set of (voucher, vouched_for) tuples implied by this statement.

        A vouching (a, b) means the statement implies a positive relationship
        where a and b share the same fate (both innocent or both guilty).

        Returns:
            Set of (a, b) tuples representing vouchings
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
        elif stmt_type == "AtMostOne":
            return AtMostOne(data["a_index"], data["b_index"])
        elif stmt_type == "IfNotAThenB":
            return IfNotAThenB(data["a_index"], data["b_index"])
        elif stmt_type == "Neither":
            return Neither(data["a_index"], data["b_index"])
        # New unified CountWerewolves type
        elif stmt_type == "CountWerewolves":
            scope = tuple(data["scope_indices"])
            count = data["count"]
            comparison = data.get("comparison", "exactly")
            return CountWerewolves(scope, count, comparison)
        # Legacy count statement types (backwards compatibility)
        elif stmt_type == "ExactlyKWerewolves":
            scope = tuple(data["scope_indices"])
            return CountWerewolves(scope, data["count"], "exactly")
        elif stmt_type == "AtMostKWerewolves":
            scope = tuple(data["scope_indices"])
            return CountWerewolves(scope, data["count"], "at_most")
        elif stmt_type == "AtLeastKWerewolves":
            scope = tuple(data["scope_indices"])
            return CountWerewolves(scope, data["count"], "at_least")
        elif stmt_type == "EvenNumberOfWerewolves":
            scope = tuple(data["scope_indices"])
            return CountWerewolves(scope, "even")
        elif stmt_type == "OddNumberOfWerewolves":
            scope = tuple(data["scope_indices"])
            return CountWerewolves(scope, "odd")
        else:
            raise ValueError(f"Unknown statement type: {stmt_type}")

    @classmethod
    def from_short_string(cls, short_str: str) -> "Statement":
        """Create statement from short string representation.

        Args:
            short_str: Short string like "I-5-7" or "N-3-4" or "E-0,1,2-2"

        Returns:
            Statement instance

        Raises:
            ValueError: If the short string format is invalid
        """
        parts = short_str.split("-")
        if len(parts) < 2:
            raise ValueError(f"Invalid short string format: {short_str}")

        code = parts[0]

        # Relationship statements: code-a-b
        if code == "I":  # IfAThenB
            if len(parts) != 3:
                raise ValueError(f"Invalid IfAThenB format: {short_str}")
            return IfAThenB(int(parts[1]), int(parts[2]))
        elif code == "B":  # BothOrNeither
            if len(parts) != 3:
                raise ValueError(f"Invalid BothOrNeither format: {short_str}")
            return BothOrNeither(int(parts[1]), int(parts[2]))
        elif code == "A":  # AtLeastOne
            if len(parts) != 3:
                raise ValueError(f"Invalid AtLeastOne format: {short_str}")
            return AtLeastOne(int(parts[1]), int(parts[2]))
        elif code == "X":  # ExactlyOne
            if len(parts) != 3:
                raise ValueError(f"Invalid ExactlyOne format: {short_str}")
            return ExactlyOne(int(parts[1]), int(parts[2]))
        elif code == "F":  # IfNotAThenB
            if len(parts) != 3:
                raise ValueError(f"Invalid IfNotAThenB format: {short_str}")
            return IfNotAThenB(int(parts[1]), int(parts[2]))
        elif code == "T":  # AtMostOne
            if len(parts) != 3:
                raise ValueError(f"Invalid AtMostOne format: {short_str}")
            return AtMostOne(int(parts[1]), int(parts[2]))
        elif code == "N":  # Neither
            if len(parts) != 3:
                raise ValueError(f"Invalid Neither format: {short_str}")
            return Neither(int(parts[1]), int(parts[2]))
        # Count statements (all return CountWerewolves)
        elif code == "E":  # ExactlyKWerewolves: E-scope-count (scope uses dots)
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid CountWerewolves (exactly) format: {short_str}"
                )
            scope = tuple(int(x) for x in parts[1].split("."))
            count = int(parts[2])
            return CountWerewolves(scope, count, "exactly")
        elif code == "M":  # AtMostKWerewolves: M-scope-count (scope uses dots)
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid CountWerewolves (at_most) format: {short_str}"
                )
            scope = tuple(int(x) for x in parts[1].split("."))
            count = int(parts[2])
            return CountWerewolves(scope, count, "at_most")
        elif code == "L":  # AtLeastKWerewolves: L-scope-count (scope uses dots)
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid CountWerewolves (at_least) format: {short_str}"
                )
            scope = tuple(int(x) for x in parts[1].split("."))
            count = int(parts[2])
            return CountWerewolves(scope, count, "at_least")
        elif code == "V":  # EvenNumberOfWerewolves: V-scope (scope uses dots)
            if len(parts) != 2:
                raise ValueError(f"Invalid CountWerewolves (even) format: {short_str}")
            scope = tuple(int(x) for x in parts[1].split("."))
            return CountWerewolves(scope, "even")
        elif code == "O":  # OddNumberOfWerewolves: O-scope (scope uses dots)
            if len(parts) != 2:
                raise ValueError(f"Invalid CountWerewolves (odd) format: {short_str}")
            scope = tuple(int(x) for x in parts[1].split("."))
            return CountWerewolves(scope, "odd")
        else:
            raise ValueError(f"Unknown statement code: {code}")

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

    @abstractmethod
    def to_short_string(self) -> str:
        """Return a short string representation of this relationship statement.

        Returns:
            Short string like "I-5-7" for IfAThenB(5,7)
        """
        pass


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

    @abstractmethod
    def to_short_string(self) -> str:
        """Return a short string representation of this count statement.

        Returns:
            Short string like "E-0,1,2-2" for ExactlyKWerewolves((0,1,2), 2)
        """
        pass


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
        # W[a] => W[b]
        return z3.Implies(W_vars[self.a_index], W_vars[self.b_index])

    def to_english(self, names: list[str]) -> str:
        return f"If {names[self.a_index]} is a werewolf, then {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1

    def to_short_string(self) -> str:
        """Return short string representation: I-a-b"""
        return f"I-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """a's guilt implies b's guilt - accusation from a to b."""
        return {(self.a_index, self.b_index)}

    def get_vouchings(self) -> set[tuple[int, int]]:
        """Contrapositive: b's innocence implies a's innocence - b vouches for a."""
        return {(self.b_index, self.a_index)}


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
        # W[a] == W[b]
        return W_vars[self.a_index] == W_vars[self.b_index]

    def to_english(self, names: list[str]) -> str:
        return f"{names[self.a_index]} and {names[self.b_index]} are both werewolves, or neither is."

    def complexity_cost(self) -> int:
        return 1

    def to_short_string(self) -> str:
        """Return short string representation: B-a-b"""
        return f"B-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """No accusations - this is a mutual vouching relationship."""
        return set()

    def get_vouchings(self) -> set[tuple[int, int]]:
        """Mutual vouching - they share the same fate."""
        return {(self.a_index, self.b_index), (self.b_index, self.a_index)}


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
        # W[a] OR W[b]
        return z3.Or(W_vars[self.a_index], W_vars[self.b_index])

    def to_english(self, names: list[str]) -> str:
        return f"At least one of {names[self.a_index]} and {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1

    def to_short_string(self) -> str:
        """Return short string representation: A-a-b"""
        return f"A-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """Mutual accusation - if one is innocent, the other must be guilty."""
        return {(self.a_index, self.b_index), (self.b_index, self.a_index)}

    def get_vouchings(self) -> set[tuple[int, int]]:
        """No vouchings - this is an accusatory statement."""
        return set()


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
        # W[a] != W[b]
        return W_vars[self.a_index] != W_vars[self.b_index]

    def to_english(self, names: list[str]) -> str:
        return f"Exactly one of {names[self.a_index]} and {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1

    def to_short_string(self) -> str:
        """Return short string representation: X-a-b"""
        return f"X-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """Mutual accusation - one must be guilty, they're in opposition."""
        return {(self.a_index, self.b_index), (self.b_index, self.a_index)}

    def get_vouchings(self) -> set[tuple[int, int]]:
        """No vouchings - they cannot both be innocent or both be guilty."""
        return set()


class AtMostOne(RelationshipStatement):
    """Semantics: NOT(W[a] AND W[b]) - at most one of them is a werewolf."""

    def __init__(self, a_index: int, b_index: int):
        """Initialize an AtMostOne statement, normalizing indices for symmetry."""
        # Normalize: always store min(a, b) as a_index, max(a, b) as b_index
        super().__init__(min(a_index, b_index), max(a_index, b_index))

    @property
    def statement_id(self) -> str:
        return f"NAND({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        # NOT(W[a] AND W[b]) = NOT W[a] OR NOT W[b]
        return not (assignment[self.a_index] and assignment[self.b_index])

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        # NOT(W[a] AND W[b])
        return z3.Not(z3.And(W_vars[self.a_index], W_vars[self.b_index]))

    def to_english(self, names: list[str]) -> str:
        return f"{names[self.a_index]} and {names[self.b_index]} behave so differently, at most one of them is a werewolf."

    def complexity_cost(self) -> int:
        return 1

    def to_short_string(self) -> str:
        """Return short string representation: T-a-b"""
        return f"T-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """No accusations - this is a mutual vouching relationship (at most one guilty)."""
        return set()

    def get_vouchings(self) -> set[tuple[int, int]]:
        """Mutual partial vouching - if one is guilty, the other is innocent."""
        return {(self.a_index, self.b_index), (self.b_index, self.a_index)}


class IfNotAThenB(RelationshipStatement):
    """Semantics: (NOT W[a]) => W[b]

    WARNING: This statement is logically equivalent to AtLeastOne(a, b),
    since (NOT W[a]) => W[b] ≡ W[a] OR W[b].
    Prefer using AtLeastOne for puzzle generation to avoid duplicates.
    """

    @property
    def statement_id(self) -> str:
        return f"IMP_NOT({self.a_index},{self.b_index})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        # (NOT W[a]) => W[b] is equivalent to W[a] OR W[b]
        return assignment[self.a_index] or assignment[self.b_index]

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        # (NOT W[a]) => W[b]
        return z3.Implies(z3.Not(W_vars[self.a_index]), W_vars[self.b_index])

    def to_english(self, names: list[str]) -> str:
        return f"If {names[self.a_index]} is not a werewolf, then {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 1

    def to_short_string(self) -> str:
        """Return short string representation: F-a-b"""
        return f"F-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """Mutual accusation - equivalent to AtLeastOne, at least one must be guilty."""
        return {(self.a_index, self.b_index), (self.b_index, self.a_index)}

    def get_vouchings(self) -> set[tuple[int, int]]:
        """No vouchings - this is an accusatory statement."""
        return set()


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
        # (NOT W[a]) AND (NOT W[b])
        return z3.And(z3.Not(W_vars[self.a_index]), z3.Not(W_vars[self.b_index]))

    def to_english(self, names: list[str]) -> str:
        return f"Neither {names[self.a_index]} nor {names[self.b_index]} is a werewolf."

    def complexity_cost(self) -> int:
        return 2  # Higher cost as this is a strong statement

    def to_short_string(self) -> str:
        """Return short string representation: N-a-b"""
        return f"N-{self.a_index}-{self.b_index}"

    def get_accusations(self) -> set[tuple[int, int]]:
        """No accusations - both are asserted innocent."""
        return set()

    def get_vouchings(self) -> set[tuple[int, int]]:
        """Mutual vouching - both are asserted innocent, they share innocence."""
        return {(self.a_index, self.b_index), (self.b_index, self.a_index)}


# Count Statement Subclasses


class CountWerewolves(CountStatement):
    """Unified count statement for werewolf constraints.

    Semantics depend on count and comparison:
    - count=int, comparison="exactly": SUM(W[i]) == count
    - count=int, comparison="at_most": SUM(W[i]) <= count
    - count=int, comparison="at_least": SUM(W[i]) >= count
    - count="even": SUM(W[i]) % 2 == 0
    - count="odd": SUM(W[i]) % 2 == 1
    """

    def __init__(
        self,
        scope_indices: tuple[int, ...],
        count: int | str,
        comparison: str = "exactly",
    ):
        """Initialize a count statement.

        Args:
            scope_indices: Tuple of villager indices in the scope
            count: Either an int for numeric counts, or "odd"/"even" for parity
            comparison: For int counts: "exactly", "at_most", or "at_least"
                       Ignored for parity counts ("odd"/"even").
        """
        super().__init__(scope_indices)
        if isinstance(count, str) and count not in ("odd", "even"):
            raise ValueError(f"count must be int, 'odd', or 'even', got: {count}")
        if isinstance(count, int) and comparison not in (
            "exactly",
            "at_most",
            "at_least",
        ):
            raise ValueError(
                f"comparison must be 'exactly', 'at_most', or 'at_least', got: {comparison}"
            )
        self.count = count
        self.comparison = comparison if isinstance(count, int) else None

    @property
    def _is_parity(self) -> bool:
        """Return True if this is a parity statement."""
        return isinstance(self.count, str)

    @property
    def statement_id(self) -> str:
        scope_str = ",".join(map(str, sorted(self.scope_indices)))
        if self._is_parity:
            if self.count == "even":
                return f"COUNT_EVEN(scope=[{scope_str}])"
            else:  # odd
                return f"COUNT_ODD(scope=[{scope_str}])"
        else:
            if self.comparison == "exactly":
                return f"COUNT_EQ(scope=[{scope_str}],count={self.count})"
            elif self.comparison == "at_most":
                return f"COUNT_LE(scope=[{scope_str}],count={self.count})"
            else:  # at_least
                return f"COUNT_GE(scope=[{scope_str}],count={self.count})"

    def evaluate_on_assignment(self, assignment: tuple[bool, ...]) -> bool:
        werewolf_count = sum(1 for i in self.scope_indices if assignment[i])
        if self._is_parity:
            if self.count == "even":
                return werewolf_count % 2 == 0
            else:  # odd
                return werewolf_count % 2 == 1
        else:
            if self.comparison == "exactly":
                return werewolf_count == self.count
            elif self.comparison == "at_most":
                return werewolf_count <= self.count
            else:  # at_least
                return werewolf_count >= self.count

    def to_solver_expr(self, W_vars: list) -> "BoolRef":
        total = sum(z3.If(W_vars[i], 1, 0) for i in self.scope_indices)
        if self._is_parity:
            if self.count == "even":
                return total % 2 == 0
            else:  # odd
                return total % 2 == 1
        else:
            if self.comparison == "exactly":
                return total == self.count
            elif self.comparison == "at_most":
                return total <= self.count
            else:  # at_least
                return total >= self.count

    def _scope_description(self, names: list[str]) -> str:
        """Generate English description of the scope."""
        scope_names = [names[i] for i in self.scope_indices]
        if len(scope_names) == 1:
            return scope_names[0]
        elif len(scope_names) <= 3:
            return ", ".join(scope_names[:-1]) + f", and {scope_names[-1]}"
        else:
            return f"{len(scope_names)} villagers"

    def to_english(self, names: list[str]) -> str:
        scope_desc = self._scope_description(names)
        if self._is_parity:
            parity = "even" if self.count == "even" else "odd"
            return f"An {parity} number of werewolves among {scope_desc}."
        else:
            count_val = self.count
            wolves_word = "werewolf" if count_val == 1 else "werewolves"
            if self.comparison == "exactly":
                return f"Exactly {count_val} {wolves_word} among {scope_desc}."
            elif self.comparison == "at_most":
                return f"At most {count_val} {wolves_word} among {scope_desc}."
            else:  # at_least
                return f"At least {count_val} {wolves_word} among {scope_desc}."

    def complexity_cost(self) -> int:
        if self._is_parity:
            return 2
        elif self.comparison == "exactly":
            return 3  # Higher cost for exact counts
        else:
            return 2

    def to_short_string(self) -> str:
        """Return short string representation.

        Format:
        - E-scope-count for exactly (e.g., E-0.1.2-2)
        - M-scope-count for at_most (e.g., M-0.1-1)
        - L-scope-count for at_least (e.g., L-0.1.2.3-2)
        - V-scope for even (e.g., V-0.1.2)
        - O-scope for odd (e.g., O-0.1)
        """
        scope_str = ".".join(map(str, sorted(self.scope_indices)))
        if self._is_parity:
            if self.count == "even":
                return f"V-{scope_str}"
            else:  # odd
                return f"O-{scope_str}"
        else:
            if self.comparison == "exactly":
                return f"E-{scope_str}-{self.count}"
            elif self.comparison == "at_most":
                return f"M-{scope_str}-{self.count}"
            else:  # at_least
                return f"L-{scope_str}-{self.count}"

    def to_dict(self) -> dict:
        """Convert count statement to dictionary.

        Returns:
            Dictionary with 'type', 'scope_indices', 'count', and optionally 'comparison'
        """
        result = {
            "type": "CountWerewolves",
            "scope_indices": list(self.scope_indices),
            "count": self.count,
        }
        if not self._is_parity:
            result["comparison"] = self.comparison
        return result

    def get_accusations(self) -> set[tuple[int, int]]:
        """No direct inter-person accusations for count statements."""
        return set()

    def get_vouchings(self) -> set[tuple[int, int]]:
        """No direct inter-person vouchings for count statements."""
        return set()


# Backwards-compatible factory functions for old class names
def ExactlyKWerewolves(scope_indices: tuple[int, ...], count: int) -> CountWerewolves:
    """Create a CountWerewolves with comparison='exactly'.

    Backwards-compatible alias for ExactlyKWerewolves.
    """
    return CountWerewolves(scope_indices, count, comparison="exactly")


def AtMostKWerewolves(scope_indices: tuple[int, ...], count: int) -> CountWerewolves:
    """Create a CountWerewolves with comparison='at_most'.

    Backwards-compatible alias for AtMostKWerewolves.
    """
    return CountWerewolves(scope_indices, count, comparison="at_most")


def AtLeastKWerewolves(scope_indices: tuple[int, ...], count: int) -> CountWerewolves:
    """Create a CountWerewolves with comparison='at_least'.

    Backwards-compatible alias for AtLeastKWerewolves.
    """
    return CountWerewolves(scope_indices, count, comparison="at_least")


def EvenNumberOfWerewolves(scope_indices: tuple[int, ...]) -> CountWerewolves:
    """Create a CountWerewolves with count='even'.

    Backwards-compatible alias for EvenNumberOfWerewolves.
    """
    return CountWerewolves(scope_indices, "even")


def OddNumberOfWerewolves(scope_indices: tuple[int, ...]) -> CountWerewolves:
    """Create a CountWerewolves with count='odd'.

    Backwards-compatible alias for OddNumberOfWerewolves.
    """
    return CountWerewolves(scope_indices, "odd")
