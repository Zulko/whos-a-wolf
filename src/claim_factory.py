"""Canonical string serialization and parsing for claims."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .claims import Claim

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


class ClaimFactory:
    """Factory for creating claims from canonical strings and vice versa."""
    
    @staticmethod
    def to_canonical_string(claim: "Claim") -> str:
        """Convert a claim to its canonical string representation.
        
        Args:
            claim: The claim to serialize
            
        Returns:
            Canonical string representation
        """
        return claim.claim_id
    
    @staticmethod
    def from_canonical_string(s: str) -> "Claim":
        """Parse a canonical string into a Claim object.
        
        Args:
            s: Canonical string representation
            
        Returns:
            Claim object
            
        Raises:
            ValueError: If the string cannot be parsed
        """
        s = s.strip()
        
        # Relationship claims
        if match := re.match(r"^IMP\((\d+),(\d+)\)$", s):
            a, b = int(match.group(1)), int(match.group(2))
            return IfAThenB(a, b)
        
        if match := re.match(r"^EQ\((\d+),(\d+)\)$", s):
            a, b = int(match.group(1)), int(match.group(2))
            return BothOrNeither(a, b)
        
        if match := re.match(r"^OR\((\d+),(\d+)\)$", s):
            a, b = int(match.group(1)), int(match.group(2))
            return AtLeastOne(a, b)
        
        if match := re.match(r"^XOR\((\d+),(\d+)\)$", s):
            a, b = int(match.group(1)), int(match.group(2))
            return ExactlyOne(a, b)
        
        if match := re.match(r"^IMP_NOT\((\d+),(\d+)\)$", s):
            a, b = int(match.group(1)), int(match.group(2))
            return IfNotAThenB(a, b)
        
        if match := re.match(r"^NEITHER\((\d+),(\d+)\)$", s):
            a, b = int(match.group(1)), int(match.group(2))
            return Neither(a, b)
        
        # Count claims
        # Format: COUNT_EQ(scope=[0,1,2],count=3)
        if match := re.match(r"^COUNT_EQ\(scope=\[([\d,]+)\],count=(\d+)\)$", s):
            scope_str = match.group(1)
            count = int(match.group(2))
            scope = tuple(int(x) for x in scope_str.split(",") if x)
            return ExactlyKWerewolves(scope, count)
        
        if match := re.match(r"^COUNT_LE\(scope=\[([\d,]+)\],count=(\d+)\)$", s):
            scope_str = match.group(1)
            count = int(match.group(2))
            scope = tuple(int(x) for x in scope_str.split(",") if x)
            return AtMostKWerewolves(scope, count)
        
        if match := re.match(r"^COUNT_GE\(scope=\[([\d,]+)\],count=(\d+)\)$", s):
            scope_str = match.group(1)
            count = int(match.group(2))
            scope = tuple(int(x) for x in scope_str.split(",") if x)
            return AtLeastKWerewolves(scope, count)
        
        if match := re.match(r"^COUNT_EVEN\(scope=\[([\d,]+)\]\)$", s):
            scope_str = match.group(1)
            scope = tuple(int(x) for x in scope_str.split(",") if x)
            return EvenNumberOfWerewolves(scope)
        
        if match := re.match(r"^COUNT_ODD\(scope=\[([\d,]+)\]\)$", s):
            scope_str = match.group(1)
            scope = tuple(int(x) for x in scope_str.split(",") if x)
            return OddNumberOfWerewolves(scope)
        
        raise ValueError(f"Cannot parse claim string: {s}")

