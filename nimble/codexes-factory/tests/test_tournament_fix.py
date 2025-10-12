#!/usr/bin/env python3
"""
Test script to verify the tournament engine fix.
"""

import sys
import os
sys.path.append('src')

# Mock streamlit session state for testing
class MockSessionState:
    def __init__(self):
        self.data = {
            'advanced_ideation_initialized': True,
            'generated_concepts': [],
            'tournament_results': [],
            'reader_evaluations': []
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __contains__(self, key):
        return key in self.data
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value

# Mock streamlit
class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()
    
    def set_page_config(self, **kwargs):
        pass
    
    def title(self, text):
        print(f"TITLE: {text}")
    
    def markdown(self, text):
        print(f"MARKDOWN: {text}")
    
    def columns(self, n):
        return [MockColumn() for _ in range(n)]
    
    def metric(self, label, value):
        print(f"METRIC: {label} = {value}")
    
    def tabs(self, labels):
        return [MockTab(label) for label in labels]
    
    def error(self, message):
        print(f"ERROR: {message}")
    
    def warning(self, message):
        print(f"WARNING: {message}")
    
    def info(self, message):
        print(f"INFO: {message}")

class MockColumn:
    def metric(self, label, value):
        print(f"COLUMN METRIC: {label} = {value}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

class MockTab:
    def __init__(self, label):
        self.label = label
    
    def __enter__(self):
        print(f"ENTERING TAB: {self.label}")
        return self
    
    def __exit__(self, *args):
        print(f"EXITING TAB: {self.label}")

# Replace streamlit with mock
sys.modules['streamlit'] = MockStreamlit()
import streamlit as st

def test_dashboard_initialization():
    """Test that the dashboard initializes without errors."""
    print("Testing dashboard initialization...")
    
    try:
        # Import after mocking streamlit
        from codexes.pages.ideation_and_development import IdeationDashboard
        
        dashboard = IdeationDashboard()
        print(f"✓ Dashboard initialized successfully")
        print(f"✓ Tournament engine: {'Available' if dashboard.tournament_engine else 'Not available'}")
        print(f"✓ Database: {'Available' if dashboard.database else 'Not available'}")
        
        if dashboard.tournament_engine:
            # Test the methods that were failing
            active = dashboard.tournament_engine.get_active_tournaments()
            print(f"✓ get_active_tournaments() returned {len(active)} tournaments")
            
            history = dashboard.tournament_engine.get_tournament_history()
            print(f"✓ get_tournament_history() returned {len(history)} entries")
        
        return True
        
    except Exception as e:
        print(f"✗ Dashboard initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Tournament Engine Fix Test")
    print("=" * 40)
    
    success = test_dashboard_initialization()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! The fix should work.")
    else:
        print("✗ Tests failed. There are still issues to resolve.")