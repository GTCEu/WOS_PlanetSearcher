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
def get_image_colors(image):
    img_array = np.array(image)
    mean_color = np.mean(img_array, axis=(0, 1))
    return mean_color.astype(int)

# Function to check if a planet matches the search criteria
def planet_matches_criteria(planet_data, criteria):
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
                planet_color = planet_data.get("Color", [0, 0, 0])
                color_similarity = rgb_euclidean_distance(value, planet_color)
                if color_similarity < criteria["MinColorSimilarity"]:
                    return False
        elif key in ["Atmosphere", "TidallyLocked", "HasRings"]:
            if value is not None and planet_data.get(key, False) != value:
                return False
        elif key in ["Type", "SubType"]:
            if value and planet_data.get(key) != value:
                return False
    return True

# Function to search for planets based on criteria
def search_planets(planetbase, search_criteria, top_5_per_subtype=False):
    matching_planets = defaultdict(list)
    for system in planetbase:
        for planet_coords, planet_data in planetbase[system].items():
            if planet_matches_criteria(planet_data, search_criteria):
                planet_color = planet_data.get("Color", [0, 0, 0])
                color_similarity = rgb_euclidean_distance(search_criteria["Color"], planet_color) if search_criteria["Color"] is not None else 100
                subtype = planet_data.get("SubType", "Unknown")
                result = (system, planet_coords, color_similarity, planet_color, subtype, planet_data)
                matching_planets[subtype].append(result)
    
    # Sort planets within each subtype
    for subtype in matching_planets:
        matching_planets[subtype].sort(key=lambda x: x[2], reverse=True)
        if top_5_per_subtype:
            matching_planets[subtype] = matching_planets[subtype][:5]
    
    return matching_planets

# Function to display detailed planet information
def display_planet_info(planet_data):
    st.subheader("Planet Details")
    for key, value in planet_data.items():
        if key == "Color":
            color_hex = f"#{int(value[0]):02x}{int(value[1]):02x}{int(value[2]):02x}"
            st.color_picker(f"{key}:", color_hex, disabled=True)
        elif isinstance(value, (list, tuple)):
            st.write(f"{key}: {', '.join(map(str, value))}")
        else:
            st.write(f"{key}: {value}")

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

# Type and SubType
search_criteria["Type"] = st.selectbox("Type", [""] + list(set(planet["Type"] for system in planetbase for planet in planetbase[system].values() if "Type" in planet)))
search_criteria["SubType"] = st.selectbox("SubType", [""] + list(set(planet["SubType"] for system in planetbase for planet in planetbase[system].values() if "SubType" in planet)))

# Excluded SubTypes
excluded_subtypes = st.multiselect("Excluded SubTypes", list(set(planet["SubType"] for system in planetbase for planet in planetbase[system].values() if "SubType" in planet)))
search_criteria["ExcludedSubTypes"] = excluded_subtypes

# Temperature
temp_range = st.slider("Temperature Range (°F)", -273, 400, (-273, 400))
search_criteria["Temperature"] = temp_range

# Atmosphere, TidallyLocked, HasRings
for key in ["Atmosphere", "TidallyLocked", "HasRings"]:
    value = st.radio(key, [("Yes", True), ("No", False), ("Any", None)], format_func=lambda x: x[0])
    search_criteria[key] = value[1]

# Gravity
gravity_range = st.slider("Gravity Range (g)", 0.0, 300.0, (0.0, 300.0))
search_criteria["Gravity"] = gravity_range

# Resources
all_resources = list(set(resource for system in planetbase for planet in planetbase[system].values() for resource in planet.get("Resources", [])))
search_criteria["Resources"] = st.multiselect("Resources", all_resources)

# Color
color_option = st.radio("Color Input", ["None", "RGB Values", "Image Upload"])
if color_option == "RGB Values":
    r = st.slider("Red", 0, 255, 128)
    g = st.slider("Green", 0, 255, 128)
    b = st.slider("Blue", 0, 255, 128)
    search_criteria["Color"] = [r, g, b]
elif color_option == "Image Upload":
    uploaded_image = st.file_uploader("Upload an image for color matching", type=["png", "jpg", "jpeg"])
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        search_criteria["Color"] = get_image_colors(image)
        st.image(image, caption="Uploaded Image", use_column_width=True)
else:
    search_criteria["Color"] = None

# Minimum color similarity slider
search_criteria["MinColorSimilarity"] = st.slider("Minimum Color Similarity (%)", 0, 100, 80)

# Option for top 5 results per subtype
top_5_per_subtype = st.checkbox("Get top 5 results for each subtype (only applies when color is provided)")

# Search button
if st.button("Search Planets"):
    results = search_planets(planetbase, search_criteria, top_5_per_subtype and search_criteria["Color"] is not None)
    total_planets = sum(len(planets) for planets in results.values())
    st.write(f"Found {total_planets} matching planets across {len(results)} subtypes:")
    
    for subtype, planets in results.items():
        with st.expander(f"{subtype} ({len(planets)} planets)"):
            for index, (system, coords, similarity, color, _, planet_data) in enumerate(planets):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    color_hex = f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}"
                    st.color_picker("", color_hex, key=f"color_picker_{subtype}_{index}", disabled=True)
                with col2:
                    st.write(f"{system}, {coords} - Color Similarity: {similarity:.2f}%")
                with col3:
                    if st.button("More Info", key=f"info_button_{subtype}_{index}"):
                        display_planet_info(planet_data)

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
st.markdown("8. Click the 'More Info' button next to a planet to see detailed information about it.")
