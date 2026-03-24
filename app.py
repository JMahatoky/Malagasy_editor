import streamlit as st
import json
import re

# Configuration de la page
st.set_page_config(page_title="Autocomplétion Malagasy", page_icon="🇲🇬")

@st.cache_resource
def load_model(model_path):
    with open(model_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_suggestions(full_text, model_data, nb_suggestions=5):
    n = model_data['n']
    model = model_data['data']
    
    # Nettoyage et découpage
    words = full_text.lower().split()
    if not words:
        return []

    # Si le texte finit par un espace, on cherche le mot suivant
    # Sinon, on est en train de taper un mot (préfixe)
    if full_text.endswith(" "):
        context_words = words[-(n-1):]
        prefix = ""
    else:
        context_words = words[-(n):-(1)] if len(words) >= n else words[:-1]
        prefix = words[-1]

    context = " ".join(context_words)
    
    candidates = []
    if context in model:
        # Filtrer par préfixe et trier par fréquence
        for word, count in model[context].items():
            if word.startswith(prefix):
                candidates.append((word, count))
        
        candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    
    return [c[0] for c in candidates[:nb_suggestions]]

# --- INTERFACE STREAMLIT ---
st.title("🇲🇬 Autocomplétion Malagasy")
st.markdown("Tapez votre texte ci-dessous. Les suggestions s'adaptent en temps réel.")

# Chargement du modèle
try:
    model_data = load_model('malagasy_global_model.json')
    
    # Initialisation du texte dans la session state pour pouvoir le modifier
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""

    # Zone de saisie
    text_input = st.text_input(
        "Soraty eto...", 
        value=st.session_state.user_input, 
        key="main_input",
        placeholder="Ohatra: Te hividy..."
    )

    # Récupération des suggestions
    if text_input:
        suggestions = get_suggestions(text_input, model_data)
        
        if suggestions:
            st.write("**Suggestions :**")
            cols = st.columns(len(suggestions))
            
            for i, word in enumerate(suggestions):
                # Si on clique sur un bouton, on complète le texte
                if cols[i].button(word):
                    # Logique de complétion
                    words = text_input.split()
                    if text_input.endswith(" "):
                        new_text = text_input + word + " "
                    else:
                        words[-1] = word # Remplace le préfixe par le mot complet
                        new_text = " ".join(words) + " "
                    
                    st.session_state.user_input = new_text
                    st.rerun() # Recharge l'app avec le nouveau texte

except FileNotFoundError:
    st.error("Fichier modèle introuvable. Veuillez lancer l'entraînement d'abord.")