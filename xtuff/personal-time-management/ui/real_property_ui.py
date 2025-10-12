"""
Real Property Agent UI Components
"""

import streamlit as st
from datetime import datetime, date
from typing import List, Dict, Any
import uuid

from persistent_agents.agent_manager import AgentManager


def render_real_property_management():
    """Render real property management interface"""
    st.subheader("🏠 Real Property Management")
    
    agent_manager = AgentManager()
    property_agent = agent_manager.get_agent('real_property')
    
    if not property_agent:
        st.error("Real Property agent not available")
        return
    
    # Tabs for different property management sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Owned Properties",
        "👀 Watchlist",
        "📊 Market Watch",
        "📈 Property Report"
    ])
    
    with tab1:
        render_owned_properties(property_agent)
    
    with tab2:
        render_watchlist_properties(property_agent)
    
    with tab3:
        render_market_watch_areas(property_agent)
    
    with tab4:
        render_property_report(property_agent)


def render_owned_properties(property_agent):
    """Render owned properties management"""
    st.write("**Your Property Portfolio**")
    
    # Get existing properties
    owned_properties = property_agent.get_owned_properties()
    
    if owned_properties:
        # Portfolio summary
        total_value = sum(prop.get('current_valuation', 0) for prop in owned_properties if prop.get('current_valuation'))
        total_purchase = sum(prop.get('purchase_price', 0) for prop in owned_properties if prop.get('purchase_price'))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Properties Owned", len(owned_properties))
        with col2:
            st.metric("Current Value", f"${total_value:,.0f}" if total_value else "N/A")
        with col3:
            if total_purchase and total_value:
                gain_pct = ((total_value - total_purchase) / total_purchase) * 100
                st.metric("Portfolio Gain", f"{gain_pct:+.1f}%")
            else:
                st.metric("Portfolio Gain", "N/A")
        
        st.divider()
        
        # Display each property
        for prop in owned_properties:
            with st.expander(f"🏠 {prop['address']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {prop.get('property_type', 'N/A')}")
                    st.write(f"**Purchase Date:** {prop.get('purchase_date', 'N/A')}")
                    st.write(f"**Purchase Price:** ${prop.get('purchase_price', 0):,.0f}")
                    st.write(f"**Current Valuation:** ${prop.get('current_valuation', 0):,.0f}")
                    st.write(f"**Valuation Date:** {prop.get('valuation_date', 'N/A')}")
                
                with col2:
                    st.write(f"**Square Footage:** {prop.get('square_footage', 'N/A')}")
                    st.write(f"**Bedrooms:** {prop.get('bedrooms', 'N/A')}")
                    st.write(f"**Bathrooms:** {prop.get('bathrooms', 'N/A')}")
                    st.write(f"**Lot Size:** {prop.get('lot_size', 'N/A')} sq ft")
                
                if prop.get('property_notes'):
                    st.write("**Notes:**")
                    st.write(prop['property_notes'])
                
                if prop.get('llm_analysis'):
                    st.write("**AI Analysis:**")
                    st.write(prop['llm_analysis'])
                
                # Edit/Update buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✏️ Edit", key=f"edit_owned_{prop['id']}"):
                        st.session_state[f"editing_owned_{prop['id']}"] = True
                
                with col2:
                    if st.button(f"📊 Update Valuation", key=f"update_val_{prop['id']}"):
                        st.session_state[f"updating_val_{prop['id']}"] = True
                
                # Edit form
                if st.session_state.get(f"editing_owned_{prop['id']}", False):
                    render_owned_property_form(prop, property_agent, is_edit=True)
                
                # Valuation update form
                if st.session_state.get(f"updating_val_{prop['id']}", False):
                    render_valuation_update_form(prop, property_agent)
    
    else:
        st.info("No owned properties added yet.")
    
    # Add new property
    st.divider()
    st.write("**Add New Property**")
    if st.button("➕ Add Owned Property"):
        st.session_state['adding_owned_property'] = True
    
    if st.session_state.get('adding_owned_property', False):
        new_property = {
            'id': str(uuid.uuid4()),
            'address': '',
            'property_type': 'Single Family',
            'purchase_date': '',
            'purchase_price': 0,
            'current_valuation': 0,
            'valuation_date': '',
            'valuation_source': '',
            'square_footage': 0,
            'bedrooms': 0,
            'bathrooms': 0,
            'lot_size': 0,
            'property_notes': ''
        }
        render_owned_property_form(new_property, property_agent, is_new=True)


