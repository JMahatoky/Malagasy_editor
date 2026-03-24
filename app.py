import streamlit as st
import json

# --- CHARGEMENT DU MODÈLE ---
@st.cache_resource
def load_model():
    with open('malagasy_global_model.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_suggestions(text, model_data):
    n = model_data['n']
    model = model_data['data']
    words = text.lower().strip().split()
    if not words: return []
    
    # On prend les (n-1) derniers mots
    context = " ".join(words[-(n-1):])
    if context in model:
        sorted_words = sorted(model[context].items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:5]]
    return []

# --- LOGIQUE DE MISE À JOUR ---
# Cette variable stocke le texte "source de vérité"
if 'buffer_texte' not in st.session_state:
    st.session_state.buffer_texte = ""

model_data = load_model()

st.title("🇲🇬 Autocomplétion Malagasy")
st.write("Tapez votre texte + **Espace** + **Entrée** pour voir les suggestions.")

# --- LE CHAMP DE SAISIE ---
# On utilise 'value' pour l'affichage, mais on ne définit PAS de 'key' identique à la variable
# pour éviter l'erreur "StreamlitAPIException"
input_actuel = st.text_input(
    "Soraty eto...", 
    value=st.session_state.buffer_texte,
    placeholder="Ohatra: Te hividy..."
)

# On synchronise le buffer avec ce que l'utilisateur vient de taper
st.session_state.buffer_texte = input_actuel

# --- AFFICHAGE DES SUGGESTIONS ---
if input_actuel.endswith(" "):
    suggestions = get_suggestions(input_actuel, model_data)
    
    if suggestions:
        st.markdown("### 💡 Soso-kevitra :")
        # On crée des colonnes pour les boutons
        cols = st.columns(len(suggestions))
        
        for i, word in enumerate(suggestions):
            # SI L'UTILISATEUR CLIQUE SUR LE BOUTON
            if cols[i].button(word, key=f"btn_{word}_{i}"):
                # 1. On met à jour le buffer avec le mot choisi
                st.session_state.buffer_texte = input_actuel + word + " "
                # 2. On force le rechargement immédiat pour que le text_input lise la nouvelle value
                st.rerun()
    else:
        st.caption("Tsy misy soso-kevitra hita.")

# Rappel pour l'utilisateur
st.divider()
st.info("Fanamarihana: Mila manindry 'Entrée' ianao aorian'ny fanasiana elanelana (espace) vao mipoitra ny soso-kevitra.")