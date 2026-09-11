"""
RAG (Retrieval Augmented Generation) service for PetPal Pakistan.

Grounds AI answers in real veterinary reference documents instead of
letting the LLM guess from training data:
  - AAFCO Dog & Cat Food Nutrient Profiles  -> nutrition/recipe answers
  - UVAS Manual of Common Pet Drugs (Pakistan) -> vaccination/drug info
  - WSAVA Nutritional Assessment Guidelines  -> nutrition/BCS answers

Approach: lightweight TF-IDF retrieval (no embedding model download needed,
so it works reliably on Streamlit Cloud's free tier). Good enough for these
keyword-heavy technical documents (drug names, nutrient names, doses).
"""

import os
import re
import glob
import pickle
import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
INDEX_CACHE = os.path.join(KB_DIR, "_index_cache.pkl")

CHUNK_SIZE = 900       # characters per chunk
CHUNK_OVERLAP = 150    # overlap so we don't cut a fact in half


def _extract_text(pdf_path):
    """Pull text from a PDF, page by page."""
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return pages


def _chunk_text(pages, source_name):
    """Split page text into overlapping chunks, tagging each with its source."""
    chunks = []
    for page_num, page_text in enumerate(pages, 1):
        text = " ".join(page_text.split())  # normalize whitespace
        # Strip table-of-contents dot-leaders (e.g. "VACCINES ....... 42") which
        # otherwise pollute TF-IDF matches with junk that isn't real content.
        text = re.sub(r"\.{3,}", " ", text)
        text = re.sub(r"\s{2,}", " ", text).strip()

        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            # Skip near-empty or mostly-numeric/punctuation chunks (leftover TOC noise)
            letters = sum(c.isalpha() for c in chunk)
            if chunk.strip() and letters > 40:
                chunks.append({
                    "text": chunk,
                    "source": source_name,
                    "page": page_num,
                })
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _build_index():
    """Extract + chunk all PDFs in knowledge_base/, fit a TF-IDF index."""
    all_chunks = []
    for pdf_path in sorted(glob.glob(os.path.join(KB_DIR, "*.pdf"))):
        source_name = os.path.splitext(os.path.basename(pdf_path))[0]
        pages = _extract_text(pdf_path)
        all_chunks.extend(_chunk_text(pages, source_name))

    if not all_chunks:
        return None

    texts = [c["text"] for c in all_chunks]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=20000)
    matrix = vectorizer.fit_transform(texts)

    index = {"chunks": all_chunks, "vectorizer": vectorizer, "matrix": matrix}

    try:
        with open(INDEX_CACHE, "wb") as f:
            pickle.dump(index, f)
    except Exception:
        pass  # cache is a nice-to-have, not required

    return index


@st.cache_resource(show_spinner="Loading veterinary reference library...")
def get_index():
    """Load a cached index if present, else build it once per app session."""
    if os.path.exists(INDEX_CACHE):
        try:
            with open(INDEX_CACHE, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return _build_index()


def retrieve(query, k=4, sources=None):
    """
    Return the top-k most relevant chunks for a query.
    `sources` optionally restricts retrieval to specific PDFs, e.g.
    sources=["aafco_nutrient_profiles"] to only search that document.
    """
    index = get_index()
    if not index:
        return []

    query_vec = index["vectorizer"].transform([query])
    scores = cosine_similarity(query_vec, index["matrix"])[0]

    ranked = sorted(
        zip(scores, index["chunks"]), key=lambda x: x[0], reverse=True
    )

    results = []
    for score, chunk in ranked:
        if score <= 0:
            continue
        if sources and chunk["source"] not in sources:
            continue
        results.append(chunk)
        if len(results) >= k:
            break
    return results


def build_context_block(query, k=4, sources=None):
    """Format retrieved chunks into a citation-friendly context block for the LLM prompt."""
    hits = retrieve(query, k=k, sources=sources)
    if not hits:
        return None
    lines = []
    for h in hits:
        lines.append(f"[Source: {h['source']}, page {h['page']}] {h['text']}")
    return "\n\n".join(lines)
