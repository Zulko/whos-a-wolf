"""Z3-based solver for puzzle verification and uniqueness checking."""

import z3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Puzzle


class PuzzleSolver:
    """Solver for werewolf puzzles using Z3."""
    
    @staticmethod
    def build_solver(puzzle: "Puzzle") -> z3.Solver:
        """Build a Z3 solver instance for a puzzle.
        
        Args:
            puzzle: The puzzle to build constraints for
            
        Returns:
            Z3 Solver instance with all constraints added
        """
        solver = z3.Solver()
        N = len(puzzle.villagers)
        
        # Create boolean variables for each villager
        W_vars = [z3.Bool(f"W{i}") for i in range(N)]
        
        # For each speaker, add the truthfulness constraint:
        # AND(claims_by_speaker[i]) == NOT(W[i])
        for i, claims in enumerate(puzzle.claims_by_speaker):
            if not claims:
                continue
            
            # Compute AND of all claims for this speaker
            claim_exprs = [claim.to_solver_expr(W_vars) for claim in claims]
            all_claims_true = z3.And(*claim_exprs) if len(claim_exprs) > 1 else claim_exprs[0]
            
            # Constraint: all_claims_true == NOT(W[i])
            solver.add(all_claims_true == z3.Not(W_vars[i]))
        
        return solver
    
    @staticmethod
    def find_one_solution(puzzle: "Puzzle") -> tuple[bool, ...] | None:
        """Find one solution to the puzzle.
        
        Args:
            puzzle: The puzzle to solve
            
        Returns:
            A tuple of booleans representing W[0..N-1], or None if unsatisfiable
        """
        solver = PuzzleSolver.build_solver(puzzle)
        
        if solver.check() != z3.sat:
            return None
        
        model = solver.model()
        N = len(puzzle.villagers)
        W_vars = [z3.Bool(f"W{i}") for i in range(N)]
        
        assignment = tuple(
            z3.is_true(model[W_vars[i]]) for i in range(N)
        )
        
        return assignment
    
    @staticmethod
    def is_uniquely_satisfiable(puzzle: "Puzzle") -> bool:
        """Check if the puzzle has exactly one solution.
        
        Args:
            puzzle: The puzzle to check
            
        Returns:
            True if the puzzle has exactly one solution, False otherwise
        """
        solver = PuzzleSolver.build_solver(puzzle)
        
        # Check if satisfiable
        if solver.check() != z3.sat:
            return False
        
        # Get first solution
        model = solver.model()
        N = len(puzzle.villagers)
        W_vars = [z3.Bool(f"W{i}") for i in range(N)]
        
        # Build blocking constraint: assignment != found_model
        blocking_constraints = []
        for i in range(N):
            if z3.is_true(model[W_vars[i]]):
                blocking_constraints.append(z3.Not(W_vars[i]))
            else:
                blocking_constraints.append(W_vars[i])
        
        # Add blocking constraint and check for another solution
        solver.add(z3.Or(*blocking_constraints))
        
        # If still satisfiable, there's more than one solution
        return solver.check() != z3.sat
    
    @staticmethod
    def enumerate_solutions(puzzle: "Puzzle", max_solutions: int) -> list[tuple[bool, ...]]:
        """Enumerate solutions to the puzzle (up to max_solutions).
        
        Args:
            puzzle: The puzzle to solve
            max_solutions: Maximum number of solutions to return
            
        Returns:
            List of solution assignments
        """
        solutions = []
        solver = PuzzleSolver.build_solver(puzzle)
        N = len(puzzle.villagers)
        W_vars = [z3.Bool(f"W{i}") for i in range(N)]
        
        while len(solutions) < max_solutions:
            if solver.check() != z3.sat:
                break
            
            model = solver.model()
            assignment = tuple(
                z3.is_true(model[W_vars[i]]) for i in range(N)
            )
            solutions.append(assignment)
            
            # Block this solution
            blocking_constraints = []
            for i in range(N):
                if z3.is_true(model[W_vars[i]]):
                    blocking_constraints.append(z3.Not(W_vars[i]))
                else:
                    blocking_constraints.append(W_vars[i])
            solver.add(z3.Or(*blocking_constraints))
        
        return solutions

