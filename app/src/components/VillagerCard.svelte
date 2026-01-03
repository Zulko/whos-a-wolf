<script>
  import { getDefaultCharacters } from "../lib/characters.js";

  let {
    villagerName,
    statement,
    suspicion,
    isSolved,
    onSuspicionChange,
    numVillagers = 6,
  } = $props();
  let imageError = $state(false);
  let isPulsing = $state(false);

  const characters = $derived(getDefaultCharacters(numVillagers));
  const villager = $derived(characters.find((c) => c.name === villagerName));
  const shortName = $derived(villager ? villager.shortName : villagerName);

  function getImagePath() {
    const baseUrl = import.meta.env.MODE === "production" ? "/whos-a-wolf" : "";
    const basePath = `${baseUrl}/images/characters`;
    if (isSolved) {
      if (suspicion === "werewolf") {
        return `${basePath}/${shortName}_werewolf.jpg`;
      } else if (suspicion === "shill") {
        return `${basePath}/${shortName}_shill.jpg`;
      } else {
        return `${basePath}/${shortName}_happy.jpg`;
      }
    } else {
      if (suspicion === "truthful") {
        return `${basePath}/${shortName}_neutral.jpg`;
      } else if (suspicion === "shill") {
        return `${basePath}/${shortName}_angry.jpg`;
      } else {
        return `${basePath}/${shortName}_furious.jpg`;
      }
    }
  }

  function getSuspicionColor() {
    if (suspicion === "truthful") {
      return "#4caf50"; // Green
    } else if (suspicion === "werewolf") {
      return "#1a1a1a"; // Dark gray/black
    } else {
      return "#f44336"; // Red
    }
  }

  function getSuspicionTextColor() {
    // Ensure text is always readable
    if (suspicion === "werewolf") {
      return "#ffffff"; // White text on dark background
    }
    return "#ffffff"; // White text for all labels
  }

  function cycleSuspicion(event) {
    isPulsing = true;
    setTimeout(() => (isPulsing = false), 150);
    if (suspicion === "truthful") {
      onSuspicionChange("shill");
    } else if (suspicion === "shill") {
      onSuspicionChange("werewolf");
    } else {
      onSuspicionChange("truthful");
    }
    // Remove focus after clicking to avoid persistent selected state
    if (event?.currentTarget) {
      event.currentTarget.blur();
    }
  }

  function getSuspicionText() {
    return suspicion.charAt(0).toUpperCase() + suspicion.slice(1);
  }
</script>

<div
  class="villager-card"
  class:pulse={isPulsing}
  onclick={cycleSuspicion}
  role="button"
  tabindex="0"
  onkeydown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      cycleSuspicion(e);
    }
  }}
>
  <div class="villager-picture">
    {#if !imageError}
      <img
        src={getImagePath()}
        alt={shortName}
        onerror={() => (imageError = true)}
      />
    {:else}
      <div class="placeholder">
        <div class="placeholder-content">
          {shortName.charAt(0)}
        </div>
      </div>
    {/if}
  </div>

  <div class="card-content">
    <div class="top-labels">
      <div class="name-label">{villagerName}</div>
      <div
        class="suspicion-label"
        style="background-color: {getSuspicionColor()}; color: {getSuspicionTextColor()};"
      >
        {getSuspicionText()}
      </div>
    </div>
    <div class="statement">
      {statement ? statement.toEnglish(characters.map((c) => c.shortName)) : ""}
    </div>
  </div>
</div>

<style>
  .villager-card {
    display: flex;
    flex-direction: row;
    gap: 0;
    border: 2px solid var(--card-border, #333);
    border-radius: 0;
    background-color: var(--card-bg, rgba(255, 255, 255, 0.05));
    min-width: 0;
    width: 100%;
    max-width: 500px;
    position: relative;
    overflow: visible;
    height: 80px;
    cursor: pointer;
    transition: box-shadow 0.2s ease;
  }

  .villager-card:hover {
    box-shadow: 0 0 0 2px var(--card-border, #333);
  }

  .villager-card:focus-visible {
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }

  .villager-card.pulse {
    animation: pulse 0.15s ease-out;
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.02);
    }
    100% {
      transform: scale(1);
    }
  }

  .villager-picture {
    width: 80px;
    height: 80px;
    border-radius: 0;
    overflow: hidden;
    background-color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    margin: 0;
    flex-shrink: 0;
  }

  .villager-picture img {
    width: 90%;
    height: 90%;
    object-fit: cover;
    display: block;
  }

  .placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--card-border, #444);
  }

  .placeholder-content {
    font-size: 3rem;
    color: var(--text-secondary, #888);
  }

  .card-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    padding: 0.5rem;
    padding-top: 0.25rem;
    position: relative;
    height: 80px;
    box-sizing: border-box;
  }

  .top-labels {
    display: flex;
    flex-direction: row;
    gap: 0.5rem;
    align-items: flex-start;
    margin-bottom: 0.25rem;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    z-index: 5;
    margin-left: 0.5rem;
    padding-right: 0.5rem;
  }

  .name-label {
    padding: 0rem 0.4rem;
    background-color: #f5f5dc; /* Beige */
    border: 1px solid #d4c5a9; /* Subtle border */
    border-radius: 2px;
    font-size: 1.3rem;
    font-weight: normal;
    color: #2c2c2c; /* Blackish */
    white-space: nowrap;
    position: relative;
    top: -12px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1); /* Subtle shadow for paper effect */
  }

  .suspicion-label {
    padding: 0rem 0.4rem;
    border: 2px solid currentColor;
    border-radius: 4px;
    font-size: 1.3rem;
    font-weight: bold;
    white-space: nowrap;
    position: relative;
    top: -12px;
  }

  .statement {
    text-align: left;
    font-style: italic;
    color: var(--text-secondary, #ddd);
    line-height: 1.1rem;
    font-size: 1.3rem;
    margin: 0;
    margin-top: 0.5rem;
    padding: 0;
    word-wrap: break-word;
    overflow-wrap: break-word;
    flex: 1;
    display: flex;
    align-items: center;
    padding-left: 0.25rem;
  }

  @media (max-width: 600px) {
    .villager-card {
      height: 65px;
    }

    .villager-picture {
      width: 65px;
      height: 65px;
    }

    .card-content {
      height: 65px;
    }

    .name-label {
      font-size: 1rem;
    }

    .suspicion-label {
      font-size: 1rem;
    }

    .statement {
      font-size: 1rem;
    }
  }
</style>
