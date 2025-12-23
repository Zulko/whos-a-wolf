"""CLI entry point for werewolf puzzle generator."""

import argparse
import sys
from pathlib import Path

from .generator import generate_puzzle
from .models import GenerationConfig
from .render import PuzzleRenderer
from .truth_cache import ClaimTruthTableCache


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
        "--claims-min",
        type=int,
        default=2,
        help="Minimum claims per speaker (default: 2)",
    )
    parser.add_argument(
        "--claims-max",
        type=int,
        default=2,
        help="Maximum claims per speaker (default: 2)",
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
        "--has-minion",
        action="store_true",
        help="Enable minion mode: exactly one non-werewolf will be a minion who lies",
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

    args = parser.parse_args()

    # Create config
    config = GenerationConfig(
        N=args.N,
        claims_per_speaker_min=args.claims_min,
        claims_per_speaker_max=args.claims_max,
        max_attempts=args.max_attempts,
        has_minion=args.has_minion,
        min_werewolves=args.min_werewolves,
        max_werewolves=args.max_werewolves,
    )

    # Load or build truth cache
    cache_path = Path(args.cache_file)
    if args.rebuild_cache or not cache_path.exists():
        print(f"Building truth cache for N={config.N}...", file=sys.stderr)
        from .generator import build_claim_library

        claim_library = build_claim_library(config)
        truth_cache = ClaimTruthTableCache.build_for_claim_library(
            claim_library, config.N
        )
        truth_cache.save_to_json(str(cache_path))
        print(f"Cache saved to {cache_path}", file=sys.stderr)
    else:
        print(f"Loading truth cache from {cache_path}...", file=sys.stderr)
        try:
            truth_cache = ClaimTruthTableCache.load_from_json(str(cache_path))
            if truth_cache.N != config.N:
                print(
                    f"Warning: Cache has N={truth_cache.N}, but requested N={config.N}",
                    file=sys.stderr,
                )
                print("Rebuilding cache...", file=sys.stderr)
                from .generator import build_claim_library

                claim_library = build_claim_library(config)
                truth_cache = ClaimTruthTableCache.build_for_claim_library(
                    claim_library, config.N
                )
                truth_cache.save_to_json(str(cache_path))
        except Exception as e:
            print(f"Error loading cache: {e}", file=sys.stderr)
            print("Rebuilding cache...", file=sys.stderr)
            from .generator import build_claim_library

            claim_library = build_claim_library(config)
            truth_cache = ClaimTruthTableCache.build_for_claim_library(
                claim_library, config.N
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
            claims_by_speaker=puzzle.claims_by_speaker,
            difficulty_score=puzzle.difficulty_score,
            solution_assignment=None,
            minion_assignment=None,
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
