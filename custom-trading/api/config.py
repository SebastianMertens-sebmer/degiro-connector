"""
Configuration Management
Smart path resolution that works on any computer
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Smart configuration manager with flexible path resolution"""
    
    def __init__(self):
        self.project_root = self._find_project_root()
    
    def _find_project_root(self) -> Path:
        """Find project root by looking for key files"""
        current = Path(__file__).parent
        
        # Look for indicators of project root
        indicators = ["requirements.txt", "setup.py", ".env", "README.md"]
        
        # Search up the directory tree
        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent
                
        # Fallback to parent of api directory
        return current.parent
    
    def get_config_path(self, filename: str = "config.json") -> Path:
        """Get config file path with smart resolution"""
        
        # Priority order for config location:
        # 1. Environment variable
        # 2. ./config/filename (relative to project root)
        # 3. ./filename (relative to project root)
        # 4. ./config/filename (relative to current directory)
        
        env_path = os.getenv("DEGIRO_CONFIG_PATH")
        if env_path:
            path = Path(env_path)
            if path.is_absolute():
                return path
            else:
                return self.project_root / path
        
        # Try standard locations
        possible_paths = [
            self.project_root / "config" / filename,
            self.project_root / filename,
            Path.cwd() / "config" / filename,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Default: config directory in project root
        return self.project_root / "config" / filename
    
    def load_config(self, filename: str = "config.json") -> Dict[str, Any]:
        """Load configuration from JSON file"""
        config_path = self.get_config_path(filename)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
    
    def get_env_config(self) -> Dict[str, Any]:
        """Get configuration from environment variables"""
        return {
            "username": os.getenv("DEGIRO_USERNAME"),
            "password": os.getenv("DEGIRO_PASSWORD"),
            "totp_secret_key": os.getenv("DEGIRO_TOTP_SECRET"),
            "int_account": int(os.getenv("DEGIRO_INT_ACCOUNT", 0)) or None,
            "user_token": os.getenv("DEGIRO_USER_TOKEN"),
        }
    
    def get_merged_config(self) -> Dict[str, Any]:
        """Get configuration with environment variables overriding file config"""
        try:
            file_config = self.load_config()
        except FileNotFoundError:
            file_config = {}
        
        env_config = self.get_env_config()
        
        # Merge configs (env vars override file config)
        merged = file_config.copy()
        for key, value in env_config.items():
            if value is not None:
                merged[key] = value
        
        return merged


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> Dict[str, Any]:
    """Get configuration (convenience function)"""
    return config_manager.get_merged_config()


def get_config_path(filename: str = "config.json") -> Path:
    """Get config file path (convenience function)"""
    return config_manager.get_config_path(filename)