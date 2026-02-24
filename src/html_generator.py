"""
HTML Generator Module

This module provides functionality for generating an interactive HTML visualization
from lineage graphs, similar to dbt's documentation site.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional

from .lineage_graph import LineageGraph

logger = logging.getLogger(__name__)

class HTMLGenerator:
    """Generator for interactive HTML visualization from lineage graphs."""
    
    def __init__(self, lineage_graph: LineageGraph):
        """
        Initialize the HTML generator.
        
        Args:
            lineage_graph: Lineage graph to generate HTML from
        """
        self.lineage_graph = lineage_graph
    
    def generate_output(self) -> str:
        """
        Generate an interactive HTML visualization of the lineage graph.
        
        Returns:
            HTML string representation of the lineage graph
        """
        # Get all nodes and edges
        nodes = self.lineage_graph.get_all_nodes()
        edges = self.lineage_graph.get_all_edges()
        
        # Convert nodes and edges to Cytoscape.js format
        cytoscape_elements = self._convert_to_cytoscape_format(nodes, edges)
        
        # Generate HTML with embedded JavaScript
        return self._generate_html(cytoscape_elements)
    
    def generate_project_output(self, project_name: str) -> str:
        """
        Generate an interactive HTML visualization for a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            HTML string representation of the project
        """
        # Get project nodes and edges
        nodes = self.lineage_graph.get_project_nodes(project_name)
        edges = self.lineage_graph.get_project_edges(project_name)
        
        # Convert nodes and edges to Cytoscape.js format
        cytoscape_elements = self._convert_to_cytoscape_format(nodes, edges)
        
        # Generate HTML with embedded JavaScript
        return self._generate_html(cytoscape_elements, project_name)
    
    def generate_cross_project_output(self) -> str:
        """
        Generate an interactive HTML visualization showing only cross-project dependencies.
        
        Returns:
            HTML string representation of cross-project dependencies
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
        
        # Convert nodes and edges to Cytoscape.js format
        cytoscape_elements = self._convert_to_cytoscape_format(nodes, edges)
        
        # Generate HTML with embedded JavaScript
        return self._generate_html(cytoscape_elements, "Cross-Project Dependencies")
    
    def _convert_to_cytoscape_format(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert nodes and edges to Cytoscape.js format.
        
        Args:
            nodes: List of node information dictionaries
            edges: List of edge information dictionaries
            
        Returns:
            Dictionary with nodes and edges in Cytoscape.js format
        """
        cytoscape_nodes = []
        cytoscape_edges = []
        
        # Convert nodes
        for node in nodes:
            node_id = node.get('id', '')
            node_type = node.get('type', '')
            project = node.get('project', '')
            name = node.get('name', '')
            path = node.get('path', '')
            compiled_name = node.get('compiled_name', '')
            
            # Create node label
            project = node.get('project', '')
            if node_type == 'source':
                source = node.get('source', '')
                if source:
                    label = f"{source}.{name}"
                else:
                    label = name
            else:
                label = name
            
            # Add project to label data for display in tooltip
            display_label = label
            
            # Create node data
            node_data = {
                'id': node_id,
                'label': label,
                'type': node_type,
                'project': project,
                'path': path,
                'compiled_name': compiled_name
            }
            
            # Add node to list
            cytoscape_nodes.append({
                'data': node_data,
                'classes': node_type
            })
        
        # Convert edges
        for edge in edges:
            source_id = edge.get('source', '')
            target_id = edge.get('target', '')
            
            # Determine if it's a cross-project edge
            source_node = self.lineage_graph.get_node_by_id(source_id)
            target_node = self.lineage_graph.get_node_by_id(target_id)
            
            edge_class = ''
            if source_node and target_node and source_node.get('project') != target_node.get('project'):
                edge_class = 'crossProject'
            
            # Create edge data
            edge_data = {
                'id': f"{source_id}-{target_id}",
                'source': source_id,
                'target': target_id
            }
            
            # Add inferred property if present
            if 'inferred' in edge:
                edge_data['inferred'] = edge['inferred']
            
            # Add edge to list
            cytoscape_edges.append({
                'data': edge_data,
                'classes': edge_class
            })
        
        return {
            'nodes': cytoscape_nodes,
            'edges': cytoscape_edges
        }
    
    def _generate_html(self, cytoscape_elements: Dict[str, List[Dict[str, Any]]], title: str = "DBT Lineage Visualization") -> str:
        """
        Generate HTML with embedded JavaScript for visualization.
        
        Args:
            cytoscape_elements: Dictionary with nodes and edges in Cytoscape.js format
            title: Title for the visualization
            
        Returns:
            HTML string
        """
        # Convert elements to JSON string
        elements_json = json.dumps(cytoscape_elements['nodes'] + cytoscape_elements['edges'])
        
        # Read the HTML template
        template_path = os.path.join(os.path.dirname(__file__), 'html_template.html')
        
        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            logger.error(f"HTML template file not found at {template_path}")
            return f"<html><body><h1>Error: HTML template file not found</h1></body></html>"
        
        # Replace placeholders in the template
        html = template.replace('{{title}}', title).replace('{{elements_json}}', elements_json)
        
        return html