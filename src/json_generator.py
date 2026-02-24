"""
JSON Generator Module

This module provides functionality for generating JSON output
from lineage graphs.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from .lineage_graph import LineageGraph

logger = logging.getLogger(__name__)

class JSONGenerator:
    """Generator for JSON output from lineage graphs."""
    
    def __init__(self, lineage_graph: LineageGraph):
        """
        Initialize the JSON generator.
        
        Args:
            lineage_graph: Lineage graph to generate JSON from
        """
        self.lineage_graph = lineage_graph
    
    def generate_output(self) -> str:
        """
        Generate a JSON representation of the lineage graph.
        
        Returns:
            JSON string representation of the lineage graph
        """
        # Get all nodes and edges
        nodes = self.lineage_graph.get_all_nodes()
        edges = self.lineage_graph.get_all_edges()
        
        # Create a dictionary with nodes and edges
        data = {
            'nodes': nodes,
            'edges': edges
        }
        
        # Convert to JSON string with pretty formatting
        return json.dumps(data, indent=2)
    
    def generate_project_output(self, project_name: str) -> str:
        """
        Generate a JSON representation of a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            JSON string representation of the project
        """
        # Get project nodes and edges
        nodes = self.lineage_graph.get_project_nodes(project_name)
        edges = self.lineage_graph.get_project_edges(project_name)
        
        # Create a dictionary with project info, nodes, and edges
        data = {
            'project': project_name,
            'nodes': nodes,
            'edges': edges
        }
        
        # Convert to JSON string with pretty formatting
        return json.dumps(data, indent=2)
    
    def generate_cross_project_output(self) -> str:
        """
        Generate a JSON representation showing only cross-project dependencies.
        
        Returns:
            JSON string representation of cross-project dependencies
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
        
        # Create a dictionary with cross-project info, nodes, and edges
        data = {
            'type': 'cross_project_dependencies',
            'nodes': nodes,
            'edges': edges
        }
        
        # Convert to JSON string with pretty formatting
        return json.dumps(data, indent=2)