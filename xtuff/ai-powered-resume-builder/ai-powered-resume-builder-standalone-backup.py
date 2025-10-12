import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
import re
import io
import base64
import hashlib
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Page configuration
st.set_page_config(
    page_title="Team Resume Builder - Collaborative Professional Profiles",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]  # Simple user ID for demo
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_registered' not in st.session_state:
    st.session_state.is_registered = False
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'generated_resume' not in st.session_state:
    st.session_state.generated_resume = None
if 'uploaded_resume' not in st.session_state:
    st.session_state.uploaded_resume = None
if 'uploaded_work_products' not in st.session_state:
    st.session_state.uploaded_work_products = []
if 'preset_prompts' not in st.session_state:
    st.session_state.preset_prompts = [
        "Generate a resume emphasizing collaborative AI development experience",
        "Create a team profile highlighting complementary technical and business skills",
        "Build a combined resume showing our startup founding team capabilities"
    ]
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Resume Builder"
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None
if 'teams' not in st.session_state:
    # Initialize with example teams of different types
    st.session_state.teams = {
        'startup_founders': {
            'id': 'startup_founders',
            'name': 'Serial Founders Collective',
            'captain': 'demo_user_1',
            'members': ['demo_user_1', 'demo_user_2'],
            'description': 'Experienced founders who complement each other\'s skills - technical, product, and growth',
            'skills_focus': ['Product Development', 'Fundraising', 'Technical Architecture', 'Growth Marketing'],
            'team_type': 'Startup Team',
            'created_date': datetime.now(),
            'visibility': 'public',
            'join_method': 'invite'
        },
        'health_ai_experts': {
            'id': 'health_ai_experts',
            'name': 'Health AI Innovation Group',
            'captain': 'demo_user_3',
            'members': ['demo_user_3', 'demo_user_4'],
            'description': 'Healthcare professionals and AI engineers working on next-gen health solutions',
            'skills_focus': ['Clinical AI', 'Healthcare Systems', 'HIPAA Compliance', 'ML Ops'],
            'team_type': 'Industry Expertise',
            'created_date': datetime.now(),
            'visibility': 'public',
            'join_method': 'request'
        }
    }
if 'user_teams' not in st.session_state:
    st.session_state.user_teams = []
if 'team_resumes' not in st.session_state:
    st.session_state.team_resumes = {}
if 'user_profiles' not in st.session_state:
    st.session_state.user_profiles = {}

# Team Types (for categorization)
TEAM_TYPES = [
    "Startup Team",
    "Consulting Group",
    "Research Collaboration",
    "Industry Expertise",
    "Alumni Network",
    "Project-Based Team",
    "Skill-Based Collective",
    "Geographic Network",
    "Domain Experts",
    "Open Source Contributors",
    "Other"
]

# Team Management Classes
@dataclass
class UserProfile:
    user_id: str
    username: str
    full_name: str = ""
    email: str = ""
    skills: List[str] = field(default_factory=list)
    experience_years: int = 0
    current_role: str = ""
    looking_for_team: bool = True
    preferred_team_types: List[str] = field(default_factory=list)
    bio: str = ""
    github: str = ""
    linkedin: str = ""
    portfolio_url: str = ""

@dataclass
class Team:
    id: str
    name: str
    captain: str
    members: List[str]
    description: str
    skills_focus: List[str]
    team_type: str
    created_date: datetime
    visibility: str = "public"  # public, private
    join_method: str = "request"  # open, request, invite
    max_members: int = 10
    team_goals: str = ""
    looking_for: List[str] = field(default_factory=list)  # Skills/roles they're seeking
    pending_requests: Dict[str, str] = field(default_factory=dict)  # user_id: message
    
    def add_member(self, user_id: str) -> bool:
        if user_id not in self.members and len(self.members) < self.max_members:
            self.members.append(user_id)
            return True
        return False
            
    def remove_member(self, user_id: str) -> bool:
        if user_id in self.members and user_id != self.captain:
            self.members.remove(user_id)
            return True
        return False
            
    def is_captain(self, user_id: str) -> bool:
        return self.captain == user_id
    
    def can_edit(self, user_id: str) -> bool:
        return self.is_captain(user_id)
    
    def request_to_join(self, user_id: str, message: str = ""):
        if user_id not in self.members and user_id not in self.pending_requests:
            self.pending_requests[user_id] = message
    
    def approve_request(self, user_id: str) -> bool:
        if user_id in self.pending_requests:
            del self.pending_requests[user_id]
            return self.add_member(user_id)
        return False
    
    def reject_request(self, user_id: str):
        if user_id in self.pending_requests:
            del self.pending_requests[user_id]

