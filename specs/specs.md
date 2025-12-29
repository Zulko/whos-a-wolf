Problem: you've been sent to the village of X, where werewolves have been killing people at night, and citizens have been hanging alleged werewolves by day.
Now there are only 6 villagers left, and you must establish once and for all who is a werewolf and who isn't.
Werewolves are untrustful: at least one thing they say is wrong. Other villagers always tell the truth.

Variables are WA WB WC WD WE WF meaning "A is a werewolf", "B is a werewolf", etc.
Each villager has a statement on the others:

CA = F1(WB, WC, WD, WE, WF) Where F1 is a logical function
CB = F2(WA, WC, WD, WE, WF)
etc.

Since werewolves lie at least once and humans never lie, we have WA == not(CA), WB == not(CB) etc.

There must be a unique solution, which means a unique set of values for (WA WB WC WD WE WF) that makes the problem coherent for all the statements. I'll call this a Werewolf Problem in the rest of the specs.

- Is there a mathematical way to generate such problems?
- what frameworks would you use.

# Villager names

The names can be parameters provided later, but the defaults could be:

Alchemist Alice
Barber Bob
Captain Custard
Doctor Dorothy
Elder Edith
Farmer Frank

Each of the logical relations will be represented by a class that can be easily hashed, converted to z3, converted to plain English.

# Types of statements

## Statements about a relationships

class RelationshipStatement:
a_index:
b_index:

class IfAThenB(PairRelationship):

      def to_z3(self, W): return W[a_index] => W[b_index]
      def to_english(self, names): "If {names[a_index]} is a werewolf, then {names[b_index] is a werewolf}"
      def __str__(self): return "W{a_index} => W{b_index}      a_index:
      b_index:"

Other pair relationship classes:

- "Either A and B are both werevolves or none of them are" (A=B)
- "At least one of A and B are werewoves"(A or B)
- "Exactly one of A or B are werewolves" (A != B)
- "If A is not a werewolf, then B is a werewolf" (not(A)=>B)
- "None of them are werewolves" (not(A) and not(B))

## Count statement

there are classes with a single parameter

class CountStatement
count=3
def to_z3(self):
return Sum([If(v, 1, 0) for v in vars]) == self.count

     def to_english(self): return "There are {self.count} werewolves."

     def __Str__(self): return "{count} werevolves"

Also these classes:

- There are at most {count} werewolves
- There are at least {count} werewolves
- There is an even number of werevolves
- there is an odd number of werewolves.

## String-to-statement

We will have a function Statement.from_string(str) that returns a statement of the right class for each string, like "W2 => W3" becomes IfAThenB(2, 3)".

# Process to generate a new puzzle.

## The set of truth tables.

How the algorithm should work:

- Generate all possible truth assignments for the 6 variables WA, WB, WC, WD, WE, WF, of the form (True, True, False, False, True). And give them a number. The easiest is probably to use the binary representation of the numbers from 0 to 2^6. It should be a dictionnary truth_assignment_to_index = {(\*assignment): index}
- Then for each possible statement (for instance, all pairwise relationships for all values of a and b), make the list of truth assignments that the statement is NOT compatible with:

statement_to_imcompatible_assignments = {str(statement): set(
index
for truth_assignment, index in truth_assignment_to_index.items()
if not statement.evaluate_on(truth_assignment)
)}

This table is computed once, then stored to disk (as JSON).

## Generating a problem

For a given truth table, say (True, True, True, False, False, False). We will find a set of assignments that eliminate all assignments except this one.

- get the index for that assignment (index = truth_assignment_to_index[(True, True, True, False, False, False)])
- Find all the truth assignments that do not contain the index.
- Find a minimal cover of the truth assignments such that they cover all other indices. This means they only leave our selected assignment as the only possible one. We will have a function find_minimal_cover(subsets) which returns a minimal cover subset found using a greedy algorithm. In our case the minimal cover will be expressed in terms of the strings "W1 => W2", "W5!=W6", etc.

- The rest of the algorithm will consist in finding 3 more statements which are lies (they are incompatible with the ground truth (T, T, T, F, F, F)) but also such that when the statements are attributed to the different characters, the resulting werewolf problem has a unique solution. How this will be done exactly, will depend on the length of the minimal-cover solutions in the previous steps.

## APPENDIX - examples of real code for reference (doesn't fully encode what we have here)

This snippet (with limited number of expressions) shows how to check that a problem has a single solution with z3.

```python
from z3 import *

V = ["A","B","C","D","E","F"]
W = {name: Bool(f"W{name}") for name in V}

def exactly_k(vars, k: int):
    return Sum([If(v, 1, 0) for v in vars]) == k

def unique_model(solver, vars_):
    # Return (is_unique, model_or_none)
    if solver.check() != sat:
        return (False, None)
    m = solver.model()
    block = Or([v != is_true(m.eval(v, model_completion=True)) for v in vars_])
    solver2 = Solver()
    solver2.add(solver.assertions())
    solver2.add(block)
    return (solver2.check() == unsat, m)

# Example: build statements S_A..S_F from templates
S = {}

# For illustration, make S_A be: "exactly 2 of {B,C,D} are wolves"
S["A"] = exactly_k([W["B"], W["C"], W["D"]], 2)

# You'd generate these programmatically for all villagers:
# S["B"] = ...
# ...

# Build puzzle constraints
sol = Solver()
for i in V:
    sol.add(S[i] == Not(W[i]))  # S_i <-> ¬W_i; equality works for Bool in Z3

# Optional global constraint: at least 1 wolf
sol.add(Or([W[i] for i in V]))

isuniq, model = unique_model(sol, [W[i] for i in V])
print("unique?", isuniq)
if model:
    print({i: is_true(model.eval(W[i], model_completion=True)) for i in V})
```
