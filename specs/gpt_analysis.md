You’re very close to a clean, generatable “liars/werewolves” logic-puzzle spec. The main thing to watch is that your truthfulness rule and your generation method (set cover) need to line up perfectly.

Core logic: your equivalence is valid (with an important assumption)

You wrote:

werewolves lie at least once and humans never lie, we have WA == not(CA)

That equivalence is correct only if each villager makes exactly one claim (one proposition) and:

humans: their claim is true

werewolves: their claim is false (since “at least one thing they say is wrong” + only one thing said ⇒ that thing must be wrong)

If you ever let villagers make multiple claims, then the werewolf constraint becomes:

werewolf ⇒ NOT(all claims true) (i.e., at least one false)

human ⇒ all claims true

So: your current spec is consistent, just “bakes in” one claim per person.

Modeling note: be explicit about “claims talk about others”

You stated CA = F1(WB, WC, WD, WE, WF) (A talks about others), but later your claim classes allow arbitrary indices. That’s fine, but you should enforce no self-reference at generation time (or decide you allow it).

Also decide whether “CountClaim” counts all 6 or “all except speaker”. Either is fine, but you want it consistent and explicit.

Claim class design: good, with a couple tweaks

Your plan (“hashable, z3, english”) is solid. I’d add:

vars_involved() → returns the set of indices used (helps generation + difficulty scoring)

evaluate(assignment) → a pure-python evaluator (you already implicitly use this)

complexity_cost() → a small integer used to bias generation toward simpler puzzles

RelationshipClaim list looks good

Your pairwise operators cover a nice basis. One caution:

“None of them are werewolves” = ¬A ∧ ¬B is very strong and often dominates. It’s fine, but you may want to assign it a higher complexity_cost or restrict how often it appears.

Count claims are great for variety

Your Z3 encoding is correct in spirit. Just ensure you pass the intended variable list:

Sum([If(W[i], 1, 0) for i in scope]) == count


where scope is either range(6) or “all except speaker”.

String-to-claim

Totally doable, but don’t hand-roll parsing with splits once you have more forms.

Use a tiny grammar (e.g. lark), or a strict regex set.

Also: from_string() should probably return a canonical object so hashing/serialization is stable.

The big thing: set-cover generation won’t automatically respect speaker truthfulness

Your set-cover idea (“pick claims that eliminate all assignments except target”) is basically a hitting set over falsifying assignments. That’s a valid approach for building constraints that uniquely identify a target assignment.

But your puzzles are not “just a conjunction of claims”.
They’re “claims + the meta-rule”:

For each villager i:

If W[i] == False (human), then Claim[i] must evaluate True

If W[i] == True (werewolf), then Claim[i] must evaluate False

So the actual constraint is:

ClaimTruth[i] == ¬W[i]

That coupling means you can’t treat claims as independent eliminators unless you incorporate who says what into the coverage.

A cleaner generation viewpoint

Think of a generated puzzle as choosing, for each villager i, a claim Ci from a library such that the system:

∀i: evaluate(Ci, W) == ¬W[i]

has exactly one solution for W.

That’s the crisp mathematical formulation.

Is there a mathematical way to generate such problems?

Yes — it’s a standard constraint satisfaction / SAT / SMT synthesis problem:

Universe: all possible assignments W ∈ {0,1}^6

Decision variables: which claim each villager utters (choose from a finite library)

Constraints:

Coherence: for the “real” W, each villager’s truthfulness matches their type

Uniqueness: exactly one W satisfies all villagers’ truthfulness constraints

Optional: difficulty / style constraints (no duplicate claim forms, avoid trivial counts, etc.)

This is basically synthesis under uniqueness, often solved with:

SAT/SMT + iterative blocking clauses

CP-SAT (OR-Tools)

brute-force search + Z3 verification (simple and often fastest for 6 villagers)

What frameworks would I use?

Given you already like Z3:

1) Z3 (SMT) — best fit

Use Z3 to:

represent W[i] booleans

represent each candidate claim as a Z3 formula

enforce claim(i) == Not(W[i])

check uniqueness by model enumeration (or “find one model, then block it, see if another exists”)

2) python-constraint / python-sat (SAT)

If your claim library is purely boolean and small, SAT is great.
But you’ll likely re-implement some counting constraints unless you go PB-SAT.

3) OR-Tools CP-SAT

Really good if you lean into integer/count constraints and want optimization (“minimize complexity”, “maximize variety”).

For your current plan, I’d do:

generation with a simple search/heuristics

verification + uniqueness with Z3

A generation approach that will work well in practice

Here’s a robust recipe that matches your spec and keeps your “precompute truth tables” idea:

Step A — Precompute claim truth tables (your idea, but include speaker coupling)

For each claim c you can compute the set of assignments where it is True/False.
Store both:

true_set[c] = {assignments where c is true}

false_set[c] = {assignments where c is false}

Step B — Choose a target solution W*

Pick a random W* (optionally with constraints like “between 2 and 3 werewolves”).

Step C — For each villager i, choose a claim consistent with W*

You need:

if W*[i] = 0 (human) ⇒ choose claim c such that W* ∈ true_set[c]

if W*[i] = 1 (werewolf) ⇒ choose claim c such that W* ∈ false_set[c]

That ensures the “real world” is coherent.

Step D — Enforce uniqueness by eliminating all other assignments

Maintain a set Remaining = all_assignments.
After assigning claims to villagers, an assignment W remains viable iff for all i:

if W[i]=0 then W ∈ true_set[C_i]

if W[i]=1 then W ∈ false_set[C_i]

You can compute the survivors quickly because it’s only 64 assignments.

Goal: Remaining == {W*}.

Step E — Search strategy

Greedy works well:

At each step pick an unassigned villager i and choose among candidate claims the one that removes the most wrong assignments while keeping W*.

Then finalize with a Z3 uniqueness check (cheap) as a sanity check.

This gives you what you wanted (table-driven) but properly accounts for “the claim truth depends on whether i is wolf”.

Your “add 3 lies afterwards” plan: I’d invert it

Right now you:

find a minimal-cover of constraints for W*

then try to “inject lies” and still keep uniqueness

That’s harder than it needs to be.

Instead:

Decide W*

Decide which villagers are wolves (already determined by W*)

For each villager i, directly choose a claim that is true/false accordingly

Keep adding claims until uniqueness holds

This way “lies” are not an afterthought; they’re baked in.

Small spec improvements that will save you pain

Decide whether a_index == b_index is allowed for pair claims (usually no).

Add a “no duplicate claim” rule (or a soft penalty), otherwise generation often repeats.

Add a difficulty signal:

fewer count-claims = harder

avoid “There are exactly k werewolves” too often (it can trivialize)

penalize claims that directly mention only one variable (“B is a werewolf”) if you add those later

If you want, I can sketch the exact Z3 uniqueness-check pattern (find model, block it, check sat again) and a greedy generator loop that uses your precomputed incompatible_assignments tables — but the big conceptual fix is: covering assignments must incorporate speaker truthfulness, not just claim truth.
