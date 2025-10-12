"""
Social Security Agent - Stripped Down Version
Focuses on family situation, correspondence review, and deadline tracking
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
from .base_agent import PersistentAgent, Alert, AlertPriority, FamilyMember


class SocialSecurityAgent(PersistentAgent):
    """Social Security monitoring agent focused on correspondence and deadlines"""
    
    def __init__(self, db_path: str = 'daily_engine.db'):
        super().__init__("social_security", db_path)
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        base_url = "https://api.openai.com/v1/"
        print(f"Connecting to OpenAI API at {base_url}")
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        except Exception as e:
            print(f"Error connecting to OpenAI API: {str(e)}")
            self.client = None
    
    def monitor(self) -> List[Alert]:
        """Monitor for Social Security issues and deadlines"""
        alerts = []
        
        # Check for upcoming deadlines based on family member ages
        alerts.extend(self._check_age_based_deadlines())
        
        # Check for unprocessed correspondence
        alerts.extend(self._check_correspondence_deadlines())
        
        return alerts
    
    def _check_age_based_deadlines(self) -> List[Alert]:
        """Check for age-based Social Security deadlines"""
        alerts = []
        family_members = self.get_family_members()
        
        for member in family_members:
            if not member.birth_date:
                continue
                
            try:
                birth_date = datetime.strptime(member.birth_date, '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
                
                # Check for Medicare enrollment (age 65)
                if 64 <= age < 65:
                    days_to_65 = (birth_date.replace(year=birth_date.year + 65) - datetime.now()).days
                    if days_to_65 <= 90:  # 3 months before 65th birthday
                        alert = Alert(
                            agent_type=self.agent_type,
                            priority=AlertPriority.HIGH,
                            category="Medicare Enrollment",
                            title=f"Medicare Enrollment Deadline Approaching for {member.name}",
                            description=f"{member.name} will turn 65 in {days_to_65} days. Medicare enrollment should begin 3 months before their 65th birthday.",
                            action_required=True,
                            due_date=birth_date.replace(year=birth_date.year + 65) - timedelta(days=90),
                            family_member_ids=[member.id],
                            llm_reasoning="Medicare enrollment has specific timing requirements to avoid penalties.",
                            recommended_actions="1. Contact Social Security Administration\n2. Review Medicare plan options\n3. Consider supplemental insurance",
                            impact_assessment="Missing enrollment deadline could result in permanent premium penalties."
                        )
                        alerts.append(alert)
                
                # Check for Social Security eligibility (age 62)
                if 61 <= age < 62:
                    days_to_62 = (birth_date.replace(year=birth_date.year + 62) - datetime.now()).days
                    if days_to_62 <= 180:  # 6 months before 62nd birthday
                        alert = Alert(
                            agent_type=self.agent_type,
                            priority=AlertPriority.MEDIUM,
                            category="Social Security Eligibility",
                            title=f"Social Security Early Retirement Option for {member.name}",
                            description=f"{member.name} will be eligible for early Social Security benefits in {days_to_62} days.",
                            action_required=False,
                            due_date=birth_date.replace(year=birth_date.year + 62),
                            family_member_ids=[member.id],
                            llm_reasoning="Early retirement at 62 provides benefits but at a reduced rate.",
                            recommended_actions="1. Review benefit estimates\n2. Consider waiting until full retirement age\n3. Evaluate financial needs",
                            impact_assessment="Early claiming reduces benefits permanently but provides earlier income."
                        )
                        alerts.append(alert)
                        
            except ValueError:
                continue
        
        return alerts
    
    def _check_correspondence_deadlines(self) -> List[Alert]:
        """Check for deadlines in uploaded correspondence"""
        alerts = []
        
        # Get unprocessed documents
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, file_path, llm_summary, key_insights, action_items
            FROM agent_documents 
            WHERE agent_type = ? AND processed = 1
            AND (action_items IS NOT NULL AND action_items != '')
        ''', (self.agent_type,))
        
        for row in cursor.fetchall():
            doc_id, file_path, summary, insights, action_items = row
            
            # Parse action items for deadlines
            if action_items:
                deadlines = self._extract_deadlines_from_text(action_items)
                for deadline in deadlines:
                    alert = Alert(
                        agent_type=self.agent_type,
                        priority=AlertPriority.HIGH if deadline['urgent'] else AlertPriority.MEDIUM,
                        category="Correspondence Deadline",
                        title=f"Action Required: {deadline['action']}",
                        description=f"Based on correspondence analysis: {deadline['description']}",
                        action_required=True,
                        due_date=deadline['date'],
                        llm_reasoning=f"Extracted from document analysis: {summary}",
                        recommended_actions=action_items,
                        impact_assessment=deadline.get('impact', 'Potential loss of benefits or penalties')
                    )
                    alerts.append(alert)
        
        conn.close()
        return alerts
    
    def _extract_deadlines_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract deadline information from text"""
        deadlines = []
        
        # Simple regex patterns for common deadline phrases
        deadline_patterns = [
            r'(?:by|before|within)\s+(\d+)\s+days?',
            r'(?:by|before)\s+([A-Za-z]+\s+\d+,?\s+\d{4})',
            r'deadline\s+(?:is|of)\s+([A-Za-z]+\s+\d+,?\s+\d{4})',
            r'must\s+(?:respond|reply|act)\s+(?:by|within)\s+([A-Za-z]+\s+\d+,?\s+\d{4})'
        ]
        
        for pattern in deadline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                deadline_text = match.group(1)
                try:
                    # Try to parse the date
                    if deadline_text.isdigit():
                        # Days from now
                        deadline_date = datetime.now() + timedelta(days=int(deadline_text))
                    else:
                        # Try to parse date string
                        deadline_date = datetime.strptime(deadline_text, '%B %d, %Y')
                    
                    # Check if deadline is within next 90 days
                    days_until = (deadline_date - datetime.now()).days
                    if 0 <= days_until <= 90:
                        deadlines.append({
                            'action': 'Response Required',
                            'description': f'Deadline in {days_until} days',
                            'date': deadline_date,
                            'urgent': days_until <= 30,
                            'impact': 'Missing deadline may affect benefit eligibility'
                        })
                except ValueError:
                    continue
        
        return deadlines
    
    def process_correspondence(self, file_path: str, family_member_id: str = None) -> Dict[str, Any]:
        """Process Social Security correspondence using LLM"""
        if not self.client:
            return {'success': False, 'error': 'LLM client not available'}

        try:
            # Read the document - handle both PDF and text files
            if file_path.lower().endswith('.pdf'):
                # Use PyMuPDF to extract text from PDF
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    content = ""
                    for page in doc:
                        content += page.get_text()
                    doc.close()
                except ImportError:
                    return {'success': False, 'error': 'PyMuPDF not installed. Install with: pip install pymupdf'}
            else:
                # Text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
        except Exception as e:
            return {'success': False, 'error': f'Could not read file: {str(e)}'}

        # Analyze with LLM
        try:
            prompt = f"""
            Analyze this Social Security Administration correspondence and extract:
            
            1. SUMMARY: Brief summary of the document's purpose
            2. KEY_INSIGHTS: Important information or changes
            3. ACTION_ITEMS: Any required actions with deadlines
            4. DEADLINES: Specific dates mentioned
            5. IMPACT: How this affects the recipient's benefits
            
            Document content:
            {content[:4000]}  # Limit content to avoid token limits
            
            Format your response as:
            SUMMARY: [summary]
            KEY_INSIGHTS: [insights]
            ACTION_ITEMS: [actions]
            DEADLINES: [deadlines]
            IMPACT: [impact]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing Social Security Administration correspondence and identifying important deadlines and actions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            # Parse the structured response
            sections = {}
            current_section = None
            for line in analysis.split('\n'):
                if line.startswith(('SUMMARY:', 'KEY_INSIGHTS:', 'ACTION_ITEMS:', 'DEADLINES:', 'IMPACT:')):
                    current_section = line.split(':', 1)[0].lower()
                    sections[current_section] = line.split(':', 1)[1].strip()
                elif current_section and line.strip():
                    sections[current_section] += '\n' + line.strip()
            
            # Save to database
            doc_id = self._save_document_analysis(file_path, family_member_id, sections)
            
            return {
                'success': True,
                'document_id': doc_id,
                'analysis': sections
            }
            
        except Exception as e:
            return {'success': False, 'error': f'LLM analysis failed: {str(e)}'}
    
    def _save_document_analysis(self, file_path: str, family_member_id: str, analysis: Dict[str, str]) -> str:
        """Save document analysis to database"""
        import uuid
        
        doc_id = str(uuid.uuid4())
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_documents (
                id, agent_type, document_type, file_path, family_member_id,
                processed, llm_summary, key_insights, action_items, processing_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id, self.agent_type, 'correspondence', file_path, family_member_id,
            True, analysis.get('summary', ''), analysis.get('key_insights', ''),
            analysis.get('action_items', ''), analysis.get('impact', '')
        ))
        
        conn.commit()
        conn.close()
        
        return doc_id
    
    def _get_db_connection(self):
        """Get database connection"""
        import sqlite3
        return sqlite3.connect(self.db_path)
    
    def get_family_situation_summary(self) -> Dict[str, Any]:
        """Get summary of family situation for Social Security planning"""
        family_members = self.get_family_members()
        
        summary = {
            'total_members': len(family_members),
            'members_by_relationship': {},
            'upcoming_milestones': [],
            'benefit_eligible': 0
        }
        
        for member in family_members:
            # Count by relationship
            rel = member.relationship
            summary['members_by_relationship'][rel] = summary['members_by_relationship'].get(rel, 0) + 1
            
            # Check for upcoming milestones
            if member.birth_date:
                try:
                    birth_date = datetime.strptime(member.birth_date, '%Y-%m-%d')
                    age = (datetime.now() - birth_date).days // 365
                    
                    if age >= 62:
                        summary['benefit_eligible'] += 1
                    
                    # Check for upcoming milestones
                    milestones = [
                        (62, 'Social Security Early Retirement'),
                        (65, 'Medicare Eligibility'),
                        (67, 'Full Retirement Age')  # Simplified - actual FRA varies by birth year
                    ]
                    
                    for milestone_age, milestone_name in milestones:
                        if age < milestone_age:
                            milestone_date = birth_date.replace(year=birth_date.year + milestone_age)
                            days_until = (milestone_date - datetime.now()).days
                            if days_until <= 365:  # Within next year
                                summary['upcoming_milestones'].append({
                                    'member_name': member.name,
                                    'milestone': milestone_name,
                                    'date': milestone_date.strftime('%Y-%m-%d'),
                                    'days_until': days_until
                                })
                            break  # Only add the next milestone
                            
                except ValueError:
                    continue
        
        return summary
    
    def generate_expert_overview(self) -> Dict[str, Any]:
        """Generate comprehensive expert overview of family's Social Security situation"""
        if not self.client:
            return {'success': False, 'error': 'LLM client not available'}
        
        try:
            # Get compressed family data
            family_data = self._get_compressed_family_data()
            st.write(family_data)
            # Create expert prompt
            prompt = f"""
You are a Social Security Administration expert advisor. Here is information about the Social Security holder's family and situation:

{family_data}

Analyze this family's situation and provide a comprehensive overview with specific, actionable recommendations.

**FORMATTING REQUIREMENTS:**
- Use proper markdown structure with headers, subheaders, and bullet points
- Break content into digestible chunks - NO paragraphs longer than 3-4 sentences
- Use bullet points extensively for lists and recommendations
- Use subheadings to organize advice by family member
- Include clear action items with specific deadlines where applicable
- Use bold text for emphasis on key terms and amounts
- No emojis.  Only LaTex supported characters.

**CONTENT STRUCTURE:**
Return your analysis in exactly this format:

## Situation Overview
[Brief 2-3 sentence summary, then bullet points for key facts]

## Key Opportunities  
### [Family Member Name] ([age], [status])
- [Specific opportunity 1]
- [Specific opportunity 2]

### [Next Family Member]
- [Opportunities for this member]

##  Immediate Actions
- [ ] **[Action item]**
  - [Specific steps]
  - [Timeline/deadline]
- [ ] **[Next action]**
  - [Details]

## Long-Term Strategy
- **[Strategy area]**: [Brief description]
  - [Specific step 1]
  - [Specific step 2]
- **[Next strategy area]**: [Description]

##  Risk Assessment  
- **[Risk type]**: [Brief description of risk]
  - Mitigation: [How to address it]
- **[Next risk]**: [Description]

## Questions to Consider
- [Specific question that needs answering]?
- [Next important question]?
- [Follow-up question]?

**RULES:**
- Maximum 3 sentences per paragraph before using bullet points
- Every recommendation must be specific and actionable
- Include dollar amounts, timeframes, and specific SSA forms when relevant
- Use checkboxes [ ] for action items
- Use ⇒ for emphasis
- Bold all important terms, deadlines, and dollar amounts
"""
            
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are an expert Social Security Administration advisor with deep knowledge of benefits, claiming strategies, Medicare coordination, and family benefit optimization."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=16000
            )
            st.write(response.choices[0])
            analysis = response.choices[0].message.content
            st.write(analysis)
            # Parse the structured response
            sections = {}
            current_section = None
            current_content = []
            
            for line in analysis.split('\n'):
                line = line.strip()
                if line.endswith(':') and line.replace(':', '').replace(' ', '_').upper() in [
                    'SITUATION_OVERVIEW', 'KEY_OPPORTUNITIES', 'IMMEDIATE_ACTIONS', 
                    'LONG_TERM_STRATEGY', 'RISK_ASSESSMENT', 'QUESTIONS_TO_CONSIDER'
                ]:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = line.replace(':', '').replace(' ', '_').lower()
                    current_content = []
                elif line and current_section:
                    current_content.append(line)
            
            # Add the last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            return {
                'success': True,
                'overview': sections,
                'raw_analysis': analysis,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Expert analysis failed: {str(e)}'}

    def _prepare_markdown_for_pdf(self, markdown_content: str) -> str:
        """Replace emojis with text equivalents for better PDF rendering"""
        emoji_replacements = {
            '📋': '**[CHECKLIST]**',
            '💡': '**[IDEA]**',
            '⚡': '**[ACTION]**',
            '⚠️': '**[WARNING]**',
            '❓': '**[QUESTION]**',
            '📈': '**[STRATEGY]**',
            '💰': '**[REVENUE]**',
            '🎯': '**[GOALS]**',
            '🚀': '**[PROJECTS]**',
        }

        for emoji, replacement in emoji_replacements.items():
            markdown_content = markdown_content.replace(emoji, replacement)

        return markdown_content

    def _get_compressed_family_data(self) -> str:
        """Get compressed family data for LLM analysis"""
        family_members = self.get_family_members()
        
        # Get recent alerts for context
        recent_alerts = self.get_active_alerts()
        
        # Get recent document insights
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT llm_summary, key_insights, action_items
            FROM agent_documents 
            WHERE agent_type = ? AND processed = 1
            ORDER BY processed_at DESC
            LIMIT 3
        ''', (self.agent_type,))
        recent_docs = cursor.fetchall()
        conn.close()
        
        # Build compressed data structure
        compressed_data = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'family_members': [],
            'recent_alerts': [],
            'recent_correspondence': []
        }
        
        # Compress family member data
        for member in family_members:
            age = None
            if member.birth_date:
                try:
                    birth_date = datetime.strptime(member.birth_date, '%Y-%m-%d')
                    age = (datetime.now() - birth_date).days // 365
                except ValueError:
                    pass
            
            member_data = {
                'name': member.name,
                'relationship': member.relationship,
                'age': age,
                'employment_status': member.employment_status,
                'key_context': []
            }
            
            # Add key context (non-empty fields)
            if member.personal_notes:
                member_data['key_context'].append(f"Notes: {member.personal_notes[:200]}")
            if member.health_context:
                member_data['key_context'].append(f"Health: {member.health_context[:200]}")
            if member.financial_context:
                member_data['key_context'].append(f"Financial: {member.financial_context[:200]}")
            
            compressed_data['family_members'].append(member_data)
        
        # Compress recent alerts
        for alert in recent_alerts[:5]:  # Last 5 alerts
            compressed_data['recent_alerts'].append({
                'title': alert.title,
                'category': alert.category,
                'priority': alert.priority.value,
                'description': alert.description[:300]
            })
        
        # Compress recent correspondence
        for doc in recent_docs:
            if doc[0] or doc[1]:  # Has summary or insights
                compressed_data['recent_correspondence'].append({
                    'summary': doc[0][:200] if doc[0] else '',
                    'insights': doc[1][:200] if doc[1] else '',
                    'actions': doc[2][:200] if doc[2] else ''
                })
        
        # Convert to readable string format
        data_str = f"""
FAMILY COMPOSITION:
"""
        for member in compressed_data['family_members']:
            data_str += f"- {member['name']} ({member['relationship']}, age {member['age'] or 'unknown'}, {member['employment_status']})\n"
            for context in member['key_context']:
                data_str += f"  * {context}\n"
        
        if compressed_data['recent_alerts']:
            data_str += f"\nRECENT ALERTS:\n"
            for alert in compressed_data['recent_alerts']:
                data_str += f"- {alert['priority'].upper()}: {alert['title']} - {alert['description']}\n"
        
        if compressed_data['recent_correspondence']:
            data_str += f"\nRECENT CORRESPONDENCE ANALYSIS:\n"
            for i, doc in enumerate(compressed_data['recent_correspondence'], 1):
                data_str += f"Document {i}:\n"
                if doc['summary']:
                    data_str += f"  Summary: {doc['summary']}\n"
                if doc['insights']:
                    data_str += f"  Insights: {doc['insights']}\n"
                if doc['actions']:
                    data_str += f"  Actions: {doc['actions']}\n"
        
        return data_str
    
    def generate_overview_pdf(self, analysis, output_path: str = None) -> Dict[str, Any]:
        """Generate PDF report from expert overview data"""
        # Use pandoc as the primary PDF generation method
        return self._generate_pandoc_pdf(analysis, output_path)

    def _generate_text_report(self, overview_data: Dict[str, Any], output_path: str = None) -> Dict[str, Any]:
        """Generate text report as final fallback"""
        try:
            # Create output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"social_security_overview_{timestamp}.txt"
            
            gen_date = datetime.fromisoformat(overview_data['generated_at']).strftime('%B %d, %Y at %I:%M %p')
            
            content = f"""
SOCIAL SECURITY EXPERT OVERVIEW
===============================

Generated: {gen_date}

"""
            
            # Add sections
            sections = overview_data['overview']
            section_titles = {
                'situation_overview': 'SITUATION OVERVIEW',
                'key_opportunities': 'KEY OPPORTUNITIES',
                'immediate_actions': 'IMMEDIATE ACTIONS',
                'long_term_strategy': 'LONG-TERM STRATEGY',
                'risk_assessment': 'RISK ASSESSMENT',
                'questions_to_consider': 'QUESTIONS TO CONSIDER'
            }
            
            for section_key, section_content in sections.items():
                if section_content and section_content.strip():
                    title = section_titles.get(section_key, section_key.replace('_', ' ').upper())
                    content += f"""
{title}
{'-' * len(title)}

{section_content}

"""
            
            # Add disclaimer
            content += """
DISCLAIMER
----------

This analysis is generated by AI and is for informational purposes only. 
It should not be considered as official Social Security Administration guidance or professional 
financial advice. Please consult with the Social Security Administration or a qualified 
financial advisor for official guidance on your specific situation. Social Security rules 
and regulations may change, and individual circumstances may affect benefit calculations.
"""
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': output_path,
                'file_size': os.path.getsize(output_path),
                'format': 'text'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Text report generation failed: {str(e)}'
            }

    def _generate_pandoc_pdf(self, analysis, output_path: str = None) -> Dict[str, Any]:
        """Generate PDF using pandoc from markdown text"""
        try:
            import subprocess
            import tempfile

            markdown_content = self._generate_markdown_report(analysis)
            #markdown_content = self._prepare_markdown_for_pdf(markdown_content)

            # save analysis to temp file
            temp_md_path = os.path.join(tempfile.gettempdir(), 'social_security_overview.md')
            with open(temp_md_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_markdown_report(markdown_content))
            st.write(temp_md_path)
            # Create output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"social_security_overview_{timestamp}.pdf"

            try:

                pandoc_cmd = [
                    'pandoc',
                    temp_md_path,
                    '-o', output_path,
                    '--pdf-engine=xelatex',
                    '--variable', 'geometry:margin=1in',
                    '--variable', 'fontsize=11pt',
                    '--variable', 'linestretch=1.2',  # Make sure this is separate
                    '--toc',  # This should be separate
                    '--toc-depth=2',
                    '--highlight-style=tango',
                    '--verbose'
                ]

                st.write(pandoc_cmd)
                result = subprocess.run(pandoc_cmd, capture_output=True, text=True, timeout=30)
              #  st.write(result)

                if result.returncode == 0:
                    return {
                        'success': True,
                        'file_path': output_path,
                        'file_size': os.path.getsize(output_path)
                    }
                else:
                    st.write(result.stderr)

                    return {
                        'success': False,
                        'error': f'Pandoc conversion failed: {result.stderr}'
                    }

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_md_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Pandoc conversion timed out'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Pandoc not found. Please install pandoc: https://pandoc.org/installing.html'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Pandoc PDF generation failed: {str(e)}'
            }
    
    def _generate_markdown_report(self, analysis):
        """Generate markdown report content for pandoc conversion"""
        gen_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        markdown = f"""---
title: "Social Security Expert Overview"
author: "AI Financial Analysis"
date: "{gen_date}"
geometry: margin=1in
fontsize: 11pt
linestretch: 1.2
mainfont: "Adobe Caslon Pro"
sansfont: "Futura"
monofont: "Source Code Pro"
---

# Social Security Expert Overview

**Generated:** {gen_date}

---

{analysis}

## Disclaimer

**IMPORTANT:** This analysis is generated by AI and is for informational purposes only. It should not be considered as official Social Security Administration guidance or professional financial advice. 

Please consult with the Social Security Administration or a qualified financial advisor for official guidance on your specific situation. Social Security rules and regulations may change, and individual circumstances may affect benefit calculations.

---

*This report was generated using AI analysis of your family's Social Security situation and should be used as a starting point for further research and professional consultation.*
"""
        
        return markdown
    
