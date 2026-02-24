"""
CSV Generator Module

This module provides functionality for generating CSV output
from lineage graphs.
"""

import csv
import io
import logging
import os
from typing import List, Dict, Any, Optional, Tuple

from .lineage_graph import LineageGraph

logger = logging.getLogger(__name__)

class CSVGenerator:
    """Generator for CSV output from lineage graphs."""
    
    def __init__(self, lineage_graph: LineageGraph):
        """
        Initialize the CSV generator.
        
        Args:
            lineage_graph: Lineage graph to generate CSV from
        """
        self.lineage_graph = lineage_graph
    
    def generate_output(self, output_path: str) -> None:
        """
        Generate CSV files for nodes and edges.
        
        Args:
            output_path: Base path for output files (without extension)
        """
        # Get all nodes and edges
        nodes = self.lineage_graph.get_all_nodes()
        edges = self.lineage_graph.get_all_edges()
        
        # Generate CSV files
        self._generate_nodes_csv(nodes, f"{output_path}_nodes.csv")
        self._generate_edges_csv(edges, f"{output_path}_edges.csv")
        
        logger.info(f"Generated CSV files: {output_path}_nodes.csv and {output_path}_edges.csv")
    
    def generate_project_output(self, project_name: str, output_path: str) -> None:
        """
        Generate CSV files for a specific project.
        
        Args:
            project_name: Name of the project
            output_path: Base path for output files (without extension)
        """
        # Get project nodes and edges
        nodes = self.lineage_graph.get_project_nodes(project_name)
        edges = self.lineage_graph.get_project_edges(project_name)
        
        # Generate CSV files
        self._generate_nodes_csv(nodes, f"{output_path}_{project_name}_nodes.csv")
        self._generate_edges_csv(edges, f"{output_path}_{project_name}_edges.csv")
        
        logger.info(f"Generated CSV files for project {project_name}: {output_path}_{project_name}_nodes.csv and {output_path}_{project_name}_edges.csv")
    
    def generate_cross_project_output(self, output_path: str) -> None:
        """
        Generate CSV files showing only cross-project dependencies.
        
        Args:
            output_path: Base path for output files (without extension)
        """
        # Get all nodes
        all_nodes = self.lineage_graph.get_all_nodes()
        
        # Get cross-project edges
        edges = self.lineage_graph.get_cross_project_edges()
        
        # Get nodes involved in cross-project edges
        node_ids = set()
        for edge in edges:
            node_ids.add(edge['source'])
            node_ids.add(edge['target'])
        
        nodes = [node for node in all_nodes if node['id'] in node_ids]
        
        # Generate CSV files
        self._generate_nodes_csv(nodes, f"{output_path}_cross_project_nodes.csv")
        self._generate_edges_csv(edges, f"{output_path}_cross_project_edges.csv")
        
        logger.info(f"Generated CSV files for cross-project dependencies: {output_path}_cross_project_nodes.csv and {output_path}_cross_project_edges.csv")
    
    def _generate_nodes_csv(self, nodes: List[Dict[str, Any]], output_file: str) -> None:
        """
        Generate a CSV file for nodes.
        
        Args:
            nodes: List of node information dictionaries
            output_file: Path to the output file
        """
        # Define the fieldnames for the CSV
        fieldnames = ['id', 'name', 'type', 'project', 'path', 'compiled_name']
        
        # Write to CSV file
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for node in nodes:
                # Extract relevant fields
                row = {
                    'id': node.get('id', ''),
                    'name': node.get('name', ''),
                    'type': node.get('type', ''),
                    'project': node.get('project', ''),
                    'path': node.get('path', ''),
                    'compiled_name': node.get('compiled_name', '')
                }
                writer.writerow(row)
    
    def _generate_edges_csv(self, edges: List[Dict[str, Any]], output_file: str) -> None:
        """
        Generate a CSV file for edges.
        
        Args:
            edges: List of edge information dictionaries
            output_file: Path to the output file
        """
        # Define the fieldnames for the CSV
        fieldnames = ['source', 'target', 'type', 'cross_project']
        
        # Write to CSV file
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for edge in edges:
                # Determine if it's a cross-project edge
                source_id = edge.get('source', '')
                target_id = edge.get('target', '')
                
                source_node = self.lineage_graph.get_node_by_id(source_id)
                target_node = self.lineage_graph.get_node_by_id(target_id)
                
                cross_project = False
                if source_node and target_node and source_node.get('project') != target_node.get('project'):
                    cross_project = True
                
                # Extract relevant fields
                row = {
                    'source': source_id,
                    'target': target_id,
                    'type': edge.get('type', ''),
                    'cross_project': cross_project
                }
                writer.writerow(row)