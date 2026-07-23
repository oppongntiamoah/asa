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
  import Transactions from "./routes/Transactions.svelte";
  import TransactionForm from "./routes/TransactionForm.svelte";
  import TransactionAnalysis from "./routes/analysis/TransactionAnalysis.svelte";
  import CostBasis from "./routes/analysis/CostBasis.svelte";
  import SectorAnalysis from "./routes/analysis/SectorAnalysis.svelte";
  import Performance from "./routes/analysis/Performance.svelte";
  import RiskHealth from "./routes/analysis/RiskHealth.svelte";
  import Insights from "./routes/analysis/Insights.svelte";
  import CashFlow from "./routes/analysis/CashFlow.svelte";
  import TaxSummary from "./routes/analysis/TaxSummary.svelte";
  import Timeline from "./routes/analysis/Timeline.svelte";
  import Dividends from "./routes/Dividends.svelte";
  import Calendar from "./routes/Calendar.svelte";
  import Market from "./routes/Market.svelte";
  import Watchlist from "./routes/Watchlist.svelte";
  import StatementList from "./routes/statements/StatementList.svelte";
  import StatementUpload from "./routes/statements/Upload.svelte";
  import StatementStatus from "./routes/statements/Status.svelte";
  import StatementReview from "./routes/statements/Review.svelte";
  import StatementConfirmed from "./routes/statements/Confirmed.svelte";
  import Billing from "./routes/Billing.svelte";
  import Credits from "./routes/Credits.svelte";
  import Settings from "./routes/Settings.svelte";
  import Support from "./routes/Support.svelte";

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
    "/transactions": Transactions,
    "/transactions/add": TransactionForm,
    "/transactions/:id/edit": TransactionForm,
    "/analysis/transactions": TransactionAnalysis,
    "/analysis/cost-basis": CostBasis,
    "/analysis/sectors": SectorAnalysis,
    "/analysis/performance": Performance,
    "/analysis/risk": RiskHealth,
    "/analysis/insights": Insights,
    "/analysis/cash-flow": CashFlow,
    "/analysis/tax": TaxSummary,
    "/analysis/timeline": Timeline,
    "/dividends": Dividends,
    "/calendar": Calendar,
    "/market": Market,
    "/watchlist": Watchlist,
    "/statements": StatementList,
    "/statements/upload": StatementUpload,
    "/statements/:id/review": StatementReview,
    "/statements/:id/confirmed": StatementConfirmed,
    "/statements/:id": StatementStatus,
    "/billing": Billing,
    "/credits": Credits,
    "/settings": Settings,
    "/support": Support,
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
