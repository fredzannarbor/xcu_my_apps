"""
Real Property Agent
Monitors owned properties, watchlist properties, and market trends
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .base_agent import PersistentAgent, Alert, AlertPriority


class RealPropertyAgent(PersistentAgent):
    """Real estate monitoring agent for properties and markets"""
    
    def __init__(self, db_path: str = 'daily_engine.db'):
        super().__init__("real_property", db_path)
        
        # Initialize OpenAI client for market analysis
        try:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
        except Exception:
            self.client = None
        
        self._init_property_database()
    
    def _init_property_database(self):
        """Initialize property-specific database tables"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Owned properties table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS owned_properties (
                id TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                property_type TEXT,
                purchase_date TEXT,
                purchase_price REAL,
                current_valuation REAL,
                valuation_date TEXT,
                valuation_source TEXT,
                square_footage INTEGER,
                bedrooms INTEGER,
                bathrooms REAL,
                lot_size REAL,
                property_notes TEXT,
                llm_analysis TEXT,
                market_trends TEXT,
                investment_analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Watchlist properties table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist_properties (
                id TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                property_type TEXT,
                list_price REAL,
                listing_date TEXT,
                days_on_market INTEGER,
                price_history TEXT,
                interest_level TEXT,
                watch_reason TEXT,
                llm_analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Market watch areas table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_watch_areas (
                id TEXT PRIMARY KEY,
                area_name TEXT NOT NULL,
                area_type TEXT,
                geographic_bounds TEXT,
                criteria TEXT,
                median_price REAL,
                price_trend TEXT,
                market_analysis TEXT,
                llm_insights TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Property valuations history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS property_valuations (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                valuation_amount REAL NOT NULL,
                valuation_date TEXT NOT NULL,
                valuation_source TEXT,
                confidence_level TEXT,
                methodology TEXT,
                market_conditions TEXT,
                llm_analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES owned_properties (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def monitor(self) -> List[Alert]:
        """Monitor properties and markets for important changes"""
        alerts = []
        
        # Check for significant property value changes
        alerts.extend(self._check_property_value_changes())
        
        # Check watchlist properties for price changes
        alerts.extend(self._check_watchlist_changes())
        
        # Check market trends
        alerts.extend(self._check_market_trends())
        
        # Check for stale valuations
        alerts.extend(self._check_stale_valuations())
        
        return alerts
    
    def _check_property_value_changes(self) -> List[Alert]:
        """Check for significant changes in owned property values"""
        alerts = []
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get properties with recent valuations
        cursor.execute('''
            SELECT p.id, p.address, p.current_valuation, p.valuation_date,
                   prev.valuation_amount as prev_valuation
            FROM owned_properties p
            LEFT JOIN (
                SELECT property_id, valuation_amount,
                       ROW_NUMBER() OVER (PARTITION BY property_id ORDER BY valuation_date DESC) as rn
                FROM property_valuations
            ) prev ON p.id = prev.property_id AND prev.rn = 2
            WHERE p.current_valuation IS NOT NULL
        ''')
        
        for row in cursor.fetchall():
            prop_id, address, current_val, val_date, prev_val = row
            
            if prev_val and current_val:
                change_pct = ((current_val - prev_val) / prev_val) * 100
                
                if abs(change_pct) >= 10:  # 10% or more change
                    priority = AlertPriority.HIGH if abs(change_pct) >= 20 else AlertPriority.MEDIUM
                    direction = "increased" if change_pct > 0 else "decreased"
                    
                    alert = Alert(
                        agent_type=self.agent_type,
                        priority=priority,
                        category="Property Valuation",
                        title=f"Significant Value Change: {address}",
                        description=f"Property value has {direction} by {abs(change_pct):.1f}% from ${prev_val:,.0f} to ${current_val:,.0f}",
                        action_required=True,
                        llm_reasoning=f"Property valuation changed significantly, indicating market movement or property-specific factors.",
                        recommended_actions="1. Review market conditions\n2. Consider property assessment\n3. Evaluate refinancing opportunities" if change_pct > 0 else "1. Investigate cause of decline\n2. Review property condition\n3. Consider market timing",
                        impact_assessment=f"${abs(current_val - prev_val):,.0f} change in property value affects net worth and potential refinancing options."
                    )
                    alerts.append(alert)
        
        conn.close()
        return alerts
    
    def _check_watchlist_changes(self) -> List[Alert]:
        """Check watchlist properties for price changes or new listings"""
        alerts = []
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, address, list_price, days_on_market, interest_level
            FROM watchlist_properties
            WHERE updated_at > datetime('now', '-7 days')
        ''')
        
        for row in cursor.fetchall():
            prop_id, address, list_price, days_on_market, interest_level = row
            
            # Alert for price reductions
            if days_on_market and days_on_market > 30:
                alert = Alert(
                    agent_type=self.agent_type,
                    priority=AlertPriority.MEDIUM,
                    category="Watchlist Property",
                    title=f"Extended Market Time: {address}",
                    description=f"Watchlist property has been on market for {days_on_market} days at ${list_price:,.0f}",
                    action_required=False,
                    llm_reasoning="Extended time on market may indicate pricing issues or opportunity for negotiation.",
                    recommended_actions="1. Research recent price changes\n2. Analyze comparable sales\n3. Consider making an offer",
                    impact_assessment="Potential opportunity for favorable purchase terms."
                )
                alerts.append(alert)
        
        conn.close()
        return alerts
    
    def _check_market_trends(self) -> List[Alert]:
        """Check market watch areas for significant trends"""
        alerts = []
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, area_name, median_price, price_trend, market_analysis
            FROM market_watch_areas
            WHERE last_updated > datetime('now', '-30 days')
        ''')
        
        for row in cursor.fetchall():
            area_id, area_name, median_price, price_trend, market_analysis = row
            
            if price_trend and ("significant" in price_trend.lower() or "rapid" in price_trend.lower()):
                alert = Alert(
                    agent_type=self.agent_type,
                    priority=AlertPriority.MEDIUM,
                    category="Market Trend",
                    title=f"Market Movement in {area_name}",
                    description=f"Significant price trend detected: {price_trend}",
                    action_required=False,
                    llm_reasoning="Market trends can indicate investment opportunities or risks for owned properties.",
                    recommended_actions="1. Review owned properties in area\n2. Consider market timing\n3. Evaluate investment opportunities",
                    impact_assessment="Market trends may affect property values and investment decisions."
                )
                alerts.append(alert)
        
        conn.close()
        return alerts
    
    def _check_stale_valuations(self) -> List[Alert]:
        """Check for properties with outdated valuations"""
        alerts = []
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, address, valuation_date
            FROM owned_properties
            WHERE valuation_date < date('now', '-365 days')
            OR valuation_date IS NULL
        ''')
        
        for row in cursor.fetchall():
            prop_id, address, val_date = row
            
            days_old = "unknown" if not val_date else str((datetime.now() - datetime.strptime(val_date, '%Y-%m-%d')).days)
            
            alert = Alert(
                agent_type=self.agent_type,
                priority=AlertPriority.LOW,
                category="Property Maintenance",
                title=f"Valuation Update Needed: {address}",
                description=f"Property valuation is {days_old} days old and should be updated",
                action_required=True,
                llm_reasoning="Regular property valuations are important for financial planning and insurance coverage.",
                recommended_actions="1. Get professional appraisal\n2. Check online valuation tools\n3. Review comparable sales",
                impact_assessment="Outdated valuations may affect insurance coverage and financial planning accuracy."
            )
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def add_owned_property(self, property_data: Dict[str, Any]) -> str:
        """Add a new owned property"""
        import uuid
        
        prop_id = str(uuid.uuid4())
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO owned_properties (
                id, address, property_type, purchase_date, purchase_price,
                current_valuation, valuation_date, valuation_source,
                square_footage, bedrooms, bathrooms, lot_size, property_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prop_id, property_data.get('address'), property_data.get('property_type'),
            property_data.get('purchase_date'), property_data.get('purchase_price'),
            property_data.get('current_valuation'), property_data.get('valuation_date'),
            property_data.get('valuation_source'), property_data.get('square_footage'),
            property_data.get('bedrooms'), property_data.get('bathrooms'),
            property_data.get('lot_size'), property_data.get('property_notes')
        ))
        
        conn.commit()
        conn.close()
        
        return prop_id
    
    def add_watchlist_property(self, property_data: Dict[str, Any]) -> str:
        """Add a property to watchlist"""
        import uuid
        
        prop_id = str(uuid.uuid4())
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO watchlist_properties (
                id, address, property_type, list_price, listing_date,
                days_on_market, interest_level, watch_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prop_id, property_data.get('address'), property_data.get('property_type'),
            property_data.get('list_price'), property_data.get('listing_date'),
            property_data.get('days_on_market'), property_data.get('interest_level'),
            property_data.get('watch_reason')
        ))
        
        conn.commit()
        conn.close()
        
        return prop_id
    
    def add_market_watch_area(self, area_data: Dict[str, Any]) -> str:
        """Add a market area to watch"""
        import uuid
        
        area_id = str(uuid.uuid4())
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO market_watch_areas (
                id, area_name, area_type, geographic_bounds, criteria
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            area_id, area_data.get('area_name'), area_data.get('area_type'),
            area_data.get('geographic_bounds'), area_data.get('criteria')
        ))
        
        conn.commit()
        conn.close()
        
        return area_id
    
    def get_owned_properties(self) -> List[Dict[str, Any]]:
        """Get all owned properties"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, address, property_type, purchase_date, purchase_price,
                   current_valuation, valuation_date, valuation_source,
                   square_footage, bedrooms, bathrooms, lot_size, property_notes,
                   llm_analysis, market_trends, investment_analysis
            FROM owned_properties
            ORDER BY address
        ''')
        
        properties = []
        for row in cursor.fetchall():
            properties.append({
                'id': row[0],
                'address': row[1],
                'property_type': row[2],
                'purchase_date': row[3],
                'purchase_price': row[4],
                'current_valuation': row[5],
                'valuation_date': row[6],
                'valuation_source': row[7],
                'square_footage': row[8],
                'bedrooms': row[9],
                'bathrooms': row[10],
                'lot_size': row[11],
                'property_notes': row[12],
                'llm_analysis': row[13],
                'market_trends': row[14],
                'investment_analysis': row[15]
            })
        
        conn.close()
        return properties
    
    def get_watchlist_properties(self) -> List[Dict[str, Any]]:
        """Get all watchlist properties"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, address, property_type, list_price, listing_date,
                   days_on_market, interest_level, watch_reason, llm_analysis
            FROM watchlist_properties
            ORDER BY interest_level DESC, address
        ''')
        
        properties = []
        for row in cursor.fetchall():
            properties.append({
                'id': row[0],
                'address': row[1],
                'property_type': row[2],
                'list_price': row[3],
                'listing_date': row[4],
                'days_on_market': row[5],
                'interest_level': row[6],
                'watch_reason': row[7],
                'llm_analysis': row[8]
            })
        
        conn.close()
        return properties
    
    def get_market_watch_areas(self) -> List[Dict[str, Any]]:
        """Get all market watch areas"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, area_name, area_type, geographic_bounds, criteria,
                   median_price, price_trend, market_analysis, llm_insights, last_updated
            FROM market_watch_areas
            ORDER BY area_name
        ''')
        
        areas = []
        for row in cursor.fetchall():
            areas.append({
                'id': row[0],
                'area_name': row[1],
                'area_type': row[2],
                'geographic_bounds': row[3],
                'criteria': row[4],
                'median_price': row[5],
                'price_trend': row[6],
                'market_analysis': row[7],
                'llm_insights': row[8],
                'last_updated': row[9]
            })
        
        conn.close()
        return areas
    
    def generate_property_market_report(self) -> Dict[str, Any]:
        """Generate comprehensive property and market analysis report"""
        if not self.client:
            return {'success': False, 'error': 'LLM client not available'}
        
        try:
            # Get all property and market data
            owned_properties = self.get_owned_properties()
            watchlist_properties = self.get_watchlist_properties()
            market_areas = self.get_market_watch_areas()
            
            # Create comprehensive data summary
            data_summary = self._create_property_data_summary(owned_properties, watchlist_properties, market_areas)
            
            # Generate LLM analysis
            prompt = f"""
            You are a real estate investment and market analysis expert. Analyze this property portfolio and market data to provide comprehensive insights.

            PROPERTY DATA:
            {data_summary}

            Please provide analysis in the following format:

            PORTFOLIO_OVERVIEW:
            [Summary of owned properties and overall portfolio health]

            MARKET_ANALYSIS:
            [Analysis of market trends in watched areas]

            INVESTMENT_OPPORTUNITIES:
            [Specific opportunities based on watchlist and market data]

            RISK_ASSESSMENT:
            [Potential risks in current portfolio and markets]

            VALUATION_INSIGHTS:
            [Analysis of property valuations and market positioning]

            RECOMMENDED_ACTIONS:
            [Specific actions to take in next 3-6 months]

            LONG_TERM_STRATEGY:
            [Strategic recommendations for portfolio growth]

            Focus on actionable insights based on current market conditions and property data.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert real estate analyst with deep knowledge of property markets, investment strategies, and portfolio management."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500
            )
            
            analysis = response.choices[0].message.content
            
            # Parse structured response
            sections = {}
            current_section = None
            current_content = []
            
            for line in analysis.split('\n'):
                line = line.strip()
                if line.endswith(':') and line.replace(':', '').replace(' ', '_').upper() in [
                    'PORTFOLIO_OVERVIEW', 'MARKET_ANALYSIS', 'INVESTMENT_OPPORTUNITIES',
                    'RISK_ASSESSMENT', 'VALUATION_INSIGHTS', 'RECOMMENDED_ACTIONS', 'LONG_TERM_STRATEGY'
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
                'report': sections,
                'raw_analysis': analysis,
                'generated_at': datetime.now().isoformat(),
                'properties_analyzed': len(owned_properties),
                'watchlist_count': len(watchlist_properties),
                'markets_tracked': len(market_areas)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Property analysis failed: {str(e)}'}
    
    def _create_property_data_summary(self, owned_props: List[Dict], watchlist_props: List[Dict], market_areas: List[Dict]) -> str:
        """Create compressed summary of property data for LLM analysis"""
        
        summary = f"ANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Owned Properties Summary
        if owned_props:
            summary += "OWNED PROPERTIES:\n"
            total_value = 0
            for prop in owned_props:
                current_val = prop.get('current_valuation') or 0
                purchase_price = prop.get('purchase_price') or 0
                total_value += current_val
                
                gain_loss = ""
                if current_val and purchase_price:
                    change = ((current_val - purchase_price) / purchase_price) * 100
                    gain_loss = f" ({change:+.1f}% from purchase)"
                
                summary += f"- {prop['address']}: ${current_val:,.0f}{gain_loss}\n"
                if prop.get('property_notes'):
                    summary += f"  Notes: {prop['property_notes'][:100]}\n"
            
            summary += f"Total Portfolio Value: ${total_value:,.0f}\n\n"
        
        # Watchlist Properties Summary
        if watchlist_props:
            summary += "WATCHLIST PROPERTIES:\n"
            for prop in watchlist_props:
                list_price = prop.get('list_price') or 0
                days_on_market = prop.get('days_on_market') or 0
                interest = prop.get('interest_level', 'Medium')
                
                summary += f"- {prop['address']}: ${list_price:,.0f} ({days_on_market} days on market, {interest} interest)\n"
                if prop.get('watch_reason'):
                    summary += f"  Reason: {prop['watch_reason'][:100]}\n"
            summary += "\n"
        
        # Market Areas Summary
        if market_areas:
            summary += "MARKET WATCH AREAS:\n"
            for area in market_areas:
                median_price = area.get('median_price') or 0
                price_trend = area.get('price_trend', 'Unknown')
                
                summary += f"- {area['area_name']}: Median ${median_price:,.0f}, Trend: {price_trend}\n"
                if area.get('criteria'):
                    summary += f"  Criteria: {area['criteria'][:100]}\n"
            summary += "\n"
        
        return summary
    
    def _get_db_connection(self):
        """Get database connection"""
        import sqlite3
        return sqlite3.connect(self.db_path)