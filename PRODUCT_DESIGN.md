# SikaTrack — GSE Retail Investor Platform

**Product Design Document — MVP v1**
*"Sika" is Twi for money/gold. Working name only — rename freely before launch (check GSE/SEC-Ghana trademark and domain availability first).*

Prepared for: solo Django developer, existing GSE-focused Telegram audience, 6–8 week MVP runway.

---

## Table of Contents

1. [Product Requirements Document](#1-product-requirements-document)
2. [System Architecture](#2-system-architecture)
3. [Data Model](#3-data-model)
4. [Statement Parsing Design](#4-statement-parsing-design)
5. [Alert Engine Design](#5-alert-engine-design)
6. [Monetization Design](#6-monetization-design)
7. [UI/UX Specification](#7-uiux-specification)
8. [Security & Compliance](#8-security--compliance)
9. [MVP Build Plan](#9-mvp-build-plan-6-8-weeks)
10. [Validation Plan](#10-validation-plan)

---

## 1. Product Requirements Document

### 1.1 Problem statement

Ghanaian retail investors on the GSE have no affordable way to see their real portfolio performance across brokers, get timely corporate-action alerts, or track a stock without manually re-reading PDF statements and scattered broker/GSE announcements. The founder already has a trusted distribution channel (a GSE Telegram audience) but no product to convert that trust into a habitual tool.

### 1.2 Personas

**P1 — Novice retail investor ("Ama")**
- Owns 2–5 stocks bought through one broker over a few years, mostly buy-and-hold.
- Not spreadsheet-literate; wants "what am I worth, what did I make" in plain language.
- Primary device: mid-range Android phone, intermittent data bundle — bandwidth matters.
- Trigger to use SikaTrack: wants to stop guessing her returns and finding out about dividends late.

**P2 — Active trader ("Kwabena")**
- 10–30 positions, trades a few times a month across possibly two brokers.
- Wants price-movement alerts on watchlist stocks, fast portfolio view, cares about realized vs unrealized P&L for decisions.
- Will pay for instant alerts if they're reliably faster than his broker's app or the GSE website.

**P3 — Diaspora investor ("Efua")**
- Lives abroad, invests in GSE stocks via a Ghanaian broker for diversification/home-country reasons.
- Cares about consolidated view without needing to log into a Ghanaian broker portal from abroad; time-zone means she wants alerts async (Telegram), not "check the website."
- More price-sensitive to platform trust and correctness (money is coming from abroad) than to the paid tier price itself.

### 1.3 User stories with acceptance criteria

Format: `As a <persona>, I want <capability>, so that <benefit>.` Acceptance criteria in Given/When/Then.

**US-1 (P1, P2, P3): Manual transaction entry**
- As a user, I want to log a buy or sell transaction for a GSE stock, so that my portfolio reflects reality without waiting on statement uploads.
- AC: Given I'm on "Add transaction", when I submit ticker, type (buy/sell), quantity, price, date, and fees, then the transaction appears in my history and my holdings/cost-basis recalculate immediately.
- AC: Given I submit a sell quantity greater than my current holding for that ticker, when I submit, then I see a validation error and no transaction is created (no short positions in MVP).

**US-2 (all): Portfolio dashboard**
- As a user, I want to see current holdings, total value, and unrealized P&L at a glance, so that I know where I stand without doing arithmetic.
- AC: Given I have ≥1 open position and a same-day-or-later closing price exists for it, when I open the dashboard, then I see per-holding market value using the latest available close, not a live price.
- AC: Given no closing price newer than 3 trading days exists for a held stock, when I view that holding, then the UI shows a "price as of {date}" staleness label rather than implying a live quote.

**US-3 (P1, P3): Broker statement upload**
- As a user, I want to upload my IC Securities PDF statement, so that I don't have to hand-type months of history.
- AC: Given I upload a supported PDF, when parsing succeeds, then I see an editable review screen listing every extracted transaction with confidence flags before anything is committed to my portfolio.
- AC: Given the parser cannot confidently extract a row (e.g., merged columns, OCR ambiguity), when I reach the review screen, then that row is visually flagged "needs review" and pre-fills its best-guess values as editable fields, not silently dropped or silently guessed.
- AC: Given I confirm the review screen, when I submit, then only the confirmed rows are committed as transactions, tagged with their source statement for audit.

**US-4 (all): Dividend income history**
- As a user, I want to see dividends received per holding and in total, so that I understand my full return, not just price appreciation.
- AC: Given a dividend record exists for a stock I held on its record date, when I view the dividend history, then that dividend appears with amount = my held quantity × per-share dividend, and it contributes to total return calculations.

**US-5 (P2): Price movement alerts**
- As a trader, I want to set a % move threshold on a watched stock, so that I hear about it without checking the app all day.
- AC: Given I set a 5% threshold on stock X, when the daily close moves ≥5% vs the prior close, then I receive a Telegram alert same-day after the ingest job runs (not real-time — daily data only).

**US-6 (all): Corporate action alerts**
- As a user, I want ex-dividend, AGM, rights issue, and earnings alerts for stocks I hold or watch, so that I don't miss deadlines that affect me.
- AC: Given a corporate action is entered for a stock I hold, when the alert dispatch job runs, then I receive exactly one Telegram message per action per user, not one per matching subscription rule.

**US-7 (all): Account linking**
- As a user, I want my Telegram account linked to my web account, so that alerts and portfolio data are the same identity everywhere.
- AC: Given I start the bot with `/start <link_code>` generated from the web app, when the bot validates the code, then my Telegram chat ID is attached to my user account and the code is invalidated after one use.

**US-8 (P2, P3, paying tier): Instant vs delayed alerts**
- As a free-tier user, I receive alerts at the daily batch time; as a paid user, I receive them as soon as the triggering data (corporate action entry, ingest run) is processed, so paying feels meaningfully faster.
- AC: Given two users (free, paid) are both subscribed to the same alert, when the alert condition fires, then the paid user's message is queued before/without the free tier's batch delay window.

**US-9 (P1): Zero-state onboarding**
- As a brand-new user with no transactions, I want a clear next step, so that I'm not staring at an empty dashboard.
- AC: Given I've just registered, when I land on the dashboard, then I see two clear CTAs — "Upload a broker statement" and "Add a transaction manually" — and no empty charts/tables with no explanation.

### 1.4 MVP feature list vs post-MVP roadmap

**MVP (in scope, 6–8 weeks):**
- Email/phone signup, login, password reset.
- Manual transaction CRUD (buy/sell only — no corporate-action-driven adjustments beyond dividends).
- Holdings + cost basis (average cost method) + realized/unrealized P&L computation.
- Daily price ingest from CSV (manually triggered/admin-uploaded CSV at first; scrape pipeline design included but scraper itself can ship in week 2 hardening, not day 1).
- Dashboard: total value, allocation pie/table, top movers among *held* stocks, upcoming corporate actions for held stocks.
- IC Securities PDF statement parser (one broker only for MVP) with review-before-commit flow.
- Dividend income tracking (admin-entered dividend records matched to holdings).
- Telegram bot: account linking, corporate action alerts, price threshold alerts (free tier = daily digest; paid tier = instant, gated behind a manual/simple payment flow).
- Paystack mobile money one-time payment for a paid-tier period (subscription *lifecycle* logic even if renewal is manual, see §6).
- Basic admin (Django admin) for entering corporate actions, dividends, and uploading price CSVs.

**Explicitly out of scope for MVP (post-MVP roadmap):**
- Additional broker parsers (Databank, etc.) — architecture supports it, implementation deferred.
- Automated GSE scraping (start with manual/admin CSV upload; add scraper once format is proven stable).
- Automated corporate-action scraping from GSE/company sites — admin entry first.
- FIFO/specific-lot cost basis method (average cost only for MVP).
- Multi-currency / non-GSE instruments.
- In-app charting beyond simple server-rendered charts (no candlesticks, no intraday).
- Social/community features (leaderboards, sharing).
- Automated subscription renewal / recurring MoMo billing.
- Native mobile app (PWA only).
- SMS alerts (Telegram only for MVP).
- Tax reporting exports.

---

## 2. System Architecture

### 2.1 Component overview (text diagram)

```
                         ┌─────────────────────────┐
                         │        Users             │
                         │  (Browser/PWA)  (Telegram)│
                         └───────┬───────────┬───────┘
                                 │           │
                     HTTPS (Django views)    │ Telegram Bot API (webhook)
                                 │           │
                 ┌───────────────▼───────────▼─────────────┐
                 │              VPS (single box)             │
                 │                                            │
                 │  ┌──────────────┐    ┌──────────────────┐ │
                 │  │ Django (WSGI/│    │  Telegram webhook │ │
                 │  │ Gunicorn)    │◄──►│  view (same       │ │
                 │  │ - web app    │    │  Django process)  │ │
                 │  │ - admin      │    └──────────────────┘ │
                 │  └──────┬───────┘                          │
                 │         │                                   │
                 │  ┌──────▼───────┐    ┌───────────────────┐ │
                 │  │ PostgreSQL   │    │ Django-Q2 cluster │ │
                 │  │ (single DB)  │◄──►│ (background       │ │
                 │  └──────────────┘    │ worker process)   │ │
                 │                       │ - daily price     │ │
                 │                       │   ingest          │ │
                 │                       │ - alert matching  │ │
                 │                       │ - alert dispatch  │ │
                 │                       │ - PDF parsing     │ │
                 │                       │   (async)         │ │
                 │                       └─────────┬─────────┘ │
                 │                                  │           │
                 │  ┌──────────────┐   ┌────────────▼────────┐ │
                 │  │ Nginx        │   │ Telegram Bot API      │ │
                 │  │ (reverse     │   │ (outbound: send      │ │
                 │  │ proxy, TLS,  │   │  messages)            │ │
                 │  │ static files)│   └───────────────────────┘ │
                 │  └──────────────┘                              │
                 └────────────────────────────┬────────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │ Paystack (MoMo)      │
                                    │ - checkout           │
                                    │ - webhook callback    │
                                    └───────────────────────┘

External/offline inputs:
  - Daily GSE closing prices → CSV → admin upload / scheduled scrape job
  - Broker PDF statements → user upload
  - Corporate actions/dividends → admin entry (Django admin) in MVP
```

**Judgment call:** everything (web, bot webhook, worker) runs in one Django codebase on one VPS. Tradeoff: simplest possible ops for a solo dev with no team to hand off infra to; costs you horizontal scalability, which you don't need at MVP traffic.

### 2.2 Django project/app structure

```
sikatrack/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                      # project package (settings, urls, asgi/wsgi)
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                    # custom user model, auth, telegram linking
│   ├── models.py                # User, TelegramLink
│   ├── views.py                 # signup/login/link-telegram
│   └── forms.py
├── instruments/                 # tickers, sectors, daily prices
│   ├── models.py                # Instrument, PriceBar
│   └── ingest/
│       ├── csv_ingest.py        # parses daily CSV into PriceBar rows
│       └── scraper.py           # post-MVP: pulls CSV/HTML from GSE source
├── portfolio/                   # transactions, holdings, P&L
│   ├── models.py                # Transaction, Holding (computed/cached)
│   ├── services.py              # cost-basis + P&L calculation logic
│   └── views.py                 # dashboard, add/edit transaction
├── dividends/                   # dividend records + per-user income calc
│   ├── models.py                # DividendRecord, DividendReceipt
│   └── services.py
├── corporate_actions/           # AGMs, rights issues, earnings dates
│   ├── models.py                # CorporateAction
│   └── admin.py
├── statements/                  # broker statement upload/parse pipeline
│   ├── models.py                # StatementUpload, ExtractedTransaction
│   ├── parsers/
│   │   ├── base.py              # BrokerParser abstract base
│   │   ├── ic_securities.py     # IC Securities-specific parser
│   │   └── registry.py          # maps broker choice -> parser class
│   ├── tasks.py                 # async parse job (Django-Q2)
│   └── views.py                 # upload, review, confirm
├── alerts/                      # subscriptions, matching, dispatch
│   ├── models.py                # AlertSubscription, AlertDelivery
│   ├── matching.py              # subscription <-> event matching logic
│   └── tasks.py                 # dispatch job
├── telegram_bot/                # bot logic, separate from webhook plumbing
│   ├── handlers.py              # command handlers (/start, /watch, etc.)
│   ├── webhook_view.py          # Django view receiving Telegram updates
│   └── client.py                # thin wrapper for sending messages
├── billing/                     # subscriptions, payments, Paystack
│   ├── models.py                # SubscriptionPlan, Subscription, Payment
│   ├── paystack.py              # API client + webhook verification
│   └── views.py
├── templates/                   # Django templates (HTMX partials live alongside)
└── static/                      # Tailwind output, Alpine.js, minimal JS
```

**Judgment call:** apps are split by domain (portfolio, statements, alerts, billing) rather than by technical layer. Tradeoff: slightly more app boilerplate up front; pays off because statement parsing, alerting, and billing each have real independent complexity you'll want to test in isolation.

### 2.3 Telegram bot integration: webhook vs polling

**Decision: webhook, not long-polling**, using `python-telegram-bot` (PTB) purely as a thin update-parsing/dispatch library, with the actual HTTP endpoint being a normal Django view (not PTB's built-in webserver).

- A Django view at `/telegram/webhook/<secret-path-token>/` receives Telegram's POST, verifies the `X-Telegram-Bot-Api-Secret-Token` header, builds a PTB `Update` object from the JSON body, and hands it to a PTB `Application` (built with `updater=None` since Django owns the server loop) for command routing.
- Outbound sends (alerts) do **not** go through the webhook path — the alert dispatch background job calls the Telegram Bot API directly via a small synchronous HTTP client (`telegram_bot/client.py`, wrapping `httpx`/`requests`), because that's simpler to call from a Django-Q2 task than spinning up PTB's async runtime inside a sync worker.

**Judgment call:** running PTB's own polling loop or built-in webhook server as a second process is more "idiomatic PTB" but means a second long-running process to deploy/monitor. Folding inbound updates into a Django view and outbound sends into a plain HTTP client keeps the whole system to two processes total (gunicorn + Django-Q2 worker), which is the right tradeoff for a solo dev on one VPS.

### 2.4 Background task strategy: Django-Q2 over Celery

**Decision: Django-Q2**, using PostgreSQL (via `django-q2`'s ORM broker) as the queue backend — no Redis/RabbitMQ to run.

Reasons specific to this project:
- Needs are modest and well-scheduled: one daily price ingest, one/two daily alert-dispatch runs, and on-demand PDF parse jobs. Celery's strengths (complex routing, many queues, huge throughput) aren't needed.
- One fewer service to operate on a single VPS (no broker process, no Flower). Django-Q2's admin-visible task list is enough observability for solo ops.
- Built-in scheduler (`Schedule` model) replaces the need for Celery Beat.

**Judgment call:** Celery + Redis is more "industry standard" and would matter if this needed to scale to many workers or complex retries later; for a solo dev shipping in 6–8 weeks, Django-Q2's operational simplicity outweighs Celery's ecosystem maturity. Migrating later (if ever needed) is a contained change since task functions are plain Python callables either way.

**Scheduled jobs (via Django-Q2 `Schedule`):**
| Job | Cadence | Notes |
|---|---|---|
| `ingest_daily_prices` | Once daily, ~17:30 GMT (after GSE close + settlement) | Reads latest uploaded CSV or runs scraper (post-MVP) |
| `dispatch_free_tier_alerts` | Once daily, after ingest | Batches all free-tier eligible alerts into digest sends |
| `dispatch_paid_tier_alerts` | Triggered async immediately after any alert-worthy event is created (not a fixed cron) | Enqueued as an immediate task, not scheduled |
| `send_subscription_renewal_reminders` | Once daily | Checks subscriptions expiring in N days, sends Telegram/email reminder |

---

## 3. Data Model

Below are the core Django models. Field choices favor explicitness (e.g., storing `price` and `fees` on `Transaction` rather than inferring) so P&L math never has to guess.

```python
# accounts/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model from day one — cheap now, painful to retrofit later."""
    phone_number = models.CharField(max_length=20, blank=True)
    is_paid_tier = models.BooleanField(default=False)  # denormalized flag, source of truth is billing.Subscription
    created_at = models.DateTimeField(auto_now_add=True)


class TelegramLink(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram_link")
    chat_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=64, blank=True)
    link_code = models.CharField(max_length=12, unique=True, null=True, blank=True)
    linked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["chat_id"])]
```

```python
# instruments/models.py
from django.db import models


class Instrument(models.Model):
    """A GSE-listed security."""
    ticker = models.CharField(max_length=12, unique=True)  # e.g. "MTNGH", "GCB", "EGL"
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True)
    isin = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)  # False if delisted/suspended
    listed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["ticker"]

    def __str__(self):
        return self.ticker


class PriceBar(models.Model):
    """One daily closing observation. Deliberately NOT a live quote model."""
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="price_bars")
    trade_date = models.DateField()
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    open_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=[("csv_upload", "Manual CSV upload"), ("scrape", "Automated scrape")],
        default="csv_upload",
    )
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["instrument", "trade_date"], name="uniq_price_per_day")
        ]
        indexes = [models.Index(fields=["instrument", "-trade_date"])]
        ordering = ["-trade_date"]

    def __str__(self):
        return f"{self.instrument.ticker} {self.trade_date} @ {self.close_price}"


class PriceIngestBatch(models.Model):
    """Audit trail for each CSV upload/scrape run — critical for debugging bad data."""
    source = models.CharField(max_length=20)
    trade_date = models.DateField()
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    raw_file = models.FileField(upload_to="price_ingest/", null=True, blank=True)
    uploaded_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

```python
# portfolio/models.py
from django.conf import settings
from django.db import models


class Transaction(models.Model):
    BUY = "BUY"
    SELL = "SELL"
    TYPE_CHOICES = [(BUY, "Buy"), (SELL, "Sell")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    price_per_share = models.DecimalField(max_digits=12, decimal_places=4)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_date = models.DateField()
    broker = models.CharField(max_length=50, blank=True)  # free text or FK to a Broker model post-MVP
    source_statement = models.ForeignKey(
        "statements.StatementUpload", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="committed_transactions",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "instrument", "trade_date"]),
        ]
        ordering = ["-trade_date", "-created_at"]

    @property
    def gross_amount(self):
        return self.quantity * self.price_per_share

    @property
    def net_amount(self):
        """Cash impact: negative (outflow) for buys, positive (inflow) for sells."""
        sign = -1 if self.transaction_type == self.BUY else 1
        return sign * self.gross_amount - self.fees if self.transaction_type == self.BUY else sign * self.gross_amount - self.fees


class Holding(models.Model):
    """
    Cached/computed snapshot, one row per (user, instrument), rebuilt whenever
    that user's transactions for that instrument change. Not the source of
    truth (Transaction is) — exists so dashboard reads don't recompute from
    full transaction history on every page load.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holdings")
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="holdings")
    quantity = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    average_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)  # per-share, average-cost method
    realized_pnl = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_recalculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "instrument"], name="uniq_holding_per_user_instrument")
        ]

    @property
    def cost_basis(self):
        return self.quantity * self.average_cost

    def unrealized_pnl(self, current_price):
        return (current_price - self.average_cost) * self.quantity
```

```python
# portfolio/services.py
"""
Cost-basis + P&L calculation — average cost method (MVP scope; FIFO is post-MVP).
Pure functions over a queryset so this is trivially unit-testable without hitting
the DB for Holding writes in tests.
"""
from decimal import Decimal

from .models import Holding, Transaction


def recalculate_holding(user, instrument):
    """
    Replays all transactions for (user, instrument) in trade_date order and
    rebuilds the Holding row. Called synchronously after any transaction
    create/update/delete — volumes are low enough (dozens to low hundreds of
    transactions per user) that this is cheap; no need to make it async.
    """
    txns = Transaction.objects.filter(user=user, instrument=instrument).order_by("trade_date", "created_at")

    quantity = Decimal("0")
    total_cost = Decimal("0")
    realized_pnl = Decimal("0")

    for txn in txns:
        if txn.transaction_type == Transaction.BUY:
            total_cost += txn.gross_amount + txn.fees
            quantity += txn.quantity
        else:  # SELL
            avg_cost = (total_cost / quantity) if quantity else Decimal("0")
            realized_pnl += (txn.price_per_share - avg_cost) * txn.quantity - txn.fees
            total_cost -= avg_cost * txn.quantity
            quantity -= txn.quantity

    average_cost = (total_cost / quantity) if quantity else Decimal("0")

    holding, _ = Holding.objects.update_or_create(
        user=user,
        instrument=instrument,
        defaults={
            "quantity": quantity,
            "average_cost": average_cost,
            "realized_pnl": realized_pnl,
        },
    )
    return holding
```

```python
# dividends/models.py
from django.conf import settings
from django.db import models


class DividendRecord(models.Model):
    """Admin-entered: one per company per declared dividend."""
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="dividends")
    amount_per_share = models.DecimalField(max_digits=10, decimal_places=4)
    record_date = models.DateField(help_text="Shareholders as of this date qualify.")
    ex_dividend_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    fiscal_year_note = models.CharField(max_length=50, blank=True)  # e.g. "FY2025 final"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ex_dividend_date"]


class DividendReceipt(models.Model):
    """
    Computed per-user record: user's held quantity as of record_date x
    amount_per_share. Generated by a service function when a DividendRecord
    is created/updated — not user-editable.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dividend_receipts")
    dividend_record = models.ForeignKey(DividendRecord, on_delete=models.CASCADE, related_name="receipts")
    quantity_held = models.DecimalField(max_digits=14, decimal_places=4)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "dividend_record"], name="uniq_receipt_per_user_dividend")
        ]
```

```python
# corporate_actions/models.py
from django.db import models


class CorporateAction(models.Model):
    AGM = "AGM"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    EARNINGS = "EARNINGS"
    EX_DIVIDEND = "EX_DIVIDEND"
    OTHER = "OTHER"
    ACTION_TYPES = [
        (AGM, "Annual General Meeting"),
        (RIGHTS_ISSUE, "Rights Issue"),
        (EARNINGS, "Earnings Release"),
        (EX_DIVIDEND, "Ex-Dividend Date"),
        (OTHER, "Other"),
    ]

    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="corporate_actions")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_date = models.DateField(help_text="The date the action occurs/takes effect.")
    source_url = models.URLField(blank=True)
    entered_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL
    )  # admin entry in MVP; nullable so a future scraper can insert as system
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["instrument", "event_date"])]
        ordering = ["event_date"]
```

```python
# statements/models.py
from django.conf import settings
from django.db import models


class StatementUpload(models.Model):
    PENDING = "PENDING"
    PARSING = "PARSING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    STATUS_CHOICES = [
        (PENDING, "Pending"), (PARSING, "Parsing"), (NEEDS_REVIEW, "Needs review"),
        (CONFIRMED, "Confirmed"), (FAILED, "Failed"),
    ]

    BROKER_CHOICES = [("IC_SECURITIES", "IC Securities")]  # extend as new parsers ship

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="statement_uploads")
    broker = models.CharField(max_length=30, choices=BROKER_CHOICES)
    file = models.FileField(upload_to="statements/%Y/%m/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    parse_error = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)


class ExtractedTransaction(models.Model):
    """
    One row per transaction the parser found. Exists independently of
    portfolio.Transaction so the user review/edit step never touches
    committed data — only on confirm do rows get turned into real
    Transaction objects.
    """
    statement = models.ForeignKey(StatementUpload, on_delete=models.CASCADE, related_name="extracted_rows")
    raw_ticker_text = models.CharField(max_length=100, blank=True)  # what was literally on the PDF
    matched_instrument = models.ForeignKey(
        "instruments.Instrument", null=True, blank=True, on_delete=models.SET_NULL
    )
    transaction_type = models.CharField(max_length=4, choices=[("BUY", "Buy"), ("SELL", "Sell")], blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    price_per_share = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_date = models.DateField(null=True, blank=True)
    confidence = models.CharField(
        max_length=10,
        choices=[("HIGH", "High"), ("LOW", "Low needs review")],
        default="HIGH",
    )
    parse_notes = models.CharField(max_length=255, blank=True)  # why confidence is LOW, if it is
    is_confirmed = models.BooleanField(default=False)
    is_excluded = models.BooleanField(default=False)  # user can discard a bad row instead of confirming it
    row_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["row_order"]
```

```python
# alerts/models.py
from django.conf import settings
from django.db import models


class AlertSubscription(models.Model):
    PRICE_THRESHOLD = "PRICE_THRESHOLD"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    PORTFOLIO_HOLDINGS = "PORTFOLIO_HOLDINGS"  # "alert me for anything affecting stocks I hold"
    KIND_CHOICES = [
        (PRICE_THRESHOLD, "Price movement threshold"),
        (CORPORATE_ACTION, "Corporate action"),
        (PORTFOLIO_HOLDINGS, "All holdings"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_subscriptions")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    instrument = models.ForeignKey(
        "instruments.Instrument", null=True, blank=True, on_delete=models.CASCADE,
        help_text="Null when kind=PORTFOLIO_HOLDINGS (applies to all held stocks).",
    )
    threshold_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Only used for PRICE_THRESHOLD, e.g. 5.00 for +/-5%.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "kind", "is_active"])]


class AlertEvent(models.Model):
    """
    A single fact that might be worth alerting about (a price move past
    threshold, or a corporate action). Decoupled from AlertDelivery so
    dedup logic ("has this user already been told about this event?") is a
    simple lookup, not a fuzzy comparison.
    """
    event_type = models.CharField(max_length=20)
    instrument = models.ForeignKey("instruments.Instrument", on_delete=models.CASCADE, related_name="alert_events")
    corporate_action = models.ForeignKey(
        "corporate_actions.CorporateAction", null=True, blank=True, on_delete=models.CASCADE
    )
    trigger_date = models.DateField()
    payload = models.JSONField(default=dict, blank=True)  # e.g. {"move_pct": 6.2, "close": 12.40}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # prevents the same underlying fact from being recorded twice if
            # the ingest job is accidentally re-run for the same day
            models.UniqueConstraint(
                fields=["event_type", "instrument", "trigger_date", "corporate_action"],
                name="uniq_alert_event",
            )
        ]


class AlertDelivery(models.Model):
    """One row per (user, event) — the dedup + delivery-status ledger."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_deliveries")
    event = models.ForeignKey(AlertEvent, on_delete=models.CASCADE, related_name="deliveries")
    subscription = models.ForeignKey(AlertSubscription, null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=10, choices=[("TELEGRAM", "Telegram")], default="TELEGRAM")
    tier_at_send = models.CharField(max_length=10, choices=[("FREE", "Free"), ("PAID", "Paid")])
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "event"], name="uniq_delivery_per_user_event")
        ]
```

```python
# billing/models.py
from django.conf import settings
from django.db import models


class SubscriptionPlan(models.Model):
    code = models.CharField(max_length=30, unique=True)  # "PAID_MONTHLY", "PAID_QUARTERLY"
    name = models.CharField(max_length=100)
    price_ghs = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)


class Subscription(models.Model):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    STATUS_CHOICES = [(ACTIVE, "Active"), (EXPIRED, "Expired"), (CANCELLED, "Cancelled")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    auto_renew_requested = models.BooleanField(
        default=False,
        help_text="User intent only — MoMo has no real auto-debit in MVP; this drives reminder copy, not billing.",
    )
    renewal_reminder_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status", "ends_at"])]

    @property
    def is_currently_active(self):
        from django.utils import timezone
        return self.status == self.ACTIVE and self.ends_at > timezone.now()


class Payment(models.Model):
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    STATUS_CHOICES = [(INITIATED, "Initiated"), (SUCCESS, "Success"), (FAILED, "Failed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    amount_ghs = models.DecimalField(max_digits=8, decimal_places=2)
    provider = models.CharField(max_length=20, default="PAYSTACK")
    provider_reference = models.CharField(max_length=100, unique=True)  # Paystack transaction reference
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=INITIATED)
    momo_network = models.CharField(max_length=20, blank=True)  # MTN/Vodafone/AirtelTigo, from Paystack metadata
    raw_webhook_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
```

---

## 4. Statement Parsing Design

### 4.1 Pipeline

```
Upload (user) → Extract (per-broker parser, async) → Normalize → User review (edit/confirm/discard) → Commit
```

1. **Upload**: user picks broker (dropdown — MVP has one option, IC Securities) and a PDF. `StatementUpload` row created with `status=PENDING`; file saved to storage. An async task is enqueued (Django-Q2) — parsing a multi-page PDF can take a couple seconds and must not block the request/response cycle.
2. **Extract**: the async task looks up the parser class for `statement.broker` via `parsers/registry.py`, instantiates it with the file, and calls `parser.extract()`, which returns a list of raw row dicts plus any page-level warnings. `status → PARSING` while running.
3. **Normalize**: extracted raw rows are converted into `ExtractedTransaction` rows: ticker text is matched against `Instrument` (exact match, then fuzzy/alias table for known broker naming quirks, e.g. broker prints "MTN GHANA" for ticker `MTNGH`); dates/numbers are parsed into proper types; each row gets a `confidence` of `HIGH` or `LOW` based on parser-reported certainty (see §4.3). `status → NEEDS_REVIEW` (or `FAILED` if the PDF couldn't be parsed at all — see §4.4).
4. **User review**: user sees every `ExtractedTransaction` row in an editable table (HTMX-powered inline edit, no page reloads). LOW-confidence rows are visually flagged with the specific reason (e.g., "quantity column ambiguous"). User can edit any field, exclude a row, or confirm individually/in bulk.
5. **Commit**: on submit, only rows with `is_confirmed=True` and `is_excluded=False` are turned into real `portfolio.Transaction` objects in a single DB transaction, each tagged `source_statement=statement`. `Holding` is recalculated for every affected instrument. `StatementUpload.status → CONFIRMED`.

**Judgment call:** parsing happens async but review/commit is synchronous (normal request/response) — a review screen with a spinner that never resolves is worse UX than a short wait, and PDF extraction for a few-page brokerage statement is seconds, not minutes, so async is about not blocking the initial upload request, not about the review step.

### 4.2 Per-broker parser classes (pluggable design)

```python
# statements/parsers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class RawStatementRow:
    """What every parser must produce, regardless of broker PDF layout."""
    raw_ticker_text: str
    transaction_type: str  # "BUY" or "SELL"
    quantity: Decimal | None
    price_per_share: Decimal | None
    fees: Decimal
    trade_date: date | None
    confidence: str  # "HIGH" or "LOW"
    parse_notes: str = ""


@dataclass
class ExtractionResult:
    rows: list[RawStatementRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)  # page-level, not row-level


class BrokerParser(ABC):
    """
    One subclass per broker. Each broker's PDF layout is different enough
    (column order, headers, date formats, fee line items) that a shared
    "generic PDF table parser" fights every broker instead of fitting any
    of them — hence one class per broker rather than a config-driven
    generic parser.
    """

    broker_code: str  # must match StatementUpload.BROKER_CHOICES

    def __init__(self, file_obj):
        self.file_obj = file_obj

    @abstractmethod
    def extract(self) -> ExtractionResult:
        """Parse self.file_obj and return structured rows. Must not raise
        for row-level issues (flag as LOW confidence instead) — only raise
        for whole-document failures (unreadable/encrypted/wrong-broker PDF),
        which the caller catches and routes to StatementUpload.FAILED."""
        raise NotImplementedError
```

```python
# statements/parsers/ic_securities.py
"""
Skeleton for IC Securities statements. Uses pdfplumber to extract text/tables
since IC statements are text-based PDFs (not scanned images) as of the
broker's current export format — revisit if that changes (would need OCR,
see registry note below).
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pdfplumber

