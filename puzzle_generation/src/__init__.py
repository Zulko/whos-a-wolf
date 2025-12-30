"""Werewolf puzzle solver and generator."""

__version__ = "0.1.0"

from .generator import generate_puzzle
from .models import GenerationConfig, Puzzle, Villager
from .render import PuzzleRenderer
from .solver import PuzzleSolver

__all__ = [
    "generate_puzzle",
    "GenerationConfig",
    "Puzzle",
    "PuzzleRenderer",
    "PuzzleSolver",
    "Villager",
]

