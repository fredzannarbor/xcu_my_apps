# src/codexes/modules/builders/codex_type_generator.py
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CodexTypeGenerator:
    """Generate complete codex type definitions with all required artifacts"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.base_templates_dir = project_root / "templates"
        self.codex_types_dir = project_root / "codex_types"

        # Ensure directories exist
        self.codex_types_dir.mkdir(parents=True, exist_ok=True)

    def generate_codex_type(self, codex_type_name: str, requirements: Dict) -> Dict[str, Path]:
        """Generate all artifacts for a new codex type"""
        logger.info(f"Generating codex type: {codex_type_name}")

        try:
            codex_dir = self.codex_types_dir / codex_type_name
            codex_dir.mkdir(parents=True, exist_ok=True)

            artifacts = {}

            # 1. Generate prompts.json
            artifacts["prompts"] = self._generate_prompts_json(codex_type_name, requirements, codex_dir)

            # 2. Generate data.json
            artifacts["data"] = self._generate_data_json(codex_type_name, requirements, codex_dir)

            # 3. Generate custom prepress.py
            artifacts["prepress"] = self._generate_custom_prepress(codex_type_name, requirements, codex_dir)

            # 4. Generate validation rules
            artifacts["validation"] = self._generate_validation_rules(codex_type_name, requirements, codex_dir)

            # 5. Generate documentation
            artifacts["documentation"] = self._generate_documentation(codex_type_name, requirements, codex_dir)

            logger.info(f"Successfully generated {len(artifacts)} artifacts for {codex_type_name}")
            return artifacts

        except Exception as e:
            logger.error(f"Error generating codex type {codex_type_name}: {e}", exc_info=True)
            raise

    def _generate_prompts_json(self, codex_type_name: str, requirements: Dict, codex_dir: Path) -> Path:
        """Generate customized prompts.json for the codex type"""

        # Load base prompts as template
        base_prompts_path = self.project_root / "prompts" / "prompts.json"

        if base_prompts_path.exists():
            with open(base_prompts_path, 'r', encoding='utf-8') as f:
                base_prompts = json.load(f)
        else:
            base_prompts = self._get_default_prompts()

        # Customize prompts based on codex type
        customized_prompts = self._customize_prompts_for_type(base_prompts, codex_type_name, requirements)

        # Save to appropriate location
        output_path = codex_dir / f"{codex_type_name}_prompts.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(customized_prompts, f, indent=4, ensure_ascii=False)

        logger.debug(f"Generated prompts file: {output_path}")
        return output_path

    def _customize_prompts_for_type(self, base_prompts: Dict, codex_type_name: str, requirements: Dict) -> Dict:
        """Customize prompts based on codex type"""

        customized = base_prompts.copy()

        # Update imprint info
        customized["imprint_name"] = requirements.get('tentative_name', f"{codex_type_name} imprint").lower()

        # Customize based on codex type
        type_customizations = {
            "poetry_collection": {
                "imprint_intro": f"Our {requirements.get('tentative_name', 'Poetry')} imprint celebrates the power of verse to illuminate the human experience through carefully curated collections of contemporary and classic poetry.",
                "content_focus": "poetry, verse, literary expression, poetic traditions",
                "special_prompts": self._get_poetry_specific_prompts()
            },
            "technical_manual": {
                "imprint_intro": f"Our {requirements.get('tentative_name', 'Technical')} imprint provides comprehensive, practical guides for professionals seeking to master their craft through clear, actionable instruction.",
                "content_focus": "technical knowledge, professional development, practical skills, industry standards",
                "special_prompts": self._get_technical_specific_prompts()
            },
            "children_book": {
                "imprint_intro": f"Our {requirements.get('tentative_name', 'Children')} imprint creates engaging, educational books that inspire young minds and support learning through age-appropriate content and illustrations.",
                "content_focus": "child development, education, imagination, age-appropriate learning",
                "special_prompts": self._get_children_specific_prompts()
            },
            "academic_journal": {
                "imprint_intro": f"Our {requirements.get('tentative_name', 'Academic')} imprint advances scholarly discourse through rigorous peer-reviewed publications that contribute to the global knowledge base.",
                "content_focus": "academic research, scholarly analysis, peer review, knowledge advancement",
                "special_prompts": self._get_academic_specific_prompts()
            }
        }

        # Apply customizations
        if codex_type_name in type_customizations:
            customizations = type_customizations[codex_type_name]
            customized["imprint_intro"] = customizations["imprint_intro"]

            # Add special prompts
            if "special_prompts" in customizations:
                customized.update(customizations["special_prompts"])

            # Update existing prompts with content focus
            self._update_prompts_with_focus(customized, customizations["content_focus"])

        return customized

    def _get_poetry_specific_prompts(self) -> Dict:
        """Get poetry-specific prompts"""
        return {
            "poetry_analysis_prompt": {
                "params": {"temperature": 0.7, "max_tokens": 1000},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a poetry expert and literary analyst. Analyze poems for themes, structure, and literary devices."
                    },
                    {
                        "role": "user",
                        "content": "Analyze the following poem for its key themes and literary significance:\n\n{poem_content}"
                    }
                ]
            },
            "poetry_curation_prompt": {
                "params": {"temperature": 0.5, "max_tokens": 800},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a poetry curator. Select and organize poems around specific themes for publication."
                    },
                    {
                        "role": "user",
                        "content": "Curate a collection of poems around the theme: {theme}. Consider diversity of voice, time period, and poetic form."
                    }
                ]
            }
        }

    def _get_technical_specific_prompts(self) -> Dict:
        """Get technical manual-specific prompts"""
        return {
            "technical_instruction_prompt": {
                "params": {"temperature": 0.3, "max_tokens": 1500},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a technical writing expert. Create clear, step-by-step instructions for complex procedures."
                    },
                    {
                        "role": "user",
                        "content": "Create detailed instructions for: {procedure}. Include prerequisites, steps, troubleshooting, and verification."
                    }
                ]
            },
            "technical_reference_prompt": {
                "params": {"temperature": 0.2, "max_tokens": 1000},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are creating technical reference material. Provide accurate, concise information that professionals can quickly reference."
                    },
                    {
                        "role": "user",
                        "content": "Create a reference entry for: {technical_concept}. Include definition, parameters, examples, and related concepts."
                    }
                ]
            }
        }

    def _get_children_specific_prompts(self) -> Dict:
        """Get children's book-specific prompts"""
        return {
            "children_story_prompt": {
                "params": {"temperature": 0.8, "max_tokens": 1200},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a children's book author. Create age-appropriate, engaging stories that teach valuable lessons."
                    },
                    {
                        "role": "user",
                        "content": "Create a children's story for ages {target_age} about {theme}. Include educational elements and positive messaging."
                    }
                ]
            },
            "children_activity_prompt": {
                "params": {"temperature": 0.6, "max_tokens": 800},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an educational activity designer. Create engaging, age-appropriate activities that support learning."
                    },
                    {
                        "role": "user",
                        "content": "Design activities for children ages {target_age} to reinforce learning about {subject}."
                    }
                ]
            }
        }

    def _get_academic_specific_prompts(self) -> Dict:
        """Get academic journal-specific prompts"""
        return {
            "academic_abstract_prompt": {
                "params": {"temperature": 0.3, "max_tokens": 500},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an academic writing expert. Create clear, structured abstracts that summarize research findings."
                    },
                    {
                        "role": "user",
                        "content": "Write an academic abstract for research on: {research_topic}. Include background, methods, findings, and implications."
                    }
                ]
            },
            "literature_review_prompt": {
                "params": {"temperature": 0.4, "max_tokens": 2000},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are conducting academic literature review. Synthesize existing research and identify gaps in knowledge."
                    },
                    {
                        "role": "user",
                        "content": "Conduct a literature review on {research_area}. Identify key themes, methodologies, and research gaps."
                    }
                ]
            }
        }

    def _update_prompts_with_focus(self, prompts: Dict, content_focus: str) -> None:
        """Update existing prompts to reflect content focus"""
        focus_addition = f"\n\nThis content should align with our focus on {content_focus}."

        # Update key prompts with focus
        focus_prompts = ["imprint_quotes_prompt", "storefront_get_en_motivation", "back_cover_text"]

        for prompt_key in focus_prompts:
            if prompt_key in prompts and "messages" in prompts[prompt_key]:
                for message in prompts[prompt_key]["messages"]:
                    if message["role"] == "user":
                        message["content"] += focus_addition
                        break

    def _generate_data_json(self, codex_type_name: str, requirements: Dict, codex_dir: Path) -> Path:
        """Generate static data configuration for the codex type"""

        data_config = {
            "codex_type": codex_type_name,
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "format_specifications": self._get_format_specs(codex_type_name, requirements),
            "content_structure": self._get_content_structure(codex_type_name, requirements),
            "metadata_requirements": self._get_metadata_requirements(codex_type_name, requirements),
            "validation_rules": self._get_validation_rules(codex_type_name, requirements),
            "processing_options": self._get_processing_options(codex_type_name, requirements)
        }

        output_path = codex_dir / f"{codex_type_name}_data.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_config, f, indent=4, ensure_ascii=False)

        logger.debug(f"Generated data file: {output_path}")
        return output_path

    def _get_format_specs(self, codex_type_name: str, requirements: Dict) -> Dict:
        """Get format specifications for the codex type"""

        format_specs = {
            "poetry_collection": {
                "typical_page_count": "64-128",
                "trim_size": "5.5x8.5 or 6x9",
                "binding": "perfect bound",
                "interior_layout": "poetry_formatted",
                "special_requirements": ["line_breaks", "stanza_spacing", "poem_titles"]
            },
            "technical_manual": {
                "typical_page_count": "150-300",
                "trim_size": "7x10 or 8.5x11",
                "binding": "perfect bound or coil",
                "interior_layout": "technical_manual",
                "special_requirements": ["code_blocks", "diagrams", "cross_references", "appendices"]
            },
            "children_book": {
                "typical_page_count": "24-48",
                "trim_size": "8.5x8.5 or 8.5x11",
                "binding": "saddle stitched or perfect bound",
                "interior_layout": "children_illustrated",
                "special_requirements": ["large_text", "illustration_spaces", "safety_considerations"]
            },
            "academic_journal": {
                "typical_page_count": "200-400",
                "trim_size": "6x9 or 7x10",
                "binding": "perfect bound",
                "interior_layout": "academic_journal",
                "special_requirements": ["citations", "references", "peer_review_indicators"]
            },
            "pilsa_book": {
                "typical_page_count": "216",
                "trim_size": "6x9",
                "binding": "perfect bound",
                "interior_layout": "quote_and_facing_page",
                "special_requirements": ["meditation_spacing", "quote_formatting"]
            }
        }

        return format_specs.get(codex_type_name, {
            "typical_page_count": "100-200",
            "trim_size": "6x9",
            "binding": "perfect bound",
            "interior_layout": "standard",
            "special_requirements": []
        })

    def _get_content_structure(self, codex_type_name: str, requirements: Dict) -> Dict:
        """Get content structure requirements"""

        structures = {
            "poetry_collection": {
                "front_matter": ["title_page", "copyright", "table_of_contents", "introduction"],
                "main_content": ["poem_sections", "author_notes"],
                "back_matter": ["about_author", "acknowledgments", "index_first_lines"]
            },
            "technical_manual": {
                "front_matter": ["title_page", "copyright", "table_of_contents", "preface"],
                "main_content": ["chapters", "procedures", "examples"],
                "back_matter": ["appendices", "glossary", "index", "references"]
            },
            "children_book": {
                "front_matter": ["title_page", "copyright"],
                "main_content": ["story_pages", "illustrations"],
                "back_matter": ["about_author", "discussion_questions"]
            },
            "academic_journal": {
                "front_matter": ["title_page", "editorial_board", "table_of_contents"],
                "main_content": ["articles", "reviews", "communications"],
                "back_matter": ["author_guidelines", "subscription_info"]
            }
        }

        return structures.get(codex_type_name, {
            "front_matter": ["title_page", "copyright", "table_of_contents"],
            "main_content": ["chapters"],
            "back_matter": ["about_author"]
        })

    def _get_metadata_requirements(self, codex_type_name: str, requirements: Dict) -> List[str]:
        """Get metadata requirements for the codex type"""

        base_metadata = ["title", "author", "isbn", "publication_date", "page_count", "price"]

        type_specific = {
            "poetry_collection": ["poet_bio", "poem_count", "literary_awards"],
            "technical_manual": ["skill_level", "software_version", "prerequisites"],
            "children_book": ["age_range", "reading_level", "educational_standards"],
            "academic_journal": ["doi", "peer_review_status", "academic_discipline"]
        }

        return base_metadata + type_specific.get(codex_type_name, [])

    def _get_validation_rules(self, codex_type_name: str, requirements: Dict) -> List[str]:
        """Get validation rules for the codex type"""

        rules = {
            "poetry_collection": [
                "verify_poem_attribution",
                "check_copyright_permissions",
                "validate_line_breaks"
            ],
            "technical_manual": [
                "verify_technical_accuracy",
                "test_code_examples",
                "check_cross_references"
            ],
            "children_book": [
                "age_appropriateness_check",
                "safety_content_review",
                "educational_alignment"
            ],
            "academic_journal": [
                "peer_review_completion",
                "citation_format_check",
                "plagiarism_detection"
            ]
        }

        return rules.get(codex_type_name, ["basic_content_validation"])

    def _get_processing_options(self, codex_type_name: str, requirements: Dict) -> Dict:
        """Get processing options for the codex type"""

        return {
            "requires_illustration_processing": codex_type_name in ["children_book", "technical_manual"],
            "supports_multilingual": len(requirements.get('languages', [])) > 1,
            "batch_processing_enabled": True,
            "quality_assurance_level": requirements.get('sensitivity_level', 'medium')
        }

    def _generate_custom_prepress(self, codex_type_name: str, requirements: Dict, codex_dir: Path) -> Path:
        """Generate customized prepress.py for the codex type"""

        class_name = f"{codex_type_name.title().replace('_', '')}Prepress"

        custom_prepress = f'''# {codex_type_name}_prepress.py
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class {class_name}:
    """Customized prepress processing for {codex_type_name} format"""
    
    def __init__(self):
        self.codex_type = "{codex_type_name}"
        self.format_specs = self._load_format_specs()
    
    def process_content(self, content: str, metadata: Dict[str, Any]) -> str:
        """Process content according to {codex_type_name} specifications"""
        try:
            processed_content = content
            
            # Apply codex-type specific processing
            processed_content = self._apply_format_specific_processing(processed_content, metadata)
            processed_content = self._apply_template_formatting(processed_content, metadata)
            processed_content = self._validate_content_structure(processed_content, metadata)
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error processing {{self.codex_type}} content: {{e}}")
            return content
    
    def _apply_format_specific_processing(self, content: str, metadata: Dict[str, Any]) -> str:
        """Apply processing specific to {codex_type_name} format"""
        {self._generate_format_specific_methods(codex_type_name, requirements)}
        
        return content
    
    def _apply_template_formatting(self, content: str, metadata: Dict[str, Any]) -> str:
        """Apply template-specific formatting"""
        # Add LaTeX commands and formatting specific to this codex type
        return content
    
    def _validate_content_structure(self, content: str, metadata: Dict[str, Any]) -> str:
        """Validate that content meets {codex_type_name} structure requirements"""
        {self._generate_validation_methods(codex_type_name, requirements)}
        
        return content
    
    def _load_format_specs(self) -> Dict:
        """Load format specifications for this codex type"""
        return {{
            "codex_type": "{codex_type_name}",
            "version": "1.0.0"
        }}
'''

        output_path = codex_dir / f"{codex_type_name}_prepress.py"
        output_path.write_text(custom_prepress, encoding='utf-8')

        logger.debug(f"Generated prepress file: {output_path}")
        return output_path

    def _generate_format_specific_methods(self, codex_type_name: str, requirements: Dict) -> str:
        """Generate format-specific processing methods"""

        methods = {
            "poetry_collection": '''
        # Poetry-specific processing
        content = self._format_poem_structure(content)
        content = self._handle_line_breaks(content)
        content = self._format_stanza_spacing(content)''',

            "technical_manual": '''
        # Technical manual processing
        content = self._format_code_blocks(content)
        content = self._process_diagrams(content)
        content = self._create_cross_references(content)''',

            "children_book": '''
        # Children's book processing
        content = self._ensure_age_appropriate_language(content)
        content = self._format_large_text(content)
        content = self._mark_illustration_spaces(content)''',

            "academic_journal": '''
        # Academic journal processing
        content = self._format_citations(content)
        content = self._process_references(content)
        content = self._add_peer_review_markers(content)'''
        }

        return methods.get(codex_type_name, '        # Standard processing\n        pass')

    def _generate_validation_methods(self, codex_type_name: str, requirements: Dict) -> str:
        """Generate validation methods"""

        validations = {
            "poetry_collection": '''
        # Validate poetry structure
        self._validate_poem_formatting(content)
        self._check_copyright_attributions(content)''',

            "technical_manual": '''
        # Validate technical content
        self._verify_code_syntax(content)
        self._check_technical_accuracy(content)''',

            "children_book": '''
        # Validate children's content
        self._check_age_appropriateness(content)
        self._verify_safety_guidelines(content)''',

            "academic_journal": '''
        # Validate academic content
        self._verify_citation_format(content)
        self._check_academic_standards(content)'''
        }

        return validations.get(codex_type_name, '        # Standard validation\n        pass')

    def _generate_validation_rules(self, codex_type_name: str, requirements: Dict, codex_dir: Path) -> Path:
        """Generate validation rules file"""

        rules = {
            "codex_type": codex_type_name,
            "validation_rules": self._get_validation_rules(codex_type_name, requirements),
            "quality_standards": requirements.get('quality_standards', []),
            "sensitivity_level": requirements.get('sensitivity_level', 'medium')
        }

        output_path = codex_dir / f"{codex_type_name}_validation.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=4, ensure_ascii=False)

        logger.debug(f"Generated validation file: {output_path}")
        return output_path

    def _generate_documentation(self, codex_type_name: str, requirements: Dict, codex_dir: Path) -> Path:
        """Generate documentation for the codex type"""

        doc_content = f"""# {codex_type_name.title().replace('_', ' ')} Codex Type

## Overview
This codex type was generated for the {requirements.get('tentative_name', 'New Imprint')} imprint.

**Type:** {codex_type_name}
**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Mission
{requirements.get('content_focus', 'Content focus not specified')}

## Format Specifications
{self._format_specs_to_markdown(self._get_format_specs(codex_type_name, requirements))}

## Content Structure
{self._structure_to_markdown(self._get_content_structure(codex_type_name, requirements))}

## Usage Instructions

### 1. Setup
Ensure all generated files are in place:
- `{codex_type_name}_prompts.json`
- `{codex_type_name}_data.json` 
- `{codex_type_name}_prepress.py`
- `{codex_type_name}_validation.json`

### 2. Integration
Add this codex type to your main configuration files.

### 3. Testing
Run validation tests to ensure proper integration.

## Customization
You can customize this codex type by modifying the generated files according to your specific needs.

## Support
For questions about this codex type, refer to the main Codexes Factory documentation.
"""

        output_path = codex_dir / f"{codex_type_name}_README.md"
        output_path.write_text(doc_content, encoding='utf-8')

        logger.debug(f"Generated documentation: {output_path}")
        return output_path

    def _format_specs_to_markdown(self, specs: Dict) -> str:
        """Convert format specs to markdown"""
        lines = []
        for key, value in specs.items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        return '\n'.join(lines)

    def _structure_to_markdown(self, structure: Dict) -> str:
        """Convert content structure to markdown"""
        lines = []
        for section, items in structure.items():
            lines.append(f"### {section.replace('_', ' ').title()}")
            for item in items:
                lines.append(f"- {item.replace('_', ' ').title()}")
            lines.append("")
        return '\n'.join(lines)

    def _get_default_prompts(self) -> Dict:
        """Get default prompts structure"""
        return {
            "imprint_name": "default_imprint",
            "imprint_intro": "Default imprint introduction",
            "prompt_keys": ["gemini_get_basic_info"],
            "gemini_get_basic_info": {
                "params": {"temperature": 0.3, "max_tokens": 1000},
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional book metadata specialist."
                    },
                    {
                        "role": "user",
                        "content": "Generate basic book information for: {book_content}"
                    }
                ]
            }
        }