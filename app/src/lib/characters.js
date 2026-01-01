/** Character constants matching puzzle_generation/src/utils.py */

export const CHARACTERS = [
  { name: "Alice Addams", shortName: "Alice" },
  { name: "Baker Bob", shortName: "Bob" },
  { name: "Captain Charlie", shortName: "Charlie" },
  { name: "Dr Doris", shortName: "Doris" },
  { name: "Elder Edith", shortName: "Edith" },
  { name: "Farmer Frank", shortName: "Frank" },
];

/**
 * Get default villager names, extending if needed.
 * @param {number} N - Number of villagers
 * @returns {Array<{name: string, shortName: string}>} List of N villager objects
 */
export function getDefaultCharacters(N) {
  return CHARACTERS.slice(0, N);
}
