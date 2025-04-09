import pandas as pd
import numpy as np
import requests
from io import StringIO

def fetch_github_data(url):
    """
    Fetch data from a GitHub raw URL
    
    Args:
        url (str): URL to the raw file on GitHub
        
    Returns:
        str: Content of the file or None if failed
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.text
    except Exception as e:
        print(f"Error fetching data from GitHub: {str(e)}")
        return None

def process_github_data(url, data_type="fbref"):
    """
    Process data from GitHub based on the type of data
    
    Args:
        url (str): URL to the raw file on GitHub
        data_type (str): Type of data to process (fbref, understat, whoscored)
        
    Returns:
        tuple: (league_level_df, player_level_df, message)
    """
    content = fetch_github_data(url)
    
    if content is None:
        return None, None, "Failed to fetch data from GitHub"
    
    try:
        # Parse CSV content
        df = pd.read_csv(StringIO(content), low_memory=False)
        
        # Basic checks for expected columns
        if data_type == "fbref":
            required_cols = ['Player', 'Competition', 'Squad']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return None, None, f"Invalid FBref data format. Missing columns: {', '.join(missing_cols)}"
            
            # Proceed with fbref-specific processing
            # Call your existing processing functions here
            
            # For demonstration, return a simple message
            return df, df, f"Successfully loaded {df.shape[0]} player records from GitHub"
        
        elif data_type == "understat":
            # Handle understat data format
            pass
        
        elif data_type == "whoscored":
            # Handle whoscored data format
            pass
        
        else:
            return None, None, f"Unsupported data type: {data_type}"
    
    except Exception as e:
        return None, None, f"Error processing GitHub data: {str(e)}"

# GitHub repository utilities
def list_files_in_repo(repo_owner, repo_name, path="", token=None):
    """
    List files in a GitHub repository directory
    
    Args:
        repo_owner (str): GitHub repository owner/organization
        repo_name (str): Repository name
        path (str): Path within the repository
        token (str): Optional GitHub personal access token for private repos
        
    Returns:
        list: List of files in the directory
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        content = response.json()
        files = []
        
        if isinstance(content, list):
            for item in content:
                if item["type"] == "file":
                    files.append({
                        "name": item["name"],
                        "path": item["path"],
                        "download_url": item["download_url"],
                        "size": item["size"]
                    })
        
        return files
    
    except Exception as e:
        print(f"Error listing files in repository: {str(e)}")
        return []

def get_raw_url(repo_owner, repo_name, file_path, branch="main"):
    """
    Get raw URL for a file in a GitHub repository
    
    Args:
        repo_owner (str): GitHub repository owner/organization
        repo_name (str): Repository name
        file_path (str): Path to file within the repository
        branch (str): Repository branch
        
    Returns:
        str: Raw URL to the file
    """
    return f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file_path}"

# Example usage
if __name__ == "__main__":
    # Example: Listing files in a repository
    files = list_files_in_repo("username", "football-data", "csv")
    
    for file in files:
        print(f"File: {file['name']}, URL: {file['download_url']}")
    
    # Example: Processing data from a GitHub URL
    url = "https://raw.githubusercontent.com/username/football-data/main/premier_league_2023_24.csv"
    league_df, player_df, message = process_github_data(url, "fbref")
    
    print(message)
