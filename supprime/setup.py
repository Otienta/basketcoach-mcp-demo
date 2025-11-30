# basketcoach-mcp/setup.py
#!/usr/bin/env python3
"""
Script de setup complet pour BasketCoach MCP
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess

def print_step(message):
    """Affiche un message d'étape formaté"""
    print(f"\n🎯 {message}")
    print("=" * 50)

def run_command(command, description):
    """Exécute une commande shell avec gestion d'erreur"""
    print(f"   🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} - Succès")
            return True
        else:
            print(f"   ❌ {description} - Échec: {result.stderr}")
            return False
    except Exception as e:
        print(f"   💥 {description} - Erreur: {e}")
        return False

def create_directory_structure():
    """Crée l'arborescence complète du projet"""
    print_step("Création de l'arborescence")
    
    directories = [
        # Data directories
        "data/raw",
        "data/processed", 
        "data/external",
        "data/backup",
        
        # ML directories
        "ml/model",
        "ml/features",
        "ml/experiments",
        
        # Agents directories
        "agents",
        
        # RAG directories
        "rag/guidelines",
        "rag/embeddings",
        "rag/database",
        
        # Utils directories
        "utils",
        
        # Scripts directories
        "scripts",
        
        # Logs directories
        "logs",
        "logs/mcp",
        "logs/training",
        
        # Documentation
        "docs",
        "docs/api",
        "docs/guides",
        
        # Tests
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   📁 Créé: {directory}")

def create_config_files():
    """Crée les fichiers de configuration"""
    print_step("Création des fichiers de configuration")
    
    # Fichier de configuration principal
    config_content = """# BasketCoach MCP - Configuration
version: "1.0"

paths:
  data:
    raw: "data/raw/"
    processed: "data/processed/"
    external: "data/external/"
  logs: "logs/"

mcp:
  server:
    host: "localhost"
    port: 8000

mlflow:
  tracking_uri: "http://localhost:5000"
  experiment_name: "basketcoach-mcp"

logging:
  level: "INFO"
"""
    
    with open("config.yaml", "w") as f:
        f.write(config_content)
    print("   📄 Créé: config.yaml")
    
    # Fichier .env example
    env_content = """# Configuration BasketCoach MCP
# Clés API externes (optionnelles)

# NewsAPI (pour actualités)
NEWS_API_KEY=your_newsapi_key_here

# SportsDataIO (pour stats avancées)
SPORTS_DATA_API_KEY=your_sportsdata_key_here

# Configuration MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Configuration logging
LOG_LEVEL=INFO
"""
    
    with open(".env.example", "w") as f:
        f.write(env_content)
    print("   🔐 Créé: .env.example")

def create_requirements():
    """Crée le fichier requirements.txt"""
    print_step("Création du fichier requirements.txt")
    
    requirements = """streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
requests>=2.31.0
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
mcp>=1.0.0
scikit-learn>=1.3.0
mlflow>=2.9.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("   📦 Créé: requirements.txt")

def create_readme():
    """Crée le fichier README.md"""
    print_step("Création de la documentation")
    
    readme_content = """# 🏀 BasketCoach MCP

Plateforme de coaching basketball intelligent combinant données locales LFB et données web via MCP.

## 🎯 Fonctionnalités

- **🔍 Analyse de joueurs** avec modèle ML d'impact
- **📊 Analyse d'équipes** et classement LFB en temps réel
- **📰 Actualités et blessures** via web scraping
- **💪 Recommandations d'entraînement** personnalisées
- **📚 Guidelines médicales** avec système RAG
- **🔄 MCP visible** avec logs en temps réel

## 🚀 Installation rapide

```bash
# 1. Cloner le projet
git clone <repository>
cd basketcoach-mcp

# 2. Setup automatique
python setup.py

# 3. Installation des dépendances
pip install -r requirements.txt

# 4. Lancer le serveur MCP
python scripts/run_mcp_server.py

# 5. Interface (nouveau terminal)
streamlit run app.py
```

## 📁 Structure du projet

```
basketcoach-mcp/
├── app.py              # Interface Streamlit
├── mcp_server.py       # Serveur MCP principal
├── mcp_client.py       # Client MCP
├── config.yaml         # Configuration
├── data/               # Données JSON LFB
├── agents/             # Agents spécialisés
├── ml/                 # Modèles ML
├── rag/               # Système RAG guidelines
└── utils/             # Utilitaires
```

## 🛠️ Utilisation

1. **Placez vos fichiers JSON LFB** dans `data/raw/`
2. **Lancez le serveur MCP** sur le port 8000
3. **Ouvrez l'interface Streamlit** sur http://localhost:8501
4. **Testez les outils MCP** dans l'onglet Debug

## 🔧 API MCP

Le serveur expose 8 outils MCP :

- `get_player_impact` - Impact prédit d'un joueur
- `get_current_lfb_ranking` - Classement LFB
- `get_player_news` - Actualités joueur
- `get_team_form` - Forme d'équipe
- `search_guidelines` - Guidelines médicales
- `get_match_analysis` - Analyse de match
- `get_player_comparison` - Comparaison joueurs
- `get_training_recommendations` - Recommandations entraînement

## 📊 Données supportées

- **Données locales**: JSON LFB 2021-2024 avec stats détaillées
- **Données web**: Classement LFB, actualités, blessures
- **Guidelines**: Documents ESC/EU basketball

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
"""

    with open("README.md", "w") as f:
        f.write(readme_content)
    print("   📚 Créé: README.md")

def create_sample_data():
    """Crée un exemple de données pour tester"""
    print_step("Création d'exemple de données")
    
    sample_json = {
        "id": "2051529",
        "date": "2024-01-15",
        "clock": "00:00",
        "period": 4,
        "tm": {
            "1": {
                "name": "ESB VILLENEUVE D'ASCQ LILLE METROPOLE",
                "code": "VIL",
                "tot_sPoints": 78,
                "tot_sReboundsTotal": 42,
                "tot_sAssists": 20,
                "tot_sSteals": 8,
                "tot_sBlocks": 4,
                "tot_sTurnovers": 12,
                "pl": {
                    "1": {
                        "firstName": "Marine",
                        "familyName": "Johannès",
                        "sPoints": 22,
                        "sReboundsTotal": 5,
                        "sAssists": 7,
                        "sSteals": 2,
                        "sBlocks": 1,
                        "sTurnovers": 3,
                        "sPlusMinusPoints": 15,
                        "sMinutes": "32:15"
                    }
                }
            },
            "2": {
                "name": "BOURGES BASKET",
                "code": "BOU", 
                "tot_sPoints": 72,
                "tot_sReboundsTotal": 38,
                "tot_sAssists": 18,
                "tot_sSteals": 6,
                "tot_sBlocks": 3,
                "tot_sTurnovers": 14,
                "pl": {
                    "1": {
                        "firstName": "Sarah",
                        "familyName": "Michel", 
                        "sPoints": 18,
                        "sReboundsTotal": 6,
                        "sAssists": 5,
                        "sSteals": 3,
                        "sBlocks": 0,
                        "sTurnovers": 2,
                        "sPlusMinusPoints": 8,
                        "sMinutes": "28:45"
                    }
                }
            }
        }
    }
    
    # Créer le fichier d'exemple
    import json
    with open("data/raw/sample_match.json", "w") as f:
        json.dump(sample_json, f, indent=2, ensure_ascii=False)
    
    print("   🏀 Créé: data/raw/sample_match.json (exemple de données)")

def install_dependencies():
    """Installe les dépendances Python"""
    print_step("Installation des dépendances")
    
    if run_command("pip install -r requirements.txt", "Installation des packages"):
        print("   ✅ Toutes les dépendances installées")
    else:
        print("   ⚠️  Certaines dépendances peuvent nécessiter une installation manuelle")

def final_instructions():
    """Affiche les instructions finales"""
    print_step("🎉 Setup terminé avec succès!")
    
    print("\n📋 **PROCHAINES ÉTAPES:**")
    print("1. 📁 Placez vos fichiers JSON LFB dans data/raw/")
    print("2. 🚀 Lancez le serveur MCP: python scripts/run_mcp_server.py")
    print("3. 🌐 Ouvrez l'interface: streamlit run app.py")
    print("4. 🔍 Testez dans l'onglet Debug MCP")
    
    print("\n🛠️ **COMMANDES UTILES:**")
    print("  Serveur MCP:    python mcp_server.py")
    print("  Interface:      streamlit run app.py")
    print("  Entraînement ML: python ml/train.py")
    print("  Test MCP:       python -m pytest tests/")
    
    print("\n📞 **SUPPORT:**")
    print("  Vérifiez les logs: tail -f logs/basketcoach.log")
    print("  Test santé MCP: curl http://localhost:8000/health")
    
    print("\n🎯 **POUR VOTRE SUPERVISEUR:**")
    print("  Le MCP est visible dans l'onglet 'Debug MCP'")
    print("  8 outils disponibles avec logs en temps réel")
    print("  Combinaison données locales + web scraping")

def main():
    """Fonction principale"""
    print("🏀 BASKETCOACH MCP - SETUP COMPLET")
    print("=" * 60)
    
    try:
        # Création de la structure
        create_directory_structure()
        create_config_files()
        create_requirements()
        create_readme()
        create_sample_data()
        
        # Installation (optionnelle)
        install_prompt = input("\n❓ Voulez-vous installer les dépendances maintenant? (o/N): ")
        if install_prompt.lower() in ['o', 'oui', 'y', 'yes']:
            install_dependencies()
        
        # Instructions finales
        final_instructions()
        
    except Exception as e:
        print(f"❌ Erreur pendant le setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()