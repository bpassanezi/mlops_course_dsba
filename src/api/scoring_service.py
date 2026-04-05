"""
scoring_service.py
------------------
Helpers related to property price scoring and department market statistics.
"""

from api.market_data import DEPT_STATS


def get_dept_stats(dept: str) -> dict:
    """Return pre-computed market statistics for a department.

    Returns:
        Dict with keys avg_price_per_m2, median_price_per_m2, transaction_count.
        Empty dict if no data is available for the department.
    """
    return DEPT_STATS.get(dept, {})
