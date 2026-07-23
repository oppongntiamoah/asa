<script>
  import { onMount } from "svelte";
  import { link } from "svelte-spa-router";
  import { api } from "../lib/api.js";

  let snapshot = $state(null);

  onMount(async () => {
    try {
      snapshot = await api.marketSummary();
    } catch {
      snapshot = null;
    }
  });

  const pct = (v) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;

  const features = [
    {
      title: "Upload your broker statement",
      body: "IC Securities and Black Star Advisors PDFs, parsed automatically — review and confirm before anything is saved.",
      icon: "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z",
    },
    {
      title: "See your true portfolio value",
      body: "Equities, funds, fixed income, and cash in one view — with average-cost P&L, not just a broker's snapshot table.",
      icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
    },
    {
      title: "Install it like an app",
      body: "SikaTrack is a Progressive Web App — add it to your home screen, no app store required, works on any device.",
      icon: "M12 4v16m8-8H4",
    },
  ];
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-950">
  <header class="border-b border-gray-200 dark:border-gray-800">
    <div class="max-w-6xl mx-auto px-4 md:px-8 py-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold">S</span>
        <span class="font-bold text-lg">SikaTrack</span>
      </div>
      <div class="flex items-center gap-3">
        <a href="/login" use:link class="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">Log in</a>
        <a href="/accounts/signup/" class="text-sm font-medium bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700">Sign up</a>
      </div>
    </div>
  </header>

  <section class="max-w-6xl mx-auto px-4 md:px-8 py-16 md:py-24 grid md:grid-cols-2 gap-10 items-center">
    <div>
      <span class="inline-block text-xs font-semibold tracking-wide uppercase text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 rounded-full px-3 py-1 mb-4">
        Ghana Stock Exchange
      </span>
      <h1 class="text-4xl md:text-5xl font-bold tracking-tight mb-4">
        Your GSE portfolio,<br /><span class="text-emerald-600">finally tracked properly.</span>
      </h1>
      <p class="text-gray-600 dark:text-gray-400 text-lg mb-8 max-w-md">
        Upload your broker statement, and SikaTrack builds your real cost
        basis, allocation, and performance — across every asset class your
        broker actually holds for you.
      </p>
      <div class="flex flex-wrap items-center gap-3">
        <a href="/accounts/signup/" class="bg-emerald-600 text-white font-medium px-5 py-3 rounded-lg hover:bg-emerald-700">
          Get started free
        </a>
        <a href="/login" use:link class="font-medium px-5 py-3 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900">
          Log in
        </a>
      </div>
    </div>

    <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
      {#if snapshot}
        <div class="flex items-center justify-between mb-4">
          <p class="text-xs uppercase tracking-wide text-gray-500">GSE tracked instruments</p>
          {#if snapshot.as_of}
            <span class="text-xs text-gray-400">As of {snapshot.as_of}</span>
          {/if}
        </div>
        <p class="text-3xl font-bold mb-6">{snapshot.instrument_count}+</p>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-gray-500 mb-2">Top gainers</p>
            {#each snapshot.gainers as g}
              <div class="flex items-center justify-between text-sm py-1">
                <span class="font-medium">{g.instrument.ticker}</span>
                <span class="text-emerald-600">{pct(g.change_pct)}</span>
              </div>
            {:else}
              <p class="text-sm text-gray-400">—</p>
            {/each}
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-2">Top losers</p>
            {#each snapshot.losers as l}
              <div class="flex items-center justify-between text-sm py-1">
                <span class="font-medium">{l.instrument.ticker}</span>
                <span class="text-red-600">{pct(l.change_pct)}</span>
              </div>
            {:else}
              <p class="text-sm text-gray-400">—</p>
            {/each}
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-4">
          Daily closing prices from GSE's published data — not live quotes.
        </p>
      {:else}
        <p class="text-gray-500 text-sm">Market data loading…</p>
      {/if}
    </div>
  </section>

  <section class="max-w-6xl mx-auto px-4 md:px-8 pb-20">
    <div class="grid md:grid-cols-3 gap-6">
      {#each features as f}
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
          <div class="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d={f.icon} />
            </svg>
          </div>
          <h3 class="font-semibold mb-2">{f.title}</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">{f.body}</p>
        </div>
      {/each}
    </div>
  </section>

  <footer class="border-t border-gray-200 dark:border-gray-800">
    <div class="max-w-6xl mx-auto px-4 md:px-8 py-6 text-sm text-gray-500 flex items-center justify-between">
      <span>© {new Date().getFullYear()} SikaTrack</span>
      <span>Not affiliated with the Ghana Stock Exchange.</span>
    </div>
  </footer>
</div>
