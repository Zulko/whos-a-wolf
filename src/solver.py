"""Z3-based solver for puzzle verification and uniqueness checking."""

import z3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Puzzle
    from .truth_cache import ClaimTruthTableCache


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
    def check_uniqueness_and_difficulty(
        puzzle: "Puzzle",
        truth_cache: "ClaimTruthTableCache | None" = None,
    ) -> tuple[bool, float]:
        """Check if puzzle has unique solution and estimate difficulty.
        
        Args:
            puzzle: The puzzle to check
            truth_cache: Optional truth cache for more accurate difficulty estimation
        
        Returns:
            Tuple of (is_unique, difficulty_score)
        """
        is_unique = PuzzleSolver.is_uniquely_satisfiable(puzzle)
        difficulty = PuzzleSolver.estimate_difficulty(puzzle, truth_cache)
        return is_unique, difficulty
    
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
    
    @staticmethod
    def estimate_difficulty(
        puzzle: "Puzzle",
        truth_cache: "ClaimTruthTableCache | None" = None,
    ) -> float:
        """Estimate the difficulty of solving the puzzle.
        
        Difficulty is estimated based on:
        - Constraint tightness: how much each constraint reduces the search space
        - Number of constraints: more constraints generally make puzzles harder
        - Constraint interdependence: how constraints interact
        
        Args:
            puzzle: The puzzle to estimate difficulty for
            truth_cache: Optional truth cache for more accurate estimation.
                        If None, uses Z3-based heuristics.
        
        Returns:
            Difficulty score (higher = harder). Typical range: 0.0 to 100.0+
        """
        N = len(puzzle.villagers)
        num_assignments = 1 << N
        
        if truth_cache is not None:
            # Use bitmask-based estimation (more accurate)
            return PuzzleSolver._estimate_difficulty_with_cache(puzzle, truth_cache)
        else:
            # Use Z3-based estimation (fallback)
            return PuzzleSolver._estimate_difficulty_with_z3(puzzle)
    
    @staticmethod
    def _estimate_difficulty_with_cache(
        puzzle: "Puzzle",
        truth_cache: "ClaimTruthTableCache",
    ) -> float:
        """Estimate difficulty using truth cache bitmask operations."""
        from .truth_cache import compute_human_wolf_masks
        
        N = len(puzzle.villagers)
        num_assignments = 1 << N
        all_assignments_mask = (1 << num_assignments) - 1
        
        # Precompute human/wolf masks
        human_mask_by_speaker, wolf_mask_by_speaker = compute_human_wolf_masks(N)
        
        # Track remaining assignments as we add constraints incrementally
        remaining_mask = all_assignments_mask
        reduction_history = []
        total_claims = 0
        
        # Add constraints one speaker at a time
        for speaker_idx, claims in enumerate(puzzle.claims_by_speaker):
            if not claims:
                continue
            
            total_claims += len(claims)
            
            # Compute bundle_all_true_mask: assignments where all claims are true
            bundle_all_true_mask = all_assignments_mask
            for claim in claims:
                truth_mask = truth_cache.get_truth_mask(claim)
                bundle_all_true_mask &= truth_mask
            
            # Speaker compatibility: AND(claims) == NOT(W[speaker])
            compat_mask = (
                (human_mask_by_speaker[speaker_idx] & bundle_all_true_mask) |
                (wolf_mask_by_speaker[speaker_idx] & (all_assignments_mask & (~bundle_all_true_mask)))
            )
            
            # Update remaining mask
            assignments_before = bin(remaining_mask).count("1")
            remaining_mask &= compat_mask
            assignments_after = bin(remaining_mask).count("1")
            
            if assignments_before > 0:
                reduction = assignments_before - assignments_after
                reduction_ratio = reduction / assignments_before
                reduction_history.append({
                    'assignments_before': assignments_before,
                    'assignments_after': assignments_after,
                    'reduction': reduction,
                    'reduction_ratio': reduction_ratio,
                })
        
        # Compute difficulty metrics
        if not reduction_history:
            return 0.0
        
        # Base difficulty: number of constraints
        base_difficulty = total_claims * 2.0
        
        # Constraint tightness: average reduction ratio
        avg_reduction_ratio = sum(h['reduction_ratio'] for h in reduction_history) / len(reduction_history)
        tightness_score = avg_reduction_ratio * 30.0
        
        # Bottleneck score: minimum assignments remaining (harder if fewer remain)
        min_remaining = min(h['assignments_after'] for h in reduction_history)
        if min_remaining > 0:
            # Logarithmic scale: log2(remaining) measures how constrained
            import math
            log2_remaining = math.log2(min_remaining) if min_remaining > 0 else 0
            bottleneck_score = (N - log2_remaining) * 5.0
        else:
            bottleneck_score = N * 10.0  # Very constrained
        
        # Constraint interdependence: how much later constraints reduce space
        # (if later constraints still reduce significantly, they're interdependent)
        if len(reduction_history) > 1:
            later_reductions = [h['reduction_ratio'] for h in reduction_history[1:]]
            interdependence_score = sum(later_reductions) / len(later_reductions) * 20.0
        else:
            interdependence_score = 0.0
        
        # Puzzle size factor: larger puzzles are generally harder
        size_factor = N * 1.5
        
        difficulty = base_difficulty + tightness_score + bottleneck_score + interdependence_score + size_factor
        
        return difficulty
    
    @staticmethod
    def _estimate_difficulty_with_z3(puzzle: "Puzzle") -> float:
        """Estimate difficulty using Z3 solver statistics (fallback method)."""
        N = len(puzzle.villagers)
        
        # Count total claims
        total_claims = sum(len(claims) for claims in puzzle.claims_by_speaker)
        
        # Build solver and check satisfiability
        solver = PuzzleSolver.build_solver(puzzle)
        
        # Base difficulty from constraint count
        base_difficulty = total_claims * 2.0
        
        # Puzzle size factor
        size_factor = N * 1.5
        
        # Try to get some statistics from Z3
        # Note: Z3 doesn't directly expose search space size, so we use heuristics
        if solver.check() == z3.sat:
            # If satisfiable, estimate based on constraint count and puzzle size
            # More constraints relative to puzzle size = harder
            constraint_density = total_claims / N if N > 0 else 0
            density_score = constraint_density * 10.0
            
            difficulty = base_difficulty + size_factor + density_score
        else:
            # Unsatisfiable puzzles are "infinitely hard"
            return float('inf')
        
        return difficulty

