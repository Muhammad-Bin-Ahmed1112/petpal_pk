import streamlit as st
from datetime import datetime
from ai_service import get_vaccination_schedule, get_food_recipe, get_emergency_advice
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="PetPal Pakistan", page_icon="🐾", layout="wide")
st.title("🐾 PetPal Pakistan")

# 1. RESULT YAAD RAKHNE KE LIYE
if 'emergency_result' not in st.session_state:
    st.session_state.emergency_result = None
    st.session_state.emergency_clinics = None

menu = st.sidebar.radio("Menu", ["📅 Vaccination", "🍖 Recipe", "🚨 Emergency"])

if menu == "📅 Vaccination":
    st.header("📅 Vaccination Schedule")
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Rabbit"])
    with col2:
        age = st.text_input("Age", "2 years")

    if st.button("Get Schedule"):
        with st.spinner("Making schedule..."):
            result = get_vaccination_schedule(pet_type, age)
            st.markdown(result)

elif menu == "🍖 Recipe":
    st.header("🍖 Budget Recipe Generator")
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("Pet Type", ["Dog", "Cat"], key="recipe_pet")
    with col2:
        age = st.text_input("Age", "2 years", key="recipe_age")

    ingredients = st.text_area("Available Ingredients", "chicken, chawal, dahi")
    budget = st.number_input("Budget in PKR", 500, step=100)

    if st.button("Get Recipe"):
        with st.spinner("Cooking recipe..."):
            result = get_food_recipe(pet_type, age, ingredients, budget)
            st.markdown(result)

elif menu == "🚨 Emergency":
    st.header("🚨 Emergency Help")
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Rabbit"], key="em_pet")
    with col2:
        age = st.text_input("Age", "2 years", key="em_age")

    city = st.text_input("Your City", "Lahore")
    symptoms = st.text_area("Describe Symptoms", "vomiting, not eating, weak")

    if st.button("Get Help Now"):
        with st.spinner(f"Searching help and clinics in {city}..."):
            ai_result, clinics = get_emergency_advice(pet_type, age, symptoms, city)
            st.session_state.emergency_result = ai_result
            st.session_state.emergency_clinics = clinics

    # 2. RESULT SESSION SE SHOW KARO - IS WAJA SE GAYAB NAHI HOGA
    if st.session_state.emergency_result:
        st.markdown("### 🩺 First Aid & Severity")
        st.markdown(st.session_state.emergency_result)

        st.markdown("### 🏥 Live Veterinary Clinics Near You")
        st.caption(f"Live from OSM + DuckDuckGo • Updated {datetime.now().strftime('%I:%M %p')}")

        clinics = st.session_state.emergency_clinics
        if clinics and clinics[0]['name']!= "No live data found":
            # SIRF JINKE PAAS LAT/LON HAI UNKA MAP BANAO
            map_clinics = [c for c in clinics if c.get('lat') and c.get('lon')]

            if map_clinics:
                m = folium.Map(location=[float(map_clinics[0]['lat']), float(map_clinics[0]['lon'])], zoom_start=12)
                for clinic in map_clinics:
                    folium.Marker(
                        [float(clinic['lat']), float(clinic['lon'])],
                        popup=f"<b>{clinic['name']}</b><br>{clinic['address']}",
                        tooltip=clinic['name']
                    ).add_to(m)
                st_folium(m, width=700, height=400, returned_objects=[])
            else:
                st.info("Map data not available. Showing clinic list below.")

            st.markdown("#### Clinic List")
            for i, clinic in enumerate(clinics, 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {clinic['name']}**")
                    st.write(f"📍 {clinic['address']}")
                    st.write(f"📞 {clinic['phone']}")

                    # LINK KA CHECK
                    if clinic.get('lat') and clinic.get('lon'):
                        osm_url = f"https://www.openstreetmap.org/?mlat={clinic['lat']}&mlon={clinic['lon']}"
                        st.write(f"[🗺️ View on OpenStreetMap]({osm_url})")
                    else:
                        google_url = f"https://www.google.com/maps/search/?api=1&query={clinic['name']} {city}"
                        st.write(f"[🗺️ Search on Google Maps]({google_url})")
        else:
            st.warning("Could not load live clinics. Please try 'Lahore', 'Karachi', or 'Islamabad'")

        st.error("**Disclaimer**: This is first-aid guidance only. Contact a licensed vet immediately for emergencies.")
