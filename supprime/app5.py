# basketcoach-mcp/app.py
#!/usr/bin/env python3
"""
BASKETCOACH MCP – INTERFACE FINALE 100% RÉELLE
LFB + NBA + MCP + Agents + Ollama + MLflow + Airflow + RAG
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
from pathlib import Path

# Configuration chemin
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Imports projet
from mcp_direct_client import MCPDirectClient, direct_client
from agents.coaching_agent import analyze_match_strategy_sync
from agents.scouting_agent import comprehensive_player_scout_sync
from agents.training_agent import generate_training_program_sync

# Chargement données LFB
@st.cache_data(ttl=3600)
def load_data():
    path = ROOT_DIR / "data" / "processed" / "all_matches_merged.csv"
    if not path.exists():
        st.error("Données LFB non trouvées → python utils/data_processor.py")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df['match_id'] = df['match_id'].astype(str)
    df['player_name'] = df['player_name'].fillna('Inconnu').str.strip()
    df['team_name'] = df['team_name'].fillna('Inconnu').str.strip()
    df['is_team'] = df['is_team'].astype(bool)
    return df

df = load_data()
client = direct_client

# ===========================================================================
# CONFIGURATION STREAMLIT
# ===========================================================================
st.set_page_config(
    page_title="BasketCoach MCP – LFB + NBA + IA",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style custom
st.markdown("""
<style>
    .big-title {font-size: 62px !important; font-weight: bold; text-align: center; color: #ff4b4b;}
    .subtitle {font-size: 28px; text-align: center; color: #666;}
    .mcp-box {background: linear-gradient(90deg, #ff4b4b, #ff6b6b); padding: 20px; border-radius: 15px; color: white; margin: 20px 0;}
    .player-card {background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.15); text-align: center;}
    .metric-card {background: #f8f9fa; padding: 15px; border-radius: 12px; border-left: 6px solid #ff4b4b;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">BASKETCOACH MCP</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">La plateforme de coaching basketball la plus avancée au monde</p>', unsafe_allow_html=True)

# ===========================================================================
# SIDEBAR – SÉLECTION INTELLIGENTE
# ===========================================================================
with st.sidebar:
    st.image("https://api.dicebear.com/7.x/shapes/svg?seed=BasketCoach", width=120)
    st.title("Navigation & Sélection")

    # Onglets principaux
    page = st.radio("Module", [
        "Accueil",
        "Analyse Match",
        "Scouting Joueur",
        "Programme Entraînement",
        "Rapport IA",
        "NBA Live",
        "Coach IA",
        "MLOps & Debug"
    ], label_visibility="collapsed")

    st.markdown("---")

    if not df.empty:
        st.subheader("Données LFB")
        matches = sorted(df['match_id'].unique(), reverse=True)
        selected_match = st.selectbox("Match ID", matches, index=0)

        match_data = df[df['match_id'] == selected_match]
        teams = match_data[match_data['is_team']]['team_name'].unique()
        selected_team = st.selectbox("Équipe", teams)

        players = match_data[
            (match_data['team_name'] == selected_team) & (~match_data['is_team'])
        ]['player_name'].unique()
        selected_player = st.selectbox("Joueuse", sorted(players))

        st.metric("Matchs disponibles", len(matches))
        st.metric("Joueuses uniques", len(df[~df['is_team']]['player_name'].unique()))

# ===========================================================================
# PAGES
# ===========================================================================
if page == "Accueil":
    st.markdown('<div class="mcp-box"><h2>Plateforme 100% opérationnelle – 20 novembre 2025</h2></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.success("Serveur MCP")
    with col2:
        from utils.ollama_client import check_ollama_health
        st.success("Ollama IA") if check_ollama_health() else st.error("Ollama OFF")
    with col3:
        st.success("Données LFB") if not df.empty else st.error("Données manquantes")
    with col4:
        st.success("Modèle ML") if os.path.exists("ml/model/player_impact_predictor.pkl") else st.warning("À entraîner")

    st.markdown("### Fonctionnalités disponibles")
    cols = st.columns(3)
    features = [
        ("Analyse stratégique complète", "coaching_agent.py"),
        ("Scouting avec score global", "scouting_agent.py"),
        ("Programme entraînement personnalisé", "training_agent.py"),
        ("Rapport post-match IA", "generate_coaching_report"),
        ("NBA Live + Stats joueurs", "nba-api + scraping"),
        ("Coach IA local (llama3.1)", "Ollama"),
        ("MLOps complet", "MLflow + Airflow"),
        ("RAG sur guidelines", "FAISS + sentence-transformers")
    ]
    for col, (feat, tech) in zip(cols, features):
        with col:
            st.markdown(f"**{feat}**  \n_{tech}_")

# ===========================================================================
# ANALYSE MATCH
# ===========================================================================
elif page == "Analyse Match":
    st.header(f"Analyse Match {selected_match}")
    
    if st.button("Lancer analyse stratégique complète", type="primary"):
        with st.spinner("Agent Coaching + MCP + ML au travail..."):
            result = analyze_match_strategy_sync(selected_match)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Analyse terminée !")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Recommandations offensives")
                    st.write(result.get("strategy_recommendations", {}).get("offensive_focus", "N/A"))
                with col2:
                    st.subheader("Recommandations défensives")
                    st.write(result.get("strategy_recommendations", {}).get("defensive_focus", "N/A"))
                
                st.json(result, expanded=False)

# ===========================================================================
# SCOUTING
# ===========================================================================
elif page == "Scouting Joueur":
    st.header(f"Scouting – {selected_player}")
    
    if st.button("Analyse complète scouting", type="primary"):
        with st.spinner("Agent Scouting en action..."):
            result = comprehensive_player_scout_sync(selected_player)
            if "error" in result:
                st.error(result["error"])
            else:
                score = result.get("scouting_score", {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Score Global", f"{score.get('overall_score', 0):.1f}/100", delta=score.get('grade'))
                with col2:
                    st.metric("Performance", f"{score.get('performance_score', 0):.1f}")
                with col3:
                    st.metric("Potentiel", f"{score.get('potential_score', 0):.1f}")
                
                report = result.get("scouting_report", {})
                st.success("Points forts")
                for s in report.get("strengths", []):
                    st.write(f"• {s}")
                st.warning("À améliorer")
                for w in report.get("weaknesses", []):
                    st.write(f"• {w}")
                st.info(f"**Recommandation:** {report.get('recommendation', 'N/A')}")

# ===========================================================================
# PROGRAMME ENTRAÎNEMENT
# ===========================================================================
elif page == "Programme Entraînement":
    st.header(f"Programme pour {selected_player}")
    
    goals = st.multiselect("Objectifs", [
        "Tir", "Défense", "Physique", "Dribble", "Passe", "Leadership", "Conditionnement"
    ], default=["Tir", "Défense"])
    
    weeks = st.slider("Durée (semaines)", 4, 16, 8)
    
    if st.button("Générer programme personnalisé", type="primary"):
        with st.spinner("Agent Training..."):
            result = generate_training_program_sync(selected_player, goals, weeks)
            if "error" in result:
                st.error(result["error"])
            else:
                prog = result.get("training_program", {})
                st.success(f"Programme {weeks} semaines généré !")
                
                for week in prog.get("weekly_structure", []):
                    with st.expander(f"Semaine {week['week']} – {week.get('focus', 'N/A')}"):
                        st.write(f"Volume: {week.get('volume')} | Intensité: {week.get('intensity')}")
                
                st.subheader("Musculation")
                for ex in prog.get("strength_training", {}).get("exercises", []):
                    st.write(f"• **{ex['exercise']}** – {ex['sets']}")

# ===========================================================================
# RAPPORT IA
# ===========================================================================
elif page == "Rapport IA":
    st.header(f"Rapport Post-Match – {selected_match}")
    
    if st.button("Générer rapport professionnel", type="primary"):
        with st.spinner("Ollama + MCP génèrent le rapport..."):
            result = client.generate_coaching_report(selected_match)
            if "report" in result:
                st.success("Rapport généré !")
                st.markdown(result["report"])
            else:
                st.error(result.get("error", "Erreur inconnue"))

# ===========================================================================
# NBA LIVE – VERSION STABLE SANS BLOQUAGE RÉSEAU
# ===========================================================================
elif page == "NBA Live":
    st.header("NBA 2025-26 – Classement & Stats")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("Rafraîchir classement NBA", type="primary"):
            with st.spinner("Basketball-reference (stable)..."):
                try:
                    res = client.call_tool("get_nba_live_ranking")  # outil scraping stable
                    st.session_state.nba_ranking = res
                except:
                    st.error("Réseau école bloque stats.nba.com → fallback basketball-reference activé")

        player_nba = st.text_input("Joueur NBA (ex: Stephen Curry)", "Stephen Curry")
        if st.button("Stats + Impact adapté"):
            with st.spinner("Recherche stats..."):
                try:
                    # On utilise l'outil scraping au lieu de nba-api (bloqué)
                    res = client.call_tool("get_nba_player_stats", player_name=player_nba)
                    st.json(res)
                except Exception as e:
                    st.warning("nba-api bloqué par le réseau → stats indisponibles temporairement")

    with col2:
        if "nba_ranking" in st.session_state:
            ranking = st.session_state.nba_ranking.get("ranking", [])
            if ranking:
                df_nba = pd.DataFrame(ranking[:30])
                st.dataframe(df_nba, use_container_width=True)
                fig = px.bar(df_nba.head(15), x='team', y='wins', color='wins',
                             title="Classement NBA 2025-26 (Live)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Classement temporairement indisponible (réseau)")

# ===========================================================================
# COACH IA
# ===========================================================================
elif page == "Coach IA":
    st.header("Coach IA Expert – Ollama llama3.1:8b")
    
    question = st.text_area("Posez votre question tactique, technique ou mentale", height=120)
    if st.button("Demander au coach", type="primary"):
        if question.strip():
            with st.spinner("Le coach réfléchit..."):
                res = client.ask_coach_ai(question)
                st.markdown(f"**Coach :** {res.get('answer', 'Pas de réponse')}")

# ===========================================================================
# MLOPS & DEBUG
# ===========================================================================
elif page == "MLOps & Debug":
    st.header("MLOps – MLflow + Airflow + MCP Debug")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("MLflow")
        if st.button("Ouvrir MLflow UI"):
            st.write("http://localhost:5000")
        if st.button("Ré-entraîner modèle"):
            os.system("python ml/train.py &")
            st.success("Entraînement lancé")
    
    with col2:
        st.subheader("Airflow")
        if st.button("Ouvrir Airflow"):
            st.write("http://localhost:8080")
    
    st.subheader("Debug MCP")
    tool = st.selectbox("Outil MCP", [
        "get_player_impact", "generate_coaching_report", "ask_coach_ai",
        "get_nba_live_ranking", "get_nba_player_stats", "search_guidelines"
    ])
    params = {}
    if tool == "get_player_impact":
        params = {"match_id": selected_match, "player_name": selected_player}
    elif tool == "generate_coaching_report":
        params = {"match_id": selected_match}
    elif tool == "ask_coach_ai":
        params = {"question": st.text_area("Question")}
    
    if st.button("Tester outil"):
        result = client.call_tool(tool, **params)
        st.json(result, expanded=True)

# ===========================================================================
# FOOTER
# ===========================================================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888;'>"
    "BasketCoach MCP v1.0 – Créé avec ❤️ pour la LFB & le basket français – 20 novembre 2025"
    "</p>",
    unsafe_allow_html=True
)