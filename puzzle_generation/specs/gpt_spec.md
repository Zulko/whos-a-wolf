## Werewolf Logic Puzzle Generator — Spec + Implementation Notes

### Problem statement

You are sent to a village with **N villagers** (initially N=6). Each villager is either:

- a **Human** (always tells the truth), or
- a **Werewolf** (untrustful: **at least one thing they say is wrong**).

Each villager makes **k statements** (k is configurable per villager; typically 1–3). Each statement is a boolean statement about which villagers are werewolves (and possibly counts/parity constraints).

Goal: generate puzzles where the set of statements yields a **unique consistent assignment** of who is a werewolf.

---

## Core variables and semantics

### Werewolf variables

Let `W[i]` be a boolean variable meaning:

- `W[i] = True` ⇒ villager i is a werewolf
- `W[i] = False` ⇒ villager i is human

### Statements per villager

Villager `i` utters `k_i` statements:

- `statements_by_speaker[i] = [C_i0, C_i1, ..., C_i(k_i-1)]`

Each statement `C` is a boolean formula over some subset of the variables `W[0..N-1]` (often excluding `W[i]`, but that is a generation constraint, not required by the logic).

### Truthfulness rule (generalized for 1–3 statements)

Define the **aggregate truth** for speaker `i`:

- `ALL_TRUE[i] = AND(statements_by_speaker[i])`

Truthfulness constraint:

- Human: all statements true ⇒ `W[i] = False` ⇒ `ALL_TRUE[i] = True`
- Werewolf: at least one statement false ⇒ `W[i] = True` ⇒ `ALL_TRUE[i] = False`

So the key equivalence is:

- **`ALL_TRUE[i] == NOT(W[i])`**

This is the central constraint linking “what they say” to “what they are.”

> Optional design variant (not required): enforce that wolves also say at least one true statement. If adopted later, it becomes:
> `W[i] => (NOT ALL_TRUE[i]) AND (OR statements_by_speaker[i])`

---

## Puzzle coherence and uniqueness

A candidate puzzle is _coherent_ if there exists at least one assignment `W` satisfying the truthfulness constraints for all villagers.

A puzzle has a **unique solution** if there is exactly one assignment `W` satisfying those constraints.

We will treat uniqueness as a hard requirement for generation.

---

## Names (default for N=6)

Default villager names (can be overridden by client code):

- `0: "Alchemist Alice"`
- `1: "Barber Bob"`
- `2: "Captain Charles"`
- `3: "Doctor Dorothy"`
- `4: "Elder Edith"`
- `5: "Farmer Frank"`

Names are just UI/serialization parameters; generation uses indices.

---

## Statement object model

### Goals for statement classes

Each statement must support:

- hashing / stable serialization (for caching truth tables)
- conversion to solver form (Z3 expression)
- conversion to English
- evaluation on a concrete assignment (pure-python)

### Base class

Snippet (interface only; no real code):

```text
class Statement:
    statement_id: str                 # stable canonical string (for hashing, cache keys)
    def variables_involved() -> set[int]
    def evaluate_on_assignment(assignment: tuple[bool, ...]) -> bool
    def to_solver_expr(W_vars) -> SolverBooleanExpr
    def to_english(names: list[str]) -> str
    def complexity_cost() -> int   # used to bias toward simpler puzzles
```

`assignment` is a length-N boolean tuple like `(True, False, ...)` representing `W[0..N-1]`.

### Relationship statements (two villagers)

All pairwise statements have indices `a_index`, `b_index` and normally represent formulas like implication, equivalence, xor, etc.

```text
class RelationshipStatement(Statement):
    a_index: int
    b_index: int
```

Examples:

```text
class IfAThenB(RelationshipStatement):
    # semantics: W[a] => W[b]

class BothOrNeither(RelationshipStatement):
    # semantics: W[a] == W[b]

class AtLeastOne(RelationshipStatement):
    # semantics: W[a] OR W[b]

class ExactlyOne(RelationshipStatement):
    # semantics: W[a] XOR W[b]  (i.e., W[a] != W[b])

class IfNotAThenB(RelationshipStatement):
    # semantics: (NOT W[a]) => W[b]

class Neither(RelationshipStatement):
    # semantics: (NOT W[a]) AND (NOT W[b])
```

Implementation notes:

- generation may forbid `a_index == b_index`
- generation may forbid statements referencing the speaker (“no self-reference”)

### Count/parity statements (global or scoped)

Count statements refer to how many werewolves exist among a scope of indices.

```text
class CountStatement(Statement):
    scope_indices: tuple[int, ...]   # typically all villagers, or "all except speaker"
```

Examples:

