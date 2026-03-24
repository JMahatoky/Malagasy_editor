import json
import collections
import re

def train_multi_ngram(files, model_path):
    # On crée un dictionnaire pour chaque niveau
    models = {
        "2": collections.defaultdict(lambda: collections.Counter()),
        "3": collections.defaultdict(lambda: collections.Counter()),
        "4": collections.defaultdict(lambda: collections.Counter())
    }

    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    words = re.findall(r'\b\w+\b', line.lower())
                    
                    # On parcourt chaque n possible (2, 3, 4)
                    for n in [2, 3, 4]:
                        if len(words) < n: continue
                        for i in range(len(words) - n + 1):
                            context = " ".join(words[i : i + n - 1])
                            target = words[i + n - 1]
                            models[str(n)][context][target] += 1
        except FileNotFoundError:
            print(f"Fichier {file} non trouvé.")

    # Conversion pour JSON
    final_data = {
        n_val: {ctx: dict(counts) for ctx, counts in ctx_dict.items()}
        for n_val, ctx_dict in models.items()
    }
    
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False)
    print(f"Modèle multi-niveau sauvegardé dans {model_path}")

train_multi_ngram(['data.txt', 'journal.txt'], 'malagasy_multi_model.json')