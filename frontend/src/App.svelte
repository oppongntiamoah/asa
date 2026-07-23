<script>
  import Router from "svelte-spa-router";
  import { onMount } from "svelte";
  import { user, checkAuth } from "./lib/auth.js";
  import { api } from "./lib/api.js";
  import Sidebar from "./lib/Sidebar.svelte";
  import Login from "./routes/Login.svelte";
  import Dashboard from "./routes/Dashboard.svelte";
  import Holdings from "./routes/Holdings.svelte";

  let ready = $state(false);

  onMount(async () => {
    await api.csrf();
    await checkAuth();
    ready = true;
  });

  const routes = {
    "/": Dashboard,
    "/holdings": Holdings,
  };
</script>

{#if !ready}
  <div class="min-h-screen flex items-center justify-center text-gray-500">Loading…</div>
{:else if !$user}
  <Login />
{:else}
  <Sidebar>
    <Router {routes} />
  </Sidebar>
{/if}