```text
class ExactlyKWerewolves(CountStatement):
    count: int
    # semantics: SUM(W[i] for i in scope) == count

class AtMostKWerewolves(CountStatement):
    count: int
    # semantics: SUM(...) <= count

class AtLeastKWerewolves(CountStatement):
    count: int
    # semantics: SUM(...) >= count

class EvenNumberOfWerewolves(CountStatement):
    # semantics: SUM(...) % 2 == 0

class OddNumberOfWerewolves(CountStatement):
    # semantics: SUM(...) % 2 == 1
```

Important: decide and document whether `scope_indices` includes the speaker or not. Keep it consistent.

---

## Parsing / canonical serialization

### Canonical string form

We want a stable `statement_id` such that it uniquely identifies a statement instance. Examples:

- `"IMP(2,3)"` for `W2 => W3`
- `"XOR(4,5)"`
- `"COUNT_EQ(scope=ALL,count=3)"`

### Factory parsing

We support a string-to-statement factory:

```text
class StatementFactory:
    def from_canonical_string(s: str) -> Statement
    def to_canonical_string(statement: Statement) -> str
```

Notes:

- parsing should be strict (regex or small grammar), not ad-hoc split logic
- `to_canonical_string()` must be canonical so hashing and caching are stable

---

## Puzzle representation

```text
class Villager:
    index: int
    name: str

class Puzzle:
    villagers: list[Villager]                 # length N
    statements_by_speaker: list[list[Statement]]       # length N; each inner list length 1..3
    # optional metadata
    difficulty_score: float
    solution_assignment: tuple[bool, ...]      # W* (if known during generation)
```

The puzzle is solved by finding assignments `W` satisfying:

For each i:

- `AND(statements_by_speaker[i]) == NOT(W[i])`

---

## Solver/verification layer (Z3-based)

### Z3 model building (conceptual API)

We will build a solver instance from a puzzle.

```text
class PuzzleSolver:
    def build_solver(puzzle: Puzzle) -> Solver
    def find_one_solution(puzzle: Puzzle) -> tuple[bool, ...] | None
    def is_uniquely_satisfiable(puzzle: Puzzle) -> bool
    def enumerate_solutions(puzzle: Puzzle, max_solutions: int) -> list[tuple[bool, ...]]
```

Uniqueness check concept:

- find one model
- add a blocking constraint “assignment != found_model”
- check satisfiable again

This is used both as a verifier for generated puzzles and (optionally) inside generation.

---

## Fast generation using truth tables (bitmask approach)

Since N=6 initially, there are `2^N = 64` possible assignments. We can precompute truth values for each statement and represent sets of assignments as bitmasks (integers).

### Assignment indexing

We index each assignment by interpreting it as an N-bit number:

- `assignment_index = sum((1 if W[i] else 0) << i for i in range(N))`

We also maintain the reverse mapping if needed:

- `index_to_assignment(index) -> tuple[bool,...]`

### Precomputed statement truth masks

For each atomic statement `c` we compute:

- `truth_mask[c]`: bitmask with bit `idx` = 1 iff statement is TRUE under that assignment

Then `false_mask[c]` is the complement within N bits:

- `false_mask[c] = all_assignments_mask XOR truth_mask[c]`

Stored in a cache file:

```text
class StatementTruthTableCache:
    N: int
    statement_id_to_truth_mask: dict[str, int]

    def build_for_statement_library(statement_library: list[Statement]) -> StatementTruthTableCache
    def save_to_json(path: str)
    def load_from_json(path: str) -> StatementTruthTableCache
```

### Precompute “human/wolf masks” per speaker

For each villager index i:

- `human_mask_by_speaker[i]`: assignments where `W[i] == False`
- `wolf_mask_by_speaker[i]`: assignments where `W[i] == True`

These depend only on N.

---

## Generation algorithm

### High-level goal

Generate `statements_by_speaker` such that:

- the puzzle is coherent
- it has exactly one solution (unique `W*`)
- each speaker has 1..3 statements (often exactly 2, configurable)
- optional: style constraints (no duplicates, avoid trivial statements, etc.)

### Generation inputs

```text
class GenerationConfig:
    N: int = 6
    statements_per_speaker_min: int = 2
    statements_per_speaker_max: int = 2   # or 3
    require_unique_solution: bool = True

    forbid_self_reference: bool = True
    allow_count_statements: bool = True
    max_count_statements_total: int
    complexity_budget: int

    # selection / search
    max_attempts: int
    greedy_candidate_pool_size: int
```

### Step 1: choose target solution assignment `W_star`

Select a random assignment `W_star` (tuple[bool,...]) subject to optional constraints:

- e.g. require number of werewolves within a range

```text
def choose_target_assignment(config: GenerationConfig) -> tuple[bool, ...]
```

### Step 2: statement library construction

Build a library of atomic statements allowed under config (pair statements, count statements, etc.)

```text
def build_statement_library(config: GenerationConfig) -> list[Statement]
```

### Step 3: generate speaker statement bundles consistent with W_star

