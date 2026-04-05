# ml_engine/pipeline.py

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import OneHotEncoder, TargetEncoder
from sklearn.impute import SimpleImputer
from sklearn.base import BaseEstimator, TransformerMixin
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import VotingRegressor

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE GROUPS (Exact match to your finalized dataset)
# ─────────────────────────────────────────────────────────────────────────────
DATE_COL = ["date"]

# The 8 highly correlated numerical features
NUMERICAL_COLS = [
    "price_lag_7d",
    "price_lag_14d",
    "price_lag_30d",
    "price_7d_avg",
    "price_30d_avg",
    "temp_mean_lag_30d",
    "rainfall_mm_30d_avg",
    "rainfall_mm_30d_sum",
]

HIGH_CARDINALITY_COLS = ["STATE", "district", "Market Name"]
LOW_CARDINALITY_COLS = ["Commodity", "Variety", "Grade"]

TARGET_COL = "Modal_Price"
ALL_FEATURE_COLS = (
    DATE_COL + NUMERICAL_COLS + HIGH_CARDINALITY_COLS + LOW_CARDINALITY_COLS
)


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM TRANSFORMERS
# ─────────────────────────────────────────────────────────────────────────────
class DateFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extracts month, day_of_year, and week from the raw date column."""

    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def transform(self, X):
        df = (
            pd.DataFrame(X, columns=["date"]) if isinstance(X, np.ndarray) else X.copy()
        )
        date_series = pd.to_datetime(df.iloc[:, 0])
        return pd.DataFrame(
            {
                "month": date_series.dt.month,
                "day_of_year": date_series.dt.dayofyear,
                "week": date_series.dt.isocalendar().week.astype(int),
            },
        index= df.index
        )

    def get_feature_names_out(self, input_features=None):
        return np.array(["month", "day_of_year", "week"])


class StringCleaner(BaseEstimator, TransformerMixin):
    """Standardizes text columns to prevent mismatch errors."""

    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def transform(self, X):
        df = pd.DataFrame(X).copy()
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
        return df

    def get_feature_names_out(self, input_features=None):
        return input_features


# ─────────────────────────────────────────────────────────────────────────────
# FULL PIPELINE BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_full_pipeline():
    date_transformer = Pipeline(steps=[("extractor", DateFeatureExtractor())])

    num_transformer = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])

    high_cat_transformer = Pipeline(
        steps=[
            ("cleaner", StringCleaner()),
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("target_enc", TargetEncoder(smooth="auto", random_state=42)),
        ]
    )

    low_cat_transformer = Pipeline(
        steps=[
            ("cleaner", StringCleaner()),
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot_enc", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("date", date_transformer, DATE_COL),
            ("num", num_transformer, NUMERICAL_COLS),
            ("high_cat", high_cat_transformer, HIGH_CARDINALITY_COLS),
            ("low_cat", low_cat_transformer, LOW_CARDINALITY_COLS),
        ],
        remainder="drop",
    )
    preprocessor.set_output(transform='pandas')
    # Regularized Ensemble to prevent overfitting
    xgb_model = XGBRegressor(
        objective="reg:absoluteerror",
        n_estimators=800,
        learning_rate=0.03,
        max_depth=7,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        random_state=42,
        n_jobs=-1,
    )

    lgbm_model = LGBMRegressor(
        objective="mae",
        n_estimators=800,
        learning_rate=0.03,
        max_depth=9,
        num_leaves=63,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_samples=20,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    ensemble_model = VotingRegressor(
        estimators=[("xgb", xgb_model), ("lgbm", lgbm_model)], weights=[0.5, 0.5]
    )

    log_target_ensemble = TransformedTargetRegressor(
        regressor=ensemble_model, func=np.log1p, inverse_func=np.expm1
    )

    return Pipeline(
        steps=[("preprocessor", preprocessor), ("log_ensemble", log_target_ensemble)]
    )
