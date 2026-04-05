from api.constants import RENTAL_YIELDS
from api import market_data


def compute_investment_metrics(
    dept: str,
    prediction: float,
    surface: float,
) -> dict:
    """Compute rental yield, monthly rent, market growth, and investment score.

    The investment score (0–10) is a weighted composite of three sub-scores:
      - Yield score  (40%): higher rental yield → higher score
      - Growth score (40%): positive YoY market growth → higher score
      - Affordability score (20%): price below dept average → higher score

    Args:
        dept:       Department code.
        prediction: Estimated property price in EUR.
        surface:    Built surface area in m².

    Returns:
        Dict with keys: rental_yield, monthly_rent, market_growth, investment_score.

    Raises:
        KeyError:   If rental yield or market growth data is missing for the department.
        ValueError: If the department average price/m² is unavailable.
    """
    rental_yield  = RENTAL_YIELDS[dept]   # KeyError propagated to route → HTTP 503
    market_growth = market_data.market_state.market_growth[dept]   # KeyError propagated to route → HTTP 503

    monthly_rent = prediction * (rental_yield / 100) / 12

    # Sub-scores, each clamped to [0, 10]
    yield_score  = min(10, max(0, (rental_yield - 1) / 0.7))   # 1%→0, 8%→10
    growth_score = min(10, max(0, (market_growth + 5) / 1.5))  # -5%→0, +10%→10

    dept_avg = market_data.market_state.dept_stats.get(dept, {}).get("avg_price_per_m2")
    if not dept_avg or dept_avg <= 0:
        raise ValueError(f"Average price/m² unavailable for department '{dept}'.")

    pred_pm2     = prediction / max(surface, 1)
    afford_ratio = pred_pm2 / dept_avg
    afford_score = min(10, max(0, (2 - afford_ratio) * 10))    # 0.5×avg→10, 2×avg→0

    investment_score = round(
        yield_score * 0.4 + growth_score * 0.4 + afford_score * 0.2, 1
    )
    investment_score = min(10.0, max(0.0, investment_score))

    return {
        "rental_yield":     rental_yield,
        "monthly_rent":     round(monthly_rent, 0),
        "market_growth":    market_growth,
        "investment_score": investment_score,
    }
