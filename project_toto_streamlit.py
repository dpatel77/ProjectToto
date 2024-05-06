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
import pydeck as pdk
from datetime import datetime, timedelta

# Load the data
@st.cache
def load_data():
    data = pd.read_csv('tornado_risk.csv')
    return data

df = load_data()

# User interface
st.title("Project Toto")
st.header("Real-Time Intelligent System for Tornado Prediction")

# Convert 'DateTime' column to datetime type if not already
df['DateTime'] = pd.to_datetime(df['DateTime'])

# Selection of county
county = st.selectbox("Select a County:", df['CountyDisplayName'].unique())

# Timeframe toggle
one_year_ago = datetime.now() - timedelta(days=365)
min_time = max(df['DateTime'].min(), one_year_ago)
max_time = df['DateTime'].max()
selected_time = st.slider("Select Date and Time:", min_value=min_time, max_value=max_time, value=min_time, format="MM/DD/YY - hh:mm")

# Filter data by selected county and time
filtered_data = df[(df['CountyDisplayName'] == county) & (df['DateTime'] == selected_time)]

# Function to prepare and return map data
def map_data(data):
    # Setup view state for map
    view_state = pdk.ViewState(
        latitude=data['latitude'].mean(),  # Assuming latitude information is available
        longitude=data['longitude'].mean(),  # Assuming longitude information is available
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

st.pydeck_chart(map_data(filtered_data))
