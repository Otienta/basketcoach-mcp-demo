#!/usr/bin/env python3
"""
Test du système RAG
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.embed import rag_system

def test_rag():
    print("🧪 Test du système RAG...")
    
    # Initialisation
    rag_system.initialize()
    
    # Vérification des données
    print(f"📊 Guidelines chargées: {len(rag_system.guidelines_data)}")
    
    # Test de recherche
    queries = [
        "prévention blessures cheville",
        "nutrition sportive",
        "récupération après match",
        "entraînement intensif"
    ]
    
    for query in queries:
        print(f"\n🔍 Test: '{query}'")
        results = rag_system.search(query, top_k=3, similarity_threshold=0.3)
        print(f"📝 Résultats: {len(results)}")
        for result in results:
            print(f"  • {result['content'][:80]}... (score: {result['similarity_score']:.2f})")

if __name__ == "__main__":
    test_rag()