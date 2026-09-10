import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from browser import search # <-- ye line search ke liye

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

def _get_sources_and_answer(query, system_prompt):
    # Step 1: Search from trusted vet sites
    search_results = search(query)

    # Step 2: Combine search data + AI
    prompt = f"""{system_prompt}

    Use ONLY the information from the search results below to answer.
    If info is not in results, say "I could not find reliable data".

    SEARCH RESULTS:
    {search_results}

    USER QUESTION: {query}
    At the end add "Sources:" and list the websites used.
    """
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, max_tokens=1200)
    return res.choices[0].message.content

def get_vaccination_schedule(pet_type, age):
    query = f"{pet_type} vaccination schedule {age} Pakistan WSAVA guidelines PKR price"
    system = "You are a Pakistani veterinarian. Give accurate vaccination schedule in a table."
    return _get_sources_and_answer(query, system)

def get_food_recipe(pet_type, age, ingredients, budget):
    query = f"safe homemade {pet_type} food recipes with {ingredients} budget {budget} PKR"
    system = "You are a pet nutritionist. Give 2 recipes with ingredients, steps, and foods to avoid."
    return _get_sources_and_answer(query, system)

def get_emergency_advice(pet_type, age, symptoms, city):
    query = f"emergency {pet_type} treatment for {symptoms} vet guidelines AVMA"
    system = f"""You are an emergency vet.
    1. Give immediate steps
    2. Rate severity 1-10
    3. List 3 pet clinics in {city}, Pakistan with names and numbers if available
    4. Add disclaimer: This is not a substitute for a vet visit"""
    return _get_sources_and_answer(query, system)