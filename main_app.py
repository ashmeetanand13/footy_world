import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from streamlit_data_loader import load_sample_data  # Keep this import for fallback

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

# Load data directly from CSV instead of using data_loader_ui()
# Path to your GitHub CSV file - update with your CSV filename 
csv_path = "your_uploaded_file.csv"  # Change this to your actual CSV filename

# Load your data
try:
    # Load the CSV file
    df = pd.read_csv("df_clean.csv")
    
    # Process the data similar to how data_loader_ui() would have done
    # This assumes your CSV has similar structure to what the app expects
    
    # If you need to separate the data into leagues and players
    # For example:
    if "type" in df.columns:
        leagues_df = df[df['type'] == 'league']
        players_df = df[df['type'] == 'player']
    else:
        # If your CSV doesn't have a type column, you might need a different approach
        # For example, if they're in separate files or have different structures
        leagues_df = df
        players_df = None
    
    using_sample_data = False  # Since you're using your own data
    
    print(f"Successfully loaded data from {csv_path}")
    
except Exception as e:
    print(f"Error loading data: {e}")
    # Fallback to sample data in case of error
    leagues_df, players_df = load_sample_data()
    using_sample_data = True

if using_sample_data:
    st.warning("Currently using sample data. Upload your FBref CSV file for actual analysis.")
