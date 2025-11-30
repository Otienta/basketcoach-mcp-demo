# basketcoach-mcp/ml/train.py
#!/usr/bin/env python3
"""
Entraînement du modèle de prédiction d'impact joueur
Utilise MLflow pour le tracking et le versioning
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib
import mlflow
import mlflow.sklearn
import logging
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("ml.train")

class PlayerImpactModel:
    """Modèle de prédiction d'impact joueur avec MLflow"""
    
    def __init__(self, model_name="player_impact_predictor"):
        self.config = get_config()
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.mlflow_experiment = "basketcoach-mcp"
        
        # Configuration MLflow
        mlflow.set_tracking_uri(self.config.get("mlflow.tracking_uri", "http://localhost:5000"))
        mlflow.set_experiment(self.mlflow_experiment)
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare les features pour l'entraînement
        """
        logger.info("🛠️ Préparation des features...")
        
        # Sélection des features de base
        base_features = [
            'points', 'rebounds_total', 'assists', 'steals', 'blocks', 
            'turnovers', 'plus_minus', 'minutes_played'
        ]
        
        # Calcul de features avancées
        df_processed = df.copy()
        
        # Conversion des minutes jouées en numérique
        df_processed['minutes_played'] = df_processed['minutes_played'].apply(
            self._convert_minutes_to_numeric
        )
        
        # Features d'efficacité
        df_processed['efficiency'] = (
            df_processed['points'] + 
            df_processed['rebounds_total'] + 
            df_processed['assists'] + 
            df_processed['steals'] + 
            df_processed['blocks'] -
            df_processed['turnovers']
        )
        
        # Features de productivité par minute
        df_processed['points_per_minute'] = df_processed['points'] / df_processed['minutes_played'].clip(lower=1)
        df_processed['rebounds_per_minute'] = df_processed['rebounds_total'] / df_processed['minutes_played'].clip(lower=1)
        
        # Feature cible (impact player calculé)
        df_processed['player_impact'] = self._calculate_player_impact(df_processed)
        
        # Sélection des features finales
        self.feature_names = base_features + ['efficiency', 'points_per_minute', 'rebounds_per_minute']
        
        return df_processed
    
    def train(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        """
        Entraîne le modèle avec tracking MLflow
        """
        logger.info("🚀 Début de l'entraînement du modèle...")
        
        try:
            # Préparation des données
            df_processed = self.prepare_features(df)
            
            # Séparation features/target
            X = df_processed[self.feature_names]
            y = df_processed['player_impact']
            
            # Gestion des valeurs manquantes
            X = X.fillna(0)
            y = y.fillna(0)
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            # Normalisation
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Début du tracking MLflow
            with mlflow.start_run(run_name=f"{self.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                
                # Paramètres du modèle
                model_params = {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 2,
                    'min_samples_leaf': 1,
                    'random_state': random_state
                }
                
                # Log des paramètres
                mlflow.log_params(model_params)
                mlflow.log_param("feature_count", len(self.feature_names))
                mlflow.log_param("training_samples", len(X_train))
                
                # Entraînement du modèle
                self.model = RandomForestRegressor(**model_params)
                self.model.fit(X_train_scaled, y_train)
                
                # Prédictions et évaluation
                y_pred = self.model.predict(X_test_scaled)
                
                # Métriques
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # Log des métriques
                mlflow.log_metrics({
                    'mse': mse,
                    'rmse': rmse,
                    'mae': mae,
                    'r2': r2
                })
                
                # Validation croisée
                cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='r2')
                mlflow.log_metric('cv_r2_mean', cv_scores.mean())
                mlflow.log_metric('cv_r2_std', cv_scores.std())
                
                # Importance des features
                feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
                for feature, importance in feature_importance.items():
                    mlflow.log_metric(f'feature_importance_{feature}', importance)
                
                # Sauvegarde du modèle
                model_path = f"ml/model/{self.model_name}.pkl"
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                joblib.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names,
                    'metadata': {
                        'trained_at': datetime.now().isoformat(),
                        'model_type': 'RandomForestRegressor',
                        'feature_count': len(self.feature_names),
                        'performance': {
                            'r2': r2,
                            'rmse': rmse,
                            'mae': mae
                        }
                    }
                }, model_path)
                
                # Log du modèle dans MLflow
                mlflow.sklearn.log_model(self.model, "model")
                mlflow.log_artifact(model_path)
                
                logger.info(f"✅ Modèle entraîné avec succès!")
                logger.info(f"📊 Performance - R²: {r2:.3f}, RMSE: {rmse:.3f}, MAE: {mae:.3f}")
                
                return {
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names,
                    'performance': {
                        'r2': r2,
                        'rmse': rmse,
                        'mae': mae,
                        'cv_r2_mean': cv_scores.mean(),
                        'cv_r2_std': cv_scores.std()
                    },
                    'feature_importance': feature_importance
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'entraînement: {e}")
            raise
    
    def predict(self, player_data: pd.DataFrame) -> np.ndarray:
        """
        Prédit l'impact d'un joueur
        """
        if self.model is None:
            raise ValueError("Modèle non entraîné. Appelez train() d'abord.")
        
        # Préparation des données
        player_data_processed = self.prepare_features(player_data)
        X = player_data_processed[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)
    
    def load_model(self, model_path: str):
        """
        Charge un modèle pré-entraîné
        """
        try:
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            logger.info(f"✅ Modèle chargé: {model_path}")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            raise
    
    def _convert_minutes_to_numeric(self, minutes_str: str) -> float:
        """
        Convertit le format 'MM:SS' en minutes décimales
        """
        if pd.isna(minutes_str) or minutes_str == '':
            return 0.0
        
        try:
            if ':' in minutes_str:
                parts = minutes_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1]) if len(parts) > 1 else 0
                return minutes + seconds / 60.0
            else:
                return float(minutes_str)
        except:
            return 0.0
    
    def _calculate_player_impact(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule la variable cible (impact du joueur)
        Utilise la formule pondérée du projet
        """
        config = self.config.get("features.player_impact.weights", {})
        
        weights = {
            'points': config.get('points', 1.0),
            'rebounds_total': config.get('rebounds_total', 0.7),
            'assists': config.get('assists', 0.8),
            'steals': config.get('steals', 1.2),
            'blocks': config.get('blocks', 1.5),
            'turnovers': config.get('turnovers', -0.8),
            'plus_minus': config.get('plus_minus', 0.5)
        }
        
        impact = (
            df['points'] * weights['points'] +
            df['rebounds_total'] * weights['rebounds_total'] +
            df['assists'] * weights['assists'] +
            df['steals'] * weights['steals'] +
            df['blocks'] * weights['blocks'] +
            df['turnovers'] * weights['turnovers'] +
            df['plus_minus'] * weights['plus_minus']
        )
        
        return impact

