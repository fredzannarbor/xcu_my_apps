"""
Comprehensive validation and error handling for imprint builder.
"""

import logging
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from .imprint_concept import ImprintConcept
from .imprint_expander import ExpandedImprint
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'concept', 'branding', 'design', 'publishing', etc.
    field: str
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'severity': self.severity,
            'category': self.category,
            'field': self.field,
            'message': self.message,
            'suggestion': self.suggestion,
            'auto_fixable': self.auto_fixable
        }


@dataclass
class ValidationResult:
    """Complete validation result."""
    is_valid: bool
    overall_score: float = 0.0  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    category_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    auto_fixes_available: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    
    # Additional properties expected by the code
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    completeness_score: float = 0.0
    
    def __post_init__(self):
        """Initialize derived properties from issues."""
        self.errors = [issue.message for issue in self.issues if issue.severity == 'error']
        self.warnings = [issue.message for issue in self.issues if issue.severity == 'warning']
        self.suggestions = [issue.suggestion for issue in self.issues if issue.suggestion and issue.severity == 'info']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'is_valid': self.is_valid,
            'overall_score': self.overall_score,
            'completeness_score': self.completeness_score,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'recommendations': self.recommendations,
            'auto_fixes_available': self.auto_fixes_available,
            'validated_at': self.validated_at.isoformat(),
            'issues': [issue.to_dict() for issue in self.issues],
            'category_scores': self.category_scores
        }
    
    def get_errors(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == 'error']
    
    def get_warnings(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == 'warning']
    
    def get_info(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == 'info']
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'overall_score': self.overall_score,
            'issues': [issue.to_dict() for issue in self.issues],
            'category_scores': self.category_scores,
            'recommendations': self.recommendations,
            'auto_fixes_available': self.auto_fixes_available,
            'validated_at': self.validated_at.isoformat(),
            'summary': {
                'total_issues': len(self.issues),
                'errors': len(self.get_errors()),
                'warnings': len(self.get_warnings()),
                'info': len(self.get_info())
            }
        }


class ImprintValidator:
    """Comprehensive validator for imprint definitions."""
    
    def __init__(self, llm_caller: Optional[LLMCaller] = None):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load validation rules
        self.validation_rules = self._load_validation_rules()
        self.field_validators = self._initialize_field_validators()

    def validate_concept(self, concept: ImprintConcept) -> ValidationResult:
        """Validate an imprint concept."""
        result = ValidationResult(is_valid=True, overall_score=0.0)
        
        try:
            # Validate basic concept structure
            self._validate_concept_structure(concept, result)
            
            # Validate concept content
            self._validate_concept_content(concept, result)
            
            # Validate concept completeness
            self._validate_concept_completeness(concept, result)
            
            # Calculate scores
            self._calculate_concept_scores(concept, result)
            
            # Generate recommendations
            self._generate_concept_recommendations(concept, result)
            
        except Exception as e:
            self.logger.error(f"Error validating concept: {e}")
            result.issues.append(ValidationIssue(
                severity='error',
                category='validation',
                field='system',
                message=f"Validation system error: {str(e)}"
            ))
            result.is_valid = False
        
        return result

    def validate_expanded_imprint(self, imprint: ExpandedImprint) -> ValidationResult:
        """Validate an expanded imprint definition."""
        result = ValidationResult(is_valid=True, overall_score=0.0)
        
        try:
            # Validate each component
            self._validate_branding_component(imprint.branding, result)
            self._validate_design_component(imprint.design_specifications, result)
            self._validate_publishing_component(imprint.publishing_strategy, result)
            self._validate_production_component(imprint.operational_framework, result)
            self._validate_distribution_component(imprint.operational_framework, result)
            self._validate_marketing_component(imprint.marketing_approach, result)
            
            # Validate cross-component consistency
            self._validate_component_consistency(imprint, result)
            
            # Validate business logic
            self._validate_business_logic(imprint, result)
            
            # Calculate overall scores
            self._calculate_overall_scores(result)
            
            # Generate recommendations
            self._generate_imprint_recommendations(imprint, result)
            
        except Exception as e:
            self.logger.error(f"Error validating expanded imprint: {e}")
            result.issues.append(ValidationIssue(
                severity='error',
                category='validation',
                field='system',
                message=f"Validation system error: {str(e)}"
            ))
            result.is_valid = False
        
        return result

    def validate_template_compilation(self, template_dir: str) -> ValidationResult:
        """Validate LaTeX template compilation."""
        result = ValidationResult(is_valid=True, overall_score=1.0)
        
        try:
            template_path = Path(template_dir)
            
            # Check if template directory exists
            if not template_path.exists():
                result.issues.append(ValidationIssue(
                    severity='error',
                    category='template',
                    field='directory',
                    message=f"Template directory {template_dir} does not exist"
                ))
                result.is_valid = False
                return result
            
            # Check for required template files
            required_files = ['template.tex', 'styles.sty']
            for filename in required_files:
                file_path = template_path / filename
                if not file_path.exists():
                    result.issues.append(ValidationIssue(
                        severity='error',
                        category='template',
                        field=filename,
                        message=f"Required template file {filename} is missing",
                        suggestion=f"Generate {filename} using the artifact generator"
                    ))
                    result.is_valid = False
                elif file_path.stat().st_size == 0:
                    result.issues.append(ValidationIssue(
                        severity='error',
                        category='template',
                        field=filename,
                        message=f"Template file {filename} is empty"
                    ))
                    result.is_valid = False
            
            # Validate template syntax
            self._validate_latex_syntax(template_path, result)
            
            # Test compilation if possible
            self._test_template_compilation(template_path, result)
            
        except Exception as e:
            self.logger.error(f"Error validating template compilation: {e}")
            result.issues.append(ValidationIssue(
                severity='error',
                category='template',
                field='validation',
                message=f"Template validation error: {str(e)}"
            ))
            result.is_valid = False
        
        return result

    def validate_prompt_effectiveness(self, prompts_file: str) -> ValidationResult:
        """Validate LLM prompt effectiveness."""
        result = ValidationResult(is_valid=True, overall_score=1.0)
        
        try:
            if not Path(prompts_file).exists():
                result.issues.append(ValidationIssue(
                    severity='error',
                    category='prompts',
                    field='file',
                    message=f"Prompts file {prompts_file} does not exist"
                ))
                result.is_valid = False
                return result
            
            # Load prompts
            with open(prompts_file, 'r') as f:
                prompts_data = json.load(f)
            
            # Validate prompt structure
            self._validate_prompt_structure(prompts_data, result)
            
            # Validate prompt content
            self._validate_prompt_content(prompts_data, result)
            
            # Test prompt effectiveness if LLM caller available
            if self.llm_caller:
                self._test_prompt_effectiveness(prompts_data, result)
            
        except Exception as e:
            self.logger.error(f"Error validating prompt effectiveness: {e}")
            result.issues.append(ValidationIssue(
                severity='error',
                category='prompts',
                field='validation',
                message=f"Prompt validation error: {str(e)}"
            ))
            result.is_valid = False
        
        return result

    def validate_configuration_consistency(self, config_files: List[str]) -> ValidationResult:
        """Validate configuration file consistency."""
        result = ValidationResult(is_valid=True, overall_score=1.0)
        
        try:
            configs = {}
            
            # Load all configuration files
            for config_file in config_files:
                if not Path(config_file).exists():
                    result.issues.append(ValidationIssue(
                        severity='warning',
                        category='config',
                        field='file',
                        message=f"Configuration file {config_file} does not exist"
                    ))
                    continue
                
                try:
                    with open(config_file, 'r') as f:
                        configs[config_file] = json.load(f)
                except json.JSONDecodeError as e:
                    result.issues.append(ValidationIssue(
                        severity='error',
                        category='config',
                        field='syntax',
                        message=f"Invalid JSON in {config_file}: {str(e)}"
                    ))
                    result.is_valid = False
            
            # Validate consistency across configurations
            self._validate_config_consistency(configs, result)
            
        except Exception as e:
            self.logger.error(f"Error validating configuration consistency: {e}")
            result.issues.append(ValidationIssue(
                severity='error',
                category='config',
                field='validation',
                message=f"Configuration validation error: {str(e)}"
            ))
            result.is_valid = False
        
        return result

    def auto_fix_issues(self, imprint: ExpandedImprint, 
                       validation_result: ValidationResult) -> Dict[str, Any]:
        """Automatically fix issues where possible."""
        fixes_applied = []
        fixes_failed = []
        
        try:
            for issue in validation_result.issues:
                if issue.auto_fixable:
                    try:
                        fix_result = self._apply_auto_fix(imprint, issue)
                        if fix_result['success']:
                            fixes_applied.append({
                                'issue': issue.to_dict(),
                                'fix_applied': fix_result['description']
                            })
                        else:
                            fixes_failed.append({
                                'issue': issue.to_dict(),
                                'error': fix_result['error']
                            })
                    except Exception as e:
                        fixes_failed.append({
                            'issue': issue.to_dict(),
                            'error': str(e)
                        })
            
            return {
                'fixes_applied': fixes_applied,
                'fixes_failed': fixes_failed,
                'total_fixable': len([i for i in validation_result.issues if i.auto_fixable]),
                'total_fixed': len(fixes_applied)
            }
            
        except Exception as e:
            self.logger.error(f"Error applying auto fixes: {e}")
            return {
                'fixes_applied': [],
                'fixes_failed': [],
                'error': str(e)
            }

    def _validate_concept_structure(self, concept: ImprintConcept, result: ValidationResult):
        """Validate concept structure."""
        if not concept.raw_input:
            result.issues.append(ValidationIssue(
                severity='error',
                category='concept',
                field='raw_input',
                message="Raw input is required"
            ))
            result.is_valid = False
        elif len(concept.raw_input.strip()) < 10:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='concept',
                field='raw_input',
                message="Concept description is very short",
                suggestion="Provide more detailed description for better results"
            ))

    def _validate_concept_content(self, concept: ImprintConcept, result: ValidationResult):
        """Validate concept content quality."""
        # Since we don't have confidence_score in our ImprintConcept, skip this check
        # or add a simple quality check based on description length
        if len(concept.description) < 50:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='concept',
                field='description',
                message="Concept description is quite brief",
                suggestion="Provide more specific details about themes, audience, and requirements"
            ))
        
        if not concept.genre_focus:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='concept',
                field='genre_focus',
                message="No genre focus specified",
                suggestion="Include specific genres or subject areas in your description"
            ))
        
        if not concept.target_audience:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='concept',
                field='audience',
                message="Target audience not identified",
                suggestion="Specify who your primary readers will be"
            ))

    def _validate_concept_completeness(self, concept: ImprintConcept, result: ValidationResult):
        """Validate concept completeness."""
        completeness_factors = {
            'name': bool(concept.name),
            'description': len(concept.description) > 20,
            'audience': bool(concept.target_audience),
            'genre_focus': len(concept.genre_focus) > 0,
            'unique_value_proposition': bool(concept.unique_value_proposition)
        }
        
        completeness_score = sum(completeness_factors.values()) / len(completeness_factors)
        
        if completeness_score < 0.5:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='concept',
                field='completeness',
                message=f"Concept is incomplete ({completeness_score:.1%})",
                suggestion="Provide more details about missing elements"
            ))

    def _validate_branding_component(self, branding: Dict[str, Any], result: ValidationResult):
        """Validate branding component."""
        # Imprint name validation
        if not branding.get('imprint_name'):
            result.issues.append(ValidationIssue(
                severity='error',
                category='branding',
                field='imprint_name',
                message="Imprint name is required",
                auto_fixable=True
            ))
            result.is_valid = False
        elif len(branding.get('imprint_name', '')) > 50:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='branding',
                field='imprint_name',
                message="Imprint name is very long",
                suggestion="Consider a shorter, more memorable name"
            ))
        
        # Mission statement validation
        if not branding.get('mission_statement'):
            result.issues.append(ValidationIssue(
                severity='warning',
                category='branding',
                field='mission_statement',
                message="Mission statement is recommended",
                suggestion="Define your imprint's purpose and goals"
            ))
        elif len(branding.get('mission_statement', '')) < 20:
            result.issues.append(ValidationIssue(
                severity='info',
                category='branding',
                field='mission_statement',
                message="Mission statement is very brief",
                suggestion="Consider expanding to better communicate your vision"
            ))
        
        # Brand values validation
        brand_values = branding.get('brand_values', [])
        if not brand_values:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='branding',
                field='brand_values',
                message="Brand values are recommended",
                suggestion="Define 3-5 core values that guide your imprint"
            ))
        elif len(brand_values) > 7:
            result.issues.append(ValidationIssue(
                severity='info',
                category='branding',
                field='brand_values',
                message="Many brand values listed",
                suggestion="Consider focusing on 3-5 core values for clarity"
            ))
        
        # Tagline validation
        tagline = branding.get('tagline', '')
        if tagline and len(tagline) > 100:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='branding',
                field='tagline',
                message="Tagline is very long",
                suggestion="Keep taglines short and memorable (under 100 characters)"
            ))
        
        # USP validation
        usp = branding.get('unique_selling_proposition', '')
        if not usp:
            result.issues.append(ValidationIssue(
                severity='info',
                category='branding',
                field='unique_selling_proposition',
                message="Unique selling proposition is recommended",
                suggestion="Define what makes your imprint distinctive"
            ))
        elif len(branding.get('mission_statement', '')) < 20:
            result.issues.append(ValidationIssue(
                severity='info',
                category='branding',
                field='mission_statement',
                message="Mission statement is quite brief",
                suggestion="Consider expanding to better communicate your vision"
            ))
        
        if not branding.get('brand_values'):
            result.issues.append(ValidationIssue(
                severity='info',
                category='branding',
                field='brand_values',
                message="Brand values help define your identity",
                suggestion="Define 3-5 core values that guide your imprint"
            ))

    def _validate_design_component(self, design: Dict[str, Any], result: ValidationResult):
        """Validate design component."""
        # Color palette validation
        color_palette = design.get('color_palette', {})
        if not color_palette:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='design',
                field='color_palette',
                message="Color palette not defined",
                suggestion="Define primary, secondary, and accent colors"
            ))
        else:
            # Validate individual colors
            required_colors = ['primary', 'secondary', 'accent']
            for color_type in required_colors:
                color_value = color_palette.get(color_type)
                if not color_value:
                    result.issues.append(ValidationIssue(
                        severity='info',
                        category='design',
                        field=f'color_palette.{color_type}',
                        message=f"{color_type.title()} color not defined",
                        suggestion=f"Define a {color_type} color for your brand palette"
                    ))
                elif not self._is_valid_hex_color(color_value):
                    result.issues.append(ValidationIssue(
                        severity='warning',
                        category='design',
                        field=f'color_palette.{color_type}',
                        message=f"Invalid {color_type} color format",
                        suggestion="Use valid hex color format (e.g., #FF0000)"
                    ))
        
        # Typography validation
        typography = design.get('typography', {})
        if not typography:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='design',
                field='typography',
                message="Typography not defined",
                suggestion="Define font preferences for your imprint"
            ))
        else:
            # Check for essential typography fields
            essential_fonts = ['primary_font', 'secondary_font', 'body_font']
            for font_type in essential_fonts:
                if not typography.get(font_type):
                    result.issues.append(ValidationIssue(
                        severity='info',
                        category='design',
                        field=f'typography.{font_type}',
                        message=f"{font_type.replace('_', ' ').title()} not specified",
                        suggestion=f"Specify a {font_type.replace('_', ' ')} for consistency"
                    ))
        
        # Visual motifs validation
        visual_motifs = design.get('visual_motifs', [])
        if not visual_motifs:
            result.issues.append(ValidationIssue(
                severity='info',
                category='design',
                field='visual_motifs',
                message="Visual motifs not defined",
                suggestion="Define recurring visual elements for brand consistency"
            ))
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Validate hex color format."""
        if not isinstance(color, str):
            return False
        import re
        return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))
    def _validate_publishing_component(self, publishing: Dict[str, Any], result: ValidationResult):
        """Validate publishing component."""
        if not publishing.get('primary_genres'):
            result.issues.append(ValidationIssue(
                severity='warning',
                category='design',
                field='typography',
                message="Typography not defined",
                suggestion="Specify fonts for headings and body text"
            ))
        
        if not design.get('trim_sizes'):
            result.issues.append(ValidationIssue(
                severity='info',
                category='design',
                field='trim_sizes',
                message="No trim sizes specified",
                suggestion="Define preferred book sizes (e.g., 6x9, 5.5x8.5)"
            ))

    def _validate_publishing_component(self, publishing: Dict[str, Any], result: ValidationResult):
        """Validate publishing component."""
        if not publishing.get('primary_genres'):
            result.issues.append(ValidationIssue(
                severity='error',
                category='publishing',
                field='primary_genres',
                message="Primary genres are required",
                auto_fixable=True
            ))
            result.is_valid = False
        elif len(publishing.get('primary_genres', [])) > 5:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='publishing',
                field='primary_genres',
                message="Too many primary genres may dilute focus",
                suggestion="Consider limiting to 3-5 main genres"
            ))
        
        if not publishing.get('target_audience'):
            result.issues.append(ValidationIssue(
                severity='warning',
                category='publishing',
                field='target_audience',
                message="Target audience should be defined",
                suggestion="Specify your primary readership"
            ))

    def _validate_production_component(self, production: Dict[str, Any], result: ValidationResult):
        """Validate production component."""
        if not production.get('workflow_stages'):
            result.issues.append(ValidationIssue(
                severity='warning',
                category='production',
                field='workflow_stages',
                message="Production workflow not defined",
                suggestion="Define your production process stages"
            ))
        
        if not production.get('quality_standards'):
            result.issues.append(ValidationIssue(
                severity='info',
                category='production',
                field='quality_standards',
                message="Quality standards help ensure consistency",
                suggestion="Define quality requirements for your publications"
            ))

    def _validate_distribution_component(self, distribution: Dict[str, Any], result: ValidationResult):
        """Validate distribution component."""
        if not distribution.get('primary_channels'):
            result.issues.append(ValidationIssue(
                severity='warning',
                category='distribution',
                field='primary_channels',
                message="Distribution channels not defined",
                suggestion="Specify where your books will be sold"
            ))

    def _validate_marketing_component(self, marketing: Dict[str, Any], result: ValidationResult):
        """Validate marketing component."""
        if not marketing.get('marketing_channels'):
            result.issues.append(ValidationIssue(
                severity='info',
                category='marketing',
                field='marketing_channels',
                message="Marketing channels help reach your audience",
                suggestion="Define how you'll promote your books"
            ))

    def _validate_component_consistency(self, imprint: ExpandedImprint, result: ValidationResult):
        """Validate consistency across components."""
        # Check audience consistency
        branding_audience = imprint.branding.get('target_audience', '')
        publishing_audience = imprint.publishing_strategy.get('target_audience', '')
        
        if branding_audience and publishing_audience and branding_audience != publishing_audience:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='consistency',
                field='target_audience',
                message="Target audience inconsistent between branding and publishing",
                suggestion="Ensure consistent audience definition across components"
            ))

    def _validate_business_logic(self, imprint: ExpandedImprint, result: ValidationResult):
        """Validate business logic and feasibility."""
        # Check if publication frequency matches resource capacity
        pub_freq = imprint.publishing_strategy.get('publication_frequency', '')
        if pub_freq:
            freq = pub_freq.lower()
            if 'weekly' in freq or 'daily' in freq:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='business',
                    field='publication_frequency',
                    message="Very high publication frequency may be challenging",
                    suggestion="Consider if you have sufficient resources for this schedule"
                ))

    def _calculate_concept_scores(self, concept: ImprintConcept, result: ValidationResult):
        """Calculate concept validation scores."""
        # Base score from description quality
        base_score = min(1.0, len(concept.description) / 100.0)  # Normalize to 0-1
        
        # Adjust for completeness
        completeness_factors = {
            'name': bool(concept.name),
            'audience': bool(concept.target_audience),
            'genre_focus': len(concept.genre_focus) > 0,
            'unique_value_proposition': bool(concept.unique_value_proposition)
        }
        completeness_score = sum(completeness_factors.values()) / len(completeness_factors)
        
        # Adjust for issues
        error_penalty = len(result.get_errors()) * 0.2
        warning_penalty = len(result.get_warnings()) * 0.1
        
        final_score = max(0.0, min(1.0, base_score * completeness_score - error_penalty - warning_penalty))
        
        result.overall_score = final_score
        result.category_scores = {
            'concept_quality': base_score,
            'completeness': completeness_score,
            'validation': 1.0 - (error_penalty + warning_penalty)
        }

    def _calculate_overall_scores(self, result: ValidationResult):
        """Calculate overall validation scores."""
        # Count issues by severity
        errors = len(result.get_errors())
        warnings = len(result.get_warnings())
        
        # Base score
        base_score = 1.0
        
        # Apply penalties
        error_penalty = errors * 0.3
        warning_penalty = warnings * 0.1
        
        final_score = max(0.0, base_score - error_penalty - warning_penalty)
        
        result.overall_score = final_score
        
        # Set validity based on errors
        if errors > 0:
            result.is_valid = False

    def _generate_concept_recommendations(self, concept: ImprintConcept, result: ValidationResult):
        """Generate recommendations for concept improvement."""
        if len(concept.description) < 50:
            result.recommendations.append("Provide more detailed description of your imprint vision")
        
        if not concept.genre_focus:
            result.recommendations.append("Include specific genres or subject areas you want to focus on")
        
        if not concept.target_audience:
            result.recommendations.append("Define your primary target audience")

    def _generate_imprint_recommendations(self, imprint: ExpandedImprint, result: ValidationResult):
        """Generate recommendations for imprint improvement."""
        # Analyze validation results and generate targeted recommendations
        categories_with_issues = set(issue.category for issue in result.issues)
        
        if 'branding' in categories_with_issues:
            result.recommendations.append("Strengthen your brand identity with clear values and messaging")
        
        if 'design' in categories_with_issues:
            result.recommendations.append("Define visual identity elements for consistent branding")
        
        if 'publishing' in categories_with_issues:
            result.recommendations.append("Clarify your publishing strategy and target market")

    def _is_valid_color(self, color_value: str) -> bool:
        """Validate color format."""
        if not color_value:
            return False
        
        # Check hex format
        if re.match(r'^#[0-9A-Fa-f]{6}$', color_value):
            return True
        
        # Check named colors (basic validation)
        named_colors = ['red', 'blue', 'green', 'black', 'white', 'gray', 'yellow', 'orange', 'purple']
        if color_value.lower() in named_colors:
            return True
        
        return False

    def _validate_latex_syntax(self, template_path: Path, result: ValidationResult):
        """Validate LaTeX syntax in templates."""
        try:
            template_file = template_path / 'template.tex'
            if template_file.exists():
                with open(template_file, 'r') as f:
                    content = f.read()
                
                # Basic LaTeX syntax checks
                if content.count('{') != content.count('}'):
                    result.issues.append(ValidationIssue(
                        severity='error',
                        category='template',
                        field='syntax',
                        message="Unmatched braces in template.tex"
                    ))
                    result.is_valid = False
                
                if '\\begin{document}' not in content:
                    result.issues.append(ValidationIssue(
                        severity='error',
                        category='template',
                        field='structure',
                        message="Missing \\begin{document} in template.tex"
                    ))
                    result.is_valid = False
                
                if '\\end{document}' not in content:
                    result.issues.append(ValidationIssue(
                        severity='error',
                        category='template',
                        field='structure',
                        message="Missing \\end{document} in template.tex"
                    ))
                    result.is_valid = False
        
        except Exception as e:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='template',
                field='validation',
                message=f"Template validation error: {str(e)}"
            ))

    def _test_template_compilation(self, template_path: Path, result: ValidationResult):
        """Test template compilation if possible."""
        # This would require LaTeX installation - for now just check basic structure
        pass

    def _validate_prompt_structure(self, prompts_data: Dict[str, Any], result: ValidationResult):
        """Validate prompt structure."""
        required_sections = ['concept_parsing', 'expansion', 'editing']
        for section in required_sections:
            if section not in prompts_data:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='prompts',
                    field=section,
                    message=f"Missing prompt section: {section}"
                ))

    def _validate_prompt_content(self, prompts_data: Dict[str, Any], result: ValidationResult):
        """Validate prompt content quality."""
        for section, prompts in prompts_data.items():
            if isinstance(prompts, dict):
                for prompt_name, prompt_text in prompts.items():
                    if not prompt_text or len(prompt_text.strip()) < 50:
                        result.issues.append(ValidationIssue(
                            severity='warning',
                            category='prompts',
                            field=f'{section}.{prompt_name}',
                            message="Prompt is too short or empty"
                        ))

    def _test_prompt_effectiveness(self, prompts_data: Dict[str, Any], result: ValidationResult):
        """Test prompt effectiveness with LLM."""
        # This would require actual LLM calls - for now just validate structure
        pass

    def _validate_config_consistency(self, configs: Dict[str, Dict], result: ValidationResult):
        """Validate consistency across configuration files."""
        # Check for conflicting settings
        pass

    def _apply_auto_fix(self, imprint: ExpandedImprint, issue: ValidationIssue) -> Dict[str, Any]:
        """Apply automatic fix for an issue."""
        try:
            if issue.category == 'branding' and issue.field == 'imprint_name':
                if not hasattr(imprint, 'branding') or not imprint.branding.get('imprint_name'):
                    # Generate a default name
                    default_name = f"New Imprint {datetime.now().strftime('%Y%m%d')}"
                    if hasattr(imprint, 'branding'):
                        imprint.branding['imprint_name'] = default_name
                    return {
                        'success': True,
                        'description': f'Set default imprint name: {default_name}'
                    }
            
            return {
                'success': False,
                'error': 'No auto-fix available for this issue'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration."""
        return {
            'concept': {
                'min_description_length': 10,
                'min_confidence_score': 0.3
            },
            'branding': {
                'max_name_length': 50,
                'min_mission_length': 20
            },
            'design': {
                'required_colors': ['primary', 'secondary'],
                'required_fonts': ['heading', 'body']
            }
        }

    def _initialize_field_validators(self) -> Dict[str, Callable]:
        """Initialize field-specific validators."""
        return {
            'color': self._is_valid_color,
            'email': self._is_valid_email,
            'url': self._is_valid_url
        }

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
        try:
            template_file = template_path / 'template.tex'
            if template_file.exists() and template_file.stat().st_size > 0:
                result.issues.append(ValidationIssue(
                    severity='info',
                    category='template',
                    field='compilation',
                    message="Template appears ready for compilation"
                ))
            else:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='template',
                    field='compilation',
                    message="Template may not compile successfully"
                ))
        except Exception as e:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='template',
                field='compilation',
                message=f"Could not test template compilation: {str(e)}"
            ))

    def _validate_prompt_structure(self, prompts_data: Dict[str, Any], result: ValidationResult):
        """Validate prompt structure."""
        required_categories = ['content_generation', 'editing', 'metadata']
        
        for category in required_categories:
            if category not in prompts_data:
                result.issues.append(ValidationIssue(
                    severity='warning',
                    category='prompts',
                    field=category,
                    message=f"Missing prompt category: {category}",
                    suggestion=f"Add {category} prompts for complete functionality"
                ))

    def _validate_prompt_content(self, prompts_data: Dict[str, Any], result: ValidationResult):
        """Validate prompt content quality."""
        for category, prompts in prompts_data.items():
            if isinstance(prompts, dict):
                for prompt_name, prompt_text in prompts.items():
                    if not prompt_text or len(prompt_text.strip()) < 10:
                        result.issues.append(ValidationIssue(
                            severity='warning',
                            category='prompts',
                            field=f'{category}.{prompt_name}',
                            message=f"Prompt {prompt_name} is too short or empty",
                            suggestion="Provide more detailed prompt instructions"
                        ))

    def _test_prompt_effectiveness(self, prompts_data: Dict[str, Any], result: ValidationResult):
        """Test prompt effectiveness with LLM."""
        # This would test actual prompt effectiveness
        # For now, just validate that prompts are present
        total_prompts = 0
        for category, prompts in prompts_data.items():
            if isinstance(prompts, dict):
                total_prompts += len(prompts)
        
        if total_prompts > 0:
            result.issues.append(ValidationIssue(
                severity='info',
                category='prompts',
                field='effectiveness',
                message=f"Found {total_prompts} prompts ready for testing"
            ))

    def _validate_config_consistency(self, configs: Dict[str, Dict], result: ValidationResult):
        """Validate consistency across configuration files."""
        # Extract imprint names from all configs
        imprint_names = set()
        for config_file, config_data in configs.items():
            if 'imprint_name' in config_data:
                imprint_names.add(config_data['imprint_name'])
        
        if len(imprint_names) > 1:
            result.issues.append(ValidationIssue(
                severity='warning',
                category='config',
                field='consistency',
                message="Inconsistent imprint names across configuration files",
                suggestion="Ensure all configuration files use the same imprint name"
            ))

    def _apply_auto_fix(self, imprint: ExpandedImprint, issue: ValidationIssue) -> Dict[str, Any]:
        """Apply automatic fix for an issue."""
        try:
            if issue.category == 'branding' and issue.field == 'imprint_name':
                if not imprint.branding.get('imprint_name'):
                    imprint.branding['imprint_name'] = "New Imprint"
                    return {
                        'success': True,
                        'description': 'Set default imprint name'
                    }
            
            elif issue.category == 'publishing' and issue.field == 'primary_genres':
                if not imprint.publishing.primary_genres:
                    imprint.publishing.primary_genres = ['General']
                    return {
                        'success': True,
                        'description': 'Set default primary genre'
                    }
            
            return {
                'success': False,
                'error': 'No auto-fix available for this issue'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration."""
        return {
            'concept': {
                'min_input_length': 10,
                'min_confidence_score': 0.3,
                'required_elements': ['themes', 'audience']
            },
            'branding': {
                'required_fields': ['imprint_name'],
                'recommended_fields': ['mission_statement', 'brand_values'],
                'max_name_length': 50
            },
            'publishing': {
                'required_fields': ['primary_genres'],
                'max_genres': 5
            },
            'design': {
                'color_format': 'hex_or_named',
                'required_elements': ['color_palette', 'typography']
            }
        }

    def _initialize_field_validators(self) -> Dict[str, Callable]:
        """Initialize field-specific validators."""
        return {
            'color': self._is_valid_color,
            'email': lambda x: '@' in x if x else False,
            'url': lambda x: x.startswith(('http://', 'https://')) if x else False
        }