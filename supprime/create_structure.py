import os

# Arborescence du projet
structure = {
    "app.py": "",
    "mcp_server.py": "",
    "mcp_client.py": "",
    "config.yaml": "",
    "requirements.txt": "",
    "setup.py": "",
    "README.md": "",
    "data/raw/": None,
    "data/processed/": None,
    "data/external/": None,
    "agents/coaching_agent.py": "",
    "agents/scouting_agent.py": "",
    "agents/training_agent.py": "",
    "ml/train.py": "",
    "ml/predict.py": "",
    "ml/model/": None,
    "rag/guidelines/": None,
    "rag/embed.py": "",
    "rag/search.py": "",
    "utils/web_scrapers.py": "",
    "utils/data_processor.py": "",
    "utils/logger.py": "",
    "scripts/run_mcp_server.py": "",
    "scripts/run_training.py": "",
    "scripts/setup_environment.py": "",
}

def create_project(struct):
    for path, content in struct.items():
        if path.endswith("/"):  
            os.makedirs(path, exist_ok=True)
            print(f"[DIR]  Created: {path}")
        else:
            # Créer le dossier parent si nécessaire
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)

            # Créer le fichier
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[FILE] Created: {path}")

if __name__ == "__main__":
    create_project(structure)
    print("\n🎉 Structure complète générée avec succès !")
