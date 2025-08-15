# Remplissage PDF Quitus — FastAPI + Gradio

Outil simple pour **remplir automatiquement** des quitus à partir d’un PDF source (Licence/Master), 
avec export PDF et **journalisation Excel** par filière.

## ✨ Fonctionnalités
- Upload du **PDF source** + **modèle quitus**
- Remplissage **AcroForm** si champs présents, sinon **overlay** texte (aplanit)
- Enregistrement des données dans `students_data.xlsx` 
  - Feuille **Licence**
  - Feuille **Master**
- Clé API optionnelle pour sécuriser l’endpoint
- UI Gradio hébergeable sur Hugging Face Spaces

## 🧱 Stack
- **API** : FastAPI, pypdf, reportlab, openpyxl
- **UI** : Gradio
- **Secrets** : `.env` local, variables d’env en prod

## 📁 Architecture
api/ # service FastAPI </br>
ui/ # client Gradio </br>
data/ # PDF/Excel (gitignored)



## ⚙️ Configuration
Crée `.env` à la racine (copie `.env.example`) : </br>
API_KEY=changeme </br>
ALLOWED_ORIGINS=http://localhost:7860


## 🚀 Démarrage local
```bash
# Backend
cd api
python -m venv .venv && . .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd ../ui
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
API_URL=http://127.0.0.1:8000/process gradio app.py


