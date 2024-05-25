import asyncio
import aiohttp
import pandas as pd
import json
import pickle
import xgboost
import os

# Load the XGBoost model
script_dir = os.path.dirname(__file__)
model_path = os.path.join(script_dir, 'xgb_model.pkl')

with open(model_path, 'rb') as file:
    model = pickle.load(file)

# Define the features the model was trained on
features = ['temperature_2m', 'relative_humidity_2m', 'rain', 'pressure_msl', 'surface_pressure', 
            'wind_speed_10m', 'wind_speed_100m', 'wind_direction_10m', 'wind_direction_100m', 
            'soil_temperature_0_to_7cm', 'wind_shear']

# Function to update predictions in the Parquet file
def update_predictions(new_record, model, features, parquet_file='RTS/tornado_risk.parquet'):
    # Extract the timestamp and county from the new record
    new_time = new_record['time']
    county = new_record['county_name']
    
    # Extract features for prediction
    X = pd.DataFrame([new_record])[features].values.reshape(1, -1)
    
    # Make a prediction (probability of positive class)
    pred = model.predict_proba(X)[0][1]
    
    # Load existing data
    try:
        df = pd.read_parquet(parquet_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['time', 'county', 'risk'])
    
    # Remove the existing record for the county if it exists
    df = df[df['county'] != county]
    
    # Append the new prediction
    new_prediction = pd.DataFrame([{'time': new_time, 'county': county, 'risk': pred}])
    df = pd.concat([df, new_prediction], ignore_index=True)
    
    # Save back to the Parquet file
    df.to_parquet(parquet_file)

# Async function to stream data from the server
async def stream_data(url, model, features):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async for line in response.content:
                if line:
                    record = json.loads(line.decode('utf-8'))
                    update_predictions(record, model, features)

if __name__ == "__main__":
    url = 'http://localhost:8000'
    #clear weather data
    os.remove("RTS/tornado_risk.parquet")
    asyncio.run(stream_data(url, model, features))
