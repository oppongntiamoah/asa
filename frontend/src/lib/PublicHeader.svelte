<script>
  import { link, router } from "svelte-spa-router";

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/news", label: "News" },
    { href: "/faq", label: "FAQ" },
    { href: "/contact", label: "Contact" },
  ];
</script>

<header class="border-b border-gray-200 dark:border-gray-800">
  <div class="max-w-6xl mx-auto px-4 md:px-8 py-4 flex items-center justify-between gap-4">
    <a href="/" use:link class="flex items-center gap-2 shrink-0">
      <span class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold">S</span>
      <span class="font-bold text-lg">SikaTrack</span>
    </a>

    <nav class="hidden sm:flex items-center gap-6">
      {#each navLinks as l}
        <a
          href={l.href}
          use:link
          class="text-sm font-medium {router.location === l.href ? 'text-emerald-700 dark:text-emerald-400' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'}"
        >
          {l.label}
        </a>
      {/each}
    </nav>

    <div class="flex items-center gap-3 shrink-0">
      <a href="/login" use:link class="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">Log in</a>
      <a href="/accounts/signup/" class="text-sm font-medium bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700">Sign up</a>
    </div>
  </div>
  <nav class="sm:hidden flex items-center gap-4 px-4 pb-3 overflow-x-auto">
    {#each navLinks as l}
      <a
        href={l.href}
        use:link
        class="text-sm font-medium whitespace-nowrap {router.location === l.href ? 'text-emerald-700 dark:text-emerald-400' : 'text-gray-600 dark:text-gray-400'}"
      >
        {l.label}
      </a>
    {/each}
  </nav>
</header>
