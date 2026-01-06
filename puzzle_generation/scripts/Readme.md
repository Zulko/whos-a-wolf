Commands:

To generate a single puzzle, with different game mechanism options:

```shell
uv run scripts/generate_single_puzzle.py \
    --N 4 --statements-max 1 --has-shill \
    --diverse-statements --coherent-statements
```

To generate batches of puzzles (these use the best game mechanisms, hard-coded: one shill, diverse statements)

```shell
uv run scripts/generate_puzzles.py --characters 4 --count 1000 --cpus 6
uv run scripts/generate_puzzles.py --characters 5 --count 1000 --cpus 6
uv run scripts/generate_puzzles.py --characters 6 --count 1000 --cpus 6
```

To analyse the puzzles:

```
uv run scripts/analyze.py scripts/outputs/games_6.jsonl
```

To check the amount of duplication (generally not an issue):

```
uv run scripts/detect_duplicates.py scripts/outputs/games_6.jsonl
```
