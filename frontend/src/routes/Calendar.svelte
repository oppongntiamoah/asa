<script>
  import { onMount } from "svelte";
  import { push } from "svelte-spa-router";
  import { api } from "../lib/api.js";

  const today = new Date();
  let year = $state(today.getFullYear());
  let month = $state(today.getMonth() + 1);
  let events = $state([]);
  let loading = $state(true);
  let error = $state("");

  const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];

  async function load() {
    loading = true;
    try {
      const data = await api.calendar(year, month);
      events = data.events;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function prevMonth() {
    if (month === 1) { month = 12; year -= 1; } else { month -= 1; }
    load();
  }
  function nextMonth() {
    if (month === 12) { month = 1; year += 1; } else { month += 1; }
    load();
  }

  const daysInMonth = $derived(new Date(year, month, 0).getDate());
  const firstWeekday = $derived((new Date(year, month - 1, 1).getDay() + 6) % 7); // Monday=0
  const eventsByDay = $derived.by(() => {
    const map = {};
    for (const e of events) {
      const day = Number(e.date.split("-")[2]);
      (map[day] ||= []).push(e);
    }
    return map;
  });

  onMount(load);
</script>

<div class="flex items-center justify-between mb-6">
  <h1 class="text-xl font-semibold">Calendar</h1>
  <div class="flex items-center gap-3">
    <button onclick={prevMonth} class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900" aria-label="Previous month">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
    </button>
    <span class="text-sm font-medium w-32 text-center">{monthNames[month - 1]} {year}</span>
    <button onclick={nextMonth} class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900" aria-label="Next month">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
    </button>
  </div>
</div>

{#if loading}
  <p class="text-gray-500">Loading…</p>
{:else if error}
  <p class="text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300 rounded-lg px-4 py-3">{error}</p>
{:else}
  <div class="grid grid-cols-7 gap-1 mb-8 text-xs">
    {#each ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"] as d}
      <div class="text-center text-gray-500 font-medium py-1">{d}</div>
    {/each}
    {#each Array(firstWeekday) as _}
      <div></div>
    {/each}
    {#each Array(daysInMonth) as _, i}
      {@const day = i + 1}
      <div class="min-h-16 border border-gray-100 dark:border-gray-800 rounded-lg p-1">
        <p class="text-gray-400">{day}</p>
        {#each eventsByDay[day] || [] as e}
          <button onclick={() => push(`/ticker/${e.instrument.ticker}`)} class="block w-full text-left text-[10px] truncate text-emerald-700 dark:text-emerald-400 hover:underline">
            {e.instrument.ticker}
          </button>
        {/each}
      </div>
    {/each}
  </div>

  <h2 class="text-sm font-medium mb-3">Events this month</h2>
  {#if events.length === 0}
    <p class="text-gray-500 text-sm">No corporate actions or dividends this month for your holdings/watchlist.</p>
  {:else}
    <div class="space-y-2">
      {#each events as e}
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 flex items-center justify-between text-sm">
          <span>{e.title}</span>
          <span class="text-gray-500">{e.date}</span>
        </div>
      {/each}
    </div>
  {/if}
{/if}
