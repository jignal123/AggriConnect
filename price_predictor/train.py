# ml_engine/train.py

import pandas as pd
import numpy as np
import pickle
import os
import logging
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
)
from .pipeline import build_full_pipeline, ALL_FEATURE_COLS, TARGET_COL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ml_models", "crop_price_pipeline.pkl"
)


def load_dataset(path=None):
    if path is None:
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "dataset",
            "master_aggriculture_dataset.csv",
        )

    df = pd.read_csv(path, parse_dates=["date"])
    df = df.dropna(subset=[TARGET_COL])
    df = df[df[TARGET_COL] > 10]  # Drop zeros/errors

    # Dynamic IQR Outlier Removal
    Q1, Q3 = df[TARGET_COL].quantile(0.05), df[TARGET_COL].quantile(0.95)
    df = df[
        (df[TARGET_COL] >= (Q1 - 1.5 * (Q3 - Q1)))
        & (df[TARGET_COL] <= (Q3 + 1.5 * (Q3 - Q1)))
    ]

    df = df.sort_values(["district", "Commodity", "date"]).reset_index(drop=True)
    logger.info(f"Dataset cleaned: {df.shape[0]} rows ready for training.")
    return df


def train(dataset_path=None):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    df = load_dataset(dataset_path)

    X = df[[c for c in ALL_FEATURE_COLS if c in df.columns]]
    y = df[TARGET_COL]

    # Time-based split (80/20)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    pipeline = build_full_pipeline()
    logger.info("Training Log-Transformed Ensemble...")
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    logger.info(f"--- MODEL REPORT ---")
    logger.info(f"R² Score: {r2_score(y_test, preds):.4f}")
    logger.info(f"MAE:      ₹{mean_absolute_error(y_test, preds):.2f}")
    logger.info(f"MAPE:     {mean_absolute_percentage_error(y_test, preds)*100:.2f}%")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info(f"Model successfully saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
