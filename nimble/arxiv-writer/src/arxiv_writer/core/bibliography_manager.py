"""
Bibliography Management System for ArXiv Paper Generation

This module provides comprehensive tools for managing academic citations and bibliography
for the xynapse_traces imprint documentation paper, including BibTeX generation,
citation validation, and arXiv-compliant formatting.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class CitationValidationResult:
    """Result of citation validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ArxivCitationValidator:
    """Validates citations for arXiv submission standards."""
    
    REQUIRED_FIELDS = {
        "article": ["title", "author", "year", "journal"],
        "inproceedings": ["title", "author", "year", "booktitle"],
        "book": ["title", "author", "year", "publisher"],
        "techreport": ["title", "author", "year", "institution"],
        "manual": ["title", "organization", "year"],
        "misc": ["title", "year"]
    }
    
    OPTIONAL_FIELDS = {
        "article": ["volume", "number", "pages", "doi", "url"],
        "inproceedings": ["pages", "publisher", "address", "doi", "url"],
        "book": ["address", "isbn", "doi", "url"],
        "techreport": ["number", "address", "url"],
        "manual": ["address", "url"],
        "misc": ["author", "howpublished", "url"]
    }
    
    def validate_citation(self, citation_data: Dict[str, Any]) -> CitationValidationResult:
        """
        Validate a citation for arXiv standards.
        
        Args:
            citation_data: Citation data dictionary
            
        Returns:
            CitationValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        # Check required type field
        if "type" not in citation_data:
            errors.append("Missing required field: type")
            return CitationValidationResult(False, errors, warnings)
        
        entry_type = citation_data["type"]
        
        # Validate entry type
        if entry_type not in self.REQUIRED_FIELDS:
            errors.append(f"Unsupported entry type: {entry_type}")
            return CitationValidationResult(False, errors, warnings)
        
        # Check required fields
        required_fields = self.REQUIRED_FIELDS[entry_type]
        for field in required_fields:
            if field not in citation_data or not citation_data[field]:
                errors.append(f"Missing required field for {entry_type}: {field}")
        
        # Validate specific field formats
        self._validate_year(citation_data, errors, warnings)
        self._validate_author(citation_data, errors, warnings)
        self._validate_title(citation_data, errors, warnings)
        self._validate_url(citation_data, errors, warnings)
        self._validate_doi(citation_data, errors, warnings)
        
        # Check for recommended fields
        self._check_recommended_fields(citation_data, entry_type, warnings)
        
        is_valid = len(errors) == 0
        return CitationValidationResult(is_valid, errors, warnings)
    
    def _validate_year(self, citation: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
        """Validate year field."""
        if "year" in citation:
            year_str = str(citation["year"])
            if not re.match(r'^\d{4}$', year_str):
                errors.append(f"Invalid year format: {year_str}. Expected 4-digit year.")
            else:
                year = int(year_str)
                current_year = datetime.now().year
                if year < 1900 or year > current_year + 1:
                    warnings.append(f"Unusual year: {year}. Please verify.")
    
    def _validate_author(self, citation: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
        """Validate author field."""
        if "author" in citation:
            author = citation["author"]
            if not isinstance(author, str) or len(author.strip()) == 0:
                errors.append("Author field must be a non-empty string")
            elif " and " not in author and "," not in author and len(author.split()) < 2:
                warnings.append("Author field may need proper formatting (Last, First or Author1 and Author2)")
    
    def _validate_title(self, citation: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
        """Validate title field."""
        if "title" in citation:
            title = citation["title"]
            if not isinstance(title, str) or len(title.strip()) == 0:
                errors.append("Title field must be a non-empty string")
            elif len(title) < 5:
                warnings.append("Title seems unusually short")
    
    def _validate_url(self, citation: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
        """Validate URL field."""
        if "url" in citation:
            url = citation["url"]
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"Invalid URL format: {url}")
            except Exception:
                errors.append(f"Invalid URL format: {url}")
    
    def _validate_doi(self, citation: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
        """Validate DOI field."""
        if "doi" in citation:
            doi = citation["doi"]
            if not re.match(r'^10\.\d+/.+', doi):
                errors.append(f"Invalid DOI format: {doi}. Expected format: 10.xxxx/yyyy")
    
    def _check_recommended_fields(self, citation: Dict[str, Any], entry_type: str, warnings: List[str]) -> None:
        """Check for recommended but optional fields."""
        if entry_type == "article":
            if "volume" not in citation:
                warnings.append("Consider adding volume for journal article")
            if "pages" not in citation:
                warnings.append("Consider adding page numbers for journal article")
        elif entry_type == "inproceedings":
            if "pages" not in citation:
                warnings.append("Consider adding page numbers for conference paper")
            if "publisher" not in citation:
                warnings.append("Consider adding publisher for conference proceedings")


class BibliographyManager:
    """Manages academic citations and bibliography for the ArXiv paper."""
    
    def __init__(self, base_path: str = "."):
        """
        Initialize the bibliography manager.
        
        Args:
            base_path: Base path to the project directory
        """
        self.base_path = Path(base_path)
        self.output_path = self.base_path / "output" / "arxiv_paper" / "bibliography"
        self.citations_file = self.output_path / "citations.json"
        self.bibtex_file = self.output_path / "references.bib"
        self.validation_report_file = self.output_path / "validation_report.json"
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize validator and citations database
        self.validator = ArxivCitationValidator()
        self.citations = self._load_citations()
    
    def _load_citations(self) -> Dict[str, Any]:
        """Load existing citations from file or create new database."""
        if self.citations_file.exists():
            try:
                with open(self.citations_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing citations: {e}")
        
        return {
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "citations": {}
        }
    
    def add_citation(self, key: str, citation_data: Dict[str, Any], validate: bool = True) -> CitationValidationResult:
        """
        Add a citation to the bibliography with optional validation.
        
        Args:
            key: Unique identifier for the citation
            citation_data: Dictionary containing citation information
            validate: Whether to validate the citation before adding
            
        Returns:
            CitationValidationResult indicating validation status
        """
        validation_result = CitationValidationResult(True, [], [])
        
        if validate:
            validation_result = self.validator.validate_citation(citation_data)
            if not validation_result.is_valid:
                logger.error(f"Citation validation failed for {key}: {validation_result.errors}")
                return validation_result
            
            if validation_result.warnings:
                logger.warning(f"Citation warnings for {key}: {validation_result.warnings}")
        
        self.citations["citations"][key] = {
            **citation_data,
            "added_timestamp": datetime.now().isoformat(),
            "validation_status": {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "validated_at": datetime.now().isoformat()
            }
        }
        
        self.citations["metadata"]["last_updated"] = datetime.now().isoformat()
        self._save_citations()
        logger.info(f"Added citation: {key}")
        
        return validation_result
    
    def generate_ai_publishing_citations(self) -> Dict[str, CitationValidationResult]:
        """
        Generate comprehensive citations for AI and publishing research.
        
        Returns:
            Dictionary mapping citation keys to validation results
        """
        validation_results = {}
        
        # Core AI and LLM citations
        ai_core_citations = [
            {
                "key": "brown2020language",
                "title": "Language Models are Few-Shot Learners",
                "author": "Brown, Tom B. and Mann, Benjamin and Ryder, Nick and Subbiah, Melanie and Kaplan, Jared and Dhariwal, Prafulla and Neelakantan, Arvind and Shyam, Pranav and Saxena, Girish and Bosma, Amanda and others",
                "year": "2020",
                "type": "article",
                "journal": "Advances in Neural Information Processing Systems",
                "volume": "33",
                "pages": "1877--1901",
                "url": "https://arxiv.org/abs/2005.14165"
            },
            {
                "key": "vaswani2017attention",
                "title": "Attention is All You Need",
                "author": "Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, Lukasz and Polosukhin, Illia",
                "year": "2017",
                "type": "article",
                "journal": "Advances in Neural Information Processing Systems",
                "volume": "30",
                "url": "https://arxiv.org/abs/1706.03762"
            },
            {
                "key": "radford2019language",
                "title": "Language Models are Unsupervised Multitask Learners",
                "author": "Radford, Alec and Wu, Jeffrey and Child, Rewon and Luan, David and Amodei, Dario and Sutskever, Ilya",
                "year": "2019",
                "type": "techreport",
                "institution": "OpenAI",
                "url": "https://d4mucfpksywv.cloudfront.net/better-language-models/language_models_are_unsupervised_multitask_learners.pdf"
            },
            {
                "key": "devlin2018bert",
                "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                "author": "Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina",
                "year": "2018",
                "type": "article",
                "journal": "arXiv preprint arXiv:1810.04805",
                "url": "https://arxiv.org/abs/1810.04805"
            },
            {
                "key": "touvron2023llama",
                "title": "Llama 2: Open Foundation and Fine-Tuned Chat Models",
                "author": "Touvron, Hugo and Martin, Louis and Stone, Kevin and Albert, Peter and Almahairi, Amjad and Babaei, Yasmine and Bashlykov, Nikolay and Batra, Soumya and Bhargava, Prajjwal and Bhosale, Shruti and others",
                "year": "2023",
                "type": "article",
                "journal": "arXiv preprint arXiv:2307.09288",
                "url": "https://arxiv.org/abs/2307.09288"
            }
        ]
        
        # AI in content creation and publishing
        ai_publishing_citations = [
            {
                "key": "dale2021gpt3",
                "title": "GPT-3: What's it good for?",
                "author": "Dale, Robert",
                "year": "2021",
                "type": "article",
                "journal": "Natural Language Engineering",
                "volume": "27",
                "number": "1",
                "pages": "113--118",
                "doi": "10.1017/S1351324920000601"
            },
            {
                "key": "floridi2020gpt3",
                "title": "GPT-3: Its Nature, Scope, Limits, and Consequences",
                "author": "Floridi, Luciano and Chiriatti, Massimo",
                "year": "2020",
                "type": "article",
                "journal": "Minds and Machines",
                "volume": "30",
                "number": "4",
                "pages": "681--694",
                "doi": "10.1007/s11023-020-09548-1"
            },
            {
                "key": "eloundou2023gpts",
                "title": "GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models",
                "author": "Eloundou, Tyna and Manning, Sam and Mishkin, Pamela and Rock, Daniel",
                "year": "2023",
                "type": "article",
                "journal": "arXiv preprint arXiv:2303.10130",
                "url": "https://arxiv.org/abs/2303.10130"
            },
            {
                "key": "bubeck2023sparks",
                "title": "Sparks of Artificial General Intelligence: Early experiments with GPT-4",
                "author": "Bubeck, Sébastien and Chandrasekaran, Varun and Eldan, Ronen and Gehrke, Johannes and Horvitz, Eric and Kamar, Ece and Lee, Peter and Lee, Yin Tat and Li, Yuanzhi and Lundberg, Scott and others",
                "year": "2023",
                "type": "article",
                "journal": "arXiv preprint arXiv:2303.12712",
                "url": "https://arxiv.org/abs/2303.12712"
            }
        ]
        
        # Digital humanities and computational creativity
        digital_humanities_citations = [
            {
                "key": "moretti2013distant",
                "title": "Distant Reading",
                "author": "Moretti, Franco",
                "year": "2013",
                "type": "book",
                "publisher": "Verso Books",
                "address": "London"
            },
            {
                "key": "ramsay2011reading",
                "title": "Reading Machines: Toward an Algorithmic Criticism",
                "author": "Ramsay, Stephen",
                "year": "2011",
                "type": "book",
                "publisher": "University of Illinois Press",
                "address": "Urbana"
            },
            {
                "key": "underwood2019distant",
                "title": "Distant Horizons: Digital Evidence and Literary Change",
                "author": "Underwood, Ted",
                "year": "2019",
                "type": "book",
                "publisher": "University of Chicago Press",
                "address": "Chicago"
            }
        ]
        
        # Publishing industry and technology
        publishing_tech_citations = [
            {
                "key": "thompson2021merchants",
                "title": "Merchants of Culture: The Publishing Business in the Twenty-First Century",
                "author": "Thompson, John B.",
                "year": "2021",
                "type": "book",
                "publisher": "Polity Press",
                "address": "Cambridge",
                "edition": "3rd"
            },
            {
                "key": "striphas2009late",
                "title": "The Late Age of Print: Everyday Book Culture from Consumerism to Control",
                "author": "Striphas, Ted",
                "year": "2009",
                "type": "book",
                "publisher": "Columbia University Press",
                "address": "New York"
            },
            {
                "key": "ingram2023pod",
                "title": "Print-on-Demand Technology and Market Trends 2023",
                "author": "Ingram Content Group",
                "year": "2023",
                "type": "techreport",
                "institution": "Ingram Content Group",
                "url": "https://www.ingramcontent.com/publishers/print/pod-trends-2023"
            },
            {
                "key": "bowker2024publishing",
                "title": "Publishing Industry Statistics and Trends",
                "author": "Bowker",
                "year": "2024",
                "type": "misc",
                "howpublished": "Industry Report",
                "url": "https://www.bowker.com/news-and-insights/"
            }
        ]
        
        # Technical standards and tools
        technical_citations = [
            {
                "key": "latex2023memoir",
                "title": "The Memoir Class for Configurable Typesetting",
                "author": "Wilson, Peter and Madsen, Lars",
                "year": "2023",
                "type": "manual",
                "organization": "LaTeX Project",
                "url": "https://ctan.org/pkg/memoir"
            },
            {
                "key": "knuth1984texbook",
                "title": "The TeXbook",
                "author": "Knuth, Donald E.",
                "year": "1984",
                "type": "book",
                "publisher": "Addison-Wesley",
                "address": "Reading, MA"
            },
            {
                "key": "mittelbach2004latex",
                "title": "The LaTeX Companion",
                "author": "Mittelbach, Frank and Goossens, Michel and Braams, Johannes and Carlisle, David and Rowley, Chris",
                "year": "2004",
                "type": "book",
                "publisher": "Addison-Wesley",
                "address": "Boston",
                "edition": "2nd"
            }
        ]
        
        # Multilingual and internationalization
        i18n_citations = [
            {
                "key": "unicode2022standard",
                "title": "The Unicode Standard, Version 15.0",
                "author": "Unicode Consortium",
                "year": "2022",
                "type": "manual",
                "organization": "Unicode Consortium",
                "url": "https://www.unicode.org/versions/Unicode15.0.0/"
            },
            {
                "key": "park2019korean",
                "title": "Korean Typography in Digital Publishing",
                "author": "Park, Min-jun and Lee, Hye-jin",
                "year": "2019",
                "type": "article",
                "journal": "International Journal of Typography",
                "volume": "12",
                "number": "3",
                "pages": "45--62"
            }
        ]
        
        # Historical context citations
        historical_citations = [
            {
                "key": "eisenstein1979printing",
                "title": "The Printing Press as an Agent of Change",
                "author": "Eisenstein, Elizabeth L.",
                "year": "1979",
                "type": "book",
                "publisher": "Cambridge University Press",
                "address": "Cambridge"
            },
            {
                "key": "johns1998nature",
                "title": "The Nature of the Book: Print and Knowledge in the Making",
                "author": "Johns, Adrian",
                "year": "1998",
                "type": "book",
                "publisher": "University of Chicago Press",
                "address": "Chicago"
            }
        ]
        
        # Combine all citation groups
        all_citations = (ai_core_citations + ai_publishing_citations + 
                        digital_humanities_citations + publishing_tech_citations + 
                        technical_citations + i18n_citations + historical_citations)
        
        # Add all citations with validation
        for citation in all_citations:
            key = citation.pop("key")
            validation_result = self.add_citation(key, citation, validate=True)
            validation_results[key] = validation_result
        
        logger.info(f"Generated {len(all_citations)} citations for AI and publishing research")
        return validation_results
    
    def generate_bibtex(self) -> str:
        """
        Generate BibTeX format bibliography.
        
        Returns:
            BibTeX formatted string
        """
        bibtex_entries = []
        
        for key, citation in self.citations["citations"].items():
            entry_type = citation.get("type", "article")
            
            # Start BibTeX entry
            bibtex_entry = f"@{entry_type}{{{key},\n"
            
            # Add fields
            field_mapping = {
                "title": "title",
                "author": "author", 
                "year": "year",
                "journal": "journal",
                "booktitle": "booktitle",
                "volume": "volume",
                "number": "number",
                "pages": "pages",
                "publisher": "publisher",
                "institution": "institution",
                "organization": "organization",
                "url": "url",
                "doi": "doi"
            }
            
            for field, bibtex_field in field_mapping.items():
                if field in citation:
                    value = citation[field]
                    bibtex_entry += f"  {bibtex_field} = {{{value}}},\n"
            
            # Remove trailing comma and close entry
            bibtex_entry = bibtex_entry.rstrip(",\n") + "\n}\n\n"
            bibtex_entries.append(bibtex_entry)
        
        bibtex_content = "".join(bibtex_entries)
        
        # Save to file
        with open(self.bibtex_file, 'w') as f:
            f.write(bibtex_content)
        
        logger.info(f"Generated BibTeX with {len(bibtex_entries)} entries")
        return bibtex_content
    
    def format_citation(self, key: str, style: str = "apa") -> str:
        """
        Format a citation in the specified style.
        
        Args:
            key: Citation key
            style: Citation style (apa, mla, chicago)
            
        Returns:
            Formatted citation string
        """
        if key not in self.citations["citations"]:
            return f"[Citation not found: {key}]"
        
        citation = self.citations["citations"][key]
        
        if style.lower() == "apa":
            return self._format_apa(citation)
        elif style.lower() == "mla":
            return self._format_mla(citation)
        elif style.lower() == "chicago":
            return self._format_chicago(citation)
        else:
            return f"[Unsupported citation style: {style}]"
    
    def _format_apa(self, citation: Dict[str, Any]) -> str:
        """Format citation in APA style."""
        author = citation.get("author", "Unknown Author")
        year = citation.get("year", "n.d.")
        title = citation.get("title", "Untitled")
        
        # Basic APA format
        formatted = f"{author} ({year}). {title}."
        
        if "journal" in citation:
            journal = citation["journal"]
            volume = citation.get("volume", "")
            number = citation.get("number", "")
            pages = citation.get("pages", "")
            
            formatted += f" {journal}"
            if volume:
                formatted += f", {volume}"
            if number:
                formatted += f"({number})"
            if pages:
                formatted += f", {pages}"
            formatted += "."
        
        return formatted
    
    def _format_mla(self, citation: Dict[str, Any]) -> str:
        """Format citation in MLA style."""
        author = citation.get("author", "Unknown Author")
        title = citation.get("title", "Untitled")
        
        # Basic MLA format
        formatted = f"{author}. \"{title}.\""
        
        if "journal" in citation:
            journal = citation["journal"]
            volume = citation.get("volume", "")
            number = citation.get("number", "")
            year = citation.get("year", "")
            pages = citation.get("pages", "")
            
            formatted += f" {journal}"
            if volume:
                formatted += f", vol. {volume}"
            if number:
                formatted += f", no. {number}"
            if year:
                formatted += f", {year}"
            if pages:
                formatted += f", pp. {pages}"
            formatted += "."
        
        return formatted
    
    def _format_chicago(self, citation: Dict[str, Any]) -> str:
        """Format citation in Chicago style."""
        author = citation.get("author", "Unknown Author")
        title = citation.get("title", "Untitled")
        
        # Basic Chicago format
        formatted = f"{author}. \"{title}.\""
        
        if "journal" in citation:
            journal = citation["journal"]
            volume = citation.get("volume", "")
            number = citation.get("number", "")
            year = citation.get("year", "")
            pages = citation.get("pages", "")
            
            formatted += f" {journal} {volume}"
            if number:
                formatted += f", no. {number}"
            if year:
                formatted += f" ({year})"
            if pages:
                formatted += f": {pages}"
            formatted += "."
        
        return formatted
    
    def _save_citations(self) -> None:
        """Save citations database to file."""
        with open(self.citations_file, 'w') as f:
            json.dump(self.citations, f, indent=2)
        logger.debug(f"Saved citations to {self.citations_file}")
    
    def get_citation_count(self) -> int:
        """Get total number of citations."""
        return len(self.citations["citations"])
    
    def list_citations(self) -> List[str]:
        """Get list of all citation keys."""
        return list(self.citations["citations"].keys())
    
    def validate_all_citations(self) -> Dict[str, CitationValidationResult]:
        """
        Validate all citations in the database.
        
        Returns:
            Dictionary mapping citation keys to validation results
        """
        validation_results = {}
        
        for key, citation_data in self.citations["citations"].items():
            # Remove metadata fields for validation
            clean_citation = {k: v for k, v in citation_data.items() 
                            if k not in ["added_timestamp", "validation_status"]}
            validation_result = self.validator.validate_citation(clean_citation)
            validation_results[key] = validation_result
            
            # Update stored validation status
            self.citations["citations"][key]["validation_status"] = {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "validated_at": datetime.now().isoformat()
            }
        
        self._save_citations()
        return validation_results
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Returns:
            Dictionary containing validation statistics and details
        """
        validation_results = self.validate_all_citations()
        
        total_citations = len(validation_results)
        valid_citations = sum(1 for result in validation_results.values() if result.is_valid)
        invalid_citations = total_citations - valid_citations
        
        all_errors = []
        all_warnings = []
        
        for key, result in validation_results.items():
            for error in result.errors:
                all_errors.append({"citation": key, "error": error})
            for warning in result.warnings:
                all_warnings.append({"citation": key, "warning": warning})
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_citations": total_citations,
                "valid_citations": valid_citations,
                "invalid_citations": invalid_citations,
                "validation_rate": valid_citations / total_citations if total_citations > 0 else 0,
                "total_errors": len(all_errors),
                "total_warnings": len(all_warnings)
            },
            "errors": all_errors,
            "warnings": all_warnings,
            "citation_details": {
                key: {
                    "is_valid": result.is_valid,
                    "error_count": len(result.errors),
                    "warning_count": len(result.warnings)
                }
                for key, result in validation_results.items()
            }
        }
        
        # Save report to file
        with open(self.validation_report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated validation report: {valid_citations}/{total_citations} citations valid")
        return report
    
    def generate_arxiv_compliant_bibtex(self) -> str:
        """
        Generate arXiv-compliant BibTeX format bibliography.
        
        Returns:
            BibTeX formatted string optimized for arXiv submission
        """
        bibtex_entries = []
        
        # Sort citations by key for consistent output
        sorted_citations = sorted(self.citations["citations"].items())
        
        for key, citation in sorted_citations:
            entry_type = citation.get("type", "article")
            
            # Start BibTeX entry
            bibtex_entry = f"@{entry_type}{{{key},\n"
            
            # Field ordering for arXiv compliance
            field_order = [
                "title", "author", "year", "journal", "booktitle", 
                "volume", "number", "pages", "publisher", "address",
                "institution", "organization", "edition", "howpublished",
                "doi", "url"
            ]
            
            # Add fields in proper order
            for field in field_order:
                if field in citation and citation[field]:
                    value = str(citation[field])
                    # Escape special characters for LaTeX
                    value = self._escape_latex_chars(value)
                    bibtex_entry += f"  {field} = {{{value}}},\n"
            
            # Remove trailing comma and close entry
            bibtex_entry = bibtex_entry.rstrip(",\n") + "\n}\n\n"
            bibtex_entries.append(bibtex_entry)
        
        bibtex_content = "".join(bibtex_entries)
        
        # Add header comment
        header = f"""% Bibliography for ArXiv Paper: AI-Assisted Publishing Imprint Creation
% Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
% Total citations: {len(bibtex_entries)}

"""
        
        full_content = header + bibtex_content
        
        # Save to file
        with open(self.bibtex_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Generated arXiv-compliant BibTeX with {len(bibtex_entries)} entries")
        return full_content
    
    def _escape_latex_chars(self, text: str) -> str:
        """
        Escape special LaTeX characters in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with escaped LaTeX special characters
        """
        # Common LaTeX special characters
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\^{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\~{}',
            '\\': r'\textbackslash{}'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def get_citations_by_type(self) -> Dict[str, List[str]]:
        """
        Get citations grouped by type.
        
        Returns:
            Dictionary mapping citation types to lists of citation keys
        """
        citations_by_type = {}
        
        for key, citation in self.citations["citations"].items():
            citation_type = citation.get("type", "unknown")
            if citation_type not in citations_by_type:
                citations_by_type[citation_type] = []
            citations_by_type[citation_type].append(key)
        
        return citations_by_type
    
    def export_citations_csv(self) -> str:
        """
        Export citations to CSV format for external tools.
        
        Returns:
            Path to the generated CSV file
        """
        import csv
        
        csv_file = self.output_path / "citations_export.csv"
        
        # Define CSV columns
        columns = [
            "key", "type", "title", "author", "year", "journal", "booktitle",
            "volume", "number", "pages", "publisher", "institution", "url", "doi"
        ]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for key, citation in self.citations["citations"].items():
                row = {"key": key}
                for col in columns[1:]:  # Skip 'key' column
                    row[col] = citation.get(col, "")
                writer.writerow(row)
        
        logger.info(f"Exported citations to CSV: {csv_file}")
        return str(csv_file)


def main():
    """Main function for standalone execution."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("ArXiv Paper Bibliography Management System")
    print("=" * 50)
    
    bib_manager = BibliographyManager()
    
    # Generate comprehensive citations
    print("Generating AI and publishing research citations...")
    validation_results = bib_manager.generate_ai_publishing_citations()
    
    # Generate validation report
    print("Validating all citations...")
    validation_report = bib_manager.generate_validation_report()
    
    # Generate arXiv-compliant BibTeX
    print("Generating arXiv-compliant BibTeX...")
    bibtex_content = bib_manager.generate_arxiv_compliant_bibtex()
    
    # Export to CSV
    print("Exporting citations to CSV...")
    csv_file = bib_manager.export_citations_csv()
    
    # Print summary
    print("\nBibliography Management Summary:")
    print(f"Total citations: {bib_manager.get_citation_count()}")
    print(f"Valid citations: {validation_report['summary']['valid_citations']}")
    print(f"Invalid citations: {validation_report['summary']['invalid_citations']}")
    print(f"Validation rate: {validation_report['summary']['validation_rate']:.1%}")
    print(f"Total errors: {validation_report['summary']['total_errors']}")
    print(f"Total warnings: {validation_report['summary']['total_warnings']}")
    
    print(f"\nGenerated files:")
    print(f"- BibTeX: {bib_manager.bibtex_file}")
    print(f"- Citations JSON: {bib_manager.citations_file}")
    print(f"- Validation Report: {bib_manager.validation_report_file}")
    print(f"- CSV Export: {csv_file}")
    
    # Show citations by type
    citations_by_type = bib_manager.get_citations_by_type()
    print(f"\nCitations by type:")
    for citation_type, keys in citations_by_type.items():
        print(f"- {citation_type}: {len(keys)} citations")


if __name__ == "__main__":
    main()