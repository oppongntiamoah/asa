<script>
  import { onDestroy, onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../../lib/api.js";

  let { params } = $props();

  let statement = $state(null);
  let error = $state("");
  let interval;

  async function poll() {
    try {
      statement = await api.statement(params.id);
      if (statement.status === "NEEDS_REVIEW") {
        clearInterval(interval);
        push(`/statements/${params.id}/review`);
      } else if (statement.status === "CONFIRMED") {
        clearInterval(interval);
        push(`/statements/${params.id}/confirmed`);
      } else if (statement.status === "FAILED") {
        clearInterval(interval);
      }
    } catch (err) {
      error = err.message;
      clearInterval(interval);
    }
  }

  onMount(() => {
    poll();
    interval = setInterval(poll, 2000);
  });
  onDestroy(() => clearInterval(interval));
</script>

<h1 class="text-xl font-semibold mb-6">Statement processing</h1>

{#if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else if !statement}
  <p class="text-gray-500">Loading…</p>
{:else if statement.status === "FAILED"}
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg">
    <p class="text-red-700 dark:text-red-300 mb-2">Couldn't process this statement.</p>
    <p class="text-sm text-gray-600 dark:text-gray-400">{statement.parse_error}</p>
    <button onclick={() => push("/statements/upload")} class="mt-4 bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700">
      Try another file
    </button>
  </div>
{:else}
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg flex items-center gap-3">
    <div class="w-5 h-5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
    <p class="text-sm text-gray-600 dark:text-gray-400">Reading your statement… this usually takes under a minute.</p>
  </div>
{/if}
