import streamlit as st
import json

@st.cache_resource
def load_multi_model():
    with open('malagasy_multi_model.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_smart_suggestions(text, models):
    words = text.lower().strip().split()
    if not words: return []
    
    suggestions = []
    
    # 1. Tentative avec 4-gram (contexte de 3 mots)
    if len(words) >= 3:
        ctx4 = " ".join(words[-3:])
        if ctx4 in models["4"]:
            suggestions = sorted(models["4"][ctx4].items(), key=lambda x: x[1], reverse=True)
    
    # 2. Backoff vers Trigram (contexte de 2 mots) si pas assez de résultats
    if len(suggestions) < 3 and len(words) >= 2:
        ctx3 = " ".join(words[-2:])
        if ctx3 in models["3"]:
            new_sugg = sorted(models["3"][ctx3].items(), key=lambda x: x[1], reverse=True)
            # On ajoute sans doublons
            for word, count in new_sugg:
                if word not in [s[0] for s in suggestions]:
                    suggestions.append((word, count))

    # 3. Backoff vers Bigram (contexte de 1 mot)
    if len(suggestions) < 3 and len(words) >= 1:
        ctx2 = words[-1]
        if ctx2 in models["2"]:
            new_sugg = sorted(models["2"][ctx2].items(), key=lambda x: x[1], reverse=True)
            for word, count in new_sugg:
                if word not in [s[0] for s in suggestions]:
                    suggestions.append((word, count))

    return [s[0] for s in suggestions[:5]]

# --- Interface Streamlit ---
st.set_page_config(page_title="Malagasy Smart Predict", page_icon="🇲🇬")

if 'text_buffer' not in st.session_state:
    st.session_state.text_buffer = ""

models = load_multi_model()

st.title("🇲🇬 Smart Autocomplete (2/3/4-grams)")

# Champ de saisie
user_input = st.text_input("Soraty eto...", value=st.session_state.text_buffer)
st.session_state.text_buffer = user_input

if user_input.endswith(" "):
    results = get_smart_suggestions(user_input, models)
    
    if results:
        st.write("💡 **Soso-kevitra :**")
        cols = st.columns(len(results))
        for i, word in enumerate(results):
            if cols[i].button(word, key=f"btn_{i}"):
                st.session_state.text_buffer = user_input + word + " "
                st.rerun()
    else:
        st.caption("Tsy misy soso-kevitra hita amin'ireo datasets.")