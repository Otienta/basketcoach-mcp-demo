# basketcoach-mcp/app.py
import streamlit as st
import pandas as pd
import asyncio
import sys
import os
from pathlib import Path

# Configuration du chemin
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from mcp_client import MCPClient
from agents.coaching_agent import analyze_match_strategy_sync
from agents.scouting_agent import comprehensive_player_scout_sync
from agents.training_agent import generate_training_program_sync

# Configuration de la page
st.set_page_config(
    page_title="BasketCoach MCP",
    page_icon="🏀",
    layout="wide"
)

# Titre principal
st.title("🏀 BasketCoach MCP - Plateforme de Coaching Intelligent")
st.markdown("### Analyse de matchs • Scouting • Entraînement • Coach IA")

# Initialisation du client MCP
@st.cache_resource
def get_mcp_client():
    return MCPClient()

client = get_mcp_client()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choisir une page",
    ["Accueil", "Analyse de Match", "Scouting", "Entraînement", "Coach IA", "Rapports"]
)

# Page d'accueil
if page == "Accueil":
    st.header("🎯 Bienvenue sur BasketCoach MCP")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Fonctionnalités principales:**
        - 📊 Analyse stratégique des matchs
        - 🔍 Scouting avancé des joueurs
        - 💪 Programmes d'entraînement personnalisés
        - 🤖 Coach IA pour conseils experts
        - 📈 Prédictions d'impact joueur
        """)
    
    with col2:
        st.success("""
        **Technologies utilisées:**
        - 🧠 Machine Learning (MLflow)
        - 🔧 MCP (Modular Coaching Platform)
        - 🌐 Web scraping intelligent
        - 💬 Ollama (IA locale)
        - ⚡ FastAPI + Streamlit
        """)
    
    # Vérification des services
    st.subheader("🔧 État des services")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        if client.health_check():
            st.success("✅ Serveur MCP")
        else:
            st.error("❌ Serveur MCP")
    
    with status_col2:
        from utils.ollama_client import check_ollama_health
        if check_ollama_health():
            st.success("✅ Ollama IA")
        else:
            st.error("❌ Ollama IA")
    
    with status_col3:
        data_path = ROOT_DIR / "data/processed/all_matches_merged.csv"
        if data_path.exists():
            st.success("✅ Données LFB")
        else:
            st.warning("⚠️ Données manquantes")

# Page analyse de match
elif page == "Analyse de Match":
    st.header("📊 Analyse Stratégique de Match")
    
    col1, col2 = st.columns(2)
    
    with col1:
        match_id = st.text_input("ID du match", value="2051529")
        player_name = st.text_input("Joueur à analyser", value="Marine Johannès")
    
    with col2:
        if st.button("🔍 Analyser le match", type="primary"):
            with st.spinner("Analyse en cours..."):
                try:
                    # Analyse stratégique
                    strategy_result = analyze_match_strategy_sync(match_id)
                    
                    if "error" in strategy_result:
                        st.error(f"Erreur: {strategy_result['error']}")
                    else:
                        st.success("✅ Analyse terminée!")
                        
                        # Affichage des équipes
                        st.subheader("🏃 Équipes")
                        teams = list(strategy_result.get('team_analyses', {}).keys())
                        st.write(f"**{teams[0]}** vs **{teams[1]}**")
                        
                        # Impact joueur
                        st.subheader("⭐ Impact joueur")
                        impact_result = client.get_player_impact(match_id, player_name)
                        if "predicted_impact" in impact_result:
                            st.metric(
                                label=f"Impact prédit - {player_name}",
                                value=f"{impact_result['predicted_impact']:.1f}",
                                delta=impact_result.get("interpretation", "")
                            )
                        
                        # Recommandations
                        st.subheader("🎯 Recommandations stratégiques")
                        reco = strategy_result.get('strategy_recommendations', {})
                        st.write(f"**Offensive:** {reco.get('offensive_focus', 'N/A')}")
                        st.write(f"**Défensive:** {reco.get('defensive_focus', 'N/A')}")
                        
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse: {e}")

# Page scouting
elif page == "Scouting":
    st.header("🔍 Scouting de Joueurs")
    
    player_name = st.text_input("Nom du joueur", value="Marine Johannès")
    
    if st.button("📊 Analyser le joueur", type="primary"):
        with st.spinner("Scouting en cours..."):
            try:
                result = comprehensive_player_scout_sync(player_name)
                
                if "error" in result:
                    st.error(f"Erreur: {result['error']}")
                else:
                    st.success("✅ Analyse de scouting terminée!")
                    
                    # Score de scouting
                    score = result.get('scouting_score', {})
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Score global", f"{score.get('overall_score', 'N/A')}")
                    with col2:
                        st.metric("Performance", f"{score.get('performance_score', 'N/A')}")
                    with col3:
                        st.metric("Potentiel", f"{score.get('potential_score', 'N/A')}")
                    
                    # Rapport détaillé
                    report = result.get('scouting_report', {})
                    
                    st.subheader("✅ Points forts")
                    for strength in report.get('strengths', []):
                        st.write(f"• {strength}")
                    
                    st.subheader("📈 Points d'amélioration")
                    for weakness in report.get('weaknesses', []):
                        st.write(f"• {weakness}")
                    
                    st.subheader("🎯 Recommandation")
                    st.info(report.get('recommendation', 'N/A'))
                    
            except Exception as e:
                st.error(f"Erreur lors du scouting: {e}")

# Page entraînement
elif page == "Entraînement":
    st.header("💪 Programmes d'Entraînement")
    
    col1, col2 = st.columns(2)
    
    with col1:
        player_name = st.text_input("Nom du joueur", value="Sarah Michel", key="training_player")
        goals = st.multiselect(
            "Objectifs d'entraînement",
            ["Tir", "Défense", "Physique", "Passe", "Dribble", "Conditionnement"],
            default=["Tir", "Défense"]
        )
    
    with col2:
        timeline = st.slider("Durée du programme (semaines)", 4, 12, 8)
    
    if st.button("🏋️ Générer le programme", type="primary"):
        with st.spinner("Création du programme..."):
            try:
                result = generate_training_program_sync(player_name, goals, timeline)
                
                if "error" in result:
                    st.error(f"Erreur: {result['error']}")
                else:
                    st.success("✅ Programme généré!")
                    
                    programme = result.get('training_program', {})
                    
                    st.subheader("📅 Structure hebdomadaire")
                    for week in programme.get('weekly_structure', []):
                        with st.expander(f"Semaine {week['week']} - {week['focus']}"):
                            st.write(f"Volume: {week['volume']}, Intensité: {week['intensity']}")
                    
                    st.subheader("💪 Entraînement musculaire")
                    for exercise in programme.get('strength_training', {}).get('exercises', []):
                        st.write(f"• **{exercise['exercise']}**: {exercise['sets']} - {exercise['focus']}")
                    
                    st.subheader("🏀 Développement technique")
                    for exercise in programme.get('skill_development', {}).get('exercises', []):
                        st.write(f"• **{exercise['exercise']}**: {exercise.get('reps', exercise.get('duration', ''))}")
                    
            except Exception as e:
                st.error(f"Erreur lors de la génération: {e}")

# Page Coach IA
elif page == "Coach IA":
    st.header("🤖 Coach IA - Expert Basketball")
    
    question = st.text_area(
        "Posez votre question au coach IA",
        placeholder="Ex: Comment améliorer notre défense de zone contre une équipe rapide ?",
        height=100
    )
    
    if st.button("🎯 Demander au coach", type="primary"):
        if not question.strip():
            st.warning("Veuillez poser une question")
        else:
            with st.spinner("Le coach réfléchit..."):
                try:
                    result = client.ask_coach_ai(question)
                    
                    if "answer" in result:
                        st.success("💡 Réponse du coach:")
                        st.info(result["answer"])
                    else:
                        st.error("Erreur lors de la consultation")
                        
                except Exception as e:
                    st.error(f"Erreur: {e}")

# Page rapports
elif page == "Rapports":
    st.header("📈 Génération de Rapports")
    
    match_id = st.text_input("ID du match pour le rapport", value="2051529")
    
    if st.button("📋 Générer le rapport coaching", type="primary"):
        with st.spinner("Génération du rapport..."):
            try:
                result = client.generate_coaching_report(match_id)
                
                if "report" in result:
                    st.success("✅ Rapport généré!")
                    st.text_area("Rapport détaillé", result["report"], height=400)
                else:
                    st.error(f"Erreur: {result.get('error', 'Inconnue')}")
                    
            except Exception as e:
                st.error(f"Erreur: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "BasketCoach MCP v1.0 - Plateforme de coaching basketball intelligente\n\n"
    "Utilise l'IA pour l'analyse, le scouting et l'entraînement."
)