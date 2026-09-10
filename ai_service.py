import os
import streamlit as st
import requests
from datetime import datetime
from groq import Groq

# 1. Load Only GROQ Key
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    st.sidebar.success("✅ GROQ API Key loaded")
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    st.sidebar.warning("⚠️ Using.env file")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found! Add it in Manage app > Settings > Secrets")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODEL = "openai/gpt-oss-120b"

# 2. OSM SEARCH - For Map + GPS
def search_clinics_osm(city):
    """Search real vets using OpenStreetMap Nominatim - FREE"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"veterinary clinic {city} Pakistan",
        "format": "json",
        "limit": 3,
        "addressdetails": 1
    }
    headers = {"User-Agent": "PetPal-PK-Hackathon/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            clinics = []
            for place in data:
                clinics.append({
                    "name": place.get("name", place["display_name"].split(",")[0]),
                    "address": place.get("display_name"),
                    "lat": place.get("lat"),
                    "lon": place.get("lon"),
                    "phone": "Check Google Maps"
                })
            return clinics
        else:
            return []
    except Exception as e:
        print(f"OSM Error: {e}")
        return []

# 2.1 DDG BACKUP - For Name + Description
def search_clinics_ddg(city):
    """Backup search using DuckDuckGo - no key needed"""
    url = "https://api.duckgo.com/"
    params = {"q": f"veterinary clinic {city} Pakistan", "format": "json", "no_html": 1}
    try:
        res = requests.get(url, params=params, timeout=5).json()
        clinics = []
        for topic in res.get("RelatedTopics", [])[:3]:
            if "Text" in topic:
                clinics.append({
                    "name": topic["Text"].split(" - ")[0][:50],
                    "address": topic["Text"],
                    "lat": None,
                    "lon": None,
                    "phone": "Check link"
                })
        return clinics
    except Exception as e:
        print(f"DDG Error: {e}")
        return []

# 2.2 MAIN SMART SEARCH
def search_clinics_realtime(city):
    """First try OSM, if empty then try DDG"""
    with st.spinner(f"Searching clinics in {city}..."):
        clinics = search_clinics_osm(city)

    if not clinics:
        st.info("OSM pe result nahi mila. Trying DuckDuckGo...")
        clinics = search_clinics_ddg(city)

    if not clinics:
        clinics = [{
            "name": f"Search 'Vet Clinic {city}' on Google",
            "address": "No live data found",
            "lat": None,
            "lon": None,
            "phone": "N/A"
        }]
    return clinics

# 3. Your 3 AI Functions
def get_vaccination_schedule(pet_type, age):
    prompt = f"You are a Pakistani veterinarian. Use WSAVA/AVMA. Give vaccination schedule table for a {pet_type} aged {age} in Pakistan with PKR prices. Cite WSAVA.org"
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, temperature=0.3)
    return res.choices[0].message.content

def get_food_recipe(pet_type, age, ingredients, budget):
    prompt = f"You are a pet nutritionist. Use AVMA/PetMD. Give 2 budget recipes for {pet_type} aged {age}. Ingredients: {ingredients}. Budget: {budget} PKR. Include cost in PKR. Cite AVMA.org"
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, temperature=0.4)
    return res.choices[0].message.content

def get_emergency_advice(pet_type, age, symptoms, city):
    # Part 1: Get real clinics FIRST
    live_clinics = search_clinics_realtime(city)

    # Part 2: Build clinic list for AI
    clinics_text = "\n".join([f"{i+1}. {c['name']} - {c['address']}" for i, c in enumerate(live_clinics)])

    prompt = f"""
    You are an emergency vet. Pet: {pet_type}, Age: {age}, City: {city}, PK. Symptoms: {symptoms}.

    Task 1: Give first aid steps in a numbered table.
    Task 2: Give Severity rating 1-10 and explain why.
    Task 3: List 5 red-flag signs to go to vet immediately.

    Here are 3 real clinics near the user found just now:
    {clinics_text if clinics_text else "No live data found for this city"}

    Rules: Cite AVMA.org. Add disclaimer at end: This is not a substitute for a vet.
    """
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, temperature=0.2)
    ai_text = res.choices[0].message.content

    return ai_text, live_clinics
