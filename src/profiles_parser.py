"""
Profiles Parser Module

This module provides functionality for parsing dbt profiles.yml files
and extracting target-specific information for lineage mapping.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProfilesParser:
    """Parser for dbt profiles.yml files."""
    
    def __init__(self, profiles_path: str, target_override: Optional[str] = None):
        """
        Initialize the profiles parser.
        
        Args:
            profiles_path: Path to the profiles.yml file
            target_override: Override for the target to use (falls back to default if not found)
        """
        self.profiles = self._load_profiles(profiles_path)
        self.target_override = target_override
        logger.info(f"Initialized profiles parser with {len(self.profiles)} profiles")
        if target_override:
            logger.info(f"Using target override: {target_override}")
    
    def _load_profiles(self, profiles_path: str) -> Dict[str, Any]:
        """
        Load and parse the profiles.yml file.
        
        Args:
            profiles_path: Path to the profiles.yml file
            
        Returns:
            Dictionary containing parsed profiles
        """
        try:
            # Expand user directory if needed (e.g., ~/.dbt/profiles.yml)
            expanded_path = os.path.expanduser(profiles_path)
            
            if not os.path.exists(expanded_path):
                logger.warning(f"Profiles file not found: {expanded_path}")
                return {}
            
            with open(expanded_path, 'r') as f:
                profiles = yaml.safe_load(f)
                logger.debug(f"Loaded profiles from {expanded_path}")
                return profiles or {}
                
        except Exception as e:
            logger.error(f"Error loading profiles file: {e}")
            return {}
    
    def get_project_info(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get project information for a profile, using the specified target or falling back to default.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary containing project information, or None if not found
        """
        if profile_name not in self.profiles:
            logger.debug(f"Profile not found: {profile_name}")
            return None
        
        profile = self.profiles[profile_name]
        default_target = profile.get('target')
        target_name = self.target_override if self.target_override else default_target
        
        # Try specified target, fall back to default if not found
        if target_name not in profile.get('outputs', {}):
            logger.debug(f"Target {target_name} not found for profile {profile_name}, falling back to default: {default_target}")
            target_name = default_target
        
        if not target_name or target_name not in profile.get('outputs', {}):
            logger.warning(f"No valid target found for profile {profile_name}")
            return None
        
        target_info = profile['outputs'][target_name]
        logger.debug(f"Using target {target_name} for profile {profile_name}")
        return target_info
    
    def get_compiled_name(self, profile_name: str, model_name: str) -> Optional[str]:
        """
        Get the compiled name for a model based on profiles information.
        
        Args:
            profile_name: Name of the profile
            model_name: Name of the model
            
        Returns:
            Compiled name in the format project.dataset.model_name, or None if not available
        """
        project_info = self.get_project_info(profile_name)
        if not project_info:
            return None
        
        project = project_info.get('project')
        dataset = project_info.get('dataset')
        
        if project and dataset:
            compiled_name = f"{project}.{dataset}.{model_name}"
            logger.debug(f"Compiled name for {profile_name}.{model_name}: {compiled_name}")
            return compiled_name
        
        return None
    
    def get_all_profiles(self) -> Dict[str, Any]:
        """
        Get all profiles.
        
        Returns:
            Dictionary containing all profiles
        """
        return self.profiles