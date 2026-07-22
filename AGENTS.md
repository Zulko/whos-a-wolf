In python, use `uv run` for all python commands

The web app lives in `app/` (that's where `package.json` is). Always run
`npm` commands from inside `app/` — never from the repo root, or you'll
create a stray root `package.json`/`node_modules`.

## Git commits and pull requests

Never attribute commits or pull requests to the agent. Use the repository
owner's identity from the local git config (`user.name` and `user.email`).
Do not set, override, or invent author/committer details. Before pushing,
verify the latest commit author matches the local git config.
