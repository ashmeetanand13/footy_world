import pandas as pd
import numpy as np
import os

def process_raw_data(file_path):
    """
    Process the raw fbref data file and convert it to a format suitable for the analyzer app.
    
    Args:
        file_path (str): Path to the raw data file
        
    Returns:
        pd.DataFrame: Processed data ready for analysis
    """
    print(f"Processing file: {file_path}")
    
    # Read the data
    df = pd.read_csv(file_path, low_memory=False)
    
    # Check the loaded data shape
    print(f"Loaded data shape: {df.shape}")
    print(f"Columns: {', '.join(df.columns[:10])}...")
    
    # Basic cleaning
    # Replace NaN values with 0 for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Extract the league information
    # Assuming 'Competition' column contains league information
    if 'Competition' in df.columns:
        print(f"Leagues in data: {df['Competition'].unique()}")
    
    # Extract key metrics for our analysis categories
    
    # 1. Attack metrics
    attack_metrics = [
        'Player', 'Squad', 'Competition', 'Pos',
        'Performance Gls', 'Standard Sh', 'Standard SoT', 'Standard SoT%',
        'Expected xG', 'Expected xG/Sh', 'Standard G/Sh', 'Standard G/SoT',
        'Per 90 Minutes Gls', 'Per 90 Minutes Sh/90', 'Per 90 Minutes SoT/90'
    ]
    
    # 2. Possession metrics
    possession_metrics = [
        'Player', 'Squad', 'Competition', 'Pos',
        'Touches Touches', 'Touches Def 3rd', 'Touches Mid 3rd', 'Touches Att 3rd', 
        'Touches Att Pen', 'Carries Carries', 'Carries TotDist', 'Carries PrgDist',
        'Carries PrgC', 'Carries 1/3', 'Take-Ons Att', 'Take-Ons Succ', 'Take-Ons Succ%'
    ]
    
    # 3. Passing metrics
    passing_metrics = [
        'Player', 'Squad', 'Competition', 'Pos',
        'Total Att', 'Total Cmp', 'Total Cmp%', 
        'Short Att', 'Short Cmp', 'Short Cmp%',
        'Medium Att', 'Medium Cmp', 'Medium Cmp%',
        'Long Att', 'Long Cmp', 'Long Cmp%',
        'PrgP', 'KP', 'Pass Types TB', 'Pass Types Sw', 'Pass Types Crs'
    ]
    
    # 4. Corner metrics
    corner_metrics = [
        'Player', 'Squad', 'Competition', 'Pos',
        'Pass Types CK', 'Corner Kicks In', 'Corner Kicks Out', 'Corner Kicks Str'
    ]
    
    # Check which columns are actually in the dataframe
    def check_columns(metric_list):
        return [col for col in metric_list if col in df.columns]
    
    available_attack = check_columns(attack_metrics)
    available_possession = check_columns(possession_metrics)
    available_passing = check_columns(passing_metrics)
    available_corner = check_columns(corner_metrics)
    
    print(f"Available attack metrics: {len(available_attack)}/{len(attack_metrics)}")
    print(f"Available possession metrics: {len(available_possession)}/{len(possession_metrics)}")
    print(f"Available passing metrics: {len(available_passing)}/{len(passing_metrics)}")
    print(f"Available corner metrics: {len(available_corner)}/{len(corner_metrics)}")
    
    # Create subsets for each category
    attack_df = df[available_attack].copy() if available_attack else pd.DataFrame()
    possession_df = df[available_possession].copy() if available_possession else pd.DataFrame()
    passing_df = df[available_passing].copy() if available_passing else pd.DataFrame()
    corner_df = df[available_corner].copy() if available_corner else pd.DataFrame()
    
    # Aggregate data to league level (for the main analysis)
    leagues = []
    
    # Common identification columns for joining
    id_cols = ['Player', 'Squad', 'Competition', 'Pos']
    available_id_cols = [col for col in id_cols if col in df.columns]
    
    if 'Competition' in df.columns:
        for league in df['Competition'].unique():
            league_data = {
                'League': league
            }
            
            # Calculate attack metrics
            if not attack_df.empty:
                league_players = attack_df[attack_df['Competition'] == league]
                
                if not league_players.empty:
                    # Avoid division by zero by using .mean() on non-empty filtered frames
                    league_data['Shots Per 90'] = league_players['Standard Sh'].sum() / league_players['Playing Time 90s'].sum() if 'Playing Time 90s' in league_players.columns else np.nan
                    
                    valid_shots = league_players[league_players['Standard Sh'] > 0]
                    if not valid_shots.empty and 'Standard SoT' in valid_shots.columns:
                        league_data['Shot on Target %'] = 100 * valid_shots['Standard SoT'].sum() / valid_shots['Standard Sh'].sum()
                    
                    if 'Expected xG' in league_players.columns and 'Standard Sh' in league_players.columns:
                        valid_xg = league_players[(league_players['Expected xG'] > 0) & (league_players['Standard Sh'] > 0)]
                        if not valid_xg.empty:
                            league_data['xG Per Shot'] = valid_xg['Expected xG'].sum() / valid_xg['Standard Sh'].sum()
                    
                    if 'Performance Gls' in league_players.columns and 'Standard Sh' in league_players.columns:
                        valid_goals = league_players[(league_players['Performance Gls'] > 0) & (league_players['Standard Sh'] > 0)]
                        if not valid_goals.empty:
                            league_data['Goals Per Shot'] = valid_goals['Performance Gls'].sum() / valid_goals['Standard Sh'].sum()
            
            # Calculate possession metrics
            if not possession_df.empty:
                league_players = possession_df[possession_df['Competition'] == league]
                
                if not league_players.empty and 'Touches Touches' in league_players.columns:
                    # This is a placeholder calculation - real possession % would come from match data
                    all_touches = df['Touches Touches'].sum() if 'Touches Touches' in df.columns else 1
                    league_data['Possession %'] = 100 * league_players['Touches Touches'].sum() / all_touches
                    
                    if 'Touches Att 3rd' in league_players.columns:
                        league_data['Touches in Attacking Third'] = league_players['Touches Att 3rd'].sum() / league_players.shape[0]
                    
                    if 'Carries PrgC' in league_players.columns:
                        league_data['Progressive Carries'] = league_players['Carries PrgC'].sum() / league_players.shape[0]
            
            # Calculate passing metrics
            if not passing_df.empty:
                league_players = passing_df[passing_df['Competition'] == league]
                
                if not league_players.empty:
                    if 'Total Cmp%' in league_players.columns:
                        valid_pass_pct = league_players[league_players['Total Cmp%'] > 0]
                        if not valid_pass_pct.empty:
                            league_data['Pass Completion %'] = valid_pass_pct['Total Cmp%'].mean()
                    
                    if 'PrgP' in league_players.columns:
                        league_data['Progressive Passes'] = league_players['PrgP'].sum() / league_players.shape[0]
                    
                    if 'KP' in league_players.columns:
                        league_data['Key Passes'] = league_players['KP'].sum() / league_players.shape[0]
            
            # Calculate corner metrics
            if not corner_df.empty:
                league_players = corner_df[corner_df['Competition'] == league]
                
                if not league_players.empty and 'Pass Types CK' in league_players.columns:
                    total_matches = league_players['Matches'].nunique() if 'Matches' in league_players.columns else (league_players.shape[0] / 20)  # Estimate if matches not available
                    league_data['Corners Per Match'] = league_players['Pass Types CK'].sum() / total_matches
                    
                    # Estimate success rate (normally would use actual goal data from corners)
                    if 'Corner Kicks In' in league_players.columns and 'Pass Types CK' in league_players.columns:
                        valid_corners = league_players[league_players['Pass Types CK'] > 0]
                        if not valid_corners.empty:
                            league_data['Corner Success Rate (%)'] = 100 * valid_corners['Corner Kicks In'].sum() / valid_corners['Pass Types CK'].sum()
                    
                    # Estimate short corner percentage (normally would use actual play-by-play data)
                    if 'Corner Kicks Str' in league_players.columns and 'Pass Types CK' in league_players.columns:
                        valid_corners = league_players[league_players['Pass Types CK'] > 0]
                        if not valid_corners.empty:
                            league_data['Short Corner %'] = 100 * valid_corners['Corner Kicks Str'].sum() / valid_corners['Pass Types CK'].sum()
            
            # Only add complete league data rows
            if len(league_data) > 1:  # More than just the league name
                leagues.append(league_data)
    
    # Create the league-level dataframe
    if leagues:
        leagues_df = pd.DataFrame(leagues)
        print(f"Created league summary with {len(leagues)} leagues")
        return leagues_df
    else:
        print("Warning: No league data could be extracted")
        return pd.DataFrame()

