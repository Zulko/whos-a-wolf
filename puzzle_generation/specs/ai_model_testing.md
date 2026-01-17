I would like to build a system that:
- Generates N werewolf problems with (4,5,6) villagers, possibly with the script in scripts/generate_puzzles.py.
- For each problem it will load it, transform it into a full prompt with intro (i guess with puzzle.render_to_markdown()).
- Use gemini bash to send all of the problems to gemini bash. The result should be a structured answer {"werewolf_assignment": [bool, ...], "shill_assignment": [bool, ...]}
- The answer for each puzzle will be compared to the solution assignment found with find_one_solution_with_shill (from solver.py).
- Stats on the number of puzzles that the model got correct will be saved to a file.

The specs above describe the batch version of the system, but I would like the implementation to also allow for testing a single puzzle.