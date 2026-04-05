# ml_engine/weather.py
# Optimized for production: Fetches ONLY Rainfall and Mean Temp.

import requests
import pandas as pd
from datetime import datetime, timedelta
import calendar
import logging

logger = logging.getLogger(__name__)

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# ONLY fetch what we strictly need for the model: Rain and Mean Temp
NASA_PARAMS = "PRECTOTCORR,T2M"

NASA_COL_MAP = {
    "PRECTOTCORR": "rainfall_mm",
    "T2M": "temp_mean",
}


def fetch_nasa_weather(lat, lon, start_date, end_date):
    params = {
        "parameters": NASA_PARAMS,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }
    try:
        response = requests.get(
            NASA_POWER_BASE_URL, params=params, timeout=15
        )  # Faster timeout
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data["properties"]["parameter"])
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
        df.index.name = "date"
        df.reset_index(inplace=True)
        df.rename(columns=NASA_COL_MAP, inplace=True)
        df.replace(-999.0, pd.NA, inplace=True)
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"NASA POWER API error ({lat}, {lon}): {e}")
        return pd.DataFrame()


def get_weather_for_date(lat, lon, target_date):
    """
    Fetches strictly the 3 features required by the final model dataframe:
    - temp_mean_lag_30d
    - rainfall_mm_30d_avg
    - rainfall_mm_30d_sum
    """
    today = datetime.today()
    days_ahead = (target_date - today).days

    if days_ahead <= 14:
        # Fetch last 35 days to ensure we have enough data for 30-day lags/avgs
        start = (today - timedelta(days=35)).strftime("%Y%m%d")
        end = min(target_date, today + timedelta(days=14)).strftime("%Y%m%d")
        df = fetch_nasa_weather(lat, lon, start, end)
    else:
        # 1-year historical fallback
        year = target_date.year - 1
        month = target_date.month
        days = calendar.monthrange(year, month)[1]
        start = f"{year}{month:02d}01"
        end = f"{year}{month:02d}{days:02d}"
        df = fetch_nasa_weather(lat, lon, start, end)
        if not df.empty:
            df["date"] = df["date"] + pd.DateOffset(years=1)

    if df.empty:
        logger.warning(f"No weather for ({lat}, {lon}) — using defaults")
        return _default_weather()

    df = df.sort_values("date").reset_index(drop=True)
    for col in NASA_COL_MAP.values():
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    def lag_val(col, lag_days, default=0.0):
        lag_date = target_date - timedelta(days=lag_days)
        nearby = df[
            (df["date"] >= pd.Timestamp(lag_date - timedelta(days=2)))
            & (df["date"] <= pd.Timestamp(lag_date + timedelta(days=2)))
        ]
        return (
            float(nearby[col].iloc[-1])
            if not nearby.empty and col in nearby.columns
            else default
        )

    def rolling_avg(col, window_days):
        cutoff = pd.Timestamp(target_date - timedelta(days=window_days))
        window = df[df["date"] >= cutoff]
        return (
            float(window[col].fillna(0).mean())
            if not window.empty and col in window.columns
            else 0.0
        )

    def rolling_sum(col, window_days):
        cutoff = pd.Timestamp(target_date - timedelta(days=window_days))
        window = df[df["date"] >= cutoff]
        return (
            float(window[col].fillna(0).sum())
            if not window.empty and col in window.columns
            else 0.0
        )

    return {
        "temp_mean_lag_30d": lag_val("temp_mean", 30, 25.0),
        "rainfall_mm_30d_avg": rolling_avg("rainfall_mm", 30),
        "rainfall_mm_30d_sum": rolling_sum("rainfall_mm", 30),
    }


def _default_weather():
    return {
        "temp_mean_lag_30d": 26.0,
        "rainfall_mm_30d_avg": 0.0,
        "rainfall_mm_30d_sum": 0.0,
    }
