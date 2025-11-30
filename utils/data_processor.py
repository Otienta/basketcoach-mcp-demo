# basketcoach-mcp/utils/data_processor.py
#!/usr/bin/env python3
"""
Processeur de données pour les fichiers JSON LFB
Conversion et nettoyage des données brutes
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import sys
import os
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger("utils.data_processor")

class DataProcessor:
    """Processeur de données pour les matchs LFB"""
    
    def __init__(self, raw_data_path: str = "data/raw/", processed_path: str = "data/processed/"):
        self.raw_data_path = Path(raw_data_path)
        self.processed_path = Path(processed_path)
        self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def process_all_matches(self) -> pd.DataFrame:
        """
        Traite tous les fichiers JSON et crée un dataset consolidé
        """
        logger.info("🔄 Traitement de tous les matchs...")
        
        all_matches_data = []
        json_files = list(self.raw_data_path.glob("*.json"))
        
        if not json_files:
            logger.warning("⚠️ Aucun fichier JSON trouvé dans data/raw/")
            return pd.DataFrame()
        
        for json_file in json_files:
            try:
                match_data = self._process_single_match(json_file)
                all_matches_data.extend(match_data)
                logger.info(f"✅ {json_file.name} traité")
            except Exception as e:
                logger.error(f"❌ Erreur traitement {json_file}: {e}")
        
        if all_matches_data:
            df = pd.DataFrame(all_matches_data)
            
            # Sauvegarde
            output_file = self.processed_path / "all_matches_merged.csv"
            df.to_csv(output_file, index=False)
            
            logger.info(f"💾 Dataset sauvegardé: {output_file}")
            logger.info(f"📊 {len(df)} lignes, {len(df['match_id'].unique())} matchs traités")
            
            return df
        else:
            logger.error("❌ Aucune donnée traitée")
            return pd.DataFrame()
    
    def _process_single_match(self, json_file: Path) -> List[Dict[str, Any]]:
        """
        Traite un seul fichier JSON de match
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        extracted_data = []
        match_id = match_data.get('id', json_file.stem)
        
        # Informations générales du match
        match_info = {
            'match_id': match_id,
            'date': match_data.get('date', ''),
            'period': match_data.get('period', 0),
            'clock': match_data.get('clock', '00:00'),
            'inOT': match_data.get('inOT', 0)
        }
        
        # Parcours des équipes
        for team_key in ['1', '2']:
            if team_key not in match_data.get('tm', {}):
                continue
                
            team_data = match_data['tm'][team_key]
            team_name = team_data.get('name', 'Unknown')
            
            # Statistiques d'équipe
            team_stats = self._extract_team_stats(team_data, match_info, team_name)
            extracted_data.append(team_stats)
            
            # Statistiques par joueur
            players_data = self._extract_players_stats(team_data, match_info, team_name)
            extracted_data.extend(players_data)
        
        return extracted_data
    
    def _extract_team_stats(self, team_data: Dict, match_info: Dict, team_name: str) -> Dict[str, Any]:
        """Extrait les statistiques d'équipe"""
        return {
            **match_info,
            'team_name': team_name,
            'player_name': team_name,
            'is_team': True,
            'points': team_data.get('tot_sPoints', 0),
            'rebounds_total': team_data.get('tot_sReboundsTotal', 0),
            'rebounds_offensive': team_data.get('tot_sReboundsOffensive', 0),
            'rebounds_defensive': team_data.get('tot_sReboundsDefensive', 0),
            'assists': team_data.get('tot_sAssists', 0),
            'steals': team_data.get('tot_sSteals', 0),
            'blocks': team_data.get('tot_sBlocks', 0),
            'turnovers': team_data.get('tot_sTurnovers', 0),
            'fouls_personal': team_data.get('tot_sFoulsPersonal', 0),
            'points_from_turnovers': team_data.get('tot_sPointsFromTurnovers', 0),
            'points_second_chance': team_data.get('tot_sPointsSecondChance', 0),
            'points_fast_break': team_data.get('tot_sPointsFastBreak', 0),
            'points_in_the_paint': team_data.get('tot_sPointsInThePaint', 0),
            'bench_points': team_data.get('tot_sBenchPoints', 0)
        }
    
    def _extract_players_stats(self, team_data: Dict, match_info: Dict, team_name: str) -> List[Dict[str, Any]]:
        """Extrait les statistiques par joueur"""
        players_data = []
        players = team_data.get('pl', {})
        
        for player_id, player_data in players.items():
            if isinstance(player_data, dict):
                player_stats = {
                    **match_info,
                    'team_name': team_name,
                    'player_name': f"{player_data.get('firstName', '')} {player_data.get('familyName', '')}".strip(),
                    'is_team': False,
                    'shirt_number': player_data.get('shirtNumber', ''),
                    'starter': player_data.get('starter', False),
                    'active': player_data.get('active', True),
                    'points': player_data.get('sPoints', 0),
                    'rebounds_total': player_data.get('sReboundsTotal', 0),
                    'rebounds_offensive': player_data.get('sReboundsOffensive', 0),
                    'rebounds_defensive': player_data.get('sReboundsDefensive', 0),
                    'assists': player_data.get('sAssists', 0),
                    'steals': player_data.get('sSteals', 0),
                    'blocks': player_data.get('sBlocks', 0),
                    'turnovers': player_data.get('sTurnovers', 0),
                    'fouls_personal': player_data.get('sFoulsPersonal', 0),
                    'plus_minus': player_data.get('sPlusMinusPoints', 0),
                    'minutes_played': player_data.get('sMinutes', '0:00'),
                    'efficiency_1': player_data.get('eff_1', 0),
                    'efficiency_2': player_data.get('eff_2', 0),
                    'efficiency_3': player_data.get('eff_3', 0),
                    'efficiency_4': player_data.get('eff_4', 0),
                    'efficiency_5': player_data.get('eff_5', 0),
                    'efficiency_6': player_data.get('eff_6', 0),
                    'efficiency_7': player_data.get('eff_7', 0)
                }
                players_data.append(player_stats)
        
        return players_data
    
    def validate_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valide la qualité du dataset
        """
        validation_report = {
            'total_rows': len(df),
            'total_matches': df['match_id'].nunique(),
            'total_teams': df[df['is_team']]['team_name'].nunique(),
            'total_players': df[~df['is_team']]['player_name'].nunique(),
            'missing_data': {},
            'data_quality': {}
        }
        
        # Analyse des données manquantes
        for column in df.columns:
            missing_count = df[column].isna().sum()
            if missing_count > 0:
                validation_report['missing_data'][column] = {
                    'count': missing_count,
                    'percentage': (missing_count / len(df)) * 100
                }
        
        # Qualité des données numériques
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            validation_report['data_quality'][col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }
        
        return validation_report
    
    def generate_analysis_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Génère un rapport d'analyse du dataset
        """
        players_df = df[~df['is_team']].copy()
        teams_df = df[df['is_team']].copy()
        
        report = {
            'period_covered': {
                'start_date': df['date'].min() if 'date' in df.columns else 'Unknown',
                'end_date': df['date'].max() if 'date' in df.columns else 'Unknown'
            },
            'players_analysis': {
                'total_players': players_df['player_name'].nunique(),
                'top_scorers': self._get_top_players(players_df, 'points'),
                'top_rebounders': self._get_top_players(players_df, 'rebounds_total'),
                'top_assists': self._get_top_players(players_df, 'assists'),
                'most_efficient': self._get_most_efficient_players(players_df)
            },
            'teams_analysis': {
                'total_teams': teams_df['team_name'].nunique(),
                'highest_scoring_teams': self._get_top_teams(teams_df, 'points'),
                'best_defensive_teams': self._get_top_teams(teams_df, 'steals', 'blocks')
            }
        }
        
        return report
    
    def _get_top_players(self, players_df: pd.DataFrame, stat: str, top_n: int = 5) -> List[Dict]:
        """Retourne les meilleurs joueurs pour une statistique"""
        return players_df.groupby('player_name')[stat].mean().nlargest(top_n).to_dict()
    
    def _get_most_efficient_players(self, players_df: pd.DataFrame, top_n: int = 5) -> List[Dict]:
        """Retourne les joueurs les plus efficaces"""
        players_df['efficiency_score'] = (
            players_df['points'] + 
            players_df['rebounds_total'] + 
            players_df['assists'] + 
            players_df['steals'] + 
            players_df['blocks'] -
            players_df['turnovers'] +
            players_df['plus_minus']
        )
        return players_df.groupby('player_name')['efficiency_score'].mean().nlargest(top_n).to_dict()
    
    def _get_top_teams(self, teams_df: pd.DataFrame, *stats: str, top_n: int = 3) -> List[Dict]:
        """Retourne les meilleures équipes pour des statistiques"""
        result = {}
        for stat in stats:
            result[stat] = teams_df.groupby('team_name')[stat].mean().nlargest(top_n).to_dict()
        return result

# Fonction utilitaire
def process_data_pipeline():
    """Pipeline complet de traitement des données"""
    processor = DataProcessor()
    
    logger.info("🏀 Démarrage du traitement des données LFB...")
    
    # Traitement des données
    df = processor.process_all_matches()
    
    if not df.empty:
        # Validation
        validation_report = processor.validate_dataset(df)
        logger.info(f"✅ Validation: {validation_report['total_rows']} lignes, {validation_report['total_matches']} matchs")
        
        # Rapport d'analyse
        analysis_report = processor.generate_analysis_report(df)
        logger.info("📊 Rapport d'analyse généré")
        
        return df, validation_report, analysis_report
    else:
        logger.error("❌ Échec du traitement des données")
        return pd.DataFrame(), {}, {}

if __name__ == "__main__":
    process_data_pipeline()