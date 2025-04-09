import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO

# The raw GitHub URL for your data
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ashmeetanand13/footy_world/main/df_clean.csv"

def load_data_from_github():
    """
    Load data directly from the GitHub URL
    
    Returns:
        DataFrame or None: The loaded data or None if an error occurs
    """
    try:
        # Show loading status
        with st.spinner("Loading data from GitHub..."):
            # Fetch data from GitHub
            response = requests.get(GITHUB_RAW_URL)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Parse CSV data
            content = StringIO(response.text)
            df = pd.read_csv(content, low_memory=False)
            
            st.success(f"Successfully loaded data with {df.shape[0]} rows and {df.shape[1]} columns")
            return df
    
    except Exception as e:
        st.error(f"Error loading data from GitHub: {str(e)}")
        return None

def process_football_data(df):
    """
    Process the football data to create league-level metrics
    
    Args:
        df: DataFrame containing the football data
        
    Returns:
        tuple: (league_level_df, player_level_df)
    """
    if df is None:
        return None, None
    
    try:
        # Check for required columns
        required_cols = ['Player', 'Competition', 'Squad']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return None, None
        
        # Extract unique leagues
        leagues = df['Competition'].unique()
        
        # Create league-level metrics
        league_metrics = []
        
        for league in leagues:
            league_df = df[df['Competition'] == league]
            
            # Skip if too few players
            if league_df.shape[0] < 10:
                continue
                
            league_data = {
                'League': league
            }
            
            # Attack metrics
            if all(col in df.columns for col in ['Standard Sh', 'Playing Time 90s']):
                # Shots per 90
                league_data['Shots Per 90'] = league_df['Standard Sh'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Shot on target percentage
                if 'Standard SoT' in df.columns:
                    total_shots = league_df['Standard Sh'].sum()
                    if total_shots > 0:
                        league_data['Shot on Target %'] = 100 * league_df['Standard SoT'].sum() / total_shots
                    else:
                        league_data['Shot on Target %'] = 0
                
                # Expected goals per shot
                if 'Expected xG' in df.columns:
                    total_shots = league_df['Standard Sh'].sum()
                    if total_shots > 0:
                        league_data['xG Per Shot'] = league_df['Expected xG'].sum() / total_shots
                    else:
                        league_data['xG Per Shot'] = 0
                
                # Goals per shot
                if 'Performance Gls' in df.columns:
                    total_shots = league_df['Standard Sh'].sum()
                    if total_shots > 0:
                        league_data['Goals Per Shot'] = league_df['Performance Gls'].sum() / total_shots
                    else:
                        league_data['Goals Per Shot'] = 0
            
            # Possession metrics
            if 'Touches Touches' in df.columns:
                # Use 50% as default possession
                league_data['Possession %'] = 50
                
                # Touches in attacking third
                if 'Touches Att 3rd' in df.columns:
                    league_data['Touches in Attacking Third'] = league_df['Touches Att 3rd'].sum() / max(1, league_df.shape[0])
                
                # Progressive carries
                if 'Carries PrgC' in df.columns:
                    league_data['Progressive Carries'] = league_df['Carries PrgC'].sum() / max(1, league_df.shape[0])
            
            # Passing metrics
            if 'Total Cmp%' in df.columns:
                # Pass completion percentage
                valid_players = league_df[league_df['Total Att'] > 0]
                if not valid_players.empty:
                    league_data['Pass Completion %'] = valid_players['Total Cmp%'].mean()
                else:
                    league_data['Pass Completion %'] = 0
                
                # Progressive passes
                if 'PrgP' in df.columns:
                    league_data['Progressive Passes'] = league_df['PrgP'].sum() / max(1, league_df.shape[0])
                
                # Key passes
                if 'KP' in df.columns:
                    league_data['Key Passes'] = league_df['KP'].sum() / max(1, league_df.shape[0])
            
            # Corner metrics
            if 'Pass Types CK' in df.columns:
                # Corners per match
                num_teams = league_df['Squad'].nunique()
                estimated_matches = num_teams * (num_teams - 1) / 2
                
                if estimated_matches > 0:
                    league_data['Corners Per Match'] = league_df['Pass Types CK'].sum() / estimated_matches
                else:
                    league_data['Corners Per Match'] = 5  # Default value
                
                # Corner success rate
                if 'Corner Kicks In' in df.columns:
                    total_corners = league_df['Pass Types CK'].sum()
                    if total_corners > 0:
                        league_data['Corner Success Rate (%)'] = 100 * league_df['Corner Kicks In'].sum() / total_corners
                    else:
                        league_data['Corner Success Rate (%)'] = 0
                
                # Short corner percentage
                if 'Corner Kicks Str' in df.columns:
                    total_corners = league_df['Pass Types CK'].sum()
                    if total_corners > 0:
                        league_data['Short Corner %'] = 100 * league_df['Corner Kicks Str'].sum() / total_corners
                    else:
                        league_data['Short Corner %'] = 0
            
            # Add to metrics list if we have enough data
            if len(league_data) > 5:
                league_metrics.append(league_data)
        
        # Player-level metrics
        player_cols = ['Player', 'Squad', 'Competition', 'Pos']
        
        # Additional metrics columns
        metric_cols = [
            'Performance Gls', 'Performance Ast', 'Standard Sh', 'Expected xG',
            'Touches Touches', 'Carries PrgC', 'Total Cmp%', 'PrgP', 'KP', 'Pass Types CK'
        ]
        
        # Create player dataframe with available columns
        available_cols = player_cols + [col for col in metric_cols if col in df.columns]
        player_df = df[available_cols].copy() if available_cols else pd.DataFrame()
        
        # Create league-level dataframe
        if league_metrics:
            leagues_df = pd.DataFrame(league_metrics)
            
            # Fill missing values with defaults
            default_values = {
                'Shots Per 90': 12,
                'Shot on Target %': 35,
                'xG Per Shot': 0.1,
                'Goals Per Shot': 0.1,
                'Possession %': 50,
                'Touches in Attacking Third': 150,
                'Progressive Carries': 75,
                'Pass Completion %': 80,
                'Progressive Passes': 70,
                'Key Passes': 10,
                'Corners Per Match': 5,
                'Corner Success Rate (%)': 30,
                'Short Corner %': 15
            }
            
            for col, val in default_values.items():
                if col not in leagues_df.columns:
                    leagues_df[col] = val
            
            return leagues_df, player_df
        else:
            st.warning("Could not extract league-level metrics from the data")
            return None, None
    
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return None, None

def load_and_process_data():
    """
    Load and process the football data
    
    Returns:
        tuple: (league_level_df, player_level_df, using_sample_data)
    """
    # Load data from GitHub
    df = load_data_from_github()
    
    if df is not None:
        # Process the data
        leagues_df, players_df = process_football_data(df)
        
        if leagues_df is not None:
            return leagues_df, players_df, False
    
    # If we couldn't load or process the data, use sample data
    return load_sample_data(), True

def load_sample_data():
    """
    Load sample data when GitHub data is not available or fails
    
    Returns:
        tuple: (league_level_df, player_level_df)
    """
    # Define sample leagues
    leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
    
    # Create synthetic league data
    np.random.seed(42)  # For reproducibility
    
    data = []
    for league in leagues:
        data.append({
            "League": league,
            "Shots Per 90": np.random.normal(12.5, 1.5),
            "Shot on Target %": np.random.normal(35, 5),
            "xG Per Shot": np.random.normal(0.1, 0.02),
            "Goals Per Shot": np.random.normal(0.11, 0.02),
            "Possession %": np.random.normal(50, 5),
            "Touches in Attacking Third": np.random.normal(160, 20),
            "Progressive Carries": np.random.normal(75, 10),
            "Pass Completion %": np.random.normal(82, 3),
            "Progressive Passes": np.random.normal(70, 15),
            "Key Passes": np.random.normal(10, 2),
            "Corners Per Match": np.random.normal(5.2, 0.5),
            "Corner Success Rate (%)": np.random.normal(30, 5),
            "Short Corner %": np.random.normal(15, 5),
        })
    
    leagues_df = pd.DataFrame(data)
    
    # Create sample player data
    positions = ['GK', 'DF', 'MF', 'FW']
    player_data = []
    
    for league in leagues:
        for team in range(5):  # 5 teams per league
            team_name = f"Team {team+1} ({league})"
            
            for pos in positions:
                for i in range(3 if pos in ['MF', 'DF'] else 2):
                    player_data.append({
                        'Player': f"Player {i+1} ({pos})",
                        'Squad': team_name,
                        'Competition': league,
                        'Pos': pos,
                        'Performance Gls': np.random.poisson(8 if pos == 'FW' else (3 if pos == 'MF' else 1)),
                        'Performance Ast': np.random.poisson(5 if pos == 'MF' else (3 if pos == 'FW' else 1)),
                        'Total Cmp%': np.random.normal(85 if pos == 'GK' else 80, 5),
                        'PrgP': np.random.poisson(70 if pos == 'MF' else (40 if pos == 'DF' else 20)),
                        'Carries PrgC': np.random.poisson(60 if pos == 'MF' else (30 if pos == 'FW' else 10))
                    })
    
    players_df = pd.DataFrame(player_data)
    
    return leagues_df, players_df
