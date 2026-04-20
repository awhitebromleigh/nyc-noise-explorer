"""
Name:       Adrian White-Bromleigh
CS230:      Section 2
Data:       Noise Complaints in NYC (12/24/2025 - 1/2/2026)
URL:      https://rfn8lpwcgydg2bzmjaay7q.streamlit.app/

Description: 
This application analyzes NYC noise data to identify hotspots and trends 
during the 2025 holiday season. It uses interactive filters to let users 
explore specific boroughs and complaint types.
Use of AI: AI was used as a tool to guide me while I code.
I uploaded my proposal and asked AI how to break down my proposal into each function.
When I was confused about errors or code not running as intended, I asked it to teach me
how to properly code the line/s for the intended outcome.
"""
import streamlit as st
import pandas as pd
import pydeck as pdk

# Configure the Streamlit page view
st.set_page_config(page_title="NYC Holiday Noise Explorer", layout="wide")

@st.cache_data #Loads this as cache data
#Every time you move the slide the app would have to re-open without it
def load_data():
    """Loads and preprocesses the NYC Noise Complaints dataset."""
    df = pd.read_csv("311_Noise_Complaints_20260403.csv", low_memory=False)
    #low memory =false 
    #tells Pandas to read the entire file at once 
    # to correctly guess the data types of each column.

    # [PY6 - Lambda] Use a lambda function to parse 'Created Date' in csv into datetime objects
    df['Created Date'] = df['Created Date'].apply(lambda x: pd.to_datetime(x, errors='coerce')) 
    #coerce means "If you can't figure out the date, just turn it into NaT (Not a Time)."
    #LAMBDA EXPLANATION: The .apply() method goes through every single row in the 'Created Date' column. 
    #The lambda x: says "take the current row's value, call it x, and run it through 
    # pd.to_datetime(x)."

    # Filter for the loudest week of the year (Dec 24 2025 - Jan 2 2026)
    start_date = pd.to_datetime('2025-12-24')
    end_date = pd.to_datetime('2026-01-02')
    df = df[(df['Created Date'] >= start_date) & (df['Created Date'] <= end_date)]
    
    # Drop rows that are missing coordinates to prevent PyDeck errors
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    # Fill missing addresses for the tooltip
    df['Incident Address'] = df['Incident Address'].fillna('Unknown Address')
    return df

# [PY1 - Func2p] Function taking 2 parameters
def generate_borough_summary(filtered_df, target_boroughs):
    """Generates a summary dictionary of complaints per borough and the overall total."""
    borough_counts = {}
    total_complaints = 0
    
 # [PY4 - IterLoop] A for-loop iterating over the selected boroughs
    for borough in target_boroughs:
        # Count how many complaints match the current borough
        b_count = len(filtered_df[filtered_df['Borough'] == borough])
        borough_counts[borough] = b_count
        total_complaints += b_count
        
    # [PY5 - DictMethod] Using .items() to iterate through the dictionary
    # [PY3 - ListComp] Using a list comprehension to filter boroughs that actually have data
    active_boroughs = [b for b, count in borough_counts.items() if count > 0] 
    
    # [PY2 - FuncReturn2] Returning 3 distinct values
    return borough_counts, total_complaints, active_boroughs

# Load cleaned dataset
df = load_data()

#SIDEBAR CONTROLS
# Moving inputs to the sidebar guarantees the Streamlit layout/appearance points
st.sidebar.header("🎛️ Control Panel")
st.sidebar.write("Use these filters to update the charts and map.")

min_date = df['Created Date'].min().date()
max_date = df['Created Date'].max().date()

# Date slider 
date_range = st.sidebar.slider(
    "Select Date Range", 
    min_value=min_date, 
    max_value=max_date, 
    value=(min_date, max_date)
)

# Filter the dataframe based on the slider input
df_filtered = df[(df['Created Date'].dt.date >= date_range[0]) & (df['Created Date'].dt.date <= date_range[1])]

# [PY3 - ListComp] clean up the borough list to remove Unspecified entries
raw_boroughs = df['Borough'].dropna().unique()
valid_boroughs = [b for b in raw_boroughs if b != "Unspecified"]

# Multi-select for comparing specific boroughs side-by-side
selected_boroughs = st.sidebar.multiselect("Select Boroughs to Compare:", valid_boroughs, default=valid_boroughs)

# Numeric input to filter results by Top N categories
top_n = st.sidebar.number_input("Top 'N' Complaint Types to Display", min_value=1, max_value=20, value=5)


#Main page dashboard
st.title("🗽 NYC Holiday Noise Explorer")
st.write("Analyze NYC noise complaints recorded from Christmas Eve through New Year’s Day to discover where the loudest complaints come from.")

# Display quick stats using our new Python function
if selected_boroughs:
    b_counts, total_c, active_b = generate_borough_summary(df_filtered, selected_boroughs)
    st.info(f"**Quick Stats:** You are currently viewing **{total_c}** total complaints across **{len(active_b)}** boroughs.")

# 1. Temporal Trends
st.header("📈 Temporal Trends")
# Group by each date and plot the volume over the filtered period
complaints_by_date = df_filtered.groupby(df_filtered['Created Date'].dt.date).size()
st.line_chart(complaints_by_date)


# 2. Borough Breakdown analysis
st.header("🏙️ Borough Analysis")
df_borough = df_filtered[df_filtered['Borough'].isin(selected_boroughs)]
complaints_by_borough = df_borough['Borough'].value_counts()
st.bar_chart(complaints_by_borough)


# 3. Complaint Type Analysis
st.header("📊 Complaint Type Analysis")

# Creating a pivot table to show problem details broken down by borough
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


# 4. Geospatial Heatmap
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
        "text": "Address: {Incident Address}\nComplaint: {Problem Detail (formerly descriptor)}"
    }
)

st.pydeck_chart(r)
