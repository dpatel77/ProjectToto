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

# Function to get the max time for the timestamp
def get_max_time(df):
    if not df.empty:
        return df['time'].max()
    else:
        return 'N/A'

# Streamlit UI setup
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .header {
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        margin-bottom: 20px;
    }
    .header img {
        height: 100px;
        margin-right: 20px;
    }
    .map-container {
        height: 700px;
    }
    .large-table {
        font-size: 18px !important;
    }
    .content {
        display: flex;
        justify-content: space-between;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header section
st.markdown('<div class="header">', unsafe_allow_html=True)
st.image('project_toto_logo.png', width=200)
st.markdown(
    """
    <div>
        <h1>Project TOTO: Tornado Outbreak Threat Observations</h1>
        <h3>Developed in part with University of Chicago:</h3>
        <p>Dharti Seagraves, Steve Veldman, Michael Goodman, Forough Mofidi</p>
        <p><a href="https://github.com/dpatel77/ProjectToto">Source Code</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# Map and table section
st.markdown('<div class="content">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('### County Risk Table')
    top10_risks = st.session_state.df_st[['county', 'risk']].sort_values(by='risk', ascending=False).head(10)
    st.dataframe(top10_risks.style.set_table_styles(
        [{'selector': 'table', 'props': [('font-size', '18px')]}]
    ))

with col2:
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
    folium_static(m, width=700, height=500)

st.markdown('</div>', unsafe_allow_html=True)

# Pause and Manual Refresh buttons
st.markdown('<div style="display: flex; justify-content: center; margin-top: 20px;">', unsafe_allow_html=True)
if st.button('Pause'):
    st.stop()

if st.button('Manual Refresh'):
    st.session_state.df_st = load_dataframe()
    st.rerun()

# Timestamp
max_time = get_max_time(st.session_state.df_st)
st.markdown(f'<div style="text-align: right;">Predictions as of {max_time}</div>', unsafe_allow_html=True)
