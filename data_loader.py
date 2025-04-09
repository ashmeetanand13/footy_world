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

            #---------------------------------------------------------------------
            # 1. ATTACK METRICS
            #---------------------------------------------------------------------
            if all(col in df.columns for col in ['Standard Sh', 'Playing Time 90s']):
                # Basic shot metrics
                league_data['Shots Per 90'] = league_df['Standard Sh'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Shot on target percentage
                if 'Standard SoT' in df.columns:
                    total_shots = league_df['Standard Sh'].sum()
                    if total_shots > 0:
                        league_data['Shot on Target %'] = 100 * league_df['Standard SoT'].sum() / total_shots
                    else:
                        league_data['Shot on Target %'] = 0
                
                # Expected goals metrics
                if 'Expected xG' in df.columns:
                    total_shots = league_df['Standard Sh'].sum()
                    if total_shots > 0:
                        league_data['xG Per Shot'] = league_df['Expected xG'].sum() / total_shots
                    else:
                        league_data['xG Per Shot'] = 0
                
                # Shooting efficiency 
                if 'Performance Gls' in df.columns:
                    total_shots = league_df['Standard Sh'].sum()
                    if total_shots > 0:
                        league_data['Goals Per Shot'] = league_df['Performance Gls'].sum() / total_shots
                        league_data['Conversion Rate'] = 100 * league_df['Performance Gls'].sum() / total_shots
                    else:
                        league_data['Goals Per Shot'] = 0
                        league_data['Conversion Rate'] = 0
                
                # Goals per shots on target
                if all(col in df.columns for col in ['Performance Gls', 'Standard SoT']):
                    total_shots_on_target = league_df['Standard SoT'].sum()
                    if total_shots_on_target > 0:
                        league_data['Goals per SoT'] = league_df['Performance Gls'].sum() / total_shots_on_target
                    else:
                        league_data['Goals per SoT'] = 0
                
                # Finishing quality (G-xG)
                if all(col in df.columns for col in ['Performance Gls', 'Expected xG']):
                    league_data['G-xG'] = league_df['Performance Gls'].sum() - league_df['Expected xG'].sum()
                
                # Non-penalty attack metrics
                if all(col in df.columns for col in ['Performance G-PK', 'Expected npxG']):
                    league_data['Non-Penalty Goals'] = league_df['Performance G-PK'].sum()
                    league_data['Non-Penalty xG'] = league_df['Expected npxG'].sum()
                    # G-PK per 90
                    if 'Playing Time 90s' in df.columns:
                        league_data['Non-Penalty Goals Per 90'] = league_df['Performance G-PK'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Penalty metrics
                if all(col in df.columns for col in ['Performance PK', 'Standard PKatt']):
                    pk_attempts = league_df['Standard PKatt'].sum()
                    if pk_attempts > 0:
                        league_data['Penalty Conversion %'] = 100 * league_df['Performance PK'].sum() / pk_attempts
                    else:
                        league_data['Penalty Conversion %'] = 0
            
            # Goal creation metrics
            if all(col in df.columns for col in ['GCA GCA', 'Playing Time 90s']):
                league_data['GCA Per 90'] = league_df['GCA GCA'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # GCA types breakdown
                gca_types = ['GCA Types PassLive', 'GCA Types PassDead', 'GCA Types TO', 'GCA Types Sh', 'GCA Types Fld', 'GCA Types Def']
                for gca_type in gca_types:
                    if gca_type in df.columns:
                        total_gca = league_df['GCA GCA'].sum()
                        if total_gca > 0:
                            type_name = gca_type.replace('GCA Types ', '')
                            league_data[f'GCA {type_name} %'] = 100 * league_df[gca_type].sum() / total_gca
            
            # Threat distribution
            if all(col in df.columns for col in ['Touches Att Pen', 'Touches Touches']):
                touches = league_df['Touches Touches'].sum()
                if touches > 0:
                    league_data['Box Touches %'] = 100 * league_df['Touches Att Pen'].sum() / touches
            
            if 'Carries CPA' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Carries into Box Per 90'] = league_df['Carries CPA'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            if 'PPA' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Passes into Box Per 90'] = league_df['PPA'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            #---------------------------------------------------------------------
            # 2. DEFENSIVE METRICS
            #---------------------------------------------------------------------
            # Ball recovery
            if 'Tackles Tkl' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Tackles Per 90'] = league_df['Tackles Tkl'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Tackle success rate
                if 'Tackles TklW' in df.columns:
                    total_tackles = league_df['Tackles Tkl'].sum()
                    if total_tackles > 0:
                        league_data['Tackle Success %'] = 100 * league_df['Tackles TklW'].sum() / total_tackles
                    else:
                        league_data['Tackle Success %'] = 0
            
            # Interceptions
            if 'Int' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Interceptions Per 90'] = league_df['Int'].sum() / max(1, league_df['Playing Time 90s'].sum())
                # Combined tackles and interceptions
                if 'Tackles Tkl' in df.columns:
                    league_data['Tackles+Interceptions Per 90'] = (league_df['Tackles Tkl'].sum() + league_df['Int'].sum()) / max(1, league_df['Playing Time 90s'].sum())
            
            # Blocks
            if 'Blocks Blocks' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Blocks Per 90'] = league_df['Blocks Blocks'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Block types
                if 'Blocks Sh' in df.columns and 'Blocks Pass' in df.columns:
                    total_blocks = league_df['Blocks Blocks'].sum()
                    if total_blocks > 0:
                        league_data['Shot Blocks %'] = 100 * league_df['Blocks Sh'].sum() / total_blocks
                        league_data['Pass Blocks %'] = 100 * league_df['Blocks Pass'].sum() / total_blocks
            
            # Clearances
            if 'Clr' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Clearances Per 90'] = league_df['Clr'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            # Errors
            if 'Err' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Errors Per 90'] = league_df['Err'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            # Defensive positioning
            tackle_zones = ['Tackles Def 3rd', 'Tackles Mid 3rd', 'Tackles Att 3rd']
            if all(zone in df.columns for zone in tackle_zones):
                total_tackles = league_df[tackle_zones].sum().sum()
                if total_tackles > 0:
                    for zone in tackle_zones:
                        zone_name = zone.replace('Tackles ', '')
                        league_data[f'{zone_name} Tackles %'] = 100 * league_df[zone].sum() / total_tackles
            
            # Aerial dominance
            if all(col in df.columns for col in ['Aerial Duels Won', 'Aerial Duels Lost']):
                aerial_total = league_df['Aerial Duels Won'].sum() + league_df['Aerial Duels Lost'].sum()
                if aerial_total > 0:
                    league_data['Aerial Duels Won %'] = 100 * league_df['Aerial Duels Won'].sum() / aerial_total
            
            # Pressure metrics
            if 'Pressure Succ%' in df.columns:
                valid_pressure = league_df[league_df['Pressure Press'] > 0]
                if not valid_pressure.empty:
                    league_data['Pressure Success %'] = valid_pressure['Pressure Succ%'].mean()
                else:
                    league_data['Pressure Success %'] = 0
            
            # Recoveries
            if 'Performance Recov' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['Recoveries Per 90'] = league_df['Performance Recov'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            #---------------------------------------------------------------------
            # 3. POSSESSION METRICS
            #---------------------------------------------------------------------
            if 'Touches Touches' in df.columns:
                # Total touches per 90
                if 'Playing Time 90s' in df.columns:
                    league_data['Touches Per 90'] = league_df['Touches Touches'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Touch distribution percentages
                touch_zones = ['Touches Def 3rd', 'Touches Mid 3rd', 'Touches Att 3rd', 'Touches Att Pen', 'Touches Def Pen']
                total_touches = league_df['Touches Touches'].sum()
                
                if total_touches > 0:
                    for zone in touch_zones:
                        if zone in df.columns:
                            zone_name = zone.replace('Touches ', '')
                            league_data[f'{zone_name} Touch %'] = 100 * league_df[zone].sum() / total_touches
                
                # Use 50% as default possession
                league_data['Possession %'] = 50
                
                # Progressive carries
                if 'Carries PrgC' in df.columns:
                    if 'Playing Time 90s' in df.columns:
                        league_data['Progressive Carries Per 90'] = league_df['Carries PrgC'].sum() / max(1, league_df['Playing Time 90s'].sum())
                    
                    if 'Carries Carries' in df.columns:
                        total_carries = league_df['Carries Carries'].sum()
                        if total_carries > 0:
                            league_data['Progressive Carry %'] = 100 * league_df['Carries PrgC'].sum() / total_carries
                
                # Carries into dangerous areas
                if 'Carries 1/3' in df.columns and 'Playing Time 90s' in df.columns:
                    league_data['Carries into Final Third Per 90'] = league_df['Carries 1/3'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                if 'Carries CPA' in df.columns and 'Playing Time 90s' in df.columns:
                    league_data['Carries into Box Per 90'] = league_df['Carries CPA'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Progressive passes received
                if 'Receiving PrgR' in df.columns and 'Playing Time 90s' in df.columns:
                    league_data['Progressive Passes Received Per 90'] = league_df['Receiving PrgR'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            # Ball retention
            if all(col in df.columns for col in ['Carries Mis', 'Carries Dis', 'Carries Carries']):
                total_carries = league_df['Carries Carries'].sum()
                if total_carries > 0:
                    miscontrols = league_df['Carries Mis'].sum()
                    dispossessed = league_df['Carries Dis'].sum()
                    league_data['Miscontrols per 100 Touches'] = 100 * miscontrols / total_carries
                    league_data['Dispossessed per 100 Touches'] = 100 * dispossessed / total_carries
                    league_data['Carry Success %'] = 100 * (total_carries - miscontrols - dispossessed) / total_carries
            
            # Take-on metrics
            if all(col in df.columns for col in ['Take-Ons Succ', 'Take-Ons Att']):
                take_on_attempts = league_df['Take-Ons Att'].sum()
                if take_on_attempts > 0:
                    league_data['Take-On Success %'] = 100 * league_df['Take-Ons Succ'].sum() / take_on_attempts
                    
                    if 'Playing Time 90s' in df.columns:
                        league_data['Take-Ons Per 90'] = league_df['Take-Ons Att'].sum() / max(1, league_df['Playing Time 90s'].sum())
                        league_data['Successful Take-Ons Per 90'] = league_df['Take-Ons Succ'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            #---------------------------------------------------------------------
            # 4. PASSING METRICS
            #---------------------------------------------------------------------
            # Pass completion by distance
            pass_types = [
                ('Short Cmp', 'Short Att', 'Short Pass'),
                ('Medium Cmp', 'Medium Att', 'Medium Pass'),
                ('Long Cmp', 'Long Att', 'Long Pass')
            ]
            
            for cmp_col, att_col, name in pass_types:
                if all(col in df.columns for col in [cmp_col, att_col]):
                    attempts = league_df[att_col].sum()
                    if attempts > 0:
                        league_data[f'{name} Completion %'] = 100 * league_df[cmp_col].sum() / attempts
                    else:
                        league_data[f'{name} Completion %'] = 0
            
            # Overall pass completion
            if 'Total Cmp%' in df.columns:
                valid_players = league_df[league_df['Total Att'] > 0]
                if not valid_players.empty:
                    league_data['Pass Completion %'] = valid_players['Total Cmp%'].mean()
                else:
                    league_data['Pass Completion %'] = 0
            
            # Average pass distance
            if all(col in df.columns for col in ['Total TotDist', 'Total Att']):
                total_passes = league_df['Total Att'].sum()
                if total_passes > 0:
                    league_data['Avg Pass Distance'] = league_df['Total TotDist'].sum() / total_passes
            
            # Progressive passing
            if 'PrgP' in df.columns:
                if 'Playing Time 90s' in df.columns:
                    league_data['Progressive Passes Per 90'] = league_df['PrgP'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                if 'Total Att' in df.columns:
                    total_passes = league_df['Total Att'].sum()
                    if total_passes > 0:
                        league_data['Progressive Pass Ratio'] = 100 * league_df['PrgP'].sum() / total_passes
            
            # Pass progression distance
            if all(col in df.columns for col in ['Total PrgDist', 'Playing Time 90s']):
                league_data['Progressive Pass Distance Per 90'] = league_df['Total PrgDist'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            # Chance creation
            if 'KP' in df.columns:
                if 'Playing Time 90s' in df.columns:
                    league_data['Key Passes Per 90'] = league_df['KP'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                if 'Total Att' in df.columns:
                    total_passes = league_df['Total Att'].sum()
                    if total_passes > 0:
                        league_data['Key Pass %'] = 100 * league_df['KP'].sum() / total_passes
            
            # Expected assists
            if 'Expected xA' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['xA Per 90'] = league_df['Expected xA'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # Assist efficiency
                if 'Ast' in df.columns and 'KP' in df.columns:
                    key_passes = league_df['KP'].sum()
                    if key_passes > 0:
                        league_data['Assist Rate'] = 100 * league_df['Ast'].sum() / key_passes
                        league_data['xA per Key Pass'] = league_df['Expected xA'].sum() / key_passes
            
            # Assist vs expected assist quality
            if all(col in df.columns for col in ['Ast', 'Expected xA']):
                league_data['A-xA'] = league_df['Ast'].sum() - league_df['Expected xA'].sum()
            
            # Expected assisted goals
            if 'xAG' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['xAG Per 90'] = league_df['xAG'].sum() / max(1, league_df['Playing Time 90s'].sum())
            
            # Shot creating actions
            if 'SCA SCA' in df.columns and 'Playing Time 90s' in df.columns:
                league_data['SCA Per 90'] = league_df['SCA SCA'].sum() / max(1, league_df['Playing Time 90s'].sum())
                
                # SCA types breakdown
                sca_types = ['SCA Types PassLive', 'SCA Types PassDead', 'SCA Types TO', 'SCA Types Sh', 'SCA Types Fld', 'SCA Types Def']
                for sca_type in sca_types:
                    if sca_type in df.columns:
                        total_sca = league_df['SCA SCA'].sum()
                        if total_sca > 0:
                            type_name = sca_type.replace('SCA Types ', '')
                            league_data[f'SCA {type_name} %'] = 100 * league_df[sca_type].sum() / total_sca
            
            #---------------------------------------------------------------------
            # 5. CORNER METRICS
            #---------------------------------------------------------------------
            if 'Pass Types CK' in df.columns:
                # Corners per match
                num_teams = league_df['Squad'].nunique()
                estimated_matches = num_teams * (num_teams - 1) / 2
                
                if estimated_matches > 0:
                    league_data['Corners Per Match'] = league_df['Pass Types CK'].sum() / estimated_matches
                else:
                    league_data['Corners Per Match'] = 5  # Default value
                
                # Corner types distribution
                corner_types = ['Corner Kicks In', 'Corner Kicks Out', 'Corner Kicks Str']
                total_corners = league_df['Pass Types CK'].sum()
                
                if total_corners > 0:
                    for corner_type in corner_types:
                        if corner_type in df.columns:
                            type_name = corner_type.replace('Corner Kicks ', '')
                            league_data[f'{type_name} Corner %'] = 100 * league_df[corner_type].sum() / total_corners
                
                # Direct corners percentage
                if 'Corner Kicks Str' in df.columns:
                    if total_corners > 0:
                        league_data['Direct Corners %'] = 100 - (100 * league_df['Corner Kicks Str'].sum() / total_corners)
                    else:
                        league_data['Direct Corners %'] = 85  # Default
                
                # Corner success metrics
                league_data['Corner Success Rate (%)'] = 30  # Default success rate
            
            # If we have SCA data related to corners, we can estimate corner effectiveness
            if all(col in df.columns for col in ['SCA Types PassDead', 'Pass Types CK']):
                # This is an approximation as PassDead includes all dead ball situations
                dead_ball_sca = league_df['SCA Types PassDead'].sum()
                total_corners = league_df['Pass Types CK'].sum()
                
                if total_corners > 0:
                    # Rough estimate assuming a portion of dead ball SCAs come from corners
                    estimated_corner_sca_ratio = min(1.0, dead_ball_sca / (total_corners * 1.5))
                    league_data['Corner to Shot %'] = 100 * estimated_corner_sca_ratio
            
            #---------------------------------------------------------------------
            # 6. PLAYER IMPACT METRICS
            #---------------------------------------------------------------------
            # Team performance with player
            impact_metrics = [
                ('Team Success +/-', '+/-'),
                ('Team Success +/-90', '+/- per 90'),
                ('Team Success On-Off', 'On-Off +/-'),
                ('Team Success (xG) xG+/-', 'xG +/-'),
                ('Team Success (xG) xG+/-90', 'xG +/- per 90'),
                ('Team Success (xG) On-Off', 'xG On-Off'),
                ('Team Success PPM', 'Points per Match')
            ]
            
            for src_col, target_name in impact_metrics:
                if src_col in df.columns:
                    league_data[target_name] = league_df[src_col].mean()
            
            # Combined contribution metrics
            if all(col in df.columns for col in ['Performance Gls', 'Ast', 'Playing Time 90s']):
                goals = league_df['Performance Gls'].sum()
                assists = league_df['Ast'].sum()
                
                league_data['G+A Per 90'] = (goals + assists) / max(1, league_df['Playing Time 90s'].sum())
                
                # Non-penalty contribution
                if 'Performance G-PK' in df.columns:
                    npg = league_df['Performance G-PK'].sum()
                    league_data['G+A-PK Per 90'] = (npg + assists) / max(1, league_df['Playing Time 90s'].sum())
            
            # Expected contribution
            if all(col in df.columns for col in ['Expected xG', 'Expected xA', 'Playing Time 90s']):
                xg = league_df['Expected xG'].sum()
                xa = league_df['Expected xA'].sum()
                
                league_data['xG+xA Per 90'] = (xg + xa) / max(1, league_df['Playing Time 90s'].sum())
                
                # Non-penalty expected contribution
                if 'Expected npxG' in df.columns:
                    npxg = league_df['Expected npxG'].sum()
                    league_data['npxG+xA Per 90'] = (npxg + xa) / max(1, league_df['Playing Time 90s'].sum())
            
            #---------------------------------------------------------------------
            # 7. EFFICIENCY METRICS
            #---------------------------------------------------------------------
            # Per 90 standardization is already applied throughout
            
            # Per touch efficiency
            if 'Touches Touches' in df.columns:
                touches = league_df['Touches Touches'].sum()
                
                if touches > 0:
                    # Goal impact per 100 touches
                    if all(col in df.columns for col in ['Performance Gls', 'Ast']):
                        goals = league_df['Performance Gls'].sum()
                        assists = league_df['Ast'].sum()
                        league_data['Goal Impact per 100 Touches'] = 100 * (goals + assists) / touches
                    
                    # Expected goal impact per 100 touches
                    if all(col in df.columns for col in ['Expected xG', 'Expected xA']):
                        xg = league_df['Expected xG'].sum()
                        xa = league_df['Expected xA'].sum()
                        league_data['xG+xA per 100 Touches'] = 100 * (xg + xa) / touches
                    
                    # Shot creating actions per 100 touches
                    if 'SCA SCA' in df.columns:
                        sca = league_df['SCA SCA'].sum()
                        league_data['SCA per 100 Touches'] = 100 * sca / touches
            
            # Per pass efficiency
            if 'Total Att' in df.columns:
                passes = league_df['Total Att'].sum()
                
                if passes > 0:
                    # Progressive pass percentage
                    if 'PrgP' in df.columns:
                        prog_passes = league_df['PrgP'].sum()
                        league_data['Progressive Pass %'] = 100 * prog_passes / passes
                    
                    # Key pass percentage
                    if 'KP' in df.columns:
                        key_passes = league_df['KP'].sum()
                        league_data['Key Pass %'] = 100 * key_passes / passes
            
            # Per carry efficiency
            if 'Carries Carries' in df.columns:
                carries = league_df['Carries Carries'].sum()
                
                if carries > 0:
                    # Progressive carry percentage
                    if 'Carries PrgC' in df.columns:
                        prog_carries = league_df['Carries PrgC'].sum()
                        league_data['Progressive Carry %'] = 100 * prog_carries / carries
                    
                    # Final third entry per carry
                    if 'Carries 1/3' in df.columns:
                        final_third_entries = league_df['Carries 1/3'].sum()
                        league_data['Final Third Entry per Carry %'] = 100 * final_third_entries / carries
                    
                    # Box entry per carry
                    if 'Carries CPA' in df.columns:
                        box_entries = league_df['Carries CPA'].sum()
                        league_data['Box Entry per Carry %'] = 100 * box_entries / carries
            
            #---------------------------------------------------------------------
            # 8. COMPOSITE METRICS
            #---------------------------------------------------------------------
            # Overall player contribution metrics
            if all(col in df.columns for col in ['Performance Gls', 'Ast']):
                # Calculate overall offensive contribution metrics
                if 'Expected xG' in df.columns and 'Expected xA' in df.columns:
                    actual_output = league_df['Performance Gls'].sum() + league_df['Ast'].sum()
                    expected_output = league_df['Expected xG'].sum() + league_df['Expected xA'].sum()
                    
                    if expected_output > 0:
                        league_data['Offensive Efficiency'] = actual_output / expected_output
                
                # Offensive value added
                if all(col in df.columns for col in ['Expected G-xG', 'Expected A-xAG', 'PrgP', 'Carries PrgC']):
                    g_minus_xg = league_df['Expected G-xG'].sum()
                    a_minus_xa = league_df['Expected A-xAG'].sum()
                    prog_passes = league_df['PrgP'].sum()
                    prog_carries = league_df['Carries PrgC'].sum()
                    
                    # Normalize progressive actions
                    total_players = max(1, league_df.shape[0])
                    normalized_prog_passes = prog_passes / total_players / 10
                    normalized_prog_carries = prog_carries / total_players / 10
                    
                    league_data['Offensive Value Added'] = g_minus_xg + a_minus_xa + normalized_prog_passes + normalized_prog_carries
            
            # Defensive value metrics
            if all(col in df.columns for col in ['Int', 'Tackles TklW', 'Clr', 'Blocks Blocks']):
                interceptions = league_df['Int'].sum()
                tackles_won = league_df['Tackles TklW'].sum()
                clearances = league_df['Clr'].sum()
                blocks = league_df['Blocks Blocks'].sum()
                
                # Normalize by number of players
                total_players = max(1, league_df.shape[0])
                
                league_data['Defensive Value Metric'] = (interceptions + tackles_won + clearances + blocks) / total_players
            
            # Playing style metrics
            # Calculate possession-based vs. direct play index
            if all(col in df.columns for col in ['Total Att', 'Total Cmp%', 'Long Att']):
                total_passes = league_df['Total Att'].sum()
                long_passes = league_df['Long Att'].sum()
                pass_completion = league_df['Total Cmp%'].mean()
                
                if total_passes > 0:
                    long_pass_ratio = long_passes / total_passes
                    # Higher values indicate more direct play
                    league_data['Direct Play Index'] = (long_pass_ratio * 100) / (pass_completion / 100)
            
            # Calculate pressing intensity
            if all(col in df.columns for col in ['Tackles Att 3rd', 'Tackles Mid 3rd', 'Tackles Def 3rd']):
                att_third_tackles = league_df['Tackles Att 3rd'].sum()
                mid_third_tackles = league_df['Tackles Mid 3rd'].sum()
                def_third_tackles = league_df['Tackles Def 3rd'].sum()
                
                total_tackles = att_third_tackles + mid_third_tackles + def_third_tackles
                
                if total_tackles > 0:
                    # Higher values indicate higher pressing
                    league_data['Pressing Intensity'] = (3 * att_third_tackles + 2 * mid_third_tackles + def_third_tackles) / total_tackles
            
            # Add to metrics list if we have enough data
            if len(league_data) > 5:
                league_metrics.append(league_data)
        
        # Player-level metrics
        player_cols = ['Player', 'Squad', 'Competition', 'Pos']
        
        # Additional metrics columns - expanded from original
        metric_cols = [
            # Attack metrics
            'Performance Gls', 'Performance Ast', 'Performance G+A', 'Performance G-PK', 
            'Standard Sh', 'Standard SoT', 'Standard SoT%', 'Expected xG', 'Expected G-xG',
            'GCA GCA', 'GCA GCA90', 'Expected xA', 'Expected npxG',
            
            # Possession metrics
            'Touches Touches', 'Touches Att Pen', 'Touches Att 3rd', 'Touches Mid 3rd', 'Touches Def 3rd',
            'Carries Carries', 'Carries PrgC', 'Carries 1/3', 'Carries CPA', 
            'Receives PrgR', 'Take-Ons Att', 'Take-Ons Succ', 'Take-Ons Succ%',
            
            # Passing metrics
            'Total Att', 'Total Cmp', 'Total Cmp%', 'PrgP', 'KP', 'Ast', 'xAG',
            'Short Cmp%', 'Medium Cmp%', 'Long Cmp%', 'SCA SCA', 'SCA SCA90',
            
            # Defensive metrics
            'Tackles Tkl', 'Tackles TklW', 'Int', 'Blocks Blocks', 'Clr',
            'Aerial Duels Won', 'Aerial Duels Won%', 'Performance Recov',
            
            # Corner metrics
            'Pass Types CK', 'Corner Kicks In', 'Corner Kicks Out', 'Corner Kicks Str',
            
            # Game time metrics
            'Playing Time 90s', 'Playing Time Min'
        ]
        
        # Create player dataframe with available columns
        available_cols = player_cols + [col for col in metric_cols if col in df.columns]
        player_df = df[available_cols].copy() if available_cols else pd.DataFrame()
        
        # Create league-level dataframe
        if league_metrics:
            leagues_df = pd.DataFrame(league_metrics)
            
            # Fill missing values with defaults
            default_values = {
                # Attack defaults
                'Shots Per 90': 12,
                'Shot on Target %': 35,
                'xG Per Shot': 0.1,
                'Goals Per Shot': 0.1,
                'Conversion Rate': 10,
                'Goals per SoT': 0.3,
                'G-xG': 0,
                'GCA Per 90': 2,
                'Box Touches %': 7,
                'Carries into Box Per 90': 4,
                'Passes into Box Per 90': 5,
                'Non-Penalty Goals Per 90': 1.2,
                'Penalty Conversion %': 75,
                
                # Defense defaults
                'Tackles Per 90': 15,
                'Tackle Success %': 65,
                'Interceptions Per 90': 10,
                'Tackles+Interceptions Per 90': 25,
                'Blocks Per 90': 8,
                'Shot Blocks %': 50,
                'Pass Blocks %': 50,
                'Clearances Per 90': 20,
                'Errors Per 90': 0.5,
                'Def 3rd Tackles %': 50,
                'Mid 3rd Tackles %': 35,
                'Att 3rd Tackles %': 15,
                'Aerial Duels Won %': 50,
                'Pressure Success %': 30,
                'Recoveries Per 90': 35,
                
                # Possession defaults
                'Possession %': 50,
                'Touches Per 90': 500,
                'Def 3rd Touch %': 30,
                'Mid 3rd Touch %': 50,
                'Att 3rd Touch %': 20,
                'Att Pen Touch %': 5,
                'Def Pen Touch %': 3,
                'Progressive Carries Per 90': 30,
                'Progressive Carry %': 15,
                'Carries into Final Third Per 90': 15,
                'Carries into Box Per 90': 2,
                'Progressive Passes Received Per 90': 25,
                'Miscontrols per 100 Touches': 3,
                'Dispossessed per 100 Touches': 2,
                'Carry Success %': 95,
                'Take-On Success %': 55,
                'Take-Ons Per 90': 8,
                'Successful Take-Ons Per 90': 4.5,
                
                # Passing defaults
                'Short Pass Completion %': 88,
                'Medium Pass Completion %': 80,
                'Long Pass Completion %': 55,
                'Pass Completion %': 80,
                'Avg Pass Distance': 18,
                'Progressive Passes Per 90': 35,
                'Progressive Pass Ratio': 10,
                'Progressive Pass Distance Per 90': 400,
                'Key Passes Per 90': 1.5,
                'Key Pass %': 3,
                'xA Per 90': 0.2,
                'Assist Rate': 10,
                'xA per Key Pass': 0.1,
                'A-xA': 0,
                'xAG Per 90': 0.25,
                'SCA Per 90': 3,
                
                # Corner defaults
                'Corners Per Match': 5,
                'In Corner %': 25,
                'Out Corner %': 60,
                'Str Corner %': 15,
                'Direct Corners %': 85,
                'Corner Success Rate (%)': 30,
                'Corner to Shot %': 25,
                
                # Player impact defaults
                '+/-': 0,
                '+/- per 90': 0,
                'On-Off +/-': 0,
                'xG +/-': 0,
                'xG +/- per 90': 0,
                'xG On-Off': 0,
                'Points per Match': 1.5,
                'G+A Per 90': 0.4,
                'G+A-PK Per 90': 0.35,
                'xG+xA Per 90': 0.4,
                'npxG+xA Per 90': 0.35,
                
                # Efficiency defaults
                'Goal Impact per 100 Touches': 0.8,
                'xG+xA per 100 Touches': 0.8,
                'SCA per 100 Touches': 5,
                'Progressive Pass %': 12,
                'Key Pass %': 3,
                'Progressive Carry %': 10,
                'Final Third Entry per Carry %': 5,
                'Box Entry per Carry %': 1.5,
                
                # Composite defaults
                'Offensive Efficiency': 1.0,
                'Offensive Value Added': 0,
                'Defensive Value Metric': 50,
                'Direct Play Index': 100,
                'Pressing Intensity': 1.5
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
            # Attack metrics
            "Shots Per 90": np.random.normal(12.5, 1.5),
            "Shot on Target %": np.random.normal(35, 5),
            "xG Per Shot": np.random.normal(0.1, 0.02),
            "Goals Per Shot": np.random.normal(0.11, 0.02),
            "Conversion Rate": np.random.normal(10, 2),
            "Goals per SoT": np.random.normal(0.3, 0.05),
            "G-xG": np.random.normal(0, 5),
            "GCA Per 90": np.random.normal(2, 0.3),
            "Box Touches %": np.random.normal(7, 1.5),
            "Carries into Box Per 90": np.random.normal(4, 1),
            "Passes into Box Per 90": np.random.normal(5, 1.2),
            
            # Defense metrics
            "Tackles Per 90": np.random.normal(18, 3),
            "Tackle Success %": np.random.normal(65, 5),
            "Interceptions Per 90": np.random.normal(12, 2),
            "Blocks Per 90": np.random.normal(9, 1.5),
            "Clearances Per 90": np.random.normal(22, 4),
            "Aerial Duels Won %": np.random.normal(50, 5),
            "Pressure Success %": np.random.normal(30, 4),
            
            # Possession metrics
            "Possession %": np.random.normal(50, 5),
            "Touches in Attacking Third": np.random.normal(160, 20),
            "Progressive Carries Per 90": np.random.normal(30, 5),
            "Progressive Carry %": np.random.normal(15, 3),
            "Take-On Success %": np.random.normal(55, 8),
            
            # Passing metrics
            "Pass Completion %": np.random.normal(82, 3),
            "Progressive Passes Per 90": np.random.normal(35, 6),
            "Key Passes Per 90": np.random.normal(1.5, 0.3),
            "xA Per 90": np.random.normal(0.2, 0.05),
            "SCA Per 90": np.random.normal(3, 0.6),
            
            # Corner metrics
            "Corners Per Match": np.random.normal(5.2, 0.5),
            "Corner Success Rate (%)": np.random.normal(30, 5),
            "Direct Corners %": np.random.normal(85, 5),
            
            # Composite metrics
            "Offensive Efficiency": np.random.normal(1.0, 0.1),
            "Pressing Intensity": np.random.normal(1.5, 0.2),
            "Direct Play Index": np.random.normal(100, 15)
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
                        'Standard Sh': np.random.poisson(35 if pos == 'FW' else (25 if pos == 'MF' else 8)),
                        'Standard SoT': np.random.poisson(12 if pos == 'FW' else (8 if pos == 'MF' else 3)),
                        'Expected xG': np.random.normal(6 if pos == 'FW' else (3 if pos == 'MF' else 1), 1),
                        'Total Cmp%': np.random.normal(85 if pos == 'GK' else 80, 5),
                        'PrgP': np.random.poisson(70 if pos == 'MF' else (40 if pos == 'DF' else 20)),
                        'Carries PrgC': np.random.poisson(60 if pos == 'MF' else (30 if pos == 'FW' else 10)),
                        'Tackles Tkl': np.random.poisson(40 if pos == 'DF' else (35 if pos == 'MF' else 15)),
                        'Int': np.random.poisson(30 if pos == 'DF' else (25 if pos == 'MF' else 10)),
                        'Playing Time 90s': np.random.normal(25, 8),
                        'Touches Touches': np.random.poisson(2000 if pos == 'MF' else (1800 if pos == 'DF' else 1200))
                    })
    
    players_df = pd.DataFrame(player_data)
    
    return leagues_df, players_df
                    if all(col in df.columns for col in ['