from .base import BrokerParser, ExtractionResult, RawStatementRow

DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")


class ICSecuritiesParser(BrokerParser):
    broker_code = "IC_SECURITIES"

    def extract(self) -> ExtractionResult:
        result = ExtractionResult()

        try:
            with pdfplumber.open(self.file_obj) as pdf:
                if not pdf.pages:
                    raise ValueError("Empty PDF")
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        self._parse_table(table, result)
        except Exception as exc:
            # Whole-document failure — caller marks StatementUpload as FAILED
            # and routes to manual entry. Do not swallow silently.
            raise ValueError(f"Could not read PDF as IC Securities statement: {exc}") from exc

        if not result.rows:
            result.warnings.append("No transaction rows found — layout may not match expected IC Securities format.")

        return result

    def _parse_table(self, table: list[list[str | None]], result: ExtractionResult) -> None:
        header, *body_rows = table if table else ([], [])
        for row in body_rows:
            if not row or not any(row):
                continue
            row_result = self._parse_row(row)
            if row_result is not None:
                result.rows.append(row_result)

    def _parse_row(self, row: list[str | None]) -> RawStatementRow | None:
        """
        Expected IC Securities column order (subject to real-sample
        verification before launch):
        [Trade Date, Description/Ticker, Buy/Sell, Quantity, Price, Fees, Net Amount]
        """
        try:
            cells = [c.strip() if c else "" for c in row]
            trade_date_str, ticker_text, side, qty_str, price_str, fees_str = cells[:6]

            confidence = "HIGH"
            notes = []

            trade_date = self._parse_date(trade_date_str)
            if trade_date is None:
                confidence, notes = "LOW", notes + ["unparseable trade date"]

            quantity = self._parse_decimal(qty_str)
            if quantity is None:
                confidence, notes = "LOW", notes + ["unparseable quantity"]

            price = self._parse_decimal(price_str)
            if price is None:
                confidence, notes = "LOW", notes + ["unparseable price"]

            fees = self._parse_decimal(fees_str) or Decimal("0")

            txn_type = "BUY" if "buy" in side.lower() else ("SELL" if "sell" in side.lower() else "")
            if not txn_type:
                confidence, notes = "LOW", notes + [f"unrecognized side '{side}'"]

            return RawStatementRow(
                raw_ticker_text=ticker_text,
                transaction_type=txn_type,
                quantity=quantity,
                price_per_share=price,
                fees=fees,
                trade_date=trade_date,
                confidence=confidence,
                parse_notes="; ".join(notes),
            )
        except (IndexError, ValueError):
            # A malformed row still produces a LOW-confidence stub rather than
            # vanishing — the user needs to see "something was here" even if
            # we can't parse it.
            return RawStatementRow(
                raw_ticker_text=" ".join(c for c in row if c) if row else "",
                transaction_type="",
                quantity=None,
                price_per_share=None,
                fees=Decimal("0"),
                trade_date=None,
                confidence="LOW",
                parse_notes="row did not match expected column layout",
            )

    @staticmethod
    def _parse_date(value: str):
        if not DATE_RE.fullmatch(value):
            return None
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: str):
        cleaned = value.replace(",", "").replace("GHS", "").strip()
        try:
            return Decimal(cleaned) if cleaned else None
        except InvalidOperation:
            return None