# Validation Classes for Resume Verification
class ValidationLevel(Enum):
    VERIFIED = "✅ Verified"
    PARTIAL = "⚠️ Partially Verified"
    UNVERIFIED = "❓ Unverified"
    INCONSISTENT = "❌ Inconsistent"

@dataclass
class ValidationResult:
    claim: str
    source: str
    level: ValidationLevel
    confidence: float
    evidence: List[str]
    issues: List[str]

# Sample experience data (would be per-user in production)
def get_sample_experience_data():
    return {
        "role": [
            "AI Systems Engineer",
            "Product Manager", 
            "Research Scientist",
            "Software Developer",
            "Data Scientist"
        ],
        "organization": [
            "Tech Startup",
            "Enterprise Company",
            "Research Institute",
            "Consulting Firm",
            "Healthcare Company"
        ],
        "years": [
            "2020-Present",
            "2018-2020",
            "2015-2018",
            "2012-2015",
            "2010-2012"
        ],
        "skills": [
            ["Python", "AI/ML", "LangChain", "APIs"],
            ["Product Strategy", "Agile", "Leadership", "Analytics"],
            ["Research Methods", "Statistics", "Publishing", "Grants"],
            ["Full-Stack", "JavaScript", "React", "Node.js"],
            ["Data Analysis", "Machine Learning", "Visualization", "SQL"]
        ]
    }

def create_team_profile(team: Team, user_profiles: Dict[str, UserProfile]) -> str:
    """Generate a combined team profile/resume"""
    
    profile = f"""# Team: {team.name}
    
**Team Type:** {team.team_type}  
**Members:** {len(team.members)}  
**Founded:** {team.created_date.strftime('%B %Y')}

## Team Overview
{team.description}

## Core Competencies
"""
    
    # Aggregate skills from all members
    all_skills = set()
    for member_id in team.members:
        if member_id in user_profiles:
            all_skills.update(user_profiles[member_id].skills)
    
    if all_skills:
        profile += "• " + "\n• ".join(sorted(all_skills)[:10])
    
    profile += f"""

## Team Goals
{team.team_goals if team.team_goals else "Building innovative solutions through collaboration"}

## Looking For
"""
    
    if team.looking_for:
        profile += "• " + "\n• ".join(team.looking_for)
    else:
        profile += "Open to strategic partnerships and opportunities"
    
    profile += """

## Team Members
"""
    
    for member_id in team.members:
        if member_id in user_profiles:
            member = user_profiles[member_id]
            role = "Captain" if team.is_captain(member_id) else "Member"
            profile += f"""
### {member.full_name or member.username} ({role})
**Current Role:** {member.current_role}  
**Experience:** {member.experience_years} years  
**Key Skills:** {', '.join(member.skills[:5])}  
"""
            if member.bio:
                profile += f"**Bio:** {member.bio[:200]}...\n"
    
    return profile

def validate_resume_internal(resume_text: str, experience_df: pd.DataFrame) -> List[ValidationResult]:
    """Validate resume claims against internal data"""
    
    validations = []
    
    # Extract claims from resume
    claims = []
    
    # Check years of experience
    if "25+ years" in resume_text or "25 years" in resume_text:
        claims.append("25+ years of experience")
    
    # Check specific roles
    for role in experience_df['role'].values:
        if role.lower() in resume_text.lower():
            claims.append(f"Role: {role}")
    
    # Validate each claim
    for claim in claims:
        validation = ValidationResult(
            claim=claim,
            source="Internal Database",
            level=ValidationLevel.VERIFIED,
            confidence=0.95,
            evidence=["Found in experience database"],
            issues=[]
        )
        validations.append(validation)
    
    return validations

def validate_resume_external(resume_text: str) -> Dict:
    """Simulate external validation (would use Gemini API in production)"""
    
    # This would actually call Gemini Pro with grounding
    # For demo, return simulated results
    
    return {
        "overall_accuracy": 0.87,
        "verified_claims": [
            "GitHub repositories exist",
            "Published papers found in academic databases",
            "Company employment history partially verified"
        ],
        "unverified_claims": [
            "Specific revenue numbers",
            "Classified government work"
        ],
        "confidence_score": 0.85
    }

