"""
Centralized path resolution utility for Docker vs local environment handling.
This module provides smart path resolution that works in both Docker containers
and local Windows development environments.
"""

import os
from pathlib import Path
from typing import Union


def get_data_root() -> Path:
    """
    Smart path resolution for Docker vs local environments.
    
    Returns:
        Path: The root directory for data files
        - In Docker: /data/
        - In Local: {project_root}/local_files/
    """
    if Path('/data/scripts').exists():
        # DOCKER MODE
        return Path('/data')
    else:
        # LOCAL MODE
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'local_files'


def get_script_root() -> Path:
    """
    Get the root directory for scripts.
    
    Returns:
        Path: The root directory for scripts
        - In Docker: /data/scripts/
        - In Local: {project_root}/prod/
    """
    if Path('/data/scripts').exists():
        # DOCKER MODE
        return Path('/data/scripts')
    else:
        # LOCAL MODE
        return Path(__file__).parent.parent


def resolve_data_path(relative_path: Union[str, Path]) -> Path:
    """
    Resolve a relative data path to absolute path in current environment.
    
    Args:
        relative_path: Relative path from data root (e.g., 'sentiment_analysis/NVDA_latest_v4.json')
        
    Returns:
        Path: Absolute path in current environment
    """
    data_root = get_data_root()
    return data_root / relative_path


def resolve_script_path(relative_path: Union[str, Path]) -> Path:
    """
    Resolve a relative script path to absolute path in current environment.
    
    Args:
        relative_path: Relative path from script root (e.g., 'pipelines/analysis/advanced_sentiment_engine_v4.py')
        
    Returns:
        Path: Absolute path in current environment
    """
    script_root = get_script_root()
    return script_root / relative_path


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path: The directory path (now guaranteed to exist)
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_docker_environment() -> bool:
    """
    Check if running in Docker environment.
    
    Returns:
        bool: True if running in Docker, False if local
    """
    return Path('/data/scripts').exists()


def get_environment_info() -> dict:
    """
    Get information about current environment.
    
    Returns:
        dict: Environment information including type, data root, script root
    """
    is_docker = is_docker_environment()
    return {
        'environment': 'docker' if is_docker else 'local',
        'data_root': str(get_data_root()),
        'script_root': str(get_script_root()),
        'is_docker': is_docker
    }


# Convenience constants
DATA_ROOT = get_data_root()
SCRIPT_ROOT = get_script_root()
IS_DOCKER = is_docker_environment()

# Common data directories
SENTIMENT_DIR = DATA_ROOT / 'sentiment_analysis'
OPTIONS_DIR = DATA_ROOT / 'options_data'
COMPANIES_DIR = DATA_ROOT / 'companies'