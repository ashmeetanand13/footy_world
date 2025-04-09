
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_and_process_data

# Set page config
st.set_page_config(
    page_title="Advanced Football League Analyzer",
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
    .info-box {
        background-color: #e3f2fd;
        border-left: 5px solid #1976d2;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
    }
    .tab-subheader {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2E5AAC;
        margin: 1rem 0 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title and introduction
st.markdown('<p class="main-header">⚽ Advanced Football League Analyzer</p>', unsafe_allow_html=True)
st.markdown("""
This application provides in-depth analysis and comparison of different football leagues across 
multiple dimensions: **Attack**, **Defense**, **Possession**, **Passing**, **Corner Kicks**,
**Player Impact**, and **Efficiency Metrics**.
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
    default=list(leagues_df["League"].unique())[:3]  # Default to first 3 leagues to avoid visual clutter
)

# Filter data based on selection
filtered_df = leagues_df[leagues_df["League"].isin(selected_leagues)]

# Add analysis options
st.sidebar.markdown("## Analysis Options")
show_advanced = st.sidebar.checkbox("Show Advanced Metrics", value=False)
position_analysis = st.sidebar.checkbox("Show Position-Based Analysis", value=False)
efficiency_analysis = st.sidebar.checkbox("Show Efficiency Analysis", value=False)
composite_analysis = st.sidebar.checkbox("Show Composite Metrics", value=False)

# Main analysis tabs
tabs = ["Attack", "Defense", "Possession", "Passing", "Corners"]

if show_advanced:
    tabs.extend(["Player Impact", "Efficiency"])

if composite_analysis:
    tabs.append("Composite")

main_tabs = st.tabs(tabs)

# 1. ATTACK ANALYSIS TAB
with main_tabs[0]:
    st.markdown('<p class="sub-header">Attack Analysis</p>', unsafe_allow_html=True)
    
    # Basic attack metrics
    st.markdown('<p class="tab-subheader">Shot Quantity & Quality</p>', unsafe_allow_html=True)
    
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
        # Add diagonal line (where G = xG)
        fig.add_shape(
            type="line", line=dict(dash="dash", width=1),
            x0=filtered_df["xG Per Shot"].min(), y0=filtered_df["xG Per Shot"].min(),
            x1=filtered_df["xG Per Shot"].max(), y1=filtered_df["xG Per Shot"].max()
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Shooting metrics table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Shot Efficiency Metrics")
        
        efficiency_df = filtered_df.copy()
        # Calculate shooting metrics not already in the dataframe
        if 'Finishing Efficiency' not in efficiency_df.columns:
            efficiency_df["Finishing Efficiency"] = efficiency_df["Goals Per Shot"] / efficiency_df["xG Per Shot"]
        
        efficiency_df = efficiency_df.sort_values("Finishing Efficiency", ascending=False)
        
        # Select relevant columns
        shooting_cols = [
            "League", "Shots Per 90", "Shot on Target %", "Goals Per Shot", 
            "Goals per SoT", "xG Per Shot", "Finishing Efficiency", "G-xG"
        ]
        
        # Filter for available columns
        available_shooting_cols = [col for col in shooting_cols if col in efficiency_df.columns]
        
        # Format the table values
        shooting_table = efficiency_df[available_shooting_cols].copy()
        
        # Format specific columns
        if "Finishing Efficiency" in shooting_table.columns:
            shooting_table["Finishing Efficiency"] = shooting_table["Finishing Efficiency"].map(lambda x: f"{x:.2f}x")
        
        if "Shot on Target %" in shooting_table.columns:
            shooting_table["Shot on Target %"] = shooting_table["Shot on Target %"].map(lambda x: f"{x:.1f}%")
        
        if "G-xG" in shooting_table.columns:
            shooting_table["G-xG"] = shooting_table["G-xG"].map(lambda x: f"{x:+.1f}")
        
        st.dataframe(shooting_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Radar chart for attacking metrics
        attack_metrics = [
            "Shots Per 90", "Shot on Target %", "xG Per Shot", 
            "Goals Per Shot", "Goals per SoT"
        ]
        
        # Filter for available metrics
        available_attack_metrics = [metric for metric in attack_metrics if metric in filtered_df.columns]
        
        if len(available_attack_metrics) >= 3:  # Need at least 3 metrics for a meaningful radar
            # Normalize data for radar chart
            radar_df = filtered_df.copy()
            for metric in available_attack_metrics:
                min_val = radar_df[metric].min()
                max_val = radar_df[metric].max()
                if max_val > min_val:
                    radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                else:
                    radar_df[metric] = 0.5  # Default value if no variation
            
            fig = go.Figure()
            for i, league in enumerate(radar_df["League"]):
                fig.add_trace(go.Scatterpolar(
                    r=radar_df.loc[radar_df["League"] == league, available_attack_metrics].values[0],
                    theta=available_attack_metrics,
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

# 3. POSSESSION ANALYSIS TAB
with main_tabs[2]:
    st.markdown('<p class="sub-header">Possession Analysis</p>', unsafe_allow_html=True)
    
    # Basic possession metrics
    st.markdown('<p class="tab-subheader">Ball Retention & Distribution</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Possession percentage
        if "Possession %" in filtered_df.columns:
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
        
        # Touch distribution breakdown
        touch_zones = ["Def 3rd Touch %", "Mid 3rd Touch %", "Att 3rd Touch %", "Att Pen Touch %", "Def Pen Touch %"]
        available_zones = [zone for zone in touch_zones if zone in filtered_df.columns]
        
        if len(available_zones) >= 3:
            # Create a new dataframe for the stacked bar chart
            zones_df = filtered_df[["League"] + available_zones].copy()
            
            # Melt the dataframe for the stacked bar chart
            zones_melted = pd.melt(
                zones_df, 
                id_vars=["League"], 
                value_vars=available_zones,
                var_name="Zone", 
                value_name="Percentage"
            )
            
            # Clean up the zone names
            zones_melted["Zone"] = zones_melted["Zone"].str.replace(" Touch %", "")
            
            # Create the stacked bar chart
            fig = px.bar(
                zones_melted,
                x="League",
                y="Percentage",
                color="Zone",
                title="Touch Distribution by Field Zone",
                labels={"Percentage": "Percentage of Touches"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Progressive carries
        if "Progressive Carries Per 90" in filtered_df.columns:
            y_col = "Progressive Carries Per 90"
            title = "Progressive Carries Per 90 Minutes by League"
            
            fig = px.bar(
                filtered_df, 
                x="League", 
                y=y_col,
                color="League",
                title=title,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Possession metrics table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Ball Progression Metrics")
        
        progression_cols = [
            "League", "Progressive Carries Per 90", "Carries into Final Third Per 90",
            "Carries into Box Per 90", "Progressive Passes Received Per 90"
        ]
        
        # Filter for available columns
        available_prog_cols = [col for col in progression_cols if col in filtered_df.columns]
        
        # Format the table
        prog_table = filtered_df[available_prog_cols].copy()
        
        # Format numeric columns
        for col in available_prog_cols:
            if col != "League":
                prog_table[col] = prog_table[col].map(lambda x: f"{x:.1f}")
        
        st.dataframe(prog_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Ball retention metrics
    if any(col in filtered_df.columns for col in ["Carry Success %", "Take-On Success %", "Miscontrols per 100 Touches", "Dispossessed per 100 Touches"]):
        st.markdown('<p class="tab-subheader">Ball Retention & Take-Ons</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Carry success percentage
            if "Carry Success %" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="Carry Success %",
                    color="League",
                    title="Carry Success Rate by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Take-on success
            if "Take-On Success %" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="Take-On Success %",
                    color="League",
                    title="Take-On Success Rate by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Ball loss metrics
        ball_loss_metrics = ["Miscontrols per 100 Touches", "Dispossessed per 100 Touches"]
        available_loss_metrics = [col for col in ball_loss_metrics if col in filtered_df.columns]
        
        if available_loss_metrics:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### Ball Loss Metrics")
            
            # Format the table
            loss_table = filtered_df[["League"] + available_loss_metrics].copy()
            
            # Format numeric columns
            for col in available_loss_metrics:
                loss_table[col] = loss_table[col].map(lambda x: f"{x:.2f}")
            
            st.dataframe(loss_table, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# 5. CORNER KICKS ANALYSIS TAB
with main_tabs[4]:
    st.markdown('<p class="sub-header">Corner Kick Analysis</p>', unsafe_allow_html=True)
    
    # Basic corner metrics
    st.markdown('<p class="tab-subheader">Corner Frequency & Success</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Corners per match
        if "Corners Per Match" in filtered_df.columns:
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
        
        # Corner success rate
        if "Corner Success Rate (%)" in filtered_df.columns:
            fig = px.bar(
                filtered_df, 
                x="League", 
                y="Corner Success Rate (%)",
                color="League",
                title="Corner Success Rate by League",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Corner approach table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Corner Kick Strategies")
        
        corner_cols = [
            "League", "Corners Per Match", "Corner Success Rate (%)", 
            "Direct Corners %", "In Corner %", "Out Corner %", "Str Corner %"
        ]
        
        # Filter for available columns
        available_corner_cols = [col for col in corner_cols if col in filtered_df.columns]
        
        # Format the table
        corner_table = filtered_df[available_corner_cols].copy()
        
        # Format columns
        for col in available_corner_cols:
            if col != "League":
                if "%" in col:
                    corner_table[col] = corner_table[col].map(lambda x: f"{x:.1f}%")
                else:
                    corner_table[col] = corner_table[col].map(lambda x: f"{x:.1f}")
        
        st.dataframe(corner_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Corner types breakdown
        corner_types = ["In Corner %", "Out Corner %", "Str Corner %"]
        available_types = [col for col in corner_types if col in filtered_df.columns]
        
        if len(available_types) >= 2:
            # Create a new dataframe for the stacked bar chart
            types_df = filtered_df[["League"] + available_types].copy()
            
            # Melt the dataframe for the stacked bar chart
            types_melted = pd.melt(
                types_df, 
                id_vars=["League"], 
                value_vars=available_types,
                var_name="Corner Type", 
                value_name="Percentage"
            )
            
            # Clean up the type names
            types_melted["Corner Type"] = types_melted["Corner Type"].str.replace(" Corner %", "")
            
            # Create the stacked bar chart
            fig = px.bar(
                types_melted,
                x="League",
                y="Percentage",
                color="Corner Type",
                title="Corner Kick Types Distribution",
                labels={"Percentage": "Percentage of Corners"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # Corner effectiveness
    if "Corner to Shot %" in filtered_df.columns:
        st.markdown('<p class="tab-subheader">Corner Effectiveness</p>', unsafe_allow_html=True)
        
        # Corner effectiveness metrics
        effectiveness_cols = ["League", "Corner to Shot %", "Corner Success Rate (%)"]
        
        # Filter for available columns
        available_effect_cols = [col for col in effectiveness_cols if col in filtered_df.columns]
        
        if len(available_effect_cols) > 1:  # Need league plus at least one metric
            # Format the table
            effect_table = filtered_df[available_effect_cols].copy()
            
            # Format percentage columns
            for col in available_effect_cols:
                if col != "League" and "%" in col:
                    effect_table[col] = effect_table[col].map(lambda x: f"{x:.1f}%")
            
            st.dataframe(effect_table, use_container_width=True)
    
    # Advanced corner analysis
    if show_advanced:
        # Corner radar chart
        corner_metrics = [
            "Corners Per Match", "Corner Success Rate (%)", "Direct Corners %"
        ]
        
        # Filter for available metrics
        available_corner_metrics = [metric for metric in corner_metrics if metric in filtered_df.columns]
        
        if len(available_corner_metrics) >= 3:  # Need at least 3 metrics for a meaningful radar
            # Normalize data for radar chart
            radar_df = filtered_df.copy()
            for metric in available_corner_metrics:
                min_val = radar_df[metric].min()
                max_val = radar_df[metric].max()
                if max_val > min_val:
                    radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                else:
                    radar_df[metric] = 0.5  # Default value if no variation
            
            fig = go.Figure()
            for i, league in enumerate(radar_df["League"]):
                fig.add_trace(go.Scatterpolar(
                    r=radar_df.loc[radar_df["League"] == league, available_corner_metrics].values[0],
                    theta=available_corner_metrics,
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
    
    # Advanced possession metrics
    if show_advanced:
        st.markdown('<p class="tab-subheader">Advanced Possession Metrics</p>', unsafe_allow_html=True)
        
        # Possession radar chart
        possession_metrics = [
            "Possession %", "Progressive Carries Per 90", "Progressive Carry %",
            "Take-On Success %", "Carry Success %"
        ]
        
        # Filter for available metrics
        available_poss_metrics = [metric for metric in possession_metrics if metric in filtered_df.columns]
        
        if len(available_poss_metrics) >= 3:  # Need at least 3 metrics for a meaningful radar
            # Normalize data for radar chart
            radar_df = filtered_df.copy()
            for metric in available_poss_metrics:
                min_val = radar_df[metric].min()
                max_val = radar_df[metric].max()
                if max_val > min_val:
                    radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                else:
                    radar_df[metric] = 0.5  # Default value if no variation
            
            fig = go.Figure()
            for i, league in enumerate(radar_df["League"]):
                fig.add_trace(go.Scatterpolar(
                    r=radar_df.loc[radar_df["League"] == league, available_poss_metrics].values[0],
                    theta=available_poss_metrics,
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
        
        # Take-on metrics
        take_on_metrics = ["Take-Ons Per 90", "Successful Take-Ons Per 90", "Take-On Success %"]
        available_take_on = [col for col in take_on_metrics if col in filtered_df.columns]
        
        if len(available_take_on) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                if "Take-Ons Per 90" in available_take_on:
                    fig = px.bar(
                        filtered_df, 
                        x="League", 
                        y="Take-Ons Per 90",
                        color="League",
                        title="Take-On Attempts Per 90 Minutes by League",
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

# 4. PASSING ANALYSIS TAB
with main_tabs[3]:
    st.markdown('<p class="sub-header">Passing Analysis</p>', unsafe_allow_html=True)
    
    # Basic passing metrics
    st.markdown('<p class="tab-subheader">Pass Completion & Distribution</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pass completion percentage
        if "Pass Completion %" in filtered_df.columns:
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
        
        # Pass distance distribution
        pass_distance_metrics = ["Short Pass Completion %", "Medium Pass Completion %", "Long Pass Completion %"]
        available_distance = [col for col in pass_distance_metrics if col in filtered_df.columns]
        
        if len(available_distance) >= 2:
            # Create a new dataframe for the bar chart
            distance_df = filtered_df[["League"] + available_distance].copy()
            
            # Melt the dataframe for grouped bar chart
            distance_melted = pd.melt(
                distance_df, 
                id_vars=["League"], 
                value_vars=available_distance,
                var_name="Pass Type", 
                value_name="Completion %"
            )
            
            # Clean up the type names
            distance_melted["Pass Type"] = distance_melted["Pass Type"].str.replace(" Completion %", "")
            
            # Create the grouped bar chart
            fig = px.bar(
                distance_melted,
                x="League",
                y="Completion %",
                color="Pass Type",
                barmode="group",
                title="Pass Completion % by Distance",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Progressive passing
        if "Progressive Passes Per 90" in filtered_df.columns:
            fig = px.bar(
                filtered_df, 
                x="League", 
                y="Progressive Passes Per 90",
                color="League",
                title="Progressive Passes Per 90 Minutes by League",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Key passing metrics table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Creative Passing Metrics")
        
        creative_cols = [
            "League", "Key Passes Per 90", "xA Per 90", "xAG Per 90", "SCA Per 90"
        ]
        
        # Filter for available columns
        available_creative = [col for col in creative_cols if col in filtered_df.columns]
        
        # Format the table
        creative_table = filtered_df[available_creative].copy()
        
        # Format numeric columns
        for col in available_creative:
            if col != "League":
                creative_table[col] = creative_table[col].map(lambda x: f"{x:.2f}")
        
        st.dataframe(creative_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Passing efficiency metrics
    if any(col in filtered_df.columns for col in ["Progressive Pass %", "Key Pass %", "Progressive Pass Ratio"]):
        st.markdown('<p class="tab-subheader">Passing Efficiency & Creation</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Efficiency scatter plot
            if all(col in filtered_df.columns for col in ["Pass Completion %", "Progressive Passes Per 90"]):
                size_col = "Key Passes Per 90" if "Key Passes Per 90" in filtered_df.columns else None
                
                fig = px.scatter(
                    filtered_df,
                    x="Pass Completion %",
                    y="Progressive Passes Per 90",
                    size=size_col,
                    color="League",
                    hover_name="League",
                    title="Passing Style: Safety vs. Progression",
                    labels={
                        "Pass Completion %": "Pass Completion Rate (%)", 
                        "Progressive Passes Per 90": "Progressive Passes per 90"
                    },
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=450)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Passing efficiency metrics table
            efficiency_cols = [
                "League", "Progressive Pass %", "Key Pass %", "Progressive Pass Ratio"
            ]
            
            # Filter for available columns
            available_efficiency = [col for col in efficiency_cols if col in filtered_df.columns]
            
            if available_efficiency:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Pass Efficiency Metrics")
                
                # Format the table
                efficiency_table = filtered_df[available_efficiency].copy()
                
                # Format percentage columns
                for col in available_efficiency:
                    if col != "League" and "%" in col:
                        efficiency_table[col] = efficiency_table[col].map(lambda x: f"{x:.1f}%")
                    elif col != "League":
                        efficiency_table[col] = efficiency_table[col].map(lambda x: f"{x:.2f}")
                
                st.dataframe(efficiency_table, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # SCA metrics if available
            if "SCA Per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="SCA Per 90",
                    color="League",
                    title="Shot-Creating Actions Per 90 Minutes by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=450)
                st.plotly_chart(fig, use_container_width=True)
    
    # Advanced passing metrics
    if show_advanced:
        st.markdown('<p class="tab-subheader">Advanced Passing Metrics</p>', unsafe_allow_html=True)
        
        # SCA Types breakdown (if available)
        sca_types = [col for col in filtered_df.columns if col.startswith("SCA ") and col.endswith(" %")]
        
        if sca_types and len(sca_types) >= 2:
            st.markdown("### Shot Creating Actions Breakdown by Type")
            
            # Create a new dataframe for the stacked bar chart
            sca_breakdown = filtered_df[["League"] + sca_types].copy()
            
            # Melt the dataframe for the stacked bar chart
            sca_melted = pd.melt(
                sca_breakdown, 
                id_vars=["League"], 
                value_vars=sca_types,
                var_name="SCA Type", 
                value_name="Percentage"
            )
            
            # Clean up the type names
            sca_melted["SCA Type"] = sca_melted["SCA Type"].str.replace("SCA ", "").str.replace(" %", "")
            
            # Create the stacked bar chart
            fig = px.bar(
                sca_melted,
                x="League",
                y="Percentage",
                color="SCA Type",
                title="Shot Creating Actions Breakdown by Type",
                labels={"Percentage": "Percentage of SCAs"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Passing radar chart
        passing_metrics = [
            "Pass Completion %", "Progressive Passes Per 90", "Key Passes Per 90",
            "xA Per 90", "SCA Per 90"
        ]
        
        # Filter for available metrics
        available_pass_metrics = [metric for metric in passing_metrics if metric in filtered_df.columns]
        
        if len(available_pass_metrics) >= 3:  # Need at least 3 metrics for a meaningful radar
            # Normalize data for radar chart
            radar_df = filtered_df.copy()
            for metric in available_pass_metrics:
                min_val = radar_df[metric].min()
                max_val = radar_df[metric].max()
                if max_val > min_val:
                    radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                else:
                    radar_df[metric] = 0.5  # Default value if no variation
            
            fig = go.Figure()
            for i, league in enumerate(radar_df["League"]):
                fig.add_trace(go.Scatterpolar(
                    r=radar_df.loc[radar_df["League"] == league, available_pass_metrics].values[0],
                    theta=available_pass_metrics,
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
        
        # Assist metrics
        if "A-xA" in filtered_df.columns:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### Assist vs Expected Assist Analysis")
            
            # Format the table
            assist_table = filtered_df[["League", "A-xA"]].copy()
            assist_table["A-xA"] = assist_table["A-xA"].map(lambda x: f"{x:+.2f}")
            
            st.dataframe(assist_table, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if "Successful Take-Ons Per 90" in available_take_on:
                    fig = px.bar(
                        filtered_df, 
                        x="League", 
                        y="Successful Take-Ons Per 90",
                        color="League",
                        title="Successful Take-Ons Per 90 Minutes by League",
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

# 2. DEFENSE ANALYSIS TAB
with main_tabs[1]:
    st.markdown('<p class="sub-header">Defense Analysis</p>', unsafe_allow_html=True)
    
    # Basic defensive metrics
    st.markdown('<p class="tab-subheader">Ball Recovery & Defensive Actions</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tackles per 90
        if "Tackles Per 90" in filtered_df.columns:
            fig = px.bar(
                filtered_df, 
                x="League", 
                y="Tackles Per 90",
                color="League",
                title="Tackles Per 90 Minutes by League",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Defense metrics table
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Defensive Actions Per 90 Minutes")
        
        defense_cols = [
            "League", "Tackles Per 90", "Interceptions Per 90", 
            "Blocks Per 90", "Clearances Per 90", "Tackles+Interceptions Per 90"
        ]
        
        # Filter for available columns
        available_defense_cols = [col for col in defense_cols if col in filtered_df.columns]
        
        # Format the table
        defense_table = filtered_df[available_defense_cols].copy()
        
        # Format numeric columns
        for col in available_defense_cols:
            if col != "League":
                defense_table[col] = defense_table[col].map(lambda x: f"{x:.1f}")
        
        st.dataframe(defense_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Defensive actions scatter plot
        if all(col in filtered_df.columns for col in ["Tackles Per 90", "Interceptions Per 90"]):
            size_col = "Blocks Per 90" if "Blocks Per 90" in filtered_df.columns else None
            
            fig = px.scatter(
                filtered_df,
                x="Tackles Per 90",
                y="Interceptions Per 90",
                size=size_col,
                color="League",
                hover_name="League",
                title="Defensive Style: Tackles vs Interceptions",
                labels={
                    "Tackles Per 90": "Tackles Per 90 Minutes", 
                    "Interceptions Per 90": "Interceptions Per 90 Minutes"
                },
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Defense success metrics
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Defensive Success Metrics")
        
        success_cols = [
            "League", "Tackle Success %", "Aerial Duels Won %", 
            "Pressure Success %", "Errors Per 90"
        ]
        
        # Filter for available columns
        available_success_cols = [col for col in success_cols if col in filtered_df.columns]
        
        # Format the table
        success_table = filtered_df[available_success_cols].copy()
        
        # Format percentage columns
        for col in available_success_cols:
            if col != "League":
                if "%" in col:
                    success_table[col] = success_table[col].map(lambda x: f"{x:.1f}%")
                else:
                    success_table[col] = success_table[col].map(lambda x: f"{x:.2f}")
        
        st.dataframe(success_table, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Defensive positioning
    if any(col in filtered_df.columns for col in ["Def 3rd Tackles %", "Mid 3rd Tackles %", "Att 3rd Tackles %"]):
        st.markdown('<p class="tab-subheader">Defensive Positioning & Style</p>', unsafe_allow_html=True)
        
        # Defensive positioning breakdown
        tackle_zones = ["Def 3rd Tackles %", "Mid 3rd Tackles %", "Att 3rd Tackles %"]
        available_zones = [zone for zone in tackle_zones if zone in filtered_df.columns]
        
        if available_zones:
            # Create a new dataframe for the stacked bar chart
            zones_df = filtered_df[["League"] + available_zones].copy()
            
            # Melt the dataframe for the stacked bar chart
            zones_melted = pd.melt(
                zones_df, 
                id_vars=["League"], 
                value_vars=available_zones,
                var_name="Zone", 
                value_name="Percentage"
            )
            
            # Clean up the zone names
            zones_melted["Zone"] = zones_melted["Zone"].str.replace(" Tackles %", "")
            
            # Create the stacked bar chart
            fig = px.bar(
                zones_melted,
                x="League",
                y="Percentage",
                color="Zone",
                title="Tackle Distribution by Field Zone",
                labels={"Percentage": "Percentage of Tackles"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    
    # Advanced defensive metrics
    if show_advanced and "Pressing Intensity" in filtered_df.columns:
        st.markdown('<p class="tab-subheader">Pressing & Recoveries</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pressing intensity
            fig = px.bar(
                filtered_df, 
                x="League", 
                y="Pressing Intensity",
                color="League",
                title="Pressing Intensity Index by League",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Recoveries per 90 (if available)
            if "Recoveries Per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="Recoveries Per 90",
                    color="League",
                    title="Ball Recoveries Per 90 Minutes by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Defense radar chart
        defense_metrics = [
            "Tackles Per 90", "Interceptions Per 90", "Blocks Per 90", 
            "Tackle Success %", "Pressure Success %"
        ]
        
        # Filter for available metrics
        available_defense_metrics = [metric for metric in defense_metrics if metric in filtered_df.columns]
        
        if len(available_defense_metrics) >= 3:  # Need at least 3 metrics for a meaningful radar
            # Normalize data for radar chart
            radar_df = filtered_df.copy()
            for metric in available_defense_metrics:
                min_val = radar_df[metric].min()
                max_val = radar_df[metric].max()
                if max_val > min_val:
                    radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                else:
                    radar_df[metric] = 0.5  # Default value if no variation
            
            fig = go.Figure()
            for i, league in enumerate(radar_df["League"]):
                fig.add_trace(go.Scatterpolar(
                    r=radar_df.loc[radar_df["League"] == league, available_defense_metrics].values[0],
                    theta=available_defense_metrics,
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
                title="Defensive Metrics Comparison",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Advanced attack metrics (if available)
    if show_advanced:
        st.markdown('<p class="tab-subheader">Advanced Attack Metrics</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Goal creation actions
            if "GCA Per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="GCA Per 90",
                    color="League",
                    title="Goal-Creating Actions Per 90 Minutes by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Non-penalty goals (if available)
            if "Non-Penalty Goals Per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="Non-Penalty Goals Per 90",
                    color="League",
                    title="Non-Penalty Goals Per 90 Minutes by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Penalty conversion (if available)
            if "Penalty Conversion %" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="Penalty Conversion %",
                    color="League",
                    title="Penalty Conversion Rate by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Box penetration metrics
            box_metrics = ["Box Touches %", "Carries into Box Per 90", "Passes into Box Per 90"]
            available_box_metrics = [col for col in box_metrics if col in filtered_df.columns]
            
            if available_box_metrics:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Box Penetration Metrics")
                
                # Prepare the data
                box_df = filtered_df[["League"] + available_box_metrics].copy()
                
                # Format values
                for col in available_box_metrics:
                    if "%" in col:
                        box_df[col] = box_df[col].map(lambda x: f"{x:.1f}%")
                    else:
                        box_df[col] = box_df[col].map(lambda x: f"{x:.2f}")
                
                st.dataframe(box_df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # GCA Types breakdown (if available)
        gca_types = [col for col in filtered_df.columns if col.startswith("GCA ") and col.endswith(" %")]
        
        if gca_types and len(gca_types) >= 2:
            st.markdown("### Goal Creating Actions Breakdown by Type")
            
            # Create a new dataframe for the stacked bar chart
            gca_breakdown = filtered_df[["League"] + gca_types].copy()
            
            # Melt the dataframe for the stacked bar chart
            gca_melted = pd.melt(
                gca_breakdown, 
                id_vars=["League"], 
                value_vars=gca_types,
                var_name="GCA Type", 
                value_name="Percentage"
            )
            
            # Clean up the type names
            gca_melted["GCA Type"] = gca_melted["GCA Type"].str.replace("GCA ", "").str.replace(" %", "")
            
            # Create the stacked bar chart
            fig = px.bar(
                gca_melted,
                x="League",
                y="Percentage",
                color="GCA Type",
                title="Goal Creating Actions Breakdown by Type",
                labels={"Percentage": "Percentage of GCAs"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
# Conditional tabs for advanced metrics
if show_advanced and len(tabs) > 5:
    # 6. PLAYER IMPACT METRICS TAB
    with main_tabs[5]:
        st.markdown('<p class="sub-header">Player Impact Analysis</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
        This section analyzes how players in different leagues impact their team's performance metrics 
        when they are on vs. off the field. Higher values indicate players who have a stronger positive 
        influence on team results.
        </div>
        """, unsafe_allow_html=True)
        
        # Team performance metrics
        st.markdown('<p class="tab-subheader">Team Performance with Player</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Plus-minus per 90
            if "+/- per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="+/- per 90",
                    color="League",
                    title="Goal Difference Per 90 Minutes With Player",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            # On-Off differential
            if "On-Off +/-" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="On-Off +/-",
                    color="League",
                    title="On-Off Goal Difference by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # xG differential per 90
            if "xG +/- per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="xG +/- per 90",
                    color="League",
                    title="xG Difference Per 90 Minutes With Player",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            # xG On-Off differential
            if "xG On-Off" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="xG On-Off",
                    color="League",
                    title="On-Off xG Difference by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
        
        # Combined contribution metrics
        st.markdown('<p class="tab-subheader">Combined Contribution Metrics</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Goals + Assists per 90
            if "G+A Per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="G+A Per 90",
                    color="League",
                    title="Goals + Assists Per 90 Minutes by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Expected Goals + Assists per 90
            if "xG+xA Per 90" in filtered_df.columns:
                fig = px.bar(
                    filtered_df, 
                    x="League", 
                    y="xG+xA Per 90",
                    color="League",
                    title="Expected Goals + Assists Per 90 Minutes by League",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
        
        # Impact metrics table
        impact_cols = [
            "League", "G+A Per 90", "G+A-PK Per 90", "xG+xA Per 90", "npxG+xA Per 90",
            "+/- per 90", "On-Off +/-", "xG +/- per 90", "xG On-Off", "Points per Match"
        ]
        
        # Filter for available columns
        available_impact_cols = [col for col in impact_cols if col in filtered_df.columns]
        
        if len(available_impact_cols) > 1:  # Need league plus at least one metric
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### Player Impact Metrics by League")
            
            # Format the table
            impact_table = filtered_df[available_impact_cols].copy()
            
            # Format columns
            for col in available_impact_cols:
                if col != "League":
                    impact_table[col] = impact_table[col].map(lambda x: f"{x:.2f}")
            
            st.dataframe(impact_table, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # 7. EFFICIENCY METRICS TAB
    if efficiency_analysis or (show_advanced and len(tabs) > 6):
        with main_tabs[6 if show_advanced else 5]:
            st.markdown('<p class="sub-header">Efficiency Metrics Analysis</p>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
            This section focuses on efficiency metrics that show how effectively teams use their 
            possession, passes, and carries to create meaningful output. Higher values indicate 
            more efficient use of resources.
            </div>
            """, unsafe_allow_html=True)
            
            # Per touch efficiency
            st.markdown('<p class="tab-subheader">Per-Touch Efficiency</p>', unsafe_allow_html=True)
            
            touch_cols = [
                "League", "Goal Impact per 100 Touches", "xG+xA per 100 Touches", "SCA per 100 Touches"
            ]
            
            # Filter for available columns
            available_touch_cols = [col for col in touch_cols if col in filtered_df.columns]
            
            if len(available_touch_cols) > 1:  # Need league plus at least one metric
                col1, col2 = st.columns(2)
                
                with col1:
                    # Goal impact per 100 touches
                    if "Goal Impact per 100 Touches" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Goal Impact per 100 Touches",
                            color="League",
                            title="Goal Impact per 100 Touches by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # xG+xA per 100 touches
                    if "xG+xA per 100 Touches" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="xG+xA per 100 Touches",
                            color="League",
                            title="Expected Goals + Assists per 100 Touches by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Touch efficiency table
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Touch Efficiency Metrics")
                
                # Format the table
                touch_table = filtered_df[available_touch_cols].copy()
                
                # Format columns
                for col in available_touch_cols:
                    if col != "League":
                        touch_table[col] = touch_table[col].map(lambda x: f"{x:.2f}")
                
                st.dataframe(touch_table, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Pass efficiency
            st.markdown('<p class="tab-subheader">Pass & Carry Efficiency</p>', unsafe_allow_html=True)
            
            efficiency_cols = [
                "League", "Progressive Pass %", "Key Pass %", "Progressive Carry %", 
                "Final Third Entry per Carry %", "Box Entry per Carry %"
            ]
            
            # Filter for available columns
            available_eff_cols = [col for col in efficiency_cols if col in filtered_df.columns]
            
            if len(available_eff_cols) > 1:  # Need league plus at least one metric
                col1, col2 = st.columns(2)
                
                with col1:
                    # Progressive pass percentage
                    if "Progressive Pass %" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Progressive Pass %",
                            color="League",
                            title="Progressive Pass Percentage by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=450)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Progressive carry percentage
                    if "Progressive Carry %" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Progressive Carry %",
                            color="League",
                            title="Progressive Carry Percentage by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=450)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Efficiency table
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Pass & Carry Efficiency Metrics")
                
                # Format the table
                eff_table = filtered_df[available_eff_cols].copy()
                
                # Format columns
                for col in available_eff_cols:
                    if col != "League" and "%" in col:
                        eff_table[col] = eff_table[col].map(lambda x: f"{x:.1f}%")
                
                st.dataframe(eff_table, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Efficiency radar chart
            efficiency_metrics = [
                "Progressive Pass %", "Key Pass %", "Progressive Carry %", 
                "Goal Impact per 100 Touches", "xG+xA per 100 Touches"
            ]
            
            # Filter for available metrics
            available_eff_metrics = [metric for metric in efficiency_metrics if metric in filtered_df.columns]
            
            if len(available_eff_metrics) >= 3:  # Need at least 3 metrics for a meaningful radar
                # Normalize data for radar chart
                radar_df = filtered_df.copy()
                for metric in available_eff_metrics:
                    min_val = radar_df[metric].min()
                    max_val = radar_df[metric].max()
                    if max_val > min_val:
                        radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                    else:
                        radar_df[metric] = 0.5  # Default value if no variation
                
                fig = go.Figure()
                for i, league in enumerate(radar_df["League"]):
                    fig.add_trace(go.Scatterpolar(
                        r=radar_df.loc[radar_df["League"] == league, available_eff_metrics].values[0],
                        theta=available_eff_metrics,
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
                    title="Efficiency Metrics Comparison",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

    # 8. COMPOSITE METRICS TAB
    if composite_analysis and "Composite" in tabs:
        tab_index = tabs.index("Composite")
        with main_tabs[tab_index]:
            st.markdown('<p class="sub-header">Composite Metrics Analysis</p>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
            This section presents composite metrics that combine multiple performance dimensions into 
            unified ratings. These comprehensive indicators help identify overall league playing styles 
            and effectiveness.
            </div>
            """, unsafe_allow_html=True)
            
            # Composite metrics
            st.markdown('<p class="tab-subheader">Overall Performance Metrics</p>', unsafe_allow_html=True)
            
            composite_cols = [
                "League", "Offensive Efficiency", "Offensive Value Added", 
                "Defensive Value Metric", "Direct Play Index", "Pressing Intensity"
            ]
            
            # Filter for available columns
            available_comp_cols = [col for col in composite_cols if col in filtered_df.columns]
            
            if len(available_comp_cols) > 1:  # Need league plus at least one metric
                col1, col2 = st.columns(2)
                
                with col1:
                    # Offensive efficiency
                    if "Offensive Efficiency" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Offensive Efficiency",
                            color="League",
                            title="Offensive Efficiency by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=450)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Direct play index
                    if "Direct Play Index" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Direct Play Index",
                            color="League",
                            title="Direct Play Index by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=450)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Defensive value metric
                    if "Defensive Value Metric" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Defensive Value Metric",
                            color="League",
                            title="Defensive Value Metric by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=450)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Pressing intensity
                    if "Pressing Intensity" in filtered_df.columns:
                        fig = px.bar(
                            filtered_df, 
                            x="League", 
                            y="Pressing Intensity",
                            color="League",
                            title="Pressing Intensity by League",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        fig.update_layout(height=450)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Composite metrics table
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Composite Performance Metrics")
                
                # Format the table
                comp_table = filtered_df[available_comp_cols].copy()
                
                # Format columns
                for col in available_comp_cols:
                    if col != "League":
                        comp_table[col] = comp_table[col].map(lambda x: f"{x:.2f}")
                
                st.dataframe(comp_table, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Style categorization
            if "Direct Play Index" in filtered_df.columns and "Pressing Intensity" in filtered_df.columns:
                st.markdown('<p class="tab-subheader">Playing Style Classification</p>', unsafe_allow_html=True)
                
                # Create a new dataframe with style classifications
                style_df = filtered_df.copy()
                
                # Determine possession style
                style_df["Possession Style"] = np.where(
                    style_df["Direct Play Index"] > style_df["Direct Play Index"].mean(),
                    "Direct",
                    "Possession-based"
                )
                
                # Determine pressing style
                style_df["Pressing Style"] = np.where(
                    style_df["Pressing Intensity"] > style_df["Pressing Intensity"].mean(),
                    "High-Press",
                    "Low-Block"
                )
                
                # Determine attacking style if metrics available
                if "Shot on Target %" in style_df.columns and "xG Per Shot" in style_df.columns:
                    style_df["Attacking Style"] = np.where(
                        style_df["Shot on Target %"] > style_df["Shot on Target %"].mean(),
                        "Precise",
                        "Volume-based"
                    )
                
                # Combine metrics for overall style classification
                if "Offensive Efficiency" in style_df.columns and "Defensive Value Metric" in style_df.columns:
                    # Normalize both metrics
                    off_mean = style_df["Offensive Efficiency"].mean()
                    def_mean = style_df["Defensive Value Metric"].mean()
                    
                    style_df["Style Balance"] = np.where(
                        (style_df["Offensive Efficiency"] > off_mean) & (style_df["Defensive Value Metric"] < def_mean),
                        "Attack-Focused",
                        np.where(
                            (style_df["Offensive Efficiency"] < off_mean) & (style_df["Defensive Value Metric"] > def_mean),
                            "Defense-Focused",
                            "Balanced"
                        )
                    )
                
                # Select style columns
                style_cols = ["League", "Possession Style", "Pressing Style"]
                if "Attacking Style" in style_df.columns:
                    style_cols.append("Attacking Style")
                if "Style Balance" in style_df.columns:
                    style_cols.append("Style Balance")
                
                # Display style classification table
                st.dataframe(style_df[style_cols], use_container_width=True)
                
                # Create a visualization of playing styles
                if len(style_df) >= 2 and "Attacking Style" in style_df.columns:
                    fig = px.scatter(
                        style_df,
                        x="Direct Play Index",
                        y="Pressing Intensity",
                        size="Offensive Efficiency" if "Offensive Efficiency" in style_df.columns else None,
                        color="League",
                        hover_name="League",
                        text="League",
                        title="League Playing Style Visualization",
                        labels={
                            "Direct Play Index": "Direct Play → | ← Possession-Based", 
                            "Pressing Intensity": "Pressing Intensity"
                        },
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig.update_traces(textposition='top center')
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("""
                    <div class="info-box">
                    <strong>How to read this chart:</strong><br>
                    - <strong>Horizontal axis:</strong> Higher values indicate more direct play style, lower values indicate possession-based approach<br>
                    - <strong>Vertical axis:</strong> Higher values indicate higher pressing intensity, lower values indicate deeper defensive block<br>
                    - <strong>Bubble size:</strong> Represents offensive efficiency (larger = more efficient)
                    </div>
                    """, unsafe_allow_html=True)

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
            metric_categories = {
                "Attack": ["Performance Gls", "Performance Ast", "Performance G+A", "Standard Sh", "Expected xG", "GCA GCA"],
                "Possession": ["Touches Touches", "Carries PrgC", "Carries 1/3", "Take-Ons Succ", "Take-Ons Succ%"],
                "Passing": ["Total Cmp%", "PrgP", "KP", "Ast", "xAG", "SCA SCA"],
                "Defense": ["Tackles Tkl", "Tackles TklW", "Int", "Blocks Blocks", "Clr", "Aerial Duels Won%"]
            }
            
            # Flatten the metric categories for selection
            all_metrics = [metric for category in metric_categories.values() for metric in category]
            available_metrics = [col for col in all_metrics if col in filtered_players.columns]
            
            if available_metrics:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    # Let user select category first
                    category_options = [cat for cat, metrics in metric_categories.items() 
                                      if any(metric in available_metrics for metric in metrics)]
                    selected_category = st.selectbox(
                        "Select Metric Category",
                        options=category_options,
                        index=0
                    )
                    
                    # Filter metrics by selected category
                    category_metrics = [metric for metric in metric_categories[selected_category] 
                                      if metric in available_metrics]
                    
                    performance_metric = st.selectbox(
                        "Select Performance Metric",
                        options=category_metrics,
                        index=0 if category_metrics else None
                    )
                
                with col2:
                    if performance_metric:
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
                
                # Position-specific metrics analysis
                st.markdown("### Position-Specific Metrics Analysis")
                
                # Select a position to analyze
                position_options = ["All Positions"] + sorted(filtered_players["Primary Position"].unique().tolist())
                selected_position = st.selectbox(
                    "Select Position to Analyze",
                    options=position_options,
                    index=0
                )
                
                # Filter by selected position if not "All Positions"
                if selected_position != "All Positions":
                    position_players = filtered_players[filtered_players["Primary Position"] == selected_position]
                else:
                    position_players = filtered_players
                
                # Get relevant metrics for the position
                if selected_position in ["FW", "FW,MF", "MF,FW"] or selected_position == "All Positions":
                    relevant_metrics = ["Performance Gls", "Standard Sh", "Standard SoT%", "Expected xG", "Performance Ast"]
                elif selected_position in ["MF", "MF,DF", "DF,MF"]:
                    relevant_metrics = ["PrgP", "KP", "Carries PrgC", "Tackles Tkl", "Int"]
                elif selected_position in ["DF", "DF,FW", "FW,DF"]:
                    relevant_metrics = ["Tackles Tkl", "Int", "Clr", "Aerial Duels Won%", "Blocks Blocks"]
                elif selected_position == "GK":
                    relevant_metrics = ["Performance Gls", "Performance Ast", "Total Cmp%"]  # Limited GK metrics
                
                # Filter for available metrics
                available_relevant = [metric for metric in relevant_metrics if metric in position_players.columns]
                
                if available_relevant:
                    # Calculate league averages for the relevant metrics
                    league_avgs = position_players.groupby("Competition")[available_relevant].mean().reset_index()
                    
                    # Reshape for radar chart
                    # Normalize data for radar chart
                    radar_df = league_avgs.copy()
                    for metric in available_relevant:
                        min_val = radar_df[metric].min()
                        max_val = radar_df[metric].max()
                        if max_val > min_val:
                            radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
                        else:
                            radar_df[metric] = 0.5  # Default value if no variation
                    
                    # Create radar chart
                    fig = go.Figure()
                    for i, league in enumerate(radar_df["Competition"]):
                        fig.add_trace(go.Scatterpolar(
                            r=radar_df.loc[radar_df["Competition"] == league, available_relevant].values[0],
                            theta=available_relevant,
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
                        title=f"{selected_position} Performance Metrics by League",
                        height=600
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No performance metrics available in the data.")
    else:
        st.warning("No position data available for the selected leagues.")

# Summary section
st.markdown('<p class="sub-header">League Style Summary</p>', unsafe_allow_html=True)

# Create a summary dataframe with league archetypes
summary_df = filtered_df.copy()

# Determine archetypal characteristics
# Attack style
if "xG Per Shot" in summary_df.columns:
    summary_df["Attack Style"] = np.where(
        summary_df["xG Per Shot"] > summary_df["xG Per Shot"].mean(),
        "Quality Chances",
        "High Volume"
    )

# Possession approach
if "Progressive Carries Per 90" in summary_df.columns:
    summary_df["Possession Approach"] = np.where(
        summary_df["Progressive Carries Per 90"] > summary_df["Progressive Carries Per 90"].mean(),
        "Progressive",
        "Conservative"
    )

# Passing identity
if "Key Passes Per 90" in summary_df.columns:
    summary_df["Passing Identity"] = np.where(
        summary_df["Key Passes Per 90"] > summary_df["Key Passes Per 90"].mean(),
        "Creative",
        "Safe"
    )

# Set piece emphasis
if "Corner Success Rate (%)" in summary_df.columns:
    summary_df["Set Piece Emphasis"] = np.where(
        summary_df["Corner Success Rate (%)"] > summary_df["Corner Success Rate (%)"].mean(),
        "Set Piece Focused",
        "Open Play Focused"
    )

# Defensive approach
if "Pressing Intensity" in summary_df.columns:
    summary_df["Defensive Approach"] = np.where(
        summary_df["Pressing Intensity"] > summary_df["Pressing Intensity"].mean(),
        "High Pressing",
        "Defensive Block"
    )

# Select style columns that exist
style_cols = ["League", "Attack Style", "Possession Approach", "Passing Identity", "Set Piece Emphasis", "Defensive Approach"]
available_style_cols = [col for col in style_cols if col in summary_df.columns]

# Display style summary if we have at least some style classifications
if len(available_style_cols) > 1:
    style_summary = summary_df[available_style_cols]
    st.dataframe(style_summary, use_container_width=True)

# League comparison chart (overall style visualization)
st.markdown("### Overall League Style Comparison")

# Create a normalized dataframe for overall comparison
comparison_metrics = [
    "Shots Per 90", "xG Per Shot", "Possession %", 
    "Progressive Carries Per 90", "Pass Completion %", "Key Passes Per 90",
    "Corners Per Match", "Corner Success Rate (%)"
]

# Filter for available metrics
available_comparison = [metric for metric in comparison_metrics if metric in filtered_df.columns]

if available_comparison:
    compare_df = filtered_df.copy()
    for metric in available_comparison:
        min_val = compare_df[metric].min()
        max_val = compare_df[metric].max()
        if max_val > min_val:
            compare_df[metric] = (compare_df[metric] - min_val) / (max_val - min_val)
        else:
            compare_df[metric] = 0.5  # Default value if no variation

    # Heatmap of normalized values
    fig = px.imshow(
        compare_df.set_index('League')[available_comparison],
        labels=dict(x="Metric", y="League", color="Normalized Value"),
        x=available_comparison,
        y=compare_df["League"],
        color_continuous_scale="Blues",
        title="League Style Heatmap (Normalized Values)"
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

# Footer with instructions
st.markdown("""
---
### How to use this analyzer:

1. **Data Source**: The app automatically loads football data from GitHub. If the data can't be loaded, sample data is used.
2. **League Selection**: Select specific leagues to compare using the dropdown menu in the sidebar.
3. **Analysis Options**: Toggle additional analysis views using the checkboxes in the sidebar:
   - Show Advanced Metrics: Displays more detailed analytics in each category
   - Show Position-Based Analysis: Enables position-specific comparisons
   - Show Efficiency Analysis: Focuses on metrics normalized by possession and actions
   - Show Composite Metrics: Presents overall performance indicators
4. **Navigation**: Use the tabs at the top to explore different aspects of playing styles:
   - Attack: Shot volume, efficiency, and expected goals analysis
   - Defense: Tackles, interceptions, blocks, and defensive positioning
   - Possession: Ball retention, touch distribution, and progression metrics
   - Passing: Pass completion, progression, and creativity analysis
   - Corners: Set piece strategies and effectiveness
   - Player Impact: Team performance with players on/off field (if advanced metrics enabled)
   - Efficiency: Normalized performance metrics (if efficiency analysis enabled)
   - Composite: Overall performance indicators (if composite metrics enabled)
5. **Position Analysis**: If enabled, scroll down after the tabs for position-specific breakdowns
""")
