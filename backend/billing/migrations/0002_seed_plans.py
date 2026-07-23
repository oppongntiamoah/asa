from django.db import migrations

PLANS = [
    dict(
        code="BASIC", name="Basic Plan", price_ghs="10.00", sort_order=1,
        pdf_processing_credits=2, stock_alert_credits=2, dividend_alert_credits=2,
        data_export_credits=0, max_devices=3,
        feature_bullets=["Email & SMS notifications"],
    ),
    dict(
        code="PRO", name="Pro Plan", price_ghs="50.00", sort_order=2,
        pdf_processing_credits=15, stock_alert_credits=15, dividend_alert_credits=15,
        data_export_credits=3, max_devices=7,
        feature_bullets=[
            "Priority processing and support",
            "Advanced analytics",
            "Analyst Projections",
            "AI-powered financial assistant",
        ],
    ),
    dict(
        code="ULTRA", name="Ultra Plan", price_ghs="250.00", sort_order=3,
        pdf_processing_credits=50, stock_alert_credits=50, dividend_alert_credits=50,
        data_export_credits=10, max_devices=10,
        feature_bullets=[
            "One-on-one guidance (WhatsApp, Zoom, etc)",
            "Personal AI Financial Assistant",
            "Document analysis & upload",
            "Priority processing and support",
            "Advanced analytics",
            "Analyst Projections",
        ],
    ),
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    for plan_data in PLANS:
        Plan.objects.update_or_create(code=plan_data["code"], defaults=plan_data)


def remove_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(code__in=[p["code"] for p in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [migrations.RunPython(seed_plans, remove_plans)]
