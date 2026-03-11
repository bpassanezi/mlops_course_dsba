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
            
            # Display results in a nice card
            st.markdown(f"""
            <div class="prediction-card">
                <h3>Estimated Value</h3>
                <div class="prediction-value">€{prediction:,.2f}</div>
                <p>Based on the latest model artifacts</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.balloons()
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

st.divider()
st.caption("Developed for MLOps Course DSBA")
