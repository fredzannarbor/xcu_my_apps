#!/usr/bin/env python3
"""
BISAC Code Validator

This module provides validation and generation of BISAC subject codes
according to current BISAC standards (2024).
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BISACValidationResult:
    """Result of BISAC code validation."""
    is_valid: bool
    message: str
    suggested_codes: List[str] = None
    category_name: Optional[str] = None


class BISACValidator:
    """Validates and suggests BISAC codes according to current standards."""
    
    def __init__(self):
        """Initialize with current BISAC codes database."""
        self.valid_codes = self._load_bisac_codes()
        self.category_mappings = self._load_category_mappings()
    
    def _load_bisac_codes(self) -> Dict[str, str]:
        """Load valid BISAC codes with their descriptions."""
        # Current BISAC codes as of 2024
        return {
            # General categories
            "GEN000000": "General",
            "REF000000": "Reference",
            
            # Business & Economics
            "BUS000000": "Business & Economics",
            "BUS001000": "Business & Economics / Accounting / General",
            "BUS002000": "Business & Economics / Advertising & Promotion",
            "BUS003000": "Business & Economics / Auditing",
            "BUS004000": "Business & Economics / Banks & Banking",
            "BUS005000": "Business & Economics / Budgeting",
            "BUS006000": "Business & Economics / Careers / General",
            "BUS007000": "Business & Economics / Consulting",
            "BUS008000": "Business & Economics / Consumer Behavior",
            "BUS009000": "Business & Economics / Customer Relations",
            "BUS010000": "Business & Economics / Development / Business Development",
            "BUS011000": "Business & Economics / Development / Economic Development",
            "BUS012000": "Business & Economics / Economics / General",
            "BUS013000": "Business & Economics / Economics / Macroeconomics",
            "BUS014000": "Business & Economics / Economics / Microeconomics",
            "BUS015000": "Business & Economics / Entrepreneurship",
            "BUS016000": "Business & Economics / Ethics",
            "BUS017000": "Business & Economics / Finance / General",
            "BUS018000": "Business & Economics / Finance / Corporate Finance",
            "BUS019000": "Business & Economics / Finance / Financial Risk Management",
            "BUS020000": "Business & Economics / Finance / Investment",
            "BUS021000": "Business & Economics / Finance / Personal Finance / General",
            "BUS022000": "Business & Economics / Finance / Personal Finance / Budgeting",
            "BUS023000": "Business & Economics / Finance / Personal Finance / Investing",
            "BUS024000": "Business & Economics / Finance / Personal Finance / Money Management",
            "BUS025000": "Business & Economics / Finance / Personal Finance / Retirement Planning",
            "BUS026000": "Business & Economics / Human Resources & Personnel Management",
            "BUS027000": "Business & Economics / Industries / General",
            "BUS028000": "Business & Economics / Industries / Hospitality, Travel & Tourism",
            "BUS029000": "Business & Economics / Industries / Media & Communications",
            "BUS030000": "Business & Economics / Industries / Real Estate / General",
            "BUS031000": "Business & Economics / Industries / Retail",
            "BUS032000": "Business & Economics / Industries / Transportation",
            "BUS033000": "Business & Economics / Insurance / General",
            "BUS034000": "Business & Economics / International / General",
            "BUS035000": "Business & Economics / International / Economics",
            "BUS036000": "Business & Economics / International / Marketing",
            "BUS037000": "Business & Economics / Leadership",
            "BUS038000": "Business & Economics / Management",
            "BUS039000": "Business & Economics / Management Science",
            "BUS040000": "Business & Economics / Marketing / General",
            "BUS041000": "Business & Economics / Marketing / Direct",
            "BUS042000": "Business & Economics / Marketing / Internet",
            "BUS043000": "Business & Economics / Marketing / Research",
            "BUS044000": "Business & Economics / Mergers & Acquisitions",
            "BUS045000": "Business & Economics / Motivational",
            "BUS046000": "Business & Economics / Negotiating",
            "BUS047000": "Business & Economics / Nonprofit Organizations & Charities",
            "BUS048000": "Business & Economics / Operations Research",
            "BUS049000": "Business & Economics / Organizational Behavior",
            "BUS050000": "Business & Economics / Personal Success",
            "BUS051000": "Business & Economics / Production & Operations Management",
            "BUS052000": "Business & Economics / Project Management",
            "BUS053000": "Business & Economics / Public Relations",
            "BUS054000": "Business & Economics / Purchasing & Buying",
            "BUS055000": "Business & Economics / Quality Control",
            "BUS056000": "Business & Economics / Real Estate / General",
            "BUS057000": "Business & Economics / Sales & Selling / General",
            "BUS058000": "Business & Economics / Small Business",
            "BUS059000": "Business & Economics / Statistics",
            "BUS060000": "Business & Economics / Strategic Planning",
            "BUS061000": "Business & Economics / Taxation / General",
            "BUS062000": "Business & Economics / Time Management",
            "BUS063000": "Business & Economics / Training",
            "BUS064000": "Business & Economics / Women in Business",
            "BUS065000": "Business & Economics / Workplace Culture",
            
            # Technology & Computing
            "COM000000": "Computers",
            "COM001000": "Computers / General",
            "COM002000": "Computers / Artificial Intelligence",
            "COM003000": "Computers / Computer Graphics",
            "COM004000": "Computers / Computer Literacy",
            "COM005000": "Computers / Computer Science",
            "COM006000": "Computers / Computer Vision & Pattern Recognition",
            "COM007000": "Computers / Cybernetics",
            "COM008000": "Computers / Data Processing",
            "COM009000": "Computers / Data Science / General",
            "COM010000": "Computers / Database Administration & Management",
            "COM011000": "Computers / Desktop Applications / General",
            "COM012000": "Computers / Desktop Applications / Spreadsheets",
            "COM013000": "Computers / Desktop Applications / Word Processing",
            "COM014000": "Computers / Desktop Publishing",
            "COM015000": "Computers / Digital Media / General",
            "COM016000": "Computers / Digital Media / Audio",
            "COM017000": "Computers / Digital Media / Photography",
            "COM018000": "Computers / Digital Media / Video & Animation",
            "COM019000": "Computers / Electronic Commerce",
            "COM020000": "Computers / Enterprise Applications / General",
            "COM021000": "Computers / Hardware / General",
            "COM022000": "Computers / Hardware / Mainframes & Minicomputers",
            "COM023000": "Computers / Hardware / Microprocessors",
            "COM024000": "Computers / Hardware / Network Hardware",
            "COM025000": "Computers / Hardware / Personal Computers / General",
            "COM026000": "Computers / Hardware / Personal Computers / Macintosh",
            "COM027000": "Computers / Hardware / Personal Computers / PCs",
            "COM028000": "Computers / Hardware / Peripherals",
            "COM029000": "Computers / Hardware / Printers",
            "COM030000": "Computers / Hardware / Servers",
            "COM031000": "Computers / Information Technology",
            "COM032000": "Computers / Information Theory",
            "COM033000": "Computers / Intelligence (AI) & Semantics",
            "COM034000": "Computers / Internet / General",
            "COM035000": "Computers / Internet / Web Browsers",
            "COM036000": "Computers / Internet / Web Programming",
            "COM037000": "Computers / Internet / Web Servers",
            "COM038000": "Computers / Languages / General",
            "COM039000": "Computers / Languages / C",
            "COM040000": "Computers / Languages / C++",
            "COM041000": "Computers / Languages / Java",
            "COM042000": "Computers / Languages / JavaScript",
            "COM043000": "Computers / Languages / Pascal",
            "COM044000": "Computers / Languages / Python",
            "COM045000": "Computers / Languages / SQL",
            "COM046000": "Computers / Languages / Visual Basic",
            "COM047000": "Computers / Machine Theory",
            "COM048000": "Computers / Mathematical & Statistical Software",
            "COM049000": "Computers / Networking / General",
            "COM050000": "Computers / Networking / Hardware",
            "COM051000": "Computers / Networking / Network Protocols",
            "COM052000": "Computers / Networking / Network Security",
            "COM053000": "Computers / Networking / Vendor Specific",
            "COM054000": "Computers / Operating Systems / General",
            "COM055000": "Computers / Operating Systems / Linux",
            "COM056000": "Computers / Operating Systems / Macintosh",
            "COM057000": "Computers / Operating Systems / UNIX",
            "COM058000": "Computers / Operating Systems / Windows",
            "COM059000": "Computers / Programming / General",
            "COM060000": "Computers / Programming / Algorithms",
            "COM061000": "Computers / Programming / Games",
            "COM062000": "Computers / Programming / Microsoft Programming",
            "COM063000": "Computers / Programming / Object Oriented",
            "COM064000": "Computers / Programming / Open Source",
            "COM065000": "Computers / Programming Languages / General",
            "COM066000": "Computers / Security / General",
            "COM067000": "Computers / Security / Cryptography",
            "COM068000": "Computers / Security / Network Security",
            "COM069000": "Computers / Software Development & Engineering / General",
            "COM070000": "Computers / Software Development & Engineering / Quality Assurance & Testing",
            "COM071000": "Computers / Software Development & Engineering / Systems Analysis & Design",
            "COM072000": "Computers / Software Development & Engineering / Tools",
            "COM073000": "Computers / System Administration / General",
            "COM074000": "Computers / System Administration / Linux & UNIX Administration",
            "COM075000": "Computers / System Administration / Network Administration",
            "COM076000": "Computers / System Administration / Storage & Retrieval",
            "COM077000": "Computers / User Interfaces",
            "COM078000": "Computers / Web / General",
            "COM079000": "Computers / Web / Web Programming",
            "COM080000": "Computers / Web / Web Services & APIs",
            
            # Science
            "SCI000000": "Science",
            "SCI001000": "Science / General",
            "SCI002000": "Science / Astronomy",
            "SCI003000": "Science / Biology / General",
            "SCI004000": "Science / Chemistry / General",
            "SCI005000": "Science / Earth Sciences / General",
            "SCI006000": "Science / Environmental Science",
            "SCI007000": "Science / Life Sciences / General",
            "SCI008000": "Science / Mathematics / General",
            "SCI009000": "Science / Physics / General",
            
            # Self-Help
            "SEL000000": "Self-Help",
            "SEL001000": "Self-Help / General",
            "SEL002000": "Self-Help / Affirmations",
            "SEL003000": "Self-Help / Communication & Social Skills",
            "SEL004000": "Self-Help / Creativity",
            "SEL005000": "Self-Help / Death, Grief, Bereavement",
            "SEL006000": "Self-Help / Dreams",
            "SEL007000": "Self-Help / Eating Disorders & Body Image",
            "SEL008000": "Self-Help / Emotions",
            "SEL009000": "Self-Help / Fashion & Style",
            "SEL010000": "Self-Help / Handwriting Analysis",
            "SEL011000": "Self-Help / Hypnotism",
            "SEL012000": "Self-Help / Inner Child",
            "SEL013000": "Self-Help / Memory Improvement",
            "SEL014000": "Self-Help / Motivational & Inspirational",
            "SEL015000": "Self-Help / Neuro-Linguistic Programming (NLP)",
            "SEL016000": "Self-Help / Personal Growth / General",
            "SEL017000": "Self-Help / Personal Growth / Happiness",
            "SEL018000": "Self-Help / Personal Growth / Memory Improvement",
            "SEL019000": "Self-Help / Personal Growth / Self-Esteem",
            "SEL020000": "Self-Help / Personal Growth / Success",
            "SEL021000": "Self-Help / Relationships / General",
            "SEL022000": "Self-Help / Relationships / Dating",
            "SEL023000": "Self-Help / Relationships / Divorce & Separation",
            "SEL024000": "Self-Help / Relationships / Love & Romance",
            "SEL025000": "Self-Help / Relationships / Marriage & Long-Term Relationships",
            "SEL026000": "Self-Help / Sexual Instruction",
            "SEL027000": "Self-Help / Spiritual",
            "SEL028000": "Self-Help / Stress Management",
            "SEL029000": "Self-Help / Substance Abuse & Addictions / General",
            "SEL030000": "Self-Help / Time Management",
            
            # Philosophy
            "PHI000000": "Philosophy",
            "PHI001000": "Philosophy / General",
            "PHI002000": "Philosophy / Aesthetics",
            "PHI003000": "Philosophy / Ancient",
            "PHI004000": "Philosophy / Criticism",
            "PHI005000": "Philosophy / Eastern",
            "PHI006000": "Philosophy / Epistemology",
            "PHI007000": "Philosophy / Ethics & Moral Philosophy",
            "PHI008000": "Philosophy / Free Will & Determinism",
            "PHI009000": "Philosophy / Good & Evil",
            "PHI010000": "Philosophy / History & Surveys / General",
            "PHI011000": "Philosophy / History & Surveys / Ancient & Classical",
            "PHI012000": "Philosophy / History & Surveys / Medieval",
            "PHI013000": "Philosophy / History & Surveys / Modern",
            "PHI014000": "Philosophy / Logic",
            "PHI015000": "Philosophy / Metaphysics",
            "PHI016000": "Philosophy / Mind & Body",
            "PHI017000": "Philosophy / Movements / General",
            "PHI018000": "Philosophy / Movements / Existentialism",
            "PHI019000": "Philosophy / Movements / Humanism",
            "PHI020000": "Philosophy / Movements / Pragmatism",
            "PHI021000": "Philosophy / Political",
            "PHI022000": "Philosophy / Religious",
            "PHI023000": "Philosophy / Social",
            "PHI024000": "Philosophy / Surveys & Introductions"
        }
    
    def _load_category_mappings(self) -> Dict[str, List[str]]:
        """Load keyword to BISAC category mappings."""
        return {
            'technology': ['COM001000', 'COM005000', 'COM032000'],
            'artificial intelligence': ['COM002000', 'COM033000'],
            'ai': ['COM002000', 'COM033000'],
            'machine learning': ['COM002000', 'COM033000'],
            'programming': ['COM059000', 'COM060000'],
            'python': ['COM044000', 'COM059000'],
            'javascript': ['COM042000', 'COM059000'],
            'web development': ['COM036000', 'COM079000'],
            'business': ['BUS000000', 'BUS038000'],
            'management': ['BUS038000', 'BUS037000'],
            'leadership': ['BUS037000', 'BUS050000'],
            'marketing': ['BUS040000', 'BUS041000'],
            'finance': ['BUS017000', 'BUS021000'],
            'economics': ['BUS012000', 'BUS013000'],
            'entrepreneurship': ['BUS015000', 'BUS058000'],
            'self-help': ['SEL001000', 'SEL016000'],
            'personal development': ['SEL016000', 'SEL020000'],
            'motivation': ['SEL014000', 'SEL020000'],
            'relationships': ['SEL021000', 'SEL025000'],
            'philosophy': ['PHI001000', 'PHI007000'],
            'ethics': ['PHI007000', 'BUS016000'],
            'science': ['SCI001000', 'SCI003000'],
            'mathematics': ['SCI008000', 'COM048000'],
            'physics': ['SCI009000'],
            'biology': ['SCI003000', 'SCI007000'],
            'chemistry': ['SCI004000'],
            'environment': ['SCI006000'],
            'astronomy': ['SCI002000'],
            'reference': ['REF000000'],
            'general': ['GEN000000']
        }
    
    def validate_bisac_code(self, code: str) -> BISACValidationResult:
        """
        Validate a BISAC code against current standards.
        
        Args:
            code: BISAC code to validate (e.g., 'BUS001000')
            
        Returns:
            BISACValidationResult with validation status and details
        """
        if not code:
            return BISACValidationResult(
                is_valid=False,
                message="BISAC code cannot be empty"
            )
        
        # Check format: 3 letters + 6 digits
        if not re.match(r'^[A-Z]{3}\d{6}$', code):
            return BISACValidationResult(
                is_valid=False,
                message=f"Invalid BISAC format: '{code}'. Expected format: 3 letters + 6 digits (e.g., BUS001000)",
                suggested_codes=self._suggest_format_corrections(code)
            )
        
        # Check if code exists in current database
        if code in self.valid_codes:
            return BISACValidationResult(
                is_valid=True,
                message="Valid BISAC code",
                category_name=self.valid_codes[code]
            )
        else:
            return BISACValidationResult(
                is_valid=False,
                message=f"BISAC code '{code}' not found in current standards",
                suggested_codes=self._suggest_similar_codes(code)
            )
    
    def suggest_bisac_codes(self, keywords: List[str], max_suggestions: int = 3) -> List[Tuple[str, str, float]]:
        """
        Suggest BISAC codes based on keywords.
        
        Args:
            keywords: List of keywords describing the book content
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of tuples (code, description, confidence_score)
        """
        suggestions = []
        keyword_text = ' '.join(keywords).lower()
        
        # Direct keyword matching
        for keyword, codes in self.category_mappings.items():
            if keyword in keyword_text:
                for code in codes:
                    if code in self.valid_codes:
                        confidence = 0.9 if keyword in keyword_text.split() else 0.7
                        suggestions.append((code, self.valid_codes[code], confidence))
        
        # Fuzzy matching on descriptions
        for code, description in self.valid_codes.items():
            description_lower = description.lower()
            matches = sum(1 for keyword in keywords if keyword.lower() in description_lower)
            if matches > 0:
                confidence = min(0.8, matches / len(keywords))
                suggestions.append((code, description, confidence))
        
        # Remove duplicates and sort by confidence
        unique_suggestions = {}
        for code, desc, conf in suggestions:
            if code not in unique_suggestions or unique_suggestions[code][1] < conf:
                unique_suggestions[code] = (desc, conf)
        
        sorted_suggestions = [
            (code, desc, conf) 
            for code, (desc, conf) in unique_suggestions.items()
        ]
        sorted_suggestions.sort(key=lambda x: x[2], reverse=True)
        
        return sorted_suggestions[:max_suggestions]
    
    def _suggest_format_corrections(self, invalid_code: str) -> List[str]:
        """Suggest format corrections for malformed BISAC codes."""
        suggestions = []
        
        # Try to extract valid parts
        letters = ''.join(c for c in invalid_code if c.isalpha()).upper()
        digits = ''.join(c for c in invalid_code if c.isdigit())
        
        if len(letters) >= 3 and len(digits) >= 6:
            corrected = letters[:3] + digits[:6]
            if corrected in self.valid_codes:
                suggestions.append(corrected)
        
        # Common format mistakes
        if len(invalid_code) == 9:  # Might be missing leading zeros
            if invalid_code[:3].isalpha() and invalid_code[3:].isdigit():
                padded = invalid_code[:3] + invalid_code[3:].zfill(6)
                if padded in self.valid_codes:
                    suggestions.append(padded)
        
        return suggestions[:3]
    
    def _suggest_similar_codes(self, invalid_code: str) -> List[str]:
        """Suggest similar valid BISAC codes."""
        suggestions = []
        
        if len(invalid_code) >= 3:
            prefix = invalid_code[:3]
            # Find codes with same prefix
            similar = [code for code in self.valid_codes.keys() if code.startswith(prefix)]
            suggestions.extend(similar[:5])
        
        return suggestions
    
    def validate_category_name(self, category_name: str) -> BISACValidationResult:
        """
        Validate a BISAC category name (not code).
        
        Args:
            category_name: Category name to validate (e.g., 'BUSINESS & ECONOMICS / General')
            
        Returns:
            BISACValidationResult with validation status and details
        """
        if not category_name:
            return BISACValidationResult(
                is_valid=False,
                message="Category name cannot be empty"
            )
        
        category_name = category_name.strip()
        
        # Check if the category name exists in our database
        for code, name in self.valid_codes.items():
            if name.lower() == category_name.lower():
                return BISACValidationResult(
                    is_valid=True,
                    message="Valid BISAC category name",
                    category_name=name
                )
        
        # Check for partial matches or similar names
        similar_names = []
        category_lower = category_name.lower()
        
        for code, name in self.valid_codes.items():
            name_lower = name.lower()
            if category_lower in name_lower or name_lower in category_lower:
                similar_names.append(name)
        
        if similar_names:
            return BISACValidationResult(
                is_valid=False,
                message=f"Category name '{category_name}' not found, but similar categories exist",
                suggested_codes=similar_names[:5]
            )
        
        # If no matches found, it might still be valid but not in our database
        return BISACValidationResult(
            is_valid=False,
            message=f"Category name '{category_name}' not found in BISAC database",
            suggested_codes=self._suggest_by_keywords(category_name)
        )
    
    def get_category_name_from_code(self, code: str) -> Optional[str]:
        """
        Get the full category name from a BISAC code.
        
        Args:
            code: BISAC code (e.g., 'BUS001000')
            
        Returns:
            Full category name if code is valid, None otherwise
        """
        return self.valid_codes.get(code)
    
    def get_code_from_category_name(self, category_name: str) -> Optional[str]:
        """
        Get the BISAC code from a category name.
        
        Args:
            category_name: Category name (e.g., 'BUSINESS & ECONOMICS / General')
            
        Returns:
            BISAC code if category is found, None otherwise
        """
        if not category_name:
            return None
        
        category_name = category_name.strip()
        
        for code, name in self.valid_codes.items():
            if name.lower() == category_name.lower():
                return code
        
        return None
    
    def _suggest_by_keywords(self, category_name: str) -> List[str]:
        """
        Suggest categories based on keywords in the category name.
        
        Args:
            category_name: Category name to analyze
            
        Returns:
            List of suggested category names
        """
        if not category_name:
            return []
        
        keywords = category_name.lower().split()
        suggestions = []
        
        for code, name in self.valid_codes.items():
            name_lower = name.lower()
            matches = sum(1 for keyword in keywords if keyword in name_lower)
            if matches > 0:
                suggestions.append((name, matches))
        
        # Sort by number of matches and return top suggestions
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in suggestions[:5]]
    
    def get_fallback_codes(self) -> List[str]:
        """Get safe fallback BISAC codes for when generation fails."""
        return [
            "GEN000000",  # General
            "REF000000",  # Reference
            "BUS000000"   # Business & Economics
        ]
    
    def get_fallback_category_names(self) -> List[str]:
        """Get safe fallback BISAC category names for when generation fails."""
        return [
            "GENERAL",
            "REFERENCE / General", 
            "BUSINESS & ECONOMICS / General"
        ]


# Global validator instance
_bisac_validator = None

def get_bisac_validator() -> BISACValidator:
    """Get the global BISAC validator instance."""
    global _bisac_validator
    if _bisac_validator is None:
        _bisac_validator = BISACValidator()
    return _bisac_validator