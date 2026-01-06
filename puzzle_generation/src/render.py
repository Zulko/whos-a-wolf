"""Rendering puzzles to text and markdown formats."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Puzzle


class PuzzleRenderer:
    """Renderer for werewolf puzzles."""

    @staticmethod
    def render_to_text(puzzle: "Puzzle") -> str:
        """Render puzzle to plain text format.

        Args:
            puzzle: The puzzle to render

        Returns:
            Plain text representation
        """
        lines = []
        lines.append("=" * 60)
        lines.append("WEREWOLF LOGIC PUZZLE")
        lines.append("=" * 60)
        lines.append("")
        lines.append("You arrive at a village with the following villagers:")
        lines.append("")

        for villager in puzzle.villagers:
            lines.append(f"  {villager.index + 1}. {villager.name}")

        lines.append("")
        has_shill = puzzle.shill_assignment is not None
        if has_shill:
            lines.append("Each villager is either a Human (always tells the truth),")
            lines.append("a Werewolf (at least one thing they say is wrong),")
            lines.append(
                "or a shill (not a werewolf, but at least one thing they say is wrong)."
            )
            lines.append("There is exactly one shill among the non-werewolves.")
        else:
            lines.append("Each villager is either a Human (always tells the truth)")
            lines.append("or a Werewolf (at least one thing they say is wrong).")
        lines.append("")
        lines.append("The villagers make the following statements:")
        lines.append("")

        for villager in puzzle.villagers:
            statements = puzzle.statements_by_speaker[villager.index]
            if not statements:
                continue

            lines.append(f"{villager.name} says:")
            names = [v.name for v in puzzle.villagers]
            for i, statement in enumerate(statements, 1):
                lines.append(f"  {i}. {statement.to_english(names)}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("Can you determine who is a werewolf?")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def render_to_markdown(puzzle: "Puzzle") -> str:
        """Render puzzle to markdown format.

        Args:
            puzzle: The puzzle to render

        Returns:
            Markdown representation
        """
        lines = []
        lines.append("# Werewolf Logic Puzzle")
        lines.append("")
        lines.append("You arrive at a village with the following villagers:")
        lines.append("")

        for villager in puzzle.villagers:
            lines.append(f"- **{villager.name}**")

        lines.append("")
        has_shill = puzzle.shill_assignment is not None
        if has_shill:
            lines.append(
                "Each villager is either a **honest villager** (always tells the truth),"
            )
            lines.append("a **werewolf* (at least one thing they say is wrong),")
            lines.append(
                "or a **shill** (not a werewolf, but at least one thing they say is wrong)."
            )
            lines.append("There is exactly one shill among the non-werewolves.")
        else:
            lines.append(
                "Each villager is either a **honest villager** (always tells the truth)"
            )
            lines.append("or a **werewolf* (at least one thing they say is wrong).")
        lines.append("")
        lines.append("## Statements")
        lines.append("")

        for villager in puzzle.villagers:
            statements = puzzle.statements_by_speaker[villager.index]
            if not statements:
                continue

            lines.append(f"### {villager.name}")
            lines.append("")
            names = [v.name for v in puzzle.villagers]
            if len(statements) == 1:
                # Single statement: use quote format
                lines.append(f"> {statements[0].to_english(names)}")
            else:
                # Multiple statements: use numbered list
                for i, statement in enumerate(statements, 1):
                    lines.append(f"{i}. {statement.to_english(names)}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("**Can you determine who is a werewolf?**")

        if puzzle.solution_assignment:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("## Solution")
            lines.append("")
            werewolves = [
                puzzle.villagers[i].name
                for i, is_wolf in enumerate(puzzle.solution_assignment)
                if is_wolf
            ]
            if werewolves:
                lines.append("The werewolves are:")
                for name in werewolves:
                    lines.append(f"- {name}")
            else:
                lines.append("There are no werewolves - all villagers are human!")

            if puzzle.shill_assignment:
                shills = [
                    puzzle.villagers[i].name
                    for i, is_shill in enumerate(puzzle.shill_assignment)
                    if is_shill
                ]
                if shills:
                    lines.append("")
                    lines.append("The shill is:")
                    for name in shills:
                        lines.append(f"- {name}")

        return "\n".join(lines)
