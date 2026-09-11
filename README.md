# 🐾 PetPal Pakistan

An AI-powered pet care assistant for dog and cat owners in Pakistan — vaccination schedules, budget-friendly recipes, and emergency first-aid guidance with live veterinary clinic search, grounded in real veterinary reference documents (not AI guesswork).

## Features

- **📅 Vaccination Schedule** — Age-appropriate vaccination plans grounded in the WSAVA Nutritional Assessment Guidelines and the UVAS (Univ. of Veterinary & Animal Sciences, Lahore) Manual of Common Pet Drugs, referencing real vaccine brands available in Pakistan.
- **🍖 Budget Recipe Generator** — Budget-friendly home-cooked meal suggestions using local ingredients, checked against AAFCO minimum nutrient (protein/fat) concentrations rather than inventing numbers.
- **🚨 Emergency Help** — Severity triage and first-aid steps for a sick or injured pet, plus **live** nearby veterinary clinics (any city in Pakistan) pulled in real time from OpenStreetMap — no hardcoded clinic list.
- **Live pricing grounding** — When available, vaccination and grocery cost estimates are pulled from live web search rather than the AI hallucinating PKR figures.
- **RAG (Retrieval-Augmented Generation)** — All medical/nutritional claims are grounded in three real reference PDFs bundled with the app (see `knowledge_base/`), retrieved via TF-IDF search and injected into the LLM prompt.

## Tech Stack

| Layer | Tool |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| LLM | [Groq](https://groq.com) (`openai/gpt-oss-120b`) |
| Maps | [Folium](https://python-visualization.github.io/folium/) + [streamlit-folium](https://github.com/randyzwitch/streamlit-folium) |
| Live clinic search | OpenStreetMap — [Overpass API](https://overpass-api.de/) (primary) + [Nominatim](https://nominatim.org/) (fallback) |
| Live pricing search | [Tavily](https://tavily.com) web search API |
| RAG / retrieval | [pypdf](https://pypdf.readthedocs.io/) + [scikit-learn](https://scikit-learn.org) TF-IDF |

## Project Structure

```
petpal_pk/
├── app.py                  # Streamlit UI (Vaccination / Recipe / Emergency tabs)
├── ai_service.py           # Groq LLM calls, live web grounding, live clinic search
├── rag_service.py          # PDF extraction, chunking, TF-IDF retrieval (RAG)
├── requirements.txt
└── knowledge_base/         # Reference PDFs the RAG agent retrieves from
    ├── aafco_nutrient_profiles.pdf      # AAFCO Dog & Cat Food Nutrient Profiles
    ├── uvas_drug_manual.pdf             # UVAS Manual of Common Pet Drugs (Pakistan)
    └── wsava_nutrition_guidelines.pdf   # WSAVA Nutritional Assessment Guidelines
```

## Setup & Local Run

1. **Clone the repo**
   ```bash
   git clone https://github.com/Muhammad-Bin-Ahmed1112/petpal_pk.git
   cd petpal_pk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**

   | Variable | Required? | Purpose |
   |---|---|---|
   | `GROQ_API_KEY` | Yes | Powers all AI responses. Get a free key at [console.groq.com](https://console.groq.com). |
   | `TAVILY_API_KEY` | Optional | Enables live PKR pricing grounding. Get a free key at [tavily.com](https://tavily.com). Without it, the app still works — it just won't invent prices and will say "contact your local vet for current pricing." |

   ```bash
   export GROQ_API_KEY="your-key-here"
   export TAVILY_API_KEY="your-key-here"   # optional
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Deploying on Streamlit Community Cloud

1. Push this repo to GitHub (already done if you're reading this here).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at this repo, branch `main`, main file `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your-key-here"
   TAVILY_API_KEY = "your-key-here"
   ```
4. Deploy. On first run, the RAG index builds from the PDFs in `knowledge_base/` (takes ~20–30 seconds) and is then cached for the rest of the session.

## How the RAG Agent Works

`rag_service.py` extracts text from the three PDFs in `knowledge_base/`, splits it into overlapping ~900-character chunks, and indexes them with TF-IDF (chosen over embedding models to avoid large model downloads on Streamlit Cloud's free tier). When a user asks for a vaccination schedule or recipe, `ai_service.py` retrieves the most relevant chunks and injects them into the Groq prompt as grounding context — so the model answers from real reference text instead of relying purely on its training data.

## Disclaimer

PetPal Pakistan provides general informational guidance only and is **not a substitute for professional veterinary care**. Emergency advice never includes specific medication doses for owners to self-administer — always contact a licensed veterinarian for diagnosis and treatment.

## Credits

Built for a hackathon by the PetPal Pakistan team. Reference sources: AAFCO, UVAS (Lahore), WSAVA.
