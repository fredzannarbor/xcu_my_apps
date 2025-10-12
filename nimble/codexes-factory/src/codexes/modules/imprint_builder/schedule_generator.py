"""
Prepress workflow and schedule generation system for imprints.
"""

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

from .imprint_expander import ExpandedImprint
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class BookSchedule:
    """Schedule for a single book production."""
    book_id: str
    title: str
    author: str
    imprint_name: str
    genre: str
    target_audience: str
    estimated_word_count: int
    priority: str  # 'high', 'medium', 'low'
    
    # Timeline
    start_date: datetime
    manuscript_deadline: datetime
    editing_deadline: datetime
    design_deadline: datetime
    production_deadline: datetime
    publication_date: datetime
    
    # Workflow stages
    workflow_stages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Resources
    assigned_editor: str = ""
    assigned_designer: str = ""
    assigned_proofreader: str = ""
    
    # Status tracking
    current_stage: str = "planning"
    completion_percentage: float = 0.0
    notes: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'book_id': self.book_id,
            'title': self.title,
            'author': self.author,
            'imprint_name': self.imprint_name,
            'genre': self.genre,
            'target_audience': self.target_audience,
            'estimated_word_count': self.estimated_word_count,
            'priority': self.priority,
            'start_date': self.start_date.isoformat(),
            'manuscript_deadline': self.manuscript_deadline.isoformat(),
            'editing_deadline': self.editing_deadline.isoformat(),
            'design_deadline': self.design_deadline.isoformat(),
            'production_deadline': self.production_deadline.isoformat(),
            'publication_date': self.publication_date.isoformat(),
            'workflow_stages': self.workflow_stages,
            'assigned_editor': self.assigned_editor,
            'assigned_designer': self.assigned_designer,
            'assigned_proofreader': self.assigned_proofreader,
            'current_stage': self.current_stage,
            'completion_percentage': self.completion_percentage,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ImprintScheduleGenerator:
    """Generates production schedules and book ideas for imprints."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load scheduling templates and configurations
        self.workflow_templates = self._load_workflow_templates()
        self.timeline_templates = self._load_timeline_templates()

    def generate_initial_schedule(self, imprint: ExpandedImprint, 
                                num_books: int = 12, 
                                planning_horizon_months: int = 18) -> List[BookSchedule]:
        """Generate initial book schedule for an imprint."""
        try:
            self.logger.info(f"Generating initial schedule for {imprint.branding.imprint_name}")
            
            schedules = []
            
            # Generate book ideas aligned with imprint
            book_ideas = self._generate_book_ideas(imprint, num_books)
            
            # Create schedules for each book
            start_date = datetime.now()
            
            for i, book_idea in enumerate(book_ideas):
                # Stagger book starts
                book_start = start_date + timedelta(weeks=i * 6)  # Start new book every 6 weeks
                
                schedule = self._create_book_schedule(
                    imprint=imprint,
                    book_idea=book_idea,
                    start_date=book_start,
                    priority=self._determine_priority(book_idea, i)
                )
                
                schedules.append(schedule)
            
            # Optimize schedule for resource conflicts
            optimized_schedules = self._optimize_schedule(schedules)
            
            self.logger.info(f"Generated {len(optimized_schedules)} book schedules")
            return optimized_schedules
            
        except Exception as e:
            self.logger.error(f"Error generating initial schedule: {e}")
            return []

    def generate_workflow_config(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate prepress workflow configuration."""
        try:
            workflow_config = {
                'imprint_name': imprint.branding.imprint_name,
                'workflow_stages': self._generate_workflow_stages(imprint),
                'quality_gates': self._generate_quality_gates(imprint),
                'resource_requirements': self._generate_resource_requirements(imprint),
                'automation_rules': self._generate_automation_rules(imprint),
                'escalation_procedures': self._generate_escalation_procedures(imprint),
                'generated_at': datetime.now().isoformat()
            }
            
            return workflow_config
            
        except Exception as e:
            self.logger.error(f"Error generating workflow config: {e}")
            return {}

    def suggest_codex_types(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Suggest new codex types aligned with imprint themes."""
        try:
            prompt = f"""
            Based on this imprint profile, suggest 5 innovative codex types (book formats/structures):
            
            Imprint: {imprint.branding.imprint_name}
            Mission: {imprint.branding.mission_statement}
            Genres: {', '.join(imprint.publishing.primary_genres)}
            Audience: {imprint.publishing.target_audience}
            Brand Voice: {imprint.branding.brand_voice}
            
            For each codex type, provide:
            - Name and description
            - Target use case
            - Unique features
            - Market potential
            - Production considerations
            
            Focus on innovative formats that align with the imprint's mission and audience.
            """
            
            response = self.llm_caller.call_model_with_prompt(
                model_name="mistral",
                prompt_config={"prompt": prompt},
                response_format_type="json"
            )
            
            if response and response.get('parsed_content'):
                return response['parsed_content'].get('codex_types', [])
            
        except Exception as e:
            self.logger.error(f"Error suggesting codex types: {e}")
        
        return self._get_default_codex_types(imprint)

    def create_publication_timeline(self, imprint: ExpandedImprint, 
                                  target_books_per_year: int = 12) -> Dict[str, Any]:
        """Create publication timeline and milestones."""
        try:
            timeline = {
                'imprint_name': imprint.branding.imprint_name,
                'target_books_per_year': target_books_per_year,
                'publication_frequency': self._calculate_publication_frequency(target_books_per_year),
                'seasonal_strategy': self._generate_seasonal_strategy(imprint),
                'milestone_calendar': self._generate_milestone_calendar(target_books_per_year),
                'resource_planning': self._generate_resource_planning(imprint, target_books_per_year),
                'risk_mitigation': self._generate_risk_mitigation_plan(imprint),
                'generated_at': datetime.now().isoformat()
            }
            
            return timeline
            
        except Exception as e:
            self.logger.error(f"Error creating publication timeline: {e}")
            return {}

    def _generate_book_ideas(self, imprint: ExpandedImprint, num_books: int) -> List[Dict[str, Any]]:
        """Generate book ideas aligned with imprint themes."""
        try:
            prompt = f"""
            Generate {num_books} book ideas for {imprint.branding.imprint_name}:
            
            Imprint Focus: {', '.join(imprint.publishing.primary_genres)}
            Target Audience: {imprint.publishing.target_audience}
            Brand Mission: {imprint.branding.mission_statement}
            Brand Voice: {imprint.branding.brand_voice}
            
            For each book, provide:
            - Title
            - Author (fictional but realistic)
            - Genre
            - Brief description (2-3 sentences)
            - Estimated word count
            - Target audience
            - Market appeal
            - Unique selling points
            
            Ensure variety while maintaining alignment with the imprint's focus.
            """
            
            response = self.llm_caller.call_model_with_prompt(
                model_name="mistral",
                prompt_config={"prompt": prompt},
                response_format_type="json"
            )
            
            if response and response.get('parsed_content'):
                return response['parsed_content'].get('book_ideas', [])
            
        except Exception as e:
            self.logger.error(f"Error generating book ideas: {e}")
        
        return self._get_default_book_ideas(imprint, num_books)

    def _create_book_schedule(self, imprint: ExpandedImprint, book_idea: Dict[str, Any], 
                            start_date: datetime, priority: str) -> BookSchedule:
        """Create a schedule for a single book."""
        
        # Calculate timeline based on word count and complexity
        word_count = book_idea.get('estimated_word_count', 80000)
        timeline_weeks = self._calculate_production_timeline(word_count, priority)
        
        # Create milestone dates
        manuscript_deadline = start_date + timedelta(weeks=timeline_weeks['manuscript'])
        editing_deadline = manuscript_deadline + timedelta(weeks=timeline_weeks['editing'])
        design_deadline = editing_deadline + timedelta(weeks=timeline_weeks['design'])
        production_deadline = design_deadline + timedelta(weeks=timeline_weeks['production'])
        publication_date = production_deadline + timedelta(weeks=timeline_weeks['distribution'])
        
        # Generate workflow stages
        workflow_stages = self._generate_book_workflow_stages(imprint, book_idea)
        
        schedule = BookSchedule(
            book_id=str(uuid.uuid4()),
            title=book_idea.get('title', 'Untitled'),
            author=book_idea.get('author', 'Unknown Author'),
            imprint_name=imprint.branding.imprint_name,
            genre=book_idea.get('genre', imprint.publishing.primary_genres[0] if imprint.publishing.primary_genres else 'General'),
            target_audience=book_idea.get('target_audience', imprint.publishing.target_audience),
            estimated_word_count=word_count,
            priority=priority,
            start_date=start_date,
            manuscript_deadline=manuscript_deadline,
            editing_deadline=editing_deadline,
            design_deadline=design_deadline,
            production_deadline=production_deadline,
            publication_date=publication_date,
            workflow_stages=workflow_stages
        )
        
        return schedule

    def _determine_priority(self, book_idea: Dict[str, Any], index: int) -> str:
        """Determine book priority based on market appeal and position."""
        market_appeal = book_idea.get('market_appeal', 'medium')
        
        if index < 3:  # First 3 books are high priority
            return 'high'
        elif market_appeal == 'high' or 'bestseller' in book_idea.get('description', '').lower():
            return 'high'
        elif index > 8:  # Later books are lower priority
            return 'low'
        else:
            return 'medium'

    def _calculate_production_timeline(self, word_count: int, priority: str) -> Dict[str, int]:
        """Calculate production timeline in weeks."""
        base_timeline = {
            'manuscript': 8,
            'editing': 4,
            'design': 2,
            'production': 2,
            'distribution': 1
        }
        
        # Adjust for word count
        if word_count > 100000:
            base_timeline['manuscript'] += 4
            base_timeline['editing'] += 2
        elif word_count < 50000:
            base_timeline['manuscript'] -= 2
            base_timeline['editing'] -= 1
        
        # Adjust for priority
        if priority == 'high':
            # Compress timeline for high priority
            for stage in base_timeline:
                base_timeline[stage] = max(1, int(base_timeline[stage] * 0.8))
        elif priority == 'low':
            # Extend timeline for low priority
            for stage in base_timeline:
                base_timeline[stage] = int(base_timeline[stage] * 1.2)
        
        return base_timeline

    def _generate_workflow_stages(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Generate workflow stages for the imprint."""
        stages = []
        
        # Use imprint's production workflow or default
        stage_names = imprint.production.workflow_stages or [
            'Manuscript Intake', 'Content Review', 'Developmental Editing',
            'Copy Editing', 'Design & Layout', 'Proofreading',
            'Final Review', 'Production', 'Distribution'
        ]
        
        for i, stage_name in enumerate(stage_names):
            stage = {
                'name': stage_name,
                'order': i + 1,
                'description': self._get_stage_description(stage_name),
                'estimated_duration_days': self._get_stage_duration(stage_name),
                'required_roles': self._get_stage_roles(stage_name),
                'quality_gates': self._get_stage_quality_gates(stage_name, imprint),
                'deliverables': self._get_stage_deliverables(stage_name)
            }
            stages.append(stage)
        
        return stages

    def _generate_book_workflow_stages(self, imprint: ExpandedImprint, 
                                     book_idea: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate workflow stages for a specific book."""
        base_stages = self._generate_workflow_stages(imprint)
        
        # Customize stages based on book characteristics
        word_count = book_idea.get('estimated_word_count', 80000)
        genre = book_idea.get('genre', 'General')
        
        # Adjust durations based on book specifics
        for stage in base_stages:
            if stage['name'] == 'Developmental Editing' and word_count > 100000:
                stage['estimated_duration_days'] += 7
            elif stage['name'] == 'Design & Layout' and genre in ['Art', 'Photography', 'Children']:
                stage['estimated_duration_days'] += 5
        
        return base_stages

    def _optimize_schedule(self, schedules: List[BookSchedule]) -> List[BookSchedule]:
        """Optimize schedule to avoid resource conflicts."""
        # Sort by priority and start date
        schedules.sort(key=lambda x: (x.priority != 'high', x.start_date))
        
        # Track resource usage
        editor_schedule = {}
        designer_schedule = {}
        
        for schedule in schedules:
            # Assign resources and adjust dates if conflicts
            schedule = self._assign_resources(schedule, editor_schedule, designer_schedule)
        
        return schedules

    def _assign_resources(self, schedule: BookSchedule, 
                         editor_schedule: Dict, designer_schedule: Dict) -> BookSchedule:
        """Assign resources and adjust timeline if needed."""
        # Simple resource assignment (in practice, this would be more sophisticated)
        available_editors = ['Editor A', 'Editor B', 'Editor C']
        available_designers = ['Designer X', 'Designer Y']
        
        # Find available editor
        for editor in available_editors:
            if self._is_resource_available(editor, schedule.editing_deadline, 
                                         schedule.design_deadline, editor_schedule):
                schedule.assigned_editor = editor
                editor_schedule[editor] = schedule.editing_deadline
                break
        
        # Find available designer
        for designer in available_designers:
            if self._is_resource_available(designer, schedule.design_deadline, 
                                         schedule.production_deadline, designer_schedule):
                schedule.assigned_designer = designer
                designer_schedule[designer] = schedule.design_deadline
                break
        
        return schedule

    def _is_resource_available(self, resource: str, start_date: datetime, 
                             end_date: datetime, schedule: Dict) -> bool:
        """Check if resource is available during the specified period."""
        if resource not in schedule:
            return True
        
        # Simple availability check (in practice, this would be more sophisticated)
        return schedule[resource] < start_date

    def _generate_quality_gates(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Generate quality gates for the workflow."""
        quality_standards = imprint.production.quality_standards
        
        gates = [
            {
                'name': 'Manuscript Quality Gate',
                'stage': 'Content Review',
                'criteria': [
                    'Content aligns with imprint mission',
                    'Target audience appropriateness',
                    'Brand voice consistency',
                    'Minimum quality threshold met'
                ],
                'required_approvers': ['Content Editor', 'Editorial Director'],
                'escalation_threshold_days': 3
            },
            {
                'name': 'Editorial Quality Gate',
                'stage': 'Copy Editing',
                'criteria': [
                    'Grammar and style consistency',
                    'Fact-checking completed',
                    'Brand guidelines compliance',
                    'Readability standards met'
                ],
                'required_approvers': ['Copy Editor', 'Senior Editor'],
                'escalation_threshold_days': 2
            },
            {
                'name': 'Design Quality Gate',
                'stage': 'Design & Layout',
                'criteria': [
                    'Brand visual identity compliance',
                    'Typography standards met',
                    'Layout consistency',
                    'Print production requirements met'
                ],
                'required_approvers': ['Designer', 'Art Director'],
                'escalation_threshold_days': 2
            },
            {
                'name': 'Production Quality Gate',
                'stage': 'Final Review',
                'criteria': [
                    'All previous quality gates passed',
                    'Final proofreading completed',
                    'Metadata accuracy verified',
                    'Distribution requirements met'
                ],
                'required_approvers': ['Production Manager', 'Publisher'],
                'escalation_threshold_days': 1
            }
        ]
        
        return gates

    def _generate_resource_requirements(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate resource requirements for the imprint."""
        return {
            'editorial_team': {
                'content_editors': 2,
                'copy_editors': 2,
                'proofreaders': 1,
                'editorial_director': 1
            },
            'design_team': {
                'book_designers': 2,
                'cover_designers': 1,
                'art_director': 1
            },
            'production_team': {
                'production_manager': 1,
                'quality_assurance': 1
            },
            'technology_requirements': {
                'design_software': ['Adobe InDesign', 'Adobe Photoshop', 'Adobe Illustrator'],
                'editorial_tools': ['Track Changes', 'Grammarly', 'Style Guide Software'],
                'project_management': ['Project Management Software', 'Calendar System']
            },
            'external_resources': {
                'freelance_editors': 'As needed for overflow',
                'freelance_designers': 'As needed for specialized projects',
                'printing_partners': 'Print-on-demand and offset printing'
            }
        }

    def _generate_automation_rules(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Generate automation rules for the workflow."""
        automation_settings = imprint.production.automation_settings
        
        rules = []
        
        if automation_settings.get('auto_formatting', False):
            rules.append({
                'name': 'Auto-formatting',
                'trigger': 'Manuscript upload',
                'action': 'Apply standard formatting templates',
                'conditions': ['File format is supported', 'Content passes basic validation']
            })
        
        if automation_settings.get('auto_validation', False):
            rules.append({
                'name': 'Auto-validation',
                'trigger': 'Stage completion',
                'action': 'Run automated quality checks',
                'conditions': ['All deliverables present', 'Previous stage approved']
            })
        
        rules.append({
            'name': 'Deadline notifications',
            'trigger': 'Approaching deadline',
            'action': 'Send notification to assigned team members',
            'conditions': ['3 days before deadline', 'Task not marked complete']
        })
        
        rules.append({
            'name': 'Escalation trigger',
            'trigger': 'Missed deadline',
            'action': 'Escalate to supervisor',
            'conditions': ['Deadline passed', 'No extension approved']
        })
        
        return rules

    def _generate_escalation_procedures(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Generate escalation procedures."""
        return [
            {
                'level': 1,
                'trigger': 'Task overdue by 1 day',
                'action': 'Notify team lead',
                'responsible_party': 'Project Manager'
            },
            {
                'level': 2,
                'trigger': 'Task overdue by 3 days',
                'action': 'Escalate to department head',
                'responsible_party': 'Editorial Director'
            },
            {
                'level': 3,
                'trigger': 'Critical path impact',
                'action': 'Executive review and resource reallocation',
                'responsible_party': 'Publisher'
            }
        ]

    def _calculate_publication_frequency(self, target_books_per_year: int) -> str:
        """Calculate publication frequency description."""
        if target_books_per_year >= 24:
            return "Bi-weekly releases"
        elif target_books_per_year >= 12:
            return "Monthly releases"
        elif target_books_per_year >= 6:
            return "Bi-monthly releases"
        elif target_books_per_year >= 4:
            return "Quarterly releases"
        else:
            return "Irregular releases"

    def _generate_seasonal_strategy(self, imprint: ExpandedImprint) -> Dict[str, Any]:
        """Generate seasonal publication strategy."""
        genres = imprint.publishing.primary_genres
        
        strategy = {
            'spring': {
                'focus': 'New releases and fresh content',
                'recommended_genres': ['Self-help', 'Business', 'Health'],
                'marketing_themes': ['New beginnings', 'Growth', 'Renewal']
            },
            'summer': {
                'focus': 'Light reading and entertainment',
                'recommended_genres': ['Fiction', 'Travel', 'Romance'],
                'marketing_themes': ['Vacation reading', 'Relaxation', 'Adventure']
            },
            'fall': {
                'focus': 'Educational and serious content',
                'recommended_genres': ['Academic', 'Biography', 'History'],
                'marketing_themes': ['Learning', 'Preparation', 'Reflection']
            },
            'winter': {
                'focus': 'Gift books and holiday themes',
                'recommended_genres': ['Art', 'Cooking', 'Inspirational'],
                'marketing_themes': ['Gifts', 'Comfort', 'Celebration']
            }
        }
        
        return strategy

    def _generate_milestone_calendar(self, target_books_per_year: int) -> List[Dict[str, Any]]:
        """Generate milestone calendar for the year."""
        milestones = []
        
        # Quarterly reviews
        for quarter in range(1, 5):
            milestones.append({
                'name': f'Q{quarter} Review',
                'type': 'review',
                'month': quarter * 3,
                'description': f'Quarterly performance and pipeline review',
                'deliverables': ['Performance report', 'Pipeline status', 'Resource planning']
            })
        
        # Publication milestones
        books_per_quarter = target_books_per_year // 4
        for quarter in range(1, 5):
            milestones.append({
                'name': f'Q{quarter} Publications',
                'type': 'publication',
                'month': quarter * 3,
                'description': f'Target: {books_per_quarter} books published',
                'deliverables': ['Published books', 'Marketing campaigns', 'Sales reports']
            })
        
        return milestones

    def _generate_resource_planning(self, imprint: ExpandedImprint, 
                                  target_books_per_year: int) -> Dict[str, Any]:
        """Generate resource planning recommendations."""
        return {
            'staffing_recommendations': {
                'editors_needed': max(2, target_books_per_year // 8),
                'designers_needed': max(1, target_books_per_year // 12),
                'project_managers_needed': max(1, target_books_per_year // 15)
            },
            'capacity_planning': {
                'books_per_editor_per_year': 8,
                'books_per_designer_per_year': 12,
                'peak_capacity_months': ['March', 'September', 'November'],
                'low_capacity_months': ['January', 'July', 'December']
            },
            'budget_planning': {
                'editorial_costs_per_book': 2000,
                'design_costs_per_book': 1500,
                'production_costs_per_book': 500,
                'marketing_costs_per_book': 1000
            }
        }

    def _generate_risk_mitigation_plan(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Generate risk mitigation plan."""
        return [
            {
                'risk': 'Author delays',
                'probability': 'High',
                'impact': 'Medium',
                'mitigation': 'Build buffer time into schedules, maintain backup content pipeline',
                'contingency': 'Activate freelance authors, adjust publication schedule'
            },
            {
                'risk': 'Quality issues',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Implement robust quality gates, regular training',
                'contingency': 'Additional editing rounds, external quality review'
            },
            {
                'risk': 'Resource unavailability',
                'probability': 'Medium',
                'impact': 'Medium',
                'mitigation': 'Cross-train team members, maintain freelancer network',
                'contingency': 'Outsource critical tasks, adjust timelines'
            },
            {
                'risk': 'Market changes',
                'probability': 'Low',
                'impact': 'High',
                'mitigation': 'Regular market research, flexible content strategy',
                'contingency': 'Pivot content focus, adjust marketing approach'
            }
        ]

    def _get_stage_description(self, stage_name: str) -> str:
        """Get description for a workflow stage."""
        descriptions = {
            'Manuscript Intake': 'Initial review and processing of submitted manuscripts',
            'Content Review': 'Comprehensive review of content for alignment with imprint standards',
            'Developmental Editing': 'Structural and content editing to improve overall quality',
            'Copy Editing': 'Line-by-line editing for grammar, style, and consistency',
            'Design & Layout': 'Book design, layout, and visual element creation',
            'Proofreading': 'Final review for errors and formatting issues',
            'Final Review': 'Comprehensive quality check before production',
            'Production': 'File preparation and production coordination',
            'Distribution': 'Distribution setup and launch coordination'
        }
        return descriptions.get(stage_name, 'Standard workflow stage')

    def _get_stage_duration(self, stage_name: str) -> int:
        """Get estimated duration in days for a workflow stage."""
        durations = {
            'Manuscript Intake': 2,
            'Content Review': 5,
            'Developmental Editing': 14,
            'Copy Editing': 10,
            'Design & Layout': 7,
            'Proofreading': 3,
            'Final Review': 2,
            'Production': 5,
            'Distribution': 3
        }
        return durations.get(stage_name, 5)

    def _get_stage_roles(self, stage_name: str) -> List[str]:
        """Get required roles for a workflow stage."""
        roles = {
            'Manuscript Intake': ['Editorial Assistant', 'Content Editor'],
            'Content Review': ['Content Editor', 'Editorial Director'],
            'Developmental Editing': ['Developmental Editor', 'Content Editor'],
            'Copy Editing': ['Copy Editor', 'Proofreader'],
            'Design & Layout': ['Book Designer', 'Art Director'],
            'Proofreading': ['Proofreader', 'Copy Editor'],
            'Final Review': ['Production Manager', 'Editorial Director'],
            'Production': ['Production Manager', 'Technical Specialist'],
            'Distribution': ['Distribution Coordinator', 'Marketing Manager']
        }
        return roles.get(stage_name, ['Team Member'])

    def _get_stage_quality_gates(self, stage_name: str, imprint: ExpandedImprint) -> List[str]:
        """Get quality gates for a workflow stage."""
        gates = {
            'Content Review': [
                'Content aligns with imprint mission',
                'Target audience appropriateness verified',
                'Brand voice consistency checked'
            ],
            'Copy Editing': [
                'Grammar and style standards met',
                'Fact-checking completed',
                'Brand guidelines compliance verified'
            ],
            'Design & Layout': [
                'Visual brand compliance verified',
                'Typography standards met',
                'Print specifications confirmed'
            ],
            'Final Review': [
                'All quality gates passed',
                'Metadata accuracy verified',
                'Distribution requirements met'
            ]
        }
        return gates.get(stage_name, ['Standard quality check completed'])

    def _get_stage_deliverables(self, stage_name: str) -> List[str]:
        """Get deliverables for a workflow stage."""
        deliverables = {
            'Manuscript Intake': ['Intake form', 'Initial assessment', 'Project setup'],
            'Content Review': ['Content review report', 'Approval/rejection decision', 'Feedback document'],
            'Developmental Editing': ['Edited manuscript', 'Editorial notes', 'Revision recommendations'],
            'Copy Editing': ['Copy-edited manuscript', 'Style sheet', 'Query list'],
            'Design & Layout': ['Designed book files', 'Cover design', 'Layout specifications'],
            'Proofreading': ['Proofread manuscript', 'Corrections list', 'Final approval'],
            'Final Review': ['Final manuscript', 'Quality checklist', 'Production approval'],
            'Production': ['Print-ready files', 'Production specifications', 'Quality samples'],
            'Distribution': ['Distribution files', 'Metadata package', 'Launch materials']
        }
        return deliverables.get(stage_name, ['Stage completion confirmation'])

    def _get_default_book_ideas(self, imprint: ExpandedImprint, num_books: int) -> List[Dict[str, Any]]:
        """Get default book ideas if LLM generation fails."""
        primary_genre = imprint.publishing.primary_genres[0] if imprint.publishing.primary_genres else 'General'
        
        ideas = []
        for i in range(num_books):
            ideas.append({
                'title': f'{primary_genre} Book {i+1}',
                'author': f'Author {i+1}',
                'genre': primary_genre,
                'description': f'A compelling {primary_genre.lower()} book for {imprint.publishing.target_audience}.',
                'estimated_word_count': 80000,
                'target_audience': imprint.publishing.target_audience,
                'market_appeal': 'medium'
            })
        
        return ideas

    def _get_default_codex_types(self, imprint: ExpandedImprint) -> List[Dict[str, Any]]:
        """Get default codex types if LLM generation fails."""
        return [
            {
                'name': 'Standard Book',
                'description': 'Traditional book format with standard chapters',
                'use_case': 'General publishing',
                'features': ['Linear narrative', 'Chapter structure', 'Standard pagination'],
                'market_potential': 'High',
                'production_considerations': 'Standard production workflow'
            },
            {
                'name': 'Interactive Guide',
                'description': 'Book with interactive elements and exercises',
                'use_case': 'Educational and self-help content',
                'features': ['Worksheets', 'Interactive exercises', 'Progress tracking'],
                'market_potential': 'Medium',
                'production_considerations': 'Additional design work required'
            }
        ]

    def _load_workflow_templates(self) -> Dict[str, Any]:
        """Load workflow templates."""
        return {
            'standard': {
                'stages': ['Intake', 'Review', 'Edit', 'Design', 'Produce', 'Distribute'],
                'duration_weeks': 16
            },
            'expedited': {
                'stages': ['Intake', 'Edit', 'Design', 'Produce', 'Distribute'],
                'duration_weeks': 10
            }
        }

    def _load_timeline_templates(self) -> Dict[str, Any]:
        """Load timeline templates."""
        return {
            'fiction': {
                'manuscript_weeks': 8,
                'editing_weeks': 4,
                'design_weeks': 2,
                'production_weeks': 2
            },
            'non_fiction': {
                'manuscript_weeks': 10,
                'editing_weeks': 5,
                'design_weeks': 3,
                'production_weeks': 2
            }
        }

    def save_schedule(self, schedules: List[BookSchedule], file_path: str):
        """Save schedules to file."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            schedule_data = {
                'schedules': [schedule.to_dict() for schedule in schedules],
                'generated_at': datetime.now().isoformat(),
                'total_books': len(schedules)
            }
            
            with open(file_path, 'w') as f:
                json.dump(schedule_data, f, indent=2)
            
            self.logger.info(f"Saved {len(schedules)} schedules to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving schedules: {e}")
            raise

    def load_schedule(self, file_path: str) -> List[BookSchedule]:
        """Load schedules from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            schedules = []
            for schedule_data in data['schedules']:
                # Convert date strings back to datetime objects
                for date_field in ['start_date', 'manuscript_deadline', 'editing_deadline', 
                                 'design_deadline', 'production_deadline', 'publication_date',
                                 'created_at', 'updated_at']:
                    if date_field in schedule_data:
                        schedule_data[date_field] = datetime.fromisoformat(schedule_data[date_field])
                
                schedule = BookSchedule(**schedule_data)
                schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error loading schedules: {e}")
            raise