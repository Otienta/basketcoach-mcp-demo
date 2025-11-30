# basketcoach-mcp/scripts/setup_environment.py
#!/usr/bin/env python3
"""
Script de setup et configuration de l'environnement BasketCoach MCP
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
import logging

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 ou supérieur requis")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")

def create_directory_structure():
    """Crée l'arborescence du projet"""
    directories = [
        "data/raw",
        "data/processed",
        "data/external",
        "ml/model",
        "ml/features",
        "rag/guidelines",
        "rag/embeddings",
        "rag/database",
        "logs",
        "scripts",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Créé: {directory}")

def check_dependencies():
    """Vérifie et installe les dépendances"""
    requirements = [
        "streamlit", "pandas", "numpy", "plotly",
        "requests", "aiohttp", "beautifulsoup4",
        "scikit-learn", "mlflow", "joblib",
        "sentence-transformers", "faiss-cpu",
        "pyyaml", "python-dotenv"
    ]
    
    missing = []
    for package in requirements:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n📦 Installation des packages manquants...")
        for package in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installé")
            except subprocess.CalledProcessError:
                print(f"❌ Échec installation {package}")
    
    return len(missing) == 0

def create_sample_data():
    """Crée des données d'exemple pour le test"""
    import json
    
    sample_match = {
        "id": "2051529",
        "date": "2024-01-15",
        "clock": "00:00",
        "period": 4,
        "periodLength": 10,
        "periodType": "REGULAR",
        "inOT": 0,
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
                        "shirtNumber": "23",
                        "starter": True,
                        "active": True,
                        "sPoints": 22,
                        "sReboundsTotal": 5,
                        "sAssists": 7,
                        "sSteals": 2,
                        "sBlocks": 1,
                        "sTurnovers": 3,
                        "sPlusMinusPoints": 15,
                        "sMinutes": "32:15",
                        "eff_1": 25,
                        "eff_2": 18,
                        "eff_3": 22
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
                        "shirtNumber": "5",
                        "starter": True,
                        "active": True,
                        "sPoints": 18,
                        "sReboundsTotal": 6,
                        "sAssists": 5,
                        "sSteals": 3,
                        "sBlocks": 0,
                        "sTurnovers": 2,
                        "sPlusMinusPoints": 8,
                        "sMinutes": "28:45",
                        "eff_1": 20,
                        "eff_2": 16,
                        "eff_3": 18
                    }
                }
            }
        }
    }
    
    with open("data/raw/sample_match.json", "w", encoding="utf-8") as f:
        json.dump(sample_match, f, indent=2, ensure_ascii=False)
    
    print("🏀 Créé: data/raw/sample_match.json (données d'exemple)")

def setup_mlflow():
    """Configure MLflow"""
    try:
        # Vérification si MLflow est accessible
        import mlflow
        mlflow.set_tracking_uri("http://localhost:5000")
        
        # Création de l'expérience
        try:
            mlflow.create_experiment("basketcoach-mcp")
            print("✅ Expérience MLflow créée")
        except:
            print("ℹ️  Expérience MLflow existe déjà")
            
    except Exception as e:
        print(f"⚠️  MLflow non configuré: {e}")

def main():
    """Fonction principale de setup"""
    print("🏀 BASKETCOACH MCP - SETUP COMPLET")
    print("=" * 60)
    
    try:
        # Vérifications de base
        print("\n1. Vérification de l'environnement Python...")
        check_python_version()
        
        # Création de l'arborescence
        print("\n2. Création de l'arborescence...")
        create_directory_structure()
        
        # Vérification des dépendances
        print("\n3. Vérification des dépendances...")
        deps_ok = check_dependencies()
        
        # Données d'exemple
        print("\n4. Création des données d'exemple...")
        create_sample_data()
        
        # Configuration MLflow
        print("\n5. Configuration MLflow...")
        setup_mlflow()
        
        # Instructions finales
        print("\n🎉 SETUP TERMINÉ AVEC SUCCÈS!")
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. 🚀 Lancez le serveur MCP: python scripts/run_mcp_server.py")
        print("2. 🌐 Ouvrez l'interface: streamlit run app.py")
        print("3. 🔧 Testez dans l'onglet 'Debug MCP'")
        print("4. 🧠 Entraînez le modèle: python scripts/run_training.py --process-data")
        
        print("\n🛠️  COMMANDES UTILES:")
        print("  Serveur MCP:    python scripts/run_mcp_server.py")
        print("  Interface:      streamlit run app.py")
        print("  Entraînement:   python scripts/run_training.py --process-data")
        print("  Traitement:     python -m utils.data_processor")
        
        if not deps_ok:
            print("\n⚠️  Certaines dépendances peuvent nécessiter une installation manuelle")
            print("   pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Erreur pendant le setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()