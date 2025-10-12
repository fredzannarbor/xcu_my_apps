"""
Imprint-Ideation Bridge Component

Provides integration between the ideation system and imprint-specific publishing workflows.
Supports selectable integration modes and imprint-specific guidance.
"""

import streamlit as st
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType
from codexes.modules.metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """Available integration modes between ideation and imprint workflows."""
    IMPRINT_DRIVEN = "imprint_driven"
    EXPORT_TO_PIPELINE = "export_to_pipeline"
    BIDIRECTIONAL_SYNC = "bidirectional_sync"


@dataclass
class ImprintContext:
    """Context information for an imprint."""
    name: str
    publisher: str
    config_path: str
    branding: Dict[str, Any]
    publishing_focus: Dict[str, Any]
    constraints: Dict[str, Any]
    guidance: Dict[str, Any]


class ImprintIdeationBridge:
    """
    Bridge component that integrates ideation workflows with imprint-specific publishing processes.
    Provides selectable integration modes and imprint-aware content generation.
    """
    
    def __init__(self):
        """Initialize the imprint-ideation bridge."""
        self.available_imprints = self._load_available_imprints()
        self.integration_modes = {
            IntegrationMode.IMPRINT_DRIVEN: {
                "name": "Imprint-Driven Content",
                "description": "Generate content aligned with imprint brand guidelines and constraints",
                "features": [
                    "Brand-consistent content generation",
                    "Genre and audience alignment",
                    "Imprint-specific prompts and guidance",
                    "Automatic constraint validation"
                ]
            },
            IntegrationMode.EXPORT_TO_PIPELINE: {
                "name": "Export to Pipeline",
                "description": "Convert ideation outputs to book production pipeline format",
                "features": [
                    "CodexObject to CodexMetadata conversion",
                    "Imprint-specific metadata mapping",
                    "Pipeline-ready file generation",
                    "Production workflow integration"
                ]
            },
            IntegrationMode.BIDIRECTIONAL_SYNC: {
                "name": "Bidirectional Sync",
                "description": "Full synchronization between ideation and production systems",
                "features": [
                    "Real-time metadata synchronization",
                    "Production status updates in ideation",
                    "Cross-system content tracking",
                    "Unified workflow management"
                ]
            }
        }
    
    def _load_available_imprints(self) -> Dict[str, ImprintContext]:
        """Load available imprints from configuration files."""
        imprints = {}
        configs_path = Path("configs/imprints")
        
        if not configs_path.exists():
            logger.warning(f"Imprints config directory not found: {configs_path}")
            return imprints
        
        for config_file in configs_path.glob("*.json"):
            if config_file.name == "imprint_template.json":
                continue  # Skip template file
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Skip template files
                if config_data.get("imprint") == "TEMPLATE_IMPRINT_NAME":
                    continue
                
                imprint_name = config_data.get("imprint", config_file.stem)
                
                # Extract constraints and guidance
                constraints = self._extract_imprint_constraints(config_data)
                guidance = self._extract_imprint_guidance(config_data)
                
                imprint_context = ImprintContext(
                    name=imprint_name,
                    publisher=config_data.get("publisher", "Unknown"),
                    config_path=str(config_file),
                    branding=config_data.get("branding", {}),
                    publishing_focus=config_data.get("publishing_focus", {}),
                    constraints=constraints,
                    guidance=guidance
                )
                
                imprints[imprint_name] = imprint_context
                
            except Exception as e:
                logger.error(f"Failed to load imprint config {config_file}: {e}")
                continue
        
        return imprints
    
    def _extract_imprint_constraints(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content constraints from imprint configuration."""
        constraints = {}
        
        # Genre constraints
        publishing_focus = config_data.get("publishing_focus", {})
        if "primary_genres" in publishing_focus:
            constraints["preferred_genres"] = publishing_focus["primary_genres"]
        
        # Audience constraints
        if "target_audience" in publishing_focus:
            constraints["target_audience"] = publishing_focus["target_audience"]
        
        # Language constraints
        if "languages" in publishing_focus:
            constraints["languages"] = publishing_focus["languages"]
        
        # Content guidelines from metadata defaults
        metadata_defaults = config_data.get("metadata_defaults", {})
        if "bisac_category_preferences" in metadata_defaults:
            constraints["bisac_preferences"] = metadata_defaults["bisac_category_preferences"]
        
        # Age range constraints
        age_range = metadata_defaults.get("default_age_range", {})
        if age_range.get("min_age") or age_range.get("max_age"):
            constraints["age_range"] = age_range
        
        # Production constraints
        production_settings = config_data.get("production_settings", {})
        quality_standards = production_settings.get("quality_standards", {})
        if quality_standards:
            constraints["quality_standards"] = quality_standards
        
        return constraints
    
    def _extract_imprint_guidance(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content guidance from imprint configuration."""
        guidance = {}
        
        # Branding guidance
        branding = config_data.get("branding", {})
        if "tagline" in branding:
            guidance["brand_tagline"] = branding["tagline"]
        
        # Publishing focus guidance
        publishing_focus = config_data.get("publishing_focus", {})
        if "specialization" in publishing_focus:
            guidance["specialization"] = publishing_focus["specialization"]
        
        # Marketing guidance
        marketing_defaults = config_data.get("marketing_defaults", {})
        if "review_quote_policy" in marketing_defaults:
            guidance["review_policy"] = marketing_defaults["review_quote_policy"]
        
        # Workflow guidance
        workflow_settings = config_data.get("workflow_settings", {})
        if workflow_settings.get("require_manual_review"):
            guidance["requires_review"] = True
        
        return guidance
    
    def render_imprint_selection_interface(self) -> Tuple[Optional[str], Optional[IntegrationMode]]:
        """Render the imprint selection and integration mode interface."""
        st.markdown("### 🏢 Imprint Integration")
        
        if not self.available_imprints:
            st.warning("⚠️ No imprint configurations found. Please check the configs/imprints directory.")
            return None, None
        
        # Imprint selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            imprint_options = ["None"] + list(self.available_imprints.keys())
            selected_imprint = st.selectbox(
                "Select Imprint Context:",
                options=imprint_options,
                help="Choose an imprint to apply brand guidelines and constraints to your content"
            )
        
        with col2:
            if selected_imprint and selected_imprint != "None":
                imprint_context = self.available_imprints[selected_imprint]
                st.info(f"**Publisher:** {imprint_context.publisher}")
        
        if selected_imprint == "None":
            return None, None
        
        # Show imprint details
        imprint_context = self.available_imprints[selected_imprint]
        self._render_imprint_details(imprint_context)
        
        # Integration mode selection
        st.markdown("### ⚙️ Integration Mode")
        
        mode_options = list(self.integration_modes.keys())
        mode_names = [self.integration_modes[mode]["name"] for mode in mode_options]
        
        selected_mode_index = st.radio(
            "Choose integration features:",
            range(len(mode_options)),
            format_func=lambda i: mode_names[i],
            help="Select which integration features you want to use"
        )
        
        selected_mode = mode_options[selected_mode_index]
        
        # Show mode details
        mode_info = self.integration_modes[selected_mode]
        with st.expander(f"ℹ️ About {mode_info['name']}", expanded=True):
            st.write(mode_info["description"])
            st.write("**Features:**")
            for feature in mode_info["features"]:
                st.write(f"• {feature}")
        
        return selected_imprint, selected_mode
    
    def _render_imprint_details(self, imprint_context: ImprintContext):
        """Render detailed information about the selected imprint."""
        with st.expander(f"📋 {imprint_context.name} Details", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Publishing Focus:**")
                focus = imprint_context.publishing_focus
                if "primary_genres" in focus:
                    st.write(f"• Genres: {', '.join(focus['primary_genres'])}")
                if "target_audience" in focus:
                    st.write(f"• Audience: {focus['target_audience']}")
                if "specialization" in focus:
                    st.write(f"• Specialization: {focus['specialization']}")
                
                st.write("**Branding:**")
                branding = imprint_context.branding
                if "tagline" in branding:
                    st.write(f"• Tagline: {branding['tagline']}")
                if "website" in branding:
                    st.write(f"• Website: {branding['website']}")
            
            with col2:
                st.write("**Content Constraints:**")
                constraints = imprint_context.constraints
                if "preferred_genres" in constraints:
                    st.write(f"• Preferred Genres: {', '.join(constraints['preferred_genres'][:3])}...")
                if "target_audience" in constraints:
                    st.write(f"• Target Audience: {constraints['target_audience']}")
                if "languages" in constraints:
                    st.write(f"• Languages: {', '.join(constraints['languages'])}")
                
                st.write("**Guidance:**")
                guidance = imprint_context.guidance
                if "specialization" in guidance:
                    st.write(f"• Focus: {guidance['specialization']}")
                if "requires_review" in guidance:
                    st.write("• Manual review required")
    
    def apply_imprint_constraints(self, codex_object: CodexObject, imprint_name: str) -> CodexObject:
        """Apply imprint-specific constraints and guidance to a CodexObject."""
        if imprint_name not in self.available_imprints:
            logger.warning(f"Unknown imprint: {imprint_name}")
            return codex_object
        
        imprint_context = self.available_imprints[imprint_name]
        constraints = imprint_context.constraints
        
        # Apply genre constraints
        if "preferred_genres" in constraints and not codex_object.genre:
            # Set to first preferred genre if no genre is specified
            codex_object.genre = constraints["preferred_genres"][0]
        
        # Apply audience constraints
        if "target_audience" in constraints and not codex_object.target_audience:
            codex_object.target_audience = constraints["target_audience"]
        
        # Add imprint-specific tags
        imprint_tag = f"imprint:{imprint_name.lower().replace(' ', '_')}"
        if imprint_tag not in codex_object.tags:
            codex_object.tags.append(imprint_tag)
        
        # Add processing history entry
        codex_object.processing_history.append({
            "action": "imprint_constraints_applied",
            "timestamp": codex_object.last_modified,
            "details": {
                "imprint": imprint_name,
                "constraints_applied": list(constraints.keys())
            }
        })
        
        return codex_object
    
    def validate_content_for_imprint(self, codex_object: CodexObject, imprint_name: str) -> Dict[str, Any]:
        """Validate content against imprint constraints and return validation results."""
        if imprint_name not in self.available_imprints:
            return {"valid": False, "errors": [f"Unknown imprint: {imprint_name}"]}
        
        imprint_context = self.available_imprints[imprint_name]
        constraints = imprint_context.constraints
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate genre
        if "preferred_genres" in constraints:
            preferred_genres = [g.lower() for g in constraints["preferred_genres"]]
            if codex_object.genre and codex_object.genre.lower() not in preferred_genres:
                validation_results["warnings"].append(
                    f"Genre '{codex_object.genre}' is not in preferred genres: {', '.join(constraints['preferred_genres'])}"
                )
        
        # Validate audience
        if "target_audience" in constraints:
            expected_audience = constraints["target_audience"]
            if codex_object.target_audience and codex_object.target_audience != expected_audience:
                validation_results["warnings"].append(
                    f"Target audience '{codex_object.target_audience}' differs from imprint focus: '{expected_audience}'"
                )
        
        # Validate age range if applicable
        if "age_range" in constraints:
            age_range = constraints["age_range"]
            if age_range.get("min_age") or age_range.get("max_age"):
                validation_results["suggestions"].append(
                    f"Consider age range: {age_range.get('min_age', 'Any')} - {age_range.get('max_age', 'Any')}"
                )
        
        # Check for required elements based on imprint guidance
        guidance = imprint_context.guidance
        if "requires_review" in guidance:
            validation_results["suggestions"].append("This imprint requires manual review before publication")
        
        return validation_results
    
    def export_to_pipeline(self, codex_objects: List[CodexObject], imprint_name: str) -> Dict[str, Any]:
        """Export CodexObjects to the book production pipeline format."""
        if imprint_name not in self.available_imprints:
            return {"success": False, "error": f"Unknown imprint: {imprint_name}"}
        
        imprint_context = self.available_imprints[imprint_name]
        export_results = {
            "success": True,
            "imprint": imprint_name,
            "exported_objects": [],
            "metadata_files": [],
            "warnings": []
        }
        
        for codex_object in codex_objects:
            try:
                # Convert to CodexMetadata
                metadata = codex_object.to_codex_metadata()
                
                # Apply imprint-specific metadata
                metadata = self._apply_imprint_metadata(metadata, imprint_context)
                
                # Validate for pipeline compatibility
                validation = self._validate_pipeline_compatibility(metadata, imprint_context)
                
                export_result = {
                    "codex_object_uuid": codex_object.uuid,
                    "title": codex_object.title,
                    "metadata": metadata.to_dict(),
                    "validation": validation,
                    "pipeline_ready": validation["valid"]
                }
                
                export_results["exported_objects"].append(export_result)
                
                if not validation["valid"]:
                    export_results["warnings"].extend(validation["errors"])
                
            except Exception as e:
                logger.error(f"Failed to export CodexObject {codex_object.uuid}: {e}")
                export_results["warnings"].append(f"Failed to export '{codex_object.title}': {str(e)}")
        
        return export_results
    
    def _apply_imprint_metadata(self, metadata: CodexMetadata, imprint_context: ImprintContext) -> CodexMetadata:
        """Apply imprint-specific metadata to CodexMetadata object."""
        # Load imprint configuration
        try:
            with open(imprint_context.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load imprint config: {e}")
            return metadata
        
        # Apply imprint name
        metadata.imprint = imprint_context.name
        metadata.publisher = imprint_context.publisher
        
        # Apply default settings
        default_settings = config_data.get("default_book_settings", {})
        if "language_code" in default_settings:
            metadata.language = default_settings["language_code"]
        if "binding_type" in default_settings:
            metadata.binding_type = default_settings["binding_type"]
        if "territorial_rights" in default_settings:
            metadata.territorial_rights = default_settings["territorial_rights"]
        
        # Apply metadata defaults
        metadata_defaults = config_data.get("metadata_defaults", {})
        if "edition_number" in metadata_defaults:
            metadata.edition_number = metadata_defaults["edition_number"]
        if "edition_description" in metadata_defaults:
            metadata.edition_description = metadata_defaults["edition_description"]
        
        # Apply BISAC preferences if not already set
        if not metadata.bisac_text and "bisac_category_preferences" in metadata_defaults:
            bisac_prefs = metadata_defaults["bisac_category_preferences"]
            if bisac_prefs:
                metadata.bisac_text = bisac_prefs[0]  # Use first preference
        
        # Apply LSI-specific settings
        lsi_settings = config_data.get("lsi_specific_settings", {})
        if "publisher_reference_id" in lsi_settings:
            metadata.publisher_reference_id = lsi_settings["publisher_reference_id"]
        
        return metadata
    
    def _validate_pipeline_compatibility(self, metadata: CodexMetadata, imprint_context: ImprintContext) -> Dict[str, Any]:
        """Validate metadata for pipeline compatibility."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["title", "imprint", "publisher"]
        for field in required_fields:
            if not getattr(metadata, field, None):
                validation["errors"].append(f"Missing required field: {field}")
                validation["valid"] = False
        
        # Check content requirements
        if not metadata.summary_long and not metadata.summary_short:
            validation["errors"].append("Missing content summary")
            validation["valid"] = False
        
        # Check word count
        if metadata.word_count == 0:
            validation["warnings"].append("Word count is zero - content may be incomplete")
        
        return validation
    
    def render_imprint_guidance(self, imprint_name: str, content_type: CodexObjectType) -> None:
        """Render imprint-specific guidance for content creation."""
        if imprint_name not in self.available_imprints:
            return
        
        imprint_context = self.available_imprints[imprint_name]
        
        st.markdown(f"### 📋 {imprint_context.name} Guidance")
        
        # Show brand-specific guidance
        guidance = imprint_context.guidance
        constraints = imprint_context.constraints
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Brand Guidelines:**")
            if "brand_tagline" in guidance:
                st.info(f"💡 Brand Focus: {guidance['brand_tagline']}")
            
            if "specialization" in guidance:
                st.write(f"• Specialization: {guidance['specialization']}")
            
            if "preferred_genres" in constraints:
                genres = constraints["preferred_genres"][:3]  # Show first 3
                st.write(f"• Preferred Genres: {', '.join(genres)}")
        
        with col2:
            st.markdown("**Content Recommendations:**")
            
            # Type-specific recommendations
            if content_type == CodexObjectType.IDEA:
                st.write("• Focus on core concept alignment with brand")
                st.write("• Consider genre preferences early")
            elif content_type == CodexObjectType.SYNOPSIS:
                st.write("• Ensure plot aligns with imprint focus")
                st.write("• Highlight unique selling points")
            elif content_type in [CodexObjectType.OUTLINE, CodexObjectType.DRAFT]:
                st.write("• Maintain brand consistency throughout")
                st.write("• Consider production requirements")
            
            if "target_audience" in constraints:
                st.write(f"• Target Audience: {constraints['target_audience']}")
        
        # Show validation status if content exists
        if "validation_results" in st.session_state:
            validation = st.session_state["validation_results"]
            if validation.get("warnings"):
                with st.expander("⚠️ Content Validation", expanded=False):
                    for warning in validation["warnings"]:
                        st.warning(warning)
            
            if validation.get("suggestions"):
                with st.expander("💡 Suggestions", expanded=False):
                    for suggestion in validation["suggestions"]:
                        st.info(suggestion)