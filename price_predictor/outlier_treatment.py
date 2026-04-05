# ml_engine/outlier_treatment.py
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class Winsorizer(BaseEstimator, TransformerMixin):
    """
    Clips values beyond lower/upper percentile boundaries.

    Why not delete outliers?
        - Price spikes are real events (floods, festivals, strikes)
        - Deleting them makes model blind to extreme conditions
        - Clipping keeps the signal but prevents scaling distortion

    Example: lower=0.02, upper=0.98
        Values below 2nd percentile  → set to 2nd percentile value
        Values above 98th percentile → set to 98th percentile value

    Boundaries are learned ONLY on training data (fit),
    then applied consistently on test/prediction data (transform).
    This prevents data leakage.
    """

    def __init__(self, lower=0.01, upper=0.99):
        self.lower = lower
        self.upper = upper
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}

    def fit(self, X, y=None):
        df = pd.DataFrame(X)
        for col in df.columns:
            self.lower_bounds_[col] = df[col].quantile(self.lower)
            self.upper_bounds_[col] = df[col].quantile(self.upper)
        return self

    def transform(self, X):
        df = pd.DataFrame(X).copy()
        for col in df.columns:
            df[col] = df[col].clip(
                lower=self.lower_bounds_.get(col),
                upper=self.upper_bounds_.get(col),
            )
        return df.values

    def get_feature_names_out(self, input_features=None):
        return input_features
