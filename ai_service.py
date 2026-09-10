import os
import requests
import time
import streamlit as st
from groq import Groq

# GROQ CLIENT
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_groq(prompt):
    """Helper function to call Groq"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b", # sabse tez model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

# 1. GEMINI KI JAGAH GROQ
def get_vaccination_schedule(pet_type, age):
    prompt = f"Act as a vet in Pakistan. Create a simple vaccination schedule for a {pet_type} aged {age}. Use bullet points. Mention vaccines available in Pakistan."
    return call_groq(prompt)

def get_food_recipe(pet_type, age, ingredients, budget):
    prompt = f"Act as a pet nutritionist in Pakistan. Create 1 budget-friendly recipe for a {pet_type} aged {age}. Ingredients: {ingredients}. Budget: {budget} PKR. Give recipe name, ingredients, and steps. Use local ingredients."
    return call_groq(prompt)

def get_emergency_advice(pet_type, age, symptoms, city):
    prompt = f"Act as an emergency vet. A {age} old {pet_type} in {city}, Pakistan has: {symptoms}. 1. Give Severity: Low/Medium/High. 2. Give 3 First-Aid steps. 3. Add 'Contact a vet immediately'."
    ai_result = call_groq(prompt)
    return ai_result, search_clinics_realtime(city)

# 2. OSM SEARCH - 10 VARIATIONS
def search_clinics_osm(city):
    keywords = ["vet", "veterinary clinic", "animal hospital", "pet clinic", "dog clinic"]
    search_queries = [f"{kw} {city} Pakistan" for kw in keywords]

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "PetPal-PK-Hackathon/1.0"}

    for query in search_queries:
        params = {"q": query, "format": "json", "limit": 5}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=4)
            if response.status_code == 200 and response.json():
                clinics = []
                for place in response.json():
                    clinics.append({
                        "name": place.get("name", place["display_name"].split(",")[0]),
                        "address": place["display_name"],
                        "lat": place.get("lat"),
                        "lon": place.get("lon"),
                        "phone": "N/A"
                    })
                return clinics
            time.sleep(1.1)
        except: continue
    return []

# 3. MANUAL BACKUP FOR 3 CITIES ONLY
def get_manual_clinics(city):
    city = city.lower()
    manual_data = {
        "lahore": [
            {"name": "UVAS Pet Center", "address": "University of Veterinary Sciences, Lahore", "lat": "31.5204", "lon": "74.3587", "phone": "042-99211374"},
            {"name": "Pets and Vets Clinic", "address": "Johar Town, Lahore", "lat": "31.4724", "lon": "74.2797", "phone": "0300-1234567"}
        ],
        "karachi": [
            {"name": "ACF Animal Rescue", "address": "DHA Phase 2, Karachi", "lat": "24.8069", "lon": "67.0602", "phone": "021-35893386"},
            {"name": "Karachi Pet Clinic", "address": "Clifton, Karachi", "lat": "24.8138", "lon": "67.0249", "phone": "0302-3456789"}
        ],
        "gujranwala": [
            {"name": "Gujranwala Veterinary Hospital", "address": "Civil Lines, Gujranwala", "lat": "32.1877", "lon": "74.1945", "phone": "055-3730123"},
            {"name": "Pet Care Center Gujranwala", "address": "G.T Road, Gujranwala", "lat": "32.1635", "lon": "74.1867", "phone": "0305-1112233"}
        ]
    }
    return manual_data.get(city, [])

# 4. MAIN SMART SEARCH
def search_clinics_realtime(city):
    with st.spinner(f"Searching clinics in {city}..."):
        clinics = search_clinics_osm(city)

    if not clinics: # FINAL BACKUP
        st.warning(f"⚠️ Live data not found. Showing saved clinics for {city}")
        clinics = get_manual_clinics(city)

    if not clinics:
        clinics = [{"name": f"No data for {city}", "address": "Please select Lahore, Karachi, or Gujranwala", "lat": None, "lon": None, "phone": "N/A"}]
    return clinics
