import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_default_portfolios(apps, schema_editor):
    """Every existing user gets one 'Default' portfolio containing all of
    their current transactions/holdings/cash balance, so nothing breaks
    and no one loses data when portfolios go from implicit (one per user)
    to explicit (a Portfolio row a user can add more of)."""
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Portfolio = apps.get_model("portfolio", "Portfolio")
    Transaction = apps.get_model("portfolio", "Transaction")
    Holding = apps.get_model("portfolio", "Holding")
    CashBalance = apps.get_model("portfolio", "CashBalance")

    for user in User.objects.all():
        portfolio = Portfolio.objects.create(user=user, name="Default", is_default=True)
        Transaction.objects.filter(user=user).update(portfolio=portfolio)
        Holding.objects.filter(user=user).update(portfolio=portfolio)
        CashBalance.objects.filter(user=user).update(portfolio=portfolio)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("portfolio", "0002_cashbalance"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Portfolio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="The portfolio a user lands on when no other is selected. Exactly one per user.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="portfolios",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddField(
            model_name="transaction",
            name="portfolio",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions", to="portfolio.portfolio",
            ),
        ),
        migrations.AddField(
            model_name="holding",
            name="portfolio",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="holdings", to="portfolio.portfolio",
            ),
        ),
        migrations.AddField(
            model_name="cashbalance",
            name="portfolio",
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="cash_balance", to="portfolio.portfolio",
            ),
        ),
        migrations.RunPython(backfill_default_portfolios, noop),
        migrations.RemoveConstraint(
            model_name="holding",
            name="uniq_holding_per_user_instrument",
        ),
        migrations.RemoveIndex(
            model_name="transaction",
            name="portfolio_t_user_id_dbf3b3_idx",
        ),
        migrations.RemoveField(model_name="transaction", name="user"),
        migrations.RemoveField(model_name="holding", name="user"),
        migrations.RemoveField(model_name="cashbalance", name="user"),
        migrations.AlterField(
            model_name="transaction",
            name="portfolio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions", to="portfolio.portfolio",
            ),
        ),
        migrations.AlterField(
            model_name="holding",
            name="portfolio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="holdings", to="portfolio.portfolio",
            ),
        ),
        migrations.AlterField(
            model_name="cashbalance",
            name="portfolio",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cash_balance", to="portfolio.portfolio",
            ),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["portfolio", "instrument", "trade_date"], name="portfolio_t_portf_trd_idx"),
        ),
        migrations.AddConstraint(
            model_name="holding",
            constraint=models.UniqueConstraint(
                fields=("portfolio", "instrument"), name="uniq_holding_per_portfolio_instrument"
            ),
        ),
    ]
