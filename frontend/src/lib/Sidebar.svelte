<script>
  import { link, router } from "svelte-spa-router";
  import { user, logout } from "./auth.js";
  import { theme, cycleTheme } from "./theme.js";
  import { privacyMode, togglePrivacy } from "./privacy.js";

  let { children } = $props();

  const themeIcon = {
    light: "M12 3v1m0 16v1m9-9h-1M4 12H3m15.36 6.36l-.7-.7M6.34 6.34l-.7-.7m12.02 0l-.7.7M6.34 17.66l-.7.7M16 12a4 4 0 11-8 0 4 4 0 018 0z",
    dark: "M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z",
    system: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  };
  const themeLabel = { light: "Light", dark: "Dark", system: "Auto" };

  const groups = [
    {
      label: "Portfolio",
      links: [
        { href: "/", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
        { href: "/holdings", label: "Holdings", icon: "M9 17V7m6 10V11m-3 6V5M5 21h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z" },
        { href: "/transactions", label: "Transactions", icon: "M8 7h12m0 0l-4-4m4 4l-4 4M16 17H4m0 0l4 4m-4-4l4-4" },
        { href: "/statements", label: "Statements", icon: "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" },
      ],
    },
    {
      label: "Analysis",
      links: [
        { href: "/analysis/performance", label: "Performance", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
        { href: "/analysis/cost-basis", label: "Cost Basis", icon: "M9 7h6m0 10v-3m-3 3v-6m-3 6v-9m-2 9V6a2 2 0 012-2h6a2 2 0 012 2v12H5z" },
        { href: "/analysis/sectors", label: "Sector Analysis", icon: "M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" },
        { href: "/analysis/transactions", label: "Transaction Analysis", icon: "M8 7h12m0 0l-4-4m4 4l-4 4M16 17H4m0 0l4 4m-4-4l4-4" },
        { href: "/analysis/risk", label: "Risk & Health", icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" },
        { href: "/analysis/insights", label: "Insights", icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" },
        { href: "/analysis/cash-flow", label: "Cash Flow", icon: "M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2z" },
        { href: "/analysis/tax", label: "Tax Summary", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
        { href: "/analysis/timeline", label: "Timeline", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
      ],
    },
    {
      label: "Income",
      links: [
        { href: "/dividends", label: "Dividends", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" },
      ],
    },
    {
      label: "Discover",
      links: [
        { href: "/market", label: "Market", icon: "M3 3v18h18M18.7 8l-5.1 5.2-2.8-2.7L7 14.3" },
        { href: "/watchlist", label: "Watchlist", icon: "M12 4.5C7 4.5 2.7 7.6 1 12c1.7 4.4 6 7.5 11 7.5s9.3-3.1 11-7.5c-1.7-4.4-6-7.5-11-7.5zM12 15a3 3 0 100-6 3 3 0 000 6z" },
        { href: "/calendar", label: "Calendar", icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" },
      ],
    },
    {
      label: "Account",
      links: [
        { href: "/billing", label: "Pricing", icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
        { href: "/credits", label: "My Credits", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" },
        { href: "/settings", label: "Settings", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" },
        { href: "/support", label: "Support", icon: "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
      ],
    },
  ];

  let mobileOpen = $state(false);

  async function handleLogout() {
    await logout();
    window.location.href = "/accounts/login/";
  }
</script>

<div class="min-h-screen flex">
  <aside class="hidden md:flex md:flex-col w-60 shrink-0 border-r border-gray-200 dark:border-gray-800 p-4 h-screen sticky top-0 overflow-y-auto">
    <div class="flex items-center gap-2 mb-6 px-2">
      <span class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold">S</span>
      <span class="font-bold">SikaTrack</span>
    </div>

    <nav class="flex-1 space-y-5">
      {#each groups as group}
        <div>
          <p class="px-3 text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">{group.label}</p>
          <div class="space-y-0.5">
            {#each group.links as l}
              <a
                href={l.href}
                use:link
                class="flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium
                  {router.location === l.href ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900'}"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d={l.icon} />
                </svg>
                {l.label}
              </a>
            {/each}
          </div>
        </div>
      {/each}
    </nav>

    <div class="border-t border-gray-200 dark:border-gray-800 pt-4 mt-4">
      {#if $user}
        <p class="px-3 text-sm text-gray-500 mb-2 truncate">{$user.first_name || $user.username}</p>
      {/if}
      <button
        onclick={cycleTheme}
        class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900"
      >
        <span class="flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d={themeIcon[$theme]} />
          </svg>
          Theme
        </span>
        <span class="text-xs text-gray-400">{themeLabel[$theme]}</span>
      </button>
      <button
        onclick={togglePrivacy}
        class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900"
      >
        <span class="flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            {#if $privacyMode}
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
            {:else}
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            {/if}
          </svg>
          Hide amounts
        </span>
        <span class="text-xs text-gray-400">{$privacyMode ? "On" : "Off"}</span>
      </button>
      <button
        onclick={handleLogout}
        class="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900"
      >
        Log out
      </button>
    </div>
  </aside>

  <div class="flex-1 min-w-0">
    <header class="md:hidden flex items-center justify-between border-b border-gray-200 dark:border-gray-800 px-4 py-3">
      <div class="flex items-center gap-2">
        <span class="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-sm">S</span>
        <span class="font-bold">SikaTrack</span>
      </div>
      <button onclick={() => (mobileOpen = !mobileOpen)} aria-label="Menu" class="p-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </header>

    {#if mobileOpen}
      <nav class="md:hidden border-b border-gray-200 dark:border-gray-800 px-4 py-2 max-h-[70vh] overflow-y-auto">
        {#each groups as group}
          <p class="px-3 pt-3 text-xs font-semibold uppercase tracking-wide text-gray-400">{group.label}</p>
          {#each group.links as l}
            <a href={l.href} use:link onclick={() => (mobileOpen = false)} class="block px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400">
              {l.label}
            </a>
          {/each}
        {/each}
        <button onclick={cycleTheme} class="block w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400">
          Theme: {themeLabel[$theme]}
        </button>
        <button onclick={togglePrivacy} class="block w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400">
          Hide amounts: {$privacyMode ? "On" : "Off"}
        </button>
        <button onclick={handleLogout} class="block w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400">
          Log out
        </button>
      </nav>
    {/if}

    <main class="p-4 md:p-8 max-w-6xl mx-auto">
      {@render children()}
    </main>
  </div>
</div>
