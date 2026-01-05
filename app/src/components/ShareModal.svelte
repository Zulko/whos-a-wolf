<script>
  let { open = $bindable(false) } = $props();
  let copied = $state(false);
  let shareUrl = $derived(window.location.href);

  function handleCopy() {
    navigator.clipboard.writeText(shareUrl).then(() => {
      copied = true;
      setTimeout(() => {
        copied = false;
      }, 2000);
    });
  }

  function handleCancel() {
    open = false;
  }
</script>

{#if open}
  <div class="modal-overlay" on:click={handleCancel}>
    <div class="modal-content" on:click={(e) => e.stopPropagation()}>
      <h2>Share this puzzle</h2>
      <div class="url-container">
        <input type="text" readonly value={shareUrl} class="url-input" />
        <button class="copy-button" on:click={handleCopy}>
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div class="modal-buttons">
        <button class="close-button" on:click={handleCancel}>Close</button>
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

