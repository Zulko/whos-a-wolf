<script>
  import { onMount } from "svelte";
  import { getDefaultCharacters } from "./lib/characters.js";
  import {
    getPuzzleFromURL,
    parsePuzzleFromString,
    updatePuzzleURL,
    getRandomPuzzle,
  } from "./lib/puzzle.js";
  import VillagerCard from "./components/VillagerCard.svelte";
  import NewGameModal from "./components/NewGameModal.svelte";

  let numVillagers = $state(6);
  let statements = $state(new Map());
  let suspicions = $state(new Map());
  let showNewGameModal = $state(false);
  let theme = $state("system"); // "light" | "dark" | "system"

  const characters = $derived(getDefaultCharacters(numVillagers));

  // Computed: decision_error
  const decisionError = $derived.by(() => {
    const suspicionValues = Array.from(suspicions.values());
    const werewolfCount = suspicionValues.filter(
      (s) => s === "werewolf"
    ).length;
    const shillCount = suspicionValues.filter((s) => s === "shill").length;

    // Check: at least one werewolf
    if (werewolfCount === 0) {
      return "We know that at least one of villager is a werewolf. Click on the characters to change your suspicions.";
    }

    // Check: exactly one shill
    if (shillCount === 0) {
      return "We know that one villager must be a shill.";
    }
    if (shillCount > 1) {
      return "We know that exactly one villager must bea shill.";
    }

    // Check statement consistency
    // Convert suspicions to werewolf assignment (True = werewolf, False = not werewolf)
    const werewolfAssignment = characters.map(
      (char) => suspicions.get(char.name) === "werewolf"
    );

    for (const char of characters) {
      const suspicion = suspicions.get(char.name);
      const statement = statements.get(char.name);

      if (!statement) continue;

      const statementResult =
        statement.evaluateOnAssignment(werewolfAssignment);

      if (suspicion === "werewolf" || suspicion === "shill") {
        // Werewolves and shills lie: statement must be FALSE
        if (statementResult) {
          const role = suspicion === "werewolf" ? "werewolf" : "shill";
          return `You suspect ${char.name} of being a ${role}, yet according to your other suspicions, they are not lying.`;
        }
      } else if (suspicion === "truthful") {
        // Truthful villagers tell truth: statement must be TRUE
        if (!statementResult) {
          return `You marked ${char.name} as truthful, yet their statement disagrees with the rest of your suspicions.`;
        }
      }
    }

    return null; // No errors - puzzle solved!
  });

  function initializePuzzle(puzzleStr, nVillagers) {
    numVillagers = nVillagers;
    statements = parsePuzzleFromString(puzzleStr, nVillagers);

    // Initialize suspicions to "truthful" for all villagers
    suspicions = new Map();
    for (const char of getDefaultCharacters(nVillagers)) {
      suspicions.set(char.name, "truthful");
    }
  }

  function handleSuspicionChange(villagerName, newSuspicion) {
    suspicions.set(villagerName, newSuspicion);
    suspicions = new Map(suspicions); // Trigger reactivity
  }

  function handleNewGame(nVillagers, puzzleStr) {
    initializePuzzle(puzzleStr, nVillagers);
  }

  function openNewGameModal() {
    showNewGameModal = true;
  }

  function setTheme(newTheme) {
    theme = newTheme;
    localStorage.setItem("theme", newTheme);
    if (newTheme === "system") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", newTheme);
    }
  }

  onMount(() => {
    // Load saved theme preference
    const savedTheme = localStorage.getItem("theme") || "system";
    setTheme(savedTheme);
    // Puzzles are already loaded and bundled in the app
    // Initialize from URL or select random puzzle
    let puzzleStr = getPuzzleFromURL();
    let nVillagers = 6; // Default to 6 villagers

    if (!puzzleStr) {
      // No puzzle in URL, select a random one (default to 6 villagers)
      puzzleStr = getRandomPuzzle(nVillagers);
      updatePuzzleURL(puzzleStr);
    } else {
      // Determine number of villagers from puzzle string
      const statementCount = puzzleStr
        .split("_")
        .filter((s) => s.length > 0).length;

      if (statementCount === 0) {
        console.warn("Invalid puzzle string in URL, selecting random puzzle");
        puzzleStr = getRandomPuzzle(nVillagers);
        updatePuzzleURL(puzzleStr);
      } else {
        nVillagers = statementCount;
      }
    }

    try {
      initializePuzzle(puzzleStr, nVillagers);
    } catch (error) {
      console.error("Error initializing puzzle:", error);
      // Fallback to random puzzle
      puzzleStr = getRandomPuzzle(nVillagers);
      updatePuzzleURL(puzzleStr);
      initializePuzzle(puzzleStr, nVillagers);
    }

    // Listen for URL changes (e.g., browser back/forward)
    window.addEventListener("popstate", () => {
      let newPuzzleStr = getPuzzleFromURL();
      let newNVillagers = 6;

      if (!newPuzzleStr) {
        // No puzzle in URL, select a random one
        newPuzzleStr = getRandomPuzzle(newNVillagers);
        updatePuzzleURL(newPuzzleStr);
      } else {
        const newStatementCount = newPuzzleStr
          .split("_")
          .filter((s) => s.length > 0).length;

        if (newStatementCount === 0) {
          newPuzzleStr = getRandomPuzzle(newNVillagers);
          updatePuzzleURL(newPuzzleStr);
        } else {
          newNVillagers = newStatementCount;
        }
      }

      try {
        initializePuzzle(newPuzzleStr, newNVillagers);
      } catch (error) {
        console.error("Error handling popstate:", error);
        // Fallback to random puzzle
        newPuzzleStr = getRandomPuzzle(newNVillagers);
        updatePuzzleURL(newPuzzleStr);
        initializePuzzle(newPuzzleStr, newNVillagers);
      }
    });
  });
