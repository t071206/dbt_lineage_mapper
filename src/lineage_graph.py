"""
Lineage Graph Module

This module provides a graph structure for representing lineage
between dbt models, both within and across projects.
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class LineageGraph:
    """Graph structure for representing lineage between dbt models."""
    
    def __init__(self):
        """Initialize the lineage graph."""
        self.projects = {}  # Dict[project_name, project_info]
        self.nodes = {}  # Dict[node_id, node_info]
        self.edges = []  # List of (source_id, target_id, metadata)
    
    def add_project(self, project_info: Dict[str, Any]) -> None:
        """
        Add a project to the lineage graph.
        
        Args:
            project_info: Dictionary containing project information
        """
        project_name = project_info['name']
        
        # Store project information
        self.projects[project_name] = project_info
        
        # Add models as nodes
        self._add_project_models(project_name, project_info)
        
        # Add sources as nodes
        self._add_project_sources(project_name, project_info)
        
        # Add dependencies as edges
        self._add_project_dependencies(project_name, project_info)
        
        logger.info(f"Added project to lineage graph: {project_name}")
    
    def _add_project_models(self, project_name: str, project_info: Dict[str, Any]) -> None:
        """
        Add project models as nodes to the lineage graph.
        
        Args:
            project_name: Name of the project
            project_info: Dictionary containing project information
        """
        models = project_info.get('models', {})
        
        for model_name, model_info in models.items():
            # Create a unique node ID for the model
            node_id = f"{project_name}.{model_name}"
            
            # Create node information
            node_info = {
                'id': node_id,
                'name': model_name,
                'project': project_name,
                'type': 'model',
                'compiled_name': model_info.get('compiled_name'),
                'path': model_info.get('path'),
                'defined_in': model_info.get('defined_in', 'model')  # Add origin information
            }
            
            # Add node to the graph
            self.nodes[node_id] = node_info
            
            logger.debug(f"Added model node: {node_id}")
    
    def _add_project_sources(self, project_name: str, project_info: Dict[str, Any]) -> None:
        """
        Add project sources as nodes to the lineage graph.
        
        Args:
            project_name: Name of the project
            project_info: Dictionary containing project information
        """
        sources = project_info.get('sources', {})
        
        for source_ref, source_info in sources.items():
            # Create a unique node ID for the source
            node_id = f"{project_name}.source.{source_ref}"
            
            # Extract source name and table name
            if '.' in source_ref:
                source_name, table_name = source_ref.split('.', 1)
            else:
                source_name = source_ref
                table_name = None
            
            # Create node information
            node_info = {
                'id': node_id,
                'name': table_name if table_name else source_name,
                'source': source_name,
                'project': project_name,
                'type': 'source'
            }
            
            # Add node to the graph
            self.nodes[node_id] = node_info
            
            logger.debug(f"Added source node: {node_id}")
    
    def _add_project_dependencies(self, project_name: str, project_info: Dict[str, Any]) -> None:
        """
        Add project dependencies as edges to the lineage graph.
        
        Args:
            project_name: Name of the project
            project_info: Dictionary containing project information
        """
        dependencies = project_info.get('dependencies', {})
        
        for model_name, model_deps in dependencies.items():
            # Get the source node ID
            source_id = f"{project_name}.{model_name}"
            
            # Skip if the source node doesn't exist
            if source_id not in self.nodes:
                logger.warning(f"Source node not found for dependency: {source_id}")
                continue
            
            # Process each dependency
            for dep in model_deps:
                dep_type = dep.get('type')
                dep_name = dep.get('name')
                
                if dep_type == 'model':
                    # Check if it's a cross-project reference
                    if '.' in dep_name:
                        # Format: project_name.model_name
                        target_id = dep_name
                    else:
                        # Same project reference
                        target_id = f"{project_name}.{dep_name}"
                elif dep_type == 'source':
                    # Source reference
                    target_id = f"{project_name}.source.{dep_name}"
                else:
                    logger.warning(f"Unknown dependency type: {dep_type}")
                    continue
                
                # Add edge to the graph - reversed direction to show data flow
                # Instead of model -> dependency, we now have dependency -> model
                self.edges.append({
                    'source': target_id,  # dependency (provider)
                    'target': source_id,  # model (consumer)
                    'type': dep_type
                })
                
                logger.debug(f"Added dependency edge (data flow): {target_id} -> {source_id}")
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """
        Get all nodes in the lineage graph.
        
        Returns:
            List of node information dictionaries
        """
        return list(self.nodes.values())
    
    def get_all_edges(self) -> List[Dict[str, Any]]:
        """
        Get all edges in the lineage graph.
        
        Returns:
            List of edge information dictionaries
        """
        return self.edges
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Node information dictionary, or None if not found
        """
        return self.nodes.get(node_id)
    
    def get_node_dependencies(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get all dependencies of a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of edge information dictionaries
        """
        return [edge for edge in self.edges if edge['source'] == node_id]
    
    def get_node_dependents(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get all dependents of a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of edge information dictionaries
        """
        return [edge for edge in self.edges if edge['target'] == node_id]
    
    def get_cross_project_edges(self) -> List[Dict[str, Any]]:
        """
        Get all cross-project edges in the lineage graph.
        
        Returns:
            List of edge information dictionaries
        """
        cross_project_edges = []
        
        for edge in self.edges:
            source_id = edge['source']
            target_id = edge['target']
            
            source_node = self.nodes.get(source_id)
            target_node = self.nodes.get(target_id)
            
            if source_node and target_node and source_node['project'] != target_node['project']:
                cross_project_edges.append(edge)
        
        return cross_project_edges
    
    def get_project_nodes(self, project_name: str) -> List[Dict[str, Any]]:
        """
        Get all nodes in a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List of node information dictionaries
        """
        return [node for node in self.nodes.values() if node['project'] == project_name]
    
    def get_project_edges(self, project_name: str) -> List[Dict[str, Any]]:
        """
        Get all edges within a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List of edge information dictionaries
        """
        project_edges = []
        
        for edge in self.edges:
            source_id = edge['source']
            target_id = edge['target']
            
            source_node = self.nodes.get(source_id)
            target_node = self.nodes.get(target_id)
            
            if source_node and target_node and source_node['project'] == project_name and target_node['project'] == project_name:
                project_edges.append(edge)
        
        return project_edges
    
    def find_model_node(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a model node by name, searching across all projects.
        
        Args:
            model_name: Name of the model to find
            
        Returns:
            Node information dictionary, or None if not found
        """
        # First, check if the model name includes a project prefix (project.model)
        if '.' in model_name:
            project_name, model_short_name = model_name.split('.', 1)
            node_id = f"{project_name}.{model_short_name}"
            return self.nodes.get(node_id)
        
        # If no project prefix, search across all projects
        for node_id, node in self.nodes.items():
            if node['type'] == 'model' and node['name'] == model_name:
                return node
        
        return None
    
    def get_model_lineage(self, model_name: str, max_depth: int = None) -> Dict[str, Any]:
        """
        Get the lineage of a specific model, including upstream and downstream dependencies.
        
        Args:
            model_name: Name of the model
            max_depth: Maximum depth to traverse (None for unlimited)
            
        Returns:
            Dictionary containing nodes and edges in the model's lineage
        """
        # Find the model node
        model_node = self.find_model_node(model_name)
        if not model_node:
            logger.warning(f"Model not found: {model_name}")
            return {'nodes': [], 'edges': []}
        
        model_id = model_node['id']
        
        # Get all nodes and edges in the lineage
        lineage_node_ids = set()
        lineage_edges = []
        
        # Add the model node itself
        lineage_node_ids.add(model_id)
        
        # Get upstream dependencies (recursively)
        self._get_upstream_dependencies(model_id, lineage_node_ids, lineage_edges, 0, max_depth)
        
        # Get downstream dependents (recursively)
        self._get_downstream_dependents(model_id, lineage_node_ids, lineage_edges, 0, max_depth)
        
        # Get the node information for all nodes in the lineage
        lineage_nodes = [self.nodes[node_id] for node_id in lineage_node_ids if node_id in self.nodes]
        
        return {
            'nodes': lineage_nodes,
            'edges': lineage_edges
        }
    
    def _get_upstream_dependencies(self, node_id: str, node_ids: Set[str], edges: List[Dict[str, Any]], 
                                  current_depth: int, max_depth: Optional[int]) -> None:
        """
        Recursively get all upstream dependencies of a node.
        
        Args:
            node_id: ID of the node
            node_ids: Set to collect node IDs
            edges: List to collect edges
            current_depth: Current recursion depth
            max_depth: Maximum depth to traverse (None for unlimited)
        """
        # Check if we've reached the maximum depth
        if max_depth is not None and current_depth >= max_depth:
            return
        
        # Get all dependencies of the node
        for edge in self.edges:
            if edge['source'] == node_id:
                target_id = edge['target']
                
                # Add the edge to the lineage
                if edge not in edges:
                    edges.append(edge)
                
                # Add the target node to the lineage
                node_ids.add(target_id)
                
                # Recursively get dependencies of the target node
                self._get_upstream_dependencies(target_id, node_ids, edges, current_depth + 1, max_depth)
    
    def _get_downstream_dependents(self, node_id: str, node_ids: Set[str], edges: List[Dict[str, Any]], 
                                  current_depth: int, max_depth: Optional[int]) -> None:
        """
        Recursively get all downstream dependents of a node.
        
        Args:
            node_id: ID of the node
            node_ids: Set to collect node IDs
            edges: List to collect edges
            current_depth: Current recursion depth
            max_depth: Maximum depth to traverse (None for unlimited)
        """
        # Check if we've reached the maximum depth
        if max_depth is not None and current_depth >= max_depth:
            return
        
        # Get all dependents of the node
        for edge in self.edges:
            if edge['target'] == node_id:
                source_id = edge['source']
                
                # Add the edge to the lineage
                if edge not in edges:
                    edges.append(edge)
                
                # Add the source node to the lineage
                node_ids.add(source_id)
                
                # Recursively get dependents of the source node
                self._get_downstream_dependents(source_id, node_ids, edges, current_depth + 1, max_depth)
    
    def link_sources_to_external_models_by_name(self) -> None:
        """
        Create edges between sources and models in different projects that have the same name.
        This assumes that if a source in project A has the same name as a model in project B,
        they are related.
        """
        # Get all source nodes
        source_nodes = [node for node in self.nodes.values() if node['type'] == 'source']
        
        # Get all model nodes
        model_nodes = [node for node in self.nodes.values() if node['type'] == 'model']
        
        # For each source node
        for source_node in source_nodes:
            source_project = source_node['project']
            source_name = source_node['name']
            
            # For sources, also check the full source reference (source.name)
            full_source_name = None
            if 'source' in source_node:
                full_source_name = f"{source_node['source']}.{source_name}"
            
            # Look for models with the same name in other projects
            for model_node in model_nodes:
                model_project = model_node['project']
                model_name = model_node['name']
                
                # If names match (either simple name or full source reference) and projects are different
                if (source_name == model_name or (full_source_name and model_name == source_name)) and source_project != model_project:
                    # Create an edge from the model to the source (keeping this direction for data flow)
                    # This represents data flowing from the external model to the source
                    self.edges.append({
                        'source': model_node['id'],
                        'target': source_node['id'],
                        'type': 'cross_project_source',
                        'inferred': True  # Mark as inferred for visualization
                    })
                    
                    logger.info(f"Created cross-project link (data flow): {model_node['id']} -> {source_node['id']}")
