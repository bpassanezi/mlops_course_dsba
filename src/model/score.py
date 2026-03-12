import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
)


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    prefix: str = "",
) -> dict:
    """Compute regression metrics and return them as a dict.

    Metrics:
      - MAE  (Mean Absolute Error)
      - RMSE (Root Mean Squared Error)
      - MedAE (Median Absolute Error)
      - MAPE (Mean Absolute Percentage Error, %)
      - R²   (Coefficient of Determination)
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    medae = median_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    r2 = r2_score(y_true, y_pred)

    results = {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "medae": round(medae, 2),
        "mape_pct": round(mape, 2),
        "r2": round(r2, 4),
    }

    if prefix:
        results = {f"{prefix}_{k}": v for k, v in results.items()}

    return results
