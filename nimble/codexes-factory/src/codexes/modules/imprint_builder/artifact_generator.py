"""
Comprehensive artifact generation system for creating all imprint production artifacts.
"""

import logging
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil

from .imprint_expander import ExpandedImprint
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class TemplateSet:
    """Complete set of LaTeX templates for an imprint."""
    main_template: str = ""
    chapter_template: str = ""
    cover_template: str = ""
    title_page_template: str = ""
    copyright_template: str = ""
    toc_template: str = ""
    bibliography_template: str = ""
    index_template: str = ""
    custom_commands: str = ""
    style_definitions: str = ""


@dataclass
class PromptSet:
    """Complete set of LLM prompts for an imprint."""
    content_generation: Dict[str, str] = field(default_factory=dict)
    editing_prompts: Dict[str, str] = field(default_factory=dict)
    metadata_prompts: Dict[str, str] = field(default_factory=dict)
    marketing_prompts: Dict[str, str] = field(default_factory=dict)
    quality_control: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    """Complete workflow configuration for an imprint."""
    pipeline_settings: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    automation_settings: Dict[str, Any] = field(default_factory=dict)
    quality_standards: Dict[str, Any] = field(default_factory=dict)
    distribution_config: Dict[str, Any] = field(default_factory=dict)


class ImprintArtifactGenerator:
    """Generates all production artifacts for an imprint."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load base templates and configurations
        self.base_templates = self._load_base_templates()
        self.base_prompts = self._load_base_prompts()
        self.base_configs = self._load_base_configs()

    def generate_all_artifacts(self, imprint: ExpandedImprint, output_dir: str) -> Dict[str, Any]:
        """Generate all artifacts for an imprint."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            results = {
                'imprint_name': imprint.branding.imprint_name,
                'generated_at': datetime.now().isoformat(),
                'artifacts': {},
                'errors': [],
                'warnings': []
            }
            
            # Generate LaTeX templates
            self.logger.info("Generating LaTeX templates...")
            template_result = self.generate_latex_templates(imprint, str(output_path / "templates"))
            results['artifacts']['templates'] = template_result
            
            # Generate LLM prompts
            self.logger.info("Generating LLM prompts...")
            prompt_result = self.generate_llm_prompts(imprint, str(output_path / "prompts.json"))
            results['artifacts']['prompts'] = prompt_result
            
            # Generate configuration files
            self.logger.info("Generating configuration files...")
            config_result = self.generate_configuration_files(imprint, str(output_path / "configs"))
            results['artifacts']['configs'] = config_result
            
            # Generate workflow definitions
            self.logger.info("Generating workflow definitions...")
            workflow_result = self.generate_workflow_config(imprint, str(output_path / "workflow.json"))
            results['artifacts']['workflow'] = workflow_result
            
            # Generate documentation
            self.logger.info("Generating documentation...")
            docs_result = self.generate_documentation(imprint, str(output_path / "docs"))
            results['artifacts']['documentation'] = docs_result
            
            # Validate all generated artifacts
            self.logger.info("Validating generated artifacts...")
            validation_result = self.validate_artifacts(str(output_path))
            results['validation'] = validation_result
            
            self.logger.info(f"Successfully generated all artifacts for {imprint.branding.imprint_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating artifacts: {e}")
            results['errors'].append(f"Generation failed: {str(e)}")
            return results

    def generate_latex_templates(self, imprint: ExpandedImprint, output_dir: str) -> Dict[str, Any]:
        """Generate customized LaTeX templates."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            template_set = TemplateSet()
            
            # Generate main template
            template_set.main_template = self._generate_main_template(imprint)
            
            # Generate cover template
            template_set.cover_template = self._generate_cover_template(imprint)
            
            # Generate style definitions
            template_set.style_definitions = self._generate_style_definitions(imprint)
            
            # Generate custom commands
            template_set.custom_commands = self._generate_custom_commands(imprint)
            
            # Write templates to files
            template_files = {
                'template.tex': template_set.main_template,
                'cover.tex': template_set.cover_template,
                'styles.sty': template_set.style_definitions,
                'commands.sty': template_set.custom_commands
            }
            
            for filename, content in template_files.items():
                file_path = output_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Test template compilation
            compilation_result = self._test_template_compilation(str(output_path))
            
            return {
                'status': 'success',
                'files_generated': list(template_files.keys()),
                'compilation_test': compilation_result,
                'output_directory': str(output_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating LaTeX templates: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def generate_llm_prompts(self, imprint: ExpandedImprint, output_file: str) -> Dict[str, Any]:
        """Generate customized LLM prompts."""
        try:
            prompt_set = PromptSet()
            
            # Generate content generation prompts
            prompt_set.content_generation = self._generate_content_prompts(imprint)
            
            # Generate editing prompts
            prompt_set.editing_prompts = self._generate_editing_prompts(imprint)
            
            # Generate metadata prompts
            prompt_set.metadata_prompts = self._generate_metadata_prompts(imprint)
            
            # Generate marketing prompts
            prompt_set.marketing_prompts = self._generate_marketing_prompts(imprint)
            
            # Generate quality control prompts
            prompt_set.quality_control = self._generate_quality_prompts(imprint)
            
            # Combine all prompts
            all_prompts = {
                'imprint_info': {
                    'name': imprint.branding.imprint_name,
                    'mission': imprint.branding.mission_statement,
                    'genres': imprint.publishing.primary_genres,
                    'audience': imprint.publishing.target_audience,
                    'brand_voice': imprint.branding.brand_voice
                },
                'content_generation': prompt_set.content_generation,
                'editing': prompt_set.editing_prompts,
                'metadata': prompt_set.metadata_prompts,
                'marketing': prompt_set.marketing_prompts,
                'quality_control': prompt_set.quality_control,
                'generated_at': datetime.now().isoformat()
            }
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_prompts, f, indent=2, ensure_ascii=False)
            
            return {
                'status': 'success',
                'prompts_generated': len(all_prompts) - 2,  # Exclude metadata fields
                'output_file': output_file
            }
            
        except Exception as e:
            self.logger.error(f"Error generating LLM prompts: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def generate_configuration_files(self, imprint: ExpandedImprint, output_dir: str) -> Dict[str, Any]:
        """Generate all configuration files."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            configs = {}
            
            # Generate imprint configuration
            configs['imprint.json'] = self._generate_imprint_config(imprint)
            
            # Generate LSI configuration
            configs['lsi_config.json'] = self._generate_lsi_config(imprint)
            
            # Generate pipeline configuration
            configs['pipeline_config.json'] = self._generate_pipeline_config(imprint)
            
            # Generate distribution configuration
            configs['distribution_config.json'] = self._generate_distribution_config(imprint)
            
            # Write configuration files
            for filename, config in configs.items():
                file_path = output_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            return {
                'status': 'success',
                'configs_generated': list(configs.keys()),
                'output_directory': str(output_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating configuration files: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def generate_workflow_config(self, imprint: ExpandedImprint, output_file: str) -> Dict[str, Any]:
        """Generate workflow configuration."""
        try:
            workflow = WorkflowConfig()
            
            # Pipeline settings
            workflow.pipeline_settings = {
                'imprint_name': imprint.branding.imprint_name,
                'default_trim_size': imprint.design.trim_sizes[0] if imprint.design.trim_sizes else '6x9',
                'default_binding': 'paperback',
                'quality_level': 'high',
                'automation_level': 'medium'
            }
            
            # Validation rules
            workflow.validation_rules = {
                'required_metadata': ['title', 'author', 'isbn13', 'summary_long'],
                'content_validation': {
                    'min_word_count': 10000,
                    'max_word_count': 200000,
                    'required_sections': ['title_page', 'copyright', 'content']
                },
                'design_validation': {
                    'font_requirements': imprint.design.typography,
                    'color_requirements': imprint.design.color_palette,
                    'layout_requirements': imprint.design.layout_specifications
                }
            }
            
            # Automation settings
            workflow.automation_settings = imprint.production.automation_settings
            
            # Quality standards
            workflow.quality_standards = imprint.production.quality_standards
            
            # Distribution configuration
            workflow.distribution_config = {
                'primary_channels': imprint.distribution.primary_channels,
                'secondary_channels': imprint.distribution.secondary_channels,
                'international': imprint.distribution.international_distribution,
                'digital_first': imprint.distribution.digital_first
            }
            
            # Convert to dictionary
            workflow_dict = {
                'pipeline_settings': workflow.pipeline_settings,
                'validation_rules': workflow.validation_rules,
                'automation_settings': workflow.automation_settings,
                'quality_standards': workflow.quality_standards,
                'distribution_config': workflow.distribution_config,
                'generated_at': datetime.now().isoformat()
            }
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_dict, f, indent=2, ensure_ascii=False)
            
            return {
                'status': 'success',
                'output_file': output_file
            }
            
        except Exception as e:
            self.logger.error(f"Error generating workflow config: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def generate_documentation(self, imprint: ExpandedImprint, output_dir: str) -> Dict[str, Any]:
        """Generate documentation for the imprint."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Safe attribute access
            imprint_name = getattr(imprint.branding, 'imprint_name', 'Imprint')
            mission = getattr(imprint.branding, 'mission_statement', 'Mission statement not available')
            
            docs = {
                'README.md': f"""# {imprint_name}

{mission}

## Overview

This is the documentation for {imprint_name}.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
""",
                'STYLE_GUIDE.md': f"""# {imprint_name} Style Guide

## Brand Identity

Style guide documentation for {imprint_name}.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
""",
                'WORKFLOW.md': f"""# {imprint_name} Workflow Documentation

## Production Workflow

Workflow documentation for {imprint_name}.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
""",
                'TROUBLESHOOTING.md': f"""# {imprint_name} Troubleshooting Guide

## Common Issues

Troubleshooting guide for {imprint_name}.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
"""
            }
            
            # Write documentation files
            for filename, content in docs.items():
                file_path = output_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return {
                'status': 'success',
                'docs_generated': list(docs.keys()),
                'output_directory': str(output_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating documentation: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def validate_artifacts(self, artifacts_dir: str) -> Dict[str, Any]:
        """Validate all generated artifacts."""
        try:
            artifacts_path = Path(artifacts_dir)
            validation_results = {
                'overall_valid': True,
                'template_validation': {},
                'config_validation': {},
                'prompt_validation': {},
                'issues': []
            }
            
            # Validate templates
            templates_dir = artifacts_path / "templates"
            if templates_dir.exists():
                validation_results['template_validation'] = self._validate_templates(str(templates_dir))
                if not validation_results['template_validation'].get('valid', True):
                    validation_results['overall_valid'] = False
            
            # Validate configurations
            configs_dir = artifacts_path / "configs"
            if configs_dir.exists():
                validation_results['config_validation'] = self._validate_configs(str(configs_dir))
                if not validation_results['config_validation'].get('valid', True):
                    validation_results['overall_valid'] = False
            
            # Validate prompts
            prompts_file = artifacts_path / "prompts.json"
            if prompts_file.exists():
                validation_results['prompt_validation'] = self._validate_prompts(str(prompts_file))
                if not validation_results['prompt_validation'].get('valid', True):
                    validation_results['overall_valid'] = False
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating artifacts: {e}")
            return {
                'overall_valid': False,
                'error': str(e)
            }

    def _hex_to_cmyk(self, hex_color: str) -> str:
        """Convert hex color to approximate CMYK values for LaTeX."""
        # Remove # if present
        hex_color = hex_color.replace('#', '')
        
        # Convert hex to RGB
        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
        except (ValueError, IndexError):
            # Fallback to neutral gray if conversion fails
            return "0,0,0,0.5"
        
        # Convert RGB to CMYK (approximate conversion)
        k = 1 - max(r, g, b)
        if k == 1:
            return "0,0,0,1"
        
        c = (1 - r - k) / (1 - k)
        m = (1 - g - k) / (1 - k)
        y = (1 - b - k) / (1 - k)
        
        # Round to 2 decimal places and format
        return f"{c:.2f},{m:.2f},{y:.2f},{k:.2f}"

    def _generate_main_template(self, imprint: ExpandedImprint) -> str:
        """Generate the main LaTeX template."""
        # Get design specifications safely
        typography = getattr(imprint.design, 'typography', {})
        colors = getattr(imprint.design, 'color_palette', {})
        layout = getattr(imprint.design, 'layout_specifications', {})
        
        # Safe font access
        primary_font = getattr(typography, 'primary_font', 'Minion Pro') if hasattr(typography, 'primary_font') else 'Minion Pro'
        secondary_font = getattr(typography, 'secondary_font', 'Myriad Pro') if hasattr(typography, 'secondary_font') else 'Myriad Pro'
        
        template = f"""\\documentclass[{imprint.design.trim_sizes[0] if imprint.design.trim_sizes else '6in,9in'}]{{memoir}}

% {imprint.branding.imprint_name} Template
% Generated on {datetime.now().strftime('%Y-%m-%d')}
% Optimized for professional print production

% Typography settings
\\usepackage{{fontspec}}
\\setmainfont{{{primary_font}}}
\\setsansfont{{{secondary_font}}}

% Color definitions for CMYK printing
\\usepackage[cmyk]{{xcolor}}
\\definecolor{{primarycolor}}{{cmyk}}{{{self._hex_to_cmyk(colors.get('primary', '#2C3E50'))}}}
\\definecolor{{secondarycolor}}{{cmyk}}{{{self._hex_to_cmyk(colors.get('secondary', '#3498DB'))}}}
\\definecolor{{accentcolor}}{{cmyk}}{{{self._hex_to_cmyk(colors.get('accent', '#E74C3C'))}}}

% Professional printing settings
\\usepackage{{microtype}}  % Improved typography
\\usepackage{{graphicx}}   % Graphics support

% Layout settings
\\setlrmarginsandblock{{0.75in}}{{0.75in}}{{*}}
\\setulmarginsandblock{{0.75in}}{{0.75in}}{{*}}
\\checkandfixthelayout

% Chapter styling
\\chapterstyle{{default}}
\\renewcommand{{\\chaptitlefont}}{{\\Large\\sffamily\\color{{primarycolor}}}}

% Header/footer styling
\\pagestyle{{ruled}}
\\makeevenhead{{ruled}}{{\\sffamily\\color{{secondarycolor}}\\leftmark}}{{}}{{\\sffamily\\color{{secondarycolor}}\\thepage}}
\\makeoddhead{{ruled}}{{\\sffamily\\color{{secondarycolor}}\\thepage}}{{}}{{\\sffamily\\color{{secondarycolor}}\\rightmark}}

% Custom commands for {imprint.branding.imprint_name}
\\newcommand{{\\imprintname}}{{{imprint.branding.imprint_name}}}
\\newcommand{{\\imprintmission}}{{{imprint.branding.mission_statement}}}

% Book-specific commands (to be set when using the template)
\\newcommand{{\\booktitle}}{{[BOOK TITLE]}}
\\newcommand{{\\bookauthor}}{{[AUTHOR NAME]}}
\\newcommand{{\\bookyear}}{{\\the\\year}}

\\begin{{document}}

% Title page
\\begin{{titlingpage}}
\\centering
{{\\Huge\\sffamily\\color{{primarycolor}} \\booktitle}}\\\\[2cm]
{{\\Large\\sffamily \\bookauthor}}\\\\[1cm]
{{\\large\\sffamily\\color{{secondarycolor}} \\imprintname}}
\\end{{titlingpage}}

% Copyright page
\\clearpage
\\thispagestyle{{empty}}
\\vspace*{{\\fill}}
{{\\small
Copyright \\copyright\\ \\bookyear\\ \\bookauthor\\\\[0.5cm]
Published by \\imprintname\\\\
\\imprintmission\\\\[0.5cm]
All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher.
}}

% Table of contents
\\clearpage
\\tableofcontents

% Main content
\\mainmatter

% Content will be inserted here

\\end{{document}}
"""
        return template

    def _generate_cover_template(self, imprint: ExpandedImprint) -> str:
        """Generate cover template."""
        colors = getattr(imprint.design, 'color_palette', {})
        cover_style = getattr(imprint.design, 'cover_style', {})
        typography = getattr(imprint.design, 'typography', {})
        
        # Safe font access
        primary_font = getattr(typography, 'primary_font', 'Minion Pro') if hasattr(typography, 'primary_font') else 'Minion Pro'
        secondary_font = getattr(typography, 'secondary_font', 'Arial') if hasattr(typography, 'secondary_font') else 'Arial'
        
        template = f"""\\documentclass{{article}}
\\usepackage[paperwidth=6.125in,paperheight=9.25in,margin=0in]{{geometry}}
\\usepackage[cmyk]{{xcolor}}
\\usepackage{{fontspec}}
\\usepackage{{tikz}}
\\usepackage{{microtype}}

% {imprint.branding.imprint_name} Cover Template
% Optimized for professional CMYK printing

% CMYK color definitions for professional printing
\\definecolor{{primarycolor}}{{cmyk}}{{{self._hex_to_cmyk(colors.get('primary', '#2C3E50'))}}}
\\definecolor{{secondarycolor}}{{cmyk}}{{{self._hex_to_cmyk(colors.get('secondary', '#3498DB'))}}}
\\definecolor{{accentcolor}}{{cmyk}}{{{self._hex_to_cmyk(colors.get('accent', '#E74C3C'))}}}

% Custom commands for title and author (to be set when using the template)
\\newcommand{{\\booktitle}}{{[BOOK TITLE]}}
\\newcommand{{\\bookauthor}}{{[AUTHOR NAME]}}

% Font settings
\\setmainfont{{{primary_font}}}
\\setsansfont{{{secondary_font}}}

\\begin{{document}}
\\pagestyle{{empty}}

\\begin{{tikzpicture}}[remember picture,overlay]
% Background
\\fill[primarycolor] (current page.south west) rectangle (current page.north east);

% Title area
\\node[text=white,font=\\Huge\\sffamily,text width=5in,align=center] at (current page.center) {{\\booktitle}};

% Author area
\\node[text=white,font=\\Large\\sffamily,text width=5in,align=center] at ([yshift=-2in]current page.center) {{\\bookauthor}};

% Imprint logo area
\\node[text=secondarycolor,font=\\large\\sffamily] at ([yshift=-4in]current page.center) {{{imprint.branding.imprint_name}}};

\\end{{tikzpicture}}

\\end{{document}}
"""
        return template

    def _generate_style_definitions(self, imprint: ExpandedImprint) -> str:
        """Generate style definitions."""
        colors = getattr(imprint.design, 'color_palette', {})
        primary_color = getattr(colors, 'primary', '#2C3E50') if hasattr(colors, 'primary') else '#2C3E50'
        secondary_color = getattr(colors, 'secondary', '#3498DB') if hasattr(colors, 'secondary') else '#3498DB'
        
        return f"""% {imprint.branding.imprint_name} Style Definitions
% Generated on {datetime.now().strftime('%Y-%m-%d')}

\\ProvidesPackage{{{imprint.branding.imprint_name.lower().replace(' ', '')}_styles}}

% Brand colors - CMYK for professional printing
\\definecolor{{brandprimary}}{{cmyk}}{{{self._hex_to_cmyk(primary_color)}}}
\\definecolor{{brandsecondary}}{{cmyk}}{{{self._hex_to_cmyk(secondary_color)}}}

% Typography styles
\\newcommand{{\\brandtitle}}{{\\sffamily\\color{{brandprimary}}\\Large}}
\\newcommand{{\\brandsubtitle}}{{\\sffamily\\color{{brandsecondary}}\\large}}
\\newcommand{{\\brandtext}}{{\\rmfamily}}

% Layout styles
\\newcommand{{\\brandspacing}}{{\\setlength{{\\parskip}}{{0.5em}}}}
\\newcommand{{\\brandindent}}{{\\setlength{{\\parindent}}{{1.5em}}}}
"""

    def _generate_custom_commands(self, imprint: ExpandedImprint) -> str:
        """Generate custom LaTeX commands."""
        return f"""% {imprint.branding.imprint_name} Custom Commands
% Generated on {datetime.now().strftime('%Y-%m-%d')}

\\ProvidesPackage{{{imprint.branding.imprint_name.lower().replace(' ', '')}_commands}}

% Imprint information
\\newcommand{{\\imprintname}}{{{imprint.branding.imprint_name}}}
\\newcommand{{\\imprinttagline}}{{{imprint.branding.tagline}}}
\\newcommand{{\\imprintmission}}{{{imprint.branding.mission_statement}}}

% Formatting commands
\\newcommand{{\\emphasis}}[1]{{\\textcolor{{brandprimary}}{{\\textbf{{#1}}}}}}
\\newcommand{{\\highlight}}[1]{{\\textcolor{{brandsecondary}}{{#1}}}}

% Chapter and section styling
\\newcommand{{\\brandchapter}}[1]{{\\chapter{{\\color{{brandprimary}}#1}}}}
\\newcommand{{\\brandsection}}[1]{{\\section{{\\color{{brandsecondary}}#1}}}}
"""

    def _generate_content_prompts(self, imprint: ExpandedImprint) -> Dict[str, str]:
        """Generate content generation prompts."""
        brand_voice = imprint.branding.brand_voice
        audience = imprint.publishing.target_audience
        genres = ', '.join(imprint.publishing.primary_genres)
        
        return {
            'chapter_generation': f"""
            You are writing for {imprint.branding.imprint_name}, which focuses on {genres} for {audience}.
            
            Brand voice: {brand_voice}
            Mission: {imprint.branding.mission_statement}
            
            Generate a chapter that aligns with our brand values: {', '.join(imprint.branding.brand_values)}
            
            Ensure the content is engaging, well-structured, and appropriate for our target audience.
            """,
            
            'content_expansion': f"""
            Expand this content outline for {imprint.branding.imprint_name}.
            
            Our focus: {genres}
            Our audience: {audience}
            Our voice: {brand_voice}
            
            Create detailed, engaging content that reflects our mission: {imprint.branding.mission_statement}
            """,
            
            'dialogue_generation': f"""
            Generate dialogue for {imprint.branding.imprint_name} that reflects our brand voice: {brand_voice}
            
            Target audience: {audience}
            Genre focus: {genres}
            
            Ensure dialogue is authentic, engaging, and appropriate for our readership.
            """
        }

    def _generate_editing_prompts(self, imprint: ExpandedImprint) -> Dict[str, str]:
        """Generate editing prompts."""
        return {
            'content_review': f"""
            Review this content for {imprint.branding.imprint_name}.
            
            Check for:
            - Alignment with our mission: {imprint.branding.mission_statement}
            - Appropriate tone for our audience: {imprint.publishing.target_audience}
            - Consistency with our brand voice: {imprint.branding.brand_voice}
            - Quality standards for {', '.join(imprint.publishing.primary_genres)}
            
            Provide specific suggestions for improvement.
            """,
            
            'style_consistency': f"""
            Ensure this text maintains consistency with {imprint.branding.imprint_name} style guidelines.
            
            Brand voice: {imprint.branding.brand_voice}
            Target audience: {imprint.publishing.target_audience}
            
            Check for tone, terminology, and stylistic consistency.
            """
        }

    def _generate_metadata_prompts(self, imprint: ExpandedImprint) -> Dict[str, str]:
        """Generate metadata generation prompts."""
        return {
            'description_generation': f"""
            Generate a compelling book description for {imprint.branding.imprint_name}.
            
            Our focus: {', '.join(imprint.publishing.primary_genres)}
            Our audience: {imprint.publishing.target_audience}
            Our positioning: {imprint.branding.unique_selling_proposition}
            
            Create a description that captures our brand essence and appeals to our target readers.
            """,
            
            'keyword_generation': f"""
            Generate relevant keywords for this {imprint.branding.imprint_name} publication.
            
            Focus areas: {', '.join(imprint.publishing.primary_genres)}
            Target market: {imprint.publishing.target_audience}
            
            Include both broad and specific keywords that align with our brand positioning.
            """
        }

    def _generate_marketing_prompts(self, imprint: ExpandedImprint) -> Dict[str, str]:
        """Generate marketing prompts."""
        return {
            'social_media': f"""
            Create social media content for {imprint.branding.imprint_name}.
            
            Brand voice: {imprint.branding.brand_voice}
            Target audience: {imprint.publishing.target_audience}
            Key values: {', '.join(imprint.branding.brand_values)}
            
            Create engaging posts that reflect our mission and connect with our readers.
            """,
            
            'press_release': f"""
            Write a press release for this {imprint.branding.imprint_name} publication.
            
            Highlight our unique positioning: {imprint.branding.unique_selling_proposition}
            Target media covering: {', '.join(imprint.publishing.primary_genres)}
            
            Emphasize what makes this publication special for our audience.
            """
        }

    def _generate_quality_prompts(self, imprint: ExpandedImprint) -> Dict[str, str]:
        """Generate quality control prompts."""
        return {
            'final_review': f"""
            Conduct a final quality review for {imprint.branding.imprint_name}.
            
            Ensure the content meets our standards:
            - Mission alignment: {imprint.branding.mission_statement}
            - Brand voice consistency: {imprint.branding.brand_voice}
            - Audience appropriateness: {imprint.publishing.target_audience}
            - Genre expectations: {', '.join(imprint.publishing.primary_genres)}
            
            Identify any issues that could impact our brand reputation.
            """,
            
            'brand_compliance': f"""
            Verify this content complies with {imprint.branding.imprint_name} brand guidelines.
            
            Check against our core values: {', '.join(imprint.branding.brand_values)}
            Ensure consistency with our positioning: {imprint.branding.unique_selling_proposition}
            
            Flag any content that doesn't align with our brand identity.
            """
        }

    def _generate_imprint_config(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate imprint configuration."""
        return {
            'imprint_name': imprint.branding.imprint_name,
            'branding': imprint.branding.__dict__,
            'design': imprint.design.__dict__,
            'publishing': imprint.publishing.__dict__,
            'production': imprint.production.__dict__,
            'distribution': imprint.distribution.__dict__,
            'marketing': imprint.marketing.__dict__,
            'generated_at': datetime.now().isoformat()
        }

    def _generate_lsi_config(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate LSI-specific configuration."""
        return {
            'imprint_name': imprint.branding.imprint_name,
            'default_values': {
                'publisher': imprint.branding.imprint_name,
                'imprint': imprint.branding.imprint_name,
                'series': '',
                'binding': 'paperback',
                'trim_size': imprint.design.trim_sizes[0] if imprint.design.trim_sizes else '6x9',
                'interior_color': 'black_white',
                'cover_finish': 'matte'
            },
            'field_mappings': {
                'description_long': 'Use marketing prompts for compelling descriptions',
                'bisac_categories': f"Focus on {', '.join(imprint.publishing.primary_genres)}",
                'keywords': 'Generate based on genre and audience'
            }
        }

    def _generate_pipeline_config(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate pipeline configuration."""
        return {
            'imprint_name': imprint.branding.imprint_name,
            'workflow_stages': imprint.production.workflow_stages,
            'quality_standards': imprint.production.quality_standards,
            'automation_settings': imprint.production.automation_settings,
            'template_settings': {
                'default_template': 'template.tex',
                'cover_template': 'cover.tex',
                'style_package': f"{imprint.branding.imprint_name.lower().replace(' ', '')}_styles"
            }
        }

    def _generate_distribution_config(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate distribution configuration."""
        return {
            'imprint_name': imprint.branding.imprint_name,
            'primary_channels': imprint.distribution.primary_channels,
            'secondary_channels': imprint.distribution.secondary_channels,
            'international_distribution': imprint.distribution.international_distribution,
            'digital_first': imprint.distribution.digital_first,
            'print_on_demand': imprint.distribution.print_on_demand,
            'sales_strategy': imprint.distribution.sales_strategy
        }

    def _test_template_compilation(self, templates_dir: str) -> Dict[str, Any]:
        """Test LaTeX template compilation."""
        try:
            # This would normally test actual LaTeX compilation
            # For now, just check if files exist and have content
            templates_path = Path(templates_dir)
            
            required_files = ['template.tex', 'cover.tex', 'styles.sty']
            missing_files = []
            
            for filename in required_files:
                file_path = templates_path / filename
                if not file_path.exists():
                    missing_files.append(filename)
                elif file_path.stat().st_size == 0:
                    missing_files.append(f"{filename} (empty)")
            
            if missing_files:
                return {
                    'success': False,
                    'errors': missing_files
                }
            
            return {
                'success': True,
                'message': 'All template files present and non-empty'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_templates(self, templates_dir: str) -> Dict[str, Any]:
        """Validate generated templates."""
        try:
            templates_path = Path(templates_dir)
            issues = []
            
            # Check for required files
            required_files = ['template.tex', 'styles.sty']
            for filename in required_files:
                file_path = templates_path / filename
                if not file_path.exists():
                    issues.append(f"Missing required file: {filename}")
                elif file_path.stat().st_size == 0:
                    issues.append(f"Empty file: {filename}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def _validate_configs(self, configs_dir: str) -> Dict[str, Any]:
        """Validate generated configurations."""
        try:
            configs_path = Path(configs_dir)
            issues = []
            
            # Check for required config files
            required_configs = ['imprint.json', 'pipeline_config.json']
            for filename in required_configs:
                file_path = configs_path / filename
                if not file_path.exists():
                    issues.append(f"Missing config file: {filename}")
                else:
                    # Try to parse JSON
                    try:
                        with open(file_path, 'r') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        issues.append(f"Invalid JSON in {filename}: {str(e)}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def _validate_prompts(self, prompts_file: str) -> Dict[str, Any]:
        """Validate generated prompts."""
        try:
            issues = []
            
            # Check if file exists and is valid JSON
            if not Path(prompts_file).exists():
                issues.append("Prompts file does not exist")
            else:
                try:
                    with open(prompts_file, 'r') as f:
                        prompts = json.load(f)
                    
                    # Check for required prompt categories
                    required_categories = ['content_generation', 'editing', 'metadata']
                    for category in required_categories:
                        if category not in prompts:
                            issues.append(f"Missing prompt category: {category}")
                        elif not prompts[category]:
                            issues.append(f"Empty prompt category: {category}")
                            
                except json.JSONDecodeError as e:
                    issues.append(f"Invalid JSON in prompts file: {str(e)}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def _safe_list_join(self, items, default="Not specified"):
        """Safely join list items, handling strings and lists."""
        if isinstance(items, list):
            return ', '.join(str(item) for item in items)
        elif isinstance(items, str):
            return items
        else:
            return default

    def _safe_get_attr(self, obj, attr, default="Not specified"):
        """Safely get attribute, handling different object types."""
        try:
            value = getattr(obj, attr, default)
            if hasattr(value, 'get') and callable(getattr(value, 'get')):
                return value
            return value if value else default
        except:
            return default

    def _generate_readme(self, imprint: ExpandedImprint) -> str:
        """Generate README documentation."""
        # Safely get attributes
        imprint_name = getattr(imprint.branding, 'imprint_name', 'Imprint')
        mission = getattr(imprint.branding, 'mission_statement', 'Mission statement not available')
        brand_values = getattr(imprint.branding, 'brand_values', [])
        usp = getattr(imprint.branding, 'unique_selling_proposition', 'Not specified')
        primary_genres = getattr(imprint.publishing, 'primary_genres', [])
        target_audience = getattr(imprint.publishing, 'target_audience', 'Not specified')
        brand_voice = getattr(imprint.branding, 'brand_voice', 'Not specified')
        workflow_stages = getattr(imprint.production, 'workflow_stages', [])
        primary_channels = getattr(imprint.distribution, 'primary_channels', [])
        secondary_channels = getattr(imprint.distribution, 'secondary_channels', [])

        return f"""# {imprint_name}

{mission}

## Overview

{imprint_name} is a specialized imprint focusing on {self._safe_list_join(primary_genres)} for {target_audience}.

### Brand Values
{chr(10).join(f'- {value}' for value in (brand_values if isinstance(brand_values, list) else []))}

### Unique Selling Proposition
{usp}

## Publishing Focus

**Primary Genres:** {self._safe_list_join(primary_genres)}
**Target Audience:** {target_audience}
**Brand Voice:** {brand_voice}

## Production Workflow

{chr(10).join(f'{i+1}. {stage}' for i, stage in enumerate(workflow_stages if isinstance(workflow_stages, list) else []))}

## Distribution Channels

**Primary:** {self._safe_list_join(primary_channels)}
**Secondary:** {self._safe_list_join(secondary_channels)}

## Contact Information

For more information about {imprint_name}, please contact our publishing team.

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
"""

    def _generate_style_guide(self, imprint: ExpandedImprint) -> str:
        """Generate style guide documentation."""
        # Safely get attributes
        imprint_name = getattr(imprint.branding, 'imprint_name', 'Imprint')
        mission = getattr(imprint.branding, 'mission_statement', 'Mission statement not available')
        brand_voice = getattr(imprint.branding, 'brand_voice', 'Not specified')
        brand_values = getattr(imprint.branding, 'brand_values', [])
        
        # Typography - handle both dict and string cases
        typography = getattr(imprint.design, 'typography', {})
        if hasattr(typography, 'get'):
            primary_font = typography.get('primary_font', 'Not specified')
            secondary_font = typography.get('secondary_font', 'Not specified')
            body_font = typography.get('body_font', 'Not specified')
        else:
            primary_font = secondary_font = body_font = 'Not specified'
        
        # Color palette - handle both dict and string cases
        color_palette = getattr(imprint.design, 'color_palette', {})
        if hasattr(color_palette, 'get'):
            primary_color = color_palette.get('primary', color_palette.get('primary_color', 'Not specified'))
            secondary_color = color_palette.get('secondary', color_palette.get('secondary_color', 'Not specified'))
            accent_color = color_palette.get('accent', color_palette.get('accent_color', 'Not specified'))
        else:
            primary_color = secondary_color = accent_color = 'Not specified'
        
        trim_sizes = getattr(imprint.design, 'trim_sizes', [])
        target_audience = getattr(imprint.publishing, 'target_audience', 'Not specified')
        primary_genres = getattr(imprint.publishing, 'primary_genres', [])

        return f"""# {imprint_name} Style Guide

## Brand Identity

### Mission Statement
{mission}

### Brand Voice
{brand_voice}

### Brand Values
{chr(10).join(f'- {value}' for value in (brand_values if isinstance(brand_values, list) else []))}

## Visual Identity

### Typography
- **Primary Font:** {primary_font}
- **Secondary Font:** {secondary_font}
- **Body Font:** {body_font}

### Color Palette
- **Primary Color:** {primary_color}
- **Secondary Color:** {secondary_color}
- **Accent Color:** {accent_color}

### Layout Specifications
- **Preferred Trim Sizes:** {self._safe_list_join(trim_sizes)}

## Content Guidelines

### Target Audience
{target_audience}

### Primary Genres
{self._safe_list_join(primary_genres)}

### Content Standards
- Maintain consistency with brand voice
- Ensure content aligns with mission statement
- Follow quality standards for target audience

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
"""

def _generate_workflow_docs(self, imprint: ExpandedImprint) -> str:


    # Safely get attributes
    imprint_name = getattr(imprint.branding, 'imprint_name', 'Imprint')
    workflow_stages = getattr(imprint.production, 'workflow_stages', [])
    quality_standards = getattr(imprint.production, 'quality_standards', {})
    automation_settings = getattr(imprint.production, 'automation_settings', {})
    primary_channels = getattr(imprint.distribution, 'primary_channels', [])
    secondary_channels = getattr(imprint.distribution, 'secondary_channels', [])

    # Handle workflow stages
    workflow_text = ""
    if isinstance(workflow_stages, list):
        workflow_text = chr(10).join(f'### {i+1}. {stage}' + chr(10) + 'Description of this stage...' + chr(10) for i, stage in enumerate(workflow_stages))
    else:
        workflow_text = "Workflow stages not available"

    # Handle quality standards
    quality_text = ""
    if hasattr(quality_standards, 'items'):
        quality_text = chr(10).join(f'- **{key}:** {value}' for key, value in quality_standards.items())
    else:
        quality_text = "- Quality standards not specified"

    # Handle automation settings
    automation_text = ""
    if hasattr(automation_settings, 'items'):
        automation_text = chr(10).join(f'- **{key}:** {value}' for key, value in automation_settings.items())
    else:
        automation_text = "- Automation settings not specified"

    return f"""# {imprint_name} Workflow Documentation

## Production Workflow

{workflow_text}

## Quality Standards

{quality_text}

## Automation Settings

{automation_text}

## Distribution Process

### Primary Channels
{chr(10).join(f'- {channel}' for channel in (primary_channels if isinstance(primary_channels, list) else []))}

### Secondary Channels
{chr(10).join(f'- {channel}' for channel in (secondary_channels if isinstance(secondary_channels, list) else []))}

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
"""

    def _generate_troubleshooting_guide(self, imprint: ExpandedImprint) -> str:
        """Generate troubleshooting guide."""
        imprint_name = getattr(imprint.branding, 'imprint_name', 'Imprint')
        
        return f"""# {imprint_name} Troubleshooting Guide

## Common Issues

### Template Compilation Issues
- Ensure all required fonts are installed
- Check LaTeX package dependencies
- Verify color definitions are valid

### Content Quality Issues
- Review against brand voice guidelines
- Check target audience appropriateness
- Ensure genre expectations are met

### Distribution Issues
- Verify channel-specific requirements
- Check file format specifications
- Ensure metadata completeness

## Support Resources

### Internal Resources
- Style Guide: See STYLE_GUIDE.md
- Workflow Documentation: See WORKFLOW.md

### External Resources
- LaTeX documentation
- Distribution channel guidelines

---
*Generated on {datetime.now().strftime('%Y-%m-%d')}*
"""

    def _load_base_templates(self) -> Dict[str, str]:
        """Load base template configurations."""
        return {
            'memoir_base': '\\documentclass{memoir}',
            'color_packages': '\\usepackage{xcolor}',
            'font_packages': '\\usepackage{fontspec}'
        }

    def _load_base_prompts(self) -> Dict[str, str]:
        """Load base prompt templates."""
        return {
            'content_base': 'Generate content that is engaging and appropriate for the target audience.',
            'editing_base': 'Review content for quality, consistency, and brand alignment.',
            'metadata_base': 'Generate accurate and compelling metadata for the publication.'
        }

    def _load_base_configs(self) -> Dict[str, Any]:
        """Load base configuration templates."""
        return {
            'pipeline_base': {
                'stages': ['intake', 'editing', 'design', 'production', 'distribution'],
                'quality_checks': True,
                'automation_level': 'medium'
            }
        }