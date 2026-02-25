#!/usr/bin/env python3
"""
DBT Lineage Mapper

This tool creates lineage mappings between multiple dbt projects.
It can read from both GitHub repositories and local file systems.
"""

import os
import sys
import argparse
import logging
import http.server
import socketserver
import webbrowser
import threading
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.repository_provider import RepositoryFactory
from src.dbt_parser import DBTProjectParser
from src.lineage_graph import LineageGraph
from src.json_generator import JSONGenerator
from src.csv_generator import CSVGenerator
from src.html_generator import HTMLGenerator
from src.profiles_parser import ProfilesParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_repo_list(file_path: str) -> List[str]:
    """
    Read the list of repositories from a file.
    
    Args:
        file_path: Path to the file containing repository URLs or paths
        
    Returns:
        List of repository URLs or paths
    """
    try:
        with open(file_path, 'r') as f:
            # Strip whitespace and filter out empty lines
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading repository list file: {e}")
        sys.exit(1)

def start_web_server(html_file_path, port=8000):
    """
    Start a web server to serve the HTML file and open it in a browser.
    
    Args:
        html_file_path: Path to the HTML file to serve
        port: Port to use for the web server (default: 8000)
    """
    # Get the directory containing the HTML file
    web_dir = os.path.dirname(os.path.abspath(html_file_path))
    
    # Change to that directory
    os.chdir(web_dir)
    
    # Get the filename without the path
    filename = os.path.basename(html_file_path)
    
    # Create a handler that will serve files from the current directory
    handler = http.server.SimpleHTTPRequestHandler
    
    # Try to create a server on the specified port
    while True:
        try:
            httpd = socketserver.TCPServer(("", port), handler)
            break
        except OSError:
            # If the port is in use, try the next one
            logger.info(f"Port {port} is in use, trying {port + 1}")
            port += 1
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True  # So the thread will exit when the main program exits
    server_thread.start()
    
    # Open the browser
    url = f"http://localhost:{port}/{filename}"
    logger.info(f"Starting web server at {url}")
    webbrowser.open(url)
    
    # Keep the server running until the user presses Ctrl+C
    try:
        logger.info("Web server started. Press Ctrl+C to stop.")
        while True:
            # Sleep to prevent high CPU usage
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping web server...")
        httpd.shutdown()
        httpd.server_close()

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Generate lineage mappings between dbt projects')
    parser.add_argument('--repo-list', default='repo_list.txt',
                        help='Path to file containing list of repositories')
    parser.add_argument('--output', default='output/lineage',
                        help='Path to output file (without extension)')
    parser.add_argument('--format', default='html', choices=['json', 'csv', 'html'],
                        help='Output format (json, csv, or html)')
    parser.add_argument('--select', 
                        help='Select a specific model to display its lineage')
    parser.add_argument('--depth', type=int, default=None,
                        help='Maximum depth for model lineage (default: unlimited)')
    parser.add_argument('--github-token', default=os.environ.get('GITHUB_TOKEN'),
                        help='GitHub API token (can also be set via GITHUB_TOKEN env var)')
    parser.add_argument('--profiles', default=os.environ.get('DBT_PROFILES_PATH', os.path.expanduser('~/.dbt/profiles.yml')),
                        help='Path to dbt profiles.yml file')
    parser.add_argument('--profile-target', default=os.environ.get('DBT_PROFILE_TARGET'),
                        help='Target environment to use from profiles.yml')
    parser.add_argument('--no-server', action='store_true',
                        help='Do not start a web server for HTML output')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8000)),
                        help='Port to use for the web server (default: from PORT env var or 8000)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Read repository list
    logger.info(f"Reading repository list from {args.repo_list}")
    repo_paths = read_repo_list(args.repo_list)
    logger.info(f"Found {len(repo_paths)} repositories")
    
    # Create repository factory
    repo_factory = RepositoryFactory(github_token=args.github_token)
    
    # Create lineage graph
    lineage_graph = LineageGraph()
    
    # Initialize profiles parser if profiles path is provided
    profiles_parser = None
    if args.profiles and os.path.exists(os.path.expanduser(args.profiles)):
        logger.info(f"Using profiles from {args.profiles}")
        profiles_parser = ProfilesParser(args.profiles, args.profile_target)
    
    # Process each repository
    for repo_path in repo_paths:
        logger.info(f"Processing repository: {repo_path}")
        
        # Get repository provider
        repo_provider = repo_factory.create_provider(repo_path)
        
        # Create parser
        parser = DBTProjectParser(repo_provider, profiles_parser)
        
        # Parse project and add to lineage graph
        project_info = parser.parse_project()
        lineage_graph.add_project(project_info)
    
    # Link sources to models using profiles and inference
    if profiles_parser:
        logger.info("Linking sources to models using profiles and inference")
        lineage_graph.link_sources_to_models(profiles_parser)
    else:
        logger.info("Linking sources to external models by name (inference only)")
        lineage_graph.link_sources_to_external_models_by_name()
    
    # Generate output based on format and selection
    output_format = args.format.lower()
    output_path = args.output
    selected_model = args.select
    max_depth = args.depth
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Ensuring output directory exists: {output_dir}")
    
    # If a specific model is selected, get its lineage
    if selected_model:
        logger.info(f"Selecting model: {selected_model}")
        model_node = lineage_graph.find_model_node(selected_model)
        
        if not model_node:
            logger.error(f"Model not found: {selected_model}")
            sys.exit(1)
        
        logger.info(f"Found model: {model_node['id']}")
        
        # Get the model's lineage
        lineage = lineage_graph.get_model_lineage(selected_model, max_depth)
        
        # Create a new lineage graph with only the model's lineage
        model_lineage_graph = LineageGraph()
        
        # Add nodes to the new graph
        for node in lineage['nodes']:
            model_lineage_graph.nodes[node['id']] = node
        
        # Add edges to the new graph
        for edge in lineage['edges']:
            model_lineage_graph.edges.append(edge)
        
        # Use the model lineage graph for output
        output_lineage_graph = model_lineage_graph
        
        # Update output path to include model name
        model_name_safe = selected_model.replace('.', '_')
        output_path = f"{output_path}_{model_name_safe}"
    else:
        # Use the full lineage graph for output
        output_lineage_graph = lineage_graph
    
    if output_format == 'json':
        # Generate JSON output
        output_file = f"{output_path}.json"
        logger.info(f"Generating JSON output to {output_file}")
        generator = JSONGenerator(output_lineage_graph)
        json_data = generator.generate_output()
        
        # Write JSON to file
        with open(output_file, 'w') as f:
            f.write(json_data)
        
        logger.info(f"Lineage mapping complete. Output written to {output_file}")
    
    elif output_format == 'csv':
        # Generate CSV output
        logger.info(f"Generating CSV output to {output_path}_nodes.csv and {output_path}_edges.csv")
        generator = CSVGenerator(output_lineage_graph)
        generator.generate_output(output_path)
        
        logger.info(f"Lineage mapping complete. Output written to {output_path}_nodes.csv and {output_path}_edges.csv")
    
    elif output_format == 'html':
        # Generate HTML output
        output_file = f"{output_path}.html"
        logger.info(f"Generating interactive HTML visualization to {output_file}")
        generator = HTMLGenerator(output_lineage_graph)
        html = generator.generate_output()
        
        # Write HTML to file
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Lineage mapping complete. Output written to {output_file}")
        
        # Start a web server to serve the HTML file if requested
        if not args.no_server:
            start_web_server(output_file, args.port)
    
    else:
        logger.error(f"Unsupported output format: {output_format}")
        sys.exit(1)

if __name__ == "__main__":
    main()