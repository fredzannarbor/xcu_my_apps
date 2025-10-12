import logging
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core.llm_integration import CodexesLLMIntegration
from .imprint_expander import ExpandedImprint
from .validation import ValidationResult

# Define missing classes locally if they don't exist elsewhere
class DictWrapper:
    """Wrapper for dictionary-like access to objects."""
    def __init__(self, data):
        self._data = data or {}
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

class EditingSession:
    """Session for tracking editing changes."""
    def __init__(self, imprint, session_id=None, created_at=None, current_position=-1, is_dirty=False, **kwargs):
        self.imprint = imprint
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.change_history = []
        self.current_position = current_position
        self.is_dirty = is_dirty
        self.created_at = created_at or datetime.now()
        self.validation_cache = None
    
    def to_dict(self):
        """Convert session to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'current_position': self.current_position,
            'is_dirty': self.is_dirty,
            'imprint': self.imprint.to_dict() if hasattr(self.imprint, 'to_dict') else str(self.imprint),
            'change_history': [
                {
                    'timestamp': change.timestamp.isoformat(),
                    'component': getattr(change, 'component', ''),
                    'field': getattr(change, 'field', ''),
                    'old_value': change.old_value,
                    'new_value': change.new_value,
                    'change_type': getattr(change, 'change_type', 'update'),
                    'user_note': getattr(change, 'user_note', '')
                }
                for change in self.change_history
            ]
        }

class ChangeRecord:
    """Record of a change made during editing."""
    def __init__(self, field_path=None, old_value=None, new_value=None, timestamp=None, 
                 component=None, field=None, change_type='update', user_note=''):
        # Support both old and new parameter styles
        self.field_path = field_path or f"{component}.{field}" if component and field else ""
        self.component = component
        self.field = field
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = timestamp or datetime.now()
        self.change_type = change_type
        self.user_note = user_note


class ImprintEditor:
    """Unified interface for editing expanded imprint definitions."""

    def __init__(self, llm_caller=None):
        # Accept either LLMIntegration or a wrapper with call_model_with_prompt method
        if llm_caller is None:
            try:
                llm_integration = CodexesLLMIntegration()
                # Create wrapper to match expected interface
                class LLMCallerWrapper:
                    def __init__(self, integration):
                        self.integration = integration
                    
                    def call_model_with_prompt(self, **kwargs):
                        prompt = kwargs.get('prompt', '')
                        temperature = kwargs.get('temperature', 0.7)
                        try:
                            response = self.integration.call_llm(prompt, temperature=temperature)
                            return {"content": response}
                        except Exception as e:
                            logging.warning(f"LLM call failed: {e}, using fallback")
                            return {"content": "Unable to generate suggestions at this time."}
                
                self.llm_caller = LLMCallerWrapper(llm_integration)
            except Exception as e:
                logging.warning(f"Failed to initialize LLM integration: {e}, using mock")
                # Fallback mock
                class MockLLMCaller:
                    def call_model_with_prompt(self, **kwargs):
                        return {"content": "Mock suggestions: Consider reviewing your strategy."}
                self.llm_caller = MockLLMCaller()
        else:
            self.llm_caller = llm_caller
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_sessions: Dict[str, EditingSession] = {}
        self.validation_rules = self._load_validation_rules()

    def create_editing_session(self, imprint: ExpandedImprint, session_id: Optional[str] = None) -> EditingSession:
        """Create a new editing session."""
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create copy to avoid modifying original
        # Use a simpler copy approach to avoid deepcopy issues with DictWrapper
        try:
            imprint_copy = copy.deepcopy(imprint)
        except Exception as e:
            self.logger.warning(f"Deepcopy failed, using fallback copy: {e}")
            # Fallback to creating a new ExpandedImprint with copied data
            imprint_copy = ExpandedImprint(
                concept=imprint.concept,
                branding=DictWrapper(dict(imprint.branding._data)) if hasattr(imprint.branding, '_data') else DictWrapper(dict(imprint.branding)),
                design_specifications=DictWrapper(dict(imprint.design_specifications._data)) if hasattr(imprint.design_specifications, '_data') else DictWrapper(dict(imprint.design_specifications)),
                publishing_strategy=DictWrapper(dict(imprint.publishing_strategy._data)) if hasattr(imprint.publishing_strategy, '_data') else DictWrapper(dict(imprint.publishing_strategy)),
                operational_framework=DictWrapper(dict(imprint.operational_framework._data)) if hasattr(imprint.operational_framework, '_data') else DictWrapper(dict(imprint.operational_framework)),
                marketing_approach=DictWrapper(dict(imprint.marketing_approach._data)) if hasattr(imprint.marketing_approach, '_data') else DictWrapper(dict(imprint.marketing_approach)),
                financial_projections=DictWrapper(dict(imprint.financial_projections._data)) if hasattr(imprint.financial_projections, '_data') else DictWrapper(dict(imprint.financial_projections)),
                expanded_at=imprint.expanded_at
            )

        session = EditingSession(
            imprint=imprint_copy,
            session_id=session_id
        )

        self.active_sessions[session_id] = session
        self.logger.info(f"Created editing session {session_id}")

        return session

    def update_field(self, session: EditingSession, component: str, field: str,
                     new_value: Any, user_note: str = "") -> bool:
        """Update a field in the imprint with change tracking."""
        try:
            # Get current value
            old_value = self._get_field_value(session.imprint, component, field)

            # Validate the change
            validation_result = self._validate_field_change(component, field, new_value)
            if not validation_result.is_valid:
                self.logger.warning(f"Validation failed for {component}.{field}: {validation_result.errors}")
                return False

            # Apply the change
            self._set_field_value(session.imprint, component, field, new_value)

            # Record the change
            change_record = ChangeRecord(
                timestamp=datetime.now(),
                component=component,
                field=field,
                old_value=old_value,
                new_value=new_value,
                change_type='update',
                user_note=user_note
            )

            # Add to history (remove any redo history)
            session.change_history = session.change_history[:session.current_position + 1]
            session.change_history.append(change_record)
            session.current_position += 1
            session.is_dirty = True
            session.validation_cache = None  # Invalidate cache

            self.logger.info(f"Updated {component}.{field} in session {session.session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating field {component}.{field}: {e}")
            return False

    def undo_change(self, session: EditingSession) -> bool:
        """Undo the last change."""
        if session.current_position < 0:
            return False

        try:
            change = session.change_history[session.current_position]

            # Revert the change
            self._set_field_value(session.imprint, change.component, change.field, change.old_value)

            session.current_position -= 1
            session.is_dirty = session.current_position >= 0
            session.validation_cache = None

            self.logger.info(f"Undid change to {change.component}.{change.field} in session {session.session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error undoing change: {e}")
            return False

    def redo_change(self, session: EditingSession) -> bool:
        """Redo the next change."""
        if session.current_position >= len(session.change_history) - 1:
            return False

        try:
            session.current_position += 1
            change = session.change_history[session.current_position]

            # Reapply the change
            self._set_field_value(session.imprint, change.component, change.field, change.new_value)

            session.is_dirty = True
            session.validation_cache = None

            self.logger.info(f"Redid change to {change.component}.{change.field} in session {session.session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error redoing change: {e}")
            return False

    def validate_imprint(self, session: EditingSession, use_cache: bool = True) -> ValidationResult:
        """Validate the current imprint state."""
        if use_cache and session.validation_cache:
            return session.validation_cache

        try:
            result = ValidationResult(is_valid=True)

            # Validate each component
            self._validate_branding(session.imprint.branding, result)
            self._validate_design_specifications(session.imprint.design_specifications, result)
            self._validate_publishing_strategy(session.imprint.publishing_strategy, result)
            self._validate_operational_framework(session.imprint.operational_framework, result)
            self._validate_marketing_approach(session.imprint.marketing_approach, result)
            self._validate_financial_projections(session.imprint.financial_projections, result)

            # Calculate completeness score
            result.completeness_score = self._calculate_completeness(session.imprint)

            # Check overall consistency
            self._validate_consistency(session.imprint, result)

            # Cache the result
            session.validation_cache = result

            return result

        except Exception as e:
            self.logger.error(f"Error validating imprint: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )

    def _safe_get(self, obj, key, default=None):
        """Safely get a value from an object, whether it's a dict, DictWrapper, or has attributes."""
        if hasattr(obj, 'get') and callable(getattr(obj, 'get')):
            return obj.get(key, default)
        elif hasattr(obj, key):
            return getattr(obj, key, default)
        elif isinstance(obj, dict):
            return obj.get(key, default)
        else:
            return default

    def get_preview_data(self, session: EditingSession) -> Dict[str, Any]:
        """Generate preview data for the imprint."""
        try:
            preview = {
                'imprint_name': self._safe_get(session.imprint.branding, 'imprint_name', ''),
                'tagline': self._safe_get(session.imprint.branding, 'tagline', ''),
                'mission_statement': self._safe_get(session.imprint.branding, 'mission_statement', ''),
                'primary_genres': self._safe_get(session.imprint.publishing_strategy, 'primary_genres', []),
                'target_audience': self._safe_get(session.imprint.publishing_strategy, 'target_readership', ''),
                'design_preview': {
                    'color_palette': self._safe_get(session.imprint.design_specifications, 'color_palette', {}),
                    'typography': self._safe_get(session.imprint.design_specifications, 'typography', {}),
                    'cover_art_direction': self._safe_get(session.imprint.design_specifications, 'cover_art_direction', '')
                },
                'marketing_summary': {
                    'target_platforms': self._safe_get(session.imprint.marketing_approach, 'target_platforms', []),
                    'promotional_activities': self._safe_get(session.imprint.marketing_approach, 'promotional_activities', [])
                },
                'validation_status': self.validate_imprint(session).to_dict(),
                'completeness_percentage': self._calculate_completeness(session.imprint) * 100
            }

            return preview

        except Exception as e:
            self.logger.error(f"Error generating preview: {e}")
            return {'error': str(e)}

    def suggest_improvements(self, session: EditingSession) -> List[str]:
        """Suggest improvements for the imprint."""
        suggestions = []
        validation = self.validate_imprint(session)

        # Add validation suggestions
        suggestions.extend(validation.suggestions)

        # Add AI-powered suggestions
        try:
            ai_suggestions = self._get_ai_suggestions(session.imprint)
            suggestions.extend(ai_suggestions)
        except Exception as e:
            self.logger.error(f"Error getting AI suggestions: {e}")

        return suggestions

    def _get_field_value(self, imprint: ExpandedImprint, component: str, field: str) -> Any:
        """Get the current value of a field."""
        component_obj = getattr(imprint, component)
        return self._safe_get(component_obj, field)

    def _set_field_value(self, imprint: ExpandedImprint, component: str, field: str, value: Any):
        """Set the value of a field."""
        component_obj = getattr(imprint, component)
        component_obj[field] = value

    def _validate_field_change(self, component: str, field: str, value: Any) -> ValidationResult:
        """Validate a field change."""
        result = ValidationResult(is_valid=True)

        # Basic validation rules
        if value is None:
            result.warnings.append(f"Setting {component}.{field} to None")

        # Component-specific validation based on expected types from generator
        if component == 'branding':
            if field == 'imprint_name' and not isinstance(value, str):
                result.is_valid = False
                result.errors.append("Imprint name must be a string")
            elif field == 'brand_values' and not isinstance(value, list):
                result.is_valid = False
                result.errors.append("Brand values must be a list")

        elif component == 'design_specifications':
            if field == 'color_palette' and not isinstance(value, dict):
                result.is_valid = False
                result.errors.append("Color palette must be a dictionary")
            elif field == 'visual_motifs' and not isinstance(value, list):
                result.is_valid = False
                result.errors.append("Visual motifs must be a list")

        elif component == 'publishing_strategy':
            if field == 'primary_genres' and not isinstance(value, list):
                result.is_valid = False
                result.errors.append("Primary genres must be a list")
            elif field == 'pricing_strategy' and not isinstance(value, dict):
                result.is_valid = False
                result.errors.append("Pricing strategy must be a dictionary")

        elif component == 'operational_framework':
            if field == 'workflow_stages' and not isinstance(value, list):
                result.is_valid = False
                result.errors.append("Workflow stages must be a list")
            elif field == 'team_structure' and not isinstance(value, dict):
                result.is_valid = False
                result.errors.append("Team structure must be a dictionary")

        elif component == 'marketing_approach':
            if field == 'target_platforms' and not isinstance(value, list):
                result.is_valid = False
                result.errors.append("Target platforms must be a list")
            elif field == 'budget_allocation' and not isinstance(value, dict):
                result.is_valid = False
                result.errors.append("Budget allocation must be a dictionary")

        elif component == 'financial_projections':
            if field == 'first_year_revenue_target' and not (isinstance(value, (int, float)) and value >= 0):
                result.is_valid = False
                result.errors.append("Revenue target must be a non-negative number")
            elif field == 'profit_margin_goal' and not (isinstance(value, (int, float)) and 0 <= value <= 1):
                result.is_valid = False
                result.errors.append("Profit margin goal must be a number between 0 and 1")


        return result

    def _validate_branding(self, branding: DictWrapper, result: ValidationResult):
        """Validate branding strategy."""
        if not self._safe_get(branding, 'imprint_name'):
            result.errors.append("Branding: Imprint name is required.")
            result.is_valid = False

        if not self._safe_get(branding, 'mission_statement'):
            result.warnings.append("Branding: Mission statement is recommended.")

        if not self._safe_get(branding, 'brand_values'):
            result.suggestions.append("Branding: Consider defining brand values.")

    def _validate_design_specifications(self, design_specs: DictWrapper, result: ValidationResult):
        """Validate design specifications."""
        if not self._safe_get(design_specs, 'color_palette'):
            result.warnings.append("Design: Color palette not defined.")

        if not self._safe_get(design_specs, 'typography'):
            result.warnings.append("Design: Typography not defined.")

        if not self._safe_get(design_specs, 'cover_art_direction'):
            result.suggestions.append("Design: Consider providing cover art direction.")

    def _validate_publishing_strategy(self, publishing_strategy: DictWrapper, result: ValidationResult):
        """Validate publishing strategy."""
        if not self._safe_get(publishing_strategy, 'primary_genres'):
            result.errors.append("Publishing: Primary genres are required.")
            result.is_valid = False

        if not self._safe_get(publishing_strategy, 'target_readership'):
            result.warnings.append("Publishing: Target readership should be defined.")

        if not self._safe_get(publishing_strategy, 'publication_frequency'):
            result.suggestions.append("Publishing: Define publication frequency.")


    def _validate_operational_framework(self, operational_framework: DictWrapper, result: ValidationResult):
        """Validate operational framework."""
        if not self._safe_get(operational_framework, 'workflow_stages'):
            result.warnings.append("Operations: Workflow stages not defined.")

        if not self._safe_get(operational_framework, 'team_structure'):
            result.suggestions.append("Operations: Define team structure for clarity.")


    def _validate_marketing_approach(self, marketing_approach: DictWrapper, result: ValidationResult):
        """Validate marketing approach."""
        if not self._safe_get(marketing_approach, 'target_platforms'):
            result.warnings.append("Marketing: Target platforms not defined.")

        if not self._safe_get(marketing_approach, 'promotional_activities'):
            result.suggestions.append("Marketing: Outline promotional activities.")

    def _validate_financial_projections(self, financial_projections: DictWrapper, result: ValidationResult):
        """Validate financial projections."""
        if self._safe_get(financial_projections, 'first_year_revenue_target') is None:
            result.warnings.append("Financial: First year revenue target is recommended.")

        if self._safe_get(financial_projections, 'profit_margin_goal') is None:
            result.suggestions.append("Financial: Define a profit margin goal.")


    def _validate_consistency(self, imprint: ExpandedImprint, result: ValidationResult):
        """Validate consistency across components."""
        # Example: Check if target audience/readership is consistent
        branding_audience_concept = self._safe_get(imprint.concept, 'target_audience')
        publishing_readership = self._safe_get(imprint.publishing_strategy, 'target_readership')

        if branding_audience_concept and publishing_readership and branding_audience_concept not in publishing_readership:
            result.warnings.append(f"Consistency: Target audience in concept ('{branding_audience_concept}') might not align with publishing readership ('{publishing_readership}').")

    def _calculate_completeness(self, imprint: ExpandedImprint) -> float:
        """Calculate completeness score for the imprint."""
        total_filled_fields = 0
        total_possible_fields = 0

        # Define fields to check for completeness in each component
        # These lists are based on the JSON structures generated by ImprintExpander
        component_fields = {
            'branding': ['imprint_name', 'mission_statement', 'brand_values', 'brand_voice', 'tagline', 'unique_selling_proposition', 'logo_concept'],
            'design_specifications': ['color_palette', 'typography', 'visual_motifs', 'cover_art_direction', 'interior_layout_preferences'],
            'publishing_strategy': ['primary_genres', 'target_readership', 'publication_frequency', 'editorial_focus', 'author_acquisition_strategy', 'rights_management', 'pricing_strategy', 'market_positioning'],
            'operational_framework': ['workflow_stages', 'technology_stack', 'team_structure', 'vendor_relationships', 'quality_control_measures', 'communication_protocols'],
            'marketing_approach': ['target_platforms', 'promotional_activities', 'audience_engagement_tactics', 'budget_allocation', 'brand_partnerships', 'success_metrics'],
            'financial_projections': ['first_year_revenue_target', 'profit_margin_goal', 'investment_required', 'funding_sources', 'royalty_rates_structure', 'expense_categories', 'breakeven_point_analysis', 'long_term_financial_goals']
        }

        for component_name, fields in component_fields.items():
            component_data = getattr(imprint, component_name)
            for field in fields:
                total_possible_fields += 1
                if component_data and self._safe_get(component_data, field) not in [None, '', [], {}]:
                    total_filled_fields += 1

        if total_possible_fields == 0:
            return 0.0

        return total_filled_fields / total_possible_fields

    def _get_ai_suggestions(self, imprint: ExpandedImprint) -> List[str]:
        """Get AI-powered suggestions for improvement."""
        try:
            prompt = f"""
            Analyze this imprint definition and suggest improvements. Focus on market positioning, brand clarity, and operational efficiency.
            Provide 3-5 specific, actionable suggestions.
            
            Imprint Name: {self._safe_get(imprint.branding, 'imprint_name')}
            Mission: {self._safe_get(imprint.branding, 'mission_statement')}
            Genres: {', '.join(self._safe_get(imprint.publishing_strategy, 'primary_genres', []))}
            Target Audience: {self._safe_get(imprint.publishing_strategy, 'target_readership')}
            Brand Personality: {self._safe_get(imprint.concept, 'brand_personality')}

            Current status:
            {json.dumps(imprint.to_dict(), indent=2)}
            """
            # Using default_api.search_web for example, but ideally would call a specific LLM tool.
            # As per instruction, I will use a placeholder for LLM call if direct access is not possible.
            # Assuming `llm_caller.call_model_with_prompt` is the intended way.

            response = self.llm_caller.call_model_with_prompt(
                prompt=prompt,
                temperature=0.7 # Using a moderate temperature for balanced creativity and focus
            )

            if response and response.get('content'):
                content = response['content']
                # Assuming the LLM returns suggestions as a bulleted list or similar
                suggestions = [s.strip() for s in content.split('\n') if s.strip() and s.strip().startswith(('*', '-', '1.', '2.', '3.'))]
                return suggestions[:5]  # Limit to 5 suggestions
            else:
                self.logger.warning("AI suggestions could not be generated: Empty response or content.")
                return []

        except Exception as e:
            self.logger.error(f"Error getting AI suggestions: {e}")
            return []

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration."""
        # This can be expanded to load from a file or a more complex structure
        return {
            'required_fields': {
                'branding': ['imprint_name'],
                'publishing_strategy': ['primary_genres']
            },
            'recommended_fields': {
                'branding': ['mission_statement', 'brand_values', 'tagline'],
                'design_specifications': ['color_palette', 'typography', 'cover_art_direction'],
                'publishing_strategy': ['target_readership', 'publication_frequency'],
                'operational_framework': ['workflow_stages', 'team_structure'],
                'marketing_approach': ['target_platforms', 'promotional_activities'],
                'financial_projections': ['first_year_revenue_target', 'profit_margin_goal']
            }
        }

    def save_session(self, session: EditingSession, file_path: str):
        """Save editing session to file."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)

            self.logger.info(f"Saved session {session.session_id} to {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving session: {e}")
            raise

    def load_session(self, file_path: str) -> EditingSession:
        """Load editing session from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Reconstruct the session
            # Note: ExpandedImprint and DictWrapper need to be correctly initialized from dict
            imprint = ExpandedImprint.from_dict(data['imprint'])
            session = EditingSession(
                imprint=imprint,
                session_id=data['session_id'],
                created_at=datetime.fromisoformat(data['created_at']),
                current_position=data['current_position'],
                is_dirty=data['is_dirty']
            )

            # Reconstruct change history
            for change_data in data['change_history']:
                change = ChangeRecord(
                    timestamp=datetime.fromisoformat(change_data['timestamp']),
                    component=change_data['component'],
                    field=change_data['field'],
                    old_value=change_data['old_value'],
                    new_value=change_data['new_value'],
                    change_type=change_data['change_type'],
                    user_note=change_data['user_note']
                )
                session.change_history.append(change)

            self.active_sessions[session.session_id] = session
            return session

        except Exception as e:
            self.logger.error(f"Error loading session: {e}")
            raise

    def close_session(self, session_id: str):
        """Close an editing session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.logger.info(f"Closed session {session_id}")

    def list_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_sessions.keys())

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary information about a session."""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}

        session = self.active_sessions[session_id]
        validation = self.validate_imprint(session)

        return {
            'session_id': session_id,
            'imprint_name': self._safe_get(session.imprint.branding, 'imprint_name'),
            'created_at': session.created_at.isoformat(),
            'is_dirty': session.is_dirty,
            'changes_count': len(session.change_history),
            'completeness_score': validation.completeness_score,
            'is_valid': validation.is_valid,
            'error_count': len(validation.errors),
            'warning_count': len(validation.warnings)
        }