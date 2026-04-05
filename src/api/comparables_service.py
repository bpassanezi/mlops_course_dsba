from api import market_data


def find_comparables(
    dept: str,
    surface: float,
    rooms: float,
    type_local: str,
    n: int = 5,
) -> list[dict]:
    """Return the N most similar real transactions in the same department.

    Similarity is measured as normalised Euclidean distance on (surface, rooms).
    If enough same-type transactions exist the search is restricted to matching types.

    Args:
        dept:       Department code.
        surface:    Target surface area in m².
        rooms:      Target number of main rooms.
        type_local: Property type (e.g. 'Appartement', 'Maison').
        n:          Number of comparables to return (default 5).

    Returns:
        List of dicts with keys: price, surface, rooms, type, price_per_m2.
        Empty list if no data is available.
    """
    if market_data.market_state.cleaned_df.empty:
        return []

    sub = market_data.market_state.cleaned_df[market_data.market_state.cleaned_df["code_departement"] == dept].copy()

    same_type = sub[sub["type_local"] == type_local]
    if len(same_type) >= n:
        sub = same_type

    sub["_surf_diff"] = ((sub["surface_reelle_bati"] - surface) / max(surface, 1)) ** 2
    sub["_room_diff"] = ((sub["nombre_pieces_principales"] - rooms) / max(rooms, 1)) ** 2
    sub["_dist"] = sub["_surf_diff"] + sub["_room_diff"]

    top = sub.nsmallest(n, "_dist")

    return [
        {
            "price":       round(float(row["valeur_fonciere"]), 0),
            "surface":     round(float(row["surface_reelle_bati"]), 1),
            "rooms":       int(row["nombre_pieces_principales"]),
            "type":        row["type_local"],
            "price_per_m2": round(float(row["price_per_m2"]), 0),
        }
        for _, row in top.iterrows()
    ]
