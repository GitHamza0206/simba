import os
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from simba.core.config import Settings, PathConfig, ProjectConfig

def test_default_settings(tmp_path):
    """Test default settings when no config file exists"""
    with patch("simba.core.config.Path.cwd", return_value=tmp_path):
        settings = Settings.load_from_yaml()
        
        # Verify basic structure
        assert isinstance(settings.project, ProjectConfig)
        assert isinstance(settings.paths, PathConfig)
        
        # Verify paths are relative to current working directory
        assert settings.paths.base_dir == tmp_path
        assert settings.paths.upload_dir == tmp_path / "uploads"
        assert settings.paths.vector_store_dir == tmp_path / "vector_stores"
        
        # Verify directories were created
        assert (tmp_path / "uploads").exists()
        assert (tmp_path / "vector_stores").exists()

def test_custom_config_loading(tmp_path, caplog):
    """Test loading from a custom config file"""
    # Create test config
    config_content = """
    project:
      name: "Test Project"
    paths:
      upload_dir: "custom_uploads"
    """
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    
    with patch("simba.core.config.Path.cwd", return_value=tmp_path):
        with caplog.at_level(logging.INFO):
            settings = Settings.load_from_yaml(config_file)
        
        # Verify custom settings
        assert settings.project.name == "Test Project"
        assert settings.paths.upload_dir == tmp_path / "custom_uploads"
        assert "Loaded configuration from" in caplog.text

def test_environment_variable_config(monkeypatch, tmp_path):
    """Test loading config path from environment variable"""
    test_config = tmp_path / "env_config.yaml"
    test_config.write_text("project:\n  name: Test")
    monkeypatch.setenv("SIMBA_CONFIG_PATH", str(test_config))
    
    with patch("simba.core.config.Path.cwd", return_value=tmp_path):
        settings = Settings.load_from_yaml()
        assert settings.paths.base_dir == tmp_path

def test_directory_creation(tmp_path):
    """Verify required directories are created"""
    test_dir = tmp_path / "test_run"
    test_dir.mkdir()
    
    with patch("simba.core.config.Path.cwd", return_value=test_dir):
        config = PathConfig()
        assert (test_dir / "vector_stores/faiss_index").exists()
        assert (test_dir / "uploads").exists()

def test_invalid_config_handling(tmp_path, caplog):
    """Test invalid config file falls back to defaults"""
    bad_config = tmp_path / "bad_config.yaml"
    bad_config.write_text("invalid:\n  - not a valid config")  # Fixed YAML syntax
    
    with patch("simba.core.config.Path.cwd", return_value=tmp_path):
        with caplog.at_level(logging.WARNING):
            settings = Settings.load_from_yaml(bad_config)
        
        # Verify fallback to defaults
        assert settings.project.name == "Simba"  # Default value
        assert settings.paths.base_dir == tmp_path

def test_path_config_resolution():
    """Test path resolution in PathConfig"""
    test_path = Path("/test/cwd")
    with patch("simba.core.config.Path.cwd", return_value=test_path):
        config = PathConfig()
        
        assert config.base_dir == test_path
        assert config.upload_dir == test_path / "uploads"
        assert config.faiss_index_dir == test_path / "vector_stores/faiss_index" 