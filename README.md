# 🏀 **BasketCoach MCP - Plateforme MLOps pour le Basketball Pro (2025)**

### *Système intelligent d'analyse, de coaching et de scouting basketball avec MLOps, MCP et IA*

<p align="center">
  <strong>MLOps • Analyse Joueur • Scouting • Classement LFB • Actualités • Recommandations d'entraînement • LLM Orchestration (MCP) • RAG</strong>
</p>


**NBA-grade UI • MCP • RAG • MLflow • Airflow • CI/CD • Docker • LLM Agents**

[![CI/CD](https://github.com/Otienta/basketcoach-mcp-demo/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Otienta/basketcoach-mcp-demo/actions)
[![Coverage](https://codecov.io/gh/Otienta/basketcoach-mcp-demo/branch/main/graph/badge.svg)](https://codecov.io/gh/Otienta/basketcoach-mcp-demo)
[![Docker Image](https://img.shields.io/docker/pulls/otienta/basketcoach-mcp-demo)](https://hub.docker.com/r/otienta/basketcoach-mcp-demo)

## 🚀 Démo Locale (5 min)
```bash
docker compose up --build
# Puis ouvre http://localhost:8501
---

> **La seule plateforme qui fait du coaching, du scouting, de l'entraînement et du MLOps dans une seule interface de malade.**

---

### Fonctionnalités Live (2025)

| Fonctionnalité              | Statut     | Tech |
|-----------------------------|----------|------|
| NBA Live + LFB Live           | Live     | Scraping + MCP |
| Analyse tactique IA         | Live     | LLM + MCP |
| Scouting complet + score    | Live     | ScoutingAgent |
| Programmes d'entraînement   | Live     | TrainingAgent |
| Rapport post-match IA       | Live     | MCP + RAG |
| RAG Guidelines médicales    | Live     | FAISS + SentenceTransformers |
| Prédiction Impact Joueur    | R²=0.995 | Random Forest + MLflow |
| CI/CD Automatique           | Live     | GitHub Actions |
| Docker + Multi-stage        | Live     | Docker |

---

### Déploiement en 1 clic (2025)

```bash
# Option 1 : Local
docker compose up -d

# Option 2 : Cloud (Render, Railway, Fly.io)
git push origin main  # déclenche CI/CD auto

---

## 🏷️ **Badges**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img src="https://img.shields.io/badge/MCP-Enabled-purple" />
  <img src="https://img.shields.io/badge/MLflow-Tracking-orange" />
  <img src="https://img.shields.io/badge/Airflow-Orchestration-red" />
  <img src="https://img.shields.io/badge/Streamlit-UI-brightgreen" />
  <img src="https://img.shields.io/badge/Docker-Containerized-cyan" />
  <img src="https://img.shields.io/badge/Status-Active-success" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

---

# 📚 **Table des matières**

1. [Introduction](#-introduction)
2. [Fonctionnalités](#-fonctionnalités)
3. [Architecture MLOps](#-architecture-mlops)
4. [Installation rapide](#-installation-rapide)
5. [Utilisation](#-utilisation)
6. [API MCP](#-api-mcp)
7. [Configuration](#-configuration)
8. [Docker](#-docker)
9. [Modèle ML](#-modèle-ml)
10. [Contribuer](#-contribution)
11. [Licence](#-license)
12. [Remerciements](#-remerciements)

---

# 🎯 **Introduction**

**BasketCoach MCP** est une plateforme MLOps avancée qui combine :

* **MLOps** : Gestion du cycle de vie des modèles avec MLFlow, orchestration des pipelines avec Airflow, CI/CD
* **Données locales LFB** (JSON 2021-2024) et données externes (scraping)
* **Intelligence artificielle** (modèle d'Impact Joueur) et **LLM** via *Model Context Protocol*
* **Moteur RAG** pour les guidelines médicales et techniques
* **Agents spécialisés** (coaching, scouting, entraînement)

Le tout dans **une seule interface intelligente** qui centralise *coaching*, *scouting*, *entraînement* et *analyse d'équipe* avec une approche MLOps.

---

# ✨ **Fonctionnalités**

### 🔍 Analyse de Joueur et d'Équipe

* **Impact ML** : Prédiction de l'impact des joueurs via un modèle Random Forest
* **Historique multi-matchs** et comparaison joueur vs joueur
* **Classement LFB** en temps réel et statistiques avancées
* **Actualités**, blessures, articles web

### 🤖 Agents intelligents (LLM + MCP)

* **Coaching Agent** : Analyse stratégique, plans de match, tendances adverses
* **Scouting Agent** : Analyse approfondie des joueurs, comparaison, recommandations de recrutement
* **Training Agent** : Programmes d'entraînement personnalisés, prévention des blessures

### 📚 RAG Guidelines

* Recherche sémantique dans les documents médicaux et techniques
* Embeddings avec SentenceTransformers et recherche FAISS

### 🛠️ MCP (Model Context Protocol)

* **9 outils MCP** disponibles : analyse de match, impact joueur, classement NBA, actualités, etc.
* Logs en temps réel et tests intégrés dans Streamlit

### 🚀 MLOps

* **MLFlow** : Tracking des expériences, registre de modèles, gestion du cycle de vie
* **Airflow** : Orchestration des pipelines de données et d'entraînement
* **CI/CD** : Automatisation des tests, de la construction et du déploiement
* **Docker** : Conteneurisation pour des environnements reproductibles
* **Monitoring** : Métriques de performance, dérive des données et du concept

---

# 🏗️ **Architecture MLOps**

## 📁 Structure du projet

```
basketcoach-mcp/
├── 🚀 app.py                          # Interface Streamlit
├── 🔧 basketcoach_mcp_server.py       # Serveur MCP principal
├── 📡 mcp_direct_client.py            # Client MCP avec logging
├── ⚙️ config.yaml                     # Configuration
├── 📋 requirements.txt                # Dépendances
├── 🏗️ setup.py
├── 📚 README.md
├── 🔐 .env
│
├── 📊 data/
│   ├── raw/                          # JSON LFB bruts
│   ├── processed/                    # Données traitées
│   └── external/                     # Cache web scraping
│
├── 🤖 agents/
│   ├── __init__.py
│   ├── coaching_agent.py             # ✅ Analyse stratégique
│   ├── scouting_agent.py             # ✅ Recrutement et analyse
│   ├── smart_coaching_agent.py
│   └── training_agent.py             # ✅ Préparation physique
│
├──  airflow/
│   └──  dags/
│          └── basketcoach_mcp_pipeline.py  # DAG Airflow
│
├── 🧠 ml/
│   ├── __init__.py
│   ├── train.py                      # ✅ Entraînement modèle
│   ├── predict.py                    # ✅ Prédictions
│   └── model/                        # Modèles MLflow
│
├── 🔍 rag/
│   ├── __init__.py
│   ├── embed.py                      # ✅ Système RAG
│   ├── search.py                     # ✅ Recherche guidelines
│   └── guidelines/                   # Documents PDF
│
├──  tests/
│   ├── test_coaching_agent.py
│   ├── test_scouting_agent.py
│   ├── test_training_agent.py
│   ├── test_nba_scraping.py
│   └── test_mcp_tools.py
│
├── 🌐 utils/
│   ├── __init__.py
│   ├── data_processor.py             # ✅ Traitement JSON
│   ├── ollama_client.py 
│   ├── config.py
│   └── logger.py                     # ✅ Logging centralisé
│
├── 📦 scripts/
│   ├── __init__.py
│   ├── run_mcp_server.py             # Lancement serveur
│   ├── run_training.py               # ✅ Entraînement ML
│   └── setup_environment.py          # Configuration
│
└── 🐳 docker/
    ├── Dockerfile
    └── docker-compose.yml
```

## 🔥 **Schéma d'architecture global (ASCII)**

```
                            ┌─────────────────────────┐
                            │        Streamlit         │
                            │      UI (app.py)         │
                            └─────────────┬───────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │      MCP Client       │
                              │   (logging avancé)    │
                              └─────────────┬─────────┘
                                            │
                                            ▼
                              ┌────────────────────────┐
                              │      MCP Server        │
                              │  9 Outils disponibles  │
                              └──────┬────────┬────────┘
                                     │        │
         ┌───────────────────────────┘        └───────────────────────────┐
         ▼                                                                ▼
┌──────────────────────┐                                      ┌─────────────────────┐
│   Web Scraping        │                                      │   Modèle MLflow     │
│  (classement, news)   │                                      │  Impact Joueur      │
└──────────────────────┘                                      └─────────────────────┘
         │                                                                │
         ▼                                                                ▼
┌──────────────────────┐                                      ┌─────────────────────┐
│     Data Processor    │                                      │   Agents LLM (3)     │
│  JSON → CSV → Features│                                      │ coaching/scouting/...│
└──────────────────────┘                                      └─────────────────────┘
         │                                                                │
         ▼                                                                ▼
┌──────────────────────┐                                      ┌─────────────────────┐
│     Airflow DAGs      │                                      │   RAG Guidelines    │
│  (orchestration)      │                                      │  (recherche)        │
└──────────────────────┘                                      └─────────────────────┘
```

## 🔄 **Workflow MLOps**

1. **Ingestion des données** : Airflow orchestre la collecte et le prétraitement des données LFB et externes.
2. **Entraînement du modèle** : Le pipeline d'entraînement est déclenché, les métriques et modèles sont suivis avec MLFlow.
3. **Évaluation et validation** : Le modèle est évalué et, si les métriques sont satisfaisantes, il est promu en production.
4. **Déploiement** : Le modèle est déployé via le pipeline CI/CD (container Docker, API, etc.).
5. **Monitoring** : Surveillance des performances du modèle en production (dérive des données, métriques métier).

---

# 🚀 **Installation rapide**

## 1. Cloner le projet

```bash
git clone <repository>
cd basketcoach-mcp
```

## 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

## 3. Préparer les données

```bash
python -c "from utils.data_processor import process_data_pipeline; process_data_pipeline()"
```

## 4. Lancer les services

```bash
# Serveur MCP
python scripts/run_mcp_server.py

# Interface Streamlit
streamlit run app.py

# MLflow (optionnel)
mlflow server --host localhost --port 5000

# Airflow (optionnel)
airflow webserver --port 8080
airflow scheduler
```

## 5. Accéder aux interfaces

* **Streamlit** : [http://localhost:8501](http://localhost:8501)
* **MLflow** : [http://localhost:5000](http://localhost:5000)
* **Airflow** : [http://localhost:8080](http://localhost:8080)

---

# 📊 **Utilisation**

## Interface Streamlit

L'interface Streamlit permet d'accéder à toutes les fonctionnalités :

* **Dashboard** : Vue d'ensemble des fonctionnalités et métriques
* **NBA Live** : Classement NBA et statistiques joueurs
* **Analyse Match** : Analyse stratégique des matchs LFB
* **Scouting Joueur** : Analyse approfondie et comparaison de joueurs
* **Programme Entraînement** : Programmes personnalisés et prévention des blessures
* **Rapport Coaching** : Rapports post-match détaillés générés par IA
* **MLOps Dashboard** : Surveillance des modèles et métriques MLOps
* **Outil MCP** : Test direct des outils MCP
* **Guidelines Basketball** : Recherche dans les guidelines médicales et techniques
* **Configuration** : Statut des services et configuration

---

# 📡 **API MCP**

Le serveur MCP expose plusieurs outils :

```python
from mcp_direct_client import direct_client

# Exemples d'utilisation
impact = direct_client.get_player_impact("2051529", "Marine Johannès")
ranking = direct_client.get_nba_live_ranking()
news = direct_client.get_player_news("Marine Johannès")
guidelines = direct_client.search_guidelines("entorse cheville")
coaching_report = direct_client.generate_coaching_report("2051529")
```

---

# 🔧 **Configuration**

Le fichier `config.yaml` permet de configurer :

```yaml
mcp:
  server:
    host: "localhost"
    port: 8000

ml:
  model:
    name: "player_impact_predictor"

web_sources:
  lfb_ranking: "https://www.basketlfb.com/classement/"

rag:
  guidelines_path: "rag/guidelines/"
```

---

# 🐳 **Docker**

Le projet peut être exécuté avec Docker :

```bash
docker-compose -f docker/docker-compose.yml up -d
```

---

# 📈 **Modèle ML**

Le modèle d'impact joueur est un Random Forest entraîné sur les données LFB.

* **Features** : points, rebonds, passes, interceptions, contres, turnovers, plus/minus
* **Target** : impact du joueur (formule pondérée)
* **Performance** : R² ~0.995

Entraînement :

```bash
python scripts/run_training.py
```

Tracking MLflow : [http://localhost:5000](http://localhost:5000)

---
## 🚀 CI/CD et Déploiement

### GitHub Actions
Le projet inclut un pipeline CI/CD complet :

'''yaml
- **Tests automatiques** sur 3 versions Python
- **Linting** avec Ruff
- **Build Docker** et push vers GitHub Container Registry
- **Déploiement automatique** staging
- **Déploiement manuel** production

---

# 🤝 **Contribution**

Les contributions sont les bienvenues !

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Pushez la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

---

# 📝 **License**

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

---

# 🙏 **Remerciements**

* Ligue Féminine de Basketball (LFB) pour les données
* MLflow pour le tracking des modèles
* Apache Airflow pour l'orchestration
* Streamlit pour l'interface utilisateur
* Model Context Protocol (MCP) pour l'intégration LLM

---

# 🎯 **Use Cases**

## 🏀 Pour les Clubs Professionnels

**Scénario** : Un club LFB veut recruter une joueuse pour combler un besoin spécifique.

**Solution BasketCoach** :
- Analyse des besoins via `ScoutingAgent.identify_recruitment_needs()`
- Comparaison des joueuses disponibles avec `ScoutingAgent.compare_players()`
- Génération d'un rapport de scouting complet
- Surveillance continue des performances via le dashboard MLOps

## 🏥 Pour les Staffs Médicaux

**Scénario** : Gestion des blessures et prévention.

**Solution BasketCoach** :
- Consultation des guidelines via `search_guidelines("prévention blessures cheville")`
- Programmes de prévention personnalisés via `TrainingAgent`
- Suivi de la récupération avec monitoring des métriques

## 📊 Pour les Analystes Sportifs

**Scénario** : Préparation tactique pour un match important.

**Solution BasketCoach** :
- Analyse des tendances adverses via `CoachingAgent.analyze_opponent_tendencies()`
- Génération de plans de match personnalisés
- Rapports post-match automatiques avec IA

## 🔬 Pour les Data Scientists

**Scénario** : Développement et monitoring de modèles ML.

**Solution BasketCoach** :
- Pipeline MLOps complet avec Airflow et MLflow
- Tracking des expériences et versioning des modèles
- Surveillance de la dérive des données et des concepts
- Dashboard de monitoring en temps réel

---

## 🚀 **Différences MLOps vs DevOps**

| Aspect | DevOps | MLOps |
|--------|--------|-------|
| **Cycle de vie** | Code + Infrastructure | Code + Données + Modèles |
| **Déploiement** | Application | Modèle + Application |
| **Monitoring** | Performance technique | Performance modèle + dérive données |
| **Reproductibilité** | Environnement de déploiement | Données + entraînement + environnement |
| **Tests** | Tests unitaires/intégration | Tests données + modèles + infrastructure |

**BasketCoach MCP** implémente les bonnes pratiques MLOps avec :
- ✅ **CI/CD** pour l'automatisation
- ✅ **MLflow** pour la reproductibilité
- ✅ **Airflow** pour l'orchestration
- ✅ **Monitoring** pour la surveillance continue
- ✅ **Conteneurisation** pour la portabilité

---

# 📞 **Support**

Pour toute question ou problème, ouvrez une issue sur le repository GitHub.

---

**BasketCoach MCP** - *Révolutionnez votre approche du basketball avec l'IA et le MLOps* 🏀✨