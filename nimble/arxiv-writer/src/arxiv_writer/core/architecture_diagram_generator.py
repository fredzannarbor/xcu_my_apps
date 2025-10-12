"""
Technical Architecture Diagram Generator for ArXiv Paper

This module generates technical architecture diagrams and visual representations
of the Codexes Factory system, specifically focusing on the xynapse_traces imprint.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiagramNode:
    """Represents a node in an architecture diagram."""
    id: str
    label: str
    node_type: str
    description: str
    position: Optional[Tuple[int, int]] = None
    style: Optional[Dict[str, str]] = None


@dataclass
class DiagramEdge:
    """Represents an edge/connection in an architecture diagram."""
    source: str
    target: str
    label: str
    edge_type: str
    style: Optional[Dict[str, str]] = None


class ArchitectureDiagramGenerator:
    """Generates technical architecture diagrams for the academic paper."""
    
    def __init__(self):
        self.nodes: List[DiagramNode] = []
        self.edges: List[DiagramEdge] = []
        
    def generate_system_overview_diagram(self) -> Dict[str, Any]:
        """
        Generate a high-level system overview diagram.
        
        Returns:
            Dictionary containing diagram data for system overview
        """
        # Define system components
        nodes = [
            DiagramNode("user_interface", "Streamlit UI", "interface", "Web-based user interface for book management"),
            DiagramNode("api_layer", "API Layer", "service", "RESTful API for system interactions"),
            DiagramNode("workflow_engine", "Workflow Engine", "core", "Orchestrates book production pipeline"),
            DiagramNode("ai_services", "AI Services", "ai", "LLM integration for content generation"),
            DiagramNode("config_system", "Configuration System", "core", "Multi-level hierarchical configuration"),
            DiagramNode("metadata_engine", "Metadata Engine", "core", "Book metadata management and validation"),
            DiagramNode("prepress_pipeline", "Prepress Pipeline", "production", "LaTeX generation and PDF creation"),
            DiagramNode("distribution_system", "Distribution System", "production", "LSI CSV and distribution formats"),
            DiagramNode("storage_layer", "Storage Layer", "infrastructure", "File system and database storage"),
            DiagramNode("external_services", "External Services", "external", "Lightning Source, payment processing")
        ]
        
        # Define relationships
        edges = [
            DiagramEdge("user_interface", "api_layer", "HTTP requests", "api_call"),
            DiagramEdge("api_layer", "workflow_engine", "orchestrates", "control"),
            DiagramEdge("workflow_engine", "ai_services", "content generation", "service_call"),
            DiagramEdge("workflow_engine", "config_system", "configuration", "data_flow"),
            DiagramEdge("workflow_engine", "metadata_engine", "metadata ops", "data_flow"),
            DiagramEdge("metadata_engine", "prepress_pipeline", "book data", "data_flow"),
            DiagramEdge("metadata_engine", "distribution_system", "distribution data", "data_flow"),
            DiagramEdge("config_system", "prepress_pipeline", "templates", "configuration"),
            DiagramEdge("config_system", "distribution_system", "settings", "configuration"),
            DiagramEdge("prepress_pipeline", "storage_layer", "PDF files", "file_output"),
            DiagramEdge("distribution_system", "storage_layer", "CSV files", "file_output"),
            DiagramEdge("distribution_system", "external_services", "submission", "external_api"),
            DiagramEdge("ai_services", "storage_layer", "prompts/responses", "data_persistence")
        ]
        
        return {
            "title": "Codexes Factory System Architecture",
            "description": "High-level overview of the AI-assisted publishing platform",
            "nodes": [node.__dict__ for node in nodes],
            "edges": [edge.__dict__ for edge in edges],
            "layout_type": "hierarchical"
        }
    
    def generate_ai_integration_diagram(self) -> Dict[str, Any]:
        """
        Generate a detailed AI integration architecture diagram.
        
        Returns:
            Dictionary containing AI integration diagram data
        """
        nodes = [
            DiagramNode("llm_caller", "LLM Caller", "ai_core", "Abstraction layer for AI model interactions"),
            DiagramNode("prompt_manager", "Prompt Manager", "ai_core", "Template-based prompt management"),
            DiagramNode("response_validator", "Response Validator", "ai_core", "AI response validation and quality control"),
            DiagramNode("gemini_api", "Gemini API", "external_ai", "Google's Gemini language model"),
            DiagramNode("claude_api", "Claude API", "external_ai", "Anthropic's Claude language model"),
            DiagramNode("grok_api", "Grok API", "external_ai", "xAI's Grok language model"),
            DiagramNode("metadata_enhancer", "Metadata Enhancer", "ai_application", "AI-powered metadata completion"),
            DiagramNode("content_generator", "Content Generator", "ai_application", "AI-assisted content creation"),
            DiagramNode("quality_validator", "Quality Validator", "ai_application", "AI-powered quality assurance"),
            DiagramNode("korean_processor", "Korean Processor", "ai_application", "Korean language processing"),
            DiagramNode("config_resolver", "Config Resolver", "system", "Configuration context resolution")
        ]
        
        edges = [
            DiagramEdge("metadata_enhancer", "llm_caller", "enhancement requests", "service_call"),
            DiagramEdge("content_generator", "llm_caller", "generation requests", "service_call"),
            DiagramEdge("quality_validator", "llm_caller", "validation requests", "service_call"),
            DiagramEdge("korean_processor", "llm_caller", "translation requests", "service_call"),
            DiagramEdge("llm_caller", "prompt_manager", "prompt templates", "template_request"),
            DiagramEdge("llm_caller", "response_validator", "response validation", "validation"),
            DiagramEdge("llm_caller", "gemini_api", "API calls", "external_api"),
            DiagramEdge("llm_caller", "claude_api", "API calls", "external_api"),
            DiagramEdge("llm_caller", "grok_api", "API calls", "external_api"),
            DiagramEdge("config_resolver", "prompt_manager", "imprint context", "configuration"),
            DiagramEdge("config_resolver", "metadata_enhancer", "field mappings", "configuration"),
            DiagramEdge("response_validator", "quality_validator", "quality metrics", "feedback")
        ]
        
        return {
            "title": "AI Integration Architecture",
            "description": "Detailed view of AI service integration and orchestration",
            "nodes": [node.__dict__ for node in nodes],
            "edges": [edge.__dict__ for edge in edges],
            "layout_type": "layered"
        }
    
    def generate_configuration_hierarchy_diagram(self) -> Dict[str, Any]:
        """
        Generate a diagram showing the multi-level configuration hierarchy.
        
        Returns:
            Dictionary containing configuration hierarchy diagram data
        """
        nodes = [
            DiagramNode("global_config", "Global Defaults", "config_level", "Base configuration for all books"),
            DiagramNode("publisher_config", "Publisher Config", "config_level", "Nimble Books LLC settings"),
            DiagramNode("imprint_config", "Imprint Config", "config_level", "Xynapse Traces branding and focus"),
            DiagramNode("tranche_config", "Tranche Config", "config_level", "Series-specific settings"),
            DiagramNode("book_config", "Book Config", "config_level", "Individual book overrides"),
            DiagramNode("runtime_resolver", "Runtime Resolver", "system", "Configuration resolution engine"),
            DiagramNode("validation_engine", "Validation Engine", "system", "Configuration validation"),
            DiagramNode("context_manager", "Context Manager", "system", "Runtime context management"),
            DiagramNode("field_mapper", "Field Mapper", "system", "LSI field mapping system"),
            DiagramNode("template_engine", "Template Engine", "system", "LaTeX template resolution")
        ]
        
        edges = [
            DiagramEdge("global_config", "publisher_config", "inherits", "inheritance"),
            DiagramEdge("publisher_config", "imprint_config", "inherits", "inheritance"),
            DiagramEdge("imprint_config", "tranche_config", "inherits", "inheritance"),
            DiagramEdge("tranche_config", "book_config", "inherits", "inheritance"),
            DiagramEdge("runtime_resolver", "global_config", "loads", "data_access"),
            DiagramEdge("runtime_resolver", "publisher_config", "loads", "data_access"),
            DiagramEdge("runtime_resolver", "imprint_config", "loads", "data_access"),
            DiagramEdge("runtime_resolver", "tranche_config", "loads", "data_access"),
            DiagramEdge("runtime_resolver", "book_config", "loads", "data_access"),
            DiagramEdge("runtime_resolver", "validation_engine", "validates", "validation"),
            DiagramEdge("context_manager", "runtime_resolver", "provides context", "context"),
            DiagramEdge("runtime_resolver", "field_mapper", "resolved config", "configuration"),
            DiagramEdge("runtime_resolver", "template_engine", "template config", "configuration")
        ]
        
        return {
            "title": "Multi-Level Configuration Hierarchy",
            "description": "Five-level configuration inheritance and resolution system",
            "nodes": [node.__dict__ for node in nodes],
            "edges": [edge.__dict__ for edge in edges],
            "layout_type": "hierarchical"
        }
    
    def generate_production_pipeline_diagram(self) -> Dict[str, Any]:
        """
        Generate a diagram showing the book production pipeline.
        
        Returns:
            Dictionary containing production pipeline diagram data
        """
        nodes = [
            DiagramNode("book_input", "Book Input", "input", "Raw book data and manuscripts"),
            DiagramNode("metadata_processor", "Metadata Processor", "processing", "Metadata extraction and enhancement"),
            DiagramNode("ai_enhancer", "AI Enhancer", "ai_processing", "AI-powered content enhancement"),
            DiagramNode("config_resolver", "Config Resolver", "processing", "Configuration resolution"),
            DiagramNode("template_generator", "Template Generator", "processing", "LaTeX template generation"),
            DiagramNode("latex_compiler", "LaTeX Compiler", "processing", "PDF compilation"),
            DiagramNode("quality_checker", "Quality Checker", "validation", "PDF quality validation"),
            DiagramNode("lsi_generator", "LSI Generator", "processing", "LSI CSV generation"),
            DiagramNode("distribution_formatter", "Distribution Formatter", "processing", "Multi-format output"),
            DiagramNode("file_output", "File Output", "output", "Final production files"),
            DiagramNode("external_submission", "External Submission", "output", "Lightning Source submission")
        ]
        
        edges = [
            DiagramEdge("book_input", "metadata_processor", "raw data", "data_flow"),
            DiagramEdge("metadata_processor", "ai_enhancer", "metadata", "processing"),
            DiagramEdge("ai_enhancer", "config_resolver", "enhanced data", "processing"),
            DiagramEdge("config_resolver", "template_generator", "resolved config", "processing"),
            DiagramEdge("template_generator", "latex_compiler", "LaTeX files", "processing"),
            DiagramEdge("latex_compiler", "quality_checker", "PDF files", "validation"),
            DiagramEdge("quality_checker", "file_output", "validated PDFs", "output", {"condition": "pass"}),
            DiagramEdge("quality_checker", "latex_compiler", "retry", "feedback", {"condition": "fail"}),
            DiagramEdge("config_resolver", "lsi_generator", "distribution config", "processing"),
            DiagramEdge("metadata_processor", "lsi_generator", "book metadata", "data_flow"),
            DiagramEdge("lsi_generator", "distribution_formatter", "LSI data", "processing"),
            DiagramEdge("distribution_formatter", "file_output", "CSV files", "output"),
            DiagramEdge("file_output", "external_submission", "submission files", "external")
        ]
        
        return {
            "title": "Book Production Pipeline",
            "description": "End-to-end automated book production workflow",
            "nodes": [node.__dict__ for node in nodes],
            "edges": [edge.__dict__ for edge in edges],
            "layout_type": "workflow"
        }
    
    def generate_mermaid_diagram(self, diagram_data: Dict[str, Any]) -> str:
        """
        Convert diagram data to Mermaid format.
        
        Args:
            diagram_data: Dictionary containing nodes and edges
            
        Returns:
            Mermaid diagram string
        """
        layout_type = diagram_data.get("layout_type", "TD")
        
        if layout_type == "hierarchical":
            mermaid = ["graph TD"]
        elif layout_type == "layered":
            mermaid = ["graph LR"]
        elif layout_type == "workflow":
            mermaid = ["flowchart TD"]
        else:
            mermaid = ["graph TD"]
        
        # Add title as comment
        mermaid.append(f"    %% {diagram_data.get('title', 'Architecture Diagram')}")
        mermaid.append("")
        
        # Add nodes with styling
        for node in diagram_data["nodes"]:
            node_id = node["id"]
            label = node["label"]
            node_type = node.get("node_type", "default")
            
            # Choose node shape based on type
            if node_type in ["interface", "input", "output"]:
                mermaid.append(f'    {node_id}["{label}"]')
            elif node_type in ["ai", "ai_core", "ai_processing", "ai_application"]:
                mermaid.append(f'    {node_id}{{"{label}"}}')
            elif node_type in ["external", "external_ai", "external_api"]:
                mermaid.append(f'    {node_id}[("{label}")]')
            elif node_type in ["processing", "validation"]:
                mermaid.append(f'    {node_id}["{label}"]')
            else:
                mermaid.append(f'    {node_id}["{label}"]')
        
        mermaid.append("")
        
        # Add edges
        for edge in diagram_data["edges"]:
            source = edge["source"]
            target = edge["target"]
            label = edge.get("label", "")
            edge_type = edge.get("edge_type", "default")
            
            if edge_type == "inheritance":
                mermaid.append(f'    {source} -.->|{label}| {target}')
            elif edge_type == "feedback":
                mermaid.append(f'    {source} -.->|{label}| {target}')
            elif edge_type == "external":
                mermaid.append(f'    {source} ==>|{label}| {target}')
            else:
                mermaid.append(f'    {source} -->|{label}| {target}')
        
        # Add styling classes
        mermaid.extend([
            "",
            "    classDef interface fill:#e3f2fd,stroke:#1976d2,stroke-width:2px",
            "    classDef ai fill:#fff3e0,stroke:#f57c00,stroke-width:2px",
            "    classDef ai_core fill:#fff3e0,stroke:#f57c00,stroke-width:3px",
            "    classDef external fill:#fce4ec,stroke:#c2185b,stroke-width:2px",
            "    classDef processing fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
            "    classDef config_level fill:#e8f5e8,stroke:#388e3c,stroke-width:2px",
            "    classDef system fill:#fff8e1,stroke:#fbc02d,stroke-width:2px"
        ])
        
        # Apply classes to nodes
        for node in diagram_data["nodes"]:
            node_type = node.get("node_type", "default")
            if node_type in ["interface", "input", "output"]:
                mermaid.append(f'    class {node["id"]} interface')
            elif node_type in ["ai", "ai_core", "ai_processing", "ai_application"]:
                mermaid.append(f'    class {node["id"]} ai')
            elif node_type in ["external", "external_ai", "external_api"]:
                mermaid.append(f'    class {node["id"]} external')
            elif node_type in ["processing", "validation"]:
                mermaid.append(f'    class {node["id"]} processing')
            elif node_type == "config_level":
                mermaid.append(f'    class {node["id"]} config_level')
            elif node_type == "system":
                mermaid.append(f'    class {node["id"]} system')
        
        return '\n'.join(mermaid)
    
    def generate_all_diagrams(self) -> Dict[str, Any]:
        """
        Generate all architecture diagrams for the paper.
        
        Returns:
            Dictionary containing all diagram data and Mermaid representations
        """
        diagrams = {
            "system_overview": self.generate_system_overview_diagram(),
            "ai_integration": self.generate_ai_integration_diagram(),
            "configuration_hierarchy": self.generate_configuration_hierarchy_diagram(),
            "production_pipeline": self.generate_production_pipeline_diagram()
        }
        
        # Generate Mermaid representations
        mermaid_diagrams = {}
        for name, diagram_data in diagrams.items():
            mermaid_diagrams[name] = self.generate_mermaid_diagram(diagram_data)
        
        return {
            "diagrams": diagrams,
            "mermaid": mermaid_diagrams,
            "metadata": {
                "total_diagrams": len(diagrams),
                "generation_notes": [
                    "Diagrams focus on xynapse_traces imprint implementation",
                    "AI integration highlighted throughout architecture",
                    "Multi-level configuration system emphasized",
                    "Korean language processing capabilities shown"
                ]
            }
        }


def main():
    """Main function for testing the architecture diagram generator."""
    generator = ArchitectureDiagramGenerator()
    
    # Generate all diagrams
    all_diagrams = generator.generate_all_diagrams()
    
    # Save to output directory
    output_dir = Path("output/arxiv_paper/architecture_diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save diagram data
    with open(output_dir / "architecture_diagrams.json", 'w') as f:
        json.dump(all_diagrams, f, indent=2)
    
    # Save individual Mermaid files
    for name, mermaid_content in all_diagrams["mermaid"].items():
        with open(output_dir / f"{name}.mmd", 'w') as f:
            f.write(mermaid_content)
    
    # Create a combined Mermaid file
    with open(output_dir / "all_diagrams.mmd", 'w') as f:
        for name, mermaid_content in all_diagrams["mermaid"].items():
            f.write(f"# {name.replace('_', ' ').title()}\n\n")
            f.write(mermaid_content)
            f.write("\n\n---\n\n")
    
    print(f"Architecture diagrams saved to {output_dir}")
    print(f"Generated {len(all_diagrams['diagrams'])} diagrams")


if __name__ == "__main__":
    main()