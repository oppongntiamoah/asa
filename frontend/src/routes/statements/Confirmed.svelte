<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../../lib/api.js";

  let { params } = $props();

  let statement = $state(null);
  let error = $state("");

  onMount(async () => {
    try {
      statement = await api.statement(params.id);
    } catch (err) {
      error = err.message;
    }
  });
</script>

<div class="max-w-lg mx-auto text-center py-16">
  {#if error}
    <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
  {:else}
    <div class="w-14 h-14 rounded-full bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center mx-auto mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-7 h-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <h1 class="text-xl font-semibold mb-2">Statement confirmed</h1>
    <p class="text-gray-500 mb-6">Your transactions have been added to your portfolio.</p>
    <div class="flex justify-center gap-3">
      <button onclick={() => push("/")} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700">
        Go to dashboard
      </button>
      <button onclick={() => push("/transactions")} class="text-sm font-medium px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900">
        View transactions
      </button>
    </div>
  {/if}
</div>