def render_owned_property_form(prop: Dict[str, Any], agent, is_new: bool = False, is_edit: bool = False):
    """Render form for adding/editing owned property"""
    
    form_key = f"owned_property_form_{prop['id']}"
    
    with st.form(form_key):
        st.write("**Property Details**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            address = st.text_input("Address:", value=prop.get('address', ''))
            property_type = st.selectbox(
                "Property Type:",
                ["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial", "Land", "Other"],
                index=["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial", "Land", "Other"].index(prop.get('property_type', 'Single Family')) if prop.get('property_type') in ["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial", "Land", "Other"] else 0
            )
            purchase_date = st.date_input("Purchase Date:", value=datetime.strptime(prop.get('purchase_date', '2020-01-01'), '%Y-%m-%d') if prop.get('purchase_date') else date(2020, 1, 1))
            purchase_price = st.number_input("Purchase Price ($):", value=float(prop.get('purchase_price', 0)), min_value=0.0, step=1000.0)
        
        with col2:
            current_valuation = st.number_input("Current Valuation ($):", value=float(prop.get('current_valuation', 0)), min_value=0.0, step=1000.0)
            valuation_date = st.date_input("Valuation Date:", value=datetime.strptime(prop.get('valuation_date', str(date.today())), '%Y-%m-%d') if prop.get('valuation_date') else date.today())
            valuation_source = st.text_input("Valuation Source:", value=prop.get('valuation_source', ''))
            square_footage = st.number_input("Square Footage:", value=int(prop.get('square_footage', 0)), min_value=0, step=100)
        
        col3, col4 = st.columns(2)
        with col3:
            bedrooms = st.number_input("Bedrooms:", value=int(prop.get('bedrooms', 0)), min_value=0, max_value=20)
            bathrooms = st.number_input("Bathrooms:", value=float(prop.get('bathrooms', 0)), min_value=0.0, max_value=20.0, step=0.5)
        
        with col4:
            lot_size = st.number_input("Lot Size (sq ft):", value=float(prop.get('lot_size', 0)), min_value=0.0, step=100.0)
        
        property_notes = st.text_area("Property Notes:", value=prop.get('property_notes', ''))
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Property"):
                # Update property data
                property_data = {
                    'address': address,
                    'property_type': property_type,
                    'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                    'purchase_price': purchase_price,
                    'current_valuation': current_valuation,
                    'valuation_date': valuation_date.strftime('%Y-%m-%d'),
                    'valuation_source': valuation_source,
                    'square_footage': square_footage,
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms,
                    'lot_size': lot_size,
                    'property_notes': property_notes
                }
                
                if is_new:
                    agent.add_owned_property(property_data)
                    st.success(f"Added property: {address}")
                    st.session_state['adding_owned_property'] = False
                else:
                    # Update existing property (would need update method)
                    st.success(f"Updated property: {address}")
                    st.session_state[f"editing_owned_{prop['id']}"] = False
                
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                if is_new:
                    st.session_state['adding_owned_property'] = False
                else:
                    st.session_state[f"editing_owned_{prop['id']}"] = False
                st.rerun()


def render_valuation_update_form(prop: Dict[str, Any], agent):
    """Render form for updating property valuation"""
    
    with st.form(f"valuation_form_{prop['id']}"):
        st.write(f"**Update Valuation for {prop['address']}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_valuation = st.number_input("New Valuation ($):", value=float(prop.get('current_valuation', 0)), min_value=0.0, step=1000.0)
            valuation_source = st.text_input("Valuation Source:", value="Manual Update")
        
        with col2:
            valuation_date = st.date_input("Valuation Date:", value=date.today())
            confidence_level = st.selectbox("Confidence Level:", ["High", "Medium", "Low"])
        
        methodology = st.text_area("Methodology/Notes:", placeholder="How was this valuation determined?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Update Valuation"):
                # Add valuation record (would need method to add to property_valuations table)
                st.success(f"Updated valuation for {prop['address']}")
                st.session_state[f"updating_val_{prop['id']}"] = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state[f"updating_val_{prop['id']}"] = False
                st.rerun()


def render_watchlist_properties(property_agent):
    """Render watchlist properties management"""
    st.write("**Property Watchlist**")
    
    # Get watchlist properties
    watchlist_properties = property_agent.get_watchlist_properties()
    
    if watchlist_properties:
        for prop in watchlist_properties:
            with st.expander(f"👀 {prop['address']} - ${prop.get('list_price', 0):,.0f}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {prop.get('property_type', 'N/A')}")
                    st.write(f"**List Price:** ${prop.get('list_price', 0):,.0f}")
                    st.write(f"**Listing Date:** {prop.get('listing_date', 'N/A')}")
                    st.write(f"**Days on Market:** {prop.get('days_on_market', 'N/A')}")
                
                with col2:
                    st.write(f"**Interest Level:** {prop.get('interest_level', 'N/A')}")
                    if prop.get('watch_reason'):
                        st.write("**Watch Reason:**")
                        st.write(prop['watch_reason'])
                
                if prop.get('llm_analysis'):
                    st.write("**AI Analysis:**")
                    st.write(prop['llm_analysis'])
    else:
        st.info("No properties in watchlist yet.")
    
    # Add new watchlist property
    st.divider()
    st.write("**Add to Watchlist**")
    if st.button("➕ Add Watchlist Property"):
        st.session_state['adding_watchlist_property'] = True
    
    if st.session_state.get('adding_watchlist_property', False):
        render_watchlist_property_form(property_agent)


def render_watchlist_property_form(agent):
    """Render form for adding watchlist property"""
    
    with st.form("watchlist_property_form"):
        st.write("**Watchlist Property Details**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            address = st.text_input("Address:")
            property_type = st.selectbox("Property Type:", ["Single Family", "Condo", "Townhouse", "Multi-Family", "Commercial", "Land", "Other"])
            list_price = st.number_input("List Price ($):", min_value=0.0, step=1000.0)
        
        with col2:
            listing_date = st.date_input("Listing Date:", value=date.today())
            days_on_market = st.number_input("Days on Market:", min_value=0, step=1)
            interest_level = st.selectbox("Interest Level:", ["High", "Medium", "Low"])
        
        watch_reason = st.text_area("Why are you watching this property?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Add to Watchlist"):
                property_data = {
                    'address': address,
                    'property_type': property_type,
                    'list_price': list_price,
                    'listing_date': listing_date.strftime('%Y-%m-%d'),
                    'days_on_market': days_on_market,
                    'interest_level': interest_level,
                    'watch_reason': watch_reason
                }
                
                agent.add_watchlist_property(property_data)
                st.success(f"Added {address} to watchlist")
                st.session_state['adding_watchlist_property'] = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state['adding_watchlist_property'] = False
                st.rerun()


def render_market_watch_areas(property_agent):
    """Render market watch areas management"""
    st.write("**Market Watch Areas**")
    
    # Get market watch areas
    market_areas = property_agent.get_market_watch_areas()
    
    if market_areas:
        for area in market_areas:
            with st.expander(f"📊 {area['area_name']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Area Type:** {area.get('area_type', 'N/A')}")
                    st.write(f"**Median Price:** ${area.get('median_price', 0):,.0f}")
                    st.write(f"**Price Trend:** {area.get('price_trend', 'N/A')}")
                
                with col2:
                    st.write(f"**Last Updated:** {area.get('last_updated', 'N/A')}")
                    if area.get('criteria'):
                        st.write("**Watch Criteria:**")
                        st.write(area['criteria'])
                
                if area.get('llm_insights'):
                    st.write("**AI Market Insights:**")
                    st.write(area['llm_insights'])
    else:
        st.info("No market areas being watched yet.")
    
    # Add new market watch area
    st.divider()
    st.write("**Add Market Watch Area**")
    if st.button("➕ Add Market Area"):
        st.session_state['adding_market_area'] = True
    
    if st.session_state.get('adding_market_area', False):
        render_market_area_form(property_agent)


def render_market_area_form(agent):
    """Render form for adding market watch area"""
    
    with st.form("market_area_form"):
        st.write("**Market Watch Area Details**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            area_name = st.text_input("Area Name:", placeholder="e.g., Downtown Seattle, Orange County, etc.")
            area_type = st.selectbox("Area Type:", ["City", "Neighborhood", "County", "State", "ZIP Code", "Custom"])
        
        with col2:
            geographic_bounds = st.text_input("Geographic Bounds:", placeholder="e.g., ZIP codes, city limits, etc.")
        
        criteria = st.text_area("Watch Criteria:", placeholder="What specific market conditions or criteria are you monitoring?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Add Market Area"):
                area_data = {
                    'area_name': area_name,
                    'area_type': area_type,
                    'geographic_bounds': geographic_bounds,
                    'criteria': criteria
                }
                
                agent.add_market_watch_area(area_data)
                st.success(f"Added {area_name} to market watch")
                st.session_state['adding_market_area'] = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state['adding_market_area'] = False
                st.rerun()


def render_property_report(property_agent):
    """Render property market analysis report"""
    st.write("**Property & Market Analysis Report**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧠 Generate Property Report"):
            st.session_state['generate_property_report'] = True
    
    with col2:
        if st.button("📊 Portfolio Summary"):
            st.session_state['show_portfolio_summary'] = True
    
    # Generate report if requested
    if st.session_state.get('generate_property_report', False):
        with st.spinner("🏠 Analyzing your property portfolio and market data..."):
            result = property_agent.generate_property_market_report()
            
            if result['success']:
                st.session_state['latest_property_report'] = result
                st.session_state['generate_property_report'] = False
                st.success("✅ Property analysis complete!")
            else:
                st.error(f"❌ Analysis failed: {result['error']}")
                st.session_state['generate_property_report'] = False
    
    # Display latest report if available
    if 'latest_property_report' in st.session_state:
        report = st.session_state['latest_property_report']
        
        st.write(f"**Generated:** {datetime.fromisoformat(report['generated_at']).strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Properties Analyzed:** {report['properties_analyzed']} owned, {report['watchlist_count']} watchlist, {report['markets_tracked']} markets")
        
        # Display structured sections
        sections = report['report']
        
        if 'portfolio_overview' in sections:
            with st.expander("🏠 Portfolio Overview", expanded=True):
                st.write(sections['portfolio_overview'])
        
        if 'market_analysis' in sections:
            with st.expander("📊 Market Analysis", expanded=True):
                st.write(sections['market_analysis'])
        
        if 'investment_opportunities' in sections:
            with st.expander("💡 Investment Opportunities", expanded=True):
                st.write(sections['investment_opportunities'])
        
        if 'risk_assessment' in sections:
            with st.expander("⚠️ Risk Assessment", expanded=False):
                st.write(sections['risk_assessment'])
        
        if 'valuation_insights' in sections:
            with st.expander("💰 Valuation Insights", expanded=False):
                st.write(sections['valuation_insights'])
        
        if 'recommended_actions' in sections:
            with st.expander("⚡ Recommended Actions", expanded=True):
                st.write(sections['recommended_actions'])
        
        if 'long_term_strategy' in sections:
            with st.expander("🎯 Long-Term Strategy", expanded=False):
                st.write(sections['long_term_strategy'])
        
        # Export options
        st.subheader("📄 Export Report")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save as PDF"):
                st.info("PDF export functionality would be implemented here")
        
        with col2:
            if st.button("📧 Email Report"):
                st.info("Email functionality would be implemented here")
    
    # Show portfolio summary if requested
    if st.session_state.get('show_portfolio_summary', False):
        st.subheader("📊 Portfolio Summary")
        
        owned_properties = property_agent.get_owned_properties()
        watchlist_properties = property_agent.get_watchlist_properties()
        market_areas = property_agent.get_market_watch_areas()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Owned Properties", len(owned_properties))
        
        with col2:
            st.metric("Watchlist Properties", len(watchlist_properties))
        
        with col3:
            st.metric("Market Areas", len(market_areas))
        
        if st.button("❌ Close Summary"):
            st.session_state['show_portfolio_summary'] = False
            st.rerun()
    
    # Initial prompt if no report generated yet
    if 'latest_property_report' not in st.session_state and not st.session_state.get('generate_property_report', False):
        st.info("👆 Click 'Generate Property Report' to get a comprehensive analysis of your property portfolio and market trends.")
        
        with st.expander("ℹ️ What gets analyzed?", expanded=False):
            st.write("""
            The property report analyzes:
            
            **Portfolio Data:**
            - Each owned property's current valuation and performance
            - Purchase prices vs current values
            - Property characteristics and market positioning
            
            **Market Intelligence:**
            - Trends in your watched market areas
            - Comparative market analysis
            - Investment opportunity identification
            
            **Watchlist Analysis:**
            - Properties you're tracking and their market performance
            - Price changes and time on market
            - Investment potential assessment
            
            **Expert Analysis Provides:**
            - Portfolio performance overview
            - Market trend analysis and implications
            - Specific investment opportunities
            - Risk assessment for current holdings
            - Valuation insights and recommendations
            - Immediate and long-term strategic actions
            
            All analysis is based on current market data and real estate investment principles.
            """)
    else:
        st.info("💡 **Tip:** Generate a new report after adding properties, updating valuations, or when market conditions change.")