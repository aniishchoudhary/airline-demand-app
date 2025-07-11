import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key safely
openai.api_key = os.getenv("OPENAI_API_KEY")


# Streamlit page config
st.set_page_config(page_title="Airline Demand Trends", layout="wide")

# Title
st.title("✈️ Airline Booking Market Demand Tracker")

# -------------------- Sidebar Inputs -------------------- #
st.sidebar.header("🔎 Filter")

icao_options = {
    "Sydney - YSSY": "YSSY",
    "Melbourne - YMML": "YMML",
    "Brisbane - YBBN": "YBBN",
    "Frankfurt - EDDF": "EDDF",
    "London Heathrow - EGLL": "EGLL",
    "Los Angeles - KLAX": "KLAX",
    "Paris Charles de Gaulle - LFPG": "LFPG",
    "Amsterdam - EHAM": "EHAM"
}

airport = st.sidebar.selectbox("Select Airport", list(icao_options.keys()))
selected_icao = icao_options[airport]

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Time Range")

date_input = st.sidebar.date_input("Select Date", value=datetime.utcnow().date())
hour_input = st.sidebar.slider("Select Hour (UTC)", 0, 23, 12)

# Get UNIX timestamps for selected time
selected_datetime = datetime.combine(date_input, datetime.min.time()) + timedelta(hours=hour_input)
end_time = int(selected_datetime.timestamp())
start_time = end_time - 3600

df = pd.DataFrame()  # Initialize globally for later use

# -------------------- Fetch Flight Data -------------------- #
if st.sidebar.button("Fetch Flight Data"):
    with st.spinner("Fetching data from OpenSky Network..."):
        url = f"https://opensky-network.org/api/flights/departure?airport={selected_icao}&begin={start_time}&end={end_time}"
        response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)[['estDepartureAirport', 'estArrivalAirport', 'callsign']].dropna()
                    df.columns = ['From', 'To', 'Callsign']

                    st.subheader("📋 Recent Departures")
                    st.dataframe(df)

                    route_counts = df['To'].value_counts().reset_index()
                    route_counts.columns = ['Destination', 'Count']

                    fig = px.bar(route_counts, x='Destination', y='Count',
                                 title="Top Destination Airports (Past Hour)", color='Count')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No flight data available for this airport and time.")
            except Exception as e:
                st.error(f"Error processing data: {e}")
        elif response.status_code == 404:
            st.error("Invalid ICAO code or data not available for this region.")
        else:
            st.error(f"API Error {response.status_code}: Unable to fetch data.")

# -------------------- AI Summary Generator -------------------- #
if st.button("🧠 Generate Summary with ChatGPT"):
    if not df.empty:
        route_summary = df['To'].value_counts().head(5).to_string()
        prompt = f"""You are a data analyst. Based on the following arrival airport frequency data:\n\n{route_summary}\n\nSummarize the flight demand trends in plain English."""

        with st.spinner("Generating AI summary..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You summarize aviation data."},
                        {"role": "user", "content": prompt}
                    ]
                )
                summary = response['choices'][0]['message']['content']
                st.success("📈 Summary of Flight Demand Trends")
                st.markdown(summary)
            except Exception as e:
                st.error(f"OpenAI API error: {e}")
    else:
        st.warning("⚠️ Please fetch flight data first before generating summary.")
