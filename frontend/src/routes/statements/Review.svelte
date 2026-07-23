<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api, ApiError } from "../../lib/api.js";

  let { params } = $props();

  let statement = $state(null);
  let rows = $state([]);
  let instruments = $state([]);
  let loading = $state(true);
  let error = $state("");
  let confirming = $state(false);
  let rowErrors = $state({});
  let savingRow = $state(null);

  async function load() {
    loading = true;
    try {
      const [reviewData, marketData] = await Promise.all([api.statementRows(params.id), api.marketList()]);
      statement = reviewData.statement;
      rows = reviewData.rows;
      instruments = marketData.rows.map((r) => r.instrument).sort((a, b) => a.ticker.localeCompare(b.ticker));
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function saveRow(row, patch) {
    savingRow = row.id;
    try {
      const updated = await api.updateStatementRow(params.id, row.id, patch);
      rows = rows.map((r) => (r.id === row.id ? updated : r));
    } catch (err) {
      error = err.message;
    } finally {
      savingRow = null;
    }
  }

  const includedCount = $derived(rows.filter((r) => !r.is_excluded).length);

  async function confirm() {
    confirming = true;
    error = "";
    rowErrors = {};
    try {
      await api.confirmStatement(params.id);
      push(`/statements/${params.id}/confirmed`);
    } catch (err) {
      if (err instanceof ApiError && err.body?.errors?.rows) {
        rowErrors = err.body.errors.rows;
      }
      error = err instanceof ApiError ? err.message : "Couldn't confirm.";
    } finally {
      confirming = false;
    }
  }

  onMount(load);
</script>

<h1 class="text-xl font-semibold mb-2">Review statement</h1>
<p class="text-sm text-gray-500 mb-6">
  Check each row before confirming — nothing is added to your portfolio until you confirm.
</p>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error && rows.length === 0}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  {#if error}
    <p class="text-sm text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-3 py-2 mb-4">{error}</p>
  {/if}

  <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl mb-4">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-200 dark:border-gray-800 text-left text-gray-500">
          <th class="px-3 py-3 font-medium">Raw text</th>
          <th class="px-3 py-3 font-medium">Instrument</th>
          <th class="px-3 py-3 font-medium">Type</th>
          <th class="px-3 py-3 font-medium">Qty</th>
          <th class="px-3 py-3 font-medium">Price</th>
          <th class="px-3 py-3 font-medium">Date</th>
          <th class="px-3 py-3 font-medium">Exclude</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr class="border-b border-gray-100 dark:border-gray-800 last:border-0 {row.is_excluded ? 'opacity-50' : ''}">
            <td class="px-3 py-2 text-xs text-gray-500 max-w-32 truncate" title={row.raw_ticker_text}>{row.raw_ticker_text}</td>
            <td class="px-3 py-2">
              <select
                value={row.matched_instrument?.id || ""}
                onchange={(e) => saveRow(row, { matched_instrument_id: e.target.value || null })}
                disabled={row.is_excluded}
                class="text-xs rounded border-gray-300 dark:border-gray-700 bg-transparent"
              >
                <option value="">—</option>
                {#each instruments as inst}
                  <option value={inst.id}>{inst.ticker}</option>
                {/each}
              </select>
            </td>
            <td class="px-3 py-2">
              <select
                value={row.transaction_type}
                onchange={(e) => saveRow(row, { transaction_type: e.target.value })}
                disabled={row.is_excluded}
                class="text-xs rounded border-gray-300 dark:border-gray-700 bg-transparent"
              >
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
              </select>
            </td>
            <td class="px-3 py-2">
              <input
                type="number" step="0.0001" value={row.quantity} disabled={row.is_excluded}
                onblur={(e) => saveRow(row, { quantity: e.target.value })}
                class="text-xs rounded border-gray-300 dark:border-gray-700 bg-transparent w-20"
              />
            </td>
            <td class="px-3 py-2">
              <input
                type="number" step="0.0001" value={row.price_per_share} disabled={row.is_excluded}
                onblur={(e) => saveRow(row, { price_per_share: e.target.value })}
                class="text-xs rounded border-gray-300 dark:border-gray-700 bg-transparent w-20"
              />
            </td>
            <td class="px-3 py-2">
              <input
                type="date" value={row.trade_date} disabled={row.is_excluded}
                onblur={(e) => saveRow(row, { trade_date: e.target.value })}
                class="text-xs rounded border-gray-300 dark:border-gray-700 bg-transparent"
              />
            </td>
            <td class="px-3 py-2 text-center">
              <input
                type="checkbox" checked={row.is_excluded}
                onchange={(e) => saveRow(row, { is_excluded: e.target.checked })}
              />
            </td>
          </tr>
          {#if rowErrors[row.id]}
            <tr><td colspan="7" class="px-3 pb-2 text-xs text-red-600">{rowErrors[row.id]}</td></tr>
          {/if}
        {/each}
      </tbody>
    </table>
  </div>

  <div class="flex items-center gap-4">
    <button onclick={confirm} disabled={confirming || includedCount === 0} class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
      {confirming ? "Confirming…" : `Confirm ${includedCount} transaction${includedCount === 1 ? "" : "s"}`}
    </button>
    <span class="text-xs text-gray-400">{savingRow ? "Saving…" : ""}</span>
  </div>
{/if}
