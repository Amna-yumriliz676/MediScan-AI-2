"""
MediScan AI - Prescription OCR
"""
import streamlit as st
from PIL import Image
import pytesseract
import re
from database import MEDICINES, get_all_medicine_names


@st.cache_data(show_spinner=False)
def extract_text_from_image(image_bytes):
    try:
        img = Image.open(image_bytes)
        img = img.convert("L")
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"OCR_ERROR: {str(e)}"


def extract_medicine_names(text: str):
    if not text or "OCR_ERROR" in text:
        return []
    text_lower = text.lower()
    found = []
    for med in MEDICINES:
        med_name = med["name"].lower()
        generic = med["generic"].lower().split()[0]
        if med_name in text_lower or generic in text_lower:
            found.append({"medicine": med["name"], "generic": med["generic"],
                          "confidence": 0.95,
                          "matched_text": med["name"] if med_name in text_lower else med["generic"]})
    if not found:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
        for word in words:
            wl = word.lower()
            for med in MEDICINES:
                ml = med["name"].lower()
                if len(wl) >= 4 and (wl in ml or ml in wl):
                    found.append({"medicine": med["name"], "generic": med["generic"],
                                  "confidence": 0.65, "matched_text": word})
                    break
    seen, unique = set(), []
    for f in found:
        if f["medicine"] not in seen:
            seen.add(f["medicine"])
            unique.append(f)
    return unique


def suggest_alternatives(word: str, top_k=3):
    from difflib import SequenceMatcher
    word_lower = word.lower()
    scores = [(med["name"], SequenceMatcher(None, word_lower, med["name"].lower()).ratio())
              for med in MEDICINES]
    scores.sort(key=lambda x: -x[1])
    return scores[:top_k]
