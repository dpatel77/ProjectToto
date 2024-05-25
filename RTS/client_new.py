import asyncio
import aiohttp
import pandas as pd
import json
import pickle
import xgboost
import os
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import folium_static

# Define the features the model was trained on
features = ['temperature_2m', 'relative_humidity_2m', 'rain', 'pressure_msl', 'surface_pressure', 
            'wind_speed_10m', 'wind_speed_100m', 'wind_direction_10m', 'wind_direction_100m', 
            'soil_temperature_0_to_7cm', 'wind_shear']

# Initialize an empty DataFrame for storing predictions
df_st = pd.DataFrame(columns=['Time', 'County', 'Risk'])

# Load the XGBoost model
script_dir = os.path.dirname(__file__)  # Get the directory of the current script
model_path = os.path.join(script_dir, 'xgb_model.pkl')

with open(model_path, 'rb') as file:
    model = pickle.load(file)

# Load Iowa county boundaries
geojson_path = os.path.join(script_dir, 'Iowa_County_Boundaries.geojson')
iowa_geo = gpd.read_file(geojson_path)

# Define the update_predictions function
def update_predictions(new_record, df_st, model, features):
    # Extract the timestamp from the new record
    new_time = new_record['time']
    
    # Update max_time to be the latest timestamp
    max_time = new_time if df_st.empty else max(df_st['Time'].max(), new_time)
    
    county = new_record['county_name']
    
    # Check if the county is already in df_st
    if not df_st.empty and county in df_st['County'].values:
        # Remove the existing record for the county
        df_st = df_st[df_st['County'] != county]
    
    # Extract features for prediction
    X = pd.DataFrame([new_record])[features].values.reshape(1, -1)
    
    # Make a prediction (probability of positive class)
    pred = model.predict_proba(X)[0][1]
    
    # Append the new prediction to df_st
    new_prediction = pd.DataFrame([{'Time': new_time, 'County': county, 'Risk': pred}])
    if not new_prediction.isna().all().all():
        st.write("New prediction: ", new_prediction)
        st.write("DataFrame before concat: ", df_st)
        df_st = pd.concat([df_st, new_prediction], ignore_index=True)
        st.write("DataFrame after concat: ", df_st)
    
    # Sort df_st by the Risk value in descending order
    df_st = df_st.sort_values(by='Risk', ascending=False)
    
    return df_st, max_time

# Async function to stream data from the server
async def stream_data(url):
    global df_st
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async for line in response.content:
                if line:
                    record = json.loads(line.decode('utf-8'))
                    df_st, _ = update_predictions(record, df_st, model, features)
                    st.rerun()

# Streamlit UI setup
st.title('Iowa County Tornado Risk')

# Define color thresholds and hex codes
def get_color(risk):
    if risk > 0.85:
        return '#FF0000'  # Red
    elif risk > 0.5:
        return '#FFFF00'  # Yellow
    else:
        return '#00FF00'  # Green

# Logo and Timestamp
logo_path = os.path.join(script_dir, 'project_toto_logo.png')
st.image(logo_path, width=100)
st.write(f"Iowa County Tornado Risk as of: {df_st['Time'].max() if not df_st.empty else 'N/A'}")

# Create the map
m = folium.Map(location=[42.0, -93.0], zoom_start=7)

# Add counties to the map
for _, row in iowa_geo.iterrows():
    county_name = row['CountyName']  # Replace 'NAME' with the correct column name if different
    risk = df_st[df_st['County'] == county_name]['Risk'].values[0] if county_name in df_st['County'].values else 0
    color = get_color(risk)
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {'fillColor': color, 'color': 'black', 'weight': 2, 'fillOpacity': 0.5}
    ).add_to(m)

# Display the map
folium_static(m)

# URL of the server
url = 'http://localhost:8000'

# Create a new event loop and set it as the current event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Run the event loop
loop.run_until_complete(stream_data(url))
