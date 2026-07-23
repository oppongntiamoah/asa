<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api, ApiError } from "../lib/api.js";

  let { params = {} } = $props();
  const isEdit = $derived(!!params.id);

  let instruments = $state([]);
  let form = $state({
    instrument_id: "",
    transaction_type: "BUY",
    quantity: "",
    price_per_share: "",
    fees: "0",
    trade_date: new Date().toISOString().slice(0, 10),
    broker: "",
    notes: "",
  });
  let sellWarning = $state("");
  let error = $state("");
  let loading = $state(true);
  let submitting = $state(false);

  async function loadInstruments() {
    const { rows } = await api.marketList();
    instruments = rows.map((r) => r.instrument).sort((a, b) => a.ticker.localeCompare(b.ticker));
  }

  onMount(async () => {
    try {
      await loadInstruments();
      if (isEdit) {
        const txns = await api.transactions();
        const existing = txns.find((t) => String(t.id) === String(params.id));
        if (!existing) {
          error = "Transaction not found.";
        } else {
          form = {
            instrument_id: existing.instrument.id,
            transaction_type: existing.transaction_type,
            quantity: existing.quantity,
            price_per_share: existing.price_per_share,
            fees: existing.fees,
            trade_date: existing.trade_date,
            broker: existing.broker,
            notes: existing.notes,
          };
        }
      }
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  async function checkSell() {
    sellWarning = "";
    if (form.transaction_type !== "SELL" || !form.instrument_id || !form.quantity) return;
    try {
      const result = await api.checkSellQuantity(form.instrument_id, form.quantity, isEdit ? params.id : null);
      if (!result.ok) sellWarning = result.message;
    } catch {
      // non-critical; server-side validation on submit still applies
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    error = "";
    submitting = true;
    try {
      if (isEdit) {
        await api.updateTransaction(params.id, form);
      } else {
        await api.createTransaction(form);
      }
      push("/transactions");
    } catch (err) {
      error = err instanceof ApiError ? err.message : "Something went wrong.";
    } finally {
      submitting = false;
    }
  }
</script>

<h1 class="text-xl font-semibold mb-6">{isEdit ? "Edit" : "Add"} transaction</h1>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else}
  <form onsubmit={handleSubmit} class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 max-w-lg space-y-4">
    {#if error}
      <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2">{error}</p>
    {/if}

    <div>
      <label for="instrument" class="block text-sm font-medium mb-1">Instrument</label>
      <select id="instrument" bind:value={form.instrument_id} onchange={checkSell} required class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm">
        <option value="" disabled>Select…</option>
        {#each instruments as inst}
          <option value={inst.id}>{inst.ticker} — {inst.name}</option>
        {/each}
      </select>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label for="type" class="block text-sm font-medium mb-1">Type</label>
        <select id="type" bind:value={form.transaction_type} onchange={checkSell} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm">
          <option value="BUY">Buy</option>
          <option value="SELL">Sell</option>
        </select>
      </div>
      <div>
        <label for="date" class="block text-sm font-medium mb-1">Trade date</label>
        <input id="date" type="date" bind:value={form.trade_date} required class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label for="qty" class="block text-sm font-medium mb-1">Quantity</label>
        <input id="qty" type="number" step="0.0001" min="0" bind:value={form.quantity} oninput={checkSell} required class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
        {#if sellWarning}
          <p class="text-xs text-red-600 mt-1">{sellWarning}</p>
        {/if}
      </div>
      <div>
        <label for="price" class="block text-sm font-medium mb-1">Price per share</label>
        <input id="price" type="number" step="0.0001" min="0" bind:value={form.price_per_share} required class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label for="fees" class="block text-sm font-medium mb-1">Fees</label>
        <input id="fees" type="number" step="0.01" min="0" bind:value={form.fees} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
      </div>
      <div>
        <label for="broker" class="block text-sm font-medium mb-1">Broker (optional)</label>
        <input id="broker" type="text" bind:value={form.broker} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
      </div>
    </div>

    <div>
      <label for="notes" class="block text-sm font-medium mb-1">Notes (optional)</label>
      <input id="notes" type="text" bind:value={form.notes} class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm" />
    </div>

    <div class="flex gap-3">
      <button type="submit" disabled={submitting} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
        {submitting ? "Saving…" : isEdit ? "Save changes" : "Add transaction"}
      </button>
      <button type="button" onclick={() => push("/transactions")} class="text-sm font-medium px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900">
        Cancel
      </button>
    </div>
  </form>
{/if}
