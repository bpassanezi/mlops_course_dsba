import streamlit as st
import requests
import json

# Set page config for a premium feel
st.set_page_config(
    page_title="Real Estate Price Predictor",
    page_icon="🏠",
    layout="centered"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    .prediction-card {
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .prediction-value {
        font-size: 2.5em;
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏠 Real Estate Price Predictor")
st.write("Enter the property details below to estimate its market value.")

# Input Form
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        surface = st.number_input("Surface (m²)", min_value=1.0, value=60.0, step=1.0)
        rooms = st.number_input("Number of Rooms", min_value=1.0, value=3.0, step=1.0)
    
    with col2:
        dept = st.text_input("Department Code (e.g., 75, 13, 15)", value="75")
        type_local = st.selectbox("Property Type", ["Appartement", "Maison"])

# API URL - Default to 'backend' for Docker Compose, or 'localhost' for local development
import os
DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000/scoring/")
API_URL = st.sidebar.text_input("API URL", value=DEFAULT_API_URL)

if st.button("Run Prediction"):
    # Prepare payload
    payload = {
        "surface_reelle_bati": surface,
        "nombre_pieces_principales": rooms,
        "code_departement": dept,
        "type_local": type_local
    }
    
    try:
        with st.spinner("Calculating..."):
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            result = response.json()

            prediction = result.get("score", 0)
            breakdown = result.get("breakdown", {})

            # Display results in a nice card
            st.markdown(f"""
            <div class="prediction-card">
                <h3>Estimated Value</h3>
                <div class="prediction-value">€{prediction:,.2f}</div>
                <p>Based on the latest model artifacts</p>
            </div>
            """, unsafe_allow_html=True)

            # Price breakdown section
            if breakdown:
                def _fmt(val):
                    sign = "+" if val >= 0 else "-"
                    return f"{sign}€{abs(val):,.0f}"

                base = breakdown.get("base_value", 0)
                surface = breakdown.get("surface_contribution", 0)
                location = breakdown.get("location_effect", 0)
                rooms = breakdown.get("rooms_adjustment", 0)
                ptype = breakdown.get("property_type_adjustment", 0)

                st.markdown("")
                st.subheader("Price Breakdown")
                st.markdown(
                    f"""
                    <div style="background-color:#ffffff; border-radius:10px; padding:24px;
                                box-shadow:0 2px 8px rgba(0,0,0,0.08); font-family:monospace; font-size:1.05em;">
                        <table style="width:100%; border-collapse:collapse;">
                            <tr>
                                <td style="padding:8px 0; color:#555;">Base value</td>
                                <td style="padding:8px 0; text-align:right; font-weight:600;">€{base:,.0f}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0; color:#555;">Surface contribution</td>
                                <td style="padding:8px 0; text-align:right; font-weight:600;
                                    color:{'#2e7d32' if surface >= 0 else '#c62828'};">{_fmt(surface)}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0; color:#555;">Location effect</td>
                                <td style="padding:8px 0; text-align:right; font-weight:600;
                                    color:{'#2e7d32' if location >= 0 else '#c62828'};">{_fmt(location)}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0; color:#555;">Rooms adjustment</td>
                                <td style="padding:8px 0; text-align:right; font-weight:600;
                                    color:{'#2e7d32' if rooms >= 0 else '#c62828'};">{_fmt(rooms)}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0; color:#555;">Property type adjustment</td>
                                <td style="padding:8px 0; text-align:right; font-weight:600;
                                    color:{'#2e7d32' if ptype >= 0 else '#c62828'};">{_fmt(ptype)}</td>
                            </tr>
                            <tr>
                                <td colspan="2"><hr style="border:none; border-top:2px solid #eee; margin:8px 0;"></td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0; font-weight:700; font-size:1.1em;">Estimated price</td>
                                <td style="padding:8px 0; text-align:right; font-weight:700;
                                    font-size:1.1em; color:#ff4b4b;">€{prediction:,.0f}</td>
                            </tr>
                        </table>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.balloons()

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

st.divider()
st.caption("Developed for MLOps Course DSBA")
