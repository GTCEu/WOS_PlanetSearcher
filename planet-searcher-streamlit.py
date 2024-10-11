import streamlit as st
import json
import math
import numpy as np
from PIL import Image
from collections import defaultdict

# Function to calculate color similarity
def rgb_euclidean_distance(color1, color2):
    try:
        c1 = list(map(int, color1[:3]))
        c2 = list(map(int, color2[:3]))
        
        if len(c1) != 3 or len(c2) != 3:
            raise ValueError("Color must be a list/tuple of 3 integers")
        
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
        max_distance = math.sqrt(3 * (255 ** 2))
        similarity_percent = (1 - (distance / max_distance)) * 100
        return similarity_percent
    except (TypeError, ValueError):
        return 0

# Function to get the average color of an image
def get_dominant_color(image):
    img_array = np.array(image)
    mean_color = np.mean(img_array, axis=(0, 1))
    return mean_color.astype(int)

# Function to check if a planet matches the search criteria
def planet_matches_criteria(planet_data, criteria):
    if isinstance(planet_data, bool):
        return planet_data == criteria

    for key, value in criteria.items():
        if key == "Temperature":
            if value[0] != "" and ("Temperature" not in planet_data or planet_data["Temperature"] < float(value[0])):
                return False
            if value[1] != "" and ("Temperature" not in planet_data or planet_data["Temperature"] > float(value[1])):
                return False
        elif key == "ExcludedSubTypes":
            if "SubType" in planet_data and planet_data["SubType"] in value:
                return False
        elif key == "Gravity":
            if value[0] != "" and planet_data[key] < float(value[0]):
                return False
            if value[1] != "" and planet_data[key] > float(value[1]):
                return False
        elif key == "Resources":
            if not all(resource in planet_data[key] for resource in value):
                return False
        elif key == "Color":
            if value is not None:
                planet_color = planet_data.get("PrimaryColor", [0, 0, 0])
                color_similarity = rgb_euclidean_distance(value, planet_color)
                if color_similarity < criteria["MinColorSimilarity"]:
                    return False
        elif key in ["Atmosphere", "TidallyLocked", "HasRings"]:
            if value is not None and value != "Any" and planet_data.get(key, False) != value:
                return False
        elif key in ["Type", "SubType"]:
            if value and value != "Any" and planet_data.get(key) != value:
                return False
    return True

# Function to search for planets based on criteria
def search_planets(planetbase, search_criteria, top_5_per_subtype):
    if not isinstance(planetbase, dict):
        raise ValueError("planetbase must be a dictionary")

    matching_planets = defaultdict(list)
    for coords, planet_data in planetbase.items():
        if not isinstance(planet_data, dict):
            continue  # Skip if planet_data is not a dictionary

        # Check if planet_data contains all required keys
        required_keys = ["Type", "SubType", "PrimaryColor", "Resources", "Temperature", "Gravity", "Atmosphere", "TerrainConfig"]
        if not all(key in planet_data for key in required_keys):
            continue

        if planet_matches_criteria(planet_data, search_criteria):
            print("Planet matches criteria!")
            if search_criteria["Color"] is not None:
                planet_color = planet_data.get("PrimaryColor", [0, 0, 0])
                color_similarity = rgb_euclidean_distance(search_criteria["Color"], planet_color)
            else:
                color_similarity = 100  # Set color similarity to 100 when color is None
            subtype = planet_data.get("SubType", "Unknown")
            result = (coords, color_similarity, planet_data.get("PrimaryColor", [0, 0, 0]), subtype)
            matching_planets[subtype].append(result)
        else:
            print("Planet does not match criteria")

    # Sort planets within each subtype
    for subtype in matching_planets:
        if search_criteria["Color"] is not None:
            matching_planets[subtype].sort(key=lambda x: x[1], reverse=True)
            if top_5_per_subtype:
                matching_planets[subtype] = matching_planets[subtype][:5]
    
    return matching_planets

# Streamlit app
st.title("Planet Searcher")

