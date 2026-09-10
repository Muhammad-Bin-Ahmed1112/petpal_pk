import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

def get_vaccination_schedule(pet_type, age):
    prompt = f"""You are a Pakistani veterinarian. Use official guidelines from WSAVA and AVMA.

    Give a vaccination schedule table for a {pet_type} aged {age} in Pakistan.
    Include vaccine name, age, and estimated PKR price.
    At the end add: "Disclaimer: Consult a local vet. Source: WSAVA.org, AVMA.org"
    """
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, max_tokens=1000)
    return res.choices[0].message.content

def get_food_recipe(pet_type, age, ingredients, budget):
    prompt = f"""You are a pet nutritionist. Use data from AVMA and PetMD.

    Give 2 safe homemade food recipes for a {pet_type} aged {age}.
    Ingredients available: {ingredients}. Budget: {budget} PKR.
    Include ingredients, steps, and "Foods to AVOID".
    At the end add: "Source: AVMA.org, PetMD.com"
    """
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, max_tokens=1000)
    return res.choices[0].message.content

def get_emergency_advice(pet_type, age, symptoms, city):
    prompt = f"""You are an emergency veterinarian. Use guidelines from AVMA.

    Pet: {pet_type}, Age: {age}, City: {city}, Pakistan
    Symptoms: {symptoms}

    1. Give immediate first aid steps
    2. Rate severity from 1 to 10
    3. List 3 pet clinics in {city}, Pakistan with example names and numbers
    4. Add disclaimer: This is not a substitute for a vet visit
    5. At the end add: "Source: AVMA.org"
    """
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL, max_tokens=1200)
    return res.choices[0].message.content
