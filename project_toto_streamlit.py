import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import geopandas as gpd
from datetime import datetime, timedelta, date, time

logo_path = 'project_toto_logo.png'

# Display the logo on the right
st.markdown(f"""
    <style>
    .logo {{
        position: absolute;
        top: 0;
        right: 0;
        border: none;
    }}
    </style>
    <img src="{logo_path}" class="logo" width="100">
    """, unsafe_allow_html=True)

# Main content in the rest of the app
st.title('Welcome to Project Toto')
st.write('This is an interactive visualization app.')

# You can continue with the rest of your Streamlit code below this



# Load tornado risk data
@st.cache_data  # Use the correct decorator for caching
def load_tornado_risk_data():
    data = pd.read_csv('tornado_risk.csv')
    data['DateTime'] = pd.to_datetime(data['DateTime'])  # Ensure proper datetime format
    return data

tornado_data = load_tornado_risk_data()
print(tornado_data.head())

# Load shapefile
@st.cache_data  # Use the correct decorator for caching
def load_shapefile():
    gdf = gpd.read_file('Iowa_County_Boundaries/IowaCounties.shp')  # Update the path as needed
    return gdf

shapefile_data = load_shapefile()
print(shapefile_data.head())

# Merging shapefile with tornado risk data
@st.cache_data #(allow_output_mutation=True)  # Correct decorator for caching with mutation allowed
def merge_data(_shapefile, _tornado_data):
    merged_data = _shapefile.merge(_tornado_data, left_on=['CountyName','StateAbbr'], right_on=['County Name','State'], how='left')
    return merged_data

merged_gdf = merge_data(shapefile_data, tornado_data)

# Define color scale logic and apply it to the DataFrame
def apply_color_scale(df):
    colors = []
    for risk in df['TornadoRisk']:
        if risk < 0.5:
            colors.append([0, 125, 255])  # Blue
        elif risk < 0.75:
            colors.append([255, 255, 0])  # Yellow
        else:
            colors.append([255, 0, 0])  # Red
    df['color'] = colors

apply_color_scale(merged_gdf)

# Static variable for date and time
selected_datetime = st.sidebar.date_input("Select Date", value=pd.Timestamp('2023-02-26'))
selected_time = st.sidebar.time_input("Select Time", value=pd.Timestamp('2023-02-26 07:11:58 AM').time())
selected_datetime = pd.Timestamp.combine(selected_datetime, selected_time)

# Filter data based on selected datetime
filtered_data = merged_gdf[merged_gdf['DateTime'] == selected_datetime]
# print(filtered_data.head())

# Display the filtered data on the map
st.write("### Tornado Risk Map")
st.write("Select a date and time to view the tornado risk in Iowa.")
st.write("The map shows the tornado risk for each county in Iowa.")
st.write("Hover over a county to see the county name and tornado risk.")
st.write("Use the sidebar to select a specific date and time.")
st.write("The color scale represents the tornado risk level.")
st.write("Blue: Low risk, Yellow: Medium risk, Red: High risk.")    
st.write("Data source: [NOAA Storm Prediction Center](https://www.spc.noaa.gov/gis/svrgis/)")

st.write(filtered_data.columns)
st.write(filtered_data[['DateTime','TornadoRisk','County Name','color']].head())

# # Create PyDeck map
# view_state = pdk.ViewState(latitude=42.0308, longitude=-93.6319, zoom=7)

# layer = pdk.Layer(
#     'GeoJsonLayer',
#     data=filtered_data,
#     get_fill_color='color',  # Use the precomputed 'color' column
#     get_line_color=[255, 255, 255],  # White lines for county boundaries
#     pickable=True,
#     stroked=True,  # Enable stroking to draw boundaries
#     filled=True,
#     line_width_min_pixels=1,  # Minimum line width in pixels
#     extruded=False,
# )

# deck = pdk.Deck(
#     layers=[layer],
#     initial_view_state=view_state,
#     tooltip={"text": "{CountyName}: {TornadoRisk}"}
# )

# st.pydeck_chart(deck)


# # Filter and map setup
# selected_datetime = pd.Timestamp(st.sidebar.date_input("Select Date", value=pd.Timestamp.now()))
# filtered_data = merged_gdf[merged_gdf['DateTime'] == selected_datetime]

# Ensure data is not empty
if filtered_data.empty:
    st.error("No data available for the selected date and time.")
else:
    # Proceed with visualization
    view_state = pdk.ViewState(latitude=42.0308, longitude=-93.6319, zoom=7)
    layer = pdk.Layer(
        'GeoJsonLayer',
        data=filtered_data,
        get_fill_color='color',
        get_line_color=[255, 255, 255],
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=1,
        extruded=False,
    )
    deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{CountyName}: {TornadoRisk}"})
    st.pydeck_chart(deck)