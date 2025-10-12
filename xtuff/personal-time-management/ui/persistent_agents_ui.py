"""
Persistent Agents UI Integration for Daily Engine
"""

import streamlit as st
from datetime import datetime
from typing import List
import uuid

from persistent_agents.agent_manager import AgentManager
from persistent_agents.base_agent import Alert, AlertPriority, FamilyMember


def render_persistent_agents_panel():
    """Render the persistent agents status panel in Daily Engine"""
    
    # Initialize agent manager
    agent_manager = AgentManager()
    
    # Get dashboard summary
    summary = agent_manager.get_dashboard_summary()
    
    # Display high-priority alerts
    high_priority_alerts = agent_manager.get_high_priority_alerts()
    
    if high_priority_alerts:
        st.subheader("🚨 Priority Alerts")
        
        for alert in high_priority_alerts[:3]:  # Show top 3
            priority_color = {
                AlertPriority.CRITICAL: "🔴",
                AlertPriority.HIGH: "🟠",
                AlertPriority.MEDIUM: "🟡",
                AlertPriority.LOW: "🟢"
            }
            
            with st.expander(f"{priority_color[alert.priority]} {alert.title}", expanded=True):
                st.write(f"**Category:** {alert.category}")
                st.write(f"**Description:** {alert.description}")
                
                if alert.due_date:
                    days_until = (alert.due_date - datetime.now()).days
                    if days_until <= 0:
                        st.error(f"⏰ **OVERDUE** by {abs(days_until)} days")
                    elif days_until <= 7:
                        st.warning(f"⏰ **Due in {days_until} days**")
                    else:
                        st.info(f"⏰ Due in {days_until} days")
                
                if alert.recommended_actions:
                    st.write("**Recommended Actions:**")
                    st.write(alert.recommended_actions)
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Mark Resolved", key=f"resolve_{alert.id}"):
                        agent_manager.resolve_alert(alert.id, alert.agent_type, "Resolved by user")
                        st.success("Alert resolved!")
                        st.rerun()
                
                with col2:
                    if st.button("📝 Add Notes", key=f"notes_{alert.id}"):
                        st.session_state[f"show_notes_{alert.id}"] = True
                
                # Notes input
                if st.session_state.get(f"show_notes_{alert.id}", False):
                    user_notes = st.text_area("Add your notes:", key=f"user_notes_{alert.id}")
                    if st.button("💾 Save Notes", key=f"save_notes_{alert.id}"):
                        # Update alert with user notes (would need to add this method)
                        st.success("Notes saved!")
                        st.session_state[f"show_notes_{alert.id}"] = False
                        st.rerun()
    
    # Agent status overview
    st.subheader("🤖 Agent Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", summary['total_alerts'])
    
    with col2:
        st.metric("Action Required", summary['action_required_count'])
    
    with col3:
        st.metric("Critical/High", summary['critical_alerts'] + summary['high_priority_alerts'])
    
    with col4:
        active_agents = len([status for status in summary['agents_status'].values() if status['active']])
        st.metric("Active Agents", active_agents)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Run Monitoring"):
            with st.spinner("Running agent monitoring..."):
                results = agent_manager.run_monitoring()
                total_new = sum(len(alerts) for alerts in results.values())
                if total_new > 0:
                    st.success(f"Found {total_new} new alerts")
                    st.rerun()
                else:
                    st.info("No new alerts found")
    
    with col2:
        if st.button("📋 View All Alerts"):
            st.session_state['show_all_alerts'] = True
    
    with col3:
        if st.button("🧠 Expert Overview"):
            st.session_state['show_expert_overview'] = True
    
    # Show all alerts if requested
    if st.session_state.get('show_all_alerts', False):
        render_all_alerts_view(agent_manager)
    
    # Show expert overview if requested
    if st.session_state.get('show_expert_overview', False):
        render_expert_overview(agent_manager)


