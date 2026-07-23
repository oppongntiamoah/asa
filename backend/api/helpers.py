"""Shared JSON-shaping helpers for api/views/* — kept here rather than
duplicated per module since the same model->dict conversions (Instrument,
Decimal, mover rows) come up in almost every view."""


def instrument_dict(instrument):
    return {
        "id": instrument.id,
        "ticker": instrument.ticker,
        "name": instrument.name,
        "asset_class": instrument.asset_class,
        "sector": instrument.sector,
    }


def decimal_or_none(value):
    return None if value is None else float(value)


def mover_dict(row):
    out = {"instrument": instrument_dict(row["instrument"]), "trade_date": row["trade_date"].isoformat()}
    if "change_pct" in row:
        out["close_price"] = float(row["close_price"])
        out["change_pct"] = float(row["change_pct"])
    if "volume" in row:
        out["volume"] = row["volume"]
        out["close_price"] = float(row["close_price"])
    if "turnover_value" in row:
        out["turnover_value"] = float(row["turnover_value"])
        out["close_price"] = float(row["close_price"])
    return out