# File uploader for planets.json
uploaded_file = st.file_uploader("Upload planets.json", type="json")
if uploaded_file is not None:
    planetbase = json.load(uploaded_file)
else:
    st.warning("Please upload a planets.json file to proceed.")
    st.stop()

# Search criteria
search_criteria = {}

# Get unique types and subtypes from planetbase
types = {planet.get("Type", "Unknown") for planet in planetbase.values()}
subtypes = {planet.get("SubType", "Unknown") for planet in planetbase.values()}

# Create selectboxes for Type and SubType
search_criteria["Type"] = st.selectbox("Type", [""] + list(types))
search_criteria["SubType"] = st.selectbox("SubType", [""] + list(subtypes))

# Create multiselect for Excluded SubTypes
excluded_subtypes = st.multiselect("Excluded SubTypes", list(subtypes))
search_criteria["ExcludedSubTypes"] = excluded_subtypes

# Create slider for Temperature Range
temp_range = st.slider("Temperature Range (°C)", -273, 1000, (-273, 1000))
search_criteria["Temperature"] = temp_range

# Create radio buttons for Atmosphere, TidallyLocked, HasRings
for key in ["Atmosphere", "TidallyLocked", "HasRings"]:
    value = st.radio(key, [("Yes", True), ("No", False), ("Any", None)], format_func=lambda x: x[0])
    search_criteria[key] = value[1]

# Create slider for Gravity Range
gravity_range = st.slider("Gravity Range (g)", 0.0, 300.0, (0.0, 300.0))
search_criteria["Gravity"] = gravity_range

# Get unique resources from planetbase
all_resources = list(set(resource for planet in planetbase.values() for resource in planet.get("Resources", {}).keys()))

# Create multiselect for Resources
search_criteria["Resources"] = st.multiselect("Resources", all_resources)

# Color
color_option = st.radio("Color Input", ["None", "RGB Values", "Image Upload"])
if color_option == "RGB Values":
    r = st.slider("Red", 0, 255, 128)
    g = st.slider("Green", 0, 255, 128)
    b = st.slider("Blue ", 0, 255, 128)
    search_criteria["Color"] = [r, g, b]
elif color_option == "Image Upload":
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        image = Image.open(uploaded_image)
        dominant_color = get_dominant_color(image)
        search_criteria["Color"] = dominant_color
else:
    search_criteria["Color"] = None
    search_criteria["MinColorSimilarity"] = 0  # Set MinColorSimilarity to 0 when color is None

# Min Color Similarity
search_criteria["MinColorSimilarity"] = st.slider("Min Color Similarity", 0.0, 100.0, 50.0)

# Option for top 5 results per subtype
top_5_per_subtype = st.checkbox("Get top 5 results for each subtype (only applies when color is provided)")

# Search button
if st.button("Search Planets"):
    results = search_planets(planetbase, search_criteria, top_5_per_subtype and search_criteria["Color"] is not None)
    total_planets = sum(len(planets) for planets in results.values())
    st.write(f"Found {total_planets} matching planets across {len(results)} subtypes:")
    
    for subtype, planets in results.items():
        with st.expander(f"{subtype} ({len(planets)} planets)"):
            for index, (coords, similarity, color, subtype) in enumerate(planets):  # Modified line
                col1, col2 = st.columns([1, 4])
                with col1:
                    color_hex = f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}"
                    st.color_picker("", color_hex, key=f"color_picker_{subtype}_{index}", disabled=True)
                with col2:
                    st.write(f"{coords} - Color Similarity: {similarity:.2f}%")

# Instructions
st.markdown("---")
st.markdown("**Instructions:**")
st.markdown("1. Upload a planets.json file to start.")
st.markdown("2. Set your search criteria using the inputs above.")
st.markdown("3. If using color search, you can choose to get the top 5 results for each subtype.")
st.markdown("4. Adjust the minimum color similarity slider to filter results based on color matching.")
st.markdown("5. Click 'Search Planets' to see the results.")
st.markdown("6. Results are organized by subtype in collapsible sections.")
st.markdown("7. The color picker shows the planet's color, and the text shows the system, coordinates, and color similarity.")
