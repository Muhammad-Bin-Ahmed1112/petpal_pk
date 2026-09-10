import streamlit as st
from ai_service import get_vaccination_schedule, get_food_recipe, get_emergency_advice

st.title("🐾 PetPal Pakistan")

menu = st.sidebar.radio("Menu", ["📅 Vaccination", "🍖 Sasta Khana", "🚨 Emergency"])

if menu == "📅 Vaccination":
    pet_type = st.selectbox("Pet", ["Kutta", "Billi"])
    age = st.text_input("Umar", "2 saal")
    if st.button("Schedule"):
        st.write(get_vaccination_schedule(pet_type, age))

elif menu == "🍖 Sasta Khana":
    pet_type = st.selectbox("Pet", ["Kutta", "Billi"])
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

    city = st.text_input("Your City", "Rawalpindi") # naya field
    symptoms = st.text_area("Describe Symptoms", "vomiting, not eating, weak")

    if st.button("Get Help Now"):
        with st.spinner("Checking..."):
            result = get_emergency_advice(pet_type, age, symptoms, city)
            st.error(result)