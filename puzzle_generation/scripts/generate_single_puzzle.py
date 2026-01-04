"""CLI entry point for werewolf puzzle generator."""

import argparse
import sys
from pathlib import Path

from src.generator import build_statement_library, generate_puzzle
from src.models import GenerationConfig
from src.render import PuzzleRenderer
from src.truth_cache import StatementTruthTableCache


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate werewolf logic puzzles")
    parser.add_argument(
        "--N",
        type=int,
        default=6,
        help="Number of villagers (default: 6)",
    )
    parser.add_argument(
        "--statements-min",
        type=int,
        default=1,
        help="Minimum statements per speaker (default: 2)",
    )
    parser.add_argument(
        "--statements-max",
        type=int,
        default=2,
        help="Maximum statements per speaker (default: 2)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=100,
        help="Maximum generation attempts (default: 100)",
    )
    parser.add_argument(
        "--cache-file",
        type=str,
        default="truth_cache.json",
        help="Path to truth cache file (default: truth_cache.json)",
    )
    parser.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Rebuild the truth cache",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--show-solution",
        action="store_true",
        help="Include solution in output",
    )
    parser.add_argument(
        "--has-shill",
        action="store_true",
        help="Enable shill mode: exactly one non-werewolf will be a shill who lies",
    )
    parser.add_argument(
        "--min-werewolves",
        type=int,
        default=None,
        help="Minimum number of werewolves in the puzzle (default: no minimum)",
    )
    parser.add_argument(
        "--max-werewolves",
        type=int,
        default=None,
        help="Maximum number of werewolves in the puzzle (default: no maximum)",
    )
    parser.add_argument(
        "--diverse-statements",
        action="store_true",
        help="Require each character to use at least one statement type that no other character uses",
    )
    parser.add_argument(
        "--randomness",
        type=float,
        default=0.7,
        help="Randomness level 0.0-1.0: 0=always pick best bundle, 1=pick any valid bundle (default: 0.7)",
    )

    args = parser.parse_args()

    # Cap max_werewolves at N-1 if shills are enabled (need at least one non-werewolf for shill)
    max_werewolves = args.max_werewolves
    if args.has_shill and max_werewolves is not None:
        max_werewolves = min(max_werewolves, args.N - 1)
    elif args.has_shill:
        max_werewolves = args.N - 1

    # Create config
    config = GenerationConfig(
        N=args.N,
        statements_per_speaker_min=args.statements_min,
        statements_per_speaker_max=args.statements_max,
        max_attempts=args.max_attempts,
        has_shill=args.has_shill,
        min_werewolves=args.min_werewolves,
        max_werewolves=max_werewolves,
        diverse_statements=args.diverse_statements,
        randomness=args.randomness,
    )

    # Load or build truth cache
    cache_path = Path(args.cache_file)
    if args.rebuild_cache or not cache_path.exists():
        print(f"Building truth cache for N={config.N}...", file=sys.stderr)
        statement_library = build_statement_library(config)
        truth_cache = StatementTruthTableCache.build_for_statement_library(
            statement_library, config.N
        )
        truth_cache.save_to_json(str(cache_path))
        print(f"Cache saved to {cache_path}", file=sys.stderr)
    else:
        print(f"Loading truth cache from {cache_path}...", file=sys.stderr)
        try:
            truth_cache = StatementTruthTableCache.load_from_json(str(cache_path))
            if truth_cache.N != config.N:
                print(
                    f"Warning: Cache has N={truth_cache.N}, but requested N={config.N}",
                    file=sys.stderr,
                )
                print("Rebuilding cache...", file=sys.stderr)
                statement_library = build_statement_library(config)
                truth_cache = StatementTruthTableCache.build_for_statement_library(
                    statement_library, config.N
                )
                truth_cache.save_to_json(str(cache_path))
        except Exception as e:
            print(f"Error loading cache: {e}", file=sys.stderr)
            print("Rebuilding cache...", file=sys.stderr)
            statement_library = build_statement_library(config)
            truth_cache = StatementTruthTableCache.build_for_statement_library(
                statement_library, config.N
            )
            truth_cache.save_to_json(str(cache_path))

    # Generate puzzle
    print("Generating puzzle...", file=sys.stderr)
    puzzle = generate_puzzle(config, truth_cache)

    if puzzle is None:
        print("Failed to generate puzzle after max attempts.", file=sys.stderr)
        sys.exit(1)

    # Remove solution if not requested
    if not args.show_solution:
        puzzle = puzzle.__class__(
            villagers=puzzle.villagers,
            statements_by_speaker=puzzle.statements_by_speaker,
            difficulty_score=puzzle.difficulty_score,
            solution_assignment=None,
            shill_assignment=None,
        )

    # Render puzzle
    if args.output_format == "markdown":
        output = PuzzleRenderer.render_to_markdown(puzzle)
    else:
        output = PuzzleRenderer.render_to_text(puzzle)

    # Write output
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(output)
        print(f"Puzzle written to {args.output_file}", file=sys.stderr)
    else:
        print(output)

    # Display difficulty score
    print(f"Difficulty Score: {puzzle.difficulty_score:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
