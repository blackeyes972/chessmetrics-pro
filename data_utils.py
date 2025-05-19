import os

def get_data_directory():
    """Creates and returns the data directory path."""
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")
    return data_dir

def get_db_path(filename="chess_games.db"):
    """Returns the full path to the database file in the data directory."""
    return os.path.join(get_data_directory(), filename)

def get_log_path(filename):
    """Returns the full path to a log file in the data directory."""
    return os.path.join(get_data_directory(), filename)

def initialize_directories():
    """Creates all necessary directories for the application."""
    # Create data directory for DB and logs
    data_dir = get_data_directory()
    
    # Create logs directory (as a subdirectory of data)
    logs_dir = os.path.join(data_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"Created logs directory: {logs_dir}")
    
    # Create analysis directory if it doesn't exist
    analysis_dir = os.path.join(os.getcwd(), "analysis")
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
        print(f"Created analysis directory: {analysis_dir}")
    
    # Create gif_files directory if it doesn't exist
    gif_dir = os.path.join(os.getcwd(), "gif_files")
    if not os.path.exists(gif_dir):
        os.makedirs(gif_dir)
        print(f"Created gif_files directory: {gif_dir}")
    
    # Create pgn_files directory if it doesn't exist
    pgn_dir = os.path.join(os.getcwd(), "pgn_files")
    if not os.path.exists(pgn_dir):
        os.makedirs(pgn_dir)
        print(f"Created pgn_files directory: {pgn_dir}")