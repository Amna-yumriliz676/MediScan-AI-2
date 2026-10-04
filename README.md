# 💊 MediScan AI — Multi-Agent Medicine Assistant

An AI-powered medicine safety app with **5 coordinated agents** that reads prescriptions, verifies medicines, checks drug interactions, and finds verified pharmacies.

## 🤖 Multi-Agent System

| Agent | Role |
|-------|------|
| 🎯 **Coordinator** | Routes every query to the right specialist |
| 💊 **Medicine Info** | Looks up medicine details |
| ⚗️ **Interaction** | Checks drug-drug interactions |
| 🩺 **Symptom Triage** | Assesses symptom severity |
| 🏪 **Pharmacy Finder** | Finds verified pharmacies |

## ✨ Features

- 💬 **Chat with AI Agents** — Coordinator routes to the right agent
- 📸 **Prescription Reader** — OCR extracts medicine names
- 💊 **Medicine Verifier** — Barcode & name verification
- ⚗️ **Interaction Checker** — 13+ drug interaction pairs
- 🏪 **Pharmacy Finder** — 8 verified pharmacies with map
- 💾 **Medicine Database** — 12 medicines with full details

## 🚀 Deploy on Streamlit Cloud

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "MediScan AI with multi-agent system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mediscan-ai.git
git push -u origin main
```

### 2. Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select repo → `app.py` → **Deploy**
4. App is live in 2-3 minutes! 🎉

### 3. Get Groq API Key (Free)
- Sign up at [console.groq.com](https://console.groq.com)
- Create free API key (starts with `gsk_`)
- Paste in the app's sidebar

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI Agents | LangChain |
| LLM | Groq (Llama 3.1) |
| OCR | Tesseract |
| Image | Pillow |
| Data | Pandas |
| Deploy | Streamlit Cloud |

## 📁 Structure

```
mediscan-ai/
├── app.py              # Main app
├── agents.py           # Multi-agent system ⭐
├── database.py         # Medicine data
├── ocr_utils.py        # Prescription OCR
├── verifier.py         # Medicine verifier
├── requirements.txt
├── packages.txt        # Tesseract
└── README.md
```

## 🧪 Example Queries

- "What is Panadol used for?"
- "Is Warfarin + Aspirin safe?"
- "I have fever and headache"
- "Pharmacies near me"
- "Tell me about Augmentin"

## ⚠️ Disclaimer

**Educational purposes only.** Not a substitute for professional medical advice. Always consult a licensed doctor or pharmacist.

## 📄 License

MIT
