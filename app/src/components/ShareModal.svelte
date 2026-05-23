<script>
  import { _, locale } from "svelte-i18n";

  let { open = $bindable(false), characters = [], statements = new Map() } =
    $props();
  let urlCopied = $state(false);
  let puzzleTextCopied = $state(false);
  let shareUrl = $derived(window.location.href);

  const puzzleShareText = $derived.by(() => {
    const intro = $_("app.intro");
    const names = characters.map((c) => c.shortName);
    const lines = [intro];

    for (const char of characters) {
      const statement = statements.get(char.name);
      if (!statement) continue;

      const statementText =
        $locale === "fr"
          ? statement.toFrench(names)
          : statement.toEnglish(names);

      lines.push(
        $_("modals.share.statementLine", {
          values: { name: char.shortName, statement: statementText },
        })
      );
    }

    return lines.join("\n\n");
  });

  function handleCopyUrl() {
    navigator.clipboard.writeText(shareUrl).then(() => {
      urlCopied = true;
      setTimeout(() => {
        urlCopied = false;
      }, 2000);
    });
  }

  function handleCopyPuzzleText() {
    navigator.clipboard.writeText(puzzleShareText).then(() => {
      puzzleTextCopied = true;
      setTimeout(() => {
        puzzleTextCopied = false;
      }, 2000);
    });
  }

  function handleCancel() {
    open = false;
  }
</script>

{#if open}
  <div
    class="modal-overlay"
    onclick={(e) => e.target === e.currentTarget && handleCancel()}
    role="button"
    tabindex="0"
    onkeydown={(e) => (e.key === "Escape" || e.key === "Enter" || e.key === " ") && handleCancel()}
  >
    <div class="modal-content" role="dialog" aria-modal="true" aria-label={$_("modals.share.title")}>
      <h2>{$_("modals.share.title")}</h2>
      <div class="url-container">
        <input type="text" readonly value={shareUrl} class="url-input" />
        <button class="copy-button" onclick={handleCopyUrl}>
          {urlCopied ? $_("modals.share.copied") : $_("modals.share.copy")}
        </button>
      </div>
      <button class="copy-puzzle-text-button" onclick={handleCopyPuzzleText}>
        {puzzleTextCopied
          ? $_("modals.share.copiedPuzzleText")
          : $_("modals.share.copyPuzzleText")}
      </button>
      <div class="modal-buttons">
        <button class="close-button" onclick={handleCancel}>{$_("modals.share.close")}</button>
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
    min-width: 300px;
    max-width: 600px;
    color: var(--text-color);
  }

  .modal-content h2 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: var(--text-color);
    font-size: 1.3rem;
  }

  .url-container {
    display: flex;
    gap: 0.5rem;
    margin: 1rem 0;
  }

  .url-input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid var(--card-border, #444);
    border-radius: 4px;
    background-color: var(--bg-color, #0a0a0a);
    color: var(--text-color);
    font-size: 1.3rem;
    font-family: inherit;
  }

  .copy-button {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1.3rem;
    cursor: pointer;
    background-color: #4caf50;
    color: white;
    white-space: nowrap;
  }

  .copy-button:hover {
    opacity: 0.8;
  }

  .copy-puzzle-text-button {
    display: block;
    width: 100%;
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1.3rem;
    cursor: pointer;
    background-color: #2196f3;
    color: white;
    margin-bottom: 0.5rem;
  }

  .copy-puzzle-text-button:hover {
    opacity: 0.8;
  }

  .modal-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1.5rem;
  }

  .close-button {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1.3rem;
    cursor: pointer;
    background-color: #666;
    color: white;
  }

  .close-button:hover {
    opacity: 0.8;
  }
</style>

