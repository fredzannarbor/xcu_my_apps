"""
Agent Manager for coordinating persistent agents
"""

from typing import List, Dict, Any
from .base_agent import Alert, AlertPriority
from .social_security_agent import SocialSecurityAgent
from .real_property_agent import RealPropertyAgent


class AgentManager:
    """Manages all persistent agents"""
    
    def __init__(self, db_path: str = 'daily_engine.db'):
        self.db_path = db_path
        self.agents = {
            'social_security': SocialSecurityAgent(db_path),
            'real_property': RealPropertyAgent(db_path)
        }
    
    def get_all_alerts(self, priority_filter: AlertPriority = None) -> List[Alert]:
        """Get all alerts from all agents"""
        all_alerts = []
        
        for agent in self.agents.values():
            alerts = agent.get_active_alerts()
            if priority_filter:
                alerts = [a for a in alerts if a.priority == priority_filter]
            all_alerts.extend(alerts)
        
        # Sort by priority and due date
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3
        }
        
        all_alerts.sort(key=lambda x: (
            priority_order[x.priority],
            x.due_date if x.due_date else datetime.max
        ))
        
        return all_alerts
    
    def get_high_priority_alerts(self) -> List[Alert]:
        """Get only critical and high priority alerts"""
        alerts = self.get_all_alerts()
        return [a for a in alerts if a.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]]
    
    def run_monitoring(self) -> Dict[str, List[Alert]]:
        """Run monitoring for all agents and return new alerts"""
        results = {}
        
        for agent_name, agent in self.agents.items():
            try:
                new_alerts = agent.monitor()
                # Save new alerts to database
                for alert in new_alerts:
                    agent.save_alert(alert)
                results[agent_name] = new_alerts
            except Exception as e:
                # Log error but continue with other agents
                print(f"Error running {agent_name} agent: {e}")
                results[agent_name] = []
        
        return results
    
    def get_agent(self, agent_type: str):
        """Get specific agent by type"""
        return self.agents.get(agent_type)
    
    def resolve_alert(self, alert_id: str, agent_type: str, user_notes: str = ""):
        """Resolve an alert"""
        agent = self.agents.get(agent_type)
        if agent:
            agent.resolve_alert(alert_id, user_notes)
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary for dashboard display"""
        alerts = self.get_all_alerts()
        
        summary = {
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a.priority == AlertPriority.CRITICAL]),
            'high_priority_alerts': len([a for a in alerts if a.priority == AlertPriority.HIGH]),
            'action_required_count': len([a for a in alerts if a.action_required]),
            'recent_alerts': alerts[:5],  # Most recent 5 alerts
            'agents_status': {}
        }
        
        # Get agent-specific summaries
        for agent_name, agent in self.agents.items():
            agent_alerts = [a for a in alerts if a.agent_type == agent_name]
            summary['agents_status'][agent_name] = {
                'active': True,
                'alert_count': len(agent_alerts),
                'last_run': 'Recently'  # Simplified for now
            }
        
        return summary