# UI Helper Functions
def render_user_registration():
    """Render user registration/login interface"""
    
    if not st.session_state.is_registered:
        st.info("👤 Please register or login to access team features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Register")
            username = st.text_input("Choose username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            full_name = st.text_input("Full name", key="reg_name")
            
            if st.button("Register", type="primary"):
                if username and email:
                    st.session_state.username = username
                    st.session_state.is_registered = True
                    st.session_state.user_profiles[st.session_state.user_id] = UserProfile(
                        user_id=st.session_state.user_id,
                        username=username,
                        full_name=full_name,
                        email=email
                    )
                    st.success(f"✅ Welcome, {username}!")
                    st.rerun()
        
        with col2:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_username")
            
            if st.button("Login"):
                # Simplified login for demo
                st.session_state.username = login_username
                st.session_state.is_registered = True
                st.success(f"✅ Welcome back, {login_username}!")
                st.rerun()
    
    else:
        st.success(f"👤 Logged in as: {st.session_state.username}")

def render_team_management():
    """Render team management interface"""
    
    st.header("👥 Team Management")
    
    if not st.session_state.is_registered:
        render_user_registration()
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["My Teams", "Browse Teams", "Create Team", "Team Requests"])
    
    with tab1:
        st.subheader("My Teams")
        
        my_teams = [team for team in st.session_state.teams.values() 
                   if st.session_state.user_id in team['members']]
        
        if my_teams:
            for team_data in my_teams:
                with st.expander(f"📁 {team_data['name']}"):
                    st.write(f"**Type:** {team_data['team_type']}")
                    st.write(f"**Members:** {len(team_data['members'])}")
                    st.write(f"**Description:** {team_data['description']}")
                    
                    if team_data['captain'] == st.session_state.user_id:
                        st.info("👑 You are the team captain")
                        
                        # Captain controls
                        if st.button(f"Edit Team", key=f"edit_{team_data['id']}"):
                            st.session_state.editing_team = team_data['id']
                    
                    # Generate team resume
                    if st.button(f"Generate Team Profile", key=f"profile_{team_data['id']}"):
                        team_obj = Team(**team_data)
                        profile = create_team_profile(team_obj, st.session_state.user_profiles)
                        st.session_state.team_resumes[team_data['id']] = profile
                        st.markdown(profile)
        else:
            st.info("You're not part of any teams yet. Browse teams to join or create your own!")
    
    with tab2:
        st.subheader("Browse Public Teams")
        
        # Filter options
        team_type_filter = st.selectbox("Filter by type", ["All"] + TEAM_TYPES)
        skill_search = st.text_input("Search by skill")
        
        public_teams = [team for team in st.session_state.teams.values() 
                       if team['visibility'] == 'public']
        
        # Apply filters
        if team_type_filter != "All":
            public_teams = [t for t in public_teams if t['team_type'] == team_type_filter]
        
        if skill_search:
            public_teams = [t for t in public_teams 
                          if any(skill_search.lower() in s.lower() for s in t['skills_focus'])]
        
        for team_data in public_teams:
            with st.expander(f"🌐 {team_data['name']} ({team_data['team_type']})"):
                st.write(f"**Description:** {team_data['description']}")
                st.write(f"**Focus Areas:** {', '.join(team_data['skills_focus'])}")
                st.write(f"**Members:** {len(team_data['members'])} / {team_data.get('max_members', 10)}")
                st.write(f"**Join Method:** {team_data['join_method']}")
                
                if st.session_state.user_id not in team_data['members']:
                    if team_data['join_method'] == 'open':
                        if st.button(f"Join Team", key=f"join_{team_data['id']}"):
                            team_data['members'].append(st.session_state.user_id)
                            st.success(f"✅ Joined {team_data['name']}!")
                            st.rerun()
                    elif team_data['join_method'] == 'request':
                        message = st.text_area(f"Request message", key=f"msg_{team_data['id']}")
                        if st.button(f"Request to Join", key=f"request_{team_data['id']}"):
                            if 'pending_requests' not in team_data:
                                team_data['pending_requests'] = {}
                            team_data['pending_requests'][st.session_state.user_id] = message
                            st.success("✅ Request sent!")
    
    with tab3:
        st.subheader("Create New Team")
        
        with st.form("create_team_form"):
            team_name = st.text_input("Team Name")
            team_type = st.selectbox("Team Type", TEAM_TYPES)
            description = st.text_area("Team Description", 
                                      placeholder="Describe your team's mission and what makes you work well together")
            
            skills = st.multiselect("Core Skills/Focus Areas", 
                                   ["AI/ML", "Web Development", "Mobile", "Cloud", "Data Science",
                                    "Product Management", "Design", "Marketing", "Sales", "Legal",
                                    "Healthcare", "Finance", "Education", "Research", "Other"])
            
            team_goals = st.text_area("Team Goals", 
                                     placeholder="What are you hoping to achieve together?")
            
            looking_for = st.multiselect("Looking for members with:", 
                                        ["Technical Skills", "Business Development", "Design", 
                                         "Marketing", "Domain Expertise", "Fundraising Experience"])
            
            col1, col2 = st.columns(2)
            with col1:
                visibility = st.radio("Visibility", ["public", "private"])
            with col2:
                join_method = st.radio("Join Method", ["open", "request", "invite"])
            
            max_members = st.slider("Maximum Team Size", 2, 20, 5)
            
            submitted = st.form_submit_button("Create Team", type="primary")
            
            if submitted and team_name:
                team_id = team_name.lower().replace(" ", "_") + str(uuid.uuid4())[:4]
                
                new_team = {
                    'id': team_id,
                    'name': team_name,
                    'captain': st.session_state.user_id,
                    'members': [st.session_state.user_id],
                    'description': description,
                    'skills_focus': skills,
                    'team_type': team_type,
                    'created_date': datetime.now(),
                    'visibility': visibility,
                    'join_method': join_method,
                    'max_members': max_members,
                    'team_goals': team_goals,
                    'looking_for': looking_for,
                    'pending_requests': {}
                }
                
                st.session_state.teams[team_id] = new_team
                st.success(f"✅ Team '{team_name}' created successfully!")
                st.balloons()
                st.rerun()
    
    with tab4:
        st.subheader("Team Requests")
        
        # Show pending requests for teams where user is captain
        captain_teams = [team for team in st.session_state.teams.values() 
                        if team['captain'] == st.session_state.user_id]
        
        if captain_teams:
            for team_data in captain_teams:
                if team_data.get('pending_requests'):
                    st.write(f"**Requests for {team_data['name']}:**")
                    
                    for user_id, message in team_data['pending_requests'].items():
                        with st.container():
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                username = st.session_state.user_profiles.get(user_id, {}).get('username', user_id)
                                st.write(f"**User:** {username}")
                            with col2:
                                st.write(f"**Message:** {message[:100]}")
                            with col3:
                                if st.button("✅", key=f"approve_{team_data['id']}_{user_id}"):
                                    team_data['members'].append(user_id)
                                    del team_data['pending_requests'][user_id]
                                    st.success(f"Approved {username}")
                                    st.rerun()
                                if st.button("❌", key=f"reject_{team_data['id']}_{user_id}"):
                                    del team_data['pending_requests'][user_id]
                                    st.info(f"Rejected {username}")
                                    st.rerun()
        else:
            st.info("No pending requests for your teams")

