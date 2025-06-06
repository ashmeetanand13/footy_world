import pandas as pd
import numpy as np
import streamlit as st
import requests
from io import StringIO

# The raw GitHub URL for your data
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ashmeetanand13/footy_world/main/df_clean.csv"

def load_data():
    """
    Load football data directly from GitHub
    
    Returns:
        DataFrame: Player-level data
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
            
            # Basic data cleaning
            if 'Rk' in df.columns:
                df = df.drop('Rk', axis=1)
            
            st.success(f"Successfully loaded data with {df.shape[0]} rows and {df.shape[1]} columns")
            return df
    
    except Exception as e:
        st.error(f"Error loading data from GitHub: {str(e)}")
        return None

def load_sample_data():
    """
    Create sample data if real data cannot be loaded
    
    Returns:
        DataFrame, DataFrame: Sample league and player data
    """
    # Create sample teams data
    teams_data = []
    
    # Generate data for major leagues
    leagues = ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1']
    
    for league in leagues:
        # Generate team names based on league
        if league == 'Premier League':
            teams = ['Manchester City', 'Liverpool', 'Chelsea', 'Arsenal', 'Tottenham', 
                     'Manchester United', 'Newcastle', 'West Ham', 'Leicester', 'Brighton']
        elif league == 'La Liga':
            teams = ['Real Madrid', 'Barcelona', 'Atletico Madrid', 'Sevilla', 'Real Betis',
                     'Real Sociedad', 'Villarreal', 'Athletic Bilbao', 'Valencia', 'Osasuna']
        elif league == 'Bundesliga':
            teams = ['Bayern Munich', 'Borussia Dortmund', 'Bayer Leverkusen', 'RB Leipzig', 
                     'Union Berlin', 'Freiburg', 'Cologne', 'Mainz', 'Hoffenheim', 'Borussia Monchengladbach']
        elif league == 'Serie A':
            teams = ['AC Milan', 'Inter Milan', 'Napoli', 'Juventus', 'Lazio', 
                     'Roma', 'Fiorentina', 'Atalanta', 'Verona', 'Torino']
        else:  # Ligue 1
            teams = ['PSG', 'Marseille', 'Monaco', 'Rennes', 'Nice', 
                     'Strasbourg', 'Lens', 'Lyon', 'Nantes', 'Lille']
        
        # Generate data for each team
        for team in teams:
            # Base metrics with randomization
            goals = np.random.randint(40, 100)
            shots = np.random.randint(400, 700)
            shots_on_target = np.random.randint(int(shots * 0.3), int(shots * 0.5))
            touches = np.random.randint(15000, 25000)
            passes = np.random.randint(10000, 18000)
            tackles = np.random.randint(400, 700)
            interceptions = np.random.randint(300, 600)
            blocks = np.random.randint(200, 400)
            
            # Calculate derived metrics
            played_90s = 38 * 11  # Approx. for a full season of starters
            
            team_data = {
                'Squad': team,
                'Competition': league,
                'Season': '2022-23',
                
                # Attack metrics
                'Goals': goals,
                'Goals Per 90': goals / played_90s,
                'Shots': shots,
                'Shots Per 90': shots / played_90s,
                'Shot on Target %': 100 * shots_on_target / shots,
                'Goals Per Shot': goals / shots,
                'xG': goals * (0.9 + np.random.random() * 0.2),  # Randomize around goals
                'xG Per 90': (goals * (0.9 + np.random.random() * 0.2)) / played_90s,
                'G-xG': goals - (goals * (0.9 + np.random.random() * 0.2)),
                'Key Passes': np.random.randint(300, 500),
                'Key Passes Per 90': np.random.randint(300, 500) / played_90s,
                
                # Possession metrics
                'Touches': touches,
                'Touches Per 90': touches / played_90s,
                'Progressive Carries': np.random.randint(800, 1200),
                'Progressive Carries Per 90': np.random.randint(800, 1200) / played_90s,
                'Progressive Passes': np.random.randint(800, 1200),
                'Progressive Passes Per 90': np.random.randint(800, 1200) / played_90s,
                'Attacking Third Touches %': np.random.randint(20, 40),
                'Box Touches %': np.random.randint(5, 15),
                'Pass Completion %': np.random.randint(75, 90),
                
                # Defense metrics
                'Tackles': tackles,
                'Tackles Per 90': tackles / played_90s,
                'Interceptions': interceptions,
                'Interceptions Per 90': interceptions / played_90s,
                'Tackles + Interceptions': tackles + interceptions,
                'Tackles + Interceptions Per 90': (tackles + interceptions) / played_90s,
                'Blocks': blocks,
                'Blocks Per 90': blocks / played_90s,
                'Clearances': np.random.randint(500, 800),
                'Clearances Per 90': np.random.randint(500, 800) / played_90s,
                'Errors': np.random.randint(10, 30),
                'Errors Per 90': np.random.randint(10, 30) / played_90s,
            }
            
            teams_data.append(team_data)
    
    # Create DataFrame from the sample data
    teams_df = pd.DataFrame(teams_data)
    
    # Normalize metrics within each competition
    normalized_teams_df = normalize_sample_metrics(teams_df)
    
    return normalized_teams_df

def normalize_sample_metrics(teams_df):
    """
    Normalize sample team metrics within each competition
    
    Args:
        teams_df: DataFrame with team metrics
        
    Returns:
        DataFrame: Teams with normalized metrics
    """
    # Create a copy of the DataFrame
    normalized_df = teams_df.copy()
    
    # List of metrics to normalize
    # Exclude identification columns like 'Squad', 'Competition', 'Season'
    # Also exclude percentage metrics which are already normalized
    exclude_cols = ['Squad', 'Competition', 'Season', 'Shot on Target %', 'Attacking Third Touches %', 'Box Touches %', 'Pass Completion %']
    invert_cols = ['Errors', 'Errors Per 90']  # Lower is better for these
    
    # Get all numeric columns
    numeric_cols = normalized_df.select_dtypes(include=['number']).columns
    metrics_to_normalize = [col for col in numeric_cols if col not in exclude_cols]
    
    # Normalize metrics within each competition
    for competition in normalized_df['Competition'].unique():
        comp_mask = normalized_df['Competition'] == competition
        
        for col in metrics_to_normalize:
            col_min = normalized_df.loc[comp_mask, col].min()
            col_max = normalized_df.loc[comp_mask, col].max()
            
            # Skip if min equals max (no variation)
            if col_max > col_min:
                if col in invert_cols:
                    # For metrics where lower is better
                    normalized_df.loc[comp_mask, f'Normalized {col}'] = 1 - (normalized_df.loc[comp_mask, col] - col_min) / (col_max - col_min)
                else:
                    # For metrics where higher is better
                    normalized_df.loc[comp_mask, f'Normalized {col}'] = (normalized_df.loc[comp_mask, col] - col_min) / (col_max - col_min)
            else:
                # If all values are the same, set normalized value to 0.5
                normalized_df.loc[comp_mask, f'Normalized {col}'] = 0.5
    
    # For percentage metrics, divide by 100 to get 0-1 scale
    for col in ['Shot on Target %', 'Attacking Third Touches %', 'Box Touches %', 'Pass Completion %']:
        if col in normalized_df.columns:
            normalized_df[f'Normalized {col}'] = normalized_df[col] / 100
    
    return normalized_df

def load_and_process_data():
    """
    Load and process the football data
    
    Returns:
        DataFrame: Processed team-level data with normalized metrics
    """
    # Try to load real data
    df = load_data()
    
    if df is not None:
        # Process data here if needed
        st.success("Successfully loaded real data")
        return df
    else:
        # If real data loading fails, use sample data
        st.warning("Using sample data because real data could not be loaded")
        return load_sample_data()
