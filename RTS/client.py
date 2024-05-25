import asyncio
import aiohttp
import pandas as pd
import json
import pickle
import os

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

# Define the update_predictions function
def update_predictions(new_record, df_st, model, features):
    # Extract the timestamp from the new record
    new_time = new_record['time']
    
    # Update max_time to be the latest timestamp
    max_time = max(df_st['Time'].max(), new_time) if not df_st.empty else new_time
    
    county = new_record['county_name']
    
    # Check if the county is already in df_st
    if county in df_st['County'].values:
        # Remove the existing record for the county
        df_st = df_st[df_st['County'] != county]
    
    # Extract features for prediction
    X = pd.DataFrame([new_record])[features].values.reshape(1, -1)
    
    # Make a prediction (probability of positive class)
    pred = model.predict_proba(X)[0][1]
    
    # Append the new prediction to df_st
    new_prediction = {'Time': new_time, 'County': county, 'Risk': pred}
    df_st = pd.concat([df_st, pd.DataFrame([new_prediction])], ignore_index=True)
    
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
                    print(df_st)  # Print the updated DataFrame to the console

# URL of the server
url = 'http://localhost:8000'

# Run the event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(stream_data(url))
