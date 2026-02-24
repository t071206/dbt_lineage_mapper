"""
Repository Provider Module

This module provides an abstraction for accessing repository contents,
supporting both GitHub API and local file system repositories.
"""

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, BinaryIO, Union
import requests
import base64
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RepositoryProvider(ABC):
    """Abstract base class for repository content providers."""
    
    @abstractmethod
    def get_file_content(self, path: str) -> str:
        """
        Get the content of a file from the repository.
        
        Args:
            path: Path to the file within the repository
            
        Returns:
            Content of the file as a string
            
        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there is an error reading the file
        """
        pass
    
    @abstractmethod
    def list_directory(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List the contents of a directory in the repository.
        
        Args:
            path: Path to the directory within the repository
            
        Returns:
            List of dictionaries containing information about each item in the directory.
            Each dictionary should have at least 'name', 'path', and 'type' keys.
            
        Raises:
            FileNotFoundError: If the directory does not exist
            IOError: If there is an error reading the directory
        """
        pass
    
    @abstractmethod
    def get_repository_name(self) -> str:
        """
        Get the name of the repository.
        
        Returns:
            Name of the repository
        """
        pass


class GitHubRepositoryProvider(RepositoryProvider):
    """Repository provider that uses the GitHub API."""
    
    def __init__(self, repo_url: str, token: Optional[str] = None):
        """
        Initialize the GitHub repository provider.
        
        Args:
            repo_url: URL of the GitHub repository
            token: GitHub API token for authentication
        """
        self.repo_url = repo_url
        self.token = token
        
        # Parse repository owner and name from URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        self.owner = path_parts[0]
        self.repo = path_parts[1]
        
        # Set up session with authentication if token is provided
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'token {token}'})
        
        # Configure proxies if set in environment variables
        proxies = {}
        http_proxy = os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('HTTPS_PROXY')
        
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        if proxies:
            logger.debug(f"Using proxies: {proxies}")
            self.session.proxies.update(proxies)
    
    def get_file_content(self, path: str) -> str:
        """
        Get the content of a file from the GitHub repository.
        
        Args:
            path: Path to the file within the repository
            
        Returns:
            Content of the file as a string
            
        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there is an error reading the file
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            content_data = response.json()
            
            if isinstance(content_data, list):
                raise IsADirectoryError(f"Path is a directory, not a file: {path}")
            
            # GitHub API returns content as base64 encoded
            content = base64.b64decode(content_data['content']).decode('utf-8')
            return content
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"File not found in repository: {path}")
            else:
                raise IOError(f"Error accessing GitHub API: {e}")
    
    def list_directory(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List the contents of a directory in the GitHub repository.
        
        Args:
            path: Path to the directory within the repository
            
        Returns:
            List of dictionaries containing information about each item in the directory.
            Each dictionary has 'name', 'path', and 'type' keys.
            
        Raises:
            FileNotFoundError: If the directory does not exist
            IOError: If there is an error reading the directory
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            contents = response.json()
            
            if not isinstance(contents, list):
                raise NotADirectoryError(f"Path is a file, not a directory: {path}")
            
            # Format the response to match our expected structure
            result = []
            for item in contents:
                result.append({
                    'name': item['name'],
                    'path': item['path'],
                    'type': 'file' if item['type'] == 'file' else 'dir'
                })
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"Directory not found in repository: {path}")
            else:
                raise IOError(f"Error accessing GitHub API: {e}")
    
    def get_repository_name(self) -> str:
        """
        Get the name of the repository.
        
        Returns:
            Name of the repository
        """
        return self.repo


class LocalRepositoryProvider(RepositoryProvider):
    """Repository provider that uses the local file system."""
    
    def __init__(self, repo_path: str):
        """
        Initialize the local repository provider.
        
        Args:
            repo_path: Path to the local repository
        """
        self.repo_path = os.path.abspath(repo_path)
        
        if not os.path.isdir(self.repo_path):
            raise FileNotFoundError(f"Repository directory not found: {self.repo_path}")
        
        # Extract repository name from path
        self.repo_name = os.path.basename(self.repo_path)
    
    def get_file_content(self, path: str) -> str:
        """
        Get the content of a file from the local repository.
        
        Args:
            path: Path to the file within the repository
            
        Returns:
            Content of the file as a string
            
        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there is an error reading the file
        """
        full_path = os.path.join(self.repo_path, path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found in repository: {path}")
        except IOError as e:
            raise IOError(f"Error reading file: {e}")
    
    def list_directory(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List the contents of a directory in the local repository.
        
        Args:
            path: Path to the directory within the repository
            
        Returns:
            List of dictionaries containing information about each item in the directory.
            Each dictionary has 'name', 'path', and 'type' keys.
            
        Raises:
            FileNotFoundError: If the directory does not exist
            IOError: If there is an error reading the directory
        """
        full_path = os.path.join(self.repo_path, path)
        
        try:
            items = os.listdir(full_path)
            
            result = []
            for item in items:
                item_path = os.path.join(path, item)
                full_item_path = os.path.join(self.repo_path, item_path)
                
                result.append({
                    'name': item,
                    'path': item_path,
                    'type': 'dir' if os.path.isdir(full_item_path) else 'file'
                })
            
            return result
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Directory not found in repository: {path}")
        except IOError as e:
            raise IOError(f"Error reading directory: {e}")
    
    def get_repository_name(self) -> str:
        """
        Get the name of the repository.
        
        Returns:
            Name of the repository
        """
        return self.repo_name


class RepositoryFactory:
    """Factory for creating repository providers."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the repository factory.
        
        Args:
            github_token: GitHub API token for authentication
        """
        self.github_token = github_token
    
    def create_provider(self, repo_path: str) -> RepositoryProvider:
        """
        Create a repository provider for the given repository path.
        
        Args:
            repo_path: Path or URL of the repository
            
        Returns:
            Repository provider instance
            
        Raises:
            ValueError: If the repository path is invalid
        """
        # Check if the path is a GitHub URL
        if repo_path.startswith('https://github.com/'):
            logger.debug(f"Creating GitHub repository provider for {repo_path}")
            return GitHubRepositoryProvider(repo_path, self.github_token)
        
        # Otherwise, assume it's a local path
        logger.debug(f"Creating local repository provider for {repo_path}")
        return LocalRepositoryProvider(repo_path)