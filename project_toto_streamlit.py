import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from datetime import datetime
import json

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
selected_time = st.sidebar.time_input("Select Time", value=pd.Timestamp('2023-02-26 07:11:58').time())
selected_datetime = pd.Timestamp.combine(selected_date, selected_time)

# Filter data based on selected datetime
filtered_data = merged_gdf[merged_gdf['DateTime'] == selected_datetime]
st.write('Filtered Data: ', filtered_data.drop(columns='geometry').head())

# Define color scale logic and apply it to the filtered DataFrame
def apply_color_scale(df):
    colors = []
    for risk in df['TornadoRisk']:
        if pd.isna(risk):
            colors.append('rgba(0,0,0,0)')  # Transparent if no data
        elif risk < 0.5:
            colors.append('blue')  # Blue
        elif risk < 0.75:
            colors.append('yellow')  # Yellow
        else:
            colors.append('red')  # Red
    df['color'] = colors

apply_color_scale(filtered_data)
st.write('Filtered Data with Color:', filtered_data.drop(columns='geometry').head())

# Ensure the filtered data contains the geometry and convert DateTime to string
filtered_geojson = gpd.GeoDataFrame(filtered_data, geometry='geometry')
filtered_geojson['DateTime'] = filtered_geojson['DateTime'].astype(str)

# Convert GeoDataFrame to GeoJSON
filtered_geojson_json = json.loads(filtered_geojson.to_json())
st.write('filtered_geojson_json:', json.dumps(filtered_geojson_json, indent=2))

# Create a map with Plotly Express
fig = px.choropleth(
    filtered_geojson,
    geojson=filtered_geojson_json,
    locations='CountyName',
    featureidkey="properties.CountyName",
    color='TornadoRisk',
    color_continuous_scale=[
        [0, 'rgba(0,0,0,0)'],  # Transparent
        [0.5, 'blue'],
        [0.75, 'yellow'],
        [1, 'red']
    ],
    hover_name='CountyName',
    hover_data={'CountyName': False, 'TornadoRisk': True},
    labels={'TornadoRisk': 'Tornado Risk'}
)

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_colorbar=dict(
    title="Tornado Risk",
    tickvals=[0, 0.5, 0.75, 1],
    ticktext=['No Data', '<0.5', '0.5-0.75', '>0.75']
))

st.plotly_chart(fig)

st.write("Select a date and time to view the tornado risk in Iowa. The map shows the tornado risk for each county in Iowa. Use the sidebar to select a specific date and time. The color scale represents the tornado risk level: Blue (<0.5), Yellow (<0.75), Red (<1.0).")




# import streamlit as st
# import pandas as pd
# import geopandas as gpd
# import plotly.express as px
# from datetime import datetime

# # Set up the Streamlit app
# st.title('Iowa Tornado Risk Map')
# st.write('This app visualizes the tornado risk for each county in Iowa.')

# # Load tornado risk data
# @st.cache_data
# def load_tornado_risk_data():
#     data = pd.read_csv('tornado_risk.csv')
#     data['DateTime'] = pd.to_datetime(data['DateTime'])  # Ensure proper datetime format
#     # Trim whitespace from all string columns and convert County Name to uppercase
#     data = data.applymap(lambda x: x.strip() if isinstance(x, str) else x)
#     data['County Name'] = data['County Name'].str.upper().str.strip()
#     return data

# tornado_data = load_tornado_risk_data()
# st.write('Tornado Data', tornado_data.head())

# # Load GeoJSON file
# @st.cache_data
# def load_geojson():
#     gdf = gpd.read_file('Iowa_County_Boundaries.geojson')
#     gdf['CountyName'] = gdf['CountyName'].str.upper().str.strip()  # Ensure proper casing
#     # Trim whitespace from all string columns
#     gdf = gdf.applymap(lambda x: x.strip() if isinstance(x, str) else x)
#     return gdf

# geojson_data = load_geojson()
# st.write('GeoJSON Data', geojson_data.head())

# # Convert GeoJSON to DataFrame
# geojson_df = pd.DataFrame(geojson_data)
# st.write('GeoJSON DataFrame:', geojson_df.head())

