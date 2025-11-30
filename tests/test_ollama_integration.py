# tests/test_ollama_integration.py
import pytest
import asyncio
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from utils.ollama_client import generate_with_ollama, check_ollama_health

class TestOllamaIntegration:
    
    def test_ollama_health(self):
        """Test que Ollama est accessible"""
        assert check_ollama_health(), "Ollama doit être démarré sur localhost:11434"
    
    def test_basic_generation(self):
        """Test de génération basique"""
        response = generate_with_ollama("Réponds juste 'OK'")
        assert response is not None
        assert len(response) > 0
    
    def test_coaching_question(self):
        """Test d'une question de coaching"""
        question = "Comment améliorer la défense en zone ?"
        response = generate_with_ollama(question)
        assert "défense" in response.lower() or "zone" in response.lower()

if __name__ == "__main__":
    # Exécution des tests
    test_instance = TestOllamaIntegration()
    test_instance.test_ollama_health()
    test_instance.test_basic_generation()
    test_instance.test_coaching_question()
    print("✅ Tous les tests Ollama ont réussi!")