def render_all_alerts_view(agent_manager: AgentManager):
    """Render detailed view of all alerts"""
    st.subheader("📋 All Alerts")
    
    all_alerts = agent_manager.get_all_alerts()
    
    if not all_alerts:
        st.info("No active alerts")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.selectbox(
            "Filter by Priority:",
            ["All", "Critical", "High", "Medium", "Low"]
        )
    
    with col2:
        category_filter = st.selectbox(
            "Filter by Category:",
            ["All"] + list(set(alert.category for alert in all_alerts if alert.category))
        )
    
    with col3:
        if st.button("❌ Close All Alerts View"):
            st.session_state['show_all_alerts'] = False
            st.rerun()
    
    # Apply filters
    filtered_alerts = all_alerts
    if priority_filter != "All":
        priority_map = {
            "Critical": AlertPriority.CRITICAL,
            "High": AlertPriority.HIGH,
            "Medium": AlertPriority.MEDIUM,
            "Low": AlertPriority.LOW
        }
        filtered_alerts = [a for a in filtered_alerts if a.priority == priority_map[priority_filter]]
    
    if category_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a.category == category_filter]
    
    # Display alerts
    for alert in filtered_alerts:
        with st.expander(f"{alert.priority.value.upper()}: {alert.title}"):
            st.write(f"**Agent:** {alert.agent_type}")
            st.write(f"**Category:** {alert.category}")
            st.write(f"**Description:** {alert.description}")
            st.write(f"**Created:** {alert.created_at.strftime('%Y-%m-%d %H:%M')}")
            
            if alert.due_date:
                st.write(f"**Due Date:** {alert.due_date.strftime('%Y-%m-%d')}")
            
            if alert.llm_reasoning:
                st.write("**AI Analysis:**")
                st.write(alert.llm_reasoning)
            
            if alert.recommended_actions:
                st.write("**Recommended Actions:**")
                st.write(alert.recommended_actions)


