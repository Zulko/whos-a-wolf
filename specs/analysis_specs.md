The goal is to generate many games, and then the statistics of game generation in this project.

In a folder "analysis" at the root, for each number of player 4, 5, 6, write a script that stores the result of 1000 game generations as a JSONL (one line per puzzle)

Then a script that analyses the resulting JSONL to extract:

- The distribution of the number of werewolves in a 6-players problem.
- The general distribution of usage of each statement type.
- The distribution of usage of each statement type, for characters who are werewolves.
- The distribution of usage of each statement type, for characters who are the shill.
