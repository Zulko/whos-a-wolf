# The whos-a-wolf app

A single page application with the following state, logics, and layout.

# variables and State

```javascript
// The characters as defined in puzzle_generation/src/utils.py
// This is a given constant of the app,
constant characters: [{name: "Alice Addams" short_name: "Alice"}, ...]

state = {
// Statements will be defined in the app as in puzzle_generation/src/statements.py
// And will have the same method to be read from a short string.
// and the method to be evaluated on a suspicion list.
statements: {name: {type: IfAThenB, parameters: {a_index, ...}}]

// The decisions of the player for all wolves
suspicions: {name: werewolf | truthful | shill}
}

computed = {
    // This will go through the player's decisions and apply a series of ifs:
    // - if no villager is marked as werewolf: "We know that at least one of these villagers is a werewolf "
    // - if no villager is marked as shill: "We know that one villager is a shill"
    // - if more than one villager is marked as shill: "we know that exactly one villager is a shill"
    // Then for each characters, if the character is marked as werewolf or shill, it will check that the character's statement is wrong when evaluated on the suspicions, otherwise it will be "you marked {name} as a {shill|werewolf} yet their statement are in agreement with the rest of your suspicions. And if the character's suspicion is a truthful it will check that the statement is true when evaluated on the suspicions, otherwise "You marked {name} as truthful, yet their statement doesn't match the rest of your suspicions".
    decision_error: str | null
}
```

# Layout

```html
<h1> Who's a Wolf </h1> With a nice old-school font, something that evoques a renaissance-style handwritten font.

<p class="intro">
You have been sent to investigate the town of Holwmoor, where only a handful of villagers remain after a series of werewolf attacks. One or more of these villagers are secretly werewolves who will lie in their statements. The other villagers are truthful, but you've been warned that one of these villager is a shill who was paid by the werewolves to lie.

Determine who's a lying werewolf, who is a honest villager, and who is the lying shill.
</p>

<for each villager>
   <villager-card>
   <picture> # the picture will be one of 4 states depending on whether the villager is deemed "truthful?", "werewolf?", or "shill?". When the player has  found the right solution (when decision_error is none), the picture reflects the truth. Villagers will have pictures {name}_smile.png {name}_angry.png {name}_werewolf.png {name}_shill.png. As long as decision_error is not None, the villagers are _smiling if suspicion is truthful and _angry if shill/werewolf. Once decision_error is None, werewolf villagers are _werewolf, the shill villager is _shill, and the other villagers are _releaved.
   <button> {{suspicions[villager.name]}} # Button is white font, green background for "Truthful" suspicion, black background for "werewolf", and red background for "shill"
   <statement> {{ statements[villager.name] }}
</for>

<if decision_error> {{decision error}}
    <else> You solved the case! Congratulations # in a festive way
</>

<button>New game</button> # opens a modal "start a new game" with a radio choice 4/5/6 for the number of villagers and a button under it "start".
```

# puzzle data mechanism

The URL may contain puzzle data as `?puzzle=I-3-1_N-0-2_X-1-3_F-5-0_E-0.1.2.3.5-4_B-0-3` (make this value the default). When the app loads it should read that data and convert it into the `statements`, using the conversion logics from puzzle_generation/src/statements.py.

When the user starts a new game, the puzzle data will be loaded randomly from a puzzle data list read from a file containing 1000 of those puzzles.
