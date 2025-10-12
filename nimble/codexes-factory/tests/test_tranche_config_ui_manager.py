"""
Tests for tranche configuration UI manager.
"""

import pytest
import os
import tempfile
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from src.codexes.modules.ui.tranche_config_ui_manager import TrancheConfigUIManager


class TestTrancheConfigUIManager:
    
    def setup_method(self):
        """Set up test fixtures with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.tranches_dir = os.path.join(self.temp_dir, "configs", "tranches")
        os.makedirs(self.tranches_dir, exist_ok=True)
        
        # Create test tranche configurations
        self.create_test_tranche_configs()
        
        # Initialize manager with test directory
        self.manager = TrancheConfigUIManager()
        self.manager.tranches_dir = self.tranches_dir
    
    def teardown_method(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_tranche_configs(self):
        """Create test tranche configuration files"""
        test_configs = {
            "test_tranche_1": {
                "display_name": "Test Tranche 1",
                "description": "First test tranche",
                "imprint": "test_imprint",
                "publisher": "test_publisher",
                "contributor_one": "Test Author",
                "language": "en"
            },
            "test_tranche_2": {
                "display_name": "Test Tranche 2",
                "description": "Second test tranche",
                "imprint": "another_imprint",
                "publisher": "another_publisher",
                "language": "ko"
            }
        }
        
        for name, config in test_configs.items():
            config_path = os.path.join(self.tranches_dir, f"{name}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
    
    def test_load_available_tranches(self):
        """Test loading available tranche configurations"""
        tranches = self.manager.load_available_tranches()
        
        assert len(tranches) == 2
        
        # Check first tranche
        tranche1 = next(t for t in tranches if t['name'] == 'test_tranche_1')
        assert tranche1['display_name'] == 'Test Tranche 1'
        assert tranche1['description'] == 'First test tranche'
        assert 'config' in tranche1
        assert tranche1['config']['imprint'] == 'test_imprint'
    
    def test_refresh_tranche_dropdown(self):
        """Test refreshing tranche dropdown options"""
        options = self.manager.refresh_tranche_dropdown()
        
        assert len(options) == 2
        assert 'Test Tranche 1' in options
        assert 'Test Tranche 2' in options
    
    def test_get_tranche_names(self):
        """Test getting list of tranche names"""
        names = self.manager.get_tranche_names()
        
        assert len(names) == 2
        assert 'test_tranche_1' in names
        assert 'test_tranche_2' in names
    
    def test_validate_tranche_selection_valid(self):
        """Test validation of valid tranche selection"""
        self.manager._load_available_tranches()
        
        assert self.manager.validate_tranche_selection('test_tranche_1') is True
        assert self.manager.validate_tranche_selection('Test Tranche 1') is True
    
    def test_validate_tranche_selection_invalid(self):
        """Test validation of invalid tranche selection"""
        self.manager._load_available_tranches()
        
        assert self.manager.validate_tranche_selection('nonexistent_tranche') is False
        assert self.manager.validate_tranche_selection('') is False
        assert self.manager.validate_tranche_selection(None) is False
    
    def test_get_tranche_config(self):
        """Test retrieving tranche configuration"""
        self.manager._load_available_tranches()
        
        config = self.manager.get_tranche_config('test_tranche_1')
        
        assert config is not None
        assert config['imprint'] == 'test_imprint'
        assert config['publisher'] == 'test_publisher'
        assert config['contributor_one'] == 'Test Author'
    
    def test_get_tranche_info_by_name(self):
        """Test getting tranche info by name"""
        self.manager._load_available_tranches()
        
        info = self.manager.get_tranche_info('test_tranche_1')
        
        assert info is not None
        assert info['name'] == 'test_tranche_1'
        assert info['display_name'] == 'Test Tranche 1'
    
    def test_get_tranche_info_by_display_name(self):
        """Test getting tranche info by display name"""
        self.manager._load_available_tranches()
        
        info = self.manager.get_tranche_info('Test Tranche 1')
        
        assert info is not None
        assert info['name'] == 'test_tranche_1'
        assert info['display_name'] == 'Test Tranche 1'
    
    def test_create_tranche_config(self):
        """Test creating new tranche configuration"""
        success = self.manager._create_tranche_config(
            name="new_tranche",
            display_name="New Test Tranche",
            description="A newly created tranche",
            imprint="new_imprint",
            publisher="new_publisher",
            contributor_one="New Author",
            language="es"
        )
        
        assert success is True
        
        # Verify file was created
        config_path = os.path.join(self.tranches_dir, "new_tranche.json")
        assert os.path.exists(config_path)
        
        # Verify content
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        assert config['display_name'] == 'New Test Tranche'
        assert config['imprint'] == 'new_imprint'
        assert config['contributor_one'] == 'New Author'
        assert config['language'] == 'es'
    
    def test_no_tranches_directory(self):
        """Test behavior when tranches directory doesn't exist"""
        manager = TrancheConfigUIManager()
        manager.tranches_dir = "/nonexistent/directory"
        
        tranches = manager.load_available_tranches()
        assert len(tranches) == 0
        
        options = manager.refresh_tranche_dropdown()
        assert options == ["No tranche configurations found"]
    
    def test_invalid_json_file(self):
        """Test handling of invalid JSON files"""
        # Create invalid JSON file
        invalid_path = os.path.join(self.tranches_dir, "invalid.json")
        with open(invalid_path, 'w') as f:
            f.write("invalid json content")
        
        # Should handle gracefully
        tranches = self.manager.load_available_tranches()
        
        # Should still load valid configs, skip invalid ones
        assert len(tranches) == 2  # Only the valid ones
    
    @patch('streamlit.selectbox')
    @patch('streamlit.error')
    @patch('streamlit.info')
    def test_render_tranche_selector_success(self, mock_info, mock_error, mock_selectbox):
        """Test successful rendering of tranche selector"""
        mock_selectbox.return_value = "Test Tranche 1"
        self.manager._load_available_tranches()
        
        result = self.manager.render_tranche_selector()
        
        assert result == "test_tranche_1"
        mock_selectbox.assert_called_once()
        mock_error.assert_not_called()
    
    @patch('streamlit.selectbox')
    @patch('streamlit.error')
    def test_render_tranche_selector_no_configs(self, mock_error, mock_selectbox):
        """Test rendering when no configurations are available"""
        # Empty tranches directory
        self.manager.available_tranches = []
        
        result = self.manager.render_tranche_selector()
        
        assert result is None
        mock_error.assert_called_once()
        mock_selectbox.assert_not_called()
    
    @patch('streamlit.expander')
    @patch('streamlit.columns')
    @patch('streamlit.write')
    @patch('streamlit.json')
    def test_render_tranche_details(self, mock_json, mock_write, mock_columns, mock_expander):
        """Test rendering of tranche details"""
        # Mock streamlit components
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        mock_columns.return_value = [Mock(), Mock()]
        
        self.manager._load_available_tranches()
        
        # Should not raise exception
        self.manager.render_tranche_details("test_tranche_1")
        
        mock_expander.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling for various edge cases"""
        # Test with None values
        assert self.manager.validate_tranche_selection(None) is False
        assert self.manager.get_tranche_config(None) is None
        assert self.manager.get_tranche_info(None) is None
        
        # Test with empty strings
        assert self.manager.validate_tranche_selection("") is False
        assert self.manager.get_tranche_config("") is None
        assert self.manager.get_tranche_info("") is None