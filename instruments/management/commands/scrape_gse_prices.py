from django.core.management.base import BaseCommand

from instruments.ingest.scraper import GSEScraperError, scrape_and_ingest


class Command(BaseCommand):
    help = "Fetches the latest trading day's closing prices from GSE's website and ingests them."

    def handle(self, *args, **options):
        try:
            result = scrape_and_ingest()
        except GSEScraperError as exc:
            self.stderr.write(self.style.ERROR(f"Scrape failed: {exc}"))
            self.stderr.write("Falling back to manual CSV upload is the reliable path for today.")
            raise SystemExit(1)

        if result.error_count:
            self.stdout.write(self.style.WARNING(
                f"Ingested {result.row_count} rows with {result.error_count} errors:"
            ))
            for error in result.errors:
                self.stdout.write(f"  {error}")
        else:
            self.stdout.write(self.style.SUCCESS(f"Ingested {result.row_count} rows cleanly."))
