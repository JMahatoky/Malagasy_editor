import streamlit as st
from streamlit_quill import st_quill
from datetime import datetime
import pandas as pd
import pickle
import re
import json
from rapidfuzz import process

# --- 1. CONFIGURATION ET CHARGEMENT DES RESSOURCES ---
st.set_page_config(page_title="Malagasy AI Editor Pro", layout="wide", page_icon="🇲🇬")

@st.cache_resource
def load_resources():
    # 1. Charger l'IA de classification (Modèle + Vectorizer)
    try:
        with open('nlp/modele_malagasy.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('nlp/vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
    except:
        model, vectorizer = None, None

    # 2. Charger le dictionnaire (Racines + Vocabulaire)
    vocabulaire = set()
    lemma_dict = {}
    try:
        df = pd.read_csv("nlp/dictionnaire_complet_racines.csv", header=None)
        for _, row in df.iterrows():
            ligne = " ".join(str(v) for v in row.values).lower()
            mots = re.findall(r'[a-zàâéèêëîïôûùç]+', ligne)
            if mots:
                racine = min(mots, key=len)
                for m in mots:
                    vocabulaire.add(m)
                    lemma_dict[m] = racine
    except Exception as e:
        st.error(f"Erreur dictionnaire : {e}")

    # 3. Charger le modèle N-Gram (Autocomplétion)
    try:
        with open('nlp/malagasy_multi_model.json', 'r', encoding='utf-8') as f:
            ngram_models = json.load(f)
    except:
        ngram_models = None

    return model, vectorizer, vocabulaire, lemma_dict, ngram_models

model, vectorizer, vocabulaire, lemma_dict, ngram_models = load_resources()

# --- 2. LOGIQUE D'AUTOCOMPLÉTION (N-GRAMS) ---
def get_smart_suggestions(text, models):
    if not models: return []
    # Nettoyage simple pour la prédiction
    clean_text = re.sub('<[^<]+?>', '', text)
    words = clean_text.lower().strip().split()
    if not words: return []
    
    suggestions = []
    # 1. 4-gram
    if len(words) >= 3:
        ctx4 = " ".join(words[-3:])
        if ctx4 in models.get("4", {}):
            suggestions = sorted(models["4"][ctx4].items(), key=lambda x: x[1], reverse=True)
    
    # 2. Backoff 3-gram
    if len(suggestions) < 3 and len(words) >= 2:
        ctx3 = " ".join(words[-2:])
        if ctx3 in models.get("3", {}):
            new_sugg = sorted(models["3"][ctx3].items(), key=lambda x: x[1], reverse=True)
            for word, _ in new_sugg:
                if word not in [s[0] for s in suggestions]: suggestions.append((word, 0))

    # 3. Backoff 2-gram
    if len(suggestions) < 3 and len(words) >= 1:
        ctx2 = words[-1]
        if ctx2 in models.get("2", {}):
            new_sugg = sorted(models["2"][ctx2].items(), key=lambda x: x[1], reverse=True)
            for word, _ in new_sugg:
                if word not in [s[0] for s in suggestions]: suggestions.append((word, 0))

    return [s[0] for s in suggestions[:5]]

# --- 3. CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header {visibility: hidden;}
    [data-testid="stVerticalBlock"] > div:last-child p, 
    [data-testid="stVerticalBlock"] > div:last-child span,
    [data-testid="stVerticalBlock"] > div:last-child label,
    [data-testid="stVerticalBlock"] > div:last-child div { color: #FFFFFF !important; }
    .streamlit-expanderHeader { background-color: #1A1A1A !important; color: white !important; border-radius: 8px; }
    .stButton>button { background-color: #1A73E8 !important; color: white !important; border-radius: 20px !important; transition: 0.3s; }
    code { color: #00FF00 !important; background-color: #111111 !important; }
    /* Style spécifique pour les suggestions d'autocomplétion */
    .sugg-btn>button { background-color: #333333 !important; border: 1px solid #1A73E8 !important; font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. STRUCTURE DE L'INTERFACE ---
_, doc_col, ai_col = st.columns([0.2, 3, 1.2], gap="medium")

with doc_col:
    t_col, s_col = st.columns([3, 1])
    with t_col:
        title = st.text_input("Titre", value="Asa soratra 01", label_visibility="collapsed")
    with s_col:
        st.caption(f"🕒 {datetime.now().strftime('%H:%M')}")

    # Éditeur Quill
    content_html = st_quill(
        placeholder="Manomboha manoratra eto...",
        toolbar=[['bold', 'italic', 'underline'], [{'list': 'ordered'}, {'list': 'bullet'}]],
        key="quill_editor",
    )
    content_raw = re.sub('<[^<]+?>', '', content_html) if content_html else ""

    # --- ZONE D'AUTOCOMPLÉTION ---
    if content_raw:
        results = get_smart_suggestions(content_raw, ngram_models)
        if results:
            st.markdown("💡 **Soso-kevitra manaraka :**")
            cols = st.columns(len(results))
            for i, word in enumerate(results):
                # Note: Quill est en lecture seule pour l'injection directe via bouton dans cette version
                # Pour une insertion réelle, il faudrait utiliser un composant text_input ou un état partagé.
                cols[i].button(word, key=f"sugg_{i}", help="Soso-kevitra automatique")

with ai_col:
    st.markdown("<h3 style='color:#1A73E8;'>✨ Co-pilote IA</h3>", unsafe_allow_html=True)
    
    # Correction & Analyse
    with st.expander("🔍 Analyse & Correction", expanded=True):
        if st.button("Lancer l'analyse complète", use_container_width=True):
            if content_raw:
                mots_saisis = re.findall(r'\b[a-zàâéèêëîïôûùç]+\b', content_raw.lower())
                for word in list(set(mots_saisis)):
                    if len(word) <= 2: continue
                    if word in vocabulaire:
                        st.write(f"✅ **{word}** (Racine: `{lemma_dict[word]}`)")
                    elif model and vectorizer:
                        vec = vectorizer.transform([word])
                        prob = model.predict_proba(vec)[0][1]
                        if prob > 0.6:
                            st.warning(f"🤖 **{word}** (Nouveau mot)")
                        else:
                            st.error(f"❌ **{word}** (Inconnu)")
                            sugg = process.extractOne(word, vocabulaire)
                            if sugg and sugg[1] > 80: st.caption(f"Andramo : *{sugg[0]}*")
            else:
                st.info("Soraty aloha ny lahatsoratra.")

    # Phonotactique
    if content_raw and any(x in content_raw.lower() for x in ["nb", "mk", "np"]):
        st.error("⚠️ Règle : 'm' eo alohan'ny 'b' na 'p'.")

    # Stats
    st.divider()
    nb_teny = len(content_raw.split()) if content_raw else 0
    st.metric("Isan'ny teny", nb_teny)

st.markdown("---")
st.caption("Projet AI Malagasy - ISPM 2026")