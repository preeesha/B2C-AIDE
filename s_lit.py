import streamlit as st
import pydeck as pdk
import pandas as pd
import httpx  # Use httpx for async requests
from PIL import Image
import asyncio

# Disable Jupyter support in pydeck
import pydeck.bindings.deck
pydeck.bindings.deck.has_jupyter_extra = lambda: False

# FastAPI URL (change this to your actual server address)
API_URL = "http://localhost:8000/add_city"

# Set up the session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "home"

def go_to_page(page):
    st.session_state.page = page

# Color mapping for each unique cluster_id
CLUSTER_COLORS = {
    0: [255, 0, 0], 1: [0, 255, 0], 2: [0, 0, 255], 3: [255, 255, 0],
    4: [255, 0, 255], 5: [0, 255, 255], 6: [128, 0, 128], 7: [128, 128, 0],
    8: [128, 0, 0], 9: [0, 128, 0], 10: [0, 0, 128], 11: [128, 128, 128]
}

# Function to send POST request asynchronously and get stores data
async def get_city_stores(city_name):
    async with httpx.AsyncClient() as client:
        try:
            # Send the POST request to FastAPI, adhering to the new schema
            response = await client.post(API_URL, json={"name": city_name})  # 'name' key matches the City schema
            response.raise_for_status()
            # Parse the JSON response
            city_data = response.json()
            return city_data
        except httpx.RequestError as e:
            st.error(f"Error fetching data: {e}")
            return {}

# Home page
if st.session_state.page == "home":
    st.title("Croma Sales Analysis")
    image = st.image("Electronics.jpg", caption="Electronics Store", use_column_width=True)

    # Sidebar with buttons
    st.sidebar.title("Options")
    if st.sidebar.button("Add New Offline Store"):
        go_to_page("add_store")
    if st.sidebar.button("Previous Sales Analysis"):
        st.write("Functionality for previous sales analysis will be implemented here.")
    if st.sidebar.button("Demand Forecasting"):
        st.write("Functionality for demand forecasting will be implemented here.")
    if st.sidebar.button("Competitor Analysis"):
        st.write("Functionality for competitor analysis will be implemented here.")

# Page for adding a new offline store
elif st.session_state.page == "add_store":
    st.title("Add New Offline Store")

    city = st.text_input("Enter City Name")

    if st.button("Show Potential Spots"):
        if city:
            st.write(f"Fetching data for city: {city}...")

            # Get the stores data asynchronously
            city_data = asyncio.run(get_city_stores(city))

            # Check if valid city data is returned
            if city_data and 'stores' in city_data:
                stores = city_data['stores']
                city_lat = city_data.get('lat')
                city_long = city_data.get('long')
                city_name = city_data["name"]
                st.write("DISTANCE BASED CLUSTERING OF HOUSES AND BUILDINGS")
                image = Image.open(f"plots/{city_name}_plot.png")
                st.image(image, caption="DIVIDED INTO 12 CLUSTERS", use_column_width=True)
                
                store_locations = pd.DataFrame({
                    'lat': [store["coord"][0] for store in stores],
                    'lon': [store["coord"][1] for store in stores],
                    'cluster_id': [store["cluster_id"] for store in stores],
                    'houses': [store["houses"] for store in stores],
                    'air_dist': [store["air_dist"] for store in stores],
                    'station_dist': [store["station_dist"] for store in stores],
                    'city_name': [city_name for i in stores],  # Assign the city name to each store
                    'id': [store["id"] for store in stores] 
                })

                # Map cluster colors dynamically
                store_locations['color'] = store_locations['cluster_id'].map(lambda x: CLUSTER_COLORS.get(x, [255, 255, 255]))

                # Create pydeck layer with hover tooltips
                map_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=store_locations,
                    get_position='[lon, lat]',
                    get_radius=130,  # Adjust marker size as needed
                    get_fill_color='[color[0], color[1], color[2]]',
                    pickable=True
                )

                # Tooltip with additional store info
                tooltip = {
                    "html": """
                        <b>Houses:</b> {houses}<br/>
                        <b>Air Distance:</b> {air_dist}<br/>
                        <b>Station Distance:</b> {station_dist}<br/>
                        <img src="http://localhost:8000/static/{city_name}_{id}.png" alt="Store Image" width="150" height="100">
                    """,
                    "style": {"color": "white"}
                }



                # Set view state to center over the city's lat/long
                view_state = pdk.ViewState(
                    latitude=city_lat if city_lat else 20.5937,  # Default to India's latitude
                    longitude=city_long if city_long else 78.9629,  # Default to India's longitude
                    zoom=10,  # Zoom level centered over the city
                    pitch=0
                )

                # Display the map with stores
                st.pydeck_chart(pdk.Deck(
                    layers=[map_layer],
                    initial_view_state=view_state,
                    tooltip=tooltip
                ))
            else:
                st.warning(f"No store data found for city: {city}")
        else:
            st.warning("Please enter a city name.")

    if st.button("Go Back"):
        go_to_page("home")
