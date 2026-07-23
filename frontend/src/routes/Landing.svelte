<script>
  import { onMount } from "svelte";
  import { link } from "svelte-spa-router";
  import { api } from "../lib/api.js";
  import PublicHeader from "../lib/PublicHeader.svelte";
  import PublicFooter from "../lib/PublicFooter.svelte";

  let snapshot = $state(null);
  let latestNews = $state([]);

  onMount(async () => {
    try {
      snapshot = await api.marketSummary();
    } catch {
      snapshot = null;
    }
    try {
      const data = await api.news();
      latestNews = data.articles.slice(0, 3);
    } catch {
      latestNews = [];
    }
  });

  const pct = (v) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
  const formatDate = (iso) => new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

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
  <PublicHeader />

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

  {#if latestNews.length > 0}
    <section class="max-w-6xl mx-auto px-4 md:px-8 pb-20">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold">Market News</h2>
        <a href="/news" use:link class="text-sm text-emerald-700 dark:text-emerald-400 hover:underline">All news →</a>
      </div>
      <div class="grid md:grid-cols-3 gap-5">
        {#each latestNews as a}
          <a
            href="/news/{a.slug}"
            use:link
            class="block bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden hover:border-emerald-300 dark:hover:border-emerald-800 transition-colors"
          >
            {#if a.image}
              <img src={a.image} alt="" class="w-full h-32 object-cover" />
            {:else}
              <div class="w-full h-32 bg-gradient-to-br from-emerald-50 to-gray-100 dark:from-emerald-950 dark:to-gray-800"></div>
            {/if}
            <div class="p-4">
              <span class="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">{a.category_display}</span>
              <h3 class="font-semibold mt-1 mb-1 leading-snug line-clamp-2">{a.title}</h3>
              <p class="text-xs text-gray-400">{formatDate(a.published_at)}</p>
            </div>
          </a>
        {/each}
      </div>
    </section>
  {/if}

  <PublicFooter />
</div>
