"""
Name:       Adrian White-Bromleigh
CS230:      Section 2
Data:       Noise Complaints in NYC (12/24/2025 - 1/2/2026)
URL:        [Link to your web application on Streamlit Cloud]

Description: 
This application analyzes NYC noise data to identify hotspots and trends 
during the 2025 holiday season. It uses interactive filters to let users 
explore specific boroughs and complaint types.
Use of AI: AI was used as a tool to guide me while I code
I uploaded my proposal and asked AI how to break down my proposal into each function
When I was confused about errors or code not running as intented, I asked it to teach me
how to properly code the line/s for the intended outcome
"""
import streamlit as st
import pandas as pd
import pydeck as pdk

# Configure the Streamlit page view
st.set_page_config(page_title="NYC Holiday Noise Explorer", layout="wide")

@st.cache_data
def load_data():
    """Loads and preprocesses the NYC Noise Complaints dataset."""
    df = pd.read_csv("311_Noise_Complaints_20260403.csv", low_memory=False)
    
    #Use a lambda function to parse 'Created Date' into datetime objects
    df['Created Date'] = df['Created Date'].apply(lambda x: pd.to_datetime(x, errors='coerce'))
    
    # Filter for the loudest week of the year (Dec 24 2025 - Jan 2 2026)
    start_date = pd.to_datetime('2025-12-24')
    end_date = pd.to_datetime('2026-01-02')
    df = df[(df['Created Date'] >= start_date) & (df['Created Date'] <= end_date)]
    
    # Drop rows that are missing coordinates to prevent PyDeck errors
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    # Fill missing addresses for the tooltip
    df['Incident Address'] = df['Incident Address'].fillna('Unknown Address')
    return df

# Load cleaned dataset
df = load_data()

st.title("🗽 NYC Holiday Noise Explorer")
st.write("Analyze NYC noise complaints recorded from Christmas Eve through New Year’s Day to discover where the loudest complaints come from.")

# 1. Temporal Trends
st.header("📈 Temporal Trends")
st.write("Use the slider below to narrow down the dates and identify specific complaint spikes (e.g., New Year's Eve).")

min_date = df['Created Date'].min().date()
max_date = df['Created Date'].max().date()

# Date slider 
date_range = st.slider(
    "Select Date Range", 
    min_value=min_date, 
    max_value=max_date, 
    value=(min_date, max_date)
)

# Filter the dataframe based on the slider input
df_filtered = df[(df['Created Date'].dt.date >= date_range[0]) & (df['Created Date'].dt.date <= date_range[1])]

# Group by each date and plot the volume over the 10-day period
complaints_by_date = df_filtered.groupby(df_filtered['Created Date'].dt.date).size()
st.line_chart(complaints_by_date)


# 2. Borough Breakdown analysis
st.header("🏙️ Borough Analysis")
st.write("Compare total noise complaints across the five boroughs.")

boroughs = df['Borough'].dropna().unique().tolist()
# Multi-select for comparing specific boroughs side-by-side
selected_boroughs = st.multiselect("Select Boroughs to Compare:", boroughs, default=boroughs)

df_borough = df_filtered[df_filtered['Borough'].isin(selected_boroughs)]
complaints_by_borough = df_borough['Borough'].value_counts()
st.bar_chart(complaints_by_borough)


# 3. Complaint Type Analysis
st.header("📊 Complaint Type Analysis")
# Numeric input to filter results by Top N categories
top_n = st.number_input("Select Top 'N' Most Common Complaint Types to Display", min_value=1, max_value=20, value=5)

#Creating a pivot table to show problem details broken down by borough
pivot_df = pd.pivot_table(
    df_borough, 
    values='Unique Key', 
    index='Problem Detail (formerly Descriptor)', 
    columns='Borough', 
    aggfunc='count', 
    fill_value=0
)

# Calculate total complaints per type, sort, and extract the Top N
pivot_df['Total'] = pivot_df.sum(axis=1)
top_complaints = pivot_df.sort_values(by='Total', ascending=False).head(top_n)

st.write(f"**Top {top_n} Complaint Types by Borough:**")
st.dataframe(top_complaints)


# --- 4. Geospatial Heatmap ---
st.header("🗺️ Geospatial Heatmap: Where were the parties?")
st.write("Explore specific locations of noise complaints. Hover over the markers to view details.")

# Configure the PyDeck Layer
layer = pdk.Layer(
    "ScatterplotLayer",
    df_borough,
    get_position=['Longitude', 'Latitude'],
    get_color='[200, 30, 0, 160]',
    get_radius=60,
    pickable=True
)

# Configure the PyDeck View State Centered on NYC
view_state = pdk.ViewState(
    latitude=df['Latitude'].mean(),
    longitude=df['Longitude'].mean(),
    zoom=10,
    pitch=30
)

# Build the Map and include a tooltip to show the exact addresses and details
r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "text": "Address: {Incident Address}\nComplaint: {Problem Detail (formerly Descriptor)}"
    }
)

st.pydeck_chart(r)
