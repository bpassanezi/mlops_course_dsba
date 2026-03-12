"""
Unit tests for the data cleaning and EDA helper functions.

Why unit tests?
  - They verify that each function behaves correctly in isolation.
  - When a teammate changes the cleaning logic, these tests catch
    regressions immediately (e.g. accidentally dropping valid rows).
  - They run fast (< 1 s) because they use tiny synthetic DataFrames,
    not the real CSV files.
"""

import sys
import os

# Add src/ to the path so "from model.data_cleaning …" resolves the same way
# it does when running inside the src/ folder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd
import pytest

from model.data_cleaning import ( # type: ignore
    basic_info,
    missing_values_summary,
    numeric_summary,
    categorical_summary,
    target_variable_analysis,
    outlier_detection,
    remove_outliers_iqr,
    clean_data,
    property_type_distribution,
    surface_analysis,
    FEATURE_COLS,
    TARGET,
    VALID_TYPE_LOCAL,
)


# ---------------------------------------------------------------------------
# Helpers – small synthetic DataFrames reused across tests
# ---------------------------------------------------------------------------

def _make_raw_df(n: int = 30) -> pd.DataFrame:
    """Create a small DataFrame that looks like a raw DVF extract."""
    rng = np.random.RandomState(42)
    return pd.DataFrame({
        "nature_mutation": ["Vente"] * n,
        "valeur_fonciere": rng.uniform(50_000, 400_000, n),
        "surface_reelle_bati": rng.uniform(20, 200, n),
        "nombre_pieces_principales": rng.randint(1, 6, n).astype(float),
        "code_departement": rng.choice(["13", "31", "59", "69", "75"], n),
        "type_local": rng.choice(["Appartement", "Maison"], n),
        "longitude": rng.uniform(2.0, 5.0, n),
        "latitude": rng.uniform(43.0, 49.0, n),
        "surface_terrain": rng.uniform(0, 500, n),
        "code_postal": rng.choice([13001, 31000, 59000, 69001, 75001], n),
        "nom_commune": rng.choice(["Paris", "Lyon", "Marseille"], n),
    })


# ---------------------------------------------------------------------------
# Tests for basic_info
# ---------------------------------------------------------------------------

class TestBasicInfo:
    """Tests for the basic_info EDA helper."""

    def test_returns_expected_keys(self):
        df = _make_raw_df()
        result = basic_info(df, "test_set")
        assert set(result.keys()) == {
            "dataset", "rows", "columns", "memory_usage_mb", "duplicated_rows"
        }

    def test_row_and_column_counts(self):
        df = _make_raw_df(n=15)
        result = basic_info(df, "small")
        assert result["rows"] == 15
        assert result["columns"] == df.shape[1]

    def test_dataset_name_is_preserved(self):
        result = basic_info(_make_raw_df(), "my_data")
        assert result["dataset"] == "my_data"


# ---------------------------------------------------------------------------
# Tests for missing_values_summary
# ---------------------------------------------------------------------------

class TestMissingValuesSummary:
    """Tests for the missing_values_summary EDA helper."""

    def test_no_missing_returns_empty(self):
        df = _make_raw_df()  # no NaNs by construction
        result = missing_values_summary(df)
        assert result.empty

    def test_detects_missing_values(self):
        df = _make_raw_df()
        df.loc[0, "longitude"] = np.nan
        df.loc[1, "longitude"] = np.nan
        result = missing_values_summary(df)
        assert "longitude" in result.index
        assert result.loc["longitude", "missing_count"] == 2


# ---------------------------------------------------------------------------
# Tests for numeric_summary
# ---------------------------------------------------------------------------

class TestNumericSummary:
    """Tests for the numeric_summary EDA helper."""

    def test_returns_describe_transpose(self):
        df = _make_raw_df()
        result = numeric_summary(df)
        # describe().T has rows = numeric columns, cols like count/mean/…
        assert "count" in result.columns
        assert "mean" in result.columns

    def test_empty_numeric_returns_empty(self):
        df = pd.DataFrame({"category": ["a", "b", "c"]})
        result = numeric_summary(df)
        assert result.empty


# ---------------------------------------------------------------------------
# Tests for categorical_summary
# ---------------------------------------------------------------------------

class TestCategoricalSummary:
    """Tests for the categorical_summary EDA helper."""

    def test_returns_expected_columns(self):
        df = _make_raw_df()
        result = categorical_summary(df)
        expected_cols = {
            "column", "unique_values", "most_frequent",
            "most_frequent_count", "most_frequent_pct",
        }
        assert expected_cols == set(result.columns)

    def test_detects_categorical_cols(self):
        df = _make_raw_df()
        result = categorical_summary(df)
        cat_names = result["column"].tolist()
        # nature_mutation, code_departement, type_local, nom_commune are strings
        assert "type_local" in cat_names
        assert "nom_commune" in cat_names


# ---------------------------------------------------------------------------
# Tests for target_variable_analysis
# ---------------------------------------------------------------------------

