/** Puzzle loading and management utilities */

import { Statement } from "./statements.js";
import { getDefaultCharacters } from "./characters.js";

// Import puzzle files directly - Vite will bundle them at build time
import puzzles4Raw from "./puzzles/4_villagers.txt?raw";
import puzzles5Raw from "./puzzles/5_villagers.txt?raw";
import puzzles6Raw from "./puzzles/6_villagers.txt?raw";

export const DEFAULT_PUZZLE = "I-3-1_N-0-2_X-1-3_F-5-0_E-0.1.2.3.5-4_B-0-3";

/**
 * Parse puzzle text into an array of puzzle strings.
 * @param {string} text - Raw text content from puzzle file
 * @returns {string[]} Array of puzzle strings
 */
function parsePuzzleText(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

// Parse puzzles at module load time - they're bundled in the app
const puzzleCache = {
  4: parsePuzzleText(puzzles4Raw),
  5: parsePuzzleText(puzzles5Raw),
  6: parsePuzzleText(puzzles6Raw),
};

// Log puzzle counts for debugging
console.log(`Loaded ${puzzleCache[4].length} puzzles for 4 villagers`);
console.log(`Loaded ${puzzleCache[5].length} puzzles for 5 villagers`);
console.log(`Loaded ${puzzleCache[6].length} puzzles for 6 villagers`);

/**
 * Get a random puzzle from the cached puzzles.
 * @param {number} numVillagers - Number of villagers (4, 5, or 6)
 * @returns {string} Puzzle string
 */
export function getRandomPuzzle(numVillagers) {
  const puzzles = puzzleCache[numVillagers];

  if (!puzzles || puzzles.length === 0) {
    console.warn(
      `No puzzles cached for ${numVillagers} villagers, using default`
    );
    return DEFAULT_PUZZLE;
  }

  const randomIndex = Math.floor(Math.random() * puzzles.length);
  return puzzles[randomIndex];
}

/**
 * Parse puzzle string from URL query parameter or use default.
 * @param {string} puzzleStr - Puzzle string from URL
 * @param {number} numVillagers - Number of villagers (4, 5, or 6)
 * @returns {Map<string, Statement>} Map from villager name to statement
 */
export function parsePuzzleFromString(puzzleStr, numVillagers) {
  const characters = getDefaultCharacters(numVillagers);
  const statementStrings = puzzleStr.split("_").filter((s) => s.length > 0);

  if (statementStrings.length !== numVillagers) {
    throw new Error(
      `Expected ${numVillagers} statements but got ${statementStrings.length}`
    );
  }

  const statements = new Map();
  for (let i = 0; i < numVillagers; i++) {
    const statement = Statement.fromShortString(statementStrings[i]);
    statements.set(characters[i].name, statement);
  }

  return statements;
}

/**
 * Get puzzle string from URL query parameter or return null if not present.
 * @returns {string|null} Puzzle string or null if not in URL
 */
export function getPuzzleFromURL() {
  const params = new URLSearchParams(window.location.search);
  const puzzleParam = params.get("puzzle");
  // Return null if puzzle param is null, undefined, or empty string
  if (!puzzleParam || puzzleParam.trim() === "") {
    return null;
  }
  return puzzleParam;
}

/**
 * Load a random puzzle from the cached puzzles.
 * @param {number} numVillagers - Number of villagers (4, 5, or 6)
 * @returns {string} Puzzle string
 */
export function loadRandomPuzzle(numVillagers) {
  return getRandomPuzzle(numVillagers);
}

/**
 * Get language parameter from URL query parameter or return null if not present.
 * @returns {string|null} Language code ('en' or 'fr') or null if not in URL
 */
export function getLangFromURL() {
  const params = new URLSearchParams(window.location.search);
  const langParam = params.get("lang");
  // Return null if lang param is null, undefined, or empty string
  if (!langParam || langParam.trim() === "") {
    return null;
  }
  // Validate that it's a supported language
  if (langParam === "en" || langParam === "fr") {
    return langParam;
  }
  return null;
}

/**
 * Update URL with new language parameter.
 * @param {string} lang - Language code ('en' or 'fr')
 */
export function updateLangURL(lang) {
  const url = new URL(window.location.href);
  url.searchParams.set("lang", lang);
  window.history.pushState({}, "", url);
}

/**
 * Update URL with new puzzle string.
 * @param {string} puzzleStr - Puzzle string to set in URL
 */
export function updatePuzzleURL(puzzleStr) {
  const url = new URL(window.location.href);
  url.searchParams.set("puzzle", puzzleStr);
  // Preserve lang parameter if it exists
  const currentLang = getLangFromURL();
  if (currentLang) {
    url.searchParams.set("lang", currentLang);
  }
  window.history.pushState({}, "", url);
}
