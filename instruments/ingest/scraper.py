"""
Post-MVP: automated pull of daily closing prices from a GSE data source,
producing the same CSV shape csv_ingest.ingest_price_csv() expects so both
paths share one ingestion function. Not implemented for MVP — admin CSV
upload (see instruments/admin.py) is the launch path. See PRODUCT_DESIGN.md §2.4.
"""
