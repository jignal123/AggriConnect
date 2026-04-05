# ml_engine/government_api.py
# Optimized for production: 2-Step Fetch (No Loops, Instant Retrieval)

import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)
DATA_GOV_BASE_URL = (
    "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
)


def _get_api_key():
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        try:
            from django.conf import settings

            key = getattr(settings, "DATA_GOV_API_KEY", None)
        except Exception:
            pass
    if not key:
        raise ValueError("DATA_GOV_API_KEY not set")
    return key


def _get_cache():
    try:
        from django.core.cache import cache

        return cache
    except Exception:
        return _InMemoryCache()


class _InMemoryCache:
    _store = {}

    def get(self, key):
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires_at = entry
        if datetime.now() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key, value, timeout=3600):
        self._store[key] = (value, datetime.now() + timedelta(seconds=timeout))


def fetch_mandi_prices(district, state, commodity, days=45):
    api_key = _get_api_key()
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    base_params = {
        "api-key": api_key,
        "format": "json",
        "filters[District]": district.title(),
        "filters[State]": state.title(),
        "filters[Commodity]": commodity.title(),
    }

    # ── Step 1: Fast call to get the Total Records ──
    init_params = base_params.copy()
    init_params["limit"] = 1
    init_params["offset"] = 0

    try:
        response = requests.get(DATA_GOV_BASE_URL, params=init_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        total_records = int(data.get("total", 0))
    except Exception as e:
        logger.error(f"Mandi API initial error {response.url}: {e}")
        return pd.DataFrame()

    if total_records == 0:
        return pd.DataFrame()

    # ── Step 2: Jump to the end and fetch the newest chunk ──
    # We grab the last 1000 records. This is 1 API call and guarantees
    # we get the last 45 days, even if there are multiple entries per day.
    fetch_limit = 1000
    offset = max(0, total_records - fetch_limit)

    final_params = base_params.copy()
    final_params["limit"] = fetch_limit
    final_params["offset"] = offset

    try:
        response = requests.get(DATA_GOV_BASE_URL, params=final_params, timeout=15)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])
    except Exception as e:
        logger.error(f"Mandi API final error: {e}")
        return pd.DataFrame()

    if not records:
        return pd.DataFrame()

    # ── Step 3: Process and Filter the Dates ──
    df = pd.DataFrame(records)
    df = df.rename(columns={"Arrival_Date": "date", "Modal_Price": "modal_price"})
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")

    # Drop older dates that fall outside our requested 'days' window
    df = df[df["date"] >= pd.Timestamp(start_date)]
    df = df.dropna(subset=["date", "modal_price"])

    return df.sort_values("date").reset_index(drop=True)


def get_price_lags(district, state, commodity, target_date, days=45):
    """
    Returns exactly the 5 price features required:
    price_lag_7d, price_lag_14d, price_lag_30d, price_7d_avg, price_30d_avg
    """
    cache = _get_cache()
    # Unique cache key per district/commodity
    cache_key = f"price_lags_{district}_{commodity}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    df = fetch_mandi_prices(district, state, commodity, days=days)

    if df.empty:
        logger.warning(
            f"No price data — using zero fallback for {district}/{commodity}"
        )
        return _empty_price_lags()

    df = df.set_index("date").sort_index()
    global_avg = float(df["modal_price"].mean())

    def price_on_lag(lag_days):
        lag_date = target_date - timedelta(days=lag_days)
        nearby = df[
            (df.index >= lag_date - timedelta(days=3))
            & (df.index <= lag_date + timedelta(days=3))
        ]
        return float(nearby["modal_price"].iloc[-1]) if not nearby.empty else None

    def rolling_avg(window_days):
        cutoff = target_date - timedelta(days=window_days)
        window_df = df[df.index >= cutoff]
        return float(window_df["modal_price"].mean()) if not window_df.empty else None

    lags = {
        "price_lag_7d": price_on_lag(7),
        "price_lag_14d": price_on_lag(14),
        "price_lag_30d": price_on_lag(30),
        "price_7d_avg": rolling_avg(7),
        "price_30d_avg": rolling_avg(30),
    }

    # Fill None with global average as fallback
    lags = {k: (v if v is not None else global_avg) for k, v in lags.items()}
    cache.set(cache_key, lags, timeout=60 * 60 * 6)  # Cache for 6 hours
    return lags


def _empty_price_lags():
    return {
        "price_lag_7d": 0.0,
        "price_lag_14d": 0.0,
        "price_lag_30d": 0.0,
        "price_7d_avg": 0.0,
        "price_30d_avg": 0.0,
    }