class TestTargetVariableAnalysis:
    """Tests for the target_variable_analysis EDA helper."""

    def test_returns_stats_keys(self):
        df = _make_raw_df()
        result = target_variable_analysis(df)
        expected = {"count", "mean", "median", "std", "min", "max",
                    "skewness", "kurtosis", "q1", "q3", "iqr"}
        assert expected == set(result.keys())

    def test_missing_column_returns_empty(self):
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        result = target_variable_analysis(df)
        assert result == {}

    def test_count_matches_non_null(self):
        df = _make_raw_df(n=20)
        result = target_variable_analysis(df)
        assert result["count"] == 20


# ---------------------------------------------------------------------------
# Tests for outlier_detection
# ---------------------------------------------------------------------------

class TestOutlierDetection:
    """Tests for the outlier_detection EDA helper."""

    def test_returns_expected_keys(self):
        df = _make_raw_df()
        result = outlier_detection(df, "valeur_fonciere")
        expected = {"total_values", "outliers_count", "outliers_pct",
                    "lower_bound", "upper_bound"}
        assert expected == set(result.keys())

    def test_missing_column_returns_empty(self):
        df = _make_raw_df()
        result = outlier_detection(df, "nonexistent_col")
        assert result == {}

    def test_no_outliers_in_uniform_data(self):
        """A tight uniform distribution should have zero IQR-based outliers."""
        df = pd.DataFrame({"x": np.arange(100)})
        result = outlier_detection(df, "x")
        assert result["outliers_count"] == 0


# ---------------------------------------------------------------------------
# Tests for remove_outliers_iqr
# ---------------------------------------------------------------------------

class TestRemoveOutliersIqr:
    """Tests for the remove_outliers_iqr cleaning step."""

    def test_removes_extreme_values(self):
        # Normal range 0-99, plus one extreme outlier
        df = pd.DataFrame({"val": list(range(100)) + [10_000]})
        result = remove_outliers_iqr(df, "val")
        assert 10_000 not in result["val"].values

    def test_keeps_normal_values(self):
        df = pd.DataFrame({"val": list(range(100))})
        result = remove_outliers_iqr(df, "val")
        assert len(result) == 100  # nothing removed


# ---------------------------------------------------------------------------
# Tests for clean_data
# ---------------------------------------------------------------------------

class TestCleanData:
    """Tests for the main clean_data pipeline."""

    def test_output_has_model_columns_only(self):
        """After cleaning, only the target + feature columns should remain."""
        df = _make_raw_df()
        result = clean_data(df)
        expected_cols = set([TARGET] + FEATURE_COLS)
        assert set(result.columns) == expected_cols

    def test_no_missing_values_in_output(self):
        """clean_data drops rows with missing required values."""
        df = _make_raw_df()
        df.loc[0, "valeur_fonciere"] = np.nan
        result = clean_data(df)
        assert result.isnull().sum().sum() == 0

    def test_non_vente_rows_are_removed(self):
        """Only 'Vente' transactions should survive."""
        df = _make_raw_df(n=10)
        df.loc[0, "nature_mutation"] = "Echange"
        df.loc[1, "nature_mutation"] = "Donation"
        result = clean_data(df)
        # Those 2 rows should be gone
        assert len(result) <= 8

    def test_invalid_type_local_removed(self):
        """Rows with unknown type_local values should be filtered out."""
        df = _make_raw_df(n=10)
        df.loc[0, "type_local"] = "Garage"  # not in VALID_TYPE_LOCAL
        result = clean_data(df)
        assert "Garage" not in result["type_local"].values

    def test_non_positive_prices_removed(self):
        """Rows with valeur_fonciere <= 0 should be dropped."""
        df = _make_raw_df(n=10)
        df.loc[0, "valeur_fonciere"] = 0
        df.loc[1, "valeur_fonciere"] = -500
        result = clean_data(df)
        assert (result["valeur_fonciere"] > 0).all()

    def test_duplicates_are_removed(self):
        """Duplicate rows should be dropped."""
        df = _make_raw_df(n=5)
        df = pd.concat([df, df], ignore_index=True)  # double the data
        result = clean_data(df)
        assert len(result) <= 5

    def test_code_departement_is_string(self):
        """code_departement must be a string after cleaning."""
        df = _make_raw_df()
        result = clean_data(df)
        assert pd.api.types.is_string_dtype(result["code_departement"])

    def test_index_is_reset(self):
        """The output index should start at 0 with no gaps."""
        df = _make_raw_df()
        result = clean_data(df)
        assert list(result.index) == list(range(len(result)))


# ---------------------------------------------------------------------------
# Tests for property_type_distribution
# ---------------------------------------------------------------------------

class TestPropertyTypeDistribution:
    """Tests for the property_type_distribution EDA helper."""

    def test_returns_count_and_pct(self):
        df = _make_raw_df()
        result = property_type_distribution(df)
        assert "count" in result.columns
        assert "pct" in result.columns

    def test_missing_column_returns_empty(self):
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = property_type_distribution(df)
        assert result.empty


# ---------------------------------------------------------------------------
# Tests for surface_analysis
# ---------------------------------------------------------------------------

class TestSurfaceAnalysis:
    """Tests for the surface_analysis EDA helper."""

    def test_returns_stats(self):
        df = _make_raw_df()
        result = surface_analysis(df)
        assert "mean" in result
        assert "median" in result

    def test_missing_column_returns_empty(self):
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = surface_analysis(df)
        assert result == {}