```

```python
# statements/parsers/registry.py
from .ic_securities import ICSecuritiesParser

PARSER_REGISTRY = {
    ICSecuritiesParser.broker_code: ICSecuritiesParser,
    # "DATABANK": DatabankParser,  # post-MVP
}


def get_parser_class(broker_code: str):
    try:
        return PARSER_REGISTRY[broker_code]
    except KeyError:
        raise ValueError(f"No parser registered for broker '{broker_code}'")
```

### 4.3 Confidence flagging rules

A row is `LOW` confidence when any of: date fails to parse against the expected format, quantity/price fails to parse as a number, buy/sell side text doesn't match known keywords, or ticker text doesn't match any known `Instrument` (exact or alias). `HIGH` confidence still gets shown on the review screen — the difference is only default focus/highlighting, never a skip-review shortcut. **Every row is reviewed by the user before commit, regardless of confidence** — confidence controls UI emphasis, not whether review happens, because misplaced trust in "high confidence" parsing of someone's actual money is the failure mode to design against.

### 4.4 Error handling for malformed PDFs

| Failure mode | Handling |
|---|---|
| Encrypted/password-protected PDF | Caught at `extract()`, `StatementUpload.status = FAILED`, `parse_error` set to a user-facing message; UI offers "remove password and re-upload" or "enter transactions manually" |
| Scanned image PDF (no extractable text) | `pdfplumber` returns no tables/text → `ExtractionResult.rows` empty → surfaced as FAILED with a specific message ("this looks like a scanned/image PDF, which isn't supported yet"); logged broker+reason so it informs the OCR-vs-not decision post-MVP |
| Layout doesn't match expected columns | Handled per-row: falls back to a LOW-confidence stub row (see `_parse_row` except branch) rather than failing the whole document — partial extraction beats total failure |
| Wrong broker selected (e.g., Databank PDF run through IC parser) | Sanity check: if zero rows extracted AND page text doesn't contain expected broker letterhead markers, fail fast with "this doesn't look like an IC Securities statement — check the broker selection" instead of silently returning nothing |
| Parser crashes on an edge case (bug) | Caught at the task level; `StatementUpload.status = FAILED`, full traceback logged server-side (not shown to user), user sees "we couldn't process this file — manual entry is available" |

### 4.5 Manual-review fallback

Whenever a statement ends in `FAILED`, or a user simply prefers not to upload, the manual "Add transaction" form (US-1) is always available and is the actual source of truth mechanism — statement parsing is a convenience layer on top of it, never a required path. This is also the fallback for brokers without a parser yet (post-MVP brokers): users can still get their data in, just by typing it.

---

## 5. Alert Engine Design

### 5.1 How corporate actions enter the system

**MVP: admin entry only.** The founder (or a VA) enters `CorporateAction` and `DividendRecord` rows via Django admin as GSE/company announcements are published. This is intentionally manual at first.

**Judgment call:** building a scraper for GSE/company announcement pages before validating the alert feature is used at all would be solving a scaling problem you don't have yet. Admin entry costs ~5 minutes per announcement and directly uses the founder's existing habit of tracking these for the Telegram channel — the marginal work of also typing it into Django admin is small compared to building and maintaining a scraper against sites that can change format without notice.

**Post-MVP scraping design (for when volume justifies it):** a `corporate_actions/scraper.py` job (same shape as `instruments/ingest/scraper.py`) polls the GSE announcements page and known company investor-relations pages on a schedule, extracts candidate `CorporateAction` rows with `entered_by=None` and a `needs_admin_review=True` flag (field to add at that point), and surfaces them in Django admin for one-click approval rather than auto-publishing — corporate action data errors directly cause bad alerts to real investors, so a human-in-the-loop approval step stays even after scraping is added.

### 5.2 Matching alerts to subscriptions

Two-stage: **event generation**, then **fan-out to subscribers**.

1. **Event generation** (`alerts/tasks.py`, runs after price ingest and whenever a `CorporateAction`/`DividendRecord` is saved):
   - Price threshold: for each `Instrument` with a new `PriceBar`, compute `% change` vs the prior trading day's close. For every distinct threshold value across all `AlertSubscription(kind=PRICE_THRESHOLD)` rows on that instrument where `abs(% change) >= threshold_percent`, create (or get-if-exists, via the unique constraint) one `AlertEvent(event_type="PRICE_MOVE", instrument=..., trigger_date=today)`.
   - Corporate action: on `CorporateAction` save, create one `AlertEvent(event_type="CORPORATE_ACTION", instrument=..., corporate_action=...)`.
   - This step creates **one event per underlying fact**, not per subscriber — the fan-out to N subscribers happens next, so a stock with 500 watchers doesn't create 500 near-duplicate event rows.

2. **Fan-out matching** (`alerts/matching.py`):
   ```python
   def match_subscribers_for_event(event: AlertEvent):
       """Returns the set of users who should be notified for this event,
       from three possible subscription paths: direct instrument watch,
       'all my holdings' subscription, or (for corporate actions on a stock
       the user actually holds) implicit relevance even without an explicit
       subscription."""
       subs = AlertSubscription.objects.filter(
           is_active=True,
       ).filter(
           models.Q(instrument=event.instrument) | models.Q(kind=AlertSubscription.PORTFOLIO_HOLDINGS)
       )
       candidate_user_ids = set(subs.values_list("user_id", flat=True))

       if event.event_type == "CORPORATE_ACTION":
           # also include users who hold the stock even with no explicit
           # subscription — corporate actions on your own holdings are
           # alert-worthy by default (US-6), not opt-in-only
           holder_ids = Holding.objects.filter(
               instrument=event.instrument, quantity__gt=0
           ).values_list("user_id", flat=True)
           candidate_user_ids |= set(holder_ids)

       return candidate_user_ids
   ```

### 5.3 Deduplication

Enforced at two levels, both via DB unique constraints rather than application-level "check then create" logic (which races under concurrent task execution):
- **Event-level**: `AlertEvent`'s `UniqueConstraint(event_type, instrument, trigger_date, corporate_action)` — the same price move or corporate action can't spawn two events even if the generation task somehow runs twice.
- **Delivery-level**: `AlertDelivery`'s `UniqueConstraint(user, event)` — a user is only ever queued once per event, even if they match through multiple subscription paths (e.g., both an explicit watch and the "all holdings" rule).

Dispatch code always uses `get_or_create` on `AlertDelivery` and only sends a Telegram message on actual creation, never on "get".

### 5.4 Delivery via Telegram

- Free tier: `AlertDelivery` rows created throughout the day sit with `sent_at=None`; the daily `dispatch_free_tier_alerts` job (§2.4) batches all of a user's unsent deliveries into a single digest message ("3 updates today: ...") rather than one Telegram message per event — reduces notification fatigue and gives paid tier a tangible speed+granularity difference.
- Paid tier: dispatch is enqueued immediately (as its own async task) at event-generation time, each event as its own message, sent via `telegram_bot/client.py`'s direct Bot API call.
- Delivery failures (user blocked the bot, chat_id invalid) are caught, recorded in `AlertDelivery.delivery_error`, and do not raise — one user's blocked bot must never stop the batch for everyone else.
- Users with no `TelegramLink` simply never get `AlertDelivery.sent_at` populated; the web dashboard can still show a "your alerts" panel from `AlertDelivery` rows as a fallback so linking Telegram is encouraged but not strictly required to get value.

---

## 6. Monetization Design

### 6.1 Tiers

| | Free | Paid ("SikaTrack Plus") |
|---|---|---|
| Portfolio tracker (manual entry + statement upload) | ✅ | ✅ |
| Dashboard, P&L, dividend history | ✅ | ✅ |
| Corporate action alerts | ✅ (daily digest) | ✅ (instant) |
| Price threshold alerts | ✅ (daily digest, max 3 watched stocks) | ✅ (instant, unlimited watched stocks) |
| Portfolio-linked "all my holdings" alerts | ❌ | ✅ |
| Weekly portfolio summary (Telegram) | ❌ | ✅ |

**Judgment call:** the free tier is generous on the *portfolio tracker* (the retention hook — people won't come back to a portfolio tool that hides their own numbers) and restrictive on *alert speed/breadth* (the thing traders will actually pay to not miss). Gating the core value prop behind payment would kill the Telegram-audience-to-signup conversion the founder is counting on.

### 6.2 Pricing (GHS)

- **Monthly:** GHS 25/month
- **Quarterly:** GHS 60 (≈ GHS 20/month, ~20% discount) — encourages a less-frequent manual renewal touchpoint, which matters given §6.3
- **Annual:** GHS 200 (≈ GHS 16.7/month) — for high-conviction early adopters, and reduces renewal-reminder operational load

**Judgment call:** priced below a single brokerage trade's minimum fee (so it reads as "less than one trade a quarter") and in round GHS numbers for MoMo — these are anchoring/psychology calls, not researched elasticity; treat as a starting hypothesis to validate per §10, not a fixed number.

### 6.3 Payment integration: Paystack (mobile money)

Paystack over Flutterwave for MVP: Paystack's Ghana MoMo support (MTN MoMo, Vodafone Cash, AirtelTigo Money) via their standard Checkout/Charge API is well-documented and widely used by other Ghanaian consumer apps, minimizing integration risk for a solo dev. **Judgment call:** either provider would work; picking Paystack is about existing community docs/support for a solo dev, not a hard technical differentiator — swap if the founder has an existing merchant relationship with one.

**Flow:**
1. User selects a plan on the billing page → Django view creates a `Payment(status=INITIATED)` and calls Paystack's initialize-transaction API → user is redirected to Paystack's hosted checkout (handles the MoMo prompt/PIN flow natively, so SikaTrack never touches MoMo PINs — important, see §8).
2. Paystack sends a webhook (`charge.success` / `charge.failed`) to a Django endpoint. **Signature is verified** (`X-Paystack-Signature` HMAC check) before trusting the payload — webhook endpoints are a common spoofing target.
3. On `charge.success`: `Payment.status = SUCCESS`, a `Subscription` row is created/extended (`ends_at = max(now, current_subscription.ends_at) + plan.duration_days`, so early renewal stacks rather than wastes remaining time), `User.is_paid_tier = True`.
4. The **redirect-back page** (user returning from Paystack checkout in-browser) shows a "confirming payment..." state and polls a small status endpoint — because the webhook can arrive slightly after the redirect; never trust the redirect alone as proof of payment, only the webhook.

### 6.4 Subscription lifecycle without auto-renewal

Ghanaian MoMo checkout (via Paystack) is a one-time charge per transaction, not a stored card with silent recurring debit — auto-renewal in the Stripe-subscription sense doesn't exist for this rail. Design accordingly rather than pretending it's like a card subscription:

- `Subscription.ends_at` is a hard boundary. A background job (`send_subscription_renewal_reminders`, daily) finds subscriptions with `ends_at` in the next 5 days and not yet reminded (`renewal_reminder_sent_at is None`), and sends a Telegram (and/or email) message with a direct "renew now" link pre-filled to their current plan.
- A second reminder fires at `ends_at - 1 day` if still unrenewed.
- On expiry (`ends_at` passed, no new successful `Payment`), a scheduled check flips `Subscription.status = EXPIRED` and `User.is_paid_tier = False` — user drops to free tier automatically, **no manual admin intervention required**, and no failed-auto-debit drama since nothing was ever auto-debited.
- `auto_renew_requested` is stored purely as user intent/preference (e.g., "remind me and I'll pay again") — it never triggers an actual charge. This keeps the mental model honest: nothing happens to their money without them present at a MoMo prompt.
- Grace period: none in MVP — access drops the moment `ends_at` passes, kept simple deliberately; a short grace period is an easy post-MVP kindness once churn data exists.

---

## 7. UI/UX Specification

Stack: Django templates + HTMX (partial swaps, no SPA routing) + Alpine.js (small client-side interactivity — toggles, inline edit state) + Tailwind (utility CSS, no component framework). Server-rendered charts (simple bar/line via lightweight SVG generation or a minimal library, not Chart.js-scale bundles) to respect low-bandwidth users.

### 7.1 Screen-by-screen (mobile-first)

**Onboarding / Sign up**
- Single-column form: name, email or phone, password. Ghana phone format hint (`0XX XXX XXXX`).
- After signup, immediately redirected to a 2-step "connect Telegram" screen (optional, skippable) showing a `/start <code>` deep link button — since the bot is core to the value prop, ask early but don't block.

**Zero-state dashboard (US-9)**
- No charts, no "GHS 0.00" placeholders trying to look like real data.
- Headline: "Let's build your portfolio." Two large tappable cards: "📄 Upload a broker statement" and "✏️ Add a transaction manually."
- A short 3-bullet "what you'll get" (portfolio tracking, dividend history, corporate action alerts) so the value is visible before any data exists.

**Populated dashboard**
- Top: total portfolio value (as of latest price date, with explicit "prices as of {date}" label — never implies live), total unrealized P&L (GHS and %), total realized P&L.
- Allocation: simple horizontal bar list (ticker, % of portfolio, value) — not a JS pie chart; degrades gracefully with no JS and is lighter than canvas/SVG pie rendering.
- "Top movers among your holdings": small table, ticker / % change / new close, computed from the last two `PriceBar` rows per held instrument.
- "Upcoming for your holdings": next 5 `CorporateAction` rows across held instruments, soonest first, each with a relative date ("in 4 days").
- Sticky bottom nav (mobile): Dashboard / Holdings / Add Transaction / Alerts / Profile.

**Holdings list**
- Table (cards on narrow screens): ticker, quantity, average cost, current value, unrealized P&L (green/red), % of portfolio.
- Tapping a holding opens its detail: transaction history for that ticker, dividend receipts for that ticker, a simple line-over-time of holding value (server-rendered sparkline-style SVG, not a JS charting lib).

**Add transaction**
- Single form, HTMX-submitted without full page reload: ticker (autocomplete against `Instrument`), buy/sell toggle, quantity, price, fees (optional, defaults 0), date (defaults today).
- Inline validation: sell quantity vs current holding checked live via HTMX on blur, not just on submit.

**Statement upload**
- Step 1: pick broker (dropdown; MVP shows "IC Securities" only, others "coming soon" greyed out — signals roadmap honestly rather than hiding it).
- Step 2: file picker + upload button; on submit, shows a lightweight polling state ("Reading your statement…") using HTMX polling (`hx-trigger="every 2s"`) against the `StatementUpload` status, swapping to the review screen when `status=NEEDS_REVIEW`.
- Step 3 (review): editable table, one row per `ExtractedTransaction`. LOW-confidence rows have a yellow left-border + inline note. Each row has inline-editable fields (HTMX-powered, Alpine for local edit-mode toggle) and a per-row "exclude" checkbox. Bottom: "Confirm N transactions" primary button, showing the count dynamically as rows are excluded/included.
- Step 4 (confirmation): "12 transactions added to your portfolio" + link to dashboard.
- Failure state: plain-language error + "Add these transactions manually instead" CTA straight into the Add Transaction form.

**Dividend history**
- Simple list: date, ticker, per-share amount, quantity held, total received. Running total at top.

**Alerts / Watchlist**
- List of current subscriptions (chips: "MTNGH ±5%", "All my holdings"). "+ Add alert" opens a small form (ticker autocomplete + optional threshold; corporate-action alerts on a ticker are automatic once watched).
- Free-tier users seeing the 3-watched-stock cap get an inline upgrade nudge only when they hit the cap, not a persistent banner elsewhere.
- Telegram connection status shown here too, with a re-link button if unlinked.

**Billing / Upgrade**
- Plan cards (Monthly/Quarterly/Annual) with GHS price, "pay with Mobile Money" primary button per card → Paystack checkout redirect.
- Current subscription state (if any): plan, renews-by date, plain-language note: *"SikaTrack doesn't auto-charge your Mobile Money — we'll remind you before this expires."* (sets correct expectations, ties to §6.4).

**Profile**
- Basic account info, Telegram link status, logout, data export (CSV of transactions — cheap to build, high trust value), disclaimer link (§8.2).

### 7.2 Empty states (beyond the zero-transaction dashboard)

- Holdings list with all positions fully sold off: "No open positions right now — your closed positions and realized P&L are in History." (don't let a fully-realized user look like a zero-state new user).
- Alerts with none set: "You're not watching anything yet — alerts on stocks you hold are on by default; add specific price alerts here."
- Statement upload history with none yet: shown inline on the upload screen itself, not a separate empty page.

---

## 8. Security & Compliance

### 8.1 Financial data handling

- **Transport/at-rest:** TLS everywhere (Nginx-terminated, Let's Encrypt); PostgreSQL on the same VPS with disk-level encryption via the VPS provider if available; no financial data (transactions, statements) ever logged in plaintext application logs.
- **Statement files:** original uploaded PDFs stored outside the web root, served only via authenticated Django views (never a public media URL for `statements/`), and deleted or archived-and-access-restricted after a retention policy the founder sets (e.g., keep for audit but require re-auth to view).
- **Least privilege on payment data:** SikaTrack never receives or stores MoMo PINs, card numbers, or full MoMo numbers beyond what Paystack's webhook payload includes for display purposes (e.g., masked number, network) — the checkout redirect ensures the sensitive MoMo PIN entry happens on Paystack's page, not SikaTrack's.
- **Backups:** nightly `pg_dump` to off-VPS storage (S3-compatible or similar), encrypted at rest, since a single-VPS setup has no redundancy otherwise — losing a solo dev's only server without backups means losing every user's portfolio history.
- **Secrets:** Telegram bot token, Paystack keys, Django `SECRET_KEY` in environment variables (`.env`, not committed), never in settings.py directly.

### 8.2 Disclaimers (informational, not licensed investment advice)

SikaTrack is a **portfolio tracking and information tool**, not a licensed investment adviser or broker-dealer under Ghana's Securities Industry Act, 2016 (Act 929), and must not present itself as one. Concretely:
- A persistent, unambiguous disclaimer in the footer and on first login: *"SikaTrack shows information based on data you provide and publicly available/announced data. It is not investment advice, and SikaTrack is not a licensed investment adviser or broker under Ghanaian securities law. Consult a licensed professional before making investment decisions."*
- Never phrase alerts or dashboard copy as recommendations ("you should sell") — only factual/descriptive ("MTNGH is down 6% today", "GCB AGM is in 5 days"). This is a copywriting discipline to enforce everywhere, not a one-time checkbox.
- Price data is explicitly labeled end-of-day/delayed, never implying real-time — both a UX honesty issue (§7) and a compliance one, since implying live market-maker-grade data could misrepresent the product's regulatory posture.
- Terms of Service should state data accuracy is best-effort (dependent on manually-ingested GSE data and user-provided transactions) and SikaTrack isn't liable for decisions made using it.
- **Judgment call, not legal advice:** this document is a product/engineering design, not a legal opinion — before charging money in Ghana, the founder should get a short consult with a Ghanaian lawyer familiar with SEC-Ghana's stance on fintech/investment-adjacent tools, specifically to confirm "portfolio tracker + informational alerts" doesn't cross into needing SEC licensing or GSE approval.

### 8.3 Ghana Data Protection Act basics (Act 843, 2012)

- **Data Protection Commission (DPC) registration:** any entity processing personal data in Ghana as a data controller is expected to register with the DPC. SikaTrack processes personal data (names, phone numbers, financial transaction history) so the founder should register the business as a data controller before or shortly after launch — cheap, mostly-administrative step, worth doing early rather than retrofitting.
- **Consent & purpose limitation:** signup flow should have a clear, separate checkbox for data processing consent (not bundled silently into "I agree to Terms"), and data collected (transactions, phone number for Telegram linking) should only be used for the stated product purpose, not resold/repurposed without fresh consent.
- **Data minimization:** don't collect fields "just in case" (e.g., no need for national ID, full address, etc. for MVP) — keep the User model to what US stories actually require.
- **Right to access/delete:** provide a way for a user to request their data or account deletion (can be a manual email-to-founder process for MVP, doesn't need to be self-service on day one, but must actually be honored promptly when asked).
- **Third-party processors:** Paystack and Telegram both process user data on SikaTrack's behalf (payment details, chat messages) — this should be disclosed in the privacy policy as sub-processors, consistent with Act 843's expectations around data processed by third parties.

---

## 9. MVP Build Plan (6–8 Weeks)

Ordered so the **portfolio tracker is shippable and usable by week 3**, the **Telegram bot lands second**, and statement parsing + payments land once the core loop is proven. Assumes a solo dev working roughly full-time; compress/stretch based on actual hours available.

**Week 1 — Foundation + manual portfolio core**
- Project scaffold (`config`, apps skeleton), custom `User` model, auth (signup/login/reset), deploy pipeline to VPS (even a bare-bones one) working from day one so "deploy" is never a scary unknown at the end.
- `Instrument` + `PriceBar` models, admin CSV upload for daily prices (manual admin action first — no scraper yet).
- `Transaction` model + manual add/edit/delete views, `Holding` recalculation service (§3, `portfolio/services.py`) with unit tests on the cost-basis math specifically (this is the part that must never be silently wrong).

**Week 2 — Dashboard + core UX**
- Dashboard view: holdings table, total value/P&L, allocation breakdown, top movers.
- Zero-state onboarding screens (§7.1).
- Tailwind styling pass on the core flows (auth, dashboard, add transaction) — mobile-first from the start, not retrofitted.
- **Milestone: internally usable** — founder can enter their own real transactions and use it daily.

**Week 3 — Dividends + polish → first shippable version**
- `DividendRecord`/`DividendReceipt` models, admin entry, dividend history view, dashboard integration (total return incl. dividends).
- `CorporateAction` model + admin entry + "upcoming for your holdings" dashboard section (no alerts yet — just visible in-app).
- Bug bash, PWA manifest/service worker for installability, basic error pages.
- **Milestone: soft-launch the portfolio tracker to a small slice of the Telegram audience** (see §10) — this is the "something shippable by week 3" target.

**Week 4 — Telegram bot: linking + corporate action alerts**
- Bot webhook plumbing (§2.3), `/start <code>` account linking flow, `TelegramLink` model.
- `AlertSubscription`, `AlertEvent`, `AlertDelivery` models.
- Corporate action alert generation + daily digest dispatch (free-tier cadence only at this point — don't build the paid/instant path until paid tier exists in week 7).
- **Milestone: bot is live, existing Telegram audience can link accounts and get their first alerts.**

**Week 5 — Price threshold alerts + bot polish**
- Price movement `AlertEvent` generation tied to the daily ingest job.
- Bot commands: `/watch TICKER`, `/unwatch`, `/mystocks`, `/help`.
- Dedup logic (§5.3) hardened with tests — this is exactly the kind of bug that erodes trust fast if a user gets the same alert three times.

**Week 6 — Statement parsing (IC Securities)**
- `StatementUpload`/`ExtractedTransaction` models, upload view, async parse task.
- `ICSecuritiesParser` implementation against real sample statements (get 3–5 real anonymized IC statements from the founder's network before writing the parser — do not build against guessed column layouts).
- Review/confirm UI (§7.1), error handling paths (§4.4).
- **Milestone: statement upload works end-to-end for IC Securities users.**

**Week 7 — Billing**
- `SubscriptionPlan`, `Subscription`, `Payment` models; Paystack checkout integration + webhook handling (§6.3).
- Paid-tier gating: instant alert dispatch path, watchlist cap removal, weekly summary job.
- Renewal reminder job (§6.4).
- **Milestone: a user can actually pay and receive paid-tier alerts.**

**Week 8 — Hardening + public launch**
- Security pass: checklist against §8 (secrets, backups, statement file access control, disclaimer placement, DPC registration status).
- Load-test the daily ingest + alert dispatch jobs against realistic subscriber counts.
- Terms of Service / Privacy Policy / disclaimer copy finalized (ideally lawyer-reviewed per §8.2).
- Public announcement to the full Telegram audience.
- Buffer time — week 8 is deliberately lighter-scoped as slack, since weeks 1–7 are the ones with hard technical dependencies.

**Judgment call:** statement parsing (week 6) lands *after* the bot (weeks 4–5), even though it was listed second in the product scope — the bot converts the founder's existing Telegram audience into linked, retained users almost immediately with much less engineering risk than PDF parsing, so it should ship first to start compounding engagement while the parser (the riskiest, most broker-format-dependent piece) is built.

---

## 10. Validation Plan

Goal: use the existing Telegram audience to de-risk willingness-to-pay **before** the paid tier is fully built (week 7), not after.

**Step 1 — Pre-MVP signal (before/during week 1–3):** Post 1–2 polls in the existing Telegram channel: (a) "Would you use a free tool to track your GSE portfolio's real returns?" (b) "What's most annoying about tracking your GSE investments today?" (open text) — validates the core pain point framing before more weeks are sunk into it, and surfaces language for onboarding copy.

**Step 2 — Soft launch at week 3 milestone:** Invite a small, named subset (20–50 people) of the Telegram audience to use the portfolio tracker directly, framed as "early access, help me find bugs." Watch two things specifically: (a) do they come back after the first session (session 2/3/7-day retention — the real signal, more than signup count), (b) do they actually enter enough transactions to get value, or drop off mid-onboarding (funnel: signup → first transaction → dashboard view).

**Step 3 — Willingness-to-pay probe, before building billing (week 4–5, in parallel with bot rollout):** Do **not** wait for Stripe-style billing infra to test pricing. Instead:
- Announce the *planned* paid tier (instant alerts, unlimited watchlist, weekly summary) in the Telegram channel with the proposed GHS price, and open a simple "reserve your spot" form (even a Google Form or a `/interested` bot command) asking for a manual MoMo pre-payment commitment, OR simply a non-binding "I'd pay X for this" signal.
- Better/stronger signal: run an actual **manual pre-sale** — a small number of highly-engaged users pay via a direct MoMo transfer (no Paystack integration needed yet) for "founding member" access, manually flipped to paid-tier in the DB by the founder. If people won't send GHS 25 by hand to a person they already trust from the Telegram channel, that's a strong signal the price or value prop needs adjusting *before* spending week 7 on Paystack integration.
- Track conversion rate: (# who saw the offer) → (# who expressed interest) → (# who actually paid manually). A steep drop between "interested" and "paid" is the most important number — it's the gap between stated and revealed preference.

**Step 4 — Iterate pricing/packaging before week 7:** If the manual pre-sale conversion is weak, treat week 7 (Paystack integration) as a checkpoint to revisit tier boundaries or price (§6.2 numbers are a hypothesis, not a commitment) rather than building the payment integration on an unvalidated assumption. If it's strong, week 7 becomes "automate what we already proved people will pay for," which is a much safer place to spend engineering time.

**Judgment call:** deliberately substituting a manual MoMo pre-sale for real payment infrastructure during validation — slower and more founder-labor-intensive per transaction, but it tests actual willingness to pay weeks earlier than waiting for billing code to exist, which is the whole point of validating before building.

---

*End of document. Open judgment calls worth founder sign-off before week 1: working name/branding, exact pricing (§6.2), and the legal consult on SEC-Ghana positioning (§8.2).*
