# Werewolf Logic Puzzle Generator

A Python-based system for generating and solving Werewolf logic puzzles. Each puzzle features villagers who are either Humans (always truthful) or Werewolves (at least one statement is false), and the goal is to determine who is a werewolf based on their statements.

## Features

- **Fast Generation**: Bitmask-based algorithm for efficient puzzle generation
- **Unique Solutions**: Ensures each generated puzzle has exactly one solution
- **Z3 Verification**: Uses Z3 SMT solver for correctness verification
- **Multiple Statement Types**: Supports relationship statements (implications, equivalences, XOR, etc.) and count statements (exact counts, parity, etc.)
- **Flexible Configuration**: Customize number of villagers, statements per speaker, and generation parameters
- **Truth Table Caching**: Precomputed truth tables for fast generation
- **Multiple Output Formats**: Generate puzzles in plain text or Markdown

## Installation

### Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv) package manager

Install `uv` using the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This will install `uv` to `~/.local/bin`. Make sure this directory is in your PATH. If needed, add it to your shell configuration file (e.g., `~/.zshrc` or `~/.bashrc`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Setup

1. Clone or download this repository:

```bash
cd werewolf
```

2. Install dependencies (dependencies including `z3-solver` are specified in `pyproject.toml`):

```bash
uv sync
```

This will create a virtual environment and install all dependencies automatically.

## Usage

### Command Line Interface

Run the generator from the command line using `uv`:

```bash
uv run python -m src
```

Or activate the virtual environment first:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m src
```

This will generate a puzzle with default settings (6 villagers, 2 statements per speaker).

### Command Line Options

```bash
uv run python -m src [OPTIONS]
```

**Options:**

- `--N N`: Number of villagers (default: 6)
- `--statements-min MIN`: Minimum statements per speaker (default: 2)
- `--statements-max MAX`: Maximum statements per speaker (default: 2)
- `--max-attempts N`: Maximum generation attempts (default: 100)
- `--cache-file PATH`: Path to truth cache file (default: `truth_cache.json`)
- `--rebuild-cache`: Rebuild the truth cache
- `--output-format FORMAT`: Output format: `text` or `markdown` (default: `markdown`)
- `--output-file PATH`: Write output to file instead of stdout
- `--show-solution`: Include solution in output

### Examples

Generate a puzzle with 6 villagers:

```bash
uv run python -m src
```

Generate a puzzle with 8 villagers and 3 statements per speaker:

```bash
uv run python -m src --N 8 --statements-max 3
```

Generate and save to a file:

```bash
uv run python -m src --output-file puzzle.md --show-solution
```

Generate a text-format puzzle:

```bash
uv run python -m src --output-format text
```

Rebuild the truth cache (useful after changing N or statement types):

```bash
uv run python -m src --rebuild-cache
```

### Python API

You can also use the generator programmatically:

```python
from src import generate_puzzle, GenerationConfig, PuzzleRenderer
from src.truth_cache import StatementTruthTableCache

# Create configuration
config = GenerationConfig(
    N=6,
    statements_per_speaker_min=2,
    statements_per_speaker_max=2,
    max_attempts=100,
)

# Load or build truth cache
try:
    truth_cache = StatementTruthTableCache.load_from_json("truth_cache.json")
except FileNotFoundError:
    from src.generator import build_statement_library
    statement_library = build_statement_library(config)
    truth_cache = StatementTruthTableCache.build_for_statement_library(
        statement_library, config.N
    )
    truth_cache.save_to_json("truth_cache.json")

# Generate puzzle
puzzle = generate_puzzle(config, truth_cache)

if puzzle:
    # Render puzzle
    markdown = PuzzleRenderer.render_to_markdown(puzzle)
    print(markdown)

    # Access solution
    if puzzle.solution_assignment:
        print("\nSolution:", puzzle.solution_assignment)
else:
    print("Failed to generate puzzle")
```

## How It Works

### Puzzle Structure

Each puzzle consists of:

- **N villagers** (default: 6)
- Each villager makes **k statements** (typically 1-3, configurable)
- Each statement is a boolean statement about which villagers are werewolves

### Truthfulness Rule

- **Humans**: Always tell the truth → all their statements must be true
- **Werewolves**: At least one statement is false → not all statements can be true

Mathematically: `AND(statements_by_speaker[i]) == NOT(W[i])` for each villager i.

### Generation Algorithm

1. **Choose Target Assignment**: Randomly select a target solution `W_star`
2. **Build Statement Library**: Generate all allowed statements based on configuration
3. **Precompute Truth Tables**: Cache truth values for all statements on all assignments
4. **Generate Candidate Bundles**: For each speaker, find statement bundles consistent with `W_star`
5. **Greedy Assignment**: Iteratively assign bundles that eliminate the most incorrect assignments while preserving `W_star`
6. **Verify Uniqueness**: Use Z3 solver to confirm the puzzle has exactly one solution

### Statement Types

**Relationship Statements** (between two villagers):

- `IfAThenB`: If A is a werewolf, then B is a werewolf
- `BothOrNeither`: A and B are both werewolves, or neither is
- `AtLeastOne`: At least one of A and B is a werewolf
- `ExactlyOne`: Exactly one of A and B is a werewolf
- `IfNotAThenB`: If A is not a werewolf, then B is a werewolf
- `Neither`: Neither A nor B is a werewolf

**Count Statements** (about groups of villagers):

- `ExactlyKWerewolves`: Exactly K werewolves in the scope
- `AtMostKWerewolves`: At most K werewolves in the scope
- `AtLeastKWerewolves`: At least K werewolves in the scope
- `EvenNumberOfWerewolves`: Even number of werewolves in the scope
- `OddNumberOfWerewolves`: Odd number of werewolves in the scope

## Project Structure

```
werewolf/
├── src/
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # CLI entry point
│   ├── models.py            # Data models (Villager, Puzzle, GenerationConfig)
│   ├── statements.py            # Statement class hierarchy
│   ├── statement_factory.py     # Canonical serialization
│   ├── truth_cache.py       # Truth table caching
│   ├── solver.py            # Z3 solver integration
│   ├── generator.py        # Puzzle generation algorithm
│   ├── render.py            # Output formatting
│   └── utils.py             # Utility functions
├── specs/                   # Specification documents
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## Performance Notes

- For N=6, there are 2^6 = 64 possible assignments, making bitmask operations very fast
- Truth table caching significantly speeds up generation after the first run
- The greedy algorithm typically finds solutions quickly, but may require multiple attempts for harder configurations

## Troubleshooting

**Generation fails after max attempts:**

- Try increasing `--max-attempts`
- Try adjusting `--statements-min` and `--statements-max`
- Some configurations may be infeasible (e.g., too few statements for uniqueness)

**Cache file issues:**

- Delete `truth_cache.json` and regenerate with `--rebuild-cache`
- Ensure cache N matches your requested N

**Import errors:**

- Ensure you're running from the project root directory
- Verify dependencies are installed: `uv sync`
- Verify `z3-solver` is installed: `uv pip list | grep z3`

## License

This project is provided as-is for educational and entertainment purposes.

## Contributing

Feel free to submit issues or pull requests for improvements!
