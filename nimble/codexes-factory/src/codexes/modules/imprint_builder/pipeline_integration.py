"""
Integration with existing production pipeline for imprint builder.
"""

import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .imprint_expander import ExpandedImprint
from .artifact_generator import ImprintArtifactGenerator
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class PipelineIntegrator:
    """Integrates imprint builder with existing production pipeline."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Pipeline paths
        self.imprints_dir = Path("imprints")
        self.configs_dir = Path("configs/imprints")
        self.templates_dir = Path("templates")
        self.prompts_dir = Path("prompts")

    def integrate_imprint(self, imprint: ExpandedImprint, 
                         force_overwrite: bool = False) -> Dict[str, Any]:
        """Integrate an imprint into the existing pipeline."""
        try:
            imprint_name = getattr(imprint.branding, 'imprint_name', 'Unnamed Imprint')
            safe_name = imprint_name.lower().replace(' ', '_').replace('-', '_')
            
            self.logger.info(f"Integrating imprint {imprint_name} into pipeline")
            
            results = {
                'imprint_name': imprint_name,
                'safe_name': safe_name,
                'integration_date': datetime.now().isoformat(),
                'actions_taken': [],
                'warnings': [],
                'errors': []
            }
            
            # Create imprint directory structure
            imprint_dir = self.imprints_dir / safe_name
            if imprint_dir.exists() and not force_overwrite:
                results['warnings'].append(f"Imprint directory {imprint_dir} already exists")
            else:
                self._create_imprint_directory(imprint, imprint_dir, results)
            
            # Create configuration files
            self._create_configuration_files(imprint, safe_name, results)
            
            # Integrate templates
            self._integrate_templates(imprint, safe_name, results)
            
            # Integrate prompts
            self._integrate_prompts(imprint, safe_name, results)
            
            # Update global configurations
            self._update_global_configurations(imprint, safe_name, results)
            
            # Validate integration
            validation_results = self._validate_integration(safe_name)
            results['validation'] = validation_results
            
            self.logger.info(f"Integration complete for {imprint_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error integrating imprint: {e}")
            return {
                'imprint_name': getattr(imprint.branding, 'imprint_name', 'Unnamed Imprint'),
                'integration_date': datetime.now().isoformat(),
                'errors': [f"Integration failed: {str(e)}"]
            }

    def migrate_existing_imprint(self, imprint_name: str, 
                               new_definition: ExpandedImprint) -> Dict[str, Any]:
        """Migrate an existing imprint to new definition."""
        try:
            safe_name = imprint_name.lower().replace(' ', '_').replace('-', '_')
            
            self.logger.info(f"Migrating existing imprint {imprint_name}")
            
            results = {
                'imprint_name': imprint_name,
                'migration_date': datetime.now().isoformat(),
                'backup_created': False,
                'actions_taken': [],
                'warnings': [],
                'errors': []
            }
            
            # Create backup
            backup_results = self._create_backup(safe_name)
            results['backup_created'] = backup_results['success']
            if backup_results['success']:
                results['backup_location'] = backup_results['backup_path']
                results['actions_taken'].append(f"Created backup at {backup_results['backup_path']}")
            else:
                results['warnings'].append("Could not create backup")
            
            # Perform migration
            migration_results = self.integrate_imprint(new_definition, force_overwrite=True)
            
            # Merge results
            results['actions_taken'].extend(migration_results.get('actions_taken', []))
            results['warnings'].extend(migration_results.get('warnings', []))
            results['errors'].extend(migration_results.get('errors', []))
            results['validation'] = migration_results.get('validation', {})
            
            self.logger.info(f"Migration complete for {imprint_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error migrating imprint: {e}")
            return {
                'imprint_name': imprint_name,
                'migration_date': datetime.now().isoformat(),
                'errors': [f"Migration failed: {str(e)}"]
            }

    def check_compatibility(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Check compatibility with existing pipeline."""
        try:
            compatibility = {
                'overall_compatible': True,
                'issues': [],
                'recommendations': [],
                'required_updates': []
            }
            
            # Check LSI field mapping compatibility
            lsi_compatibility = self._check_lsi_compatibility(imprint)
            compatibility['lsi_compatibility'] = lsi_compatibility
            if not lsi_compatibility['compatible']:
                compatibility['overall_compatible'] = False
                compatibility['issues'].extend(lsi_compatibility['issues'])
            
            # Check template compatibility
            template_compatibility = self._check_template_compatibility(imprint)
            compatibility['template_compatibility'] = template_compatibility
            if not template_compatibility['compatible']:
                compatibility['overall_compatible'] = False
                compatibility['issues'].extend(template_compatibility['issues'])
            
            # Check field mapping compatibility
            field_compatibility = self._check_field_mapping_compatibility(imprint)
            compatibility['field_mapping_compatibility'] = field_compatibility
            if not field_compatibility['compatible']:
                compatibility['overall_compatible'] = False
                compatibility['issues'].extend(field_compatibility['issues'])
            
            # Check validation framework compatibility
            validation_compatibility = self._check_validation_compatibility(imprint)
            compatibility['validation_compatibility'] = validation_compatibility
            if not validation_compatibility['compatible']:
                compatibility['overall_compatible'] = False
                compatibility['issues'].extend(validation_compatibility['issues'])
            
            return compatibility
            
        except Exception as e:
            self.logger.error(f"Error checking compatibility: {e}")
            return {
                'overall_compatible': False,
                'issues': [f"Compatibility check failed: {str(e)}"]
            }

    def create_migration_plan(self, existing_imprints: List[str], 
                            new_definitions: List[ExpandedImprint]) -> Dict[str, Any]:
        """Create a migration plan for multiple imprints."""
        try:
            plan = {
                'created_at': datetime.now().isoformat(),
                'total_imprints': len(existing_imprints),
                'migration_phases': [],
                'estimated_duration_hours': 0,
                'risks': [],
                'prerequisites': []
            }
            
            # Phase 1: Backup and validation
            phase1 = {
                'phase': 1,
                'name': 'Backup and Validation',
                'description': 'Create backups and validate new definitions',
                'tasks': [
                    'Create backups of existing imprints',
                    'Validate new imprint definitions',
                    'Check compatibility with existing pipeline',
                    'Identify potential conflicts'
                ],
                'estimated_hours': 2,
                'dependencies': []
            }
            plan['migration_phases'].append(phase1)
            
            # Phase 2: Core infrastructure updates
            phase2 = {
                'phase': 2,
                'name': 'Infrastructure Updates',
                'description': 'Update core pipeline components',
                'tasks': [
                    'Update field mapping registry',
                    'Update validation frameworks',
                    'Update template system',
                    'Update configuration management'
                ],
                'estimated_hours': 4,
                'dependencies': [1]
            }
            plan['migration_phases'].append(phase2)
            
            # Phase 3: Imprint migration
            phase3 = {
                'phase': 3,
                'name': 'Imprint Migration',
                'description': 'Migrate individual imprints',
                'tasks': [],
                'estimated_hours': len(existing_imprints) * 0.5,
                'dependencies': [2]
            }
            
            for imprint_name in existing_imprints:
                phase3['tasks'].append(f'Migrate {imprint_name}')
            
            plan['migration_phases'].append(phase3)
            
            # Phase 4: Testing and validation
            phase4 = {
                'phase': 4,
                'name': 'Testing and Validation',
                'description': 'Test migrated imprints and validate functionality',
                'tasks': [
                    'Test template generation',
                    'Test LSI CSV generation',
                    'Test field mapping',
                    'Validate workflow integration',
                    'Performance testing'
                ],
                'estimated_hours': 3,
                'dependencies': [3]
            }
            plan['migration_phases'].append(phase4)
            
            # Calculate total duration
            plan['estimated_duration_hours'] = sum(phase['estimated_hours'] for phase in plan['migration_phases'])
            
            # Identify risks
            plan['risks'] = [
                'Data loss during migration',
                'Compatibility issues with existing books',
                'Performance degradation',
                'User workflow disruption'
            ]
            
            # Prerequisites
            plan['prerequisites'] = [
                'Full system backup',
                'Testing environment setup',
                'User notification and training',
                'Rollback plan preparation'
            ]
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error creating migration plan: {e}")
            return {
                'created_at': datetime.now().isoformat(),
                'error': f"Migration plan creation failed: {str(e)}"
            }

    def _create_imprint_directory(self, imprint: ExpandedImprint, 
                                imprint_dir: Path, results: Dict[str, Any]):
        """Create imprint directory structure."""
        try:
            imprint_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['templates', 'configs', 'docs', 'assets']
            for subdir in subdirs:
                (imprint_dir / subdir).mkdir(exist_ok=True)
            
            # Create imprint info file
            imprint_info = {
                'name': imprint.branding.imprint_name,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'description': imprint.branding.mission_statement,
                'genres': imprint.publishing.primary_genres,
                'target_audience': imprint.publishing.target_audience
            }
            
            with open(imprint_dir / 'imprint.json', 'w') as f:
                json.dump(imprint_info, f, indent=2)
            
            results['actions_taken'].append(f"Created imprint directory structure at {imprint_dir}")
            
        except Exception as e:
            results['errors'].append(f"Error creating imprint directory: {str(e)}")

    def _create_configuration_files(self, imprint: ExpandedImprint, 
                                  safe_name: str, results: Dict[str, Any]):
        """Create configuration files for the imprint."""
        try:
            # Create imprint-specific config
            config_file = self.configs_dir / f"{safe_name}.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'imprint_name': imprint.branding.imprint_name,
                'branding': imprint.branding.__dict__,
                'design': imprint.design.__dict__,
                'publishing': imprint.publishing.__dict__,
                'production': imprint.production.__dict__,
                'distribution': imprint.distribution.__dict__,
                'marketing': imprint.marketing.__dict__,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            results['actions_taken'].append(f"Created configuration file at {config_file}")
            
        except Exception as e:
            results['errors'].append(f"Error creating configuration files: {str(e)}")

    def _integrate_templates(self, imprint: ExpandedImprint, 
                           safe_name: str, results: Dict[str, Any]):
        """Integrate templates into the pipeline."""
        try:
            # Generate templates using artifact generator
            artifact_generator = ImprintArtifactGenerator(self.llm_caller)
            
            # Create temporary directory for templates
            temp_dir = Path(f"temp_{safe_name}_templates")
            template_results = artifact_generator.generate_latex_templates(imprint, str(temp_dir))
            
            if template_results.get('status') == 'success':
                # Move templates to imprint directory
                imprint_template_dir = self.imprints_dir / safe_name / 'templates'
                imprint_template_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy generated templates
                for file in temp_dir.glob('*'):
                    if file.is_file():
                        shutil.copy2(file, imprint_template_dir / file.name)
                
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                results['actions_taken'].append(f"Integrated templates for {imprint.branding.imprint_name}")
            else:
                results['errors'].append(f"Template generation failed: {template_results.get('error', 'Unknown error')}")
            
        except Exception as e:
            results['errors'].append(f"Error integrating templates: {str(e)}")

    def _integrate_prompts(self, imprint: ExpandedImprint, 
                         safe_name: str, results: Dict[str, Any]):
        """Integrate prompts into the pipeline."""
        try:
            # Generate prompts using artifact generator
            artifact_generator = ImprintArtifactGenerator(self.llm_caller)
            
            # Create prompts file
            prompts_file = self.imprints_dir / safe_name / f"prompts.json"
            prompt_results = artifact_generator.generate_llm_prompts(imprint, str(prompts_file))
            
            if prompt_results.get('status') == 'success':
                results['actions_taken'].append(f"Integrated prompts for {imprint.branding.imprint_name}")
            else:
                results['errors'].append(f"Prompt generation failed: {prompt_results.get('error', 'Unknown error')}")
            
        except Exception as e:
            results['errors'].append(f"Error integrating prompts: {str(e)}")

    def _update_global_configurations(self, imprint: ExpandedImprint, 
                                    safe_name: str, results: Dict[str, Any]):
        """Update global configuration files."""
        try:
            # Update default LSI config to include new imprint
            default_lsi_config_path = Path("configs/default_lsi_config.json")
            
            if default_lsi_config_path.exists():
                with open(default_lsi_config_path, 'r') as f:
                    default_config = json.load(f)
                
                # Add imprint-specific defaults
                if 'imprint_defaults' not in default_config:
                    default_config['imprint_defaults'] = {}
                
                default_config['imprint_defaults'][safe_name] = {
                    'imprint_name': imprint.branding.imprint_name,
                    'default_trim_size': imprint.design.trim_sizes[0] if imprint.design.trim_sizes else '6x9',
                    'primary_genres': imprint.publishing.primary_genres,
                    'target_audience': imprint.publishing.target_audience
                }
                
                # Create backup
                backup_path = default_lsi_config_path.with_suffix('.json.backup')
                shutil.copy2(default_lsi_config_path, backup_path)
                
                # Write updated config
                with open(default_lsi_config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                results['actions_taken'].append("Updated default LSI configuration")
            
        except Exception as e:
            results['warnings'].append(f"Could not update global configurations: {str(e)}")

    def _validate_integration(self, safe_name: str) -> Dict[str, Any]:
        """Validate the integration."""
        validation = {
            'valid': True,
            'checks_performed': [],
            'issues': []
        }
        
        try:
            # Check if imprint directory exists
            imprint_dir = self.imprints_dir / safe_name
            if imprint_dir.exists():
                validation['checks_performed'].append('Imprint directory exists')
            else:
                validation['valid'] = False
                validation['issues'].append('Imprint directory not found')
            
            # Check if configuration file exists
            config_file = self.configs_dir / f"{safe_name}.json"
            if config_file.exists():
                validation['checks_performed'].append('Configuration file exists')
                
                # Validate configuration file
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    required_keys = ['imprint_name', 'branding', 'design', 'publishing']
                    missing_keys = [key for key in required_keys if key not in config]
                    
                    if missing_keys:
                        validation['valid'] = False
                        validation['issues'].append(f"Configuration missing keys: {', '.join(missing_keys)}")
                    else:
                        validation['checks_performed'].append('Configuration file valid')
                        
                except json.JSONDecodeError:
                    validation['valid'] = False
                    validation['issues'].append('Configuration file contains invalid JSON')
            else:
                validation['valid'] = False
                validation['issues'].append('Configuration file not found')
            
            # Check if templates exist
            template_dir = imprint_dir / 'templates'
            if template_dir.exists() and any(template_dir.iterdir()):
                validation['checks_performed'].append('Templates directory exists and contains files')
            else:
                validation['issues'].append('Templates directory empty or missing')
            
            # Check if prompts exist
            prompts_file = imprint_dir / 'prompts.json'
            if prompts_file.exists():
                validation['checks_performed'].append('Prompts file exists')
            else:
                validation['issues'].append('Prompts file missing')
            
        except Exception as e:
            validation['valid'] = False
            validation['issues'].append(f"Validation error: {str(e)}")
        
        return validation

    def _create_backup(self, safe_name: str) -> Dict[str, Any]:
        """Create backup of existing imprint."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(f"backups/{safe_name}_{timestamp}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup imprint directory
            imprint_dir = self.imprints_dir / safe_name
            if imprint_dir.exists():
                shutil.copytree(imprint_dir, backup_dir / 'imprint', dirs_exist_ok=True)
            
            # Backup configuration
            config_file = self.configs_dir / f"{safe_name}.json"
            if config_file.exists():
                shutil.copy2(config_file, backup_dir / f"{safe_name}.json")
            
            return {
                'success': True,
                'backup_path': str(backup_dir)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _check_lsi_compatibility(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Check LSI field mapping compatibility."""
        compatibility = {
            'compatible': True,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check if required LSI fields can be mapped
            required_fields = ['title', 'author', 'isbn13', 'publisher', 'imprint']
            
            # Check if imprint has necessary information for LSI
            if not imprint.branding.imprint_name:
                compatibility['compatible'] = False
                compatibility['issues'].append('Imprint name required for LSI integration')
            
            if not imprint.publishing.primary_genres:
                compatibility['issues'].append('Primary genres recommended for BISAC category mapping')
            
            if not imprint.publishing.target_audience:
                compatibility['recommendations'].append('Target audience helps with LSI field completion')
            
        except Exception as e:
            compatibility['compatible'] = False
            compatibility['issues'].append(f"LSI compatibility check failed: {str(e)}")
        
        return compatibility

    def _check_template_compatibility(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Check template system compatibility."""
        compatibility = {
            'compatible': True,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check if design specifications are compatible with LaTeX
            if not imprint.design.typography:
                compatibility['recommendations'].append('Typography settings recommended for template generation')
            
            if not imprint.design.color_palette:
                compatibility['recommendations'].append('Color palette recommended for branded templates')
            
            if not imprint.design.trim_sizes:
                compatibility['recommendations'].append('Trim sizes should be specified for template generation')
            
        except Exception as e:
            compatibility['compatible'] = False
            compatibility['issues'].append(f"Template compatibility check failed: {str(e)}")
        
        return compatibility

    def _check_field_mapping_compatibility(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Check field mapping framework compatibility."""
        compatibility = {
            'compatible': True,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check if field mapping registry can handle imprint
            # This would integrate with existing field mapping system
            compatibility['recommendations'].append('Verify field mapping strategies work with new imprint')
            
        except Exception as e:
            compatibility['compatible'] = False
            compatibility['issues'].append(f"Field mapping compatibility check failed: {str(e)}")
        
        return compatibility

    def _check_validation_compatibility(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Check validation framework compatibility."""
        compatibility = {
            'compatible': True,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check if validation rules are compatible
            if not imprint.production.quality_standards:
                compatibility['recommendations'].append('Quality standards should be defined for validation')
            
            if not imprint.production.workflow_stages:
                compatibility['issues'].append('Workflow stages required for validation framework')
            
        except Exception as e:
            compatibility['compatible'] = False
            compatibility['issues'].append(f"Validation compatibility check failed: {str(e)}")
        
        return compatibility

    def list_integrated_imprints(self) -> List[Dict[str, Any]]:
        """List all integrated imprints."""
        try:
            imprints = []
            
            if not self.imprints_dir.exists():
                return imprints
            
            for imprint_dir in self.imprints_dir.iterdir():
                if imprint_dir.is_dir():
                    info_file = imprint_dir / 'imprint.json'
                    config_file = self.configs_dir / f"{imprint_dir.name}.json"
                    
                    imprint_info = {
                        'safe_name': imprint_dir.name,
                        'directory': str(imprint_dir),
                        'has_info_file': info_file.exists(),
                        'has_config_file': config_file.exists()
                    }
                    
                    if info_file.exists():
                        try:
                            with open(info_file, 'r') as f:
                                info = json.load(f)
                            imprint_info.update(info)
                        except Exception as e:
                            imprint_info['info_error'] = str(e)
                    
                    imprints.append(imprint_info)
            
            return imprints
            
        except Exception as e:
            self.logger.error(f"Error listing integrated imprints: {e}")
            return []

    def remove_imprint_integration(self, safe_name: str, 
                                 create_backup: bool = True) -> Dict[str, Any]:
        """Remove an imprint from the pipeline."""
        try:
            results = {
                'imprint_name': safe_name,
                'removal_date': datetime.now().isoformat(),
                'backup_created': False,
                'actions_taken': [],
                'warnings': [],
                'errors': []
            }
            
            # Create backup if requested
            if create_backup:
                backup_results = self._create_backup(safe_name)
                results['backup_created'] = backup_results['success']
                if backup_results['success']:
                    results['backup_location'] = backup_results['backup_path']
                    results['actions_taken'].append(f"Created backup at {backup_results['backup_path']}")
            
            # Remove imprint directory
            imprint_dir = self.imprints_dir / safe_name
            if imprint_dir.exists():
                shutil.rmtree(imprint_dir)
                results['actions_taken'].append(f"Removed imprint directory {imprint_dir}")
            
            # Remove configuration file
            config_file = self.configs_dir / f"{safe_name}.json"
            if config_file.exists():
                config_file.unlink()
                results['actions_taken'].append(f"Removed configuration file {config_file}")
            
            # Update global configurations
            self._remove_from_global_configurations(safe_name, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error removing imprint integration: {e}")
            return {
                'imprint_name': safe_name,
                'removal_date': datetime.now().isoformat(),
                'errors': [f"Removal failed: {str(e)}"]
            }

    def _remove_from_global_configurations(self, safe_name: str, results: Dict[str, Any]):
        """Remove imprint from global configurations."""
        try:
            # Update default LSI config
            default_lsi_config_path = Path("configs/default_lsi_config.json")
            
            if default_lsi_config_path.exists():
                with open(default_lsi_config_path, 'r') as f:
                    default_config = json.load(f)
                
                if 'imprint_defaults' in default_config and safe_name in default_config['imprint_defaults']:
                    del default_config['imprint_defaults'][safe_name]
                    
                    # Create backup
                    backup_path = default_lsi_config_path.with_suffix('.json.backup')
                    shutil.copy2(default_lsi_config_path, backup_path)
                    
                    # Write updated config
                    with open(default_lsi_config_path, 'w') as f:
                        json.dump(default_config, f, indent=2)
                    
                    results['actions_taken'].append("Updated default LSI configuration")
            
        except Exception as e:
            results['warnings'].append(f"Could not update global configurations: {str(e)}")