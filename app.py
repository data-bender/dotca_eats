import streamlit as st
import pandas as pd
from ca_scrapper import find_ca_food_places, FOOD_TYPES  

# --- PAGE CONFIG ---
st.set_page_config(page_title="Canadian Food Places Finder", layout="centered")

st.title("🍽 Canadian Food Places Finder")

# --- USER INPUTS ---
postal_code = st.text_input("Enter postal code:", "")

radius_km = st.slider(
    "Search radius (km):", 
    min_value=1, 
    max_value=15, 
    value=5,  # default
    step=1
)

selected_types = st.multiselect(
    "Select restaurant/food types:",
    options=FOOD_TYPES,
    default=[FOOD_TYPES[0]],
    help="Select at least one type"
)

# --- SEARCH BUTTON ---
if st.button("Search"):

    if not postal_code:
        st.warning("Please enter a postal code.")
    elif not selected_types:
        st.warning("Please select at least one food type.")
    else:
        with st.spinner("Fetching results... hang tight, this might take a few minutes."):
            try:
                df = find_ca_food_places(postal_code, radius_km, selected_types)
                if df.empty:
                    st.info("No .ca websites found for the selected criteria.")
                else:
                    # Display the results in the front-end
                    df_display = df.copy()
                    df_display["maps_link"] = df_display["maps_link"].apply(
                        lambda x: f'<a href="{x}" target="_blank">Open Map</a>'
                    )
                    df_display["website"] = df_display["website"].apply(
                        lambda x: f'<a href="{x}" target="_blank">{x}</a>'
                    )

                    st.success(f"Found {len(df)} .ca food websites!")
                    # st.dataframe(df)
                    
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download results as CSV",
                        data=csv,
                        file_name="ca_food_places.csv",
                        mime="text/csv"
                    )
                    
                    df_table = df_display.drop(columns=["lat", "lon"], errors="ignore")
                    st.write(
                        df_table.to_html(escape=False, index=False),
                        unsafe_allow_html=True
                    )

                    st.subheader("📍 Map of results")
                    map_df = df[['distance_km', 'name', 'address', 'website', 'maps_link', 'types']].copy()
                    map_df['lat'] = df.apply(lambda r: r.get('geometry', {}).get('lat', None), axis=1)
                    map_df['lon'] = df.apply(lambda r: r.get('geometry', {}).get('lon', None), axis=1)
                    
                    st.map(df[['lat', 'lon']])

            except Exception as e:
                st.error(f"Error: {e}")
