import streamlit as st
import requests
import json
import os
import folium
from streamlit_folium import st_folium
import math

# Set page config for a premium feel
st.set_page_config(
    page_title="Real Estate Price Predictor",
    page_icon="🏠",
    layout="wide"
)

# API URL
DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000")
API_URL = st.sidebar.text_input("API Base URL", value=DEFAULT_API_URL)

# ---------------------------------------------------------------------------
# Fetch department metadata from API
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_departments(api_url):
    try:
        r = requests.get(f"{api_url}/departments/", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_communes(api_url, dept_code):
    try:
        r = requests.get(f"{api_url}/communes/{dept_code}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"communes": [], "zipcodes": []}

@st.cache_data(ttl=600)
def fetch_commune_coords(api_url, dept_code, commune_name):
    try:
        r = requests.get(f"{api_url}/commune_coords/{dept_code}/{commune_name}", timeout=5)
        r.raise_for_status()
        return r.json().get("coords")
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_zipcode_coords(api_url, dept_code, zipcode):
    try:
        r = requests.get(f"{api_url}/zipcode_coords/{dept_code}/{zipcode}", timeout=5)
        r.raise_for_status()
        return r.json().get("coords")
    except Exception:
        return None


# Department main city coords (for distance calculation)
DEPT_MAIN_CITY_COORDS = {
    "13": (43.2965, 5.3698),
    "31": (43.6047, 1.4442),
    "59": (50.6292, 3.0573),
    "69": (45.7640, 4.8357),
    "75": (48.8566, 2.3522),
}
DEPT_MAIN_CITY = {
    "13": "Marseille",
    "31": "Toulouse",
    "59": "Lille",
    "69": "Lyon",
    "75": "Paris",
}
PARIS_COORDS = (48.8566, 2.3522)

def _haversine_km(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        font-size: 1.05em;
    }
    .prediction-card {
        padding: 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        text-align: center;
        color: white;
    }
    .prediction-value {
        font-size: 2.8em;
        font-weight: 800;
        margin: 8px 0;
    }
    .stat-card {
        padding: 18px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 10px;
    }
    .stat-value {
        font-size: 1.8em;
        font-weight: 700;
        color: #ff4b4b;
    }
    .stat-label {
        color: #888;
        font-size: 0.9em;
        margin-top: 4px;
    }
    .distance-row {
        display: flex;
        gap: 24px;
        justify-content: center;
        flex-wrap: wrap;
        margin-top: 8px;
    }
    .distance-item {
        text-align: center;
        min-width: 100px;
    }
    .distance-icon {
        font-size: 1.6em;
        animation: bounce 2s ease-in-out infinite;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    .distance-val {
        font-weight: 600;
        font-size: 1.1em;
        margin-top: 2px;
    }
    .distance-label {
        color: #888;
        font-size: 0.8em;
    }
    .neighborhood-bar {
        height: 14px;
        border-radius: 7px;
        background: linear-gradient(90deg, #c62828 0%, #ff9800 30%, #ffeb3b 50%, #8bc34a 70%, #2e7d32 100%);
        position: relative;
        margin-top: 8px;
    }
    .neighborhood-marker {
        position: absolute;
        top: -4px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: white;
        border: 3px solid #333;
        transform: translateX(-50%);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("🏠 Real Estate Price Predictor")
st.write("Enter the property details below to estimate its market value.")

# Load departments
dept_data = fetch_departments(API_URL)
if dept_data is None:
    st.error("Cannot connect to the API. Make sure the FastAPI server is running.")
    st.stop()

departments = dept_data["departments"]
dept_centers = dept_data["centers"]
dept_zooms = dept_data["zoom_levels"]

# Format department options
dept_options = {code: f"{code} — {name}" for code, name in departments.items()}

# =====================================================================
# INPUT SECTION
# =====================================================================
st.subheader("📋 Property Details")

# Department selection (fixed list)
dept_codes = list(dept_options.keys())
dept_labels = list(dept_options.values())
selected_label = st.selectbox("Department", dept_labels, index=dept_codes.index("75") if "75" in dept_codes else 0)
selected_dept = dept_codes[dept_labels.index(selected_label)]

# Fetch communes for selected department
commune_data = fetch_communes(API_URL, selected_dept)
communes_list = commune_data.get("communes", [])
zipcodes_list = commune_data.get("zipcodes", [])

# Optional city
city_name = st.selectbox("City (optional)", [""] + communes_list, index=0)

# Core inputs
ic1, ic2, ic3 = st.columns(3)
with ic1:
    surface = st.number_input("Surface (m²)", min_value=1.0, value=60.0, step=1.0)
with ic2:
    rooms = st.number_input("Number of Rooms", min_value=1.0, value=3.0, step=1.0)
with ic3:
    type_local = st.selectbox("Property Type", ["Appartement", "Maison"])

# ---------------------------------------------------------------------------
# Interactive Map + Distance
# ---------------------------------------------------------------------------
st.subheader("🗺️ Location Map")

# Determine map center & zoom
map_center = dept_centers.get(selected_dept, [46.6, 2.5])
map_zoom = dept_zooms.get(selected_dept, 6)

location_coords = None

# If city provided, try to zoom further
if city_name:
    coords = fetch_commune_coords(API_URL, selected_dept, city_name)
    if coords:
        map_center = coords
        map_zoom = 13
        location_coords = coords

m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="CartoDB positron")
if location_coords:
    label = city_name if city_name else "Selected location"
    folium.Marker(
        location=location_coords,
        popup=label,
        tooltip=label,
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)
st_folium(m, width=None, height=400, returned_objects=[])

# Distance info
if location_coords:
    lat, lon = location_coords
    dist_paris = _haversine_km(lat, lon, *PARIS_COORDS)
    main_city = DEPT_MAIN_CITY.get(selected_dept, "Main city")
    mc_coords = DEPT_MAIN_CITY_COORDS.get(selected_dept)
    dist_main = _haversine_km(lat, lon, *mc_coords) if mc_coords else None

    ref_city = main_city if selected_dept != "75" else "Paris center"
    ref_dist = dist_main if dist_main is not None else dist_paris

    car_speed, train_speed, bus_speed = 80, 200, 50
    car_time = ref_dist / car_speed * 60
    train_time = ref_dist / train_speed * 60
    bus_time = ref_dist / bus_speed * 60

    st.markdown(f"**Distance to {ref_city}**")
    st.markdown(f"""
    <div class="distance-row">
        <div class="distance-item">
            <div class="distance-icon">🚗</div>
            <div class="distance-val">{car_time:.0f} min</div>
            <div class="distance-label">by car</div>
        </div>
        <div class="distance-item">
            <div class="distance-icon">🚆</div>
            <div class="distance-val">{train_time:.0f} min</div>
            <div class="distance-label">by train</div>
        </div>
        <div class="distance-item">
            <div class="distance-icon">🚌</div>
            <div class="distance-val">{bus_time:.0f} min</div>
            <div class="distance-label">by bus</div>
        </div>
    </div>
    <p style="color:#aaa; font-size:0.75em; text-align:center; margin-top:4px;">
        Straight-line distance: {ref_dist:.0f} km &mdash; times are approximate
    </p>
    """, unsafe_allow_html=True)

# Predict button
st.markdown("---")
run_prediction = st.button("🔍 Run Prediction", use_container_width=True)

# =====================================================================
# OUTPUT SECTION
# =====================================================================
if run_prediction:
    payload = {
        "surface_reelle_bati": surface,
        "nombre_pieces_principales": rooms,
        "code_departement": selected_dept,
        "type_local": type_local,
    }

    try:
        with st.spinner("Calculating..."):
            response = requests.post(f"{API_URL}/scoring/", json=payload)
            response.raise_for_status()
            result = response.json()

            prediction = result.get("score", 0)
            breakdown = result.get("breakdown", {})
            dept_stats = result.get("dept_stats", {})

            # --- Estimated Value Card ---
            st.markdown(f"""
            <div class="prediction-card">
                <h3 style="margin:0; opacity:0.9;">Estimated Value</h3>
                <div class="prediction-value">€{prediction:,.0f}</div>
                <p style="margin:0; opacity:0.8; font-size:0.9em;">Based on the latest model artifacts</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            # --- Price Breakdown + Department Insights side by side ---
            res_left, res_right = st.columns(2, gap="large")

            with res_left:
                if breakdown:
                    def _fmt(val):
                        sign = "+" if val >= 0 else "-"
                        return f"{sign}€{abs(val):,.0f}"

                    base = breakdown.get("base_value", 0)
                    surf_c = breakdown.get("surface_contribution", 0)
                    loc_c = breakdown.get("location_effect", 0)
                    rooms_c = breakdown.get("rooms_adjustment", 0)
                    ptype_c = breakdown.get("property_type_adjustment", 0)

                    st.subheader("📊 Price Breakdown")
                    st.markdown(
                        f"""
                        <div style="background-color:#ffffff; border-radius:10px; padding:24px;
                                    box-shadow:0 2px 8px rgba(0,0,0,0.08); font-family:monospace; font-size:1.05em;">
                            <table style="width:100%; border-collapse:collapse;">
                                <tr>
                                    <td style="padding:8px 0; color:#555;">Base value</td>
                                    <td style="padding:8px 0; text-align:right; font-weight:600; white-space:nowrap;">€{base:,.0f}</td>
                                </tr>
                                <tr>
                                    <td style="padding:8px 0; color:#555;">Surface contribution</td>
                                    <td style="padding:8px 0; text-align:right; font-weight:600; white-space:nowrap;
                                        color:{'#2e7d32' if surf_c >= 0 else '#c62828'};">{_fmt(surf_c)}</td>
                                </tr>
                                <tr>
                                    <td style="padding:8px 0; color:#555;">Location effect</td>
                                    <td style="padding:8px 0; text-align:right; font-weight:600; white-space:nowrap;
                                        color:{'#2e7d32' if loc_c >= 0 else '#c62828'};">{_fmt(loc_c)}</td>
                                </tr>
                                <tr>
                                    <td style="padding:8px 0; color:#555;">Rooms adjustment</td>
                                    <td style="padding:8px 0; text-align:right; font-weight:600; white-space:nowrap;
                                        color:{'#2e7d32' if rooms_c >= 0 else '#c62828'};">{_fmt(rooms_c)}</td>
                                </tr>
                                <tr>
                                    <td style="padding:8px 0; color:#555;">Property type adj.</td>
                                    <td style="padding:8px 0; text-align:right; font-weight:600; white-space:nowrap;
                                        color:{'#2e7d32' if ptype_c >= 0 else '#c62828'};">{_fmt(ptype_c)}</td>
                                </tr>
                                <tr>
                                    <td colspan="2"><hr style="border:none; border-top:2px solid #eee; margin:8px 0;"></td>
                                </tr>
                                <tr>
                                    <td style="padding:8px 0; font-weight:700; font-size:1.1em;">Estimated price</td>
                                    <td style="padding:8px 0; text-align:right; font-weight:700; white-space:nowrap;
                                        font-size:1.1em; color:#ff4b4b;">€{prediction:,.0f}</td>
                                </tr>
                            </table>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with res_right:
                st.subheader("📈 Department Insights")

                avg_pm2 = dept_stats.get("avg_price_per_m2", 0)
                median_pm2 = dept_stats.get("median_price_per_m2", 0)
                tx_count = dept_stats.get("transaction_count", 0)

                dept_avg_total = avg_pm2 * surface if avg_pm2 else 0
                if dept_avg_total > 0:
                    ratio = prediction / dept_avg_total
                    raw_score = 5 + (ratio - 1) * 3
                    neighborhood_score = max(1.0, min(10.0, round(raw_score, 1)))
                else:
                    neighborhood_score = 5.0

                s1, s2 = st.columns(2)
                with s1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">€{avg_pm2:,.0f}</div>
                        <div class="stat-label">Avg. price per m² in department</div>
                    </div>
                    """, unsafe_allow_html=True)
                with s2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">€{median_pm2:,.0f}</div>
                        <div class="stat-label">Median price per m² in department</div>
                    </div>
                    """, unsafe_allow_html=True)

                score_pct = (neighborhood_score - 1) / 9 * 100
                score_color = "#2e7d32" if neighborhood_score >= 7 else "#ff9800" if neighborhood_score >= 4 else "#c62828"
                score_label = "Excellent" if neighborhood_score >= 8 else "Good" if neighborhood_score >= 6 else "Average" if neighborhood_score >= 4 else "Below average"

                st.markdown(f"""
                <div class="stat-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:600; font-size:1.05em;">Neighborhood Score</span>
                        <span style="font-weight:700; font-size:1.4em; color:{score_color};">{neighborhood_score}/10</span>
                    </div>
                    <div class="neighborhood-bar">
                        <div class="neighborhood-marker" style="left:{score_pct}%;"></div>
                    </div>
                    <div style="text-align:right; margin-top:6px; color:{score_color}; font-weight:500;">{score_label}</div>
                    <div class="stat-label" style="margin-top:6px;">
                        Based on {tx_count:,} transactions in {departments.get(selected_dept, selected_dept)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- Comparable Properties ---
            st.markdown("")
            st.subheader("🏘️ Comparable Properties")
            try:
                comp_resp = requests.get(f"{API_URL}/comparables/", params={
                    "code_departement": selected_dept,
                    "surface_reelle_bati": surface,
                    "nombre_pieces_principales": rooms,
                    "type_local": type_local,
                    "n": 5,
                }, timeout=10)
                comp_resp.raise_for_status()
                comparables = comp_resp.json().get("comparables", [])

                if comparables:
                    # Build HTML table
                    rows_html = ""
                    for i, comp in enumerate(comparables):
                        bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
                        diff = comp["price"] - prediction
                        diff_color = "#2e7d32" if diff >= 0 else "#c62828"
                        diff_sign = "+" if diff >= 0 else "-"
                        rows_html += (
                            f'<tr style="background-color:{bg};">'
                            f'<td style="padding:10px 12px;">{comp["type"]}</td>'
                            f'<td style="padding:10px 12px; text-align:right; white-space:nowrap;">€{comp["price"]:,.0f}</td>'
                            f'<td style="padding:10px 12px; text-align:right;">{comp["surface"]:.0f} m²</td>'
                            f'<td style="padding:10px 12px; text-align:center;">{comp["rooms"]}</td>'
                            f'<td style="padding:10px 12px; text-align:right; white-space:nowrap;">€{comp["price_per_m2"]:,.0f}</td>'
                            f'<td style="padding:10px 12px; text-align:right; white-space:nowrap; color:{diff_color}; font-weight:600;">{diff_sign}€{abs(diff):,.0f}</td>'
                            f'</tr>'
                        )

                    dept_name = departments.get(selected_dept, selected_dept)
                    comp_html = (
                        '<div style="background-color:#ffffff; border-radius:10px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.08); overflow-x:auto;">'
                        '<table style="width:100%; border-collapse:collapse; font-size:0.95em;">'
                        '<thead><tr style="border-bottom:2px solid #eee;">'
                        '<th style="padding:10px 12px; text-align:left; color:#888; font-weight:600;">Type</th>'
                        '<th style="padding:10px 12px; text-align:right; color:#888; font-weight:600;">Price</th>'
                        '<th style="padding:10px 12px; text-align:right; color:#888; font-weight:600;">Surface</th>'
                        '<th style="padding:10px 12px; text-align:center; color:#888; font-weight:600;">Rooms</th>'
                        '<th style="padding:10px 12px; text-align:right; color:#888; font-weight:600;">€/m²</th>'
                        '<th style="padding:10px 12px; text-align:right; color:#888; font-weight:600;">vs Estimate</th>'
                        '</tr></thead>'
                        f'<tbody>{rows_html}</tbody>'
                        '</table>'
                        f'<p style="color:#aaa; font-size:0.75em; margin:10px 0 0 0;">Showing {len(comparables)} most similar properties in {dept_name}</p>'
                        '</div>'
                    )
                    st.markdown(comp_html, unsafe_allow_html=True)
                else:
                    st.info("No comparable properties found in this department.")
            except Exception:
                st.warning("Could not load comparable properties.")

            # --- Investment Insight ---
            st.markdown("")
            st.subheader("💰 Investment Insight")
            try:
                inv_resp = requests.get(f"{API_URL}/investment/", params={
                    "code_departement": selected_dept,
                    "prediction": prediction,
                    "surface_reelle_bati": surface,
                }, timeout=10)
                inv_resp.raise_for_status()
                inv = inv_resp.json()

                rental_yield = inv["rental_yield"]
                monthly_rent = inv["monthly_rent"]
                market_growth = inv["market_growth"]
                inv_score = inv["investment_score"]

                growth_color = "#2e7d32" if market_growth >= 0 else "#c62828"
                growth_sign = "+" if market_growth >= 0 else ""
                score_color = "#2e7d32" if inv_score >= 7 else "#ff9800" if inv_score >= 4 else "#c62828"
                score_label = "Excellent" if inv_score >= 8 else "Strong" if inv_score >= 6.5 else "Moderate" if inv_score >= 4 else "Weak"
                score_pct = inv_score / 10 * 100

                ic1, ic2, ic3 = st.columns(3)
                with ic1:
                    st.markdown(
                        '<div class="stat-card">'
                        f'<div class="stat-value">{rental_yield:.1f}%</div>'
                        '<div class="stat-label">Est. Gross Rental Yield</div>'
                        f'<div style="color:#888; font-size:0.85em; margin-top:4px;">≈ €{monthly_rent:,.0f}/month</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                with ic2:
                    st.markdown(
                        '<div class="stat-card">'
                        f'<div class="stat-value" style="color:{growth_color};">{growth_sign}{market_growth:.1f}%</div>'
                        '<div class="stat-label">Market Growth (Last Year)</div>'
                        f'<div style="color:#888; font-size:0.85em; margin-top:4px;">Median €/m² YoY change</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                with ic3:
                    st.markdown(
                        '<div class="stat-card">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                        f'<span style="font-weight:600; font-size:1.05em;">Score</span>'
                        f'<span style="font-weight:700; font-size:1.4em; color:{score_color};">{inv_score}/10</span>'
                        f'</div>'
                        '<div class="neighborhood-bar">'
                        f'<div class="neighborhood-marker" style="left:{score_pct}%;"></div>'
                        '</div>'
                        f'<div style="text-align:right; margin-top:6px; color:{score_color}; font-weight:500;">{score_label}</div>'
                        '<div class="stat-label" style="margin-top:4px;">Yield + Growth + Affordability</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                st.warning("Could not load investment insight.")

            st.balloons()

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {e}")


st.divider()
st.caption("Developed for MLOps Course DSBA")
