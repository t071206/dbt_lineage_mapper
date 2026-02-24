"""
DBT Project Parser Module

This module provides functionality for parsing dbt project files,
including dbt_project.yml, schema.yml, and SQL model files.
"""

import os
import re
import logging
import yaml
from typing import List, Dict, Any, Optional, Set, Tuple

from .repository_provider import RepositoryProvider

logger = logging.getLogger(__name__)

class DBTProjectParser:
    """Parser for dbt project files."""
    
    def __init__(self, repo_provider: RepositoryProvider):
        """
        Initialize the dbt project parser.
        
        Args:
            repo_provider: Repository provider for accessing repository contents
        """
        self.repo_provider = repo_provider
        self.project_name = None
        self.project_config = None
        self.models = {}  # Dict[model_name, model_info]
        self.sources = {}  # Dict[source_name, source_info]
        self.model_dependencies = {}  # Dict[model_name, List[dependency]]
    
    def parse_project(self) -> Dict[str, Any]:
        """
        Parse the dbt project and extract all relevant information.
        
        Returns:
            Dictionary containing project information, including models and their dependencies
        """
        # Parse project configuration
        self._parse_project_config()
        
        # Find and parse model files
        self._find_and_parse_models()
        
        # Find and parse schema files
        self._find_and_parse_schemas()
        
        # Build model dependencies
        self._build_model_dependencies()
        
        # Return project information
        return {
            'name': self.project_name,
            'config': self.project_config,
            'models': self.models,
            'sources': self.sources,
            'dependencies': self.model_dependencies
        }
    
    def _parse_project_config(self) -> None:
        """
        Parse the dbt_project.yml file to extract project configuration.
        """
        try:
            content = self.repo_provider.get_file_content('dbt_project.yml')
            config = yaml.safe_load(content)
            
            self.project_name = config.get('name')
            self.project_config = config
            
            logger.info(f"Parsed project configuration for {self.project_name}")
            
        except FileNotFoundError:
            logger.warning("dbt_project.yml not found, using repository name as project name")
            self.project_name = self.repo_provider.get_repository_name()
            self.project_config = {}
        except Exception as e:
            logger.error(f"Error parsing dbt_project.yml: {e}")
            self.project_name = self.repo_provider.get_repository_name()
            self.project_config = {}
    
    def _find_and_parse_models(self) -> None:
        """
        Find and parse all model SQL files in the repository.
        """
        try:
            # Start with the models directory
            self._process_directory('models')
            
        except FileNotFoundError:
            logger.warning("Models directory not found")
        except Exception as e:
            logger.error(f"Error processing models directory: {e}")
    
    def _process_directory(self, path: str) -> None:
        """
        Process a directory recursively to find and parse model files.
        
        Args:
            path: Path to the directory within the repository
        """
        try:
            items = self.repo_provider.list_directory(path)
            
            for item in items:
                item_path = item['path']
                
                if item['type'] == 'dir':
                    # Recursively process subdirectories
                    self._process_directory(item_path)
                elif item['type'] == 'file' and item_path.endswith('.sql'):
                    # Parse SQL model file
                    self._parse_model_file(item_path)
                    
        except FileNotFoundError:
            logger.debug(f"Directory not found: {path}")
        except Exception as e:
            logger.error(f"Error processing directory {path}: {e}")
    
    def _parse_model_file(self, path: str) -> None:
        """
        Parse a SQL model file to extract model information and dependencies.
        
        Args:
            path: Path to the model file within the repository
        """
        try:
            content = self.repo_provider.get_file_content(path)
            
            # Extract model name from path
            model_name = os.path.basename(path).replace('.sql', '')
            
            # Extract model references and sources
            refs = self._extract_refs(content)
            sources = self._extract_sources(content)
            
            # Extract compiled table name if available
            compiled_name = self._extract_compiled_name(content, model_name)
            
            # Store model information
            self.models[model_name] = {
                'path': path,
                'refs': refs,
                'sources': sources,
                'compiled_name': compiled_name,
                'defined_in': 'model'  # Mark as defined in a SQL model file
            }
            
            logger.debug(f"Parsed model file: {model_name}")
            
        except Exception as e:
            logger.error(f"Error parsing model file {path}: {e}")
    
    def _extract_refs(self, content: str) -> List[str]:
        """
        Extract model references from SQL content.
        
        Args:
            content: SQL content
            
        Returns:
            List of referenced model names
        """
        # Match {{ ref('model_name') }} or {{ ref("model_name") }}
        ref_pattern = r"{{\s*ref\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?\s*\)\s*}}"
        refs = []
        
        for match in re.finditer(ref_pattern, content):
            # If there's a second group, it's a cross-project reference
            if match.group(2):
                refs.append(f"{match.group(1)}.{match.group(2)}")
            else:
                refs.append(match.group(1))
        
        return refs
    
    def _extract_sources(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract source references from SQL content.
        
        Args:
            content: SQL content
            
        Returns:
            List of tuples containing (source_name, table_name)
        """
        # Match {{ source('source_name', 'table_name') }}
        source_pattern = r"{{\s*source\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?\s*\)\s*}}"
        sources = []
        
        for match in re.finditer(source_pattern, content):
            if match.group(2):
                sources.append((match.group(1), match.group(2)))
        
        return sources
    
    def _extract_compiled_name(self, content: str, model_name: str) -> Optional[str]:
        """
        Extract compiled BigQuery table name from SQL content.
        
        Args:
            content: SQL content
            model_name: Name of the model
            
        Returns:
            Compiled table name if found, otherwise None
        """
        # Look for a comment like -- compiled_name: project.dataset.table
        compiled_pattern = r"--\s*compiled_name:\s*([^\s]+)"
        match = re.search(compiled_pattern, content)
        
        if match:
            return match.group(1)
        
        # If no explicit compiled name, try to infer from project config
        if self.project_config:
            dataset = self.project_config.get('models', {}).get('dataset')
            project = self.project_config.get('models', {}).get('project')
            
            if dataset and project:
                return f"{project}.{dataset}.{model_name}"
        
        return None
    
    def _find_and_parse_schemas(self) -> None:
        """
        Find and parse all schema YAML files in the repository.
        """
        try:
            # Look for schema files in the models directory
            self._process_schema_directory('models')
            
        except FileNotFoundError:
            logger.warning("Models directory not found for schema files")
        except Exception as e:
            logger.error(f"Error processing models directory for schema files: {e}")
    
    def _process_schema_directory(self, path: str) -> None:
        """
        Process a directory recursively to find and parse schema files.
        
        Args:
            path: Path to the directory within the repository
        """
        try:
            items = self.repo_provider.list_directory(path)
            
            for item in items:
                item_path = item['path']
                
                if item['type'] == 'dir':
                    # Recursively process subdirectories
                    self._process_schema_directory(item_path)
                elif item['type'] == 'file' and (item_path.endswith('.yml') or item_path.endswith('.yaml')):
                    # Parse schema file
                    self._parse_schema_file(item_path)
                    
        except FileNotFoundError:
            logger.debug(f"Directory not found: {path}")
        except Exception as e:
            logger.error(f"Error processing directory {path} for schema files: {e}")
    
    def _parse_schema_file(self, path: str) -> None:
        """
        Parse a schema YAML file to extract model and source information.
        
        Args:
            path: Path to the schema file within the repository
        """
        try:
            content = self.repo_provider.get_file_content(path)
            
            # Replace tabs with spaces to avoid YAML parsing errors
            content = content.replace('\t', '    ')
            
            try:
                schema = yaml.safe_load(content)
                
                # Process models
                for model in schema.get('models', []):
                    model_name = model.get('name')
                    if model_name:
                        # Update existing model or create new one
                        if model_name in self.models:
                            # Keep the original defined_in value if it exists
                            defined_in = self.models[model_name].get('defined_in', 'schema')
                            self.models[model_name].update(model)
                            self.models[model_name]['defined_in'] = defined_in
                        else:
                            model['defined_in'] = 'schema'  # Mark as defined in a schema file
                            self.models[model_name] = model
                
                # Process sources
                for source in schema.get('sources', []):
                    source_name = source.get('name')
                    if source_name:
                        # Store source information
                        self.sources[source_name] = source
                        
                        # Process tables in the source
                        for table in source.get('tables', []):
                            table_name = table.get('name')
                            if table_name:
                                # Create a reference to the source table
                                source_ref = f"{source_name}.{table_name}"
                                self.sources[source_ref] = table
                
                logger.debug(f"Parsed schema file: {path}")
                
            except yaml.YAMLError as yaml_error:
                # Try with a more lenient approach - replace problematic whitespace
                content = re.sub(r'[ \t]+', ' ', content)
                try:
                    schema = yaml.safe_load(content)
                    
                    # Process models
                    for model in schema.get('models', []):
                        model_name = model.get('name')
                        if model_name:
                            # Update existing model or create new one
                            if model_name in self.models:
                                # Keep the original defined_in value if it exists
                                defined_in = self.models[model_name].get('defined_in', 'schema')
                                self.models[model_name].update(model)
                                self.models[model_name]['defined_in'] = defined_in
                            else:
                                model['defined_in'] = 'schema'  # Mark as defined in a schema file
                                self.models[model_name] = model
                    
                    # Process sources
                    for source in schema.get('sources', []):
                        source_name = source.get('name')
                        if source_name:
                            # Store source information
                            self.sources[source_name] = source
                            
                            # Process tables in the source
                            for table in source.get('tables', []):
                                table_name = table.get('name')
                                if table_name:
                                    # Create a reference to the source table
                                    source_ref = f"{source_name}.{table_name}"
                                    self.sources[source_ref] = table
                    
                    logger.debug(f"Parsed schema file with whitespace normalization: {path}")
                    
                except Exception as nested_error:
                    logger.error(f"Error parsing schema file {path} even after whitespace normalization: {nested_error}")
                    logger.error(f"Original YAML error: {yaml_error}")
            
        except Exception as e:
            logger.error(f"Error parsing schema file {path}: {e}")
    
    def _build_model_dependencies(self) -> None:
        """
        Build model dependencies based on refs and sources.
        """
        for model_name, model_info in self.models.items():
            dependencies = []
            
            # Add model references as dependencies
            for ref in model_info.get('refs', []):
                dependencies.append({
                    'type': 'model',
                    'name': ref
                })
            
            # Add source references as dependencies
            for source_name, table_name in model_info.get('sources', []):
                dependencies.append({
                    'type': 'source',
                    'name': f"{source_name}.{table_name}"
                })
            
            # Store dependencies
            self.model_dependencies[model_name] = dependencies