import streamlit as st
import json
import math
import numpy as np
from PIL import Image
from collections import defaultdict

# ... (keep all the previous functions unchanged) ...

# Streamlit app
st.title("Planet Searcher")

# File uploader for planets.json
uploaded_file = st.file_uploader("Upload planets.json", type="json")
if uploaded_file is not None:
    planetbase = json.load(uploaded_file)
else:
    st.warning("Please upload a planets.json file to proceed.")
    st.stop()

# ... (keep all the previous search criteria inputs unchanged) ...

# Search button
if st.button("Search Planets"):
    results = search_planets(planetbase, search_criteria, top_5_per_subtype and search_criteria["Color"] is not None)
    total_planets = sum(len(planets) for planets in results.values())
    st.write(f"Found {total_planets} matching planets across {len(results)} subtypes:")
    
    for subtype, planets in results.items():
        with st.expander(f"{subtype} ({len(planets)} planets)"):
            # Create a list of planet names for the dropdown
            planet_names = [f"{system}, {coords}" for system, coords, _, _, _ in planets]
            
            # Create a dropdown menu for planet selection
            selected_planet = st.selectbox(f"Select a planet in {subtype}", [""] + planet_names, key=f"dropdown_{subtype}")
            
            if selected_planet:
                # Find the selected planet's data
                selected_system, selected_coords = selected_planet.split(", ")
                selected_planet_data = planetbase[selected_system][selected_coords]
                
                # Display detailed information about the selected planet
                st.write("### Planet Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**System:** {selected_system}")
                    st.write(f"**Coordinates:** {selected_coords}")
                    st.write(f"**Type:** {selected_planet_data.get('Type', 'Unknown')}")
                    st.write(f"**SubType:** {selected_planet_data.get('SubType', 'Unknown')}")
                    st.write(f"**Temperature:** {selected_planet_data.get('Temperature', 'Unknown')} °C")
                    st.write(f"**Gravity:** {selected_planet_data.get('Gravity', 'Unknown')} g")
                
                with col2:
                    st.write(f"**Atmosphere:** {'Yes' if selected_planet_data.get('Atmosphere', False) else 'No'}")
                    st.write(f"**Tidally Locked:** {'Yes' if selected_planet_data.get('TidallyLocked', False) else 'No'}")
                    st.write(f"**Has Rings:** {'Yes' if selected_planet_data.get('HasRings', False) else 'No'}")
                    st.write(f"**Resources:** {', '.join(selected_planet_data.get('Resources', ['None']))}")
                
                # Display planet color
                planet_color = selected_planet_data.get('Color', [0, 0, 0])
                color_hex = f"#{int(planet_color[0]):02x}{int(planet_color[1]):02x}{int(planet_color[2]):02x}"
                st.color_picker("Planet Color", color_hex, key=f"color_picker_{subtype}", disabled=True)
                
                # If there's a search color, show similarity
                if search_criteria["Color"] is not None:
                    color_similarity = rgb_euclidean_distance(search_criteria["Color"], planet_color)
                    st.write(f"**Color Similarity:** {color_similarity:.2f}%")

# Instructions
st.markdown("---")
st.markdown("**Instructions:**")
st.markdown("1. Upload a planets.json file to start.")
st.markdown("2. Set your search criteria using the inputs above.")
st.markdown("3. If using color search, you can choose to get the top 5 results for each subtype.")
st.markdown("4. Adjust the minimum color similarity slider to filter results based on color matching.")
st.markdown("5. Click 'Search Planets' to see the results.")
st.markdown("6. Results are organized by subtype in collapsible sections.")
st.markdown("7. Use the dropdown menu in each subtype to select a specific planet and view its details.")
st.markdown("8. The color picker shows the planet's color, and detailed information is displayed below it.")