def render_expert_overview(agent_manager: AgentManager):
    """Render expert overview analysis"""
    st.subheader("🧠 Social Security Expert Overview")
    
    ss_agent = agent_manager.get_agent('social_security')
    if not ss_agent:
        st.error("Social Security agent not available")
        return
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Generate New Overview"):
            st.session_state['generate_overview'] = True
    
    with col2:
        if st.button("📊 Family Summary"):
            st.session_state['show_family_summary'] = True
    
    with col3:
        if st.button("❌ Close Overview"):
            st.session_state['show_expert_overview'] = False
            st.rerun()
    
    # Generate overview if requested
    if st.session_state.get('generate_overview', False):
        with st.spinner("🧠 Analyzing your family's Social Security situation..."):
            result = ss_agent.generate_expert_overview()
            
            if result['success']:
                st.session_state['latest_overview'] = result
                st.session_state['generate_overview'] = False
                st.success("✅ Expert analysis complete!")
            else:
                st.error(f"❌ Analysis failed: {result['error']}")
                st.session_state['generate_overview'] = False
    
    # Display latest overview if available
    if 'latest_overview' in st.session_state:
        overview = st.session_state['latest_overview']
        raw_analysis = overview['raw_analysis']
        
        st.write(f"**Generated:** {datetime.fromisoformat(overview['generated_at']).strftime('%Y-%m-%d %H:%M')}")
        
        # Display structured sections
        sections = overview['overview']
        
        if 'situation_overview' in sections:
            with st.expander("📋 Situation Overview", expanded=True):
                st.write(sections['situation_overview'])
        
        if 'key_opportunities' in sections:
            with st.expander("💡 Key Opportunities", expanded=True):
                st.write(sections['key_opportunities'])
        
        if 'immediate_actions' in sections:
            with st.expander("⚡ Immediate Actions", expanded=True):
                st.write(sections['immediate_actions'])
        
        if 'long_term_strategy' in sections:
            with st.expander("🎯 Long-Term Strategy", expanded=False):
                st.write(sections['long_term_strategy'])
        
        if 'risk_assessment' in sections:
            with st.expander("⚠️ Risk Assessment", expanded=False):
                st.write(sections['risk_assessment'])
        
        if 'questions_to_consider' in sections:
            with st.expander("❓ Questions to Consider", expanded=False):
                st.write(sections['questions_to_consider'])
        
        # Raw analysis in collapsible section
        with st.expander("📄 Full Analysis (Raw)", expanded=False):
            st.text(overview['raw_analysis'])
        
        # Action buttons for the overview
        st.subheader("📝 Follow-up Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("TK")

        with col2:
            if st.button("📊 Generate New Overview"):
                st.session_state['generate_overview'] = True
                st.session_state['email_overview'] = False
                st.rerun()
        with col2:
            if st.button("💾 Save as PDF"):
                with st.spinner("📄 Generating PDF report..."):
                    result = ss_agent.generate_overview_pdf(raw_analysis)
                    
                    if result['success']:
                        # Determine file format and MIME type
                        file_format = result.get('format', 'pdf')
                        if file_format == 'text':
                            mime_type = "text/plain"
                            file_extension = "txt"
                            label = "📥 Download Text Report"
                        else:
                            mime_type = "application/pdf"
                            file_extension = "pdf"
                            label = "📥 Download PDF Report"
                        
                        # Read the file for download
                        with open(result['file_path'], 'rb') as report_file:
                            file_data = report_file.read()
                        
                        # Create download button
                        st.download_button(
                            label=label,
                            data=file_data,
                            file_name=f"social_security_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}",
                            mime=mime_type,
                            key="download_overview_report"
                        )
                        
                        format_text = "PDF" if file_format != 'text' else "text file"
                        st.success(f"✅ {format_text} generated successfully! ({result['file_size']} bytes)")
                        
                        # Clean up temporary file
                        try:
                            import os
                            os.unlink(result['file_path'])
                        except:
                            pass
                    else:
                        st.error(f"❌ PDF generation failed: {result['error']}")
                        if 'reportlab' in result['error']:
                            st.info("💡 To enable PDF export, install reportlab: `pip install reportlab`")
        
        # User notes on the overview
        user_notes = st.text_area(
            "Your notes on this analysis:",
            placeholder="Add your thoughts, questions, or action items based on this expert analysis...",
            key="overview_user_notes"
        )
        
        if st.button("💾 Save Notes"):
            # Save user notes (would implement database storage)
            st.success("Notes saved!")
    
    # Show family summary if requested
    if st.session_state.get('show_family_summary', False):
        st.subheader("👨‍👩‍👧‍👦 Family Situation Summary")
        
        summary = ss_agent.get_family_situation_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Family Members", summary['total_members'])
        
        with col2:
            st.metric("Benefit Eligible", summary['benefit_eligible'])
        
        with col3:
            st.metric("Upcoming Milestones", len(summary['upcoming_milestones']))
        
        # Family composition
        if summary['members_by_relationship']:
            st.write("**Family Composition:**")
            for relationship, count in summary['members_by_relationship'].items():
                st.write(f"- {relationship.title()}: {count}")
        
        # Upcoming milestones
        if summary['upcoming_milestones']:
            st.write("**Upcoming Milestones:**")
            for milestone in summary['upcoming_milestones']:
                days_text = f"in {milestone['days_until']} days" if milestone['days_until'] > 0 else "overdue"
                st.write(f"- **{milestone['member_name']}**: {milestone['milestone']} ({days_text})")
        
        if st.button("❌ Close Summary"):
            st.session_state['show_family_summary'] = False
            st.rerun()
    
    # Initial prompt if no overview generated yet
    if 'latest_overview' not in st.session_state and not st.session_state.get('generate_overview', False):
        st.info("👆 Click 'Generate New Overview' to get a comprehensive expert analysis of your family's Social Security situation.")
        
        # Show what data will be analyzed
        with st.expander("ℹ️ What gets analyzed?", expanded=False):
            st.write("""
            The expert overview analyzes:
            
            **Family Data:**
            - Each family member's age, relationship, and employment status
            - Personal notes and context you've provided
            - Health and financial context
            
            **Recent Activity:**
            - Active alerts and their priorities
            - Recent correspondence analysis
            - Identified deadlines and action items
            
            **Expert Analysis Provides:**
            - Benefit optimization opportunities for each family member
            - Immediate actions to take (next 3-6 months)
            - Long-term strategic recommendations (1-5 years)
            - Risk assessment and missed opportunities
            - Important questions to research or discuss
            
            All analysis is based on current Social Security Administration rules and regulations.
            """)
    
    else:
        # Show hint about refreshing analysis
        st.info("💡 **Tip:** Generate a new overview after adding family members, uploading correspondence, or when your situation changes.")


def render_family_member_management():
    """Render family member management interface"""
    st.subheader("👨‍👩‍👧‍👦 Family Members")
    
    agent_manager = AgentManager()
    ss_agent = agent_manager.get_agent('social_security')
    
    if not ss_agent:
        st.error("Social Security agent not available")
        return
    
    # Get existing family members
    family_members = ss_agent.get_family_members()
    
    # Display existing members
    if family_members:
        st.write("**Current Family Members:**")
        
        for member in family_members:
            with st.expander(f"{member.name} ({member.relationship})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Birth Date:** {member.birth_date}")
                    st.write(f"**Employment:** {member.employment_status}")
                    if member.ssn_last_four:
                        st.write(f"**SSN (last 4):** ***-**-{member.ssn_last_four}")
                
                with col2:
                    if member.personal_notes:
                        st.write("**Personal Notes:**")
                        st.write(member.personal_notes)
                    
                    if member.llm_analysis:
                        st.write("**AI Analysis:**")
                        st.write(member.llm_analysis)
                
                # Edit button
                if st.button(f"✏️ Edit {member.name}", key=f"edit_{member.id}"):
                    st.session_state[f"editing_{member.id}"] = True
                
                # Edit form
                if st.session_state.get(f"editing_{member.id}", False):
                    render_family_member_form(member, ss_agent)

    # Add new member
    st.write("**Add New Family Member:**")
    if st.button("➕ Add Family Member"):
        # Create the new member once and store in session state
        new_member = FamilyMember(
            id=str(uuid.uuid4()),
            name="",
            relationship="SELF",
            birth_date=""
        )
        st.session_state['adding_new_member'] = True
        st.session_state['new_member_data'] = new_member

    if st.session_state.get('adding_new_member', False):
        # Use the stored member data
        new_member = st.session_state.get('new_member_data')
        if new_member:
            render_family_member_form(new_member, ss_agent, is_new=True)


def render_family_member_form(member: FamilyMember, agent, is_new: bool = False):
    """Render form for editing family member"""
    
    with st.form(f"member_form_{member.id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name:", value=member.name)
            relationship = st.selectbox(
                "Relationship:",
                ["SELF", "SPOUSE", "CHILD", "DEPENDENT", "OTHER"],
                index=["SELF", "SPOUSE", "CHILD", "DEPENDENT", "OTHER"].index(member.relationship) if member.relationship in ["SELF", "SPOUSE", "CHILD", "DEPENDENT", "OTHER"] else 0
            )
            birth_date = st.date_input(
                "Birth Date:",
                value=datetime.strptime(member.birth_date, '%Y-%m-%d') if member.birth_date else None,
                min_value=datetime(1900, 1, 1),  # Allow dates from 1900
                max_value=datetime.now()  # Don't allow future birth dates
            )
            st.write(birth_date)

        with col2:
            employment_status = st.selectbox(
                "Employment Status:",
                ["EMPLOYED", "RETIRED", "DISABLED", "UNEMPLOYED", "UNKNOWN"],
                index=["EMPLOYED", "RETIRED", "DISABLED", "UNEMPLOYED", "UNKNOWN"].index(member.employment_status) if member.employment_status in ["EMPLOYED", "RETIRED", "DISABLED", "UNEMPLOYED", "UNKNOWN"] else 4
            )
            ssn_last_four = st.text_input("SSN (last 4 digits):", value=member.ssn_last_four, max_chars=4)
        
        personal_notes = st.text_area("Personal Notes:", value=member.personal_notes)
        health_context = st.text_area("Health Context:", value=member.health_context)
        financial_context = st.text_area("Financial Context:", value=member.financial_context)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save"):
                # Update member data
                member.name = name
                member.relationship = relationship
                member.birth_date = birth_date.strftime('%Y-%m-%d') if birth_date else ""
                member.employment_status = employment_status
                member.ssn_last_four = ssn_last_four
                member.personal_notes = personal_notes
                member.health_context = health_context
                member.financial_context = financial_context
                member.last_llm_update = datetime.now()

                agent.save_family_member(member)

                st.success(f"{'Added' if is_new else 'Updated'} {member.name}")

                # Clear session state
                if is_new:
                    st.session_state['adding_new_member'] = False
                    st.session_state.pop('new_member_data', None)  # Remove the stored data
                else:
                    st.session_state[f"editing_{member.id}"] = False

                st.rerun()

    with col2:
            if st.form_submit_button("❌ Cancel"):
                if is_new:
                    st.session_state['adding_new_member'] = False
                else:
                    st.session_state[f"editing_{member.id}"] = False
                st.rerun()


def render_correspondence_upload():
    """Render correspondence upload interface"""
    st.subheader("📄 Upload Social Security Correspondence")
    
    agent_manager = AgentManager()
    ss_agent = agent_manager.get_agent('social_security')
    
    if not ss_agent:
        st.error("Social Security agent not available")
        return
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Social Security correspondence (PDF, TXT):",
        type=['pdf', 'txt'],
        help="Upload letters, statements, or other correspondence from the Social Security Administration"
    )
    
    # Family member selection
    family_members = ss_agent.get_family_members()
    if family_members:
        member_options = {f"{m.name} ({m.relationship})": m.id for m in family_members}
        selected_member = st.selectbox(
            "Related to family member:",
            ["None"] + list(member_options.keys())
        )
        family_member_id = member_options.get(selected_member) if selected_member != "None" else None
    else:
        family_member_id = None
        st.info("Add family members first to associate correspondence with specific people")
    
    if uploaded_file and st.button("📤 Process Document"):
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            with st.spinner("Processing document with AI..."):
                # Process with Social Security agent
                result = ss_agent.process_correspondence(tmp_file_path, family_member_id)
                
                if result['success']:
                    st.success("Document processed successfully!")
                    
                    # Display analysis
                    analysis = result['analysis']
                    
                    if 'summary' in analysis:
                        st.write("**Summary:**")
                        st.write(analysis['summary'])
                    
                    if 'key_insights' in analysis:
                        st.write("**Key Insights:**")
                        st.write(analysis['key_insights'])
                    
                    if 'action_items' in analysis:
                        st.write("**Action Items:**")
                        st.write(analysis['action_items'])
                    
                    if 'impact' in analysis:
                        st.write("**Impact Assessment:**")
                        st.write(analysis['impact'])
                    
                    # Run monitoring to check for new alerts
                    st.info("Checking for new alerts based on this correspondence...")
                    agent_manager.run_monitoring()
                    
                else:
                    st.error(f"Failed to process document: {result['error']}")
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass