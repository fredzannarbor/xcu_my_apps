"""
Citation and Cross-Reference Management System

This module provides utilities for managing citations, cross-references,
and bibliography formatting for academic papers.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a bibliographic citation."""
    key: str
    title: str
    authors: List[str]
    year: int
    venue: str
    citation_type: str  # article, book, inproceedings, etc.
    doi: Optional[str] = None
    url: Optional[str] = None
    pages: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    arxiv_id: Optional[str] = None
    note: Optional[str] = None


@dataclass
class CrossReference:
    """Represents a cross-reference within the document."""
    ref_type: str  # section, figure, table, equation, listing
    label: str
    title: str
    section: str
    page_number: Optional[int] = None


class BibTeXGenerator:
    """Generates BibTeX entries from citation data."""
    
    def __init__(self):
        self.entry_templates = {
            'article': self._article_template,
            'book': self._book_template,
            'inproceedings': self._inproceedings_template,
            'incollection': self._incollection_template,
            'techreport': self._techreport_template,
            'misc': self._misc_template,
            'online': self._online_template
        }
    
    def generate_bibtex_entry(self, citation: Citation) -> str:
        """Generate BibTeX entry for a citation."""
        template_func = self.entry_templates.get(citation.citation_type, self._misc_template)
        return template_func(citation)
    
    def _article_template(self, citation: Citation) -> str:
        """Generate article BibTeX entry."""
        authors_str = ' and '.join(citation.authors)
        
        entry = f"""@article{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    journal = {{{citation.venue}}},
    year = {{{citation.year}}}"""
        
        if citation.volume:
            entry += f",\n    volume = {{{citation.volume}}}"
        if citation.number:
            entry += f",\n    number = {{{citation.number}}}"
        if citation.pages:
            entry += f",\n    pages = {{{citation.pages}}}"
        if citation.doi:
            entry += f",\n    doi = {{{citation.doi}}}"
        if citation.url:
            entry += f",\n    url = {{{citation.url}}}"
        if citation.note:
            entry += f",\n    note = {{{citation.note}}}"
        
        entry += "\n}\n"
        return entry
    
    def _book_template(self, citation: Citation) -> str:
        """Generate book BibTeX entry."""
        authors_str = ' and '.join(citation.authors)
        
        entry = f"""@book{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    publisher = {{{citation.publisher or citation.venue}}},
    year = {{{citation.year}}}"""
        
        if citation.isbn:
            entry += f",\n    isbn = {{{citation.isbn}}}"
        if citation.url:
            entry += f",\n    url = {{{citation.url}}}"
        if citation.note:
            entry += f",\n    note = {{{citation.note}}}"
        
        entry += "\n}\n"
        return entry
    
    def _inproceedings_template(self, citation: Citation) -> str:
        """Generate conference proceedings BibTeX entry."""
        authors_str = ' and '.join(citation.authors)
        
        entry = f"""@inproceedings{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    booktitle = {{{citation.venue}}},
    year = {{{citation.year}}}"""
        
        if citation.pages:
            entry += f",\n    pages = {{{citation.pages}}}"
        if citation.publisher:
            entry += f",\n    publisher = {{{citation.publisher}}}"
        if citation.doi:
            entry += f",\n    doi = {{{citation.doi}}}"
        if citation.url:
            entry += f",\n    url = {{{citation.url}}}"
        
        entry += "\n}\n"
        return entry
    
    def _incollection_template(self, citation: Citation) -> str:
        """Generate book chapter BibTeX entry."""
        authors_str = ' and '.join(citation.authors)
        
        entry = f"""@incollection{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    booktitle = {{{citation.venue}}},
    publisher = {{{citation.publisher}}},
    year = {{{citation.year}}}"""
        
        if citation.pages:
            entry += f",\n    pages = {{{citation.pages}}}"
        if citation.isbn:
            entry += f",\n    isbn = {{{citation.isbn}}}"
        
        entry += "\n}\n"
        return entry
    
    def _techreport_template(self, citation: Citation) -> str:
        """Generate technical report BibTeX entry."""
        authors_str = ' and '.join(citation.authors)
        
        entry = f"""@techreport{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    institution = {{{citation.venue}}},
    year = {{{citation.year}}}"""
        
        if citation.number:
            entry += f",\n    number = {{{citation.number}}}"
        if citation.url:
            entry += f",\n    url = {{{citation.url}}}"
        
        entry += "\n}\n"
        return entry
    
    def _online_template(self, citation: Citation) -> str:
        """Generate online resource BibTeX entry."""
        authors_str = ' and '.join(citation.authors) if citation.authors else "Anonymous"
        
        entry = f"""@online{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    url = {{{citation.url}}},
    year = {{{citation.year}}}"""
        
        if citation.note:
            entry += f",\n    note = {{{citation.note}}}"
        
        entry += "\n}\n"
        return entry
    
    def _misc_template(self, citation: Citation) -> str:
        """Generate miscellaneous BibTeX entry."""
        authors_str = ' and '.join(citation.authors)
        
        entry = f"""@misc{{{citation.key},
    title = {{{citation.title}}},
    author = {{{authors_str}}},
    year = {{{citation.year}}}"""
        
        if citation.venue:
            entry += f",\n    howpublished = {{{citation.venue}}}"
        if citation.url:
            entry += f",\n    url = {{{citation.url}}}"
        if citation.note:
            entry += f",\n    note = {{{citation.note}}}"
        if citation.arxiv_id:
            entry += f",\n    eprint = {{{citation.arxiv_id}}}"
            entry += f",\n    archivePrefix = {{arXiv}}"
        
        entry += "\n}\n"
        return entry


