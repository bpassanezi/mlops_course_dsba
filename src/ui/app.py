import streamlit as st
import requests
import json
import os
import folium
from streamlit_folium import st_folium
import math

# Set page config for a premium feel
st.set_page_config(
    page_title="ImmoPrice",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API Setup
DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000")
API_URL = DEFAULT_API_URL

# --- Initialize Session State for Pagination ---
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# ---------------------------------------------------------------------------
# Fetch metadata from API 
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

DEPT_MAIN_CITY_COORDS = {
    "13": (43.2965, 5.3698), "31": (43.6047, 1.4442),
    "59": (50.6292, 3.0573), "69": (45.7640, 4.8357),
    "75": (48.8566, 2.3522),
}
DEPT_MAIN_CITY = {
    "13": "Marseille", "31": "Toulouse", "59": "Lille",
    "69": "Lyon", "75": "Paris",
}
PARIS_COORDS = (48.8566, 2.3522)

# ---------------------------------------------------------------------------
# Custom CSS (Top Nav + App Styling)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import a premium Serif font (Merriweather) and clean Sans-Serif (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&family=Inter:wght@400;500;600&display=swap');
    
    .block-container { padding-top: 0rem !important; }
    
    /* Base typography */
    html, body, [class*="css"] { 
        font-family: 'Inter', -apple-system, sans-serif; 
        color: #111111;
    }
    
    /* Apply Serif to Streamlit Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Merriweather', Georgia, serif !important;
        font-weight: 400 !important;
        color: #111111 !important;
        letter-spacing: -0.01em;
    }

    /* Hide the default Streamlit header */
    [data-testid="stHeader"] { display: none !important; }

    /* --- MINIMALIST NAVBAR --- */
    .top-navbar {
        background-color: #FDFCFB; 
        padding: 1.2rem 2rem; 
        margin: 0rem -4rem 2rem -4rem;
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-bottom: 1px solid #EAEAEA;
    }
    .top-navbar .logo { 
        color: #111111; 
        font-size: 1.3em; 
        font-family: 'Merriweather', serif;
        font-weight: 700; 
        display: flex; 
        align-items: center; 
        gap: 12px;
    }
    .top-navbar .logo span { color: #8A857D; font-weight: 400; font-style: italic; }
    .nav-links { display: flex; gap: 32px; }
    .nav-links div { 
        color: #666666; 
        font-weight: 500; 
        font-size: 0.9em; 
        cursor: pointer; 
        transition: color 0.2s ease; 
    }
    .nav-links div:hover { color: #111111; }

    /* --- BUTTONS --- */
    .stButton>button {
        width: 100%; 
        border-radius: 4px; 
        height: 2.8em; 
        background-color: #2A2927;
        color: #FDFCFB; 
        font-weight: 500; 
        font-size: 1em; 
        border: 1px solid #2A2927; 
        transition: all 0.2s ease;
    }
    .stButton>button:hover { 
        background-color: #403E3A; 
        border-color: #403E3A;
        color: white;
    }
    /* Nav Buttons overrides */
    .nav-btn>button { 
        background-color: #FDFCFB; 
        color: #111111; 
        border: 1px solid #D6D3CD; 
    }
    .nav-btn>button:hover { 
        background-color: #F4F2EE; 
        border-color: #111111; 
        color: #111111;
    }

    /* --- CARDS & UI ELEMENTS --- */
    .prediction-card {
        padding: 32px 24px; 
        background-color: #FFFFFF;
        border-radius: 8px; 
        text-align: center; 
        border: 1px solid #EAEAEA;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .prediction-value { 
        font-family: 'Merriweather', serif;
        font-size: 3em; 
        font-weight: 400; 
        margin: 12px 0; 
        color: #111111; 
    }
    .stat-card {
        padding: 20px; 
        background-color: #FFFFFF; 
        border-radius: 8px;
        border: 1px solid #EAEAEA; 
        text-align: center; 
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .stat-value { font-size: 1.6em; font-weight: 500; color: #111111; }
    .stat-label { color: #666666; font-size: 0.85em; font-weight: 500; margin-top: 6px; }
    
    /* Progress Indicator */
    .step-indicator { display: flex; justify-content: center; gap: 6px; margin-bottom: 2rem; }
    .step-dot { height: 4px; width: 32px; border-radius: 2px; background-color: #EAEAEA; transition: all 0.3s;}
    .step-dot.active { background-color: #2A2927; }
</style>

<div class="top-navbar">
    <div class="logo">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="#111111" stroke-width="1.5"/>
            <path d="M8 12L12 8L16 12" stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 16V8" stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Immo<span>Price</span>
    </div>
    <div class="nav-links">
        <div style="color: #111111; border-bottom: 1px solid #111111; padding-bottom: 2px;">Valuation</div>
    </div>
</div>

<div style="
    background: linear-gradient(90deg, #1E293B 0%, #2A2927 100%);
    color: #F8FAFC;
    padding: 18px 2rem;
    margin: 0rem -4rem 2rem -4rem;
    text-align: center;
    border-bottom: 1px solid #0F172A;
">
    <p style="margin:0; font-size:1.15em; font-family:'Merriweather', serif; font-style:italic; letter-spacing:0.01em;">
        Know what a property is truly worth — before you make your move.
    </p>
    <p style="margin:6px 0 0; font-size:0.82em; color:#94A3B8; font-family:'Inter', sans-serif; letter-spacing:0.04em; text-transform:uppercase;">
        Data-driven valuations · Real market comparisons · Investment intelligence
    </p>
</div>
""", unsafe_allow_html=True)
# ---------------------------------------------------------------------------
# Data Loading & Layout
# ---------------------------------------------------------------------------
dept_data = fetch_departments(API_URL)
if dept_data is None:
    st.error("Cannot connect to the API.")
    st.stop()

departments = dept_data["departments"]
dept_centers = dept_data["centers"]
dept_zooms = dept_data["zoom_levels"]
dept_options = {code: f"{code} - {name}" for code, name in departments.items()}

# Layout
main_col1, main_col2 = st.columns([1, 1.4], gap="large")

with main_col1:
    st.info("Enter property details and click 'Generate Estimate' to build the report.")
    st.markdown("<h3 style='color: #1E293B; font-weight: 600; margin-top: 0;'>Property Parameters</h3>", unsafe_allow_html=True)
    
    dept_codes = list(dept_options.keys())
    dept_labels = list(dept_options.values())
    selected_label = st.selectbox("Department", dept_labels, index=dept_codes.index("75") if "75" in dept_codes else 0)
    selected_dept = dept_codes[dept_labels.index(selected_label)]
    
    commune_data = fetch_communes(API_URL, selected_dept)
    communes_list = commune_data.get("communes", [])
    city_name = st.selectbox("City (Optional)", [""] + communes_list, index=0)
    
    ic1, ic2 = st.columns(2)
    with ic1:
        surface = st.number_input("Surface Area (m²)", min_value=1.0, value=60.0, step=1.0)
        rooms = st.number_input("Total Rooms", min_value=1.0, value=3.0, step=1.0)
    with ic2:
        type_local = st.selectbox("Property Type", ["Appartement", "Maison"])
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Generate Estimate", use_container_width=True):
        payload = {
            "surface_reelle_bati": surface,
            "nombre_pieces_principales": rooms,
            "code_departement": selected_dept,
            "type_local": type_local,
        }
        with st.spinner("Compiling full market report..."):
            try:
                # 1. Get Score & Breakdown
                score_resp = requests.post(f"{API_URL}/scoring/", json=payload).json()
                prediction = score_resp.get("score", 0)
                
                # 2. Get Comparables
                comp_resp = requests.get(f"{API_URL}/comparables/", params={
                    "code_departement": selected_dept, "surface_reelle_bati": surface,
                    "nombre_pieces_principales": rooms, "type_local": type_local, "n": 5
                }).json()
                
                # 3. Get Investment data
                inv_resp = {}
                try:
                    inv_resp = requests.get(f"{API_URL}/investment/", params={
                        "code_departement": selected_dept, "prediction": prediction, "surface_reelle_bati": surface
                    }).json()
                except:
                    pass # Handled gracefully later
                
                # Save ALL data to session state
                st.session_state.report_data = {
                    "score_data": score_resp,
                    "comp_data": comp_resp.get("comparables", []),
                    "inv_data": inv_resp,
                    "city": city_name,
                    "surface": surface,
                    "dept_name": departments.get(selected_dept, selected_dept)
                }
                st.session_state.current_page = 1 
            except Exception as e:
                st.error(f"Error compiling report: {e}")

with main_col2:
    if st.session_state.report_data is None:
        # Initial Empty State Map
        st.markdown("<h3 style='color: #1E293B; font-weight: 600; margin-top: 0;'>Location Overview</h3>", unsafe_allow_html=True)
        map_center = dept_centers.get(selected_dept, [46.6, 2.5])
        if city_name:
            coords = fetch_commune_coords(API_URL, selected_dept, city_name)
            if coords: map_center = coords
                
        m = folium.Map(location=map_center, zoom_start=11 if city_name else 6, tiles="CartoDB positron")
        st_folium(m, width=None, height=450, returned_objects=[])

    else:
        # --- CAROUSEL HEADER ---
        st.markdown("<h3 style='color: #1E293B; font-weight: 600; margin-top: 0;'>Valuation Report</h3>", unsafe_allow_html=True)
        current = st.session_state.current_page
        
        # Dots
        st.markdown(f"""
        <div class="step-indicator">
            <div class="step-dot {'active' if current==1 else ''}"></div>
            <div class="step-dot {'active' if current==2 else ''}"></div>
            <div class="step-dot {'active' if current==3 else ''}"></div>
        </div>
        """, unsafe_allow_html=True)

        data = st.session_state.report_data
        prediction = data["score_data"].get("score", 0)
        
        # ==========================================================
        # PAGE 1: VALUATION & BREAKDOWN
        # ==========================================================
        if current == 1:
            st.markdown(f"""
            <div class="prediction-card">
                <h3 style="margin:0; font-weight:500; color:#94A3B8; text-transform:uppercase; letter-spacing:0.05em; font-size:1em;">Projected Market Value</h3>
                <div class="prediction-value">€{prediction:,.0f}</div>
                <p style="margin:0; color:#64748B; font-size:0.9em;">Based on real-time market artifacts</p>
            </div>
            <p style="color:#64748B; font-size:0.85em; margin-top:12px; line-height:1.5;">
                This is the estimated selling price of the property. It is calculated by analyzing thousands of
                real property sales across France and considering the size, number of rooms, location, and
                whether it is a flat or a house.
            </p>
            """, unsafe_allow_html=True)
            
            breakdown = data["score_data"].get("breakdown", {})
            if breakdown:
                def _fmt(val):
                    return f"{'+' if val >= 0 else '-'}€{abs(val):,.0f}"

                base = breakdown.get("base_value", 0)
                surf_c = breakdown.get("surface_contribution", 0)
                loc_c = breakdown.get("location_effect", 0)
                rooms_c = breakdown.get("rooms_adjustment", 0)
                ptype_c = breakdown.get("property_type_adjustment", 0)

                st.markdown("<br><h4 style='color: #1E293B; font-weight: 600;'>Valuation Breakdown</h4>", unsafe_allow_html=True)
                st.markdown('<p style="color:#64748B; font-size:0.85em; margin-top:0; line-height:1.5;">'
                    'This table breaks down what drives the estimated price. Starting from a baseline value, each '
                    'line shows how much the size, location, number of rooms, and property type add to or subtract from '
                    'the final price. Green values push the price up; red values pull it down.</p>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div style="background-color:#ffffff; border-radius:10px; padding:24px; border: 1px solid #E2E8F0;
                                box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); font-size:1.05em;">
                        <table style="width:100%; border-collapse:collapse;">
                            <tr style="border-bottom: 1px solid #F1F5F9;">
                                <td style="padding:12px 0; color:#64748B;">Base Benchmark</td>
                                <td style="padding:12px 0; text-align:right; font-weight:600; color:#0F172A;">€{base:,.0f}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #F1F5F9;">
                                <td style="padding:12px 0; color:#64748B;">Surface Area Adjustment</td>
                                <td style="padding:12px 0; text-align:right; font-weight:600; color:{'#10B981' if surf_c >= 0 else '#EF4444'};">{_fmt(surf_c)}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #F1F5F9;">
                                <td style="padding:12px 0; color:#64748B;">Location Premium</td>
                                <td style="padding:12px 0; text-align:right; font-weight:600; color:{'#10B981' if loc_c >= 0 else '#EF4444'};">{_fmt(loc_c)}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #F1F5F9;">
                                <td style="padding:12px 0; color:#64748B;">Room Layout Adjustment</td>
                                <td style="padding:12px 0; text-align:right; font-weight:600; color:{'#10B981' if rooms_c >= 0 else '#EF4444'};">{_fmt(rooms_c)}</td>
                            </tr>
                            <tr>
                                <td style="padding:12px 0; color:#64748B;">Property Type Adjustment</td>
                                <td style="padding:12px 0; text-align:right; font-weight:600; color:{'#10B981' if ptype_c >= 0 else '#EF4444'};">{_fmt(ptype_c)}</td>
                            </tr>
                            <tr><td colspan="2"><hr style="border:none; border-top:2px solid #CBD5E1; margin:8px 0;"></td></tr>
                            <tr>
                                <td style="padding:8px 0; font-weight:700; color:#0F172A; font-size:1.1em;">Final Estimate</td>
                                <td style="padding:8px 0; text-align:right; font-weight:700; font-size:1.1em; color:#2563EB;">€{prediction:,.0f}</td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True
                )

        # ==========================================================
        # PAGE 2: MARKET DATA & MAP
        # ==========================================================
        elif current == 2:
            dept_stats = data["score_data"].get("dept_stats", {})
            avg_pm2 = dept_stats.get("avg_price_per_m2", 0)
            median_pm2 = dept_stats.get("median_price_per_m2", 0)
            tx_count = dept_stats.get("transaction_count", 0)

            dept_avg_total = avg_pm2 * data["surface"] if avg_pm2 else 0
            if dept_avg_total > 0:
                ratio = prediction / dept_avg_total
                raw_score = 5 + (ratio - 1) * 3
                neighborhood_score = max(1.0, min(10.0, round(raw_score, 1)))
            else:
                neighborhood_score = 5.0

            st.markdown("<h4 style='color: #1E293B; font-weight: 600;'>Market Context</h4>", unsafe_allow_html=True)
            st.markdown('<p style="color:#64748B; font-size:0.85em; margin-top:0; line-height:1.5;">'
                'These figures show the typical price per square meter in the selected area, based on '
                'recent real sales. Use them to see how your property\'s estimate compares to the '
                'local market average.</p>', unsafe_allow_html=True)
            colA, colB = st.columns(2)
            with colA: st.markdown(f'<div class="stat-card"><div class="stat-value">€{avg_pm2:,.0f}</div><div class="stat-label">Avg. Price / m²</div></div>', unsafe_allow_html=True)
            with colB: st.markdown(f'<div class="stat-card"><div class="stat-value">€{median_pm2:,.0f}</div><div class="stat-label">Median Price / m²</div></div>', unsafe_allow_html=True)

            score_pct = (neighborhood_score - 1) / 9 * 100
            score_color = "#10B981" if neighborhood_score >= 7 else "#F59E0B" if neighborhood_score >= 4 else "#EF4444"
            score_label = "Premium Area" if neighborhood_score >= 8 else "Desirable" if neighborhood_score >= 6 else "Standard" if neighborhood_score >= 4 else "Below Market"

            st.markdown(f"""
            <div class="stat-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; font-size:1.05em; color:#0F172A;">Desirability Index</span>
                    <span style="font-weight:700; font-size:1.4em; color:{score_color};">{neighborhood_score}/10</span>
                </div>
                <div class="neighborhood-bar"><div class="neighborhood-marker" style="left:{score_pct}%;"></div></div>
                <div style="text-align:right; margin-top:10px; color:{score_color}; font-weight:600;">{score_label}</div>
                <div class="stat-label" style="margin-top:2px;">Analyzed {tx_count:,} local transactions</div>
            </div>
            <p style="color:#64748B; font-size:0.85em; margin-top:8px; line-height:1.5;">
                The Desirability Index scores the property&#39;s area from 1 to 10 based on how local prices
                compare to the department average. A high score (7+) means the neighbourhood is sought-after
                and commands higher prices, while a low score (below 4) suggests a more affordable area.
            </p>
            <table style="width:100%; border-collapse:collapse; font-size:0.82em; margin-top:4px;">
                <thead>
                    <tr style="background:#F1F5F9;">
                        <th style="padding:7px 10px; text-align:left; color:#475569; font-weight:600; border-radius:4px 0 0 4px;">Score</th>
                        <th style="padding:7px 10px; text-align:left; color:#475569; font-weight:600;">Label</th>
                        <th style="padding:7px 10px; text-align:left; color:#475569; font-weight:600; border-radius:0 4px 4px 0;">What it means</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid #F1F5F9;">
                        <td style="padding:7px 10px; color:#0F172A; font-weight:600;">8 – 10</td>
                        <td style="padding:7px 10px; color:#10B981; font-weight:600;">Premium Area</td>
                        <td style="padding:7px 10px; color:#64748B;">Consistently high demand; prices well above the departmental norm</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; background:#FAFAFA;">
                        <td style="padding:7px 10px; color:#0F172A; font-weight:600;">6 – 7</td>
                        <td style="padding:7px 10px; color:#10B981; font-weight:600;">Desirable</td>
                        <td style="padding:7px 10px; color:#64748B;">Above-average neighbourhood with strong market activity</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9;">
                        <td style="padding:7px 10px; color:#0F172A; font-weight:600;">4 – 5</td>
                        <td style="padding:7px 10px; color:#F59E0B; font-weight:600;">Standard</td>
                        <td style="padding:7px 10px; color:#64748B;">In line with the typical market; solid but undifferentiated</td>
                    </tr>
                    <tr style="background:#FAFAFA;">
                        <td style="padding:7px 10px; color:#0F172A; font-weight:600;">1 – 3</td>
                        <td style="padding:7px 10px; color:#EF4444; font-weight:600;">Below Market</td>
                        <td style="padding:7px 10px; color:#64748B;">Prices sit below the area average; may signal lower demand or a buying opportunity</td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)

            map_center = dept_centers.get(selected_dept, [46.6, 2.5])
            if data["city"]:
                coords = fetch_commune_coords(API_URL, selected_dept, data["city"])
                if coords: map_center = coords
            m = folium.Map(location=map_center, zoom_start=11, tiles="CartoDB positron")
            st_folium(m, width=None, height=200, returned_objects=[])

        # ==========================================================
        # PAGE 3: INVESTMENT & COMPARABLES
        # ==========================================================
        elif current == 3:
            st.markdown("<h4 style='color: #1E293B; font-weight: 600;'>Investment Analytics</h4>", unsafe_allow_html=True)
            st.markdown('<p style="color:#64748B; font-size:0.85em; margin-top:0; line-height:1.5;">'
                'Key figures to help you assess this property as an investment. '
                '<b>Est. Gross Yield</b> is the approximate annual rental income you could expect, shown as a percentage of the property price. '
                '<b>YoY Capital Growth</b> shows whether property prices in this area have been rising or falling over the past year. '
                'The <b>Asset Score</b> (0–10) is an overall investment rating that combines rental income potential, '
                'price trends, and affordability in the area.</p>', unsafe_allow_html=True)
            
            inv = data["inv_data"]
            if inv:
                rental_yield = inv.get("rental_yield", 0)
                market_growth = inv.get("market_growth", 0)
                inv_score = inv.get("investment_score", 0)

                growth_color = "#10B981" if market_growth >= 0 else "#EF4444"
                growth_sign = "+" if market_growth >= 0 else ""
                score_color = "#10B981" if inv_score >= 7 else "#F59E0B" if inv_score >= 4 else "#EF4444"
                score_pct = (inv_score / 10) * 100

                ic1, ic2, ic3 = st.columns(3)
                with ic1: st.markdown(f'<div class="stat-card"><div class="stat-value">{rental_yield:.1f}%</div><div class="stat-label">Est. Gross Yield</div></div>', unsafe_allow_html=True)
                with ic2: st.markdown(f'<div class="stat-card"><div class="stat-value" style="color:{growth_color};">{growth_sign}{market_growth:.1f}%</div><div class="stat-label">YoY Capital Growth</div></div>', unsafe_allow_html=True)
                with ic3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; font-size:1.05em; color:#0F172A;">Rating</span>
                            <span style="font-weight:700; font-size:1.2em; color:{score_color};">{inv_score}/10</span>
                        </div>
                        <div class="neighborhood-bar" style="margin-top:6px;"><div class="neighborhood-marker" style="width:14px; height:14px; top:-4px; left:{score_pct}%;"></div></div>
                        <div class="stat-label" style="margin-top:8px;">Asset Score</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Investment data not available for this configuration.")

            st.markdown("<br><h4 style='color: #1E293B; font-weight: 600;'>Recent Comparables</h4>", unsafe_allow_html=True)
            st.markdown('<p style="color:#64748B; font-size:0.85em; margin-top:0; line-height:1.5;">'
                'These are 5 recently sold properties in the same area that are most similar to yours in size and number of rooms. '
                'The <b>Variance</b> column shows the price difference compared to your estimate - '
                'positive means the comparable sold for more, negative means it sold for less.</p>', unsafe_allow_html=True)
            comparables = data["comp_data"]
            if comparables:
                rows_html = ""
                for i, comp in enumerate(comparables):
                    bg = "#F8FAFC" if i % 2 == 0 else "#ffffff"
                    diff = comp["price"] - prediction
                    diff_color = "#10B981" if diff >= 0 else "#EF4444"
                    rows_html += (
                        f'<tr style="background-color:{bg}; border-bottom: 1px solid #F1F5F9;">'
                        f'<td style="padding:10px 12px; color:#334155;">{comp["type"]}</td>'
                        f'<td style="padding:10px 12px; text-align:right; font-weight:600;">€{comp["price"]:,.0f}</td>'
                        f'<td style="padding:10px 12px; text-align:right; color:#475569;">{comp["surface"]:.0f} m²</td>'
                        f'<td style="padding:10px 12px; text-align:right; color:{diff_color}; font-weight:600;">{"+" if diff >= 0 else "-"}€{abs(diff):,.0f}</td>'
                        f'</tr>'
                    )
                comp_html = (
                    '<div style="background-color:#ffffff; border-radius:10px; border: 1px solid #E2E8F0; overflow:hidden;">'
                    '<table style="width:100%; border-collapse:collapse; font-size:0.9em;">'
                    '<thead style="background-color: #F1F5F9;"><tr>'
                    '<th style="padding:10px 12px; text-align:left; color:#475569;">Type</th>'
                    '<th style="padding:10px 12px; text-align:right; color:#475569;">Price</th>'
                    '<th style="padding:10px 12px; text-align:right; color:#475569;">Area</th>'
                    '<th style="padding:10px 12px; text-align:right; color:#475569;">Variance</th>'
                    '</tr></thead>'
                    f'<tbody>{rows_html}</tbody></table></div>'
                )
                st.markdown(comp_html, unsafe_allow_html=True)
            else:
                st.info("No comparable properties found.")

        # ==========================================================
        # NAVIGATION BUTTONS
        # ==========================================================
        st.markdown("<br><br>", unsafe_allow_html=True)
        nav_col1, empty_col, nav_col2 = st.columns([1, 1.5, 1])
        
        with nav_col1:
            if current > 1:
                st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
                if st.button("← Previous", use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
        with nav_col2:
            if current < 3:
                if st.button("Next Detail →", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()
            elif current == 3:
                st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
                if st.button("Start New Estimate", use_container_width=True):
                    st.session_state.report_data = None
                    st.session_state.current_page = 1
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)