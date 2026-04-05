"""
geography_service.py
--------------------
Helpers for commune names, postcodes, and coordinate lookups.
"""

from api.market_data import COMMUNE_DATA, COMMUNE_COORDS


def get_communes_for_dept(dept_code: str) -> dict:
    """Return communes and zipcodes for a department.

    Returns:
        Dict with keys 'communes' (list of str) and 'zipcodes' (list of str).
        Empty lists if the department is not found.
    """
    return COMMUNE_DATA.get(dept_code, {"communes": [], "zipcodes": []})


def get_coords_for_commune(dept_code: str, commune_name: str) -> list | None:
    """Return [lat, lon] for a commune, or None if unknown."""
    return COMMUNE_COORDS.get(f"{dept_code}_{commune_name}")


def get_coords_for_zipcode(dept_code: str, zipcode: str) -> list | None:
    """Return [lat, lon] for a postcode, or None if unknown."""
    return COMMUNE_COORDS.get(f"{dept_code}_zip_{zipcode}")
