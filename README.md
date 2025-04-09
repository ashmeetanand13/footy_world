# footy_world

# Football League Analyzer

A Streamlit application for comparing football (soccer) leagues based on data from FBref or similar statistics sources.

## Overview

This application analyzes and compares the playing styles of different football leagues across four key dimensions:
- **Attack** patterns
- **Possession** styles
- **Passing** tendencies
- **Corner Kick** strategies

## Files in this Project

1. **main_app.py** - The main Streamlit application that creates the interactive dashboard
2. **streamlit_data_loader.py** - Module for loading and preprocessing data from CSV files
3. **data_processor.py** - Script for batch processing of raw data files

## Setup and Installation

### Prerequisites
- Python 3.7+
- Streamlit
- Pandas
- NumPy
- Plotly
- Matplotlib
- Seaborn

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/football-league-analyzer.git
cd football-league-analyzer

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the App

```bash
streamlit run main_app.py
```

### Data Format

The application expects CSV data in FBref-style format with the following key columns:

#### Required Columns
- `Player` - Player name
- `Squad` - Team name
- `Competition` - League name
- `Pos` - Player position

#### Key Metric Columns

**Attack Metrics**
- `Performance Gls` - Goals scored
- `Standard Sh` - Shots taken
- `Standard SoT` - Shots on target
- `Expected xG` - Expected goals

**Possession Metrics**
- `Touches Touches` - Total touches
- `Touches Def 3rd`, `Touches Mid 3rd`, `Touches Att 3rd` - Touches by field position
- `Carries Carries` - Total carries
- `Carries PrgC` - Progressive carries

**Passing Metrics**
- `Total Att` - Pass attempts
- `Total Cmp` - Completed passes
- `Total Cmp%` - Pass completion percentage
- `PrgP` - Progressive passes
- `KP` - Key passes

**Corner Metrics**
- `Pass Types CK` - Corner kicks
- `Corner Kicks In`, `Corner Kicks Out`, `Corner Kicks Str` - Corner types

## Features

### League Comparison Tools
- Interactive visualizations comparing metrics across leagues
- Radar charts for multi-dimensional analysis
- League style classification based on statistical patterns
- Position-based analysis to understand tactical differences

### Data Processing
- Support for raw FBref data files
- Data cleaning and normalization
- Aggregation to league level for comparison

## Customization

You can extend the application with:
- Additional metric calculations
- Custom visualizations
- New analysis dimensions
- Integration with other data sources

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
