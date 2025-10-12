"""
Command Builder and Serialization for Pipeline Execution
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil


class CommandBuilder:
    """Convert UI configuration to command-line arguments"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_files = []  # Track temporary files for cleanup
    
    def build_pipeline_command(self, config: Dict[str, Any]) -> List[str]:
        """Build command-line arguments from UI configuration"""
        command = ["python", "run_book_pipeline.py"]
        
        # Core required parameters
        core_params = [
            ('imprint', '--imprint'),
            ('model', '--model'),
        ]

        # Optional schedule file parameter (only add if provided)
        schedule_file = config.get('schedule_file')
        if schedule_file and schedule_file != 'null':
            core_params.append(('schedule_file', '--schedule-file'))
        
        for param_name, flag in core_params:
            value = config.get(param_name)
            if value:
                # Handle file uploads specially
                if param_name == 'schedule_file' and hasattr(value, 'read'):
                    # This is an uploaded file, save it temporarily
                    temp_path = self._save_uploaded_file(value, 'schedule.json')
                    command.extend([flag, temp_path])
                else:
                    command.extend([flag, str(value)])
        
        # Optional parameters with values
        optional_params = [
            ('verifier_model', '--verifier-model'),
            ('start_stage', '--start-stage'),
            ('end_stage', '--end-stage'),
            ('max_books', '--max-books'),
            ('begin_with_book', '--begin-with-book'),
            ('end_with_book', '--end-with-book'),
            ('quotes_per_book', '--quotes-per-book'),
            ('only_run_prompts', '--only-run-prompts'),
            ('model_params_file', '--model-params-file'),
            ('catalog_file', '--catalog-file'),
            ('base_dir', '--base-dir'),
            ('lsi_config', '--lsi-config'),
            ('lsi_template', '--lsi-template'),
            ('tranche', '--tranche'),
            ('report_formats', '--report-formats')
        ]
        
        for param_name, flag in optional_params:
            value = config.get(param_name)
            if value not in [None, "", 0, []]:
                if isinstance(value, list):
                    command.extend([flag, ','.join(map(str, value))])
                else:
                    command.extend([flag, str(value)])
        
        # Boolean flags
        boolean_flags = [
            ('debug_cover', '--debug-cover'),
            ('catalog_only', '--catalog-only'),
            ('skip_catalog', '--skip-catalog'),
            ('skip_lsi', '--skip-lsi'),
            ('enable_llm_completion', '--enable-llm-completion'),
            ('enable_isbn_assignment', '--enable-isbn-assignment'),
            ('legacy_reports', '--legacy-reports'),
            ('terse_log', '--terse-log'),
            ('no_litellm_log', '--no-litellm-log'),
            ('show_prompt_logs', '--show-prompt-logs'),
            ('verbose', '--verbose'),
            ('overwrite', '--overwrite'),
            ('enable_metadata_discovery', '--enable-metadata-discovery')
        ]
        
        for param_name, flag in boolean_flags:
            if config.get(param_name):
                command.append(flag)
        
        # Special handling for leave_build_dirs (inverted logic)
        if not config.get('leave_build_dirs', True):
            command.append('--delete-build-directories')
        
        return command
    
    def serialize_complex_parameters(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Serialize complex parameters for command-line use"""
        serialized = {}
        
        for key, value in params.items():
            if isinstance(value, (dict, list)):
                # Serialize complex objects as JSON
                try:
                    serialized[key] = json.dumps(value)
                except (TypeError, ValueError) as e:
                    self.logger.warning(f"Could not serialize parameter {key}: {e}")
                    serialized[key] = str(value)
            elif value is not None:
                serialized[key] = str(value)
        
        return serialized
    
    def handle_file_uploads(self, files: Dict[str, Any]) -> Dict[str, str]:
        """Handle file uploads and return temporary file paths"""
        file_paths = {}
        
        for key, file_obj in files.items():
            if file_obj is not None and hasattr(file_obj, 'read'):
                try:
                    # Determine file extension
                    file_name = getattr(file_obj, 'name', f'{key}.json')
                    temp_path = self._save_uploaded_file(file_obj, file_name)
                    file_paths[key] = temp_path
                    
                except Exception as e:
                    self.logger.error(f"Error handling file upload for {key}: {e}")
        
        return file_paths
    
    def _save_uploaded_file(self, file_obj, filename: str) -> str:
        """Save an uploaded file to temporary location"""
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            unique_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            unique_filename = f"{filename}_{timestamp}"
        
        temp_path = temp_dir / unique_filename
        
        try:
            # Reset file pointer to beginning
            file_obj.seek(0)
            
            # Write file content
            with open(temp_path, 'wb') as f:
                f.write(file_obj.read())
            
            # Track for cleanup
            self.temp_files.append(str(temp_path))
            
            self.logger.info(f"Saved uploaded file to: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"Error saving uploaded file: {e}")
            raise
    
    def generate_command_audit_log(self, command: List[str], config: Dict[str, Any]) -> str:
        """Generate audit-ready command log"""
        timestamp = datetime.now().isoformat()
        
        audit_log = {
            "timestamp": timestamp,
            "command": command,
            "configuration": config,
            "command_string": " ".join(command),
            "parameter_count": len([arg for arg in command if arg.startswith('--')]),
            "temp_files": self.temp_files.copy()
        }
        
        # Save audit log
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        log_filename = f"command_audit_{timestamp.replace(':', '-')}.json"
        log_path = logs_dir / log_filename
        
        try:
            with open(log_path, 'w') as f:
                json.dump(audit_log, f, indent=2, default=str)
            
            self.logger.info(f"Command audit log saved: {log_path}")
            return str(log_path)
            
        except Exception as e:
            self.logger.error(f"Error saving command audit log: {e}")
            return ""
    
    def validate_command_parameters(self, command: List[str]) -> Dict[str, Any]:
        """Validate command parameters before execution"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "parameter_count": 0,
            "required_files": []
        }
        
        # Count parameters
        validation_result["parameter_count"] = len([arg for arg in command if arg.startswith('--')])
        
        # Check for required parameters
        required_flags = ['--imprint', '--model']
        for flag in required_flags:
            if flag not in command:
                validation_result["errors"].append(f"Missing required parameter: {flag}")
                validation_result["is_valid"] = False
        
        # Check file existence
        file_flags = ['--schedule-file', '--model-params-file', '--lsi-config', '--lsi-template']
        for i, arg in enumerate(command):
            if arg in file_flags and i + 1 < len(command):
                file_path = command[i + 1]
                validation_result["required_files"].append(file_path)

                # Skip file existence check for schedule-file if it's not provided or is 'null'
                if arg == '--schedule-file' and (not file_path or file_path == 'null'):
                    continue

                if not Path(file_path).exists():
                    validation_result["errors"].append(f"File not found: {file_path}")
                    validation_result["is_valid"] = False
        
        # Check stage parameters
        start_stage = None
        end_stage = None
        
        for i, arg in enumerate(command):
            if arg == '--start-stage' and i + 1 < len(command):
                try:
                    start_stage = int(command[i + 1])
                except ValueError:
                    validation_result["errors"].append("Invalid start stage value")
                    validation_result["is_valid"] = False
            
            elif arg == '--end-stage' and i + 1 < len(command):
                try:
                    end_stage = int(command[i + 1])
                except ValueError:
                    validation_result["errors"].append("Invalid end stage value")
                    validation_result["is_valid"] = False
        
        if start_stage is not None and end_stage is not None:
            if start_stage > end_stage:
                validation_result["errors"].append("Start stage cannot be greater than end stage")
                validation_result["is_valid"] = False
            
            if start_stage < 1 or start_stage > 4:
                validation_result["errors"].append("Start stage must be between 1 and 4")
                validation_result["is_valid"] = False
            
            if end_stage < 1 or end_stage > 4:
                validation_result["errors"].append("End stage must be between 1 and 4")
                validation_result["is_valid"] = False
        
        # Check for conflicting flags
        conflicting_pairs = [
            ('--catalog-only', '--skip-catalog'),
            ('--terse-log', '--verbose')
        ]
        
        for flag1, flag2 in conflicting_pairs:
            if flag1 in command and flag2 in command:
                validation_result["warnings"].append(f"Conflicting flags: {flag1} and {flag2}")
        
        return validation_result
    
    def create_configuration_file(self, config: Dict[str, Any], filename: str = None) -> str:
        """Create a temporary configuration file from UI config"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ui_config_{timestamp}.json"
        
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        config_path = temp_dir / filename
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            # Track for cleanup
            self.temp_files.append(str(config_path))
            
            self.logger.info(f"Configuration file created: {config_path}")
            return str(config_path)
            
        except Exception as e:
            self.logger.error(f"Error creating configuration file: {e}")
            raise
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
                    self.logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Could not clean up temp file {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def get_command_summary(self, command: List[str]) -> Dict[str, Any]:
        """Get a summary of the command for display"""
        summary = {
            "script": command[1] if len(command) > 1 else "",
            "total_args": len(command) - 2,  # Exclude python and script name
            "parameters": {},
            "flags": [],
            "file_parameters": []
        }
        
        # Parse parameters and flags
        i = 2  # Skip 'python' and script name
        while i < len(command):
            arg = command[i]
            
            if arg.startswith('--'):
                if i + 1 < len(command) and not command[i + 1].startswith('--'):
                    # Parameter with value
                    param_name = arg[2:].replace('-', '_')
                    param_value = command[i + 1]
                    summary["parameters"][param_name] = param_value
                    
                    # Check if it's a file parameter
                    if any(file_flag in arg for file_flag in ['file', 'config', 'template']):
                        summary["file_parameters"].append({
                            "parameter": param_name,
                            "path": param_value,
                            "exists": Path(param_value).exists()
                        })
                    
                    i += 2
                else:
                    # Boolean flag
                    flag_name = arg[2:].replace('-', '_')
                    summary["flags"].append(flag_name)
                    i += 1
            else:
                i += 1
        
        return summary
    
    def export_configuration(self, config: Dict[str, Any], export_path: str = None) -> str:
        """Export configuration to a permanent file"""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"exported_config_{timestamp}.json"
        
        export_file = Path(export_path)
        
        # Add metadata to exported config
        export_data = {
            "_export_info": {
                "exported_at": datetime.now().isoformat(),
                "exported_from": "Streamlit UI",
                "version": "1.0"
            },
            "configuration": config
        }
        
        try:
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Configuration exported to: {export_file}")
            return str(export_file)
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            raise