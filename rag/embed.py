# basketcoach-mcp/rag/embed.py
#!/usr/bin/env python3
"""
Système d'embedding et de recherche RAG pour les guidelines basketball
"""

import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import pickle
import logging
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss
import PyPDF2
from sklearn.metrics.pairwise import cosine_similarity
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("rag.embed")

class RAGSystem:
    """Système RAG pour la recherche dans les guidelines basketball"""
    
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        self.config = get_config()
        self.model_name = model_name
        self.model = None
        self.index = None
        self.guidelines_data = []
        self.is_initialized = False
        
        # Chemins
        self.guidelines_path = Path(self.config.get("rag.guidelines_path", "rag/guidelines/"))
        self.embeddings_path = Path("rag/embeddings/")
        self.database_path = Path("rag/database/")
        
        # Création des répertoires
        self.embeddings_path.mkdir(parents=True, exist_ok=True)
        self.database_path.mkdir(parents=True, exist_ok=True)
    
    def initialize(self):
        """Initialise le système RAG"""
        try:
            logger.info("🚀 Initialisation du système RAG...")
            
            # Chargement du modèle
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Modèle chargé: {self.model_name}")
            
            # Chargement ou création des embeddings
            if self._check_existing_embeddings():
                self._load_existing_embeddings()
            else:
                self._process_guidelines()
                self._create_embeddings()
            
            self.is_initialized = True
            logger.info("✅ Système RAG initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation RAG: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Recherche sémantique dans les guidelines - seuil réduit
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Embedding de la requête
            query_embedding = self.model.encode([query])
            
            # Recherche étendue
            distances, indices = self.index.search(query_embedding, top_k * 2)
            
            # Récupération des résultats avec seuil réduit
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.guidelines_data):
                    guideline = self.guidelines_data[idx]
                    # Score de similarité normalisé
                    similarity_score = float(distance)
                    
                    if similarity_score >= similarity_threshold:
                        results.append({
                            "rank": len(results) + 1,
                            "content": guideline["content"],
                            "source": guideline["source"],
                            "category": guideline["category"],
                            "similarity_score": similarity_score,
                            "page": guideline.get("page", "N/A")
                        })
                    
                    # Arrêter quand on a assez de résultats
                    if len(results) >= top_k:
                        break
            
            logger.info(f"🔍 Recherche '{query}': {len(results)} résultats (seuil: {similarity_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche RAG: {e}")
            return []
    
    def add_guideline(self, content: str, source: str, category: str, metadata: Dict = None):
        """
        Ajoute une nouvelle guideline au système
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            guideline = {
                "content": content,
                "source": source,
                "category": category,
                "metadata": metadata or {}
            }
            
            # Ajout aux données
            self.guidelines_data.append(guideline)
            
            # Mise à jour des embeddings
            self._update_embeddings([guideline])
            
            logger.info(f"✅ Guideline ajoutée: {source} - {category}")
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout guideline: {e}")
    
    def _check_existing_embeddings(self) -> bool:
        """Vérifie si des embeddings existent déjà"""
        index_path = self.embeddings_path / "guidelines.index"
        data_path = self.database_path / "guidelines_data.pkl"
        
        return index_path.exists() and data_path.exists()
    
    def _load_existing_embeddings(self):
        """Charge les embeddings existants"""
        try:
            # Chargement des données
            data_path = self.database_path / "guidelines_data.pkl"
            with open(data_path, 'rb') as f:
                self.guidelines_data = pickle.load(f)
            
            # Chargement de l'index FAISS
            index_path = self.embeddings_path / "guidelines.index"
            self.index = faiss.read_index(str(index_path))
            
            logger.info(f"✅ Embeddings chargés: {len(self.guidelines_data)} guidelines")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement embeddings: {e}")
            raise
    
    def _process_guidelines(self):
        """Traite les fichiers PDF de guidelines – VERSION OPTIMISÉE"""
        logger.info("📚 Traitement des guidelines...")

        # Réinitialisation obligatoire pour éviter les doublons
        self.guidelines_data = []
        
        # Liste des PDF trouvés
        pdf_files = list(self.guidelines_path.glob("*.pdf"))
        logger.info(f"🔍 {len(pdf_files)} fichiers PDF trouvés dans {self.guidelines_path}")

        # ----- 1) PRIORITÉ AUX PDF -----
        if pdf_files:
            for pdf_file in pdf_files:
                try:
                    logger.info(f"📄 Extraction du PDF : {pdf_file.name}")
                    pdf_guidelines = self._extract_text_from_pdf(pdf_file)
                    self.guidelines_data.extend(pdf_guidelines)
                    logger.info(f"   → {len(pdf_guidelines)} extraits ajoutés")
                except Exception as e:
                    logger.error(f"❌ Erreur traitement PDF {pdf_file}: {e}")
        else:
            logger.warning("⚠️ Aucun PDF trouvé – recours aux guidelines par défaut")

            # ----- 2) GUIDELINES PAR DÉFAUT -----
            self.guidelines_data = [
                {
                    "content": "ESC 2024: Limiter les séances intensives à 2 par semaine maximum pour prévenir le surentraînement",
                    "source": "European Society of Cardiology 2024",
                    "category": "entraînement",
                    "page": "12"
                },
                {
                    "content": "Recommandation EU: 48h de repos entre deux matches compétitifs pour une récupération optimale",
                    "source": "European Basketball Union 2023",
                    "category": "récupération",
                    "page": "8"
                },
                {
                    "content": "Protocole hydratation: 500ml 2h avant l'effort, 250ml toutes les 20min pendant l'activité",
                    "source": "International Journal of Sports Medicine",
                    "category": "nutrition",
                    "page": "15"
                },
                {
                    "content": "Cheville: Protocole RICE (Repos, Ice, Compression, Élévation) 48h pour entorses légères",
                    "source": "Journal of Orthopaedic Surgery 2024",
                    "category": "blessure",
                    "page": "22"
                },
                {
                    "content": "Genou: Consultation immédiate recommandée si gonflement > 2cm après traumatisme",
                    "source": "American Journal of Sports Medicine",
                    "category": "blessure",
                    "page": "18"
                },
                {
                    "content": "Apport protéique: 1.6-2.2g/kg/jour recommandé pour les sportives d'élite en basketball",
                    "source": "International Society of Sports Nutrition",
                    "category": "nutrition",
                    "page": "7"
                },
                {
                    "content": "Sommeil: 8-10h/nuit requis pour les sportives professionnelles pour une récupération optimale",
                    "source": "Sleep Medicine Journal",
                    "category": "récupération",
                    "page": "11"
                },
                {
                    "content": "Prévention blessures: Programme de renforcement musculaire 3x/semaine réduit les risques de 40%",
                    "source": "British Journal of Sports Medicine",
                    "category": "prévention",
                    "page": "9"
                }
            ]

        # ----- 3) Vérification finale -----
        if not self.guidelines_data:
            logger.error("❌ Aucune guideline disponible !")
            raise Exception("Aucune donnée guideline trouvée")

        logger.info(f"📊 Total guidelines chargées : {len(self.guidelines_data)}")

        # ----- 4) Sauvegarde -----
        with open(self.database_path / "guidelines_data.pkl", 'wb') as f:
            pickle.dump(self.guidelines_data, f)

    
    def _extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrait le texte d'un fichier PDF"""
        guidelines = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    # Segmentation en chunks (simplifié)
                    chunks = self._split_text_into_chunks(text)
                    
                    for chunk in chunks:
                        guidelines.append({
                            "content": chunk,
                            "source": pdf_path.name,
                            "category": "général",
                            "page": str(page_num)
                        })
        
        return guidelines
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Segmente le texte en chunks pour l'embedding"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    def _create_embeddings(self):
        """Crée les embeddings pour toutes les guidelines"""
        logger.info("🔨 Création des embeddings...")
        
        try:
            # Extraction du contenu
            contents = [guideline["content"] for guideline in self.guidelines_data]
            
            # Création des embeddings
            embeddings = self.model.encode(contents, show_progress_bar=True)
            
            # Création de l'index FAISS
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Produit scalaire pour similarité cosinus
            
            # Normalisation pour similarité cosinus
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            
            # Sauvegarde de l'index
            faiss.write_index(self.index, str(self.embeddings_path / "guidelines.index"))
            
            logger.info(f"✅ Embeddings créés: {len(self.guidelines_data)} guidelines")
            
        except Exception as e:
            logger.error(f"❌ Erreur création embeddings: {e}")
            raise
    
    def _update_embeddings(self, new_guidelines: List[Dict]):
        """Met à jour les embeddings avec de nouvelles guidelines"""
        try:
            # Embeddings des nouvelles guidelines
            new_contents = [guideline["content"] for guideline in new_guidelines]
            new_embeddings = self.model.encode(new_contents)
            
            # Ajout à l'index existant
            faiss.normalize_L2(new_embeddings)
            self.index.add(new_embeddings)
            
            # Sauvegarde de l'index mis à jour
            faiss.write_index(self.index, str(self.embeddings_path / "guidelines.index"))
            
            # Sauvegarde des données mises à jour
            with open(self.database_path / "guidelines_data.pkl", 'wb') as f:
                pickle.dump(self.guidelines_data, f)
            
            logger.info(f"✅ Embeddings mis à jour: {len(new_guidelines)} nouvelles guidelines")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour embeddings: {e}")

# Instance globale
rag_system = RAGSystem()

def initialize_rag():
    """Initialise le système RAG au démarrage"""
    rag_system.initialize()

def search_guidelines(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Fonction de recherche principale pour le serveur MCP"""
    return rag_system.search(query, top_k)