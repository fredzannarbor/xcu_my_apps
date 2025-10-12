#!/usr/bin/env python3
"""
SaaS Automation Module
Handles automated tasks for each SaaS project
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

class SaaSAutomation:
    def __init__(self, project_paths):
        self.project_paths = project_paths
        self.results = {}
    
    def run_nimble_books_automation(self):
        """Run automated tasks for Nimble Books"""
        try:
            project_path = self.project_paths['nimble_books']
            
            # Check if we can run the pipeline
            result = subprocess.run(
                ["python", "run_book_pipeline.py", "--help"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.results['nimble_books'] = {
                'status': 'success' if result.returncode == 0 else 'failed',
                'last_run': datetime.now().isoformat(),
                'output': result.stdout[:500],  # Truncate output
                'action_required': result.returncode != 0
            }
            
        except Exception as e:
            self.results['nimble_books'] = {
                'status': 'error',
                'last_run': datetime.now().isoformat(),
                'output': str(e),
                'action_required': True
            }
    
    def run_xtuff_automation(self):
        """Run automated tasks for xtuff.ai"""
        try:
            project_path = self.project_paths['xtuff']
            
            # Check app status
            result = subprocess.run(
                ["python", "-c", "import app; print('xtuff loaded successfully')"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.results['xtuff'] = {
                'status': 'success' if result.returncode == 0 else 'failed',
                'last_run': datetime.now().isoformat(),
                'output': result.stdout[:500],
                'action_required': result.returncode != 0
            }
            
        except Exception as e:
            self.results['xtuff'] = {
                'status': 'error',
                'last_run': datetime.now().isoformat(),
                'output': str(e),
                'action_required': True
            }
    
    def run_altdoge_automation(self):
        """Run automated tasks for altDOGE"""
        try:
            project_path = self.project_paths['altdoge']
            
            # Basic health check
            if os.path.exists(project_path):
                self.results['altdoge'] = {
                    'status': 'success',
                    'last_run': datetime.now().isoformat(),
                    'output': 'Project directory accessible',
                    'action_required': False
                }
            else:
                self.results['altdoge'] = {
                    'status': 'failed',
                    'last_run': datetime.now().isoformat(),
                    'output': 'Project directory not found',
                    'action_required': True
                }
                
        except Exception as e:
            self.results['altdoge'] = {
                'status': 'error',
                'last_run': datetime.now().isoformat(),
                'output': str(e),
                'action_required': True
            }
    
    def run_all_automations(self):
        """Run all SaaS automations"""
        self.run_nimble_books_automation()
        self.run_xtuff_automation()
        self.run_altdoge_automation()
        
        return self.results
    
    def get_summary(self):
        """Get a summary of all automation results"""
        if not self.results:
            return "No automations run yet"
        
        summary = []
        for project, result in self.results.items():
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            action_emoji = "⚠️" if result['action_required'] else "✓"
            summary.append(f"{status_emoji} {project}: {result['status']} {action_emoji}")
        
        return "\n".join(summary)