<script>
  import { onMount } from "svelte";
  import { api } from "../../lib/api.js";
  import { money } from "../../lib/format.js";

  let events = $state([]);
  let loading = $state(true);
  let error = $state("");

  const kindStyle = {
    BUY: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
    SELL: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
    DIVIDEND: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  };

  onMount(async () => {
    try {
      events = await api.analysisTimeline();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<h1 class="text-xl font-semibold mb-6">Timeline</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if events.length === 0}
  <p class="text-gray-500">No activity yet.</p>
{:else}
  <div class="space-y-2">
    {#each events as e}
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex items-center justify-between text-sm">
        <div class="flex items-center gap-3">
          <span class="text-xs font-medium px-2 py-0.5 rounded-full {kindStyle[e.kind] || 'bg-gray-100 text-gray-600'}">{e.kind}</span>
          <span>{e.description}</span>
        </div>
        <div class="text-right">
          <p>{money(e.amount)}</p>
          <p class="text-xs text-gray-400">{e.date}</p>
        </div>
      </div>
    {/each}
  </div>
{/if}
