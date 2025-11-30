# basketcoach-mcp/utils/config.py
#!/usr/bin/env python3
"""
Gestionnaire de configuration pour BasketCoach MCP
Charge la configuration depuis YAML et variables d'environnement
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """Classe de gestion de configuration"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._load_config()
        return cls._instance
    
    @classmethod
    def _load_config(cls):
        """Charge la configuration depuis les fichiers"""
        try:
            # Chemin par défaut
            config_path = Path("config.yaml")
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config = yaml.safe_load(f)
            else:
                # Configuration par défaut
                cls._config = cls._get_default_config()
                
                # Sauvegarde de la configuration par défaut
                config_path.parent.mkdir(exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(cls._config, f, default_flow_style=False, allow_unicode=True)
            
            # Surcharge avec les variables d'environnement
            cls._override_with_env()
            
        except Exception as e:
            print(f"❌ Erreur chargement configuration: {e}")
            cls._config = cls._get_default_config()
    
    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """Retourne la configuration par défaut"""
        return {
            "version": "1.0",
            "description": "BasketCoach MCP - Plateforme de coaching basketball",
            
            "paths": {
                "data": {
                    "raw": "data/raw/",
                    "processed": "data/processed/",
                    "external": "data/external/"
                },
                "logs": "logs/",
                "models": "ml/model/",
                "rag": "rag/guidelines/"
            },
            
            "mcp": {
                "server": {
                    "host": "localhost",
                    "port": 8000,
                    "debug": True,
                    "log_level": "INFO"
                },
                "client": {
                    "timeout": 30,
                    "max_retries": 3
                }
            },
            
            "mlflow": {
                "tracking_uri": "http://localhost:5000",
                "experiment_name": "basketcoach-mcp",
                "registry_uri": "sqlite:///mlflow.db"
            },
            
            "web_sources": {
                "lfb_ranking": "https://www.basketlfb.com/classement/",
                "ffbb_news": "https://www.ffbb.com/actualites",
                "eurobasket_stats": "https://basketball.eurobasket.com/France/LFB/",
                "cache_duration": 3600
            },
            
            "ml": {
                "model": {
                    "name": "player_impact_predictor",
                    "version": "1.0.0",
                    "features": [
                        "points", "rebounds", "assists", "steals", 
                        "blocks", "turnovers", "plus_minus"
                    ],
                    "target": "player_impact"
                },
                "training": {
                    "test_size": 0.2,
                    "random_state": 42,
                    "cv_folds": 5
                }
            },
            
            "rag": {
                "guidelines_path": "rag/guidelines/",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "chunk_size": 500,
                "chunk_overlap": 50,
                "similarity_threshold": 0.7
            },
            
            "features": {
                "player_impact": {
                    "weights": {
                        "points": 1.0,
                        "rebounds": 0.7,
                        "assists": 0.8,
                        "steals": 1.2,
                        "blocks": 1.5,
                        "turnovers": -0.8,
                        "plus_minus": 0.5
                    },
                    "thresholds": {
                        "high_impact": 25,
                        "medium_impact": 15,
                        "low_impact": 0
                    }
                }
            },
            
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/basketcoach.log"
            }
        }
    
    @classmethod
    def _override_with_env(cls):
        """Surcharge la configuration avec les variables d'environnement"""
        env_mappings = {
            "MCP_SERVER_HOST": ["mcp", "server", "host"],
            "MCP_SERVER_PORT": ["mcp", "server", "port"],
            "MLFLOW_TRACKING_URI": ["mlflow", "tracking_uri"],
            "LOG_LEVEL": ["logging", "level"]
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                cls._set_nested_value(cls._config, config_path, env_value)
    
    @classmethod
    def _set_nested_value(cls, config_dict: Dict, path: list, value: Any):
        """Définit une valeur dans un dictionnaire imbriqué"""
        current = config_dict
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration
        Supporte la notation par points: 'mcp.server.port'
        """
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Définit une valeur de configuration"""
        keys = key.split('.')
        self._set_nested_value(self._config, keys, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Retourne la configuration complète comme dictionnaire"""
        return self._config.copy()

# Instances globales
config_instance = Config()

def get_config() -> Config:
    """Retourne l'instance de configuration"""
    return config_instance

def load_config(config_path: Optional[str] = None) -> Config:
    """Charge la configuration depuis un chemin spécifique"""
    if config_path and Path(config_path).exists():
        global config_instance
        config_instance = Config()
        config_instance._load_config_from_file(config_path)
    return config_instance