#!/usr/bin/env python3
"""
Enhanced imprint expander that uses real LLM calls with hybrid generation strategies.
"""


import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Get the absolute path of the directory containing the current script.
script_dir = Path(__file__).resolve().parent
# Assume the project root is one level up from the 'tools' directory.
# This makes 'src' and 'unified_
# editor.py' importable directly if they are in the project root.
project_root = script_dir.parent

from src.codexes.modules.imprint_builder.imprint_concept import ImprintConceptParser
from src.codexes.modules.imprint_builder.imprint_expander import ImprintExpander, LLMCaller


# Valid options for constrained fields
VALID_OPTIONS = {
    'trim_sizes': ['5x8', '5.5x8.5', '6x9', '6.14x9.21', '7x10', '7.5x9.25', '8x10', '8.5x11'],
    'publication_frequencies': ['Weekly', 'Bi-weekly', 'Monthly', 'Bi-monthly', 'Quarterly', 'Semi-annually', 'Annually'],
    'pricing_tiers': ['Budget ($9.99-$14.99)', 'Mid-range ($15.99-$19.99)', 'Premium ($20.99-$29.99)', 'Luxury ($30.00+)'],
    'font_categories': ['Serif', 'Sans-serif', 'Script', 'Display', 'Monospace'],
    'popular_fonts': {
        'serif': ['Times New Roman', 'Georgia', 'Minion Pro', 'Adobe Garamond', 'Sabon', 'Caslon'],
        'sans_serif': ['Helvetica', 'Arial', 'Futura', 'Source Sans Pro', 'Open Sans'],
        'display': ['Trajan Pro', 'Optima', 'Copperplate', 'Impact', 'Bebas Neue']
    },
    'marketing_platforms': [
        'Goodreads', 'BookBub', 'NetGalley', 'Instagram', 'TikTok', 'Twitter/X', 'Facebook',
        'Literary blogs', 'Book review sites', 'Podcast networks', 'YouTube', 'LinkedIn'
    ],
    'distribution_channels': [
        'Amazon', 'Barnes & Noble', 'Independent bookstores', 'Libraries', 'Academic institutions',
        'Online retailers', 'International distributors', 'Specialty stores'
    ],
    'workflow_stages': [
        'Manuscript Acquisition', 'Initial Review', 'Editorial Assessment', 'Developmental Editing',
        'Copy Editing', 'Design & Layout', 'Proofreading', 'Production', 'Marketing & Promotion',
        'Distribution', 'Launch Support', 'Post-Launch Analysis'
    ]
}