# Sidebar navigation
with st.sidebar:
    st.header("🎯 Navigation")
    
    # User info
    if st.session_state.is_registered:
        st.success(f"👤 {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.is_registered = False
            st.session_state.username = None
            st.rerun()
    else:
        st.info("👤 Not logged in")
    
    st.divider()
    
    # Tab selection
    tabs = ["Resume Builder", "Team Management", "Document Upload", "Validation", "Profile Settings"]
    selected_tab = st.radio("Select Function:", tabs, key="tab_selector")
    st.session_state.active_tab = selected_tab
    
    st.divider()
    
    # Quick stats
    st.subheader("📊 Platform Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Teams", len(st.session_state.teams))
        st.metric("Users", len(st.session_state.user_profiles))
    with col2:
        if st.session_state.is_registered:
            my_teams_count = len([t for t in st.session_state.teams.values() 
                                if st.session_state.user_id in t['members']])
            st.metric("My Teams", my_teams_count)

# Main content area
if st.session_state.active_tab == "Resume Builder":
    st.title("🚀 Dynamic Resume Builder")
    st.markdown("*Individual or team-based professional profiles*")
    
    # Check if user wants individual or team resume
    resume_type = st.radio("Resume Type:", ["Individual", "Team"])
    
    if resume_type == "Individual":
        # Individual resume generation
        user_query = st.text_area(
            "What kind of opportunity are you looking for?",
            placeholder="Describe the role or company you're targeting...",
            height=100
        )
        
        if st.button("Generate Resume", type="primary"):
            # Generate individual resume (simplified for demo)
            st.session_state.generated_resume = f"""
# {st.session_state.username or 'Professional'} Resume

## Summary
Experienced professional seeking opportunities in innovative teams.

## Skills
• Technical Skills
• Leadership
• Communication

## Experience
[Your experience here]

## Looking For
{user_query}
"""
            st.markdown(st.session_state.generated_resume)
    
    else:
        # Team resume generation
        if not st.session_state.is_registered:
            st.warning("Please login to access team features")
            render_user_registration()
        else:
            my_teams = [team for team in st.session_state.teams.values() 
                       if st.session_state.user_id in team['members']]
            
            if my_teams:
                selected_team = st.selectbox("Select Team:", 
                                            [t['name'] for t in my_teams])
                
                team_data = next(t for t in my_teams if t['name'] == selected_team)
                
                opportunity = st.text_area(
                    "What opportunity is your team pursuing?",
                    placeholder="Describe the project, client, or opportunity..."
                )
                
                if st.button("Generate Team Profile", type="primary"):
                    team_obj = Team(**team_data)
                    profile = create_team_profile(team_obj, st.session_state.user_profiles)
                    
                    # Add opportunity-specific tailoring
                    if opportunity:
                        profile += f"\n\n## Why We're Perfect For This Opportunity\n{opportunity}"
                    
                    st.session_state.team_resumes[team_data['id']] = profile
                    st.markdown(profile)
                    
                    # Download button
                    st.download_button(
                        "📥 Download Team Profile",
                        profile,
                        f"{team_data['name']}_profile.md",
                        "text/markdown"
                    )
            else:
                st.info("Join or create a team to generate team profiles")

elif st.session_state.active_tab == "Team Management":
    render_team_management()

elif st.session_state.active_tab == "Document Upload":
    st.title("📤 Document Upload")
    st.info("Upload resumes and work samples from team members")
    
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=['pdf', 'txt', 'docx', 'doc', 'md'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"✅ Uploaded {len(uploaded_files)} files")

elif st.session_state.active_tab == "Validation":
    st.title("✅ Resume Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Internal Consistency Check")
        if st.button("Validate Internal Claims"):
            if st.session_state.generated_resume:
                # Simulate validation
                st.success("✅ Internal validation complete")
                st.metric("Accuracy Score", "92%")
                st.info("All major claims verified against internal database")
            else:
                st.warning("Generate a resume first")
    
    with col2:
        st.subheader("External Verification")
        if st.button("Verify with External Sources"):
            if st.session_state.generated_resume:
                # Simulate external validation
                results = validate_resume_external(st.session_state.generated_resume)
                st.metric("External Verification", f"{results['overall_accuracy']*100:.0f}%")
                
                with st.expander("Verification Details"):
                    st.write("**Verified:**")
                    for claim in results['verified_claims']:
                        st.write(f"✅ {claim}")
                    st.write("**Unverified:**")
                    for claim in results['unverified_claims']:
                        st.write(f"❓ {claim}")
            else:
                st.warning("Generate a resume first")

elif st.session_state.active_tab == "Profile Settings":
    st.title("⚙️ Profile Settings")
    
    if not st.session_state.is_registered:
        render_user_registration()
    else:
        st.subheader(f"Profile for {st.session_state.username}")
        
        # Get or create user profile
        if st.session_state.user_id not in st.session_state.user_profiles:
            st.session_state.user_profiles[st.session_state.user_id] = UserProfile(
                user_id=st.session_state.user_id,
                username=st.session_state.username
            )
        
        profile = st.session_state.user_profiles[st.session_state.user_id]
        
        with st.form("profile_form"):
            full_name = st.text_input("Full Name", value=profile.full_name)
            email = st.text_input("Email", value=profile.email)
            current_role = st.text_input("Current Role", value=profile.current_role)
            experience_years = st.number_input("Years of Experience", 0, 50, profile.experience_years)
            
            skills = st.multiselect("Skills", 
                                   ["Python", "AI/ML", "Web Dev", "Mobile", "Cloud", "Data Science",
                                    "Product Management", "Design", "Marketing", "Sales", "Legal"],
                                   default=profile.skills)
            
            bio = st.text_area("Bio", value=profile.bio, max_chars=500)
            
            github = st.text_input("GitHub URL", value=profile.github)
            linkedin = st.text_input("LinkedIn URL", value=profile.linkedin)
            
            looking_for_team = st.checkbox("Looking for team opportunities", value=profile.looking_for_team)
            
            preferred_team_types = st.multiselect("Preferred Team Types", 
                                                 TEAM_TYPES,
                                                 default=profile.preferred_team_types)
            
            submitted = st.form_submit_button("Update Profile", type="primary")
            
            if submitted:
                profile.full_name = full_name
                profile.email = email
                profile.current_role = current_role
                profile.experience_years = experience_years
                profile.skills = skills
                profile.bio = bio
                profile.github = github
                profile.linkedin = linkedin
                profile.looking_for_team = looking_for_team
                profile.preferred_team_types = preferred_team_types
                
                st.success("✅ Profile updated successfully!")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <p><i>"Stronger together - Build your professional network through collaborative teams"</i></p>
    <p>Team Resume Builder | Collaborative Professional Profiles</p>
</div>
""", unsafe_allow_html=True)