You are writing **short first-person dialogue** for a deduction game: an inspector interviews villagers about one another.

You will receive the inspector’s raw notes for each villager. The notes are logically useful but lack realism and flow.

### Task

For **each villager**, rewrite their statements to be:

- Natural, grounded, and motivated (why they say it), using the **villager’s profession** to justify how they know or suspect things.
- As **short** as possible.
- **Only what the villager says** (no narrator text, no stage directions, no descriptions outside their speech).
- The **second statement must connect to the first**, especially if they mention the same person.

### Hard logic requirement (do not break this)

Each rewritten statement must end with a **clear logical statement** that preserves the original proposition (in plain language).

Critical: the logical statement must be the **final sentence**, written **fluently in-character**, with **no label** like “Logic:”, no brackets, and no meta-formatting.
Example ending sentence: “So if X is a werewolf, Y is too.”

Do not let style obscure meaning. The logic must be easy to extract.

### World constraint (avoid false implications)

Villagers do **not** spend nights in one another’s company.  
Only imply being together at night if the speaker explicitly states they **know** the other is **not** a werewolf.

### Special phrasing: even/odd number of werewolves

If the original note says the number of werewolves is even/odd, express it concretely, e.g.:

- Even: “I counted the tracks; they move in pairs. The number of werewolves is even.”
- Odd: “There’s a lone set of prints—someone hunts alone. The number of werewolves is odd.”

### Output format

For each villager, output exactly two lines:

- `Statement 1: ...` (ending with the logical final sentence)
- `Statement 2: ...` (ending with the logical final sentence)

No extra headers, no extra commentary.

### Mini examples (style + logic at the end)

- “Those two always arrive together at the market; I see it every dawn. They’re either both werewolves or neither is.”
- “I saw them transform—my lantern caught their faces. X is a werewolf and Y is a werewolf.”
