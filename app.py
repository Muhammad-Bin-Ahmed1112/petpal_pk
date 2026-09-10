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
        st.caption(f"Live from OpenStreetMap • Updated {datetime.now().strftime('%I:%M %p')}")

        if clinics:
            # MAP YAHAN AAYEGA
            m = folium.Map(location=[float(clinics[0]['lat']), float(clinics[0]['lon'])], zoom_start=12)
            for clinic in clinics:
                if clinic['lat'] and clinic['lon']: # error se bachne ke liye
                    folium.Marker(
                        [float(clinic['lat']), float(clinic['lon'])],
                        popup=f"<b>{clinic['name']}</b><br>{clinic['address']}"
                    ).add_to(m)
            st_folium(m, width=700, height=400) # Map show hoga

            st.markdown("#### Clinic List")
            # LIST YAHAN AAYEGI
            for i, clinic in enumerate(clinics, 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {clinic['name']}**")
                    st.write(f"📍 {clinic['address']}")
        else:
            st.info("Could not load live clinics. Try 'Rawalpindi' or 'Lahore'")

        st.warning("**Disclaimer**: This is first-aid guidance only. Contact a licensed vet immediately.")
