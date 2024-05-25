
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from datetime import datetime
import json
import folium
from streamlit_folium import folium_static


# Set up the Streamlit app
st.title('Iowa Tornado Risk Map')
st.write('This app visualizes the tornado risk for each county in Iowa.')

# Load tornado risk data
@st.cache_data
def load_tornado_risk_data():
    data = pd.read_csv('tornado_risk.csv')
    data['DateTime'] = pd.to_datetime(data['DateTime'])  # Ensure proper datetime format
    # Trim whitespace from all string columns and convert County Name to uppercase
    data = data.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    data['County Name'] = data['County Name'].str.upper().str.strip()
    data['State'] = data['State'].str.upper().str.strip()
    data = data.rename(columns={'County Name': 'CountyName'})  # Rename column for merging
    return data

tornado_data = load_tornado_risk_data()
st.write('Tornado Data', tornado_data.head())

# Load GeoJSON file
@st.cache_data
def load_geojson():
    gdf = gpd.read_file('Iowa_County_Boundaries.geojson')
    gdf['CountyName'] = gdf['CountyName'].str.upper().str.strip()
    gdf['StateAbbr'] = gdf['StateAbbr'].str.upper().str.strip()
    gdf = gdf.rename(columns={'StateAbbr': 'State'})  # Rename column for merging
    return gdf

geojson_data = load_geojson()
st.write('GeoJSON Data', geojson_data.head())

# Ensure both columns are of string type
geojson_data['CountyName'] = geojson_data['CountyName'].astype(str)
geojson_data['State'] = geojson_data['State'].astype(str)
tornado_data['CountyName'] = tornado_data['CountyName'].astype(str)
tornado_data['State'] = tornado_data['State'].astype(str)

# Check unique values and their lengths before merging
unique_tornado_counties = tornado_data['CountyName'].unique()
unique_geojson_counties = geojson_data['CountyName'].unique()

# Create a DataFrame to display lengths
county_check = pd.DataFrame({
    'Tornado County Name': unique_tornado_counties,
    'Tornado Length': [len(name) for name in unique_tornado_counties],
    'GeoJSON County Name': unique_geojson_counties,
    'GeoJSON Length': [len(name) for name in unique_geojson_counties]
})

st.write("County Name Length Check:", county_check)

# Merging GeoJSON data with tornado risk data
@st.cache_data
def merge_data(_geojson, _tornado_data):
    merged_data = _geojson.merge(_tornado_data, on=['CountyName', 'State'], how='left')
    return merged_data

merged_gdf = merge_data(geojson_data, tornado_data)
st.write('Merged Data', merged_gdf[['DateTime', 'TornadoRisk', 'CountyName']].head(20))

# Check for any non-matching entries
non_matching = merged_gdf[merged_gdf['TornadoRisk'].isna()]
st.write('Non-matching entries after merge:', non_matching.drop(columns='geometry').head(20))

# Static variable for date and time
selected_date = st.sidebar.date_input("Select Date", value=pd.Timestamp('2023-02-26'))
selected_time = st.sidebar.time_input("Select Time", value=pd.Timestamp('07:11:58').time())
selected_datetime = pd.Timestamp.combine(selected_date, selected_time)
st.write('selected_datetime', selected_datetime)

# Filter data based on selected datetime
filtered_data = merged_gdf[merged_gdf['DateTime'] == selected_datetime]
st.write('Filtered Data: ', filtered_data.drop(columns='geometry').head())

# Define color scale logic
def apply_color_scale(df):
    colors = df['TornadoRisk'].apply(
        lambda x: 'rgba(0,0,0,0)' if pd.isna(x) else 'blue' if x < 0.5 else 'yellow' if x < 0.75 else 'red'
    )
    df['color'] = colors

apply_color_scale(filtered_data)
st.write('Filtered Data with Color:', filtered_data.drop(columns='geometry').head())

# Ensure the filtered data contains the geometry and convert DateTime to string
filtered_geojson = gpd.GeoDataFrame(filtered_data, geometry='geometry')
filtered_geojson['DateTime'] = filtered_geojson['DateTime'].astype(str)

# # Convert GeoDataFrame to GeoJSON
# filtered_geojson_json = json.loads(filtered_geojson.to_json())
# st.write('filtered_geojson_json:', json.dumps(filtered_geojson_json, indent=2))

# Center the map on Iowa
m = folium.Map(location=[41.878, -93.097], zoom_start=7)

# Function to style the counties
def style_function(feature):
    return {
        'fillColor': feature['properties']['color'],
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7,
    }

# Add the GeoJSON to the map
folium.GeoJson(
    filtered_geojson,
    name='Iowa Tornado Risk',
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['CountyName', 'TornadoRisk'], aliases=['County', 'Tornado Risk'])
).add_to(m)

# Add a layer control panel
folium.LayerControl().add_to(m)

# Display the map in Streamlit
folium_static(m)

st.write("Select a date and time to view the tornado risk in Iowa. The map shows the tornado risk for each county in Iowa. Use the sidebar to select a specific date and time. The color scale represents the tornado risk level: Blue (<0.5), Yellow (<0.75), Red (<1.0).")

