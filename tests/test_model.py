"""
Unit tests for the model training and scoring code.

Why unit tests?
  - They verify that individual functions behave correctly in isolation.
  - When someone on the team changes the code, the tests catch regressions
    immediately (e.g. a refactor that accidentally breaks feature engineering).
  - They run fast (seconds) because they use small synthetic data, not the
    full dataset.
"""

import sys
import os

# Add the src/ folder to the Python path so that "from model.score …" works
# exactly as it does when running inside src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

# Import the functions we want to test
from model.train import ( # type: ignore
    preprocess_data,
    build_pipeline,
    FEATURE_COLS,
    ENGINEERED_FEATURES,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)
from model.score import evaluate_model # type: ignore


# ---------------------------------------------------------------------------
# Helpers – small synthetic DataFrames used across several tests
# ---------------------------------------------------------------------------

def _make_sample_df(n: int = 20) -> pd.DataFrame:
    """Create a small synthetic DataFrame that mimics the cleaned dataset."""
    rng = np.random.RandomState(42)
    return pd.DataFrame({
        "surface_reelle_bati": rng.uniform(20, 200, n),
        "nombre_pieces_principales": rng.randint(1, 6, n).astype(float),
        "code_departement": rng.choice([13, 31, 59, 69, 75], n),
        "type_local": rng.choice(["Appartement", "Maison"], n),
        "valeur_fonciere": rng.uniform(50_000, 500_000, n),
    })


# ---------------------------------------------------------------------------
# Tests for preprocess_data
# ---------------------------------------------------------------------------

class TestPreprocessData:
    """Tests for the preprocess_data function."""

    def test_adds_engineered_features(self):
        """preprocess_data should create surface_per_room and log_surface."""
        df = _make_sample_df()
        result = preprocess_data(df)

        assert "surface_per_room" in result.columns
        assert "log_surface" in result.columns

    def test_surface_per_room_values(self):
        """surface_per_room should equal surface / rooms."""
        df = _make_sample_df()
        result = preprocess_data(df)
        expected = df["surface_reelle_bati"] / df["nombre_pieces_principales"]
        pd.testing.assert_series_equal(
            result["surface_per_room"], expected, check_names=False
        )

    def test_log_surface_values(self):
        """log_surface should equal log1p(surface)."""
        df = _make_sample_df()
        result = preprocess_data(df)
        expected = np.log1p(df["surface_reelle_bati"])
        np.testing.assert_array_almost_equal(
            result["log_surface"].values, expected.values # type: ignore
        )

    def test_code_departement_becomes_string(self):
        """code_departement should be cast to str (needed for OneHotEncoder)."""
        df = _make_sample_df()
        result = preprocess_data(df)
        assert pd.api.types.is_string_dtype(result["code_departement"])

    def test_preserves_row_count(self):
        """preprocess_data should not add or remove rows."""
        df = _make_sample_df(n=15)
        result = preprocess_data(df)
        assert len(result) == 15


# ---------------------------------------------------------------------------
# Tests for build_pipeline
# ---------------------------------------------------------------------------

class TestBuildPipeline:
    """Tests for the build_pipeline function."""

    def test_returns_pipeline(self):
        """build_pipeline should return a sklearn Pipeline."""
        pipe = build_pipeline()
        assert isinstance(pipe, Pipeline)

    def test_pipeline_has_preprocessor_and_regressor(self):
        """The pipeline should have exactly two steps: preprocessor + regressor."""
        pipe = build_pipeline()
        step_names = [name for name, _ in pipe.steps]
        assert step_names == ["preprocessor", "regressor"]

    def test_pipeline_can_fit_and_predict(self):
        """The pipeline should fit on synthetic data and return predictions."""
        df = _make_sample_df(n=50)
        df = preprocess_data(df)

        all_features = FEATURE_COLS + ENGINEERED_FEATURES
        X = df[all_features]
        y = df["valeur_fonciere"]

        pipe = build_pipeline()
        pipe.fit(X, y)

        preds = pipe.predict(X)
        assert len(preds) == len(X)
        assert not np.any(np.isnan(preds))


# ---------------------------------------------------------------------------
# Tests for evaluate_model (scoring)
# ---------------------------------------------------------------------------

class TestEvaluateModel:
    """Tests for the evaluate_model function."""

    def test_returns_expected_keys(self):
        """evaluate_model should return MAE, RMSE, MedAE, MAPE, R²."""
        y_true = np.array([100, 200, 300])
        y_pred = np.array([110, 190, 310])

        result = evaluate_model(y_true, y_pred)
        expected_keys = {"mae", "rmse", "medae", "mape_pct", "r2"}
        assert set(result.keys()) == expected_keys

    def test_prefix_is_applied(self):
        """When a prefix is given, all keys should start with that prefix."""
        y_true = np.array([100, 200, 300])
        y_pred = np.array([110, 190, 310])

        result = evaluate_model(y_true, y_pred, prefix="train")
        for key in result:
            assert key.startswith("train_")

    def test_perfect_predictions(self):
        """When predictions match exactly, MAE and RMSE should be 0 and R² should be 1."""
        y = np.array([100.0, 200.0, 300.0])
        result = evaluate_model(y, y)

        assert result["mae"] == 0.0
        assert result["rmse"] == 0.0
        assert result["r2"] == 1.0

    def test_metrics_are_numeric(self):
        """All returned metric values should be numbers (int or float)."""
        y_true = np.array([100, 200, 300, 400])
        y_pred = np.array([120, 180, 320, 380])

        result = evaluate_model(y_true, y_pred)
        for value in result.values():
            assert isinstance(value, (int, float))