For each speaker i, we must select a bundle of 1..3 statements such that W_star satisfies the truthfulness rule:

Let `bundle = [c1, c2, ... ck]`

- `all_true_under_W_star = evaluate(c1,W_star) AND ... AND evaluate(ck,W_star)`
- Must equal `NOT(W_star[i])`

So:

- if `W_star[i]` is human: all statements must be true under W_star
- if `W_star[i]` is wolf: at least one statement must be false under W_star

We’ll generate bundles from atomic statements using precomputed truth masks.

```text
def list_candidate_bundles_for_speaker(
    speaker_index: int,
    W_star: tuple[bool, ...],
    statement_library: list[Statement],
    truth_cache: StatementTruthTableCache,
    config: GenerationConfig
) -> list[list[Statement]]
```

(Implementation detail: you usually don’t want to enumerate _all_ 3-combinations; generate bundles incrementally and sample.)

### Step 4: greedy search to reach uniqueness

Maintain a bitmask of assignments that remain possible given decisions so far.

- `remaining_mask` starts as all 1s (all assignments possible).
- As we assign bundles to speakers, we intersect `remaining_mask` with that speaker’s compatibility mask.

#### Compute speaker compatibility mask for a bundle

Given speaker i and bundle statements `[c1..ck]`:

- `bundle_all_true_mask = truth_mask[c1] & truth_mask[c2] & ... & truth_mask[ck]`

Then assignments consistent with speaker i are:

- humans must be in `bundle_all_true_mask`
- wolves must be in `NOT bundle_all_true_mask`

So:

- `compat_mask = (human_mask_by_speaker[i] & bundle_all_true_mask) |
           (wolf_mask_by_speaker[i] & (~bundle_all_true_mask within N bits))`

This enforces `AND(statements) == NOT(W[i])` for that speaker across all candidate assignments.

Greedy step:

```text
def greedy_assign_statements_until_unique(
    W_star: tuple[bool, ...],
    candidate_bundles_by_speaker: list[list[list[Statement]]],
    truth_cache: StatementTruthTableCache,
    config: GenerationConfig
) -> Puzzle
```

Greedy heuristic:

- at each step, pick an unassigned speaker i
- test a subset of candidate bundles
- choose the bundle that:

  1. keeps W_star in the remaining set, and
  2. removes the most other assignments from `remaining_mask`

- continue until `remaining_mask` contains only W_star’s index

Stop conditions:

- success: `remaining_mask == mask_of(W_star)`
- fail: no bundle can keep W_star while making progress → restart with new W_star or new sampling

### Step 5: verify with Z3 uniqueness check

Even if the bitmask method says unique, verify with the solver layer:

```text
def verify_unique_solution_with_solver(puzzle: Puzzle) -> bool
```

This also guards against bugs in statement evaluation or parsing.

---

## Output formatting

### English rendering

Each statement has `to_english(names)`.

A puzzle renderer prints:

- intro story
- list villagers
- for each villager: numbered list of their statements (1..3)
- optionally: provide solution separately

```text
class PuzzleRenderer:
    def render_to_text(puzzle: Puzzle) -> str
    def render_to_markdown(puzzle: Puzzle) -> str
```

---

## Practical constraints & quality knobs

Suggested constraints for better puzzles:

- Forbid self-reference (`speaker_index` not in `variables_involved()`)
- Limit “too strong” statements (e.g., “Exactly 3 werewolves”) via `complexity_cost` and max count-statements
- Avoid duplicate statement_ids across all speakers
- Avoid duplicate bundles
- Ensure diversity: at least X relationship statements total

---

## Summary of key functions / modules

### Main modules

- `statements.py` — statement class hierarchy + english + solver conversion + evaluation
- `statement_factory.py` — canonical serialization + parsing
- `truth_cache.py` — precompute/store truth masks
- `generator.py` — target assignment selection + greedy bundle assignment
- `solver.py` — Z3 verifier and uniqueness checker
- `render.py` — text/markdown output

### Must-have functions (names)

- `choose_target_assignment(config) -> assignment`
- `build_statement_library(config) -> list[Statement]`
- `StatementTruthTableCache.build_for_statement_library(...)`
- `list_candidate_bundles_for_speaker(...)`
- `compute_bundle_all_true_mask(bundle, truth_cache) -> int`
- `compute_speaker_compatibility_mask(i, bundle, precomputed_masks, truth_cache) -> int`
- `greedy_assign_statements_until_unique(...) -> Puzzle`
- `PuzzleSolver.is_uniquely_satisfiable(puzzle) -> bool`
- `PuzzleRenderer.render_to_markdown(puzzle) -> str`

---

This spec gives a coding agent everything needed to implement the generator without committing to a specific solver strategy: generation can be table-driven/bitmask-fast, with Z3 used as a correctness verifier and for edge-case debugging.
