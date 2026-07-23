<script>
  import Router from "svelte-spa-router";
  import { onMount } from "svelte";
  import { user, checkAuth } from "./lib/auth.js";
  import { api } from "./lib/api.js";
  import "./lib/theme.js";
  import Sidebar from "./lib/Sidebar.svelte";
  import InstallPrompt from "./lib/InstallPrompt.svelte";
  import Landing from "./routes/Landing.svelte";
  import Login from "./routes/Login.svelte";
  import Dashboard from "./routes/Dashboard.svelte";
  import Holdings from "./routes/Holdings.svelte";
  import Ticker from "./routes/Ticker.svelte";

  let ready = $state(false);

  onMount(async () => {
    await api.csrf();
    await checkAuth();
    ready = true;
  });

  const publicRoutes = {
    "/": Landing,
    "/login": Login,
  };

  const appRoutes = {
    "/": Dashboard,
    "/holdings": Holdings,
    "/ticker/:ticker": Ticker,
  };
</script>

{#if !ready}
  <div class="min-h-screen flex items-center justify-center text-gray-500">Loading…</div>
{:else if !$user}
  <Router routes={publicRoutes} />
{:else}
  <Sidebar>
    <Router routes={appRoutes} />
  </Sidebar>
  <InstallPrompt />
{/if}
