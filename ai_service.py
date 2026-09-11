import os
import requests
import time
import streamlit as st
from groq import Groq
import rag_service

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

# ---------------------------------------------------------------------------
# LIVE WEB SEARCH GROUNDING (for real, current PKR prices — no hardcoded data)
# Uses Tavily (free tier: https://tavily.com). Set TAVILY_API_KEY as an env var.
# ---------------------------------------------------------------------------
def web_search_live(query, max_results=5):
    """Return live web search results, or [] if no key / search failed."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
            },
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []

def build_price_context(query):
    """Turn live search results into a short grounding block for the LLM prompt."""
    results = web_search_live(query)
    if not results:
        return None
    lines = []
    for r in results:
        title = r.get("title", "")
        content = (r.get("content") or "")[:250]
        url = r.get("url", "")
        lines.append(f"- {title}: {content} (source: {url})")
    return "\n".join(lines)

# 1. GEMINI KI JAGAH GROQ
def get_vaccination_schedule(pet_type, age):
    price_context = build_price_context(f"{pet_type} vaccination cost Pakistan 2026 PKR vet clinic price")

    # RAG: ground the medical content in WSAVA guidelines + the UVAS vaccine list (not the LLM's memory)
    # Use vaccine-specific keywords (not generic phrasing) so TF-IDF finds the actual vaccine
    # tables/brand names rather than table-of-contents or unrelated sections.
    if pet_type.lower() == "cat":
        vaccine_query = "feline panleukopenia calicivirus rhinotracheitis rabies vaccine trade name"
    elif pet_type.lower() == "rabbit":
        vaccine_query = "rabbit vaccination schedule myxomatosis viral hemorrhagic disease"
    else:
        vaccine_query = "canine parvo distemper hepatitis leptospirosis rabies vaccine trade name"

    vet_context = rag_service.build_context_block(
        vaccine_query, k=4, sources=["wsava_nutrition_guidelines", "uvas_drug_manual"]
    )

    grounding = ""
    if vet_context:
        grounding += f"\nVETERINARY REFERENCE DATA (WSAVA guidelines / UVAS drug manual):\n{vet_context}\n"
    if price_context:
        grounding += f"\nLIVE WEB PRICE DATA:\n{price_context}\n"

    if grounding:
        prompt = (
            f"Act as a vet in Pakistan. Using ONLY the reference data below, create a vaccination "
            f"schedule for a {pet_type} aged {age}. Prefer vaccines/brands mentioned in the veterinary "
            f"reference data where relevant. Include realistic PKR price ranges only if present in the "
            f"live web data, and note prices are approximate and may vary by clinic.\n{grounding}\n"
            f"Format as bullet points: vaccine name, recommended age/timing, approx PKR price range "
            f"(if available)."
        )
    else:
        prompt = (
            f"Act as a vet in Pakistan. Create a vaccination schedule for a {pet_type} aged {age}. "
            f"Use bullet points and mention vaccines available in Pakistan. IMPORTANT: Do NOT invent "
            f"specific PKR prices — live pricing data isn't available right now, so instead write "
            f"'Contact your local vet for current pricing' for cost."
        )
    return call_groq(prompt)

def get_food_recipe(pet_type, age, ingredients, budget):
    price_context = build_price_context(f"{ingredients} grocery price Pakistan 2026 PKR")

    # RAG: ground nutrient adequacy claims in the actual AAFCO Nutrient Profiles, not model guesswork
    nutrient_context = rag_service.build_context_block(
        f"{pet_type} minimum protein fat nutrient requirements",
        k=3,
        sources=["aafco_nutrient_profiles"],
    )

    grounding = ""
    if nutrient_context:
        grounding += f"\nAAFCO NUTRIENT PROFILE DATA:\n{nutrient_context}\n"
    if price_context:
        grounding += f"\nLIVE GROCERY PRICE DATA:\n{price_context}\n"

    if grounding:
        prompt = (
            f"Act as a pet nutritionist in Pakistan. Using the reference data below, create 1 "
            f"budget-friendly recipe for a {pet_type} aged {age}. Ingredients on hand: {ingredients}. "
            f"Budget: {budget} PKR. Give recipe name, ingredients with approx cost (only if price data "
            f"is given), steps, and a short note on whether this roughly meets the AAFCO minimum "
            f"protein/fat concentrations cited below (do not claim it is 'complete and balanced' unless "
            f"the data supports it — recommend a proper commercial or vet-formulated diet for long-term "
            f"feeding).\n{grounding}"
        )
    else:
        prompt = (
            f"Act as a pet nutritionist in Pakistan. Create 1 budget-friendly recipe for a {pet_type} "
            f"aged {age}. Ingredients: {ingredients}. Budget: {budget} PKR. Give recipe name, "
            f"ingredients, and steps. Use local ingredients. Do NOT invent exact grocery prices since "
            f"live pricing data isn't available right now — keep cost guidance qualitative."
        )
    return call_groq(prompt)

def get_emergency_advice(pet_type, age, symptoms, city):
    # RAG: pull relevant UVAS drug-manual context so the model's mention of treatment classes
    # (not doses for self-administration) is grounded in a real Pakistani veterinary reference
    drug_context = rag_service.build_context_block(symptoms, k=3, sources=["uvas_drug_manual"])
    grounding = f"\n\nVETERINARY REFERENCE DATA (for context only — do NOT give specific doses to the owner):\n{drug_context}" if drug_context else ""

    prompt = (
        f"Act as an emergency vet. A {age} old {pet_type} in {city}, Pakistan has: {symptoms}. "
        f"1. Give Severity: Low/Medium/High. 2. Give 3 First-Aid steps the owner can safely do at home "
        f"(no medications/doses). 3. You may mention, in general terms, what class of treatment a vet "
        f"might use based on the reference data below, WITHOUT giving a dose for the owner to administer. "
        f"4. Add 'Contact a vet immediately'.{grounding}"
    )
    ai_result = call_groq(prompt)
    return ai_result, search_clinics_realtime(city)

# 2. LIVE GEOCODE ANY PAKISTANI CITY (Nominatim)
def geocode_city(city):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "PetPal-PK-Hackathon/1.0"}
    params = {"q": f"{city}, Pakistan", "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=6)
        if r.status_code == 200 and r.json():
            data = r.json()[0]
            return float(data["lat"]), float(data["lon"])
    except Exception:
        pass
    return None, None

# 3. LIVE CLINIC SEARCH VIA OVERPASS (structured OSM data, includes phone/address tags)
def search_clinics_overpass(city, radius_m=15000):
    lat, lon = geocode_city(city)
    if lat is None:
        return []

    query = f"""
    [out:json][timeout:20];
    (
      node["amenity"="veterinary"](around:{radius_m},{lat},{lon});
      way["amenity"="veterinary"](around:{radius_m},{lat},{lon});
      node["healthcare"="veterinary"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=25)
        if r.status_code != 200:
            return []
        clinics = []
        for el in r.json().get("elements", []):
            tags = el.get("tags", {})
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if not el_lat or not el_lon:
                continue
            address = ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:city", city)])) or f"Near {city}"
            clinics.append({
                "name": tags.get("name", "Veterinary Clinic"),
                "address": address,
                "lat": el_lat,
                "lon": el_lon,
                "phone": tags.get("phone") or tags.get("contact:phone") or "Not listed",
            })
        return clinics
    except Exception:
        return []

# 4. LIVE FALLBACK — NOMINATIM KEYWORD SEARCH (still real-time, no hardcoded data)
def search_clinics_osm(city):
    keywords = ["vet", "veterinary clinic", "animal hospital", "pet clinic", "dog clinic"]
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "PetPal-PK-Hackathon/1.0"}

    for kw in keywords:
        params = {"q": f"{kw} {city} Pakistan", "format": "json", "limit": 5}
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
                        "phone": "Not listed",
                    })
                return clinics
            time.sleep(1.1)
        except Exception:
            continue
    return []

# 5. MAIN SMART SEARCH — 100% LIVE, WORKS FOR ANY PAKISTANI CITY, NO HARDCODED DATA
def search_clinics_realtime(city):
    with st.spinner(f"Searching live clinics in {city}..."):
        clinics = search_clinics_overpass(city)
        if not clinics:
            clinics = search_clinics_osm(city)

    if not clinics:
        st.warning(
            f"No live clinic data found on OpenStreetMap for '{city}' right now. "
            f"Try a nearby major city, or check Google Maps directly — no saved/dummy data is shown."
        )
    return clinics
