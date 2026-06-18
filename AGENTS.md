In python, use `uv run` for all python commands

The web app lives in `app/` (that's where `package.json` is). Always run
`npm` commands from inside `app/` — never from the repo root, or you'll
create a stray root `package.json`/`node_modules`.
