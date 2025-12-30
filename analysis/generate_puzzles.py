"""Generate multiple puzzles for analysis."""

import argparse
import json
import sys
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    print(
        "Warning: tqdm not installed. Install with 'uv pip install tqdm' for progress bars.",
        file=sys.stderr,
    )

    # Fallback: create a dummy tqdm that just returns the iterable
    def tqdm(iterable, **kwargs):
        return iterable


# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generator import build_statement_library, generate_puzzle
from src.models import GenerationConfig
from src.truth_cache import StatementTruthTableCache


def main() -> None:
    """Generate puzzles for the specified number of characters."""
    parser = argparse.ArgumentParser(description="Generate puzzles for analysis")
    parser.add_argument(
        "--characters",
        type=int,
        choices=[4, 5, 6],
        default=6,
        help="Number of characters (default: 6)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1000,
        help="Number of puzzles to generate (default: 1000)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: analysis/)",
    )

    args = parser.parse_args()

    N = args.characters
    num_puzzles = args.count
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent
    output_file = output_dir / f"games_{N}.jsonl"

    # Create config
    config = GenerationConfig(
        N=N,
        statements_per_speaker_min=2,
        statements_per_speaker_max=2,
        max_attempts=100,
        has_shill=True,
        min_werewolves=1,
        max_werewolves=N - 1,
    )

    # Load or build truth cache
    cache_path = output_dir.parent / f"truth_cache_{N}.json"
    if not cache_path.exists():
        print(f"Building truth cache for N={N}...", file=sys.stderr)
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

    # Generate puzzles
    print(f"Generating {num_puzzles} puzzles for N={N}...", file=sys.stderr)
    successful = 0
    failed = 0

    with open(output_file, "w") as f:
        for i in tqdm(range(num_puzzles), desc="Generating puzzles", unit="puzzle"):
            puzzle = generate_puzzle(config, truth_cache)
            if puzzle is None:
                failed += 1
                continue

            successful += 1
            # Convert puzzle to dict (includes solutions)
            puzzle_dict = puzzle.to_dict()
            # Write as JSON line
            f.write(json.dumps(puzzle_dict) + "\n")
            f.flush()

    print(
        f"\nGeneration complete! Successful: {successful}, Failed: {failed}",
        file=sys.stderr,
    )
    print(f"Output written to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
