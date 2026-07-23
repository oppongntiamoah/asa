<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../../lib/api.js";

  let items = $state([]);
  let loading = $state(true);
  let error = $state("");

  const statusStyle = {
    PENDING: "bg-gray-100 text-gray-600",
    PARSING: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
    NEEDS_REVIEW: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
    CONFIRMED: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
    FAILED: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
  };

  function open(s) {
    if (s.status === "NEEDS_REVIEW") push(`/statements/${s.id}/review`);
    else if (s.status === "CONFIRMED") push(`/statements/${s.id}/confirmed`);
    else push(`/statements/${s.id}`);
  }

  onMount(async () => {
    try {
      items = await api.statements();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<div class="flex items-center justify-between mb-6">
  <h1 class="text-xl font-semibold">Statements</h1>
  <button onclick={() => push("/statements/upload")} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700">
    Upload statement
  </button>
</div>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if items.length === 0}
  <div class="text-center py-16">
    <p class="text-gray-500 mb-6">No statements uploaded yet.</p>
    <button onclick={() => push("/statements/upload")} class="inline-block bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700">
      Upload your first statement
    </button>
  </div>
{:else}
  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-4 py-3 font-medium">Broker</th>
          <th class="px-4 py-3 font-medium">Uploaded</th>
          <th class="px-4 py-3 font-medium">Status</th>
        </tr>
      </thead>
      <tbody>
        {#each items as s}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50" onclick={() => open(s)}>
            <td class="px-4 py-3 font-medium">{s.broker_display}</td>
            <td class="px-4 py-3 text-gray-500">{new Date(s.uploaded_at).toLocaleString()}</td>
            <td class="px-4 py-3">
              <span class="text-xs font-medium px-2 py-0.5 rounded-full {statusStyle[s.status]}">{s.status.replace('_', ' ')}</span>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
