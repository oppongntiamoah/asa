import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_receipt_portfolios(apps, schema_editor):
    """Every existing DividendReceipt belonged to a user who — by this
    point — has a 'Default' portfolio (created in portfolio.0003), since
    every receipt originates from that same user's transactions."""
    DividendReceipt = apps.get_model("dividends", "DividendReceipt")
    Portfolio = apps.get_model("portfolio", "Portfolio")

    default_portfolio_by_user = {
        p.user_id: p.id for p in Portfolio.objects.filter(is_default=True)
    }
    for receipt in DividendReceipt.objects.all():
        receipt.portfolio_id = default_portfolio_by_user.get(receipt.user_id)
        receipt.save(update_fields=["portfolio"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("dividends", "0001_initial"),
        ("portfolio", "0003_portfolio"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="dividendreceipt",
            name="portfolio",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="dividend_receipts", to="portfolio.portfolio",
            ),
        ),
        migrations.RunPython(backfill_receipt_portfolios, noop),
        migrations.RemoveConstraint(
            model_name="dividendreceipt",
            name="uniq_receipt_per_user_dividend",
        ),
        migrations.RemoveField(model_name="dividendreceipt", name="user"),
        migrations.AlterField(
            model_name="dividendreceipt",
            name="portfolio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dividend_receipts", to="portfolio.portfolio",
            ),
        ),
        migrations.AddConstraint(
            model_name="dividendreceipt",
            constraint=models.UniqueConstraint(
                fields=("portfolio", "dividend_record"), name="uniq_receipt_per_portfolio_dividend"
            ),
        ),
    ]
