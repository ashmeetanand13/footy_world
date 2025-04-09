import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from simplified_data_loader import load_and_process_data

# Set page config
st.set_page_config(
    page_title="Football League Analyzer",
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
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #4B5563;
    }
</style>
""", unsafe_allow_html=True)

# Title and introduction
st.markdown('<p class="main-header">⚽ Football League Analyzer</p>', unsafe_allow_html=True)
st.markdown("""
This application analyzes and compares the playing styles of different football leagues across 
four key dimensions: **Attack**, **Possession**, **Passing**, and **Corner Kick Strategies**.
""")

# Load data
leagues_df, players_df, using_sample_data = load_and_process_data()

if using_sample_data:
    st.warning("Using sample data because the GitHub data could not be loaded or processed.")

# Sidebar for filtering
st.sidebar.markdown("## Filters")
selected_leagues = st.sidebar.multiselect(
    "Select Leagues to Compare",
    options=leagues_df["League"].unique(),
    default=list(leagues_df["League"].unique())
)

# Filter data based on selection
filtered_df = leagues_df[leagues_df["League"].isin(selected_leagues)]

# Add a positions analysis section if player data is available
position_analysis = st.checkbox("Show Position-Based Analysis", value=False)

if position_analysis and players_df is not None and not players_df.empty:
    st.write("Position analysis will be shown after the main analysis tabs.")

# Main analysis tabs
tab1, tab2, tab3, tab4 = st.tabs(["Attack", "Possession", "Passing", "Corners"])

with tab1:
    st.markdown('<p class="sub-header">Attack Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Shot quantity and quality
        fig = px.bar(
            filtered_df, 
            x="League", 
            y="Shots Per 90",
            color="League",
            title="Shots Per 90 Minutes by League",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Radar chart for attacking metrics
        attack_metrics = ["Shots Per 90", "Shot on Target %", "xG Per Shot", "Goals Per Shot"]
        
        # Normalize data for radar chart
        radar_df = filtered_df.copy()
        for metric in attack_metrics:
            min_val = radar_df[metric].min()
            max_val = radar_df[metric].max()
            if max_val > min_val:
                radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
            else:
                radar_df[metric] = 0.5  # Default value if no variation
        
        fig = go.Figure()
        for i, league in enumerate(radar_df["League"]):
            fig.add_trace(go.Scatterpolar(
                r=radar_df.loc[radar_df["League"] == league, attack_metrics].values[0],
                theta=attack_metrics,
                fill='toself',
                name=league
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Attack Metrics Comparison",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Shot efficiency
        fig = px.scatter(
            filtered_df,
            x="xG Per Shot",
            y="Goals Per Shot",
            size="Shots Per 90",
            color="League",
            hover_name="League",
            title="Shot Efficiency: xG vs. Actual Goals",
            labels={"xG Per Shot": "Expected Goals Per Shot", "Goals Per Shot": "Actual Goals Per Shot"},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        fig.add_shape(
            type="line", line=dict(dash="dash", width=1),
            x0=filtered_df["xG Per Shot"].min(), y0=filtered_df["xG Per Shot"].min(),
            x1=filtered_df["xG Per Shot"].max(), y1=filtered_df["xG Per Shot"].max()
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Attacking efficiency table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Shot Efficiency Ranking")
        
        efficiency_df = filtered_df.copy()
        efficiency_df["Finishing Efficiency"] = efficiency_df["Goals Per Shot"] / efficiency_df["xG Per Shot"]
        efficiency_df["Conversion Rate"] = efficiency_df["Shot on Target %"] / 100
        efficiency_df = efficiency_df.sort_values("Finishing Efficiency", ascending=False)
        
        efficiency_table = efficiency_df[["League", "Finishing Efficiency", "Conversion Rate"]]
        efficiency_table["Finishing Efficiency"] = efficiency_table["Finishing Efficiency"].map(lambda x: f"{x:.2f}x")
        efficiency_table["Conversion Rate"] = efficiency_table["Conversion Rate"].map(lambda x: f"{x:.1%}")
        
        st.dataframe(efficiency_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<p class="sub-header">Possession Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Possession percentage
        fig = px.bar(
            filtered_df, 
            x="League", 
            y="Possession %",
            color="League",
            title="Average Possession Percentage by League",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Possession metrics table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Possession Style Indicators")
        
        possession_df = filtered_df.copy()
        possession_df["Attacking Focus"] = possession_df["Touches in Attacking Third"] / possession_df["Possession %"]
        possession_df["Carry Progression"] = possession_df["Progressive Carries"] / possession_df["Possession %"] * 10
        
        possession_df = possession_df.sort_values("Possession %", ascending=False)
        possession_table = possession_df[["League", "Possession %", "Attacking Focus", "Carry Progression"]]
        
        possession_table["Possession %"] = possession_table["Possession %"].map(lambda x: f"{x:.1f}%")
        possession_table["Attacking Focus"] = possession_table["Attacking Focus"].map(lambda x: f"{x:.2f}")
        possession_table["Carry Progression"] = possession_table["Carry Progression"].map(lambda x: f"{x:.2f}")
        
        st.dataframe(possession_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Progressive carries visualization
        fig = px.scatter(
            filtered_df,
            x="Possession %",
            y="Progressive Carries",
            size="Touches in Attacking Third",
            color="League",
            hover_name="League",
            title="Possession Style: Ball Progression",
            labels={"Progressive Carries": "Progressive Carries per 90", "Possession %": "Possession Percentage"},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # League possession patterns - Radar chart
        possession_metrics = ["Possession %", "Touches in Attacking Third", "Progressive Carries"]
        
        # Normalize data for radar chart
        radar_df = filtered_df.copy()
        for metric in possession_metrics:
            min_val = radar_df[metric].min()
            max_val = radar_df[metric].max()
            if max_val > min_val:
                radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
            else:
                radar_df[metric] = 0.5  # Default value if no variation
        
        fig = go.Figure()
        for i, league in enumerate(radar_df["League"]):
            fig.add_trace(go.Scatterpolar(
                r=radar_df.loc[radar_df["League"] == league, possession_metrics].values[0],
                theta=possession_metrics,
                fill='toself',
                name=league
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Possession Metrics Comparison",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown('<p class="sub-header">Passing Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pass completion percentage
        fig = px.bar(
            filtered_df, 
            x="League", 
            y="Pass Completion %",
            color="League",
            title="Pass Completion Percentage by League",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Passing metrics table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Passing Style Analysis")
        
        passing_df = filtered_df.copy()
        passing_df["Progressive Pass Ratio"] = passing_df["Progressive Passes"] / passing_df["Pass Completion %"]
        passing_df["Key Pass Index"] = passing_df["Key Passes"] / passing_df["Pass Completion %"] * 10
        
        passing_df = passing_df.sort_values("Pass Completion %", ascending=False)
        passing_table = passing_df[["League", "Pass Completion %", "Progressive Pass Ratio", "Key Pass Index"]]
        
        passing_table["Pass Completion %"] = passing_table["Pass Completion %"].map(lambda x: f"{x:.1f}%")
        passing_table["Progressive Pass Ratio"] = passing_table["Progressive Pass Ratio"].map(lambda x: f"{x:.2f}")
        passing_table["Key Pass Index"] = passing_table["Key Pass Index"].map(lambda x: f"{x:.2f}")
        
        st.dataframe(passing_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Progressive vs Key passes
        fig = px.scatter(
            filtered_df,
            x="Pass Completion %",
            y="Progressive Passes",
            size="Key Passes",
            color="League",
            hover_name="League",
            title="Passing Style: Safety vs. Progression",
            labels={
                "Pass Completion %": "Pass Completion Rate (%)", 
                "Progressive Passes": "Progressive Passes per 90",
                "Key Passes": "Key Passes per 90"
            },
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Passing metrics - Radar chart
        passing_metrics = ["Pass Completion %", "Progressive Passes", "Key Passes"]
        
        # Normalize data for radar chart
        radar_df = filtered_df.copy()
        for metric in passing_metrics:
            min_val = radar_df[metric].min()
            max_val = radar_df[metric].max()
            if max_val > min_val:
                radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
            else:
                radar_df[metric] = 0.5  # Default value if no variation
        
        fig = go.Figure()
        for i, league in enumerate(radar_df["League"]):
            fig.add_trace(go.Scatterpolar(
                r=radar_df.loc[radar_df["League"] == league, passing_metrics].values[0],
                theta=passing_metrics,
                fill='toself',
                name=league
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Passing Metrics Comparison",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown('<p class="sub-header">Corner Kick Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Corners per match
        fig = px.bar(
            filtered_df, 
            x="League", 
            y="Corners Per Match",
            color="League",
            title="Corner Kicks Per Match by League",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Corner approach table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Corner Kick Strategies")
        
        corner_df = filtered_df.copy()
        corner_df["Corner Efficiency"] = corner_df["Corner Success Rate (%)"] / corner_df["Corners Per Match"]
        corner_df["Direct Corners %"] = 100 - corner_df["Short Corner %"]
        
        corner_df = corner_df.sort_values("Corner Success Rate (%)", ascending=False)
        corner_table = corner_df[["League", "Corners Per Match", "Corner Success Rate (%)", "Short Corner %", "Direct Corners %"]]
        
        corner_table["Corners Per Match"] = corner_table["Corners Per Match"].map(lambda x: f"{x:.1f}")
        corner_table["Corner Success Rate (%)"] = corner_table["Corner Success Rate (%)"].map(lambda x: f"{x:.1f}%")
        corner_table["Short Corner %"] = corner_table["Short Corner %"].map(lambda x: f"{x:.1f}%")
        corner_table["Direct Corners %"] = corner_table["Direct Corners %"].map(lambda x: f"{x:.1f}%")
        
        st.dataframe(corner_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Corner success vs frequency
        fig = px.scatter(
            filtered_df,
            x="Corners Per Match",
            y="Corner Success Rate (%)",
            size="Short Corner %",
            color="League",
            hover_name="League",
            title="Corner Kick Effectiveness",
            labels={
                "Corners Per Match": "Corners Per Match", 
                "Corner Success Rate (%)": "Success Rate (%)",
                "Short Corner %": "Short Corner Usage (%)"
            },
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Corner metrics - Radar chart
        corner_metrics = ["Corners Per Match", "Corner Success Rate (%)", "Short Corner %"]
        
        # Normalize data for radar chart
        radar_df = filtered_df.copy()
        for metric in corner_metrics:
            min_val = radar_df[metric].min()
            max_val = radar_df[metric].max()
            if max_val > min_val:
                radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
            else:
                radar_df[metric] = 0.5  # Default value if no variation
        
        fig = go.Figure()
        for i, league in enumerate(radar_df["League"]):
            fig.add_trace(go.Scatterpolar(
                r=radar_df.loc[radar_df["League"] == league, corner_metrics].values[0],
                theta=corner_metrics,
                fill='toself',
                name=league
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Corner Metrics Comparison",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

# Summary section
st.markdown('<p class="sub-header">League Style Summary</p>', unsafe_allow_html=True)

# Create a summary dataframe with league archetypes
summary_df = filtered_df.copy()

# Determine archetypal characteristics
summary_df["Attack Style"] = np.where(
    summary_df["xG Per Shot"] > summary_df["xG Per Shot"].mean(),
    "Quality Chances",
    "High Volume"
)

summary_df["Possession Approach"] = np.where(
    summary_df["Progressive Carries"] > summary_df["Progressive Carries"].mean(),
    "Progressive",
    "Conservative"
)

summary_df["Passing Identity"] = np.where(
    summary_df["Key Passes"] > summary_df["Key Passes"].mean(),
    "Creative",
    "Safe"
)

summary_df["Set Piece Emphasis"] = np.where(
    summary_df["Corner Success Rate (%)"] > summary_df["Corner Success Rate (%)"].mean(),
    "Set Piece Focused",
    "Open Play Focused"
)

# Display style summary
style_summary = summary_df[["League", "Attack Style", "Possession Approach", "Passing Identity", "Set Piece Emphasis"]]
st.dataframe(style_summary, use_container_width=True)

# League comparison chart (overall style visualization)
st.markdown("### Overall League Style Comparison")

# Create a normalized dataframe for overall comparison
comparison_metrics = [
    "Shots Per 90", "xG Per Shot", "Possession %", 
    "Progressive Carries", "Pass Completion %", "Key Passes",
    "Corners Per Match", "Corner Success Rate (%)"
]

compare_df = filtered_df.copy()
for metric in comparison_metrics:
    min_val = compare_df[metric].min()
    max_val = compare_df[metric].max()
    if max_val > min_val:
        compare_df[metric] = (compare_df[metric] - min_val) / (max_val - min_val)
    else:
        compare_df[metric] = 0.5  # Default value if no variation

# Heatmap of normalized values
fig = px.imshow(
    compare_df.set_index('League')[comparison_metrics],
    labels=dict(x="Metric", y="League", color="Normalized Value"),
    x=comparison_metrics,
    y=compare_df["League"],
    color_continuous_scale="Blues",
    title="League Style Heatmap (Normalized Values)"
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# Position-based analysis section
if position_analysis and players_df is not None and not players_df.empty:
    st.markdown('<p class="sub-header">Position-Based Analysis</p>', unsafe_allow_html=True)
    
    # Filter to selected leagues
    filtered_players = players_df[players_df["Competition"].isin(selected_leagues)]
    
    if not filtered_players.empty and "Pos" in filtered_players.columns:
        # Position distribution by league
        st.markdown("### Position Distribution by League")
        
        # Make sure position is standardized
        if "Pos" in filtered_players.columns:
            # Extract the first position for players with multiple positions (e.g., "FW,MF" becomes "FW")
            filtered_players["Primary Position"] = filtered_players["Pos"].apply(lambda x: x.split(',')[0] if isinstance(x, str) and ',' in x else x)
            
            # Count players by position and league
            position_counts = filtered_players.groupby(["Competition", "Primary Position"]).size().reset_index(name="Count")
            
            # Plot position distribution
            fig = px.bar(
                position_counts,
                x="Primary Position",
                y="Count",
                color="Competition",
                barmode="group",
                title="Player Position Distribution by League",
                labels={"Primary Position": "Position", "Count": "Number of Players"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Position performance metrics by league
            st.markdown("### Position Performance by League")
            
            # Select metric for comparison
            available_metrics = [col for col in ["Performance Gls", "Performance Ast", "Total Cmp%", "PrgP", "Carries PrgC"] 
                              if col in filtered_players.columns]
            
            if available_metrics:
                performance_metric = st.selectbox(
                    "Select Performance Metric",
                    options=available_metrics,
                    index=0
                )
                
                # Calculate average metric by position and league
                perf_by_pos = filtered_players.groupby(["Competition", "Primary Position"])[performance_metric].mean().reset_index()
                
                # Plot performance by position
                fig = px.bar(
                    perf_by_pos,
                    x="Primary Position",
                    y=performance_metric,
                    color="Competition",
                    barmode="group",
                    title=f"Average {performance_metric} by Position and League",
                    labels={"Primary Position": "Position"},
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No performance metrics available in the data.")
    else:
        st.warning("No position data available for the selected leagues.")

# Footer with instructions
st.markdown("""
---
### How to use this analyzer:

1. The app automatically loads football data from GitHub
2. Select specific leagues to compare using the dropdown menu in the sidebar
3. Navigate through the tabs to explore different aspects of playing styles:
   - Attack: Shot volume, efficiency, and expected goals analysis
   - Possession: Ball retention and progression metrics
   - Passing: Passing style and creativity analysis  
   - Corners: Set piece strategies and effectiveness
4. Enable the position-based analysis for more detailed insights by position

**Data Source**: This application uses data from a GitHub repository at:
https://github.com/ashmeetanand13/footy_world/blob/main/df_clean.csv

**Note**: If the GitHub data cannot be loaded properly, the application will use sample data instead.
""")
