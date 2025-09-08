import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from io import StringIO
import traceback
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import StandardScaler

# Set page config
st.set_page_config(
    page_title="Player Performance Comparison Tool",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    .strength {
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        display: inline-block;
    }
    .weakness {
        background-color: #ef4444;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        display: inline-block;
    }
    .neutral {
        background-color: #6b7280;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        display: inline-block;
    }
    .percentile-badge {
        font-size: 2rem;
        font-weight: 700;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .percentile-high {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    .percentile-mid {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
    }
    .percentile-low {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }

</style>
""", unsafe_allow_html=True)

def clean_numeric_column(series):
    """Clean and convert a pandas series to numeric, handling common issues"""
    if series.dtype == 'object':
        series = series.astype(str)
        series = series.str.replace(',', '')
        series = series.str.replace('%', '')
        series = series.str.replace('€', '')
        series = series.str.replace('£', '')
        series = series.str.replace('$', '')
        series = series.str.strip()
        series = series.replace(['', '-', 'N/A', 'n/a', 'NaN', 'nan', 'null'], np.nan)
    return pd.to_numeric(series, errors='coerce')

@st.cache_data
def load_player_data():
    """Load player data from GitHub"""
    GITHUB_RAW_URL = 'https://raw.githubusercontent.com/ashmeetanand13/squad-performance/main/df_clean.csv'
    
    try:
        with st.spinner("Loading player data from GitHub..."):
            response = requests.get(GITHUB_RAW_URL, timeout=15)
            response.raise_for_status()
            
            content = StringIO(response.text)
            df = pd.read_csv(content, low_memory=False, on_bad_lines='skip', encoding='utf-8')
            
            if df.shape[0] == 0:
                raise ValueError("No valid rows found in CSV")
            
            # Remove ranking column if it exists
            if 'Rk' in df.columns:
                df = df.drop('Rk', axis=1)
            
            st.success(f"Successfully loaded {df.shape[0]} player records")
            return df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

@st.cache_data
def process_player_data(df):
    """Process and clean player data, focusing on per-90 metrics"""
    if df is None:
        return None
    
    try:
        # Ensure required columns exist
        required_columns = ['Player', 'Pos', 'Squad', 'Competition', 'Season']
        column_mapping = {
            'Player': ['Player', 'Name'],
            'Pos': ['Pos', 'Position'],
            'Squad': ['Squad', 'Team', 'Club'],
            'Competition': ['Competition', 'Comp', 'League'],
            'Season': ['Season', 'Year', 'Season_Year']
        }
        
        # Fix column names
        for required, alternatives in column_mapping.items():
            if required not in df.columns:
                for alt in alternatives:
                    if alt in df.columns:
                        df = df.rename(columns={alt: required})
                        break
        
        # Check if all required columns are present
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing required columns: {missing}")
            return None
        
        # Extract primary position (first position if multiple)
        df['Primary_Position'] = df['Pos'].apply(
            lambda x: x.split(',')[0].strip() if isinstance(x, str) and ',' in x else x
        )
        
        # Clean numeric columns
        numeric_columns = []
        for col in df.columns:
            if col not in required_columns + ['Primary_Position']:
                original_type = df[col].dtype
                df[col] = clean_numeric_column(df[col])
                if df[col].notna().any():
                    numeric_columns.append(col)
        
        # Identify per-90 metrics and create them if they don't exist
        minutes_cols = [col for col in numeric_columns if 
                       any(keyword in col.lower() for keyword in ['90s', 'minutes', 'min', 'mp'])]
        
        if minutes_cols:
            minutes_col = minutes_cols[0]
            
            # Create per-90 versions of key metrics
            for col in numeric_columns:
                # Skip if already a per-90 metric or a percentage
                if not any(keyword in col.lower() for keyword in ['per 90', '/90', '%', 'pct', 'rate', '90s']):
                    per_90_col = f"{col} Per 90"
                    if per_90_col not in df.columns:
                        df[per_90_col] = df.apply(
                            lambda row: row[col] / row[minutes_col] if row[minutes_col] > 0 else 0,
                            axis=1
                        )
        
        # Fill NaN values with 0 for numeric columns
        for col in df.select_dtypes(include=['number']).columns:
            df[col] = df[col].fillna(0)
        
        return df
    
    except Exception as e:
        st.error(f"Error processing player data: {str(e)}")
        st.error(traceback.format_exc())
        return None

def get_position_metrics(position, available_columns):
    """Define relevant metrics for each specific position based on available columns"""
    # Define position-specific metric priorities for detailed positions
    position_metrics = {
        'GK': {
            'primary': ['save', 'saves%', 'clean', 'psxg', 'sota', 'ga', 'pka'],
            'secondary': ['pass', 'launch', 'avglen', 'cmp', 'throw'],
            'defensive': ['fka', 'sweeper']
        },
        'LB/LWB': {
            'primary': ['tkl', 'int', 'blocks', 'cross', 'key', 'prog'],
            'secondary': ['touches', 'pass', 'cmp', 'carries', 'take'],
            'defensive': ['clr', 'aerial', 'won', 'foul']
        },
        'RB/RWB': {
            'primary': ['tkl', 'int', 'blocks', 'cross', 'key', 'prog'],
            'secondary': ['touches', 'pass', 'cmp', 'carries', 'take'],
            'defensive': ['clr', 'aerial', 'won', 'foul']
        },
        'CB': {
            'primary': ['tkl', 'int', 'blocks', 'clr', 'aerial', 'won%'],
            'secondary': ['pass', 'cmp', 'long', 'prgp'],
            'defensive': ['err', 'foul', 'card', 'pen']
        },
        'CB/DM': {
            'primary': ['tkl', 'int', 'blocks', 'pass', 'cmp'],
            'secondary': ['clr', 'aerial', 'prgp', 'carries'],
            'defensive': ['foul', 'card', 'err']
        },
        'DM': {
            'primary': ['tkl', 'int', 'pass', 'cmp', 'prgp', 'touches'],
            'secondary': ['blocks', 'carries', 'long', 'key'],
            'defensive': ['foul', 'card', 'clr']
        },
        'CM': {
            'primary': ['pass', 'cmp', 'prgp', 'key', 'touches', 'carries'],
            'secondary': ['tkl', 'int', 'shot', 'gls', 'ast'],
            'defensive': ['press', 'blocks', 'foul']
        },
        'AM': {
            'primary': ['key', 'xa', 'sca', 'gca', 'pass', 'touches'],
            'secondary': ['gls', 'shot', 'ast', 'carries', 'prgc'],
            'defensive': ['press', 'tkl']
        },
        'AM/W': {
            'primary': ['key', 'xa', 'sca', 'shot', 'gls', 'take'],
            'secondary': ['cross', 'carries', 'touches', 'ast'],
            'defensive': ['press', 'tkl']
        },
        'LW/LM': {
            'primary': ['shot', 'gls', 'xa', 'take', 'cross', 'key'],
            'secondary': ['touches', 'carries', 'prgc', 'ast', 'sca'],
            'defensive': ['press', 'tkl', 'int']
        },
        'RW/RM': {
            'primary': ['shot', 'gls', 'xa', 'take', 'cross', 'key'],
            'secondary': ['touches', 'carries', 'prgc', 'ast', 'sca'],
            'defensive': ['press', 'tkl', 'int']
        },
        'ST/CF': {
            'primary': ['gls', 'xg', 'shot', 'sot', 'g/sh', 'npxg'],
            'secondary': ['touches', 'ast', 'xa', 'aerial', 'won'],
            'defensive': ['press', 'foul']
        },
        'FW': {
            'primary': ['gls', 'xg', 'shot', 'sot', 'ast', 'xa'],
            'secondary': ['touches', 'key', 'sca', 'gca', 'take'],
            'defensive': ['press', 'tkl']
        }
    }
    
    # If position not found, default to CM (most balanced)
    if position not in position_metrics:
        if 'Unknown' in position:
            position = 'CM'  # Default for unknown positions
        else:
            # Try to find a close match
            for key in position_metrics.keys():
                if key in position or position in key:
                    position = key
                    break
            else:
                position = 'CM'
    
    selected_metrics = []
    
    # Try to find metrics matching the position priorities
    for priority in ['primary', 'secondary', 'defensive']:
        keywords = position_metrics[position].get(priority, [])
        for keyword in keywords:
            for col in available_columns:
                col_lower = col.lower()
                # Prioritize per-90 metrics
                if keyword in col_lower and 'per 90' in col_lower:
                    if col not in selected_metrics:
                        selected_metrics.append(col)
                        if len(selected_metrics) >= 15:  # Limit to 15 metrics
                            return selected_metrics
    
    # If we don't have enough per-90 metrics, add regular metrics
    if len(selected_metrics) < 10:
        for priority in ['primary', 'secondary']:
            keywords = position_metrics[position].get(priority, [])
            for keyword in keywords:
                for col in available_columns:
                    col_lower = col.lower()
                    if keyword in col_lower and col not in selected_metrics:
                        selected_metrics.append(col)
                        if len(selected_metrics) >= 15:
                            return selected_metrics
    
    return selected_metrics

def calculate_percentiles(player_data, position_df, metrics):
    """Calculate percentile rankings for a player within their position"""
    percentiles = {}
    
    for metric in metrics:
        if metric in player_data.index and metric in position_df.columns:
            player_value = player_data[metric]
            position_values = position_df[metric].dropna()
            
            if len(position_values) > 0:
                percentile = (position_values < player_value).sum() / len(position_values) * 100
                percentiles[metric] = percentile
    
    return percentiles

def identify_strengths_weaknesses(percentiles, threshold_high=75, threshold_low=25):
    """Identify player strengths and weaknesses based on percentile rankings"""
    strengths = []
    weaknesses = []
    average = []
    
    for metric, percentile in percentiles.items():
        clean_metric = metric.replace(' Per 90', '').replace('Performance ', '').replace('Standard ', '')
        
        if percentile >= threshold_high:
            strengths.append((clean_metric, percentile))
        elif percentile <= threshold_low:
            weaknesses.append((clean_metric, percentile))
        else:
            average.append((clean_metric, percentile))
    
    # Sort by percentile
    strengths.sort(key=lambda x: x[1], reverse=True)
    weaknesses.sort(key=lambda x: x[1])
    
    return strengths, weaknesses, average

def create_radar_chart(player1_data, player2_data, metrics, percentiles1=None, percentiles2=None):
    """Create radar chart comparing two players"""
    # Filter for available metrics
    available_metrics = [m for m in metrics if m in player1_data.index and m in player2_data.index]
    
    if len(available_metrics) < 3:
        return None
    
    # Use percentiles if available, otherwise normalize values
    if percentiles1 and percentiles2:
        values1 = [percentiles1.get(m, 50) / 100 for m in available_metrics]
        values2 = [percentiles2.get(m, 50) / 100 for m in available_metrics]
    else:
        # Normalize values between 0 and 1
        values1 = []
        values2 = []
        for metric in available_metrics:
            val1 = player1_data[metric]
            val2 = player2_data[metric]
            max_val = max(val1, val2) if max(val1, val2) > 0 else 1
            values1.append(val1 / max_val if max_val > 0 else 0)
            values2.append(val2 / max_val if max_val > 0 else 0)
    
    # Clean metric names for display
    labels = [m.replace(' Per 90', '').replace('Performance ', '').replace('Standard ', '') 
              for m in available_metrics]
    
    # Create radar chart
    fig = go.Figure()
    
    # Add trace for player 1
    fig.add_trace(go.Scatterpolar(
        r=values1,
        theta=labels,
        fill='toself',
        name=player1_data['Player'],
        line_color='#1E3A8A',
        fillcolor='rgba(30, 58, 138, 0.3)'
    ))
    
    # Add trace for player 2
    fig.add_trace(go.Scatterpolar(
        r=values2,
        theta=labels,
        fill='toself',
        name=player2_data['Player'],
        line_color='#DC2626',
        fillcolor='rgba(220, 38, 38, 0.3)'
    ))
    
    # Update layout
    fig.update_layout(
        title="Player Performance Comparison",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        height=700,
        template="plotly_white"
    )
    
    return fig

def create_percentile_chart(player_data, percentiles, position):
    """Create a bar chart showing percentile rankings"""
    if not percentiles:
        return None
    
    # Sort metrics by percentile
    sorted_metrics = sorted(percentiles.items(), key=lambda x: x[1], reverse=True)[:15]
    
    metrics = [m[0].replace(' Per 90', '').replace('Performance ', '').replace('Standard ', '') 
               for m in sorted_metrics]
    values = [m[1] for m in sorted_metrics]
    
    # Color based on percentile
    colors = ['#10b981' if v >= 75 else '#ef4444' if v <= 25 else '#3b82f6' for v in values]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=metrics,
        y=values,
        marker_color=colors,
        text=[f"{v:.0f}%" for v in values],
        textposition='auto',
    ))
    
    fig.update_layout(
        title=f"{player_data['Player']} - Percentile Rankings ({position})",
        xaxis_title="Metric",
        yaxis_title="Percentile",
        height=400,
        yaxis=dict(range=[0, 100]),
        template="plotly_white",
        xaxis_tickangle=-45
    )
    
    return fig

def find_similar_players(player_data, all_players_df, position, top_n=10):
    """Find similar players based on playing style"""
    # Filter to same position
    position_df = all_players_df[all_players_df['Primary_Position'] == position].copy()
    
    # Remove the current player (all instances)
    if 'Player' in player_data.index:
        position_df = position_df[position_df['Player'] != player_data['Player']]
    
    if position_df.empty:
        return pd.DataFrame()
    
    # Get numeric columns that are in both datasets
    # Prioritize Per 90 metrics, but exclude the Total_Minutes column we created
    numeric_cols = [col for col in position_df.select_dtypes(include=['number']).columns
                   if col in player_data.index and col != 'Total_Minutes']
    
    # Filter to get meaningful metrics (prefer Per 90 or percentage metrics)
    per_90_cols = [col for col in numeric_cols if 'Per 90' in col or 'per 90' in col]
    pct_cols = [col for col in numeric_cols if '%' in col or 'pct' in col.lower()]
    other_cols = [col for col in numeric_cols if col not in per_90_cols and col not in pct_cols]
    
    # Combine, prioritizing Per 90 and percentage metrics
    selected_cols = per_90_cols + pct_cols + other_cols[:max(0, 20 - len(per_90_cols) - len(pct_cols))]
    
    if not selected_cols:
        # If no good columns found, use any numeric columns
        selected_cols = numeric_cols[:20]
    
    if not selected_cols:
        return pd.DataFrame()
    
    # Prepare data for comparison
    player_values = []
    position_values = []
    
    # Build arrays, skipping columns where player has NaN
    valid_cols = []
    for col in selected_cols:
        if pd.notna(player_data[col]):
            player_values.append(player_data[col])
            position_values.append(position_df[col].fillna(0).values)
            valid_cols.append(col)
    
    if not valid_cols:
        return pd.DataFrame()
    
    # Convert to numpy arrays
    player_array = np.array(player_values)
    position_array = np.array(position_values).T  # Transpose to get players x features
    
    # Handle NaN and inf values
    player_array = np.nan_to_num(player_array, nan=0.0, posinf=0.0, neginf=0.0)
    position_array = np.nan_to_num(position_array, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Normalize by column (feature-wise) to put all metrics on same scale
    # This is crucial for meaningful distance calculations
    all_data = np.vstack([player_array.reshape(1, -1), position_array])
    
    # Calculate min and max for each feature
    feature_min = np.min(all_data, axis=0)
    feature_max = np.max(all_data, axis=0)
    feature_range = feature_max - feature_min
    
    # Avoid division by zero
    feature_range[feature_range == 0] = 1
    
    # Normalize to 0-1 scale
    player_normalized = (player_array - feature_min) / feature_range
    position_normalized = (position_array - feature_min) / feature_range
    
    # Calculate Euclidean distances
    distances = []
    for i in range(len(position_normalized)):
        try:
            # Calculate Euclidean distance
            diff = player_normalized - position_normalized[i]
            dist = np.sqrt(np.sum(diff ** 2))
            distances.append(dist)
        except Exception as e:
            # If any error, use maximum distance
            distances.append(np.sqrt(len(valid_cols)))  # Max possible normalized distance
    
    # Add distances to dataframe
    position_df['Similarity_Distance'] = distances
    
    # Calculate similarity score (0-100%)
    # Normalize distances to 0-1 range first
    max_dist = np.sqrt(len(valid_cols))  # Maximum possible distance in normalized space
    position_df['Similarity_Score'] = 100 * (1 - position_df['Similarity_Distance'] / max_dist)
    
    # Ensure scores are in valid range
    position_df['Similarity_Score'] = position_df['Similarity_Score'].clip(0, 100)
    
    # Sort by similarity
    position_df = position_df.sort_values('Similarity_Distance')
    
    # DEDUPLICATION: Keep only the best entry for each player
    # Group by player name and keep the one with highest similarity (lowest distance)
    seen_players = set()
    deduplicated_rows = []
    
    for idx, row in position_df.iterrows():
        player_name = row['Player']
        if player_name not in seen_players:
            seen_players.add(player_name)
            deduplicated_rows.append(row)
            if len(deduplicated_rows) >= top_n:
                break
    
    # Create final dataframe from deduplicated rows
    if deduplicated_rows:
        similar_players = pd.DataFrame(deduplicated_rows)[
            ['Player', 'Squad', 'Competition', 'Season', 'Similarity_Score']
        ].copy()
        
        # Round similarity percentage
        similar_players['Similarity %'] = similar_players['Similarity_Score'].round(1)
        similar_players = similar_players.drop('Similarity_Score', axis=1)
    else:
        similar_players = pd.DataFrame()
    
    return similar_players

def main():
    """Main function to run the Streamlit application"""
    st.markdown('<p class="main-header">⚽ Player Performance Comparison Tool</p>', unsafe_allow_html=True)
    
    # Load and process data
    with st.spinner("Loading player data..."):
        df = load_player_data()
        if df is not None:
            players_df = process_player_data(df)
        else:
            st.error("Failed to load player data")
            return
    
    if players_df is None:
        st.error("Failed to process player data")
        return
    
    # Sidebar navigation
    st.sidebar.markdown("## Navigation")
    app_mode = st.sidebar.selectbox(
        "Select Mode",
        ["Player Comparison", "Single Player Analysis", "Find Similar Players"]
    )
    
    # Filter options
    st.sidebar.markdown("## Filters")
    
    # Add minimum minutes filter
    st.sidebar.markdown("### Playing Time Filter")
    
    # Look specifically for the "Playing Time Min" column first
    minutes_col = None
    if 'Playing Time Min' in players_df.columns:
        minutes_col = 'Playing Time Min'
    else:
        # Fallback to searching for other minutes columns
        possible_minutes_cols = [col for col in players_df.columns if 
                                any(keyword in col.lower() for keyword in ['minutes', 'min', 'mp', '90s'])
                                and 'playing' in col.lower()]
        if not possible_minutes_cols:
            # Broader search if no "playing" columns found
            possible_minutes_cols = [col for col in players_df.columns if 
                                    any(keyword in col.lower() for keyword in ['90s', 'minutes', 'min', 'mp'])
                                    and not any(exclude in col.lower() for exclude in ['per', 'avg', '%'])]
        
        if possible_minutes_cols:
            minutes_col = possible_minutes_cols[0]
    
    if minutes_col:
        # Debug info
        st.sidebar.caption(f"Using column: {minutes_col}")
        
        # Calculate actual minutes based on column type
        if '90s' in minutes_col.lower() or '90' in minutes_col:
            # Column is in 90s, multiply by 90 to get actual minutes
            players_df['Total_Minutes'] = players_df[minutes_col] * 90
        else:
            # Column is already in minutes (like "Playing Time Min")
            players_df['Total_Minutes'] = players_df[minutes_col]
        
        # Clean the data - remove NaN and ensure positive values
        players_df['Total_Minutes'] = players_df['Total_Minutes'].fillna(0)
        players_df['Total_Minutes'] = players_df['Total_Minutes'].clip(lower=0)
        
        # Get min and max for the slider
        min_val = 0  # Always start from 0
        max_val = players_df['Total_Minutes'].max()
        
        # Only create slider if we have valid range
        if max_val > 0:
            # Set reasonable defaults
            default_min = min(450, max_val * 0.1)  # Default to 450 minutes or 10% of max
            
            min_minutes_filter = st.sidebar.slider(
                "Minimum Minutes Played",
                min_value=min_val,
                max_value=int(max_val),
                value=int(default_min),
                step=90,
                help="Filter out players with less than this many minutes played. 90 minutes = 1 full match"
            )
            
            # Show equivalent matches
            st.sidebar.caption(f"≈ {min_minutes_filter / 90:.1f} full matches")
            
            # Apply the filter
            players_df_filtered = players_df[players_df['Total_Minutes'] >= min_minutes_filter].copy()
            
            # Show how many players remain after filtering
            total_players = len(players_df)
            filtered_players = len(players_df_filtered)
            st.sidebar.info(f"Showing {filtered_players:,} of {total_players:,} players")
            
            # Use the filtered dataframe
            players_df = players_df_filtered
        else:
            st.sidebar.warning("Could not calculate valid minutes range")
            min_minutes_filter = 0
    else:
        st.sidebar.warning("'Playing Time Min' column not found - showing all players")
        min_minutes_filter = 0
        # List available columns for debugging
        st.sidebar.caption("Available columns (first 10):")
        cols_sample = [col for col in players_df.columns][:10]
        for col in cols_sample:
            st.sidebar.caption(f"- {col}")
    
    st.sidebar.markdown("---")
    
    # Get unique values after filtering
    positions = sorted(players_df['Primary_Position'].dropna().unique())
    competitions = sorted(players_df['Competition'].dropna().unique())
    seasons = sorted(players_df['Season'].dropna().unique(), reverse=True)
    
    if app_mode == "Player Comparison":
        st.markdown('<p class="sub-header">Player Comparison</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Select First Player")
            
            # Player 1 filters
            pos1 = st.selectbox("Position", positions, key="pos1")
            comp1 = st.selectbox("Competition", ["All"] + competitions, key="comp1")
            season1 = st.selectbox("Season", ["All"] + seasons, key="season1")
            
            # Filter dataframe for player 1
            filtered_df1 = players_df[players_df['Primary_Position'] == pos1]
            if comp1 != "All":
                filtered_df1 = filtered_df1[filtered_df1['Competition'] == comp1]
            if season1 != "All":
                filtered_df1 = filtered_df1[filtered_df1['Season'] == season1]
            
            # Player selection
            player_list1 = filtered_df1['Player'].dropna().unique()
            player1_name = st.selectbox("Select Player", sorted(player_list1), key="player1")
        
        with col2:
            st.markdown("### Select Second Player")
            
            # Player 2 filters
            pos2 = st.selectbox("Position", positions, key="pos2", index=positions.index(pos1))
            comp2 = st.selectbox("Competition", ["All"] + competitions, key="comp2")
            season2 = st.selectbox("Season", ["All"] + seasons, key="season2")
            
            # Filter dataframe for player 2
            filtered_df2 = players_df[players_df['Primary_Position'] == pos2]
            if comp2 != "All":
                filtered_df2 = filtered_df2[filtered_df2['Competition'] == comp2]
            if season2 != "All":
                filtered_df2 = filtered_df2[filtered_df2['Season'] == season2]
            
            # Player selection
            player_list2 = filtered_df2['Player'].dropna().unique()
            player2_name = st.selectbox("Select Player", sorted(player_list2), key="player2")
        
        # Compare players
        if player1_name and player2_name:
            # Get player data
            player1_data = filtered_df1[filtered_df1['Player'] == player1_name].iloc[0]
            player2_data = filtered_df2[filtered_df2['Player'] == player2_name].iloc[0]
            
            # Get position metrics (use first player's position)
            available_cols = [col for col in players_df.columns if 'Per 90' in col or '%' in col]
            position_metrics = get_position_metrics(pos1, available_cols)
            
            # Calculate percentiles for both players
            position_df = players_df[players_df['Primary_Position'] == pos1]
            percentiles1 = calculate_percentiles(player1_data, position_df, position_metrics)
            percentiles2 = calculate_percentiles(player2_data, position_df, position_metrics)
            
            # Display comparison
            tabs = st.tabs(["Overview", "Detailed Metrics", "Strengths & Weaknesses"])
            
            with tabs[0]:
                # Player info cards
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{player1_name}</h3>
                        <p><strong>Team:</strong> {player1_data['Squad']}</p>
                        <p><strong>Competition:</strong> {player1_data['Competition']}</p>
                        <p><strong>Season:</strong> {player1_data['Season']}</p>
                        <p><strong>Position:</strong> {player1_data['Primary_Position']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{player2_name}</h3>
                        <p><strong>Team:</strong> {player2_data['Squad']}</p>
                        <p><strong>Competition:</strong> {player2_data['Competition']}</p>
                        <p><strong>Season:</strong> {player2_data['Season']}</p>
                        <p><strong>Position:</strong> {player2_data['Primary_Position']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Radar chart comparison
                radar_chart = create_radar_chart(player1_data, player2_data, position_metrics, percentiles1, percentiles2)
                if radar_chart:
                    st.plotly_chart(radar_chart, use_container_width=True)
                
                # Overall ratings
                col1, col2 = st.columns(2)
                
                with col1:
                    avg_percentile1 = np.mean(list(percentiles1.values())) if percentiles1 else 50
                    color_class = "percentile-high" if avg_percentile1 >= 75 else "percentile-low" if avg_percentile1 <= 25 else "percentile-mid"
                    st.markdown(f"""
                    <div class="percentile-badge {color_class}">
                        {player1_name}<br>
                        Overall Rating: {avg_percentile1:.0f}%
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    avg_percentile2 = np.mean(list(percentiles2.values())) if percentiles2 else 50
                    color_class = "percentile-high" if avg_percentile2 >= 75 else "percentile-low" if avg_percentile2 <= 25 else "percentile-mid"
                    st.markdown(f"""
                    <div class="percentile-badge {color_class}">
                        {player2_name}<br>
                        Overall Rating: {avg_percentile2:.0f}%
                    </div>
                    """, unsafe_allow_html=True)
            
            with tabs[1]:
                # Detailed metrics comparison
                st.markdown("### Per 90 Minutes Metrics Comparison")
                
                comparison_data = []
                for metric in position_metrics:
                    if metric in player1_data.index and metric in player2_data.index:
                        val1 = player1_data[metric]
                        val2 = player2_data[metric]
                        
                        # Get percentiles
                        pct1 = percentiles1.get(metric, 50)
                        pct2 = percentiles2.get(metric, 50)
                        
                        comparison_data.append({
                            'Metric': metric.replace(' Per 90', '').replace('Performance ', ''),
                            f'{player1_name}': f"{val1:.2f}",
                            f'{player1_name} %tile': f"{pct1:.0f}%",
                            f'{player2_name}': f"{val2:.2f}",
                            f'{player2_name} %tile': f"{pct2:.0f}%",
                            'Difference': f"{val1 - val2:+.2f}"
                        })
                
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True)
            
            with tabs[2]:
                # Strengths and weaknesses
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"### {player1_name}")
                    
                    strengths1, weaknesses1, average1 = identify_strengths_weaknesses(percentiles1)
                    
                    st.markdown("**Strengths:**")
                    for metric, pct in strengths1[:5]:
                        st.markdown(f'<span class="strength">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
                    
                    st.markdown("**Weaknesses:**")
                    for metric, pct in weaknesses1[:5]:
                        st.markdown(f'<span class="weakness">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"### {player2_name}")
                    
                    strengths2, weaknesses2, average2 = identify_strengths_weaknesses(percentiles2)
                    
                    st.markdown("**Strengths:**")
                    for metric, pct in strengths2[:5]:
                        st.markdown(f'<span class="strength">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
                    
                    st.markdown("**Weaknesses:**")
                    for metric, pct in weaknesses2[:5]:
                        st.markdown(f'<span class="weakness">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
    
    elif app_mode == "Single Player Analysis":
        st.markdown('<p class="sub-header">Single Player Analysis</p>', unsafe_allow_html=True)
        
        # Player selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_pos = st.selectbox("Position", positions)
        
        with col2:
            selected_comp = st.selectbox("Competition", ["All"] + competitions)
        
        with col3:
            selected_season = st.selectbox("Season", ["All"] + seasons)
        
        # Filter dataframe
        filtered_df = players_df[players_df['Primary_Position'] == selected_pos]
        if selected_comp != "All":
            filtered_df = filtered_df[filtered_df['Competition'] == selected_comp]
        if selected_season != "All":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        
        # Player selection
        player_list = filtered_df['Player'].dropna().unique()
        selected_player = st.selectbox("Select Player", sorted(player_list))
        
        if selected_player:
            # Get player data
            player_data = filtered_df[filtered_df['Player'] == selected_player].iloc[0]
            
            # Display player info
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Team", player_data['Squad'])
            with col2:
                st.metric("Competition", player_data['Competition'])
            with col3:
                st.metric("Season", player_data['Season'])
            with col4:
                st.metric("Position", player_data['Primary_Position'])
            
            # Get position metrics
            available_cols = [col for col in players_df.columns if 'Per 90' in col or '%' in col]
            position_metrics = get_position_metrics(selected_pos, available_cols)
            
            # Calculate percentiles
            position_df = players_df[players_df['Primary_Position'] == selected_pos]
            percentiles = calculate_percentiles(player_data, position_df, position_metrics)
            
            # Create tabs for analysis
            tabs = st.tabs(["Performance Overview", "Percentile Rankings", "Strengths & Weaknesses"])
            
            with tabs[0]:
                # Key metrics display
                st.markdown("### Key Performance Metrics (Per 90 Minutes)")
                
                # Display metrics in columns
                metrics_to_display = position_metrics[:12]
                
                for i in range(0, len(metrics_to_display), 3):
                    cols = st.columns(3)
                    for j, col in enumerate(cols):
                        if i + j < len(metrics_to_display):
                            metric = metrics_to_display[i + j]
                            if metric in player_data.index:
                                value = player_data[metric]
                                pct = percentiles.get(metric, 50)
                                
                                # Color based on percentile
                                delta_color = "normal"
                                if pct >= 75:
                                    delta_color = "normal"
                                elif pct <= 25:
                                    delta_color = "inverse"
                                
                                col.metric(
                                    metric.replace(' Per 90', '').replace('Performance ', ''),
                                    f"{value:.2f}",
                                    f"{pct:.0f}%ile",
                                    delta_color=delta_color
                                )
            
            with tabs[1]:
                # Percentile rankings chart
                chart = create_percentile_chart(player_data, percentiles, selected_pos)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                
                # Overall rating
                avg_percentile = np.mean(list(percentiles.values())) if percentiles else 50
                color_class = "percentile-high" if avg_percentile >= 75 else "percentile-low" if avg_percentile <= 25 else "percentile-mid"
                
                st.markdown(f"""
                <div class="percentile-badge {color_class}">
                    Overall Rating: {avg_percentile:.0f}%
                </div>
                """, unsafe_allow_html=True)
            
            with tabs[2]:
                # Strengths and weaknesses analysis
                strengths, weaknesses, average = identify_strengths_weaknesses(percentiles)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### Strengths")
                    for metric, pct in strengths[:7]:
                        st.markdown(f'<span class="strength">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### Average")
                    for metric, pct in average[:7]:
                        st.markdown(f'<span class="neutral">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown("### Weaknesses")
                    for metric, pct in weaknesses[:7]:
                        st.markdown(f'<span class="weakness">{metric} ({pct:.0f}%)</span>', unsafe_allow_html=True)
    
    elif app_mode == "Find Similar Players":
        st.markdown('<p class="sub-header">Find Similar Players</p>', unsafe_allow_html=True)
        
        # Player selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_pos = st.selectbox("Position", positions)
        
        with col2:
            selected_comp = st.selectbox("Competition", ["All"] + competitions)
        
        with col3:
            selected_season = st.selectbox("Season", ["All"] + seasons)
        
        # Filter dataframe
        filtered_df = players_df[players_df['Primary_Position'] == selected_pos]
        if selected_comp != "All":
            filtered_df = filtered_df[filtered_df['Competition'] == selected_comp]
        if selected_season != "All":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        
        # Player selection
        player_list = filtered_df['Player'].dropna().unique()
        selected_player = st.selectbox("Select Player to Find Similar Players", sorted(player_list))
        
        # Number of similar players to find
        top_n = st.slider("Number of Similar Players to Find", min_value=5, max_value=20, value=10)
        
        if selected_player:
            # Get player data
            player_data = filtered_df[filtered_df['Player'] == selected_player].iloc[0]
            
            # Display player info
            st.markdown(f"""
            <div class="card">
                <h3>{selected_player}</h3>
                <p><strong>Team:</strong> {player_data['Squad']} | 
                <strong>Competition:</strong> {player_data['Competition']} | 
                <strong>Season:</strong> {player_data['Season']} | 
                <strong>Position:</strong> {player_data['Primary_Position']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Find similar players
            with st.spinner("Finding similar players..."):
                similar_players = find_similar_players(player_data, players_df, selected_pos, top_n)
            
            if not similar_players.empty:
                st.markdown("### Most Similar Players")
                st.dataframe(similar_players, use_container_width=True)
                
                # Create comparison with top 3 similar players
                st.markdown("### Detailed Comparison with Top Similar Players")
                
                # Get position metrics
                available_cols = [col for col in players_df.columns if 'Per 90' in col or '%' in col]
                position_metrics = get_position_metrics(selected_pos, available_cols)
                
                # Compare with top 3
                for idx, (row_idx, similar_player_row) in enumerate(similar_players.head(3).iterrows()):
                    similar_player_name = similar_player_row['Player']
                    similarity_score = similar_player_row['Similarity %']
                    
                    # Get similar player data
                    similar_player_data = players_df[
                        (players_df['Player'] == similar_player_name) &
                        (players_df['Squad'] == similar_player_row['Squad']) &
                        (players_df['Competition'] == similar_player_row['Competition']) &
                        (players_df['Season'] == similar_player_row['Season'])
                    ]
                    
                    if not similar_player_data.empty:
                        similar_data = similar_player_data.iloc[0]
                        
                        st.markdown(f"""
                        <div class="card">
                            <h4>{similar_player_name} - {similarity_score}% Similar</h4>
                            <p>{similar_player_row['Squad']} | {similar_player_row['Competition']} | {similar_player_row['Season']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Create mini comparison
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            # Key metric differences
                            st.markdown("**Key Differences:**")
                            
                            for metric in position_metrics[:5]:
                                if metric in player_data.index and metric in similar_data.index:
                                    val1 = player_data[metric]
                                    val2 = similar_data[metric]
                                    diff = val1 - val2
                                    
                                    if abs(diff) > 0.1:  # Only show significant differences
                                        metric_name = metric.replace(' Per 90', '').replace('Performance ', '')
                                        if diff > 0:
                                            st.markdown(f"➕ {metric_name}: {diff:+.2f}")
                                        else:
                                            st.markdown(f"➖ {metric_name}: {diff:+.2f}")
                        
                        with col2:
                            # Mini radar chart with unique key
                            mini_radar = create_radar_chart(player_data, similar_data, position_metrics[:8])
                            if mini_radar:
                                mini_radar.update_layout(height=300, showlegend=False)
                                st.plotly_chart(mini_radar, use_container_width=True, key=f"similar_player_radar_{idx}")
            else:
                st.warning("No similar players found. Try adjusting the filters.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    ### How to Use This Tool:
    
    1. **Player Comparison**: Compare two players side-by-side, even from different leagues and seasons
    2. **Single Player Analysis**: Deep dive into a player's performance metrics and percentile rankings
    3. **Find Similar Players**: Discover players with similar playing styles based on statistical profiles
    
    **Percentile Rankings**: Show how a player compares to others in their position (75%+ = Elite, 25%- = Below Average)
    
    **Per 90 Metrics**: All statistics are normalized to 90 minutes of play for fair comparison
    """)

if __name__ == "__main__":
    main()
