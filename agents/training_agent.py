# basketcoach-mcp/agents/training_agent.py
#!/usr/bin/env python3
"""
Agent d'entraînement et de préparation physique
Génère des programmes personnalisés basés sur les données MCP
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

import os
import sys
# Ajouter le répertoire racine au Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from mcp_direct_client import direct_client, MCPDirectClient
from utils.logger import get_logger

logger = get_logger("agent.training")

class TrainingAgent:
    """Agent de préparation physique et d'entraînement personnalisé"""
    
    def __init__(self, mcp_direct_client: Optional[MCPDirectClient] = None):
        self.mcp_direct_client = mcp_direct_client or direct_client
        self.logger = logger
        
    async def generate_training_program(self, player_name: str, goals: List[str], 
                                     timeline_weeks: int = 8) -> Dict[str, Any]:
        """
        Génère un programme d'entraînement personnalisé
        Basé sur les données de performance et les objectifs
        """
        self.logger.info(f"💪 Génération programme entraînement: {player_name}")
        
        try:
            # 1. Analyse du joueur
            player_analysis = await self._analyze_player_needs(player_name)
            
            # 2. Récupération des recommandations existantes
            existing_recommendations = self.mcp_direct_client.get_training_recommendations(player_name)
            
            # 3. Génération du programme
            training_program = await self._create_training_program(
                player_name, player_analysis, goals, timeline_weeks, existing_recommendations
            )
            
            # 4. Guidelines de sécurité
            safety_guidelines = self.mcp_direct_client.search_guidelines("prévention blessures")
            
            return {
                "player": player_name,
                "program_type": "Personnalisé",
                "timeline_weeks": timeline_weeks,
                "goals": goals,
                "training_program": training_program,
                "player_analysis": player_analysis,
                "safety_guidelines": safety_guidelines.get("guidelines_found", []),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération programme: {e}")
            return {"error": f"Erreur génération programme: {str(e)}"}
    
    async def generate_team_training_plan(self, team_name: str, focus_areas: List[str],
                                        season_phase: str = "pre-season") -> Dict[str, Any]:
        """
        Génère un plan d'entraînement pour toute l'équipe
        """
        self.logger.info(f"👥 Plan entraînement équipe: {team_name} - {season_phase}")
        
        try:
            # 1. Analyse de l'équipe
            team_analysis = await self._analyze_team_training_needs(team_name)
            
            # 2. Génération du plan
            team_plan = await self._create_team_training_plan(
                team_name, team_analysis, focus_areas, season_phase
            )
            
            # 3. Calendrier d'entraînement
            training_schedule = await self._generate_training_schedule(season_phase)
            
            return {
                "team": team_name,
                "season_phase": season_phase,
                "focus_areas": focus_areas,
                "team_analysis": team_analysis,
                "training_plan": team_plan,
                "weekly_schedule": training_schedule,
                "periodization": await self._generate_periodization_plan(season_phase)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur plan équipe: {e}")
            return {"error": f"Erreur plan équipe: {str(e)}"}
    
    async def monitor_training_progress(self, player_name: str, program_start_date: str) -> Dict[str, Any]:
        """
        Surveille les progrès d'entraînement d'un joueur
        """
        self.logger.info(f"📊 Monitoring progrès: {player_name}")
        
        try:
            # 1. Données de performance actuelles
            current_performance = await self._get_current_performance(player_name)
            
            # 2. Comparaison avec le début du programme
            progress_analysis = await self._analyze_progress(
                player_name, program_start_date, current_performance
            )
            
            # 3. Ajustements recommandés
            adjustments = await self._recommend_adjustments(progress_analysis)
            
            return {
                "player": player_name,
                "program_start": program_start_date,
                "current_performance": current_performance,
                "progress_analysis": progress_analysis,
                "recommended_adjustments": adjustments,
                "next_assessment": (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur monitoring: {e}")
            return {"error": f"Erreur monitoring: {str(e)}"}
    
    async def generate_injury_prevention_plan(self, player_name: str, injury_history: List[str] = None) -> Dict[str, Any]:
        """
        Génère un plan de prévention des blessures personnalisé
        """
        self.logger.info(f"🛡️ Plan prévention blessures: {player_name}")
        
        if injury_history is None:
            injury_history = ["Cheville", "Genou"]  # Exemple
            
        try:
            # 1. Analyse du profil de risque
            risk_profile = await self._assess_injury_risk(player_name, injury_history)
            
            # 2. Récupération des guidelines
            prevention_guidelines = self.mcp_direct_client.search_guidelines("prévention blessures")
            specific_guidelines = []
            
            for injury in injury_history:
                specific_guidelines.extend(
                    self.mcp_direct_client.search_guidelines(injury).get("guidelines_found", [])
                )
            
            # 3. Génération du plan de prévention
            prevention_plan = await self._create_injury_prevention_plan(
                player_name, risk_profile, injury_history
            )
            
            return {
                "player": player_name,
                "injury_history": injury_history,
                "risk_profile": risk_profile,
                "prevention_plan": prevention_plan,
                "guidelines": prevention_guidelines.get("guidelines_found", []) + specific_guidelines,
                "monitoring_recommendations": await self._generate_monitoring_recommendations(risk_profile)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur plan prévention: {e}")
            return {"error": f"Erreur plan prévention: {str(e)}"}
    
    # Méthodes internes
    async def _analyze_player_needs(self, player_name: str) -> Dict[str, Any]:
        """Analyse les besoins d'entraînement du joueur"""
        
        # Récupération des données de performance
        impact_data = self.mcp_direct_client.get_player_impact("sample_match", player_name)
        training_recommendations = self.mcp_direct_client.get_training_recommendations(player_name)
        
        # Analyse des besoins (simplifiée)
        needs_analysis = {
            "physical_profile": await self._assess_physical_profile(player_name),
            "technical_weaknesses": await self._identify_technical_weaknesses(impact_data),
            "fitness_level": await self._assess_fitness_level(player_name),
            "recovery_needs": await self._assess_recovery_needs(player_name)
        }
        
        return {
            "player_name": player_name,
            "needs_analysis": needs_analysis,
            "existing_recommendations": training_recommendations,
            "readiness_level": "Optimal"
        }
    
    async def _create_training_program(self, player_name: str, player_analysis: Dict,
                                     goals: List[str], timeline_weeks: int,
                                     existing_recommendations: Dict) -> Dict[str, Any]:
        """Crée un programme d'entraînement personnalisé"""
        
        program = {
            "weekly_structure": await self._generate_weekly_structure(timeline_weeks),
            "strength_training": await self._generate_strength_program(player_analysis, goals),
            "skill_development": await self._generate_skill_program(player_analysis, goals),
            "conditioning": await self._generate_conditioning_program(player_analysis),
            "recovery_protocol": await self._generate_recovery_protocol(player_analysis),
            "nutrition_guidelines": await self._generate_nutrition_guidelines()
        }
        
        # Intégration des recommandations existantes
        if "recommendations" in existing_recommendations:
            for rec in existing_recommendations["recommendations"]:
                program["skill_development"]["exercises"].append({
                    "area": rec["area"],
                    "exercise": rec["exercise"],
                    "frequency": rec["frequency"]
                })
        
        return program
    
    async def _analyze_team_training_needs(self, team_name: str) -> Dict[str, Any]:
        """Analyse les besoins d'entraînement de l'équipe"""
        
        team_form = self.mcp_direct_client.get_team_form(team_name)
        
        return {
            "team_name": team_name,
            "current_form": team_form,
            "common_weaknesses": await self._identify_team_weaknesses(team_form),
            "fitness_level": "Good",
            "injury_status": "Healthy"
        }
    
    async def _create_team_training_plan(self, team_name: str, team_analysis: Dict,
                                       focus_areas: List[str], season_phase: str) -> Dict[str, Any]:
        """Crée un plan d'entraînement pour l'équipe"""
        
        return {
            "team_focus": focus_areas,
            "season_phase": season_phase,
            "collective_drills": await self._generate_collective_drills(focus_areas),
            "individual_work": await self._generate_individual_work_assignments(team_analysis),
            "video_sessions": await self._generate_video_session_topics(focus_areas),
            "scrimmage_focus": await self._determine_scrimmage_focus(season_phase)
        }
    
    async def _get_current_performance(self, player_name: str) -> Dict[str, Any]:
        """Récupère les performances actuelles du joueur"""
        impact_data = self.mcp_direct_client.get_player_impact("sample_match", player_name)
        
        return {
            "current_impact": impact_data.get("predicted_impact", 0),
            "fitness_metrics": await self._get_fitness_metrics(player_name),
            "technical_metrics": await self._get_technical_metrics(player_name)
        }
    
    async def _analyze_progress(self, player_name: str, start_date: str, 
                              current_performance: Dict) -> Dict[str, Any]:
        """Analyse les progrès depuis le début du programme"""
        
        # Simulation des données initiales
        initial_performance = {
            "impact": 18.0,
            "fitness_level": 7.5,
            "technical_skills": 7.0
        }
        
        current_impact = current_performance.get("current_impact", 0)
        progress = current_impact - initial_performance["impact"]
        
        return {
            "improvement_absolute": progress,
            "improvement_percentage": (progress / initial_performance["impact"]) * 100,
            "areas_improved": await self._identify_improved_areas(initial_performance, current_performance),
            "areas_needing_work": await self._identify_stagnant_areas(initial_performance, current_performance),
            "overall_progress_rating": self._calculate_progress_rating(progress)
        }
    
    async def _recommend_adjustments(self, progress_analysis: Dict) -> List[Dict]:
        """Recommande des ajustements au programme"""
        
        adjustments = []
        
        if progress_analysis["improvement_absolute"] < 2:
            adjustments.append({
                "type": "Intensity",
                "recommendation": "Augmenter l'intensité des exercices techniques",
                "rationale": "Progrès limités détectés"
            })
        
        if "Shooting" in progress_analysis["areas_needing_work"]:
            adjustments.append({
                "type": "Volume",
                "recommendation": "Augmenter le volume de tirs de 20%",
                "rationale": "Stagnation dans le pourcentage de réussite"
            })
        
        return adjustments
    
    async def _assess_injury_risk(self, player_name: str, injury_history: List[str]) -> Dict[str, Any]:
        """Évalue le risque de blessure du joueur"""
        
        return {
            "overall_risk": "Medium",
            "high_risk_areas": injury_history,
            "prevention_priority": "High" if len(injury_history) > 1 else "Medium",
            "biomechanical_assessment": await self._perform_biomechanical_assessment(player_name),
            "workload_tolerance": "Good"
        }
    
    async def _create_injury_prevention_plan(self, player_name: str, risk_profile: Dict,
                                           injury_history: List[str]) -> Dict[str, Any]:
        """Crée un plan de prévention des blessures"""
        
        return {
            "preventive_exercises": await self._generate_preventive_exercises(injury_history),
            "mobility_work": await self._generate_mobility_program(risk_profile),
            "recovery_protocol": await self._generate_injury_prevention_recovery(),
            "warning_signs": await self._identify_warning_signs(injury_history),
            "emergency_protocol": await self._generate_emergency_protocol()
        }
    
    # Méthodes de génération de contenu
    async def _assess_physical_profile(self, player_name: str) -> Dict[str, Any]:
        """Évalue le profil physique du joueur"""
        return {
            "strength": 8,
            "speed": 9,
            "agility": 8,
            "endurance": 7,
            "power": 8
        }
    
    async def _identify_technical_weaknesses(self, impact_data: Dict) -> List[str]:
        """Identifie les faiblesses techniques"""
        weaknesses = []
        stats = impact_data.get("stats_used", {})
        
        if stats.get("turnovers", 0) > 3:
            weaknesses.append("Ball handling under pressure")
        if stats.get("rebounds", 0) < 4:
            weaknesses.append("Rebounding positioning")
            
        return weaknesses
    
    async def _assess_fitness_level(self, player_name: str) -> str:
        """Évalue le niveau de forme physique"""
        return "Elite"
    
    async def _assess_recovery_needs(self, player_name: str) -> Dict[str, Any]:
        """Évalue les besoins en récupération"""
        return {
            "sleep_requirements": "8-9 hours",
            "nutritional_needs": "High protein, balanced carbs",
            "recovery_modalities": ["Cryotherapy", "Compression", "Active recovery"]
        }
    
    async def _generate_weekly_structure(self, timeline_weeks: int) -> List[Dict]:
        """Génère la structure hebdomadaire"""
        weeks = []
        for week in range(1, timeline_weeks + 1):
            weeks.append({
                "week": week,
                "focus": "Strength building" if week <= 4 else "Power development",
                "volume": "High" if week <= 2 else "Medium",
                "intensity": "Medium" if week <= 4 else "High"
            })
        return weeks
    
    async def _generate_strength_program(self, player_analysis: Dict, goals: List[str]) -> Dict[str, Any]:
        """Génère le programme de musculation"""
        return {
            "frequency": "3x/week",
            "exercises": [
                {"exercise": "Squat", "sets": "4x8", "focus": "Lower body power"},
                {"exercise": "Bench press", "sets": "4x8", "focus": "Upper body strength"},
                {"exercise": "Deadlift", "sets": "3x5", "focus": "Posterior chain"}
            ],
            "progression": "Linear periodization",
            "recovery_days": ["Wednesday", "Sunday"]
        }
    
    async def _generate_skill_program(self, player_analysis: Dict, goals: List[str]) -> Dict[str, Any]:
        """Génère le programme technique"""
        return {
            "frequency": "5x/week",
            "exercises": [
                {"exercise": "Form shooting", "reps": "100", "focus": "Mechanics"},
                {"exercise": "Game-speed dribbling", "duration": "15min", "focus": "Ball handling"},
                {"exercise": "Defensive slides", "duration": "10min", "focus": "Lateral quickness"}
            ],
            "specialized_work": await self._generate_specialized_work(goals)
        }
    
    async def _generate_conditioning_program(self, player_analysis: Dict) -> Dict[str, Any]:
        """Génère le programme de conditionnement"""
        return {
            "aerobic": {"sessions": "2x/week", "duration": "30min", "intensity": "Moderate"},
            "anaerobic": {"sessions": "2x/week", "format": "Interval training", "work:rest": "1:2"},
            "sport_specific": {"sessions": "3x/week", "focus": "Game simulation drills"}
        }
    
    async def _generate_recovery_protocol(self, player_analysis: Dict) -> Dict[str, Any]:
        """Génère le protocole de récupération"""
        return {
            "daily": ["Foam rolling", "Dynamic stretching", "Hydration protocol"],
            "post_training": ["Ice bath", "Compression garments", "Protein shake"],
            "weekly": ["Massage therapy", "Cryotherapy session", "Active recovery day"]
        }
    
    async def _generate_nutrition_guidelines(self) -> Dict[str, Any]:
        """Génère les guidelines nutritionnels"""
        return {
            "macronutrients": {"protein": "2g/kg", "carbs": "6g/kg", "fats": "1g/kg"},
            "hydration": "35-40ml/kg daily + 500ml per hour of training",
            "timing": {
                "pre_training": "Carb-focused meal 2-3 hours before",
                "post_training": "Protein + carbs within 30 minutes",
                "game_day": "Increased carb loading"
            }
        }
    
    async def _generate_collective_drills(self, focus_areas: List[str]) -> List[Dict]:
        """Génère les exercices collectifs"""
        drills = []
        for focus in focus_areas:
            if "defense" in focus.lower():
                drills.append({"name": "Shell drill", "duration": "20min", "focus": "Team defense"})
            if "offense" in focus.lower():
                drills.append({"name": "5-out motion", "duration": "25min", "focus": "Offensive spacing"})
        return drills
    
    async def _generate_individual_work_assignments(self, team_analysis: Dict) -> List[Dict]:
        """Génère les travaux individuels"""
        return [
            {"player_type": "Guards", "focus": "Pick and roll execution", "duration": "15min/day"},
            {"player_type": "Forwards", "focus": "Post moves and face-up", "duration": "20min/day"},
            {"player_type": "Centers", "focus": "Screen setting and rolling", "duration": "15min/day"}
        ]
    
    async def _generate_video_session_topics(self, focus_areas: List[str]) -> List[str]:
        """Génère les thèmes des sessions vidéo"""
        topics = []
        for focus in focus_areas:
            if "defense" in focus.lower():
                topics.append("Defensive rotations and help principles")
            if "offense" in focus.lower():
                topics.append("Reading defensive coverages")
        return topics
    
    async def _determine_scrimmage_focus(self, season_phase: str) -> str:
        """Détermine l'objectif des matchs d'entraînement"""
        focuses = {
            "pre-season": "System implementation and conditioning",
            "in-season": "Game preparation and adjustments", 
            "post-season": "Skill development and experimentation"
        }
        return focuses.get(season_phase, "General development")
    
    async def _generate_training_schedule(self, season_phase: str) -> Dict[str, Any]:
        """Génère l'emploi du temps d'entraînement"""
        base_schedule = {
            "monday": "Strength + Skill work",
            "tuesday": "Team practice + Conditioning",
            "wednesday": "Recovery + Individual work",
            "thursday": "Team practice + Video session",
            "friday": "Strength + Game preparation",
            "saturday": "Game day / Scrimmage",
            "sunday": "Complete rest"
        }
        
        return base_schedule
    
    async def _generate_periodization_plan(self, season_phase: str) -> Dict[str, Any]:
        """Génère le plan de périodisation"""
        return {
            "phase": season_phase,
            "objectives": await self._get_season_objectives(season_phase),
            "volume_trend": "Decreasing" if season_phase == "in-season" else "Increasing",
            "intensity_trend": "Increasing" if season_phase == "in-season" else "Stable"
        }
    
    async def _get_fitness_metrics(self, player_name: str) -> Dict[str, Any]:
        """Récupère les métriques de forme physique"""
        return {
            "vertical_jump": "28 inches",
            "sprint_time": "3.2s (court length)",
            "endurance_test": "Excellent",
            "body_fat": "12%"
        }
    
    async def _get_technical_metrics(self, player_name: str) -> Dict[str, Any]:
        """Récupère les métriques techniques"""
        return {
            "shooting_percentage": "45% FG, 38% 3P",
            "assist_to_turnover": "2.5:1",
            "defensive_rating": "102.3"
        }
    
    async def _identify_improved_areas(self, initial: Dict, current: Dict) -> List[str]:
        """Identifie les domaines d'amélioration"""
        improved = []
        if current.get("current_impact", 0) > initial["impact"]:
            improved.append("Overall impact")
        return improved
    
    async def _identify_stagnant_areas(self, initial: Dict, current: Dict) -> List[str]:
        """Identifie les domaines stagnants"""
        stagnant = []
        if abs(current.get("current_impact", 0) - initial["impact"]) < 1:
            stagnant.append("Shooting")
        return stagnant
    
    def _calculate_progress_rating(self, progress: float) -> str:
        """Calcule une note de progression"""
        if progress > 5: return "Excellent"
        elif progress > 2: return "Good"
        elif progress > 0: return "Satisfactory"
        else: return "Needs improvement"
    
    async def _generate_specialized_work(self, goals: List[str]) -> List[Dict]:
        """Génère le travail spécialisé selon les objectifs"""
        specialized = []
        for goal in goals:
            if "shooting" in goal.lower():
                specialized.append({"focus": "Shooting", "drill": "Game-speed catch and shoot"})
            if "defense" in goal.lower():
                specialized.append({"focus": "Defense", "drill": "Closeout and contest drills"})
        return specialized
    
    async def _identify_team_weaknesses(self, team_form: Dict) -> List[str]:
        """Identifie les faiblesses de l'équipe"""
        weaknesses = []
        form = team_form.get("last_matches", [])
        if form.count('L') > 2:
            weaknesses.append("Closing out games")
        return weaknesses
    
    async def _perform_biomechanical_assessment(self, player_name: str) -> Dict[str, Any]:
        """Effectue une évaluation biomécanique"""
        return {
            "movement_quality": "Good",
            "asymmetries": "Minor left-right imbalance",
            "mobility_restrictions": "Tight hip flexors",
            "strength_balance": "Balanced"
        }
    
    async def _generate_preventive_exercises(self, injury_history: List[str]) -> List[Dict]:
        """Génère les exercices préventifs"""
        exercises = []
        for injury in injury_history:
            if "cheville" in injury.lower():
                exercises.append({"area": "Ankle", "exercise": "Balance board work", "frequency": "Daily"})
            if "genou" in injury.lower():
                exercises.append({"area": "Knee", "exercise": "Single leg squats", "frequency": "3x/week"})
        return exercises
    
    async def _generate_mobility_program(self, risk_profile: Dict) -> Dict[str, Any]:
        """Génère le programme de mobilité"""
        return {
            "daily_routine": ["Dynamic warm-up", "Foam rolling", "Stretching"],
            "focus_areas": risk_profile.get("high_risk_areas", []),
            "duration": "15-20 minutes daily"
        }
    
    async def _generate_injury_prevention_recovery(self) -> Dict[str, Any]:
        """Génère le protocole de récupération pour prévention"""
        return {
            "sleep": "8-10 hours nightly",
            "nutrition": "Anti-inflammatory diet focus",
            "modalities": ["Compression", "Contrast therapy", "Mobility work"]
        }
    
    async def _identify_warning_signs(self, injury_history: List[str]) -> List[str]:
        """Identifie les signes avant-coureurs"""
        warnings = []
        for injury in injury_history:
            if "cheville" in injury.lower():
                warnings.append("Swelling or instability in ankle")
            if "genou" in injury.lower():
                warnings.append("Knee pain during cutting movements")
        return warnings
    
    async def _generate_emergency_protocol(self) -> Dict[str, Any]:
        """Génère le protocole d'urgence"""
        return {
            "immediate_response": "RICE protocol (Rest, Ice, Compression, Elevation)",
            "medical_contact": "Team physician within 24 hours",
            "return_to_play": "Graduated protocol with medical clearance"
        }
    
    async def _get_season_objectives(self, season_phase: str) -> List[str]:
        """Retourne les objectifs de la phase de saison"""
        objectives = {
            "pre-season": ["Build fitness base", "Implement systems", "Develop team chemistry"],
            "in-season": ["Maintain peak performance", "Make tactical adjustments", "Manage workload"],
            "post-season": ["Active recovery", "Skill development", "Address weaknesses"]
        }
        return objectives.get(season_phase, ["General development"])

    async def _generate_monitoring_recommendations(self, risk_profile: Dict) -> List[str]:
        """Génère les recommandations de monitoring"""
        return [
            "Daily wellness questionnaire",
            "Weekly mobility assessment", 
            "Bi-weekly strength testing",
            "Immediate reporting of any pain or discomfort"
        ]

# Interfaces synchrones pour Streamlit
def generate_training_program_sync(player_name: str, goals: List[str], timeline_weeks: int = 8) -> Dict[str, Any]:
    """Version synchrone pour Streamlit"""
    import asyncio
    agent = TrainingAgent()
    return asyncio.run(agent.generate_training_program(player_name, goals, timeline_weeks))

def generate_team_training_plan_sync(team_name: str, focus_areas: List[str], season_phase: str = "pre-season") -> Dict[str, Any]:
    """Version synchrone pour Streamlit"""
    import asyncio
    agent = TrainingAgent()
    return asyncio.run(agent.generate_team_training_plan(team_name, focus_areas, season_phase))