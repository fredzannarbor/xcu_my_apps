"""
Base Agent Framework for Persistent Agents
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import sqlite3


class AlertPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Alert:
    id: Optional[str] = None
    agent_type: str = ""
    priority: AlertPriority = AlertPriority.MEDIUM
    category: str = ""
    title: str = ""
    description: str = ""
    action_required: bool = False
    due_date: Optional[datetime] = None
    family_member_ids: List[str] = None
    created_at: datetime = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    # LLM Context Fields
    llm_reasoning: str = ""
    context_analysis: str = ""
    recommended_actions: str = ""
    impact_assessment: str = ""
    follow_up_questions: str = ""
    user_notes: str = ""
    
    def __post_init__(self):
        if self.family_member_ids is None:
            self.family_member_ids = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class FamilyMember:
    id: str
    name: str
    relationship: str  # SPOUSE, CHILD, DEPENDENT, SELF
    birth_date: str  # YYYY-MM-DD format
    ssn_last_four: str = ""
    employment_status: str = "UNKNOWN"  # EMPLOYED, RETIRED, DISABLED, UNEMPLOYED
    # LLM Context Fields
    personal_notes: str = ""
    llm_analysis: str = ""
    benefit_strategy_notes: str = ""
    health_context: str = ""
    financial_context: str = ""
    last_llm_update: Optional[datetime] = None


class PersistentAgent(ABC):
    """Base class for all persistent agents"""
    
    def __init__(self, agent_type: str, db_path: str = 'daily_engine.db'):
        self.agent_type = agent_type
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for agent data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS persistent_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                last_run TEXT,
                next_run TEXT,
                config TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                category TEXT,
                title TEXT NOT NULL,
                description TEXT,
                action_required BOOLEAN DEFAULT 0,
                due_date TEXT,
                family_member_ids TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TEXT,
                llm_reasoning TEXT,
                context_analysis TEXT,
                recommended_actions TEXT,
                impact_assessment TEXT,
                follow_up_questions TEXT,
                user_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Family members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_members (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                relationship TEXT NOT NULL,
                birth_date TEXT,
                ssn_last_four TEXT,
                employment_status TEXT,
                personal_notes TEXT,
                llm_analysis TEXT,
                benefit_strategy_notes TEXT,
                health_context TEXT,
                financial_context TEXT,
                last_llm_update TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_documents (
                id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                document_type TEXT NOT NULL,
                file_path TEXT,
                family_member_id TEXT,
                processed BOOLEAN DEFAULT 0,
                llm_summary TEXT,
                key_insights TEXT,
                action_items TEXT,
                anomalies_detected TEXT,
                processing_notes TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @abstractmethod
    def monitor(self) -> List[Alert]:
        """Monitor for issues and return alerts"""
        pass
    
    def save_alert(self, alert: Alert) -> str:
        """Save alert to database and return alert ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_alerts (
                agent_type, priority, category, title, description, action_required,
                due_date, family_member_ids, llm_reasoning, context_analysis,
                recommended_actions, impact_assessment, follow_up_questions, user_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.agent_type, alert.priority.value, alert.category, alert.title,
            alert.description, alert.action_required,
            alert.due_date.isoformat() if alert.due_date else None,
            ','.join(alert.family_member_ids) if alert.family_member_ids else '',
            alert.llm_reasoning, alert.context_analysis, alert.recommended_actions,
            alert.impact_assessment, alert.follow_up_questions, alert.user_notes
        ))
        
        alert_id = str(cursor.lastrowid)
        conn.commit()
        conn.close()
        
        return alert_id
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts for this agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, priority, category, title, description, action_required,
                   due_date, family_member_ids, llm_reasoning, context_analysis,
                   recommended_actions, impact_assessment, follow_up_questions,
                   user_notes, created_at
            FROM agent_alerts 
            WHERE agent_type = ? AND resolved = 0
            ORDER BY priority, due_date
        ''', (self.agent_type,))
        
        alerts = []
        for row in cursor.fetchall():
            alert = Alert(
                id=str(row[0]),
                agent_type=self.agent_type,
                priority=AlertPriority(row[1]),
                category=row[2],
                title=row[3],
                description=row[4],
                action_required=bool(row[5]),
                due_date=datetime.fromisoformat(row[6]) if row[6] else None,
                family_member_ids=row[7].split(',') if row[7] else [],
                llm_reasoning=row[8] or "",
                context_analysis=row[9] or "",
                recommended_actions=row[10] or "",
                impact_assessment=row[11] or "",
                follow_up_questions=row[12] or "",
                user_notes=row[13] or "",
                created_at=datetime.fromisoformat(row[14])
            )
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def resolve_alert(self, alert_id: str, user_notes: str = ""):
        """Mark an alert as resolved"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE agent_alerts 
            SET resolved = 1, resolved_at = ?, user_notes = ?
            WHERE id = ? AND agent_type = ?
        ''', (datetime.now().isoformat(), user_notes, alert_id, self.agent_type))
        
        conn.commit()
        conn.close()
    
    def save_family_member(self, member: FamilyMember):
        """Save or update family member information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO family_members (
                id, name, relationship, birth_date, ssn_last_four, employment_status,
                personal_notes, llm_analysis, benefit_strategy_notes, health_context,
                financial_context, last_llm_update, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            member.id, member.name, member.relationship, member.birth_date,
            member.ssn_last_four, member.employment_status, member.personal_notes,
            member.llm_analysis, member.benefit_strategy_notes, member.health_context,
            member.financial_context,
            member.last_llm_update.isoformat() if member.last_llm_update else None,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_family_members(self) -> List[FamilyMember]:
        """Get all family members"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, relationship, birth_date, ssn_last_four, employment_status,
                   personal_notes, llm_analysis, benefit_strategy_notes, health_context,
                   financial_context, last_llm_update
            FROM family_members
            ORDER BY relationship, name
        ''')
        
        members = []
        for row in cursor.fetchall():
            member = FamilyMember(
                id=row[0],
                name=row[1],
                relationship=row[2],
                birth_date=row[3] or "",
                ssn_last_four=row[4] or "",
                employment_status=row[5] or "UNKNOWN",
                personal_notes=row[6] or "",
                llm_analysis=row[7] or "",
                benefit_strategy_notes=row[8] or "",
                health_context=row[9] or "",
                financial_context=row[10] or "",
                last_llm_update=datetime.fromisoformat(row[11]) if row[11] else None
            )
            members.append(member)
        
        conn.close()
        return members