# # Ensure both columns are of string type
# geojson_df['CountyName'] = geojson_df['CountyName'].astype(str)
# tornado_data['County Name'] = tornado_data['County Name'].astype(str)

# # Check unique values and their lengths before merging
# unique_tornado_counties = tornado_data['County Name'].unique()
# unique_geojson_counties = geojson_df['CountyName'].unique()

# # Create a DataFrame to display lengths
# county_check = pd.DataFrame({
#     'Tornado County Name': unique_tornado_counties,
#     'Tornado Length': [len(name) for name in unique_tornado_counties],
#     'GeoJSON County Name': unique_geojson_counties,
#     'GeoJSON Length': [len(name) for name in unique_geojson_counties]
# })

# st.write("County Name Length Check:", county_check)

# # Merging GeoJSON data with tornado risk data
# @st.cache_data
# def merge_data(_geojson_df, _tornado_data):
#     merged_data = _geojson_df.merge(_tornado_data, left_on='CountyName', right_on='County Name', how='left')
#     return merged_data

# merged_gdf = merge_data(geojson_df, tornado_data)
# st.write('Merged Data', merged_gdf[['DateTime', 'TornadoRisk', 'County Name']].head(20))

# # Check for any non-matching entries
# non_matching = merged_gdf[merged_gdf['TornadoRisk'].isna()]
# st.write('Non-matching entries after merge:', non_matching.head(20))

# # Static variable for date and time
# selected_date = st.sidebar.date_input("Select Date", value=pd.Timestamp('2023-02-26'))
# selected_time = st.sidebar.time_input("Select Time", value=pd.Timestamp('2023-02-26 07:11:58').time())
# selected_datetime = pd.Timestamp.combine(selected_date, selected_time)

# # Filter data based on selected datetime
# filtered_data = merged_gdf[merged_gdf['DateTime'] == selected_datetime]
# st.write('Filtered Data: ', filtered_data[['DateTime', 'TornadoRisk', 'County Name']].head())

# # Define color scale logic and apply it to the filtered DataFrame
# def apply_color_scale(df):
#     colors = []
#     for risk in df['TornadoRisk']:
#         if pd.isna(risk):
#             colors.append('rgba(0,0,0,0)')  # Transparent if no data
#         elif risk < 0.5:
#             colors.append('blue')  # Blue
#         elif risk < 0.75:
#             colors.append('yellow')  # Yellow
#         else:
#             colors.append('red')  # Red
#     df['color'] = colors

# apply_color_scale(filtered_data)
# st.write('Filtered Data with Color:', filtered_data[['DateTime', 'TornadoRisk', 'County Name', 'color']].head())

# # Convert filtered data to GeoJSON
# filtered_geojson = gpd.GeoDataFrame(filtered_data, geometry=geojson_data.geometry)

# # Create a map with Plotly Express
# fig = px.choropleth(
#     filtered_geojson,
#     geojson=filtered_geojson.geometry.__geo_interface__,
#     locations='CountyName',
#     color='TornadoRisk',
#     color_continuous_scale=[
#         [0, 'rgba(0,0,0,0)'],  # Transparent
#         [0.5, 'blue'],
#         [0.75, 'yellow'],
#         [1, 'red']
#     ],
#     hover_name='CountyName',
#     hover_data={'CountyName': False, 'TornadoRisk': True},
#     labels={'TornadoRisk': 'Tornado Risk'}
# )

# fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_colorbar=dict(
#     title="Tornado Risk",
#     tickvals=[0, 0.5, 0.75, 1],
#     ticktext=['No Data', '<0.5', '0.5-0.75', '>0.75']
# ))

# st.plotly_chart(fig)

# st.write("Select a date and time to view the tornado risk in Iowa. The map shows the tornado risk for each county in Iowa. Use the sidebar to select a specific date and time. The color scale represents the tornado risk level: Blue (<0.5), Yellow (<0.75), Red (<1.0).")



# # Convert filtered data to GeoJSON
# filtered_gdf = filtered_data.dropna(subset=['geometry'])
# geojson = json.loads(filtered_gdf.to_json())

# # Add title and header
# st.header("Tornado Risk by County in Iowa")