class CrossReferenceManager:
    """Manages cross-references within the document."""
    
    def __init__(self):
        self.references: Dict[str, CrossReference] = {}
        self.reference_patterns = {
            'section': r'\\section\{([^}]+)\}\\label\{([^}]+)\}',
            'subsection': r'\\subsection\{([^}]+)\}\\label\{([^}]+)\}',
            'figure': r'\\caption\{([^}]+)\}\\label\{([^}]+)\}',
            'table': r'\\caption\{([^}]+)\}\\label\{([^}]+)\}',
            'equation': r'\\label\{([^}]+)\}',
            'listing': r'\\caption\{([^}]+)\}\\label\{([^}]+)\}'
        }
    
    def extract_references_from_latex(self, latex_content: str, section_name: str) -> List[CrossReference]:
        """Extract cross-references from LaTeX content."""
        references = []
        
        for ref_type, pattern in self.reference_patterns.items():
            matches = re.finditer(pattern, latex_content)
            
            for match in matches:
                if ref_type in ['section', 'subsection']:
                    title = match.group(1)
                    label = match.group(2)
                else:
                    if len(match.groups()) >= 2:
                        title = match.group(1)
                        label = match.group(2)
                    else:
                        title = f"{ref_type.title()} {match.group(1)}"
                        label = match.group(1)
                
                ref = CrossReference(
                    ref_type=ref_type,
                    label=label,
                    title=title,
                    section=section_name
                )
                
                references.append(ref)
                self.references[label] = ref
        
        return references
    
    def validate_references(self, latex_content: str) -> Dict[str, List[str]]:
        """Validate that all referenced labels exist."""
        # Find all \ref{}, \autoref{}, \pageref{} commands
        ref_commands = re.findall(r'\\(?:ref|autoref|pageref)\{([^}]+)\}', latex_content)
        
        validation_result = {
            'valid_references': [],
            'invalid_references': [],
            'unused_labels': []
        }
        
        # Check if referenced labels exist
        for ref_label in ref_commands:
            if ref_label in self.references:
                validation_result['valid_references'].append(ref_label)
            else:
                validation_result['invalid_references'].append(ref_label)
        
        # Find unused labels
        referenced_labels = set(ref_commands)
        all_labels = set(self.references.keys())
        unused_labels = all_labels - referenced_labels
        validation_result['unused_labels'] = list(unused_labels)
        
        return validation_result
    
    def generate_reference_summary(self) -> Dict[str, Any]:
        """Generate summary of all references in the document."""
        summary = {
            'total_references': len(self.references),
            'by_type': {},
            'by_section': {},
            'references': []
        }
        
        for ref in self.references.values():
            # Count by type
            if ref.ref_type not in summary['by_type']:
                summary['by_type'][ref.ref_type] = 0
            summary['by_type'][ref.ref_type] += 1
            
            # Count by section
            if ref.section not in summary['by_section']:
                summary['by_section'][ref.section] = 0
            summary['by_section'][ref.section] += 1
            
            # Add to references list
            summary['references'].append(asdict(ref))
        
        return summary


