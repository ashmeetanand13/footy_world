import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile

def load_fbref_data(uploaded_file):
    """
    Process an uploaded fbref CSV file and transform it into the format needed for analysis
    
    Args:
        uploaded_file: The file uploaded through Streamlit's file_uploader
        
    Returns:
        tuple: (league_level_df, player_level_df, success_message)
    """
    try:
        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            # Write content from uploaded file to temp file
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Read the CSV data
        df = pd.read_csv(tmp_path, low_memory=False)
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        # Check if this is valid fbref data by looking for key columns
        required_cols = ['Player', 'Competition', 'Squad']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return None, None, f"Error: Missing required columns: {', '.join(missing_cols)}"
        
        # Extract unique leagues
        leagues = df['Competition'].unique()
        
        # Create league-level metrics
        league_metrics = []
        
        for league in leagues:
            league_df = df[df['Competition'] == league]
            
            # Skip if too few players (likely not a complete league dataset)
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
                # Estimate possession percentage (normally would come from match data)
                all_touches = df['Touches Touches'].sum()
                if all_touches > 0:
                    league_data['Possession %'] = 50  # Default to 50% since we can't calculate actual possession
                else:
                    league_data['Possession %'] = 0
                
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
                # Corners per match (estimate based on average team having ~5 corners per match)
                # Ideally this would use actual match data
                avg_team_corners = 5
                num_teams = league_df['Squad'].nunique()
                estimated_matches = num_teams * (num_teams - 1) / 2  # Number of matches in a round-robin format
                
                if estimated_matches > 0:
                    league_data['Corners Per Match'] = league_df['Pass Types CK'].sum() / estimated_matches
                else:
                    league_data['Corners Per Match'] = avg_team_corners
                
                # Corner success rate (estimate - ideally would use actual goal data)
                if 'Corner Kicks In' in df.columns:
                    total_corners = league_df['Pass Types CK'].sum()
                    if total_corners > 0:
                        # Success rate here is defined as the percentage of corners that are delivered "in"
                        league_data['Corner Success Rate (%)'] = 100 * league_df['Corner Kicks In'].sum() / total_corners
                    else:
                        league_data['Corner Success Rate (%)'] = 0
                
                # Short corner percentage (estimate)
                if 'Corner Kicks Str' in df.columns:
                    total_corners = league_df['Pass Types CK'].sum()
                    if total_corners > 0:
                        league_data['Short Corner %'] = 100 * league_df['Corner Kicks Str'].sum() / total_corners
                    else:
                        league_data['Short Corner %'] = 0
            
            # Add complete data to our league metrics list
            if len(league_data) > 5:  # Only add if we have sufficient metrics
                league_metrics.append(league_data)
        
        # Create player-level metrics for position-based analysis
        player_cols = ['Player', 'Squad', 'Competition', 'Pos']
        
        # Add available metric columns
        metric_cols = [
            'Performance Gls', 'Performance Ast', 'Standard Sh', 'Expected xG',
            'Touches Touches', 'Carries PrgC', 'Total Cmp%', 'PrgP', 'KP', 'Pass Types CK'
        ]
        
        available_cols = player_cols + [col for col in metric_cols if col in df.columns]
        player_df = df[available_cols].copy() if available_cols else pd.DataFrame()
        
        # Create league-level dataframe
        if league_metrics:
            leagues_df = pd.DataFrame(league_metrics)
            
            # Fill missing values with reasonable defaults
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
            
            return leagues_df, player_df, f"Successfully loaded data for {len(leagues)} leagues"
        else:
            return None, None, "Could not extract sufficient league-level metrics from the data"
    
    except Exception as e:
        return None, None, f"Error processing file: {str(e)}"

def load_sample_data():
    """
    Load sample data when no file is uploaded
    
    Returns:
        tuple: (league_level_df, player_level_df)
    """
    # Define leagues
    leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1", "Brazilian Serie A"]
    
    # Create a synthetic dataframe with league-level metrics
    np.random.seed(42)  # For reproducibility
    
    data = []
    for league in leagues:
        # Attack metrics
        shots_per90 = np.random.normal(12.5, 1.5)
        shot_on_target_pct = np.random.normal(35, 5)
        xg_per_shot = np.random.normal(0.1, 0.02)
        goals_per_shot = np.random.normal(0.11, 0.02)
        
        # Possession metrics
        possession_pct = np.random.normal(50, 5)
        touches_att_third = np.random.normal(160, 20)
        progressive_carries = np.random.normal(75, 10)
        
        # Passing metrics
        pass_completion = np.random.normal(82, 3)
        progressive_passes = np.random.normal(70, 15)
        key_passes = np.random.normal(10, 2)
        
        # Corner metrics
        corners_per_match = np.random.normal(5.2, 0.5)
        corner_success_rate = np.random.normal(3, 0.8)
        short_corner_pct = np.random.normal(15, 5)
        
        data.append({
            "League": league,
            
            # Attack metrics
            "Shots Per 90": shots_per90,
            "Shot on Target %": shot_on_target_pct,
            "xG Per Shot": xg_per_shot,
            "Goals Per Shot": goals_per_shot,
            
            # Possession metrics
            "Possession %": possession_pct,
            "Touches in Attacking Third": touches_att_third,
            "Progressive Carries": progressive_carries,
            
            # Passing metrics
            "Pass Completion %": pass_completion,
            "Progressive Passes": progressive_passes,
            "Key Passes": key_passes,
            
            # Corner metrics
            "Corners Per Match": corners_per_match,
            "Corner Success Rate (%)": corner_success_rate,
            "Short Corner %": short_corner_pct,
        })
    
    leagues_df = pd.DataFrame(data)
    
    # Create sample player data
    positions = ['GK', 'DF', 'MF', 'FW']
    player_data = []
    
    for league in leagues:
        for team in range(5):  # 5 teams per league for the sample
            team_name = f"Team {team+1} ({league})"
            
            for pos in positions:
                for i in range(3 if pos in ['MF', 'DF'] else 2):  # More midfielders and defenders
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

def data_loader_ui():
    """
    UI component for data loading in the Streamlit app
    
    Returns:
        tuple: (league_level_df, player_level_df, using_sample_data)
    """
    st.sidebar.markdown("## Data Upload")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload your FBref data (CSV format)",
        type=['csv']
    )
    
    if uploaded_file is not None:
        # Use a standard spinner instead of the sidebar spinner
        with st.spinner("Processing data..."):
            league_df, player_df, message = load_fbref_data(uploaded_file)
            
            if league_df is not None:
                st.sidebar.success(message)
                return league_df, player_df, False
            else:
                st.sidebar.error(message)
                st.sidebar.info("Using sample data instead")
                return load_sample_data(), True
    else:
        st.sidebar.info("No file uploaded. Using sample data.")
        return load_sample_data(), True