def train_main():
    """
    Fonction principale pour l'entraînement
    """
    logger.info("🏀 Démarrage de l'entraînement du modèle BasketCoach...")
    
    try:
        # Chargement des données
        data_path = "data/processed/all_matches_merged.csv"
        if not os.path.exists(data_path):
            logger.error(f"❌ Fichier de données non trouvé: {data_path}")
            logger.info("💡 Exécutez d'abord le traitement des données JSON")
            return
        
        df = pd.read_csv(data_path)
        logger.info(f"📊 Données chargées: {len(df)} lignes")
        
        # Filtrage des données joueurs (exclure les stats d'équipe)
        df_players = df[df['is_team'] == False].copy()
        logger.info(f"🎯 Données joueurs: {len(df_players)} lignes")
        
        if len(df_players) < 50:
            logger.warning("⚠️ Peu de données disponibles, les performances peuvent être limitées")
        
        # Entraînement du modèle
        model = PlayerImpactModel()
        results = model.train(df_players)
        
        logger.info("🎉 Entraînement terminé avec succès!")
        logger.info(f"📈 R² score: {results['performance']['r2']:.3f}")
        
        # Affichage de l'importance des features
        logger.info("🔍 Importance des features:")
        for feature, importance in sorted(results['feature_importance'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"   {feature}: {importance:.3f}")
            
    except Exception as e:
        logger.error(f"💥 Erreur lors de l'entraînement: {e}")

if __name__ == "__main__":
    train_main()