def get_player_aggregates(file_path):
    """
    Extract player-level aggregates for detailed position-based analysis
    
    Args:
        file_path (str): Path to the raw data file
        
    Returns:
        pd.DataFrame: Player-level aggregated data
    """
    # Read the data
    df = pd.read_csv(file_path, low_memory=False)
    
    # Required columns for analysis
    required_cols = ['Player', 'Squad', 'Competition', 'Pos', 'Playing Time 90s']
    available_cols = [col for col in required_cols if col in df.columns]
    
    if len(available_cols) < 3:  # Need at least player, team, and league
        print("Not enough identification columns available for player analysis")
        return pd.DataFrame()
    
    # Extract key player metrics
    player_metrics = [
        # Attack metrics
        'Performance Gls', 'Performance Ast', 'Standard Sh', 'Standard SoT', 'Expected xG',
        
        # Possession metrics
        'Touches Touches', 'Carries Carries', 'Carries PrgC', 'Take-Ons Succ', 
        
        # Passing metrics
        'Total Att', 'Total Cmp', 'Total Cmp%', 'PrgP', 'KP',
        
        # Corner metrics
        'Pass Types CK', 'Corner Kicks In'
    ]
    
    # Check which columns are available
    available_metrics = [col for col in player_metrics if col in df.columns]
    print(f"Available player metrics: {len(available_metrics)}/{len(player_metrics)}")
    
    # If too few metrics available, return empty dataframe
    if len(available_metrics) < 5:
        print("Not enough metrics available for meaningful player analysis")
        return pd.DataFrame()
    
    # Create player dataframe with available columns
    player_cols = available_cols + available_metrics
    player_df = df[player_cols].copy()
    
    # Replace NaN values with zeros
    player_df = player_df.fillna(0)
    
    # Remove players with too little playing time (e.g., less than 450 minutes / 5 full matches)
    if 'Playing Time 90s' in player_df.columns:
        player_df = player_df[player_df['Playing Time 90s'] >= 5]
    
    print(f"Player dataset created with {player_df.shape[0]} qualifying players")
    return player_df

def process_data_for_app(file_path):
    """
    Process data for the Streamlit app
    
    Args:
        file_path (str): Path to the raw data file
        
    Returns:
        tuple: (league_level_df, player_level_df)
    """
    leagues_df = process_raw_data(file_path)
    players_df = get_player_aggregates(file_path)
    
    return leagues_df, players_df

if __name__ == "__main__":
    # Example usage
    file_path = "football_data.csv"
    
    if os.path.exists(file_path):
        leagues_df, players_df = process_data_for_app(file_path)
        
        if not leagues_df.empty:
            leagues_df.to_csv("league_analysis.csv", index=False)
            print(f"Saved league analysis to league_analysis.csv")
        
        if not players_df.empty:
            players_df.to_csv("player_analysis.csv", index=False)
            print(f"Saved player analysis to player_analysis.csv")
    else:
        print(f"File {file_path} not found. Please specify the correct path to your data file.")