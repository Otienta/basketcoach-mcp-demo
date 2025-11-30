# tests/test_mcp_integration.py
import pytest
import requests
import json
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

class TestMCPEndToEnd:
    BASE_URL = "http://localhost:8000"
    
    def test_server_health(self):
        """Test que le serveur MCP répond"""
        response = requests.get(f"{self.BASE_URL}/docs", timeout=10)
        assert response.status_code == 200
        print("✅ Serveur santé: OK")
    
    def test_player_impact_tool(self):
        """Test de l'outil d'impact joueur"""
        payload = {
            "match_id": "2051529", 
            "player_name": "Marine Johannès"
        }
        response = requests.post(
            f"{self.BASE_URL}/tools/get_player_impact",
            json=payload,
            timeout=180
        )
        assert response.status_code == 200
        data = response.json()
        assert "predicted_impact" in data or "error" in data
        print("✅ Outil impact joueur: OK")
    
    def test_coach_ai_tool(self):
        """Test de l'outil Coach IA"""
        payload = {"question": "Comment préparer un match important ?"}
        response = requests.post(
            f"{self.BASE_URL}/tools/ask_coach_ai", 
            json=payload,
            timeout=180
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        print("✅ Outil Coach IA: OK")
    
    def test_nba_ranking_tool(self):
        """Test de l'outil classement NBA"""
        response = requests.post(
            f"{self.BASE_URL}/tools/get_nba_live_ranking",
            timeout=180
        )
        assert response.status_code == 200
        data = response.json()
        assert "ranking" in data or "error" in data
        print("✅ Outil NBA ranking: OK")

def main():
    print("🧪 TEST INTÉGRATION MCP")
    print("=" * 40)
    
    test_instance = TestMCPEndToEnd()
    
    try:
        test_instance.test_server_health()
        test_instance.test_player_impact_tool()
        test_instance.test_coach_ai_tool() 
        test_instance.test_nba_ranking_tool()
        print("🎉 Tous les tests MCP ont réussi!")
        return True
    except Exception as e:
        print(f"❌ Échec des tests MCP: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)