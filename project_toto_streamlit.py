# # Ensure Streamit is installed:

# conda activate base
# pip install streamlit
# conda install -c conda-forge streamlit

# # Check if Streamlit is installed:

# streamlit --version

# # Running the Streamlit App:

# streamlit hello

# # Environment Issues:
# which python
# which streamlit

# # Reinstall Streamlit:

# pip uninstall streamlit
# pip install streamlit


# import streamlit as st

# st.write("Project Toto")
# st.write("## Real-Time Intelligent System for Tornado Prediction")
# x = st.text_input("Spring 2024", "Real-Time Intelligent Systems")

# if st.button("Click Me"):
#     st.write(f"Your count are you looking for `{x}`")

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime, timedelta

# Load the data
@st.cache_data
def load_data():
    data = pd.read_csv('tornado_risk.csv', header =0)
    data['DateTime'] = pd.to_datetime(data['DateTime'])  # Ensure DateTime is in pandas datetime format
    return data

df = load_data()

# User interface
st.title("Project Toto")
st.header("Real-Time Intelligent System for Tornado Prediction")

st.write(df.columns)  # This will print all column names in the DataFrame
st.write(df.head())  # This will print the first 5 rows of the DataFrame

# Selection of county
county = st.selectbox("Select a County:", df['CountyDisplayName'].unique())

now_time = pd.Timestamp(datetime.now() )
st.write("Now Time: ",now_time)

# Calculate one year ago from today, keeping as Timestamp for comparison
one_year_ago = pd.Timestamp(datetime.now() - timedelta(days=500))
st.write("One year ago: ",one_year_ago)

# Determine the maximum of the minimum datetime in your data and one year ago
min_time = max(df['DateTime'].min(), one_year_ago)
st.write("Min Time: ",min_time)

# Get the maximum datetime from your data
max_time = df['DateTime'].max()
st.write("Max Time: ",max_time)

# Convert Timestamps to POSIX timestamp for slider
min_time_unix = min_time.timestamp()
max_time_unix = max_time.timestamp()

# # Display text for min and max times
st.markdown(f"**Minimum:** {min_time.strftime('%m/%d/%Y %H:%M')} **Maximum:** {max_time.strftime('%m/%d/%Y %H:%M')}")

# # Debug print statements
# st.write(f"Minimum time (Unix): {min_time_unix} -> {datetime.fromtimestamp(min_time_unix)}")
# st.write(f"Maximum time (Unix): {max_time_unix} -> {datetime.fromtimestamp(max_time_unix)}")

# Setup the slider using UNIX timestamps
selected_time_unix = st.slider(
    "Select Date and Time:",
    min_value=int(min_time_unix),
    max_value=int(max_time_unix),
    value=int(min_time_unix),
    # format="MM/DD/YY HH:mm"
)

# Convert selected time back and display
selected_time = datetime.fromtimestamp(selected_time_unix)
st.write(f"Selected Date and Time: {selected_time.strftime('%m/%d/%Y %H:%M')}")

# # Convert selected UNIX timestamp back to Timestamp
# selected_time = pd.Timestamp(datetime.fromtimestamp(selected_time_unix))

# # Display the selected date in your desired format
# st.write("Selected Date and Time:", selected_time.strftime('%m/%d/%Y %I:%M:%S %p'))

# Filter data by selected county and time
filtered_data = df[(df['CountyDisplayName'] == county) & 
                   (df['DateTime'] == selected_time)]

# Other functions and setup...


# Function to prepare and return map df
def map_data(data):
    if data.empty:
        st.write("No data available for selected time and county.")
        return None

    # Make sure these names match your DataFrame's column names
    latitude_mean = data['Latitude'].mean() if 'Latitude' in data.columns else None
    longitude_mean = data['Longitude'].mean() if 'Longitude' in data.columns else None

    if latitude_mean is None or longitude_mean is None:
        st.error("Required columns 'Latitude' or 'Longitude' are missing in the dataset.")
        return None

    # Setup view state for map assuming latitude and longitude are provided
    view_state = pdk.ViewState(
        latitude=latitude_mean,
        longitude=longitude_mean,
        zoom=8,
        pitch=0)

    # Define color scale for TornadoRisk
    color_scale = [
        [0, 128, 255],  # Blue for low risk
        [255, 255, 0],  # Yellow for medium risk
        [255, 0, 0]     # Red for high risk
    ]
    
    data['color'] = data['TornadoRisk'].apply(lambda x: color_scale[0] if x < 0.5 else (color_scale[1] if x < 0.75 else color_scale[2]))

    # Setup PyDeck layer for rendering
    layer = pdk.Layer(
        "GeoJsonLayer",
        data,
        opacity=0.8,
        stroked=False,
        filled=True,
        extruded=True,
        wireframe=True,
        get_fill_color='color',
        get_line_color=[0, 0, 0, 255]
    )

    return pdk.Deck(layers=[layer], initial_view_state=view_state)


deck = map_data(filtered_data)
if deck:
    st.pydeck_chart(deck)
