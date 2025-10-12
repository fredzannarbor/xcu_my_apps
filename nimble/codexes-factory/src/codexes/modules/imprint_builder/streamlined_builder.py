"""
Main streamlined imprint builder that orchestrates all components.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .imprint_concept import ImprintConcept, ImprintConceptParser
from .imprint_expander import ImprintExpander, ExpandedImprint
from .unified_editor import ImprintEditor, EditingSession
from .artifact_generator import ImprintArtifactGenerator
from .schedule_generator import ImprintScheduleGenerator
from .validation import ImprintValidator, ValidationResult
from .pipeline_integration import PipelineIntegrator
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class StreamlinedImprintBuilder:
    """
    Main orchestrator for the streamlined imprint builder system.
    
    This class provides a unified interface for creating, editing, and managing
    imprints through the complete workflow from concept to production-ready artifacts.
    """
    
    def __init__(self, llm_caller: Optional[LLMCaller] = None):
        """
        Initialize the streamlined imprint builder.
        
        Args:
            llm_caller: Optional LLM caller instance. If not provided, creates a new one.
        """
        self.llm_caller = llm_caller or LLMCaller()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize all components
        self.concept_parser = ImprintConceptParser(self.llm_caller)
        self.imprint_expander = ImprintExpander(self.llm_caller)
        self.imprint_editor = ImprintEditor(self.llm_caller)
        self.artifact_generator = ImprintArtifactGenerator(self.llm_caller)
        self.schedule_generator = ImprintScheduleGenerator(self.llm_caller)
        self.validator = ImprintValidator(self.llm_caller)
        self.pipeline_integrator = PipelineIntegrator(self.llm_caller)
        
        self.logger.info("Streamlined Imprint Builder initialized")

    def create_imprint_from_concept(self, concept_text: str, 
                                  additional_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a complete imprint from a concept description.
        
        Args:
            concept_text: User's description of the imprint concept
            additional_config: Optional additional configuration parameters
            
        Returns:
            Dictionary containing the created imprint and metadata
        """
        try:
            self.logger.info(f"Creating imprint from concept: {concept_text[:100]}...")
            
            result = {
                'success': True,
                'created_at': datetime.now().isoformat(),
                'concept_text': concept_text,
                'stages_completed': [],
                'warnings': [],
                'errors': []
            }
            
            # Stage 1: Parse concept
            self.logger.info("Stage 1: Parsing concept")
            concept = self.concept_parser.parse_concept(concept_text)
            
            # Apply additional configuration if provided
            if additional_config:
                # Additional config can be used during expansion phase
                # Store it for later use in the expansion process
                pass
            
            result['concept'] = concept.to_dict()
            result['stages_completed'].append('concept_parsing')
            
            # Validate concept
            concept_validation = self.validator.validate_concept(concept)
            if not concept_validation.is_valid:
                result['warnings'].append("Concept validation found issues")
            
            result['concept_validation'] = concept_validation.to_dict()
            
            # Stage 2: Expand concept
            self.logger.info("Stage 2: Expanding concept")
            expanded_imprint = self.imprint_expander.expand_concept(concept)
            
            result['expanded_imprint'] = expanded_imprint.to_dict()
            result['stages_completed'].append('concept_expansion')
            
            # Stage 3: Validate expanded imprint
            self.logger.info("Stage 3: Validating expanded imprint")
            imprint_validation = self.validator.validate_expanded_imprint(expanded_imprint)
            
            result['imprint_validation'] = imprint_validation.to_dict()
            result['stages_completed'].append('imprint_validation')
            
            # Apply auto-fixes if available
            if imprint_validation.auto_fixes_available:
                self.logger.info("Applying automatic fixes")
                fix_results = self.validator.auto_fix_issues(expanded_imprint, imprint_validation)
                result['auto_fixes'] = fix_results
                
                # Re-validate after fixes
                imprint_validation = self.validator.validate_expanded_imprint(expanded_imprint)
                result['imprint_validation'] = imprint_validation.to_dict()
            
            # Stage 4: Check pipeline compatibility
            self.logger.info("Stage 4: Checking pipeline compatibility")
            compatibility = self.pipeline_integrator.check_compatibility(expanded_imprint)
            
            result['pipeline_compatibility'] = compatibility
            result['stages_completed'].append('compatibility_check')
            
            if not compatibility['overall_compatible']:
                result['warnings'].extend(compatibility['issues'])
            
            # Store the final imprint
            result['final_imprint'] = expanded_imprint
            
            self.logger.info(f"Successfully created imprint: {expanded_imprint.branding.imprint_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating imprint: {e}")
            return {
                'success': False,
                'error': str(e),
                'created_at': datetime.now().isoformat(),
                'concept_text': concept_text
            }

    def create_complete_imprint_package(self, concept_text: str, 
                                      output_dir: str,
                                      additional_config: Optional[Dict[str, Any]] = None,
                                      generate_schedule: bool = True,
                                      integrate_pipeline: bool = False) -> Dict[str, Any]:
        """
        Create a complete imprint package with all artifacts and schedules.
        
        Args:
            concept_text: User's description of the imprint concept
            output_dir: Directory to save all generated files
            additional_config: Optional additional configuration
            generate_schedule: Whether to generate publication schedule
            integrate_pipeline: Whether to integrate with existing pipeline
            
        Returns:
            Dictionary containing all results and file locations
        """
        try:
            self.logger.info("Creating complete imprint package")
            
            # Create base imprint
            imprint_result = self.create_imprint_from_concept(concept_text, additional_config)
            
            if not imprint_result['success']:
                return imprint_result
            
            expanded_imprint = imprint_result['final_imprint']
            
            result = {
                'success': True,
                'imprint_name': expanded_imprint.branding.imprint_name,
                'output_directory': output_dir,
                'created_at': datetime.now().isoformat(),
                'components': {},
                'files_created': [],
                'warnings': imprint_result.get('warnings', []),
                'errors': []
            }
            
            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save imprint definition
            imprint_file = output_path / 'imprint_definition.json'
            with open(imprint_file, 'w') as f:
                import json
                json.dump(expanded_imprint.to_dict(), f, indent=2, default=str)
            
            result['files_created'].append(str(imprint_file))
            result['imprint_definition_file'] = str(imprint_file)
            
            # Generate all artifacts
            self.logger.info("Generating artifacts")
            artifact_results = self.artifact_generator.generate_all_artifacts(
                expanded_imprint, str(output_path / 'artifacts')
            )
            
            result['components']['artifacts'] = artifact_results
            
            if artifact_results.get('errors'):
                result['errors'].extend(artifact_results['errors'])
            
            # Generate schedule if requested
            if generate_schedule:
                self.logger.info("Generating publication schedule")
                try:
                    schedules = self.schedule_generator.generate_initial_schedule(expanded_imprint)
                    schedule_file = output_path / 'publication_schedule.json'
                    
                    self.schedule_generator.save_schedule(schedules, str(schedule_file))
                    
                    result['components']['schedule'] = {
                        'status': 'success',
                        'books_scheduled': len(schedules),
                        'schedule_file': str(schedule_file)
                    }
                    result['files_created'].append(str(schedule_file))
                    
                except Exception as e:
                    result['components']['schedule'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    result['errors'].append(f"Schedule generation failed: {str(e)}")
            
            # Integrate with pipeline if requested
            if integrate_pipeline:
                self.logger.info("Integrating with pipeline")
                try:
                    integration_results = self.pipeline_integrator.integrate_imprint(expanded_imprint)
                    result['components']['pipeline_integration'] = integration_results
                    
                    if integration_results.get('errors'):
                        result['errors'].extend(integration_results['errors'])
                    
                except Exception as e:
                    result['components']['pipeline_integration'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    result['errors'].append(f"Pipeline integration failed: {str(e)}")
            
            # Generate summary report
            summary_file = output_path / 'imprint_summary.md'
            summary_content = self._generate_summary_report(expanded_imprint, result)
            
            with open(summary_file, 'w') as f:
                f.write(summary_content)
            
            result['files_created'].append(str(summary_file))
            result['summary_file'] = str(summary_file)
            
            # Final validation of all components
            self.logger.info("Performing final validation")
            final_validation = self._validate_complete_package(output_path, result)
            result['final_validation'] = final_validation
            
            self.logger.info(f"Complete imprint package created at {output_dir}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating complete imprint package: {e}")
            return {
                'success': False,
                'error': str(e),
                'created_at': datetime.now().isoformat(),
                'concept_text': concept_text
            }

    def edit_imprint(self, imprint: ExpandedImprint, session_id: Optional[str] = None) -> EditingSession:
        """
        Create an editing session for an imprint.
        
        Args:
            imprint: The imprint to edit
            session_id: Optional session ID
            
        Returns:
            EditingSession for making changes
        """
        return self.imprint_editor.create_editing_session(imprint, session_id)

    def validate_imprint_package(self, package_dir: str) -> Dict[str, Any]:
        """
        Validate a complete imprint package.
        
        Args:
            package_dir: Directory containing the imprint package
            
        Returns:
            Validation results for all components
        """
        try:
            package_path = Path(package_dir)
            
            validation_results = {
                'overall_valid': True,
                'package_directory': str(package_path),
                'validated_at': datetime.now().isoformat(),
                'component_validations': {},
                'issues': [],
                'recommendations': []
            }
            
            # Validate imprint definition
            imprint_file = package_path / 'imprint_definition.json'
            if imprint_file.exists():
                try:
                    with open(imprint_file, 'r') as f:
                        import json
                        imprint_data = json.load(f)
                    
                    # Reconstruct imprint for validation
                    concept = ImprintConcept.from_dict(imprint_data['concept'])
                    expanded_imprint = ExpandedImprint(concept=concept)
                    
                    # Basic reconstruction (simplified)
                    expanded_imprint.branding.__dict__.update(imprint_data['branding'])
                    expanded_imprint.design.__dict__.update(imprint_data['design'])
                    expanded_imprint.publishing.__dict__.update(imprint_data['publishing'])
                    
                    imprint_validation = self.validator.validate_expanded_imprint(expanded_imprint)
                    validation_results['component_validations']['imprint'] = imprint_validation.to_dict()
                    
                    if not imprint_validation.is_valid:
                        validation_results['overall_valid'] = False
                        validation_results['issues'].extend([
                            issue.message for issue in imprint_validation.get_errors()
                        ])
                    
                except Exception as e:
                    validation_results['component_validations']['imprint'] = {
                        'valid': False,
                        'error': str(e)
                    }
                    validation_results['overall_valid'] = False
                    validation_results['issues'].append(f"Imprint definition validation failed: {str(e)}")
            else:
                validation_results['issues'].append("Imprint definition file not found")
                validation_results['overall_valid'] = False
            
            # Validate artifacts
            artifacts_dir = package_path / 'artifacts'
            if artifacts_dir.exists():
                artifact_validation = self.artifact_generator.validate_artifacts(str(artifacts_dir))
                validation_results['component_validations']['artifacts'] = artifact_validation
                
                if not artifact_validation.get('overall_valid', True):
                    validation_results['overall_valid'] = False
                    validation_results['issues'].extend(artifact_validation.get('issues', []))
            
            # Validate templates
            templates_dir = artifacts_dir / 'templates' if artifacts_dir.exists() else None
            if templates_dir and templates_dir.exists():
                template_validation = self.validator.validate_template_compilation(str(templates_dir))
                validation_results['component_validations']['templates'] = template_validation.to_dict()
                
                if not template_validation.is_valid:
                    validation_results['overall_valid'] = False
                    validation_results['issues'].extend([
                        issue.message for issue in template_validation.get_errors()
                    ])
            
            # Validate prompts
            prompts_file = artifacts_dir / 'prompts.json' if artifacts_dir.exists() else None
            if prompts_file and prompts_file.exists():
                prompt_validation = self.validator.validate_prompt_effectiveness(str(prompts_file))
                validation_results['component_validations']['prompts'] = prompt_validation.to_dict()
                
                if not prompt_validation.is_valid:
                    validation_results['overall_valid'] = False
                    validation_results['issues'].extend([
                        issue.message for issue in prompt_validation.get_errors()
                    ])
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating imprint package: {e}")
            return {
                'overall_valid': False,
                'error': str(e),
                'validated_at': datetime.now().isoformat()
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of all system components.
        
        Returns:
            System status information
        """
        try:
            status = {
                'system_healthy': True,
                'checked_at': datetime.now().isoformat(),
                'components': {},
                'issues': []
            }
            
            # Check LLM caller
            try:
                # Simple test call
                test_response = self.llm_caller.call_model_with_prompt(
                    model_name="mistral",
                    prompt_config={"prompt": "Test"},
                    response_format_type="text"
                )
                status['components']['llm_caller'] = {
                    'status': 'healthy',
                    'test_successful': bool(test_response)
                }
            except Exception as e:
                status['components']['llm_caller'] = {
                    'status': 'error',
                    'error': str(e)
                }
                status['system_healthy'] = False
                status['issues'].append(f"LLM caller error: {str(e)}")
            
            # Check component initialization
            components = [
                'concept_parser', 'imprint_expander', 'imprint_editor',
                'artifact_generator', 'schedule_generator', 'validator',
                'pipeline_integrator'
            ]
            
            for component_name in components:
                component = getattr(self, component_name, None)
                if component:
                    status['components'][component_name] = {'status': 'initialized'}
                else:
                    status['components'][component_name] = {'status': 'missing'}
                    status['system_healthy'] = False
                    status['issues'].append(f"Component {component_name} not initialized")
            
            return status
            
        except Exception as e:
            return {
                'system_healthy': False,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }

    def _generate_summary_report(self, imprint: ExpandedImprint, creation_results: Dict[str, Any]) -> str:
        """Generate a summary report for the created imprint."""
        
        report = f"""# {imprint.branding.imprint_name} - Imprint Summary

**Created:** {creation_results['created_at']}
**Output Directory:** {creation_results['output_directory']}

## Overview

{imprint.branding.mission_statement}

**Tagline:** {imprint.branding.tagline}

## Brand Identity

### Core Values
{chr(10).join(f'- {value}' for value in imprint.branding.brand_values)}

### Unique Selling Proposition
{imprint.branding.unique_selling_proposition}

### Brand Voice
{imprint.branding.brand_voice}

## Publishing Strategy

**Primary Genres:** {', '.join(imprint.publishing.primary_genres)}
**Target Audience:** {imprint.publishing.target_audience}
**Publication Frequency:** {imprint.publishing.publication_frequency}

## Design Guidelines

### Color Palette
{chr(10).join(f'- **{name.title()}:** {color}' for name, color in imprint.design.color_palette.items())}

### Typography
{chr(10).join(f'- **{font_type.replace("_", " ").title()}:** {font_name}' for font_type, font_name in imprint.design.typography.items())}

### Trim Sizes
{', '.join(imprint.design.trim_sizes)}

## Production Workflow

{chr(10).join(f'{i+1}. {stage}' for i, stage in enumerate(imprint.production.workflow_stages))}

## Distribution Strategy

**Primary Channels:** {', '.join(imprint.distribution.primary_channels)}
**Secondary Channels:** {', '.join(imprint.distribution.secondary_channels)}
**International Distribution:** {'Yes' if imprint.distribution.international_distribution else 'No'}
**Digital First:** {'Yes' if imprint.distribution.digital_first else 'No'}

## Generated Components

### Files Created
{chr(10).join(f'- {file}' for file in creation_results.get('files_created', []))}

### Artifacts Generated
"""
        
        # Add artifact details
        artifacts = creation_results.get('components', {}).get('artifacts', {}).get('artifacts', {})
        for artifact_type, artifact_result in artifacts.items():
            status = "✅" if artifact_result.get('status') == 'success' else "❌"
            report += f"\n**{artifact_type.title()}:** {status}"
            
            if artifact_result.get('status') == 'success' and 'files_generated' in artifact_result:
                for file in artifact_result['files_generated']:
                    report += f"\n  - {file}"
        
        # Add schedule information
        schedule_info = creation_results.get('components', {}).get('schedule', {})
        if schedule_info.get('status') == 'success':
            report += f"\n\n### Publication Schedule\n"
            report += f"**Books Scheduled:** {schedule_info.get('books_scheduled', 0)}\n"
            report += f"**Schedule File:** {schedule_info.get('schedule_file', 'N/A')}\n"
        
        # Add validation summary
        validation = creation_results.get('final_validation', {})
        if validation:
            report += f"\n\n## Validation Results\n"
            report += f"**Overall Valid:** {'Yes' if validation.get('overall_valid', False) else 'No'}\n"
            
            if validation.get('issues'):
                report += f"\n### Issues Found\n"
                for issue in validation['issues']:
                    report += f"- {issue}\n"
        
        report += f"\n\n---\n*Generated by Streamlined Imprint Builder on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return report

    def _validate_complete_package(self, package_path: Path, creation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the complete package after creation."""
        
        validation = {
            'overall_valid': True,
            'components_validated': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check if all expected files exist
            expected_files = ['imprint_definition.json', 'imprint_summary.md']
            
            for file in expected_files:
                file_path = package_path / file
                if file_path.exists():
                    validation['components_validated'] += 1
                else:
                    validation['issues'].append(f"Missing expected file: {file}")
                    validation['overall_valid'] = False
            
            # Check artifacts directory
            artifacts_dir = package_path / 'artifacts'
            if artifacts_dir.exists():
                validation['components_validated'] += 1
                
                # Check for key artifact types
                expected_artifacts = ['templates', 'configs']
                for artifact_type in expected_artifacts:
                    artifact_path = artifacts_dir / artifact_type
                    if not artifact_path.exists():
                        validation['issues'].append(f"Missing artifact directory: {artifact_type}")
            else:
                validation['issues'].append("Missing artifacts directory")
                validation['overall_valid'] = False
            
            # Add recommendations based on what was created
            if creation_results.get('components', {}).get('schedule', {}).get('status') != 'success':
                validation['recommendations'].append("Consider generating a publication schedule")
            
            if not creation_results.get('components', {}).get('pipeline_integration'):
                validation['recommendations'].append("Consider integrating with the existing pipeline")
            
        except Exception as e:
            validation['overall_valid'] = False
            validation['issues'].append(f"Package validation error: {str(e)}")
        
        return validation