# # Geographic Map
# fig = go.Figure(
#     go.Choroplethmapbox(
#         geojson=geojson,
#         locations=filtered_gdf.index,
#         z=filtered_gdf['TornadoRisk'],
#         colorscale="Viridis",
#         marker_opacity=0.5,
#         marker_line_width=0,
#         featureidkey="properties.index"
#     )
# )
# fig.update_layout(
#     mapbox_style="carto-positron",
#     mapbox_zoom=6.5,
#     mapbox_center={"lat": 41.878, "lon": -93.097},
#     width=800,
#     height=600,
#     margin={"r": 0, "t": 0, "l": 0, "b": 0}
# )
# st.plotly_chart(fig)

# st.write("Select a date and time to view the tornado risk in Iowa. The map shows the tornado risk for each county in Iowa. Use the sidebar to select a specific date and time. The color scale represents the tornado risk level. Data source: [NOAA Storm Prediction Center](https://www.spc.noaa.gov/gis/svrgis/).")


# Optionally add more visualizations or data insights below

# # Create a folium map
# m = folium.Map(location=[41.878, -93.097], zoom_start=7)

# # Add counties to the map with colors based on tornado risk
# for _, row in filtered_data.iterrows():
#     geo_json = folium.GeoJson(
#         row['geometry'].__geo_interface__,
#         style_function=lambda feature, color=row['color']: {
#             'fillColor': color,
#             'color': 'black',
#             'weight': 1,
#             'fillOpacity': 0.7,
#         },
#         tooltip=folium.GeoJsonTooltip(fields=['County Name', 'TornadoRisk'], aliases=['County:', 'Tornado Risk:'])
#     )
#     geo_json.add_to(m)

# # Display the map in Streamlit
# folium_static(m)


# ### Folium

# # Create a folium map
# m = folium.Map(location=[41.878, -93.097], zoom_start=7)

# # Add counties to the map
# folium.GeoJson(shapefile_data).add_to(m)

# # Display the map in Streamlit
# folium_static(m)



# # # Create PyDeck map
# # view_state = pdk.ViewState(latitude=42.0308, longitude=-93.6319, zoom=7)

# # layer = pdk.Layer(
# #     'GeoJsonLayer',
# #     data=filtered_data,
# #     get_fill_color='color',  # Use the precomputed 'color' column
# #     get_line_color=[255, 255, 255],  # White lines for county boundaries
# #     pickable=True,
# #     stroked=True,  # Enable stroking to draw boundaries
# #     filled=True,
# #     line_width_min_pixels=1,  # Minimum line width in pixels
# #     extruded=False,
# # )

# # deck = pdk.Deck(
# #     layers=[layer],
# #     initial_view_state=view_state,
# #     tooltip={"text": "{CountyName}: {TornadoRisk}"}
# # )

# # st.pydeck_chart(deck)

# # # Filter and map setup
# # selected_datetime = pd.Timestamp(st.sidebar.date_input("Select Date", value=pd.Timestamp.now()))
# # filtered_data = merged_gdf[merged_gdf['DateTime'] == selected_datetime]

# # Ensure data is not empty
# if filtered_data.empty:
#     st.error("No data available for the selected date and time.")
# else:
#     # Proceed with visualization
#     view_state = pdk.ViewState(latitude=42.0308, longitude=-93.6319, zoom=7)
#     layer = pdk.Layer(
#         'GeoJsonLayer',
#         data=filtered_data,
#         get_fill_color='color',
#         get_line_color=[255, 255, 255],
#         pickable=True,
#         stroked=True,
#         filled=True,
#         line_width_min_pixels=1,
#         extruded=False,
#     )
#     deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{CountyName}: {TornadoRisk}"})
#     st.pydeck_chart(deck)

# # ### Plotly
# # import streamlit as st
# # import pandas as pd
# # import geopandas as gpd
# # import matplotlib.pyplot as plt

# # # Load data
# # @st.cache_data
# # def load_data():
# #     gdf = gpd.read_file('Iowa_County_Boundaries/IowaCounties.shp')
# #     return gdf

# # gdf = load_data()

# # # Plot
# # fig, ax = plt.subplots(figsize=(10, 10))
# # gdf.plot(ax=ax, color='white', edgecolor='black')
# # ax.set_title('Iowa Counties')

# # # Display in Streamlit
# # st.pyplot(fig)


