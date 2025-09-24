import requests
import math
import pandas as pd
import time
import streamlit as st


# --- CONFIGURATION ---
API_KEY = st.secrets["API_KEY"]
FOOD_TYPES = ["restaurant", "cafe", "bar", "bakery", "meal_takeaway", "meal_delivery", "food"]

# --- HELPER FUNCTIONS ---
def get_lat_lng_from_postal(postal_code):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": f"{postal_code}, Canada", "key": API_KEY}
    response = requests.get(url, params=params).json()
    if response.get("results"):
        loc = response["results"][0]["geometry"]["location"]
        print(response)
        return loc["lat"], loc["lng"]
    else:
        raise ValueError(f"Postal code not found: {postal_code}")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_places(lat, lng, radius_m, place_type):
    all_results = []
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{lat},{lng}", "radius": radius_m, "type": place_type, "key": API_KEY}

    while True:
        response = requests.get(url, params=params).json()
        # filtered = [r for r in response.get("results", []) if any(t in FOOD_TYPES for t in r.get("types", []))]
        # all_results.extend(filtered)
        all_results.extend(response.get("results", []))

        next_page = response.get("next_page_token")
        if next_page:
            time.sleep(2)
            params = {"pagetoken": next_page, "key": API_KEY}
        else:
            break
    return all_results

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "fields": "website,formatted_address,name,geometry,types", "key": API_KEY}
    response = requests.get(url, params=params).json()
    return response.get("result", {})

def create_maps_link(place_id):
    return f"https://maps.google.com/?q=place_id:{place_id}"

def find_ca_food_places(postal_code, radius_km, selected_types):
    lat_origin, lng_origin = get_lat_lng_from_postal(postal_code)
    radius_m = radius_km * 1000
    data = []

    for place_type in selected_types:
        places = get_places(lat_origin, lng_origin, radius_m, place_type)
        for place in places:
            details = get_place_details(place["place_id"])
            loc = details.get("geometry", {}).get("location", {})
            lat, lng = loc.get("lat"), loc.get("lng")
            website = details.get("website")
            if website and (website.endswith(".ca") or ".ca/" in website):
                loc = details.get("geometry", {}).get("location", {})
                lat, lng = loc.get("lat"), loc.get("lng")
                distance_m = haversine(lat_origin, lng_origin, lat, lng) if lat and lng else None
                # Only include types from our predefined list
                types = [t for t in details.get("types", []) if t in FOOD_TYPES]
                data.append({
                    "name": details.get("name"),
                    "website": website,
                    "maps_link": create_maps_link(place["place_id"]),
                    "address": details.get("formatted_address"),
                    "distance_km": round(distance_m / 1000, 2) if distance_m else None,
                    "types": ", ".join(types),
                    "lat": lat,
                    "lon": lng
                })

    # Remove duplicates by name
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.drop_duplicates(subset=["name"]).sort_values(by="distance_km")

    return df

def select_food_types():
    print("Select food types by number (comma-separated):")
    for i, t in enumerate(FOOD_TYPES, start=1):
        print(f"{i}. {t}")
    selection = input("Enter choices (e.g. 1,3,5): ").strip()
    indices = [int(x)-1 for x in selection.split(",") if x.isdigit() and 0 <= int(x)-1 < len(FOOD_TYPES)]
    return [FOOD_TYPES[i] for i in indices]

# --- MAIN ---
if __name__ == "__main__":
    postal_code = input("Enter postal code: ").strip()
    radius_km = float(input("Enter radius in kilometers (e.g. 5): ").strip())
    selected_types = select_food_types()

    if not selected_types:
        print("No food types selected. Exiting.")
    else:
        try:
            df = find_ca_food_places(postal_code, radius_km, selected_types)
            print(f"\nFound {len(df)} .ca food websites.\n")
            print(df)
            # Export
            df.to_csv("food_places_2.csv", index=False)
            # df.to_json("food_places.json", orient="records", indent=2)
        except Exception as e:
            print("Error:", e)
