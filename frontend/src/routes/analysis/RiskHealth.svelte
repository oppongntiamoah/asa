<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";

  let data = $state(null);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      data = await api.analysisRisk();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  function scoreColor(score) {
    if (score === null) return "text-gray-500";
    if (score >= 70) return "text-emerald-600";
    if (score >= 40) return "text-amber-600";
    return "text-red-600";
  }
</script>

<h1 class="text-xl font-semibold mb-6">Risk & Health</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  <div class="grid grid-cols-2 gap-4 mb-8">
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Health score</p>
      <p class="text-2xl font-semibold {scoreColor(data.health_score)}">{data.health_score ?? "—"}<span class="text-sm text-gray-400">/100</span></p>
    </div>
    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4">
      <p class="text-xs text-gray-500 mb-1">Diversification score</p>
      <p class="text-2xl font-semibold {scoreColor(data.diversification_score)}">
        {data.diversification_score === null ? "—" : Math.round(data.diversification_score)}<span class="text-sm text-gray-400">/100</span>
      </p>
    </div>
  </div>

  {#if data.largest_position}
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
      Largest position: <strong>{data.largest_position.instrument.ticker}</strong> at {data.largest_position.pct.toFixed(1)}% of your portfolio.
    </p>
  {/if}
  {#if data.largest_sector}
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-6">
      Largest sector: <strong>{data.largest_sector.sector}</strong> at {data.largest_sector.pct.toFixed(1)}% of your portfolio.
    </p>
  {/if}

  {#if data.warnings.length > 0}
    <h2 class="text-sm font-medium mb-3">Warnings</h2>
    <div class="space-y-2">
      {#each data.warnings as w}
        <p class="text-sm text-amber-800 bg-amber-50 dark:bg-amber-950 dark:text-amber-300 rounded-lg px-4 py-2">{w}</p>
      {/each}
    </div>
  {:else}
    <p class="text-sm text-gray-500">No concentration warnings right now.</p>
  {/if}
{/if}
