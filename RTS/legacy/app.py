import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import os
import time

# Load Iowa county boundaries
script_dir = os.path.dirname(__file__)
geojson_path = os.path.join(script_dir, 'Iowa_County_Boundaries.geojson')
iowa_geo = gpd.read_file(geojson_path)

# Function to load data from the Parquet file
def load_dataframe(parquet_file='tornado_risk.parquet'):
    try:
        df = pd.read_parquet(parquet_file)
        return df
    except FileNotFoundError:
        st.warning('Parquet file not found. Initializing empty DataFrame.')
        return pd.DataFrame(columns=['time', 'county', 'risk'])
    except Exception as e:
        st.error(f'Error loading Parquet file: {e}')
        return pd.DataFrame(columns=['time', 'county', 'risk'])

# Initialize session state for df_st if it doesn't exist
if 'df_st' not in st.session_state:
    st.session_state.df_st = load_dataframe()

# Streamlit UI setup
st.title('Iowa County Tornado Risk')

# Layout for the header section
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.write("")

with col2:
    st.image(os.path.join(script_dir, 'project_toto_logo.png'), width=200)
    st.markdown('### Project By: Michael Goodman, Dharti Seagraves, Steve Veldman, and Forough Mofidi')
    st.markdown(f"**Iowa County Tornado Risk as of: {st.session_state.df_st['time'].max() if not st.session_state.df_st.empty else 'N/A'}**")
    st.markdown(f"**County: {st.session_state.df_st['county'].max() if not st.session_state.df_st.empty else 'N/A'}**")
    st.markdown(f"**Pred: {st.session_state.df_st['risk'].max() if not st.session_state.df_st.empty else 'N/A'}**")

with col3:
    st.write("")

# Merge the risk data with the GeoJSON data
iowa_geo['county'] = iowa_geo['CountyName']  # Ensure the county names match
merged_df = iowa_geo.merge(st.session_state.df_st, on='county', how='left')

# Set the color based on risk
def get_color(risk):
    if pd.isna(risk):
        return '#59d4ff'  # Gray for missing data
    elif risk > 0.85:
        return '#c72b1d'  # Red
    elif risk > 0.5:
        return '#fdbf3b'  # Yellow
    else:
        return '#869755'  # Green

merged_df['color'] = merged_df['risk'].apply(get_color)

# Round the risk values to 4 decimal places for display
merged_df['risk'] = merged_df['risk'].round(4)

# Center the map on Iowa
m = folium.Map(location=[41.878, -93.097], zoom_start=7)

# Function to style the counties
def style_function(feature):
    return {
        'fillColor': feature['properties']['color'],
        'color': '#c04e01',
        'weight': 1,
        'fillOpacity': 0.7,
    }

# Add the GeoJSON to the map
folium.GeoJson(
    merged_df,
    name='Iowa Tornado Risk',
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['CountyName', 'risk'], aliases=['County', 'Tornado Risk'])
).add_to(m)

# Add a layer control panel
folium.LayerControl().add_to(m)

# Display the map
folium_static(m)

# Automatically refresh the DataFrame and rerun the script every 10 seconds
if st.button('Manual Refresh'):
    st.session_state.df_st = load_dataframe()
    st.rerun()

#st.rerun()  # Ensure the script is rerun every time it's loaded

# Sleep for a few seconds to prevent rapid reruns
time.sleep(1)

st.session_state.df_st = load_dataframe()
st.rerun()




