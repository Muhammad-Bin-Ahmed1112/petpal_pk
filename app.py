import streamlit as st
from datetime import datetime
from ai_service import get_vaccination_schedule, get_food_recipe, get_emergency_advice
from streamlit_folium import st_folium # NEW
import folium # NEW
st.title("🐾 PetPal Pakistan")

menu = st.sidebar.radio("Menu", ["📅 Vaccination", "🍖 Recipe", "🚨 Emergency"])

if menu == "📅 Vaccination":
    pet_type = st.selectbox("Pet", ["Dog", "Billi"])
    age = st.text_input("Umar", "2 saal")
    if st.button("Schedule"):
        st.write(get_vaccination_schedule(pet_type, age))

elif menu == "🍖 Recipe":
    pet_type = st.selectbox("Pet", ["Dog", "Billi"])
    age = st.text_input("Umar", "2 saal")
    ingredients = st.text_area("Ingredients", "chicken, chawal")
    budget = st.number_input("Budget", 500)
    if st.button("Recipe"):
        st.write(get_food_recipe(pet_type, age, ingredients, budget))

elif menu == "🚨 Emergency":
    st.header("🚨 Emergency Help")
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Rabbit"])
    with col2:
        age = st.text_input("Age", "2 years")

    city = st.text_input("Your City", "Rawalpindi")
    symptoms = st.text_area("Describe Symptoms", "vomiting, not eating, weak")

    if st.button("Get Help Now"):
        ai_result, clinics = get_emergency_advice(pet_type, age, symptoms, city)

        st.markdown("### 🩺 First Aid & Severity")
        st.write(ai_result)

        st.markdown("### 🏥 Live Veterinary Clinics Near You")
        st.caption(f"Live from OSM + DuckDuckGo • Updated {datetime.now().strftime('%I:%M %p')}")

        if clinics:
            # 1. PEHLE MAP BANANE KI KOSHISH KARO
            map_clinics = [c for c in clinics if c.get('lat') and c.get('lon')]

            if map_clinics: # Agar OSM se data aya
                m = folium.Map(location=[float(map_clinics[0]['lat']), float(map_clinics[0]['lon'])], zoom_start=12)
                for clinic in map_clinics:
                    folium.Marker(
                        [float(clinic['lat']), float(clinic['lon'])],
                        popup=f"<b>{clinic['name']}</b><br>{clinic['address']}"
                    ).add_to(m)
                st_folium(m, width=700, height=400)
            else: # Agar DDG se aya to map nahi banega
                st.info("Map data not available. Showing links below.")

            # 2. LIST HAR HAAL ME SHOW HOGI
            st.markdown("#### Clinic List")
            for i, clinic in enumerate(clinics, 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {clinic['name']}**")
                    st.write(f"📍 {clinic['address']}")
                    st.write(f"📞 {clinic['phone']}")

                    # YEH NAYA CHECK: Link add kiya
                    if clinic.get('lat') and clinic.get('lon'):
                        osm_url = f"https://www.openstreetmap.org/?mlat={clinic['lat']}&mlon={clinic['lon']}"
                        st.write(f"[🗺️ View on OpenStreetMap]({osm_url})")
                    else:
                        google_url = f"https://www.google.com/maps/search/?api=1&query={clinic['name']} {city}"
                        st.write(f"[🗺️ Search on Google Maps]({google_url})")
        else:
            st.info("Could not load live clinics. Try 'Rawalpindi' or 'Lahore'")

        st.warning("**Disclaimer**: This is first-aid guidance only. Contact a licensed vet immediately.")
