"""Analyze generated puzzle data to extract statistics."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib = None
    plt = None

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Puzzle


def plot_analysis_results(results: dict, N: int, output_dir: Path) -> None:
    """Plot analysis results in multiple subplots and save as games_N.png.

    Args:
        results: Dictionary containing analysis results
        N: Number of characters
        output_dir: Directory to save the plot
    """
    if plt is None:
        print(
            "Warning: matplotlib not installed. Skipping plot generation.",
            file=sys.stderr,
        )
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Analysis Results for {N} Players", fontsize=16, fontweight="bold")

    # Plot 1: Werewolf count distribution
    ax1 = axes[0, 0]
    ww_dist = results.get("werewolf_count_distribution", {})
    if ww_dist:
        # Sort keys by their integer value, but keep original keys for lookup
        sorted_keys = sorted(ww_dist.keys(), key=lambda k: int(k))
        counts = [int(k) for k in sorted_keys]
        frequencies = [ww_dist[k] for k in sorted_keys]
        total = sum(frequencies)
        percentages = (
            [100 * f / total for f in frequencies] if total > 0 else frequencies
        )
        ax1.bar(counts, percentages, color="steelblue", edgecolor="black")
        ax1.set_xlabel("Number of Werewolves")
        ax1.set_ylabel("Percentage (%)")
        ax1.set_title(f"Werewolf Count Distribution ({N} Players)")
        ax1.set_xticks(counts)
        ax1.grid(axis="y", alpha=0.3)
    else:
        ax1.text(
            0.5,
            0.5,
            "No data",
            ha="center",
            va="center",
            transform=ax1.transAxes,
        )
        ax1.set_title("Werewolf Count Distribution")

    # Plot 2: General statement type distribution
    ax2 = axes[0, 1]
    stmt_dist = results.get("statement_type_distribution", {})
    if stmt_dist:
        # Sort by count descending (most frequent first)
        sorted_items = sorted(stmt_dist.items(), key=lambda x: x[1], reverse=True)
        types = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        total = sum(counts)
        percentages = [100 * c / total for c in counts] if total > 0 else counts
        ax2.barh(types, percentages, color="forestgreen", edgecolor="black")
        ax2.set_xlabel("Percentage (%)")
        ax2.set_ylabel("Statement Type")
        ax2.set_title("General Statement Type Distribution")
        ax2.grid(axis="x", alpha=0.3)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)
        ax2.set_title("General Statement Type Distribution")

    # Plot 3: Statement type distribution for werewolves
    ax3 = axes[1, 0]
    ww_stmt_dist = results.get("statement_type_distribution_werewolves", {})
    if ww_stmt_dist:
        # Sort by count descending (most frequent first)
        sorted_items = sorted(ww_stmt_dist.items(), key=lambda x: x[1], reverse=True)
        types = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        total = sum(counts)
        percentages = [100 * c / total for c in counts] if total > 0 else counts
        ax3.barh(types, percentages, color="crimson", edgecolor="black")
        ax3.set_xlabel("Percentage (%)")
        ax3.set_ylabel("Statement Type")
        ax3.set_title("Statement Type Distribution (Werewolves)")
        ax3.grid(axis="x", alpha=0.3)
    else:
        ax3.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax3.transAxes)
        ax3.set_title("Statement Type Distribution (Werewolves)")

    # Plot 4: Statement type distribution for shills
    ax4 = axes[1, 1]
    shill_stmt_dist = results.get("statement_type_distribution_shills", {})
    if shill_stmt_dist:
        # Sort by count descending (most frequent first)
        sorted_items = sorted(shill_stmt_dist.items(), key=lambda x: x[1], reverse=True)
        types = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        total = sum(counts)
        percentages = [100 * c / total for c in counts] if total > 0 else counts
        ax4.barh(types, percentages, color="darkorange", edgecolor="black")
        ax4.set_xlabel("Percentage (%)")
        ax4.set_ylabel("Statement Type")
        ax4.set_title("Statement Type Distribution (Shills)")
        ax4.grid(axis="x", alpha=0.3)
    else:
        ax4.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax4.transAxes)
        ax4.set_title("Statement Type Distribution (Shills)")

    plt.tight_layout()

    output_file = output_dir / f"games_{N}.png"
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"Plot saved to {output_file}", file=sys.stderr)
    plt.close()


def main() -> None:
    """Analyze JSONL files and extract statistics."""
    parser = argparse.ArgumentParser(description="Analyze puzzle data from JSONL files")
    parser.add_argument(
        "files",
        nargs="+",
        type=str,
        help="JSONL files to analyze",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for plots (default: same as input files)",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip generating plots",
    )

    args = parser.parse_args()

    # Statistics to collect
    werewolf_count_distribution = Counter()
    statement_type_distribution = Counter()
    statement_type_distribution_werewolves = Counter()
    statement_type_distribution_shills = Counter()

    # Convert file paths to Path objects
    jsonl_files = [Path(f) for f in args.files]

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Use directory of first input file
        output_dir = jsonl_files[0].parent

    # Determine N from filename pattern (games_N.jsonl) or from data
    N = None
    for jsonl_file in jsonl_files:
        # Try to extract N from filename
        if jsonl_file.stem.startswith("games_"):
            try:
                N = int(jsonl_file.stem.split("_")[1])
                break
            except (ValueError, IndexError):
                pass

    total_puzzles = 0
    for jsonl_file in jsonl_files:
        if not jsonl_file.exists():
            print(f"Error: {jsonl_file} not found.", file=sys.stderr)
            sys.exit(1)

        print(f"Reading {jsonl_file}...", file=sys.stderr)
        puzzles_in_file = 0

        with open(jsonl_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    puzzle_dict = json.loads(line)
                    puzzle = Puzzle.from_dict(puzzle_dict)
                    puzzles_in_file += 1
                    total_puzzles += 1

                    # Extract N from number of villagers (if not already set)
                    if N is None:
                        N = len(puzzle.villagers)
                    elif N != len(puzzle.villagers):
                        print(
                            f"Warning: Inconsistent N values detected. Expected {N}, found {len(puzzle.villagers)}",
                            file=sys.stderr,
                        )

                    # Extract solution assignment
                    solution_assignment = puzzle.solution_assignment
                    shill_assignment = puzzle.shill_assignment

                    if solution_assignment is None:
                        print(
                            f"Warning: Puzzle at line {line_num} in {jsonl_file} has no solution_assignment, skipping...",
                            file=sys.stderr,
                        )
                        continue

                    # Werewolf count distribution
                    werewolf_count = sum(1 for w in solution_assignment if w)
                    werewolf_count_distribution[werewolf_count] += 1

                    # Process statements by speaker
                    for speaker_idx, statements in enumerate(
                        puzzle.statements_by_speaker
                    ):
                        is_werewolf = (
                            solution_assignment[speaker_idx]
                            if solution_assignment
                            else False
                        )
                        is_shill = (
                            shill_assignment[speaker_idx]
                            if shill_assignment and shill_assignment[speaker_idx]
                            else False
                        )

                        for statement in statements:
                            # Get statement type from the statement dict
                            stmt_dict = statement.to_dict()
                            stmt_type = stmt_dict.get("type", "Unknown")

                            # General distribution
                            statement_type_distribution[stmt_type] += 1

                            # Distribution for werewolves
                            if is_werewolf:
                                statement_type_distribution_werewolves[stmt_type] += 1

                            # Distribution for shills
                            if is_shill:
                                statement_type_distribution_shills[stmt_type] += 1

                except json.JSONDecodeError as e:
                    print(
                        f"Error parsing JSON at line {line_num} in {jsonl_file}: {e}",
                        file=sys.stderr,
                    )
                    continue
                except Exception as e:
                    print(
                        f"Error processing puzzle at line {line_num} in {jsonl_file}: {e}",
                        file=sys.stderr,
                    )
                    continue

        print(f"Processed {puzzles_in_file} puzzles from {jsonl_file}", file=sys.stderr)

    print(f"\nTotal puzzles processed: {total_puzzles}", file=sys.stderr)

    # Determine N if not set
    if N is None:
        print("Warning: Could not determine N. Using 6 as default.", file=sys.stderr)
        N = 6

    # Prepare output
    results = {
        "werewolf_count_distribution": dict(werewolf_count_distribution),
        "statement_type_distribution": dict(statement_type_distribution),
        "statement_type_distribution_werewolves": dict(
            statement_type_distribution_werewolves
        ),
        "statement_type_distribution_shills": dict(statement_type_distribution_shills),
    }

    # Output as JSON
    print(json.dumps(results, indent=2))

    # Generate plots if requested
    if not args.no_plot:
        plot_analysis_results(results, N, output_dir)


if __name__ == "__main__":
    main()
