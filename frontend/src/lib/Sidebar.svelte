<script>
  import { link, router } from "svelte-spa-router";
  import { user, logout } from "./auth.js";
  import { theme, cycleTheme } from "./theme.js";

  let { children } = $props();

  const themeIcon = {
    light: "M12 3v1m0 16v1m9-9h-1M4 12H3m15.36 6.36l-.7-.7M6.34 6.34l-.7-.7m12.02 0l-.7.7M6.34 17.66l-.7.7M16 12a4 4 0 11-8 0 4 4 0 018 0z",
    dark: "M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z",
    system: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  };
  const themeLabel = { light: "Light", dark: "Dark", system: "Auto" };

  const links = [
    { href: "/", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
    { href: "/holdings", label: "Holdings", icon: "M9 17V7m6 10V11m-3 6V5M5 21h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z" },
  ];

  let mobileOpen = $state(false);

  async function handleLogout() {
    await logout();
    window.location.href = "/accounts/login/";
  }
</script>

<div class="min-h-screen flex">
  <aside class="hidden md:flex md:flex-col w-56 shrink-0 border-r border-gray-200 dark:border-gray-800 p-4">
    <div class="flex items-center gap-2 mb-8 px-2">
      <span class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold">S</span>
      <span class="font-bold">SikaTrack</span>
    </div>

    <nav class="flex-1 space-y-1">
      {#each links as l}
        <a
          href={l.href}
          use:link
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
            {router.location === l.href ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900'}"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d={l.icon} />
          </svg>
          {l.label}
        </a>
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
        onclick={handleLogout}
        class="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900"
      >
        Log out
      </button>
      <a href="/holdings/" class="block px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-900">
        More analysis (legacy pages)
      </a>
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
      <nav class="md:hidden border-b border-gray-200 dark:border-gray-800 px-4 py-2 space-y-1">
        {#each links as l}
          <a href={l.href} use:link onclick={() => (mobileOpen = false)} class="block px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400">
            {l.label}
          </a>
        {/each}
        <button onclick={cycleTheme} class="block w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400">
          Theme: {themeLabel[$theme]}
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