class EnhancedImprintExpander:
    """Enhanced expander using real LLM with hybrid generation strategies."""
    
    def __init__(self, llm_caller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def expand_concept(self, concept) -> Dict[str, Any]:
        """Expand concept using hybrid LLM + rule-based approach."""
        
        self.logger.info(f"Expanding concept with hybrid approach: {concept.name}")
        
        # Extract key info from concept
        concept_text = concept.description
        target_audience = getattr(concept, 'target_audience', 'General readers')
        genre_focus = getattr(concept, 'genre_focus', ['Fiction'])
        
        # Generate each section with appropriate strategy
        branding = self._generate_branding_llm(concept_text, target_audience)
        design_specs = self._generate_design_hybrid(concept_text, branding)
        publishing_strategy = self._generate_publishing_hybrid(concept_text, genre_focus, target_audience)
        operational_framework = self._generate_operational_hybrid(concept_text)
        marketing_approach = self._generate_marketing_hybrid(concept_text, target_audience)
        financial_projections = self._generate_financial_hybrid(concept_text)
        
        return {
            'concept': concept.to_dict(),
            'branding': branding,
            'design_specifications': design_specs,
            'publishing_strategy': publishing_strategy,
            'operational_framework': operational_framework,
            'marketing_approach': marketing_approach,
            'financial_projections': financial_projections,
            'expanded_at': datetime.now().isoformat()
        }
    
    def _call_llm_safe(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Safely call LLM and parse JSON response."""
        try:
            response = self.llm_caller.call_model_with_prompt(prompt, temperature=temperature)
            content = response.get('content', '{}')
            
            # Clean up common JSON issues
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return {}
    
    def _generate_branding_llm(self, concept_text: str, target_audience: str) -> Dict[str, Any]:
        """Generate branding using pure LLM creativity."""
        
        prompt = f"""Based on this imprint concept, create comprehensive branding:

Concept: {concept_text}
Target Audience: {target_audience}

Generate branding that captures the essence of this concept. Return ONLY valid JSON with these exact fields:

{{
    "imprint_name": "A compelling, memorable name for the imprint",
    "mission_statement": "A clear, inspiring mission statement (2-3 sentences)",
    "brand_values": ["3-5 core values as strings"],
    "brand_voice": "Description of the brand's communication style",
    "tagline": "A memorable tagline (under 10 words)",
    "unique_selling_proposition": "What makes this imprint unique (1-2 sentences)",
    "logo_concept": "Detailed description of logo concept and visual elements"
}}

Make the branding authentic to the concept and appealing to the target audience."""
        
        result = self._call_llm_safe(prompt)
        
        # Ensure required fields with fallbacks
        return {
            'imprint_name': result.get('imprint_name', 'New Literary Imprint'),
            'mission_statement': result.get('mission_statement', 'To publish exceptional literature that connects with readers.'),
            'brand_values': result.get('brand_values', ['Quality', 'Innovation', 'Authenticity']),
            'brand_voice': result.get('brand_voice', 'Professional, engaging, and accessible'),
            'tagline': result.get('tagline', 'Stories That Matter'),
            'unique_selling_proposition': result.get('unique_selling_proposition', 'Distinctive literary publishing with focus on quality and reader connection.'),
            'logo_concept': result.get('logo_concept', 'Clean, modern design reflecting literary excellence')
        }
    
    def _generate_design_hybrid(self, concept_text: str, branding: Dict[str, Any]) -> Dict[str, Any]:
        """Generate design using LLM for creative elements + rules for technical specs."""
        
        # LLM for creative color palette and visual direction
        creative_prompt = f"""Based on this imprint concept and branding, suggest a color palette and visual direction:

Concept: {concept_text}
Imprint Name: {branding.get('imprint_name', 'Literary Imprint')}
Brand Voice: {branding.get('brand_voice', 'Professional')}

Return ONLY valid JSON:
{{
    "color_palette": {{
        "primary": "(0,0,0,0) CMYK color",
        "secondary": "(0,0,0,0) CMYK color",
        "accent": "(0,0,0,0) CMYK color",
        "neutral": "(0,0,0,0) CMYK color"
    }},
    "visual_motifs": ["3-4 visual elements as strings"],
    "cover_art_direction": "Brief description of cover art style",
    "interior_layout_preferences": {{
        "chapter_start": "Description of chapter opening style",
        "margins": "Margin preferences",
        "text_and_header_styles": "Typography style guidance"
    }}
}}"""
        
        creative_result = self._call_llm_safe(creative_prompt)
        
        # Rule-based font selection
        fonts = self._select_fonts_by_rules(concept_text, branding.get('brand_voice', ''))
        
        # Rule-based trim sizes
        trim_sizes = self._select_trim_sizes_by_rules(concept_text)
        
        return {
            'color_palette': creative_result.get('color_palette', {
                'primary': '#2C3E50',
                'secondary': '#3498DB',
                'accent': '#E74C3C',
                'neutral': '#F8F9FA'
            }),
            'typography': {
                'headline': fonts.get('headline_style', 'Serif, bold, elegant'),
                'body': fonts.get('body_style', 'Sans-serif, readable, modern'),
                'primary_font': fonts.get('primary_font', 'Georgia'),
                'secondary_font': fonts.get('secondary_font', 'Helvetica'),
                'body_font': fonts.get('body_font', 'Times New Roman')
            },
            'visual_motifs': creative_result.get('visual_motifs', ['Clean lines', 'Literary symbols', 'Modern elements']),
            'cover_art_direction': creative_result.get('cover_art_direction', 'Modern, clean design with strong typography'),
            'interior_layout_preferences': creative_result.get('interior_layout_preferences', {
                'chapter_start': 'Elegant drop cap with clean typography',
                'margins': 'Generous, balanced margins for comfortable reading',
                'text_and_header_styles': 'Professional, readable typography'
            }),
            'trim_sizes': trim_sizes
        }
    
    def _select_fonts_by_rules(self, concept_text: str, brand_voice: str) -> Dict[str, str]:
        """Select fonts based on concept analysis."""
        
        concept_lower = concept_text.lower()
        voice_lower = brand_voice.lower()
        
        # Determine font category based on concept
        if any(word in concept_lower for word in ['literary', 'classic', 'traditional', 'academic']):
            primary_font = 'Georgia'
            headline_style = 'Serif, elegant, traditional'
        elif any(word in concept_lower for word in ['modern', 'contemporary', 'digital', 'tech']):
            primary_font = 'Helvetica'
            headline_style = 'Sans-serif, clean, modern'
        elif any(word in concept_lower for word in ['creative', 'artistic', 'design']):
            primary_font = 'Futura'
            headline_style = 'Sans-serif, geometric, creative'
        else:
            primary_font = 'Minion Pro'
            headline_style = 'Serif, readable, professional'
        
        # Select complementary fonts
        if primary_font in VALID_OPTIONS['popular_fonts']['serif']:
            secondary_font = 'Futura'  # Sans-serif complement
            body_font = primary_font
        else:
            secondary_font = 'Source Serif Pro'  # Serif complement
            body_font = 'Source Sans Pro'
        
        return {
            'primary_font': primary_font,
            'secondary_font': secondary_font,
            'body_font': body_font,
            'headline_style': headline_style,
            'body_style': 'Clean, readable, professional'
        }
    
    def _select_trim_sizes_by_rules(self, concept_text: str) -> List[str]:
        """Select trim sizes based on concept type."""
        
        concept_lower = concept_text.lower()
        
        if any(word in concept_lower for word in ['academic', 'textbook', 'reference']):
            return ['8.5x11', '7x10']
        elif any(word in concept_lower for word in ['poetry', 'art', 'photography']):
            return ['6x9', '7.5x9.25']
        elif any(word in concept_lower for word in ['novel', 'fiction', 'literary']):
            return ['6x9', '5.5x8.5']
        elif any(word in concept_lower for word in ['children', 'young adult', 'ya']):
            return ['5.5x8.5', '6x9']
        else:
            return ['6x9', '5.5x8.5', '7x10']  # Standard options
    
    def _generate_publishing_hybrid(self, concept_text: str, genre_focus: List[str], target_audience: str) -> Dict[str, Any]:
        """Generate publishing strategy using LLM + rules."""
        
        # LLM for strategic content
        strategy_prompt = f"""Based on this imprint concept, create a publishing strategy:

Concept: {concept_text}
Genre Focus: {', '.join(genre_focus)}
Target Audience: {target_audience}

Return ONLY valid JSON:
{{
    "primary_genres": ["3-5 specific genres as strings"],
    "target_readership": "Detailed description of ideal readers",
    "editorial_focus": "What types of narratives/themes to prioritize",
    "author_acquisition_strategy": "How to find and sign authors",
    "market_positioning": "How to differentiate in the market"
}}"""
        
        strategy_result = self._call_llm_safe(strategy_prompt)
        
        # Rule-based selections
        publication_frequency = self._select_publication_frequency(concept_text)
        pricing_strategy = self._select_pricing_strategy(concept_text)
        rights_management = self._select_rights_management(concept_text)
        
        return {
            'primary_genres': strategy_result.get('primary_genres', genre_focus),
            'target_readership': strategy_result.get('target_readership', target_audience),
            'target_audience': target_audience,
            'publication_frequency': publication_frequency,
            'editorial_focus': strategy_result.get('editorial_focus', 'High-quality, engaging content'),
            'author_acquisition_strategy': strategy_result.get('author_acquisition_strategy', 'Agent submissions and direct outreach'),
            'rights_management': rights_management,
            'pricing_strategy': pricing_strategy,
            'market_positioning': strategy_result.get('market_positioning', 'Quality-focused publishing with strong editorial standards')
        }
    
    def _select_publication_frequency(self, concept_text: str) -> str:
        """Select publication frequency based on concept."""
        concept_lower = concept_text.lower()
        
        if any(word in concept_lower for word in ['8-12', '10-15', 'many', 'high volume']):
            return 'Monthly'
        elif any(word in concept_lower for word in ['4-6', '6-8', 'few', 'selective']):
            return 'Quarterly'
        elif any(word in concept_lower for word in ['1-3', 'rare', 'exclusive']):
            return 'Semi-annually'
        else:
            return 'Bi-monthly'  # Default
    
    def _select_pricing_strategy(self, concept_text: str) -> Dict[str, str]:
        """Select pricing strategy based on concept."""
        concept_lower = concept_text.lower()
        
        if any(word in concept_lower for word in ['premium', 'luxury', 'high-end', 'exclusive']):
            return {
                'hardcover': 'Premium ($24.99-$34.99)',
                'paperback': 'Mid-range ($16.99-$22.99)',
                'ebook': 'Standard ($12.99-$16.99)'
            }
        elif any(word in concept_lower for word in ['budget', 'affordable', 'accessible']):
            return {
                'hardcover': 'Mid-range ($19.99-$24.99)',
                'paperback': 'Budget ($12.99-$16.99)',
                'ebook': 'Budget ($7.99-$11.99)'
            }
        else:
            return {
                'hardcover': 'Mid-range ($22.99-$27.99)',
                'paperback': 'Mid-range ($14.99-$18.99)',
                'ebook': 'Standard ($9.99-$13.99)'
            }
    
    def _select_rights_management(self, concept_text: str) -> List[str]:
        """Select rights management approach."""
        concept_lower = concept_text.lower()
        
        rights = ['World English rights', 'Digital rights']
        
        if any(word in concept_lower for word in ['international', 'global', 'worldwide']):
            rights.extend(['Translation rights', 'International distribution rights'])
        
        if any(word in concept_lower for word in ['audio', 'audiobook', 'podcast']):
            rights.append('Audio rights')
        
        if any(word in concept_lower for word in ['film', 'movie', 'adaptation', 'screen']):
            rights.append('Film/TV rights')
        
        return rights
    
    def _generate_operational_hybrid(self, concept_text: str) -> Dict[str, Any]:
        """Generate operational framework using rules + LLM."""
        
        # Rule-based workflow stages
        workflow_stages = VALID_OPTIONS['workflow_stages'].copy()
        
        # LLM for team structure and processes
        ops_prompt = f"""Based on this imprint concept, suggest operational details:

Concept: {concept_text}

Return ONLY valid JSON:
{{
    "technology_stack": ["4-6 essential tools/systems as strings"],
    "team_structure": {{
        "editorial": "Description of editorial team needs",
        "production": "Description of production team needs",
        "marketing": "Description of marketing team needs",
        "sales": "Description of sales team needs"
    }},
    "vendor_relationships": ["4-6 key vendor types as strings"],
    "quality_control_measures": "Description of quality control processes",
    "communication_protocols": "Description of team communication approach"
}}"""
        
        ops_result = self._call_llm_safe(ops_prompt)
        
        return {
            'workflow_stages': workflow_stages,
            'technology_stack': ops_result.get('technology_stack', [
                'Manuscript management system', 'Design software', 'Project management tools',
                'Distribution platform', 'Analytics tools', 'Communication platform'
            ]),
            'team_structure': ops_result.get('team_structure', {
                'editorial': 'Editorial Director, Senior Editor, Associate Editor',
                'production': 'Production Manager, Designer, Production Coordinator',
                'marketing': 'Marketing Director, Marketing Specialist',
                'sales': 'Sales Director, Sales Representative'
            }),
            'vendor_relationships': ops_result.get('vendor_relationships', [
                'Print-on-demand services', 'Freelance editors', 'Book distributors',
                'Marketing agencies', 'Translation services', 'Legal services'
            ]),
            'quality_control_measures': ops_result.get('quality_control_measures', 
                'Multi-stage editorial review, professional proofreading, and quality assurance checks'),
            'communication_protocols': ops_result.get('communication_protocols',
                'Weekly team meetings, monthly reviews, and quarterly planning sessions')
        }
    
    def _generate_marketing_hybrid(self, concept_text: str, target_audience: str) -> Dict[str, Any]:
        """Generate marketing approach using LLM + platform selection."""
        
        # Rule-based platform selection
        platforms = self._select_marketing_platforms(concept_text, target_audience)
        
        # LLM for strategy and tactics
        marketing_prompt = f"""Based on this imprint concept and audience, create marketing strategy:

Concept: {concept_text}
Target Audience: {target_audience}

Return ONLY valid JSON:
{{
    "promotional_activities": ["5-7 specific promotional activities as strings"],
    "audience_engagement_tactics": "Description of community building approach",
    "brand_partnerships": ["4-6 potential partnership types as strings"],
    "success_metrics": "How to measure marketing effectiveness"
}}"""
        
        marketing_result = self._call_llm_safe(marketing_prompt)
        
        # Rule-based budget allocation
        budget_allocation = self._calculate_budget_allocation(concept_text)
        
        return {
            'target_platforms': platforms,
            'promotional_activities': marketing_result.get('promotional_activities', [
                'Author reading events', 'Book club partnerships', 'Review campaigns',
                'Social media contests', 'Literary award submissions', 'Influencer collaborations'
            ]),
            'audience_engagement_tactics': marketing_result.get('audience_engagement_tactics',
                'Community building through social media, newsletters, and reader events'),
            'budget_allocation': budget_allocation,
            'brand_partnerships': marketing_result.get('brand_partnerships', [
                'Independent bookstores', 'Literary festivals', 'Reading groups',
                'Educational institutions', 'Cultural organizations'
            ]),
            'success_metrics': marketing_result.get('success_metrics',
                'Book sales, social media engagement, review coverage, and brand awareness')
        }
    
    def _select_marketing_platforms(self, concept_text: str, target_audience: str) -> List[str]:
        """Select marketing platforms based on concept and audience."""
        
        concept_lower = concept_text.lower()
        audience_lower = target_audience.lower()
        
        platforms = ['Goodreads']  # Always include
        
        # Age-based platform selection
        if any(word in audience_lower for word in ['young', 'teen', '16-25', 'ya', 'gen z']):
            platforms.extend(['TikTok', 'Instagram', 'YouTube'])
        elif any(word in audience_lower for word in ['adult', '25-45', 'millennial']):
            platforms.extend(['Instagram', 'Twitter/X', 'Facebook'])
        elif any(word in audience_lower for word in ['mature', '45+', 'boomer']):
            platforms.extend(['Facebook', 'Literary blogs'])
        
        # Genre-based additions
        if any(word in concept_lower for word in ['literary', 'academic', 'scholarly']):
            platforms.extend(['Literary blogs', 'Academic networks'])
        
        if any(word in concept_lower for word in ['popular', 'commercial', 'mainstream']):
            platforms.extend(['BookBub', 'NetGalley'])
        
        return list(set(platforms))  # Remove duplicates
    
    def _calculate_budget_allocation(self, concept_text: str) -> Dict[str, str]:
        """Calculate budget allocation based on concept."""
        
        concept_lower = concept_text.lower()
        
        if any(word in concept_lower for word in ['digital', 'online', 'social media']):
            return {
                'digital_ads': '40%',
                'influencer_marketing': '25%',
                'events': '15%',
                'PR': '15%',
                'content_marketing': '5%'
            }
        elif any(word in concept_lower for word in ['traditional', 'literary', 'academic']):
            return {
                'digital_ads': '25%',
                'influencer_marketing': '15%',
                'events': '30%',
                'PR': '25%',
                'content_marketing': '5%'
            }
        else:
            return {
                'digital_ads': '30%',
                'influencer_marketing': '20%',
                'events': '25%',
                'PR': '20%',
                'content_marketing': '5%'
            }
    
    def _generate_financial_hybrid(self, concept_text: str) -> Dict[str, Any]:
        """Generate financial projections using rules + LLM insights."""
        
        # Rule-based financial calculations
        financials = self._calculate_base_financials(concept_text)
        
        # LLM for strategic financial insights
        financial_prompt = f"""Based on this imprint concept, provide financial insights:

Concept: {concept_text}

Return ONLY valid JSON:
{{
    "funding_sources": ["3-5 potential funding sources as strings"],
    "expense_categories": ["5-7 main expense categories as strings"],
    "breakeven_point_analysis": "Realistic timeline and conditions for breakeven",
    "long_term_financial_goals": "Strategic financial objectives for growth"
}}"""
        
        financial_result = self._call_llm_safe(financial_prompt)
        
        return {
            'first_year_revenue_target': financials['revenue_target'],
            'profit_margin_goal': financials['profit_margin'],
            'investment_required': financials['investment_required'],
            'funding_sources': financial_result.get('funding_sources', [
                'Angel investors', 'Small business loans', 'Grants', 'Publisher partnerships'
            ]),
            'royalty_rates_structure': {
                'authors': '10-15% print, 25% digital',
                'agents': '15% commission'
            },
            'expense_categories': financial_result.get('expense_categories', [
                'Staff salaries', 'Editorial costs', 'Marketing', 'Technology',
                'Office expenses', 'Legal/professional services', 'Production costs'
            ]),
            'breakeven_point_analysis': financial_result.get('breakeven_point_analysis',
                'Expected breakeven within 18-24 months with consistent publication schedule'),
            'long_term_financial_goals': financial_result.get('long_term_financial_goals',
                'Achieve sustainable 20% profit margins and expand publication capacity')
        }
    
    def _calculate_base_financials(self, concept_text: str) -> Dict[str, Any]:
        """Calculate base financial projections using rules."""
        
        concept_lower = concept_text.lower()
        
        # Determine scale based on concept
        if any(word in concept_lower for word in ['8-12', '10-15', 'many books']):
            # Higher volume operation
            revenue_target = 750000
            investment_required = 400000
            profit_margin = 0.18
        elif any(word in concept_lower for word in ['4-6', '6-8', 'selective']):
            # Medium volume operation
            revenue_target = 500000
            investment_required = 250000
            profit_margin = 0.22
        elif any(word in concept_lower for word in ['1-3', 'few', 'boutique']):
            # Boutique operation
            revenue_target = 300000
            investment_required = 150000
            profit_margin = 0.25
        else:
            # Standard operation
            revenue_target = 500000
            investment_required = 250000
            profit_margin = 0.20
        
        # Adjust for market positioning
        if any(word in concept_lower for word in ['premium', 'luxury', 'high-end']):
            revenue_target = int(revenue_target * 1.3)
            profit_margin += 0.05
        elif any(word in concept_lower for word in ['budget', 'affordable']):
            revenue_target = int(revenue_target * 0.8)
            profit_margin -= 0.03
        
        return {
            'revenue_target': revenue_target,
            'investment_required': investment_required,
            'profit_margin': profit_margin
        }