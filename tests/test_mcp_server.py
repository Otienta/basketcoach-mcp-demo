#!/usr/bin/env python3
"""
Tests unitaires pour le serveur MCP BasketCoach
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Ajout du chemin racine pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from mcp_client import MCPClient
from utils.data_processor import DataProcessor
from ml.predict import Predictor

class TestMCPClient:
    """Tests pour le client MCP"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.client = MCPClient()
    
    def test_client_initialization(self):
        """Test l'initialisation du client"""
        assert self.client is not None
        assert hasattr(self.client, 'call_tool')
    
    def test_health_check(self):
        """Test la vérification de santé"""
        # Note: Ce test nécessite le serveur MCP en cours d'exécution
        health = self.client.health_check()
        assert isinstance(health, bool)

class TestDataProcessor:
    """Tests pour le processeur de données"""
    
    def setup_method(self):
        self.processor = DataProcessor()
    
    def test_directory_creation(self):
        """Test la création des répertoires"""
        assert Path("data/raw").exists()
        assert Path("data/processed").exists()
    
    def test_sample_data_processing(self):
        """Test le traitement des données d'exemple"""
        # Vérifie que le fichier d'exemple existe
        sample_path = Path("data/raw/sample_match.json")
        assert sample_path.exists()
        
        # Traitement des données
        df = self.processor.process_all_matches()
        
        if not df.empty:
            assert len(df) > 0
            assert 'match_id' in df.columns
            assert 'player_name' in df.columns

class TestPredictor:
    """Tests pour le système de prédiction"""
    
    def setup_method(self):
        self.predictor = Predictor()
    
    def test_predictor_initialization(self):
        """Test l'initialisation du prédicteur"""
        assert self.predictor is not None
    
    def test_prediction_methods_exist(self):
        """Test que les méthodes de prédiction existent"""
        assert hasattr(self.predictor, 'predict_single_player')
        assert hasattr(self.predictor, 'predict_multiple_players')

def test_config_loading():
    """Test le chargement de la configuration"""
    from utils.config import get_config
    config = get_config()
    
    assert config is not None
    assert config.get('version') == "1.0"
    assert 'mcp' in config.to_dict()

def test_rag_system():
    """Test le système RAG"""
    from rag.search import search_guidelines
    
    # Test de recherche basique
    results = search_guidelines("blessure", max_results=2)
    
    assert 'search_results' in results
    assert isinstance(results['search_results'], list)

# Tests d'intégration (nécessitent les services)
@pytest.mark.integration
class TestIntegration:
    """Tests d'intégration nécessitant les services"""
    
    def test_full_mcp_workflow(self):
        """Test le workflow complet MCP"""
        client = MCPClient()
        
        # Test si le serveur est accessible
        if client.health_check():
            # Test d'un outil simple
            result = client.get_current_lfb_ranking()
            assert isinstance(result, dict)
    
    def test_ml_training_integration(self):
        """Test l'intégration ML"""
        # Ce test nécessite des données pré-traitées
        data_path = Path("data/processed/all_matches_merged.csv")
        if data_path.exists():
            from ml.train import PlayerImpactModel
            model = PlayerImpactModel()
            assert model is not None

if __name__ == "__main__":
    # Exécution des tests basiques
    pytest.main([__file__, "-v"])