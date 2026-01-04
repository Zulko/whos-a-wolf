Commands:

```shell
uv run generate_puzzles.py --characters 4 --count 1000 --cpus 6
uv run generate_puzzles.py --characters 5 --count 1000 --cpus 6
uv run generate_puzzles.py --characters 6 --count 1000 --cpus 6
```

```
uv run analyze.py outputs/games_6.jsonl
```
