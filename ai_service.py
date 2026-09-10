import os
import streamlit as st
from groq import Groq

# 1. Pehle secrets check karo
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    st.sidebar.success("✅ API Key loaded from Secrets")
except Exception as e:
    API_KEY = os.getenv("GROQ_API_KEY")
    st.sidebar.warning(f"⚠️ Using.env file. Error: {e}")

# 2. Agar key nahi mili to app yahi rok do
if not API_KEY or API_KEY == "":
    st.error("GROQ_API_KEY not found! Please add it in Manage app > Settings > Secrets")
    st.stop()

# 3. Ab client banao
client = Groq(api_key=API_KEY)
MODEL = "openai/gpt-oss-120b"

def get_vaccination_schedule(pet_type, age):
    prompt = f"You are a Pakistani veterinarian. Use WSAVA/AVMA. Give vaccination schedule for a {pet_type} aged {age} in Pakistan with PKR prices. Source: WSAVA.org"
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL)
    return res.choices[0].message.content

def get_food_recipe(pet_type, age, ingredients, budget):
    prompt = f"You are a pet nutritionist. Use AVMA/PetMD. Give 2 budget recipes for {pet_type} aged {age}. Ingredients: {ingredients}. Budget: {budget} PKR. Source: AVMA.org"
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL)
    return res.choices[0].message.content

def get_emergency_advice(pet_type, age, symptoms, city):
    prompt = f"You are an emergency vet. Pet: {pet_type}, Age: {age}, City: {city}, PK. Symptoms: {symptoms}. Give first aid, severity 1-10, and 3 clinic names in {city}. Source: AVMA.org. Disclaimer: See a vet."
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL)
    return res.choices[0].message.content
