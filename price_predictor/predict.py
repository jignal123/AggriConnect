# ml_engine/predict.py

import pickle
import pandas as pd
import os
import logging
from .districts import get_coords
from .weather import get_weather_for_date
from .government_api import get_price_lags
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aggriconnect.settings")
logger = logging.getLogger(__name__)
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ml_models", "crop_price_pipeline.pkl"
)

_pipeline = None


def load_pipeline():
    global _pipeline
    if _pipeline is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("Run 'python -m ml_engine.train' first.")
        with open(MODEL_PATH, "rb") as f:
            _pipeline = pickle.load(f)
    return _pipeline


def predict_price(
    district, commodity, target_date, market_name="Local", variety="FAQ", grade="FAQ"
):
    pipeline = load_pipeline()

    coords = get_coords(district)
    if not coords:
        return {"error": f"District '{district}' not found."}

    state = coords["state"].strip()
    district = district.strip().lower()

    # ── Fetch Data via Optimized APIs ──────────────────────────────────────
    weather_data = get_weather_for_date(coords["lat"], coords["lon"], target_date)
    price_lags = get_price_lags(district, state, commodity, target_date)

    # ── Construct Input Row ────────────────────────────────────────────────
    row = pd.DataFrame(
        [
            {
                "date": target_date,
                "STATE": state,
                "district": district,
                "Market Name": market_name.strip().title(),
                "Commodity": commodity.strip().title(),
                "Variety": variety.strip().title(),
                "Grade": grade.strip().title(),
                # Price Lags
                "price_lag_7d": price_lags.get("price_lag_7d", 0.0),
                "price_lag_14d": price_lags.get("price_lag_14d", 0.0),
                "price_lag_30d": price_lags.get("price_lag_30d", 0.0),
                "price_7d_avg": price_lags.get("price_7d_avg", 0.0),
                "price_30d_avg": price_lags.get("price_30d_avg", 0.0),
                # Weather Lags
                "temp_mean_lag_30d": weather_data.get("temp_mean_lag_30d", 25.0),
                "rainfall_mm_30d_avg": weather_data.get("rainfall_mm_30d_avg", 0.0),
                "rainfall_mm_30d_sum": weather_data.get("rainfall_mm_30d_sum", 0.0),
            }
        ]
    )

    # ── Predict ────────────────────────────────────────────────────────────
    predicted = pipeline.predict(row)[0]
    predicted = max(0, float(predicted))

    return {
        "state": state.title(),
        "district": district.title(),
        "market_name": market_name.title(),
        "variety": variety.title(),
        "grade": grade.title(),
        "commodity": commodity.title(),
        "target_date": str(target_date.date()),
        "predicted_price": round(predicted, 2),
        "confidence_low": round(predicted * 0.90, 2),
        "confidence_high": round(predicted * 1.10, 2),
        "price_lag_7d": float(row["price_lag_7d"].iloc[0]),
        "price_lag_14d": float(row["price_lag_14d"].iloc[0]),
        "price_lag_30d": float(row["price_lag_30d"].iloc[0]),
        "price_7d_avg": float(row["price_7d_avg"].iloc[0]),
        "price_30d_avg": float(row["price_30d_avg"].iloc[0]),
        "temp_mean_lag_30d": float(row["temp_mean_lag_30d"].iloc[0]),
        "rainfall_mm_30d_avg": float(row["rainfall_mm_30d_avg"].iloc[0]),
        "rainfall_mm_30d_sum": float(row["rainfall_mm_30d_sum"].iloc[0]),
    }


# if __name__ == "__main__":
#     print("Predicting....")
#     pred = predict_price(
#         district="sangrur",
#         commodity="Potato",
#         target_date=datetime.strptime("2026-03-29", "%Y-%m-%d"),
#         market_name="Malerkotla",
#         variety="Local",
#         grade="Medium",
#     )
#     print(pred)
