# basketcoach-mcp/scripts/run_training.py
#!/usr/bin/env python3
"""
Script de lancement de l'entraînement du modèle ML
"""

import os
import sys
import argparse
from pathlib import Path

# Ajout du chemin racine pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from ml.train import train_main
from utils.data_processor import process_data_pipeline
from utils.logger import get_logger

logger = get_logger("scripts.training")

def main():
    """Fonction principale d'entraînement"""
    parser = argparse.ArgumentParser(description="Entraînement du modèle BasketCoach")
    parser.add_argument("--process-data", action="store_true", 
                       help="Traiter les données avant l'entraînement")
    parser.add_argument("--force-retrain", action="store_true",
                       help="Forcer le ré-entraînement même si un modèle existe")
    
    args = parser.parse_args()
    
    try:
        logger.info("🎯 Démarrage du pipeline d'entraînement...")
        
        # Traitement des données si demandé
        if args.process_data:
            logger.info("🔄 Traitement des données...")
            df, validation_report, analysis_report = process_data_pipeline()
            
            if df.empty:
                logger.error("❌ Échec du traitement des données")
                return
        
        # Vérification de l'existence des données
        data_path = Path("data/processed/all_matches_merged.csv")
        if not data_path.exists():
            logger.error("❌ Aucune donnée traitée trouvée")
            logger.info("💡 Utilisez --process-data ou exécutez le traitement manuellement")
            return
        
        # Vérification de l'existence du modèle
        model_path = Path("ml/model/player_impact_predictor.pkl")
        if model_path.exists() and not args.force_retrain:
            logger.info("✅ Modèle existant trouvé. Utilisez --force-retrain pour ré-entraîner")
            return
        
        # Entraînement du modèle
        logger.info("🧠 Début de l'entraînement du modèle...")
        train_main()
        
        logger.info("🎉 Pipeline d'entraînement terminé avec succès!")
        
    except Exception as e:
        logger.error(f"💥 Erreur lors de l'entraînement: {e}")
        raise

if __name__ == "__main__":
    main()