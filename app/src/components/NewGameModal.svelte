<script>
  import { _ } from "svelte-i18n";
  import { loadRandomPuzzle, updatePuzzleURL, parsePuzzleFromString } from "../lib/puzzle.js";

  let { open = $bindable(false), onNewGame } = $props();
  let selectedCount = $state("6");

  function handleStart() {
    const count = parseInt(selectedCount);
    const puzzleStr = loadRandomPuzzle(count);
    updatePuzzleURL(puzzleStr);
    onNewGame(count, puzzleStr);
    open = false;
  }

  function handleCancel() {
    open = false;
  }
</script>

{#if open}
  <div class="modal-overlay" onclick={handleCancel} role="button" tabindex="0" onkeydown={(e) => e.key === 'Escape' && handleCancel()}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
      <h2>{$_("modals.newGame.title")}</h2>
      <div class="radio-group">
        <label>
          <input type="radio" value="4" bind:group={selectedCount} />
          {$_("modals.newGame.villagers.4")}
        </label>
        <label>
          <input type="radio" value="5" bind:group={selectedCount} />
          {$_("modals.newGame.villagers.5")}
        </label>
        <label>
          <input type="radio" value="6" bind:group={selectedCount} />
          {$_("modals.newGame.villagers.6")}
        </label>
      </div>
      <div class="modal-buttons">
        <button class="start-button" onclick={handleStart}>{$_("modals.newGame.start")}</button>
        <button class="cancel-button" onclick={handleCancel}>{$_("modals.newGame.cancel")}</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-content {
    background-color: var(--card-bg, #1a1a1a);
    border: 2px solid var(--card-border, #444);
    border-radius: 8px;
    padding: 2rem;
    min-width: 200px;
    max-width: 300px;
    color: var(--text-color);
  }

  .modal-content h2 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: var(--text-color);
    font-size: 1.3rem;
  }

  .radio-group label {
    color: var(--text-color);
    font-size: 1.3rem;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin: 1rem 0;
  }

  .radio-group label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .modal-buttons {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }

  .start-button,
  .cancel-button {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1.3rem;
    cursor: pointer;
  }

  .start-button {
    background-color: #4caf50;
    color: white;
  }

  .cancel-button {
    background-color: #666;
    color: white;
  }

  .start-button:hover,
  .cancel-button:hover {
    opacity: 0.8;
  }
</style>