</script>

<main>
  <h1>Who's a Wolf ?</h1>

  <p class="intro">
    You’ve been sent to gather statements from the last villagers of Howlmore
    Town after a string of werewolf attacks. One or more are lying because they
    are secretly werewolves. One other villager, you were told, is a shill paid
    by the werewolves to lie.
    <br /><br />
    Can you find who's a werewolf, who's an honest villager, and who is the lying
    shill?
  </p>

  <div class="villagers-grid">
    {#each characters as char}
      <VillagerCard
        villagerName={char.name}
        statement={statements.get(char.name)}
        suspicion={suspicions.get(char.name) || "truthful"}
        isSolved={decisionError === null}
        {numVillagers}
        onSuspicionChange={(newSuspicion) =>
          handleSuspicionChange(char.name, newSuspicion)}
      />
    {/each}
  </div>

  {#if decisionError}
    <div class="error-message">{decisionError}</div>
  {:else}
    <div class="success-message">
      🎉 You solved the case! Congratulations! 🎉
    </div>
  {/if}

  <button class="new-game-button" onclick={openNewGameModal}>New game</button>
</main>

<NewGameModal bind:open={showNewGameModal} onNewGame={handleNewGame} />

<footer class="theme-switcher">
  <button
    class="theme-btn"
    class:active={theme === "light"}
    onclick={() => setTheme("light")}
    title="Light mode">☀</button
  >
  <button
    class="theme-btn"
    class:active={theme === "system"}
    onclick={() => setTheme("system")}
    title="System default">⚙</button
  >
  <button
    class="theme-btn"
    class:active={theme === "dark"}
    onclick={() => setTheme("dark")}
    title="Dark mode">☾</button
  >
</footer>

<style>
  main {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem;
  }

  h1 {
    font-family: "Press Start 2P", monospace;
    font-size: 1.6rem;
    font-weight: 400;
    text-align: center;
    margin-bottom: 1rem;
    color: var(--text-color);
    line-height: 1.4;
  }

  .intro {
    text-align: left;
    max-width: 760px;
    margin: 0 auto 2rem auto;
    line-height: 1.2rem;
    color: var(--text-secondary);
    font-size: 1.35rem;
  }

  .villagers-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    margin-bottom: 2rem;
    justify-items: center;
  }

  @media (min-width: 900px) {
    .villagers-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .error-message {
    text-align: left;
    padding: 1rem;
    background-color: var(--error-bg);
    border: 2px solid var(--error-border);
    border-radius: 8px;
    color: var(--error-text);
    margin-bottom: 1rem;
    font-weight: bold;
    font-size: 1.35rem;
  }

  .success-message {
    text-align: left;
    padding: 1.5rem;
    background-color: var(--success-bg);
    border: 2px solid var(--success-border);
    border-radius: 8px;
    color: var(--success-text);
    margin-bottom: 1rem;
    font-weight: bold;
    font-size: 1.2rem;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
  }

  .new-game-button {
    display: block;
    margin: 2rem auto;
    padding: 0.75rem 2rem;
    font-size: 1.1rem;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .new-game-button:hover {
    background-color: #45a049;
  }

  @media (max-width: 500px) {
    main {
      width: 95%;
      padding: 1rem;
    }

    .intro {
      font-size: 1.1rem;
      line-height: 1.3;
    }

    h1 {
      font-size: 1.2rem;
    }

    .error-message {
      font-size: 1rem;
    }
  }

  .theme-switcher {
    display: flex;
    justify-content: center;
    gap: 0.25rem;
    padding: 2rem 0;
    opacity: 0.4;
    transition: opacity 0.2s ease;
  }

  .theme-switcher:hover {
    opacity: 1;
  }

  .theme-btn {
    width: 2rem;
    height: 2rem;
    padding: 0;
    font-size: 1rem;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 4px;
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .theme-btn:hover {
    background: var(--card-border);
  }

  .theme-btn.active {
    background: var(--text-secondary);
    color: var(--bg-color);
    border-color: var(--text-secondary);
  }
</style>