class CitationManager:
    """Main citation and reference management system."""
    
    def __init__(self, bibliography_file: Optional[str] = None):
        self.citations: Dict[str, Citation] = {}
        self.bibtex_generator = BibTeXGenerator()
        self.cross_ref_manager = CrossReferenceManager()
        
        if bibliography_file:
            self.load_bibliography(bibliography_file)
    
    def load_bibliography(self, bibliography_file: str):
        """Load bibliography from JSON file."""
        bib_path = Path(bibliography_file)
        
        if not bib_path.exists():
            logger.warning(f"Bibliography file not found: {bib_path}")
            return
        
        try:
            with open(bib_path, 'r') as f:
                bib_data = json.load(f)
            
            if isinstance(bib_data, list):
                # List of citations
                for citation_data in bib_data:
                    citation = Citation(**citation_data)
                    self.citations[citation.key] = citation
            elif isinstance(bib_data, dict):
                # Dictionary of citations
                for key, citation_data in bib_data.items():
                    citation_data['key'] = key
                    citation = Citation(**citation_data)
                    self.citations[key] = citation
            
            logger.info(f"Loaded {len(self.citations)} citations from {bib_path}")
            
        except Exception as e:
            logger.error(f"Error loading bibliography: {e}")
    
    def add_citation(self, citation: Citation):
        """Add a citation to the bibliography."""
        self.citations[citation.key] = citation
    
    def get_citation(self, key: str) -> Optional[Citation]:
        """Get a citation by key."""
        return self.citations.get(key)
    
    def generate_bibtex_file(self, output_file: str):
        """Generate complete BibTeX file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("% Bibliography generated by Codexes-Factory Citation Manager\n")
            f.write(f"% Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Sort citations by key for consistency
            sorted_citations = sorted(self.citations.values(), key=lambda c: c.key)
            
            for citation in sorted_citations:
                bibtex_entry = self.bibtex_generator.generate_bibtex_entry(citation)
                f.write(bibtex_entry)
                f.write("\n")
        
        logger.info(f"Generated BibTeX file: {output_path}")
    
    def validate_citations_in_text(self, latex_content: str) -> Dict[str, Any]:
        """Validate citations in LaTeX text."""
        # Find all \cite{}, \citep{}, \citet{} commands
        cite_pattern = r'\\cite[pt]?\{([^}]+)\}'
        cite_matches = re.findall(cite_pattern, latex_content)
        
        # Parse multiple citations in single command
        cited_keys = []
        for match in cite_matches:
            keys = [key.strip() for key in match.split(',')]
            cited_keys.extend(keys)
        
        validation_result = {
            'total_citations_used': len(cited_keys),
            'unique_citations_used': len(set(cited_keys)),
            'valid_citations': [],
            'invalid_citations': [],
            'unused_citations': []
        }
        
        # Check if cited keys exist in bibliography
        for key in set(cited_keys):
            if key in self.citations:
                validation_result['valid_citations'].append(key)
            else:
                validation_result['invalid_citations'].append(key)
        
        # Find unused citations
        used_keys = set(cited_keys)
        all_keys = set(self.citations.keys())
        unused_keys = all_keys - used_keys
        validation_result['unused_citations'] = list(unused_keys)
        
        return validation_result
    
    def process_document_references(self, latex_files: Dict[str, str]) -> Dict[str, Any]:
        """Process all references in a complete document."""
        all_content = ""
        section_references = {}
        
        # Extract references from each section
        for section_name, content in latex_files.items():
            if section_name.endswith('.tex') and section_name != 'main.tex':
                section_key = section_name.replace('.tex', '')
                refs = self.cross_ref_manager.extract_references_from_latex(content, section_key)
                section_references[section_key] = refs
                all_content += content + "\n"
        
        # Validate cross-references
        cross_ref_validation = self.cross_ref_manager.validate_references(all_content)
        
        # Validate citations
        citation_validation = self.validate_citations_in_text(all_content)
        
        # Generate reference summary
        reference_summary = self.cross_ref_manager.generate_reference_summary()
        
        return {
            'cross_references': {
                'validation': cross_ref_validation,
                'summary': reference_summary,
                'by_section': section_references
            },
            'citations': citation_validation,
            'total_bibliography_entries': len(self.citations)
        }
    
    def create_ai_publishing_bibliography(self) -> List[Citation]:
        """Create a bibliography focused on AI and publishing research."""
        ai_publishing_citations = [
            Citation(
                key="radford2019language",
                title="Language Models are Unsupervised Multitask Learners",
                authors=["Alec Radford", "Jeffrey Wu", "Rewon Child", "David Luan", "Dario Amodei", "Ilya Sutskever"],
                year=2019,
                venue="OpenAI Blog",
                citation_type="online",
                url="https://openai.com/blog/better-language-models/"
            ),
            Citation(
                key="brown2020language",
                title="Language Models are Few-Shot Learners",
                authors=["Tom B. Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah", "Jared Kaplan"],
                year=2020,
                venue="Advances in Neural Information Processing Systems",
                citation_type="inproceedings",
                pages="1877--1901"
            ),
            Citation(
                key="vaswani2017attention",
                title="Attention is All You Need",
                authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones"],
                year=2017,
                venue="Advances in Neural Information Processing Systems",
                citation_type="inproceedings",
                pages="5998--6008"
            ),
            Citation(
                key="devlin2018bert",
                title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                authors=["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
                year=2018,
                venue="arXiv preprint arXiv:1810.04805",
                citation_type="misc",
                arxiv_id="1810.04805"
            ),
            Citation(
                key="floridi2020gpt3",
                title="GPT-3: Its Nature, Scope, Limits, and Consequences",
                authors=["Luciano Floridi", "Massimo Chiriatti"],
                year=2020,
                venue="Minds and Machines",
                citation_type="article",
                volume="30",
                number="4",
                pages="681--694",
                doi="10.1007/s11023-020-09548-1"
            ),
            Citation(
                key="dale2021gpt3",
                title="GPT-3: What's it good for?",
                authors=["Robert Dale"],
                year=2021,
                venue="Natural Language Engineering",
                citation_type="article",
                volume="27",
                number="1",
                pages="113--118",
                doi="10.1017/S1351324920000601"
            ),
            Citation(
                key="bommasani2021opportunities",
                title="On the Opportunities and Risks of Foundation Models",
                authors=["Rishi Bommasani", "Drew A. Hudson", "Ehsan Adeli", "Russ Altman", "Simran Arora"],
                year=2021,
                venue="arXiv preprint arXiv:2108.07258",
                citation_type="misc",
                arxiv_id="2108.07258"
            ),
            Citation(
                key="qiu2020pre",
                title="Pre-trained Models for Natural Language Processing: A Survey",
                authors=["Xipeng Qiu", "Tianxiang Sun", "Yige Xu", "Yunfan Shao", "Ning Dai", "Xuanjing Huang"],
                year=2020,
                venue="Science China Information Sciences",
                citation_type="article",
                volume="63",
                number="1",
                pages="1--25",
                doi="10.1007/s11432-020-2956-5"
            )
        ]
        
        # Add citations to manager
        for citation in ai_publishing_citations:
            self.add_citation(citation)
        
        return ai_publishing_citations


def create_citation_manager(bibliography_file: str = None) -> CitationManager:
    """Create citation manager with optional bibliography file."""
    manager = CitationManager(bibliography_file)
    
    # Add default AI/publishing bibliography if no file provided
    if not bibliography_file:
        manager.create_ai_publishing_bibliography()
    
    return manager


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create citation manager with AI publishing bibliography
    manager = create_citation_manager()
    
    # Generate BibTeX file
    manager.generate_bibtex_file("output/arxiv_paper/bibliography/references.bib")
    
    print(f"Generated bibliography with {len(manager.citations)} citations")