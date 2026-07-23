<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";

  let insights = $state([]);
  let loading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      const data = await api.analysisInsights();
      insights = data.insights;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-2">Insights</h1>
<p class="text-sm text-gray-500 mb-6">Plain observations generated from your own data — not AI-generated.</p>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if insights.length === 0}
  <p class="text-gray-500">Not enough data yet for insights.</p>
{:else}
  <div class="space-y-3">
    {#each insights as insight}
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 text-sm flex items-start gap-3">
        <span class="w-6 h-6 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center text-xs shrink-0">i</span>
        <span class={insight.includes("GHS") ? "money-mask" : ""}>{insight}</span>
      </div>
    {/each}
  </div>
{/if}
