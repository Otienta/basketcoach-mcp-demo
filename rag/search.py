# basketcoach-mcp/rag/search.py
#!/usr/bin/env python3
"""
Interface de recherche pour le système RAG
Intégration simplifiée avec le serveur MCP
"""
from typing import List, Dict, Any
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.embed import rag_system, initialize_rag
from utils.logger import get_logger

# CORRECTION : Gestion plus robuste du reranker
try:
    from sentence_transformers import CrossEncoder
    RERANKER_MODEL = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    reranker = CrossEncoder(RERANKER_MODEL)
    RERANKER_AVAILABLE = True
    logger = get_logger("rag.search")
    logger.info("✅ Reranker chargé avec succès")
except Exception as e:
    logger = get_logger("rag.search")
    logger.warning(f"⚠️ Reranker non disponible: {e}")
    RERANKER_AVAILABLE = False
    reranker = None

def search_guidelines(query: str, max_results: int = 3, categories: List[str] = None) -> Dict[str, Any]:
    """
    Recherche des guidelines avec filtrage et Re-ranking - VERSION CORRIGÉE
    """
    try:
        if not rag_system.is_initialized:
            initialize_rag()
       
        # 1. Recherche initiale
        all_results_raw = rag_system.search(query, top_k=max_results * 5, similarity_threshold=0.0)
       
        # Filtrage par catégorie si spécifié
        if categories:
            results_to_rerank = [
                result for result in all_results_raw
                if result["category"] in categories
            ]
        else:
            results_to_rerank = all_results_raw
        
        # Si pas de résultats, retourner vide
        if not results_to_rerank:
            return {
                "search_results": [],
                "analysis": {
                    "query": query,
                    "total_found": 0,
                    "returned": 0,
                    "reranked_from": 0,
                    "categories_found": [],
                    "average_similarity": 0,
                },
                "suggestions": ["Aucun résultat trouvé. Essayez d'autres termes de recherche."]
            }
        
        # 2. RE-RANKING (si disponible)
        if RERANKER_AVAILABLE and reranker is not None:
            try:
                contents = [r['content'] for r in results_to_rerank]
                pairs = [[query, content] for content in contents]
                new_scores = reranker.predict(pairs)
                
                for i, result in enumerate(results_to_rerank):
                    result['rerank_score'] = float(new_scores[i])
                
                # Tri par score de reranking
                reranked_results = sorted(results_to_rerank, key=lambda x: x['rerank_score'], reverse=True)
                final_results = reranked_results[:max_results]
                
            except Exception as rerank_error:
                logger.warning(f"⚠️ Erreur reranking, utilisation des résultats initiaux: {rerank_error}")
                # En cas d'erreur, utiliser les résultats initiaux triés par similarité
                final_results = sorted(results_to_rerank, key=lambda x: x['similarity_score'], reverse=True)[:max_results]
        else:
            # Sans reranker, utiliser les résultats initiaux
            final_results = sorted(results_to_rerank, key=lambda x: x['similarity_score'], reverse=True)[:max_results]
        
        # 3. Préparation de l'analyse
        analysis = {
            "query": query,
            "total_found": len(all_results_raw),
            "returned": len(final_results),
            "reranked_from": len(results_to_rerank),
            "categories_found": list(set(r["category"] for r in final_results)),
            "average_similarity": sum(r.get('similarity_score', 0) for r in final_results) / len(final_results) if final_results else 0,
        }
        
        return {
            "search_results": final_results,
            "analysis": analysis,
            "suggestions": _generate_search_suggestions(query, final_results)
        }
   
    except Exception as e:
        logger.error(f"❌ Erreur recherche guidelines: {e}")
        return {
            "error": f"Erreur recherche: {str(e)}",
            "search_results": [],
            "analysis": {},
            "suggestions": ["Erreur temporaire. Veuillez réessayer."]
        }


def get_guideline_categories() -> List[str]:
    """
    Retourne la liste des catégories disponibles
    """
    try:
        if not rag_system.is_initialized:
            initialize_rag()
        
        categories = list(set(guideline["category"] for guideline in rag_system.guidelines_data))
        
        # S'assurer que les catégories de base existent
        base_categories = ["blessure", "prévention", "nutrition", "récupération", "entraînement"]
        for cat in base_categories:
            if cat not in categories:
                categories.append(cat)
        
        return sorted(categories)
    
    except Exception as e:
        logger.error(f"❌ Erreur récupération catégories: {e}")
        # Retourner les catégories de base en cas d'erreur
        return ["blessure", "prévention", "nutrition", "récupération", "entraînement"]

def add_custom_guideline(content: str, source: str = "Utilisateur", category: str = "personnalisé") -> bool:
    """
    Ajoute une guideline personnalisée au système
    """
    try:
        rag_system.add_guideline(content, source, category)
        logger.info(f"✅ Guideline personnalisée ajoutée: {category}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Erreur ajout guideline: {e}")
        return False

def _generate_search_suggestions(query: str, results: List[Dict]) -> List[str]:
    """Génère des suggestions de recherche basées sur les résultats"""
    suggestions = []
    
    if not results:
        suggestions.extend([
            "Essayez avec des termes plus généraux",
            "Vérifiez l'orthographe des mots-clés",
            "Consultez les catégories disponibles"
        ])
    else:
        categories = list(set(r["category"] for r in results))
        if len(categories) > 1:
            suggestions.append(f"Catégories trouvées: {', '.join(categories)}")
        
        if len(results) < 3:
            suggestions.append("Essayez d'élargir votre recherche pour plus de résultats")
    
    return suggestions

def get_guideline_category_counts() -> Dict[str, int]:
    """
    Retourne le nombre de guidelines par catégorie
    """
    try:
        if not rag_system.is_initialized:
            initialize_rag()
        
        category_counts = {}
        for guideline in rag_system.guidelines_data:
            category = guideline.get("category", "non catégorisé")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return category_counts
    
    except Exception as e:
        logger.error(f"❌ Erreur comptage catégories: {e}")
        return {}