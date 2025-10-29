"""
Tournament of 32 Imprint Ideas

A competitive tournament system for evaluating and selecting the best
new imprint concepts using AI-assisted evaluation and user input.
"""


import streamlit as st
import json
import uuid
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import logging
import pandas as pd



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# Add paths for imports
sys.path.insert(0, '/Users/fred/my-apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import with fallback pattern
try:
    from codexes.core.auth import get_allowed_pages, get_user_role
    from codexes.core.llm_caller import call_model_with_prompt
except ImportError:
    from src.codexes.core.auth import get_allowed_pages, get_user_role
    from src.codexes.core.llm_caller import call_model_with_prompt

# Import existing tournament infrastructure
try:
    from codexes.modules.ideation.tournament.bracket_generator import BracketGenerator
    from codexes.modules.ideation.core.codex_object import CodexObject
    TOURNAMENT_ENGINE_AVAILABLE = True
except ImportError:
    # Graceful fallback if tournament engine not available
    BracketGenerator = None
    CodexObject = None
    TOURNAMENT_ENGINE_AVAILABLE = False



# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")



logger = logging.getLogger(__name__)


def main():
    """Main tournament interface."""
    # Render unified sidebar only if not already rendered by main app
    # Main app sets sidebar_rendered=True to prevent duplication
    if not st.session_state.get('sidebar_rendered', False):
        # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app
    # DO NOT render sidebar here - it's already rendered by codexes-factory-home-ui.py

    # Sync session state from shared auth
        if is_authenticated():
            user_info = get_user_info()
        st.session_state.username = user_info.get('username')
        st.session_state.user_name = user_info.get('user_name')
        st.session_state.user_email = user_info.get('user_email')
        logger.info(f"User authenticated via shared auth: {st.session_state.username}")
    else:
        if "username" not in st.session_state:
            st.session_state.username = None

    # Get tournament size from session state or default
    tournament_size = st.session_state.get('tournament_size', 32)
    
    st.title(f"🏆 Tournament of {tournament_size} Imprint Ideas")
    st.markdown("*Discover the next great publishing imprint through competitive evaluation*")
    
    # Tournament tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Setup Tournament", "⚔️ Run Tournament", "🏅 Results", "💡 Generate Ideas"])
    
    with tab1:
        render_tournament_setup()
    
    with tab2:
        render_tournament_runner()
    
    with tab3:
        render_tournament_results()
    
    with tab4:
        render_idea_generator()


def render_tournament_setup():
    """Set up a new tournament of imprint ideas."""
    st.subheader("🎯 Tournament Setup")

    # Publisher and Template Selection (Phase 3 Enhancement)
    with st.expander("🏢 Publisher & Template Selection", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            publisher_options = ["Nimble Books LLC", "Big Five Killer LLC"]
            selected_publisher = st.selectbox("Publisher", publisher_options, key="tournament_publisher")

            if selected_publisher == "Big Five Killer LLC":
                st.info("🔮 Thaumette will review all B5K tournament finals")
                # Load imprints for B5K
                imprint_path = Path("configs/imprints")
                if imprint_path.exists():
                    imprint_files = list(imprint_path.glob("*.json"))
                    imprint_names = ["All Imprints (Publisher-Level)"] + [f.stem.replace("_", " ").title() for f in imprint_files]
                else:
                    imprint_names = ["All Imprints (Publisher-Level)"]

                selected_scope = st.selectbox("Tournament Scope", imprint_names, key="tournament_scope")

                if selected_scope == "All Imprints (Publisher-Level)":
                    st.success("📚 Running publisher-level tournament across all 575 B5K imprints")
                    st.session_state.tournament_level = "publisher"
                else:
                    st.session_state.tournament_level = "imprint"
                    st.session_state.tournament_imprint = selected_scope
            else:
                st.session_state.tournament_level = "imprint"

        with col2:
            template_options = ["Idea Generation", "Manuscript Evaluation", "Cover Design"]
            selected_template = st.selectbox("Tournament Template", template_options, key="tournament_template")

            template_map = {
                "Idea Generation": "idea_generation.json",
                "Manuscript Evaluation": "manuscript_evaluation.json",
                "Cover Design": "cover_design.json"
            }

            template_file = Path(f"templates/tournament_configs/{template_map[selected_template]}")
            if template_file.exists():
                st.success(f"✅ Template loaded: {selected_template}")
                with open(template_file) as f:
                    template_config = json.load(f)
                st.session_state.tournament_template = template_config
            else:
                st.warning(f"⚠️ Template not found: {template_file}")
                st.session_state.tournament_template = None

    st.markdown("---")

    # Check for existing tournament
    tournament_file = Path("tournaments/current_imprint_tournament.json")
    
    if tournament_file.exists():
        try:
            with open(tournament_file, 'r') as f:
                current_tournament = json.load(f)
            
            st.info(f"Current tournament: **{current_tournament['name']}** ({current_tournament['status']})")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 View Current Tournament"):
                    st.session_state.view_current = True
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear & Start New"):
                    tournament_file.unlink()
                    st.success("Tournament cleared!")
                    st.rerun()
                    
            if st.session_state.get("view_current"):
                display_tournament_overview(current_tournament)
                return
                
        except Exception as e:
            st.error(f"Error loading current tournament: {e}")
    
    # Upload existing ideas section
    st.markdown("### 📊 Upload Existing Imprint Ideas")
    
    uploaded_file = st.file_uploader(
        "Upload your imprint ideas spreadsheet",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a CSV or Excel file with your partial imprint ideas. We'll analyze and help complete them."
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Uploaded {len(df)} imprint ideas from {uploaded_file.name}")
            
            # Display preview
            with st.expander("📋 Preview Uploaded Ideas", expanded=True):
                st.dataframe(df.head(10))
                
                if len(df) > 10:
                    st.info(f"Showing first 10 rows of {len(df)} total ideas")
            
            # Analysis of completeness
            analyze_imprint_ideas_completeness(df)
            
            # Store in session state for later use
            st.session_state['uploaded_imprint_ideas'] = df.to_dict('records')
            
            # Also save to persistent file for cross-page access
            uploaded_ideas_file = Path("data/uploaded_imprint_ideas.json")
            uploaded_ideas_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(uploaded_ideas_file, 'w') as f:
                json.dump({
                    "uploaded_at": datetime.now().isoformat(),
                    "filename": uploaded_file.name,
                    "ideas": df.to_dict('records')
                }, f, indent=2)
                
            st.info("💾 Imprint ideas saved for use in Enhanced Imprint Creator")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Please ensure your file has proper column headers and is in CSV or Excel format")
    
    st.markdown("---")
    
    # Create new tournament
    st.markdown("### Create New Tournament")
    
    # Check if we have uploaded ideas
    uploaded_ideas_count = 0
    if 'uploaded_imprint_ideas' in st.session_state:
        uploaded_ideas_count = len(st.session_state['uploaded_imprint_ideas'])
        st.info(f"📊 You have {uploaded_ideas_count} uploaded ideas ready to use in the tournament")
    
    with st.form("tournament_setup"):
        col1, col2 = st.columns(2)
        
        with col1:
            tournament_name = st.text_input("Tournament Name", 
                                          value=f"Imprint Ideas Tournament {datetime.now().strftime('%B %Y')}")
            
            # Tournament size configuration - allow any number
            tournament_size = st.number_input(
                "Tournament Size", 
                min_value=2, 
                max_value=256,
                value=uploaded_ideas_count if uploaded_ideas_count >= 2 else 16,
                help="Number of imprint ideas in the tournament (any number 2-256). Non-power-of-2 will use byes."
            )
            
            # Store tournament size in session state
            st.session_state.tournament_size = tournament_size
            
            # Show tournament structure info
            def is_power_of_2(n):
                return n > 0 and (n & (n - 1)) == 0
            
            if is_power_of_2(tournament_size):
                # Perfect bracket size, no byes needed
                st.success(f"✅ Perfect bracket: {tournament_size} participants, no byes needed")
            else:
                # Need byes to reach next power of 2
                next_power_of_2 = 1
                while next_power_of_2 < tournament_size:
                    next_power_of_2 *= 2
                
                byes_needed = next_power_of_2 - tournament_size
                st.info(f"📋 Tournament structure: {tournament_size} participants + {byes_needed} byes → {next_power_of_2}-slot bracket")
            
            # Adjust defaults based on uploaded ideas and tournament size
            default_user_ideas = min(uploaded_ideas_count, tournament_size) if uploaded_ideas_count > 0 else max(1, tournament_size // 4)
            default_ai_ideas = tournament_size - default_user_ideas
            
            user_ideas_count = st.number_input("Your Ideas", min_value=0, max_value=tournament_size, 
                                             value=default_user_ideas,
                                             help="Number of imprint ideas you'll provide (including uploaded)")
            
            llm_ideas_count = st.number_input("AI Generated Ideas", min_value=0, max_value=tournament_size, 
                                            value=default_ai_ideas, 
                                            help="Number of ideas for AI to generate")
            
            # Validation
            total_ideas = user_ideas_count + llm_ideas_count
            if total_ideas != tournament_size:
                st.warning(f"Total ideas must equal {tournament_size} (currently {total_ideas})")
        
        with col2:
            evaluation_criteria = st.multiselect("Evaluation Criteria",
                                                ["Commercial Viability", "Editorial Innovation", "Market Gap", 
                                                 "Brand Potential", "Audience Appeal", "Production Feasibility",
                                                 "Competitive Advantage", "Cultural Relevance"],
                                                default=["Commercial Viability", "Editorial Innovation", "Market Gap"])
            
            tournament_duration = st.selectbox("Tournament Duration", 
                                             ["1 Week", "2 Weeks", "1 Month"],
                                             index=1)
            
            allow_public_voting = st.checkbox("Allow Public Voting", value=True,
                                            help="Let website visitors vote on imprint ideas")
        
        if st.form_submit_button("🚀 Create Tournament"):
            if total_ideas == tournament_size and tournament_name:
                create_new_tournament({
                    "name": tournament_name,
                    "tournament_size": tournament_size,
                    "user_ideas_count": user_ideas_count,
                    "llm_ideas_count": llm_ideas_count,
                    "evaluation_criteria": evaluation_criteria,
                    "tournament_duration": tournament_duration,
                    "allow_public_voting": allow_public_voting
                })
            else:
                st.error(f"Please ensure {tournament_size} total ideas and provide a tournament name")


def create_new_tournament(config: Dict[str, Any]):
    """Create a new tournament configuration."""
    try:
        tournament_id = str(uuid.uuid4())[:8]
        
        tournament_data = {
            "tournament_id": tournament_id,
            "name": config["name"],
            "created_at": datetime.now().isoformat(),
            "status": "setup",
            "config": config,
            "ideas": [],
            "brackets": {},
            "results": {},
            "voting_stats": {
                "total_votes": 0,
                "participants": 0,
                "completion_rate": 0.0
            }
        }
        
        # Ensure tournament directory exists
        tournament_dir = Path("tournaments")
        tournament_dir.mkdir(exist_ok=True)
        
        # Save tournament
        tournament_file = tournament_dir / "current_imprint_tournament.json"
        with open(tournament_file, 'w') as f:
            json.dump(tournament_data, f, indent=2)
        
        st.success(f"✅ Tournament '{config['name']}' created!")
        st.info("Next: Add your imprint ideas and generate AI ideas")
        
        st.session_state.tournament_created = True
        st.rerun()
        
    except Exception as e:
        st.error(f"Failed to create tournament: {e}")
        logger.error(f"Tournament creation failed: {e}")


def render_tournament_runner():
    """Run the active tournament."""
    st.subheader("⚔️ Tournament Runner")
    
    tournament_file = Path("tournaments/current_imprint_tournament.json")
    
    if not tournament_file.exists():
        st.warning("No active tournament. Create one in the Setup tab.")
        return
    
    try:
        with open(tournament_file, 'r') as f:
            tournament = json.load(f)
        
        st.markdown(f"### {tournament['name']}")
        st.write(f"**Status**: {tournament['status']}")
        tournament_size = tournament.get('config', {}).get('tournament_size', 32)
        st.write(f"**Ideas**: {len(tournament.get('ideas', []))}/{tournament_size}")
        
        # Tournament status and actions
        if tournament['status'] == 'setup':
            render_idea_collection(tournament)
        elif tournament['status'] == 'running':
            render_bracket_voting(tournament)
        elif tournament['status'] == 'completed':
            render_tournament_completion(tournament)
        
    except Exception as e:
        st.error(f"Error loading tournament: {e}")


def render_idea_collection(tournament: Dict[str, Any]):
    """Collect imprint ideas for the tournament."""
    st.markdown("### 💡 Collect Imprint Ideas")
    
    ideas = tournament.get('ideas', [])
    user_ideas = [idea for idea in ideas if idea.get('source') == 'user']
    ai_ideas = [idea for idea in ideas if idea.get('source') == 'ai']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### Your Ideas ({len(user_ideas)}/{tournament['config']['user_ideas_count']})")
        
        if len(user_ideas) < tournament['config']['user_ideas_count']:
            with st.form("add_user_idea"):
                idea_name = st.text_input("Imprint Name")
                idea_charter = st.text_area("Editorial Charter", height=100)
                idea_focus = st.text_input("Market Focus")
                
                if st.form_submit_button("Add Your Idea"):
                    if idea_name and idea_charter:
                        user_idea = {
                            "id": str(uuid.uuid4())[:8],
                            "name": idea_name,
                            "charter": idea_charter,
                            "focus": idea_focus,
                            "source": "user",
                            "submitted_at": datetime.now().isoformat(),
                            "votes": 0,
                            "evaluation_score": 0.0
                        }
                        
                        tournament['ideas'].append(user_idea)
                        save_tournament(tournament)
                        st.success(f"Added idea: {idea_name}")
                        st.rerun()
                    else:
                        st.error("Please provide name and charter")
        
        # Display user ideas
        for idea in user_ideas:
            with st.expander(f"💡 {idea['name']}"):
                st.write(f"**Charter**: {idea['charter']}")
                st.write(f"**Focus**: {idea.get('focus', 'Not specified')}")
    
    with col2:
        st.markdown(f"#### AI Generated Ideas ({len(ai_ideas)}/{tournament['config']['llm_ideas_count']})")
        
        if len(ai_ideas) < tournament['config']['llm_ideas_count']:
            needed_ideas = tournament['config']['llm_ideas_count'] - len(ai_ideas)
            
            if st.button(f"🤖 Generate {min(5, needed_ideas)} AI Ideas"):
                generate_ai_imprint_ideas(tournament, min(5, needed_ideas))
        
        # Display AI ideas
        for idea in ai_ideas[-5:]:  # Show last 5
            with st.expander(f"🤖 {idea['name']}"):
                st.write(f"**Charter**: {idea['charter']}")
                st.write(f"**Focus**: {idea.get('focus', 'AI generated')}")
    
    # Start tournament when ready
    total_ideas = len(tournament.get('ideas', []))
    tournament_size = tournament.get('config', {}).get('tournament_size', 32)
    
    if total_ideas == tournament_size:
        st.success(f"🎉 All {tournament_size} ideas collected!")
        if st.button("🏁 Start Tournament"):
            tournament['status'] = 'running'
            tournament['started_at'] = datetime.now().isoformat()
            create_tournament_brackets(tournament)
            save_tournament(tournament)
            st.success("Tournament started!")
            st.rerun()
    else:
        st.info(f"Collect {tournament_size - total_ideas} more ideas to start the tournament")


def generate_ai_imprint_ideas(tournament: Dict[str, Any], count: int):
    """Generate AI imprint ideas using LLM."""
    try:
        # Create prompt for imprint idea generation
        prompt_config = {
            "messages": [
                {
                    "role": "user",
                    "content": f"""Generate {count} innovative publishing imprint concepts. Each imprint should have:
                    
1. A compelling, unique name
2. A clear editorial charter (50-100 words)
3. A specific market focus or niche
4. Commercial viability potential
5. Distinctive positioning in the market

Focus on creative, commercially viable concepts that could succeed in today's publishing landscape. Consider emerging trends, underserved markets, and innovative approaches to traditional publishing.

Return as JSON with this structure:
{{
  "imprints": [
    {{
      "name": "Imprint Name",
      "charter": "Editorial mission and philosophy",
      "focus": "Target market and positioning",
      "rationale": "Why this imprint would succeed"
    }}
  ]
}}"""
                }
            ],
            "params": {
                "temperature": 0.8,
                "max_tokens": 2000
            }
        }
        
        # Call LLM
        with st.spinner("Generating AI imprint ideas..."):
            response = call_model_with_prompt(
                model_name="gemini/gemini-2.5-flash",
                prompt_config=prompt_config,
                response_format_type="json_object",
                prompt_name="imprint_tournament_generation"
            )
            
            if response.get("parsed_content"):
                imprints_data = response["parsed_content"]
                
                for imprint_data in imprints_data.get("imprints", [])[:count]:
                    ai_idea = {
                        "id": str(uuid.uuid4())[:8],
                        "name": imprint_data.get("name", "AI Generated Imprint"),
                        "charter": imprint_data.get("charter", "AI generated charter"),
                        "focus": imprint_data.get("focus", "AI generated focus"),
                        "rationale": imprint_data.get("rationale", ""),
                        "source": "ai",
                        "generated_at": datetime.now().isoformat(),
                        "votes": 0,
                        "evaluation_score": 0.0
                    }
                    
                    tournament['ideas'].append(ai_idea)
                
                save_tournament(tournament)
                st.success(f"Generated {count} AI imprint ideas!")
                st.rerun()
            else:
                st.error("Failed to generate AI ideas - invalid response format")
                
    except Exception as e:
        st.error(f"Error generating AI ideas: {e}")
        logger.error(f"AI idea generation failed: {e}")


def render_bracket_voting(tournament: Dict[str, Any]):
    """Render tournament bracket voting interface."""
    st.markdown("### ⚔️ Tournament Brackets")
    
    brackets = tournament.get('brackets', {})
    
    if not brackets:
        st.info("Tournament brackets not yet created")
        return
    
    # Show current round
    current_round = get_current_tournament_round(tournament)
    st.write(f"**Current Round**: {current_round}")
    
    # Display matchups for current round
    round_key = f"round_{current_round}"
    if round_key in brackets:
        matchups = brackets[round_key]
        
        st.markdown(f"#### Round {current_round} Matchups")
        
        for i, matchup in enumerate(matchups):
            if not matchup.get('winner'):
                render_matchup_voting(tournament, current_round, i, matchup)
    
    # Check if round is complete
    if is_round_complete(tournament, current_round):
        if st.button("Advance to Next Round"):
            advance_tournament_round(tournament)


def render_matchup_voting(tournament: Dict[str, Any], round_num: int, matchup_idx: int, matchup: Dict[str, Any]):
    """Render individual matchup voting."""
    idea1 = get_idea_by_id(tournament, matchup['idea1_id'])
    idea2 = get_idea_by_id(tournament, matchup['idea2_id'])
    
    if not idea1 or not idea2:
        st.error("Invalid matchup - missing ideas")
        return
    
    st.markdown(f"#### Matchup {matchup_idx + 1}")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown(f"**{idea1['name']}**")
        st.write(idea1['charter'])
        st.write(f"*Focus: {idea1['focus']}*")
        
        if st.button(f"Vote for {idea1['name']}", key=f"vote_1_{round_num}_{matchup_idx}"):
            record_vote(tournament, round_num, matchup_idx, idea1['id'])
    
    with col2:
        st.markdown("**VS**")
        st.markdown("---")
        st.write("🏆")
    
    with col3:
        st.markdown(f"**{idea2['name']}**")
        st.write(idea2['charter'])
        st.write(f"*Focus: {idea2['focus']}*")
        
        if st.button(f"Vote for {idea2['name']}", key=f"vote_2_{round_num}_{matchup_idx}"):
            record_vote(tournament, round_num, matchup_idx, idea2['id'])


def render_tournament_results():
    """Display tournament results."""
    st.subheader("🏅 Tournament Results")
    
    tournament_file = Path("tournaments/current_imprint_tournament.json")
    
    if not tournament_file.exists():
        st.info("No tournament results available")
        return
    
    try:
        with open(tournament_file, 'r') as f:
            tournament = json.load(f)
        
        if tournament['status'] == 'completed':
            winner = tournament['results'].get('winner')
            if winner:
                st.balloons()
                st.markdown(f"## 🎉 Winner: {winner['name']}")
                st.markdown(f"**Charter**: {winner['charter']}")
                st.markdown(f"**Focus**: {winner['focus']}")
                
                if st.button("🚀 Create This Imprint"):
                    create_winning_imprint(winner)
        
        # Show bracket progression
        display_bracket_tree(tournament)
        
        # Show statistics
        display_tournament_stats(tournament)
        
    except Exception as e:
        st.error(f"Error displaying results: {e}")


def render_idea_generator():
    """Generate additional imprint ideas for inspiration."""
    st.subheader("💡 Imprint Idea Generator")
    
    st.markdown("Generate inspiration for new imprint concepts")
    
    with st.form("idea_generation"):
        col1, col2 = st.columns(2)
        
        with col1:
            focus_areas = st.multiselect("Focus Areas",
                                        ["Nonfiction", "Business", "Self-Help", "Science",  "Technology", "History", "Biography", "Pop Culture", "Movies and TV",
                                         "Philosophy", "Art & Design", "Random", "Emerging Trends"],
                                        default=["Emerging Trends","Nonfiction"],
                                        help="Select one or more focus areas for imprint ideas")
            additional_focus_areas = st.text_area("Additional Focus Areas", "", help="Enter additional focus areas separated by  semicolons")
            focus_areas += additional_focus_areas.split(";")
            
            target_market = st.selectbox("Target Market",
                                       ["General Readers", "Young Adults", "Seniors", "8-12 years old", "Infrequent Readers",
                                        "Industry Specialists", "International Audiences", "Niche Communities"])
        
        with col2:
            innovation_level = st.slider("Innovation Level", 0.0, 1.0, 0.7,
                                       help="0.0 = Traditional, 1.0 = Highly Experimental")
            
            num_ideas = st.number_input("Number of Ideas", min_value=1, max_value=10, value=5)
        
        if st.form_submit_button("Generate Ideas"):
            if focus_areas:  # Only generate if at least one focus area is selected
                generate_inspiration_ideas(focus_areas, target_market, innovation_level, num_ideas)
            else:
                st.error("Please select at least one focus area or enter text in the additional focus areas field")


def generate_inspiration_ideas(focus_areas: List[str], target_market: str, innovation_level: float, count: int):
    """Generate inspiration ideas based on parameters."""
    try:
        focus_areas_text = ", ".join(focus_areas)
        
        prompt_config = {
            "messages": [
                {
                    "role": "user", 
                    "content": f"""Generate {count} innovative publishing imprint ideas with these parameters:

Focus Areas: {focus_areas_text}
Target Market: {target_market}
Innovation Level: {innovation_level} (0.0=traditional, 1.0=experimental)

Each imprint should have:
1. Creative, memorable name
2. Clear editorial mission (30-50 words)
3. Specific market positioning
4. Unique value proposition
5. Innovative product ideas that are well suitable to current frontier models
6. Commercial potential assessment

Make them creative but commercially viable. Consider current market trends and underserved niches.

Format as JSON:
{{
  "ideas": [
    {{
      "name": "Imprint Name",
      "charter": "Editorial mission",
      "positioning": "Market position", 
      "value_prop": "Unique advantage",
      "product_ideas": "Unique product ideas",
      "commercial_assessment": "Viability analysis"
    }}
  ]
}}"""
                }
            ]
        }
        
        with st.spinner("Generating inspiration ideas..."):
            response = call_model_with_prompt(
                model_name="gemini/gemini-2.5-flash",
                prompt_config=prompt_config,
                response_format_type="json_object",
                prompt_name="imprint_inspiration_generation"
            )
            
            if response.get("parsed_content"):
                ideas_data = response["parsed_content"]
                ideas_list = ideas_data.get("ideas", [])
                st.write(ideas_data)
                
                st.markdown("### Generated Imprint Ideas")
                
                # Store ideas in session state for checkbox handling
                if f"generated_ideas_{hash(str(ideas_list))}" not in st.session_state:
                    st.session_state[f"generated_ideas_{hash(str(ideas_list))}"] = ideas_list
                
                # Checkbox selection interface
                st.markdown("**Select ideas to add to tournament:**")
                
                # Create a dataframe for better display
                df_data = []
                for i, idea in enumerate(ideas_list):
                    df_data.append({
                        "Select": False,
                        "Name": idea.get('name', 'Unknown'),
                        "Charter": idea.get('charter', 'No charter')[:80] + "..." if len(idea.get('charter', '')) > 80 else idea.get('charter', 'No charter'),
                        "Positioning": idea.get('positioning', 'No positioning')[:50] + "..." if len(idea.get('positioning', '')) > 50 else idea.get('positioning', 'No positioning'),
                        "Commercial Potential": idea.get('commercial_assessment', 'No assessment')[:60] + "..." if len(idea.get('commercial_assessment', '')) > 60 else idea.get('commercial_assessment', 'No assessment')
                    })
                df = pd.DataFrame(df_data)
                # Selection interface
                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    select_all = st.checkbox("Select All")
                
                with col2:
                    if st.button("Add Selected to Tournament", disabled=len(ideas_list) == 0):
                        add_selected_ideas_to_tournament(ideas_list, st.session_state.get('selected_ideas', []))
                
                # Individual selection checkboxes
                selected_ideas = []
                for i, idea in enumerate(ideas_list):
                    key = f"idea_select_{i}_{hash(str(idea))}"
                    selected = st.checkbox(
                        f"**{idea.get('name', 'Unknown')}**", 
                        value=select_all,
                        key=key
                    )
                    if selected:
                        selected_ideas.append(i)
                    
                    # Show details in expander
                    with st.expander(f"📋 Details: {idea.get('name', 'Unknown')}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Charter**: {idea.get('charter', 'No charter')}")
                            st.write(f"**Value Proposition**: {idea.get('value_prop', 'No value prop')}")
                        with col_b:
                            st.write(f"**Positioning**: {idea.get('positioning', 'No positioning')}")
                            st.write(f"**Product Ideas**: {idea.get('product_ideas', 'No product ideas')}")
                        st.write(f"**Commercial Assessment**: {idea.get('commercial_assessment', 'No assessment')}")
                
                # Store selected ideas in session state
                st.session_state['selected_ideas'] = selected_ideas
                st.session_state['current_generated_ideas'] = ideas_list
                
                if selected_ideas:
                    st.info(f"💡 {len(selected_ideas)} idea(s) selected for tournament addition")

            else:
                st.error("Failed to generate ideas")

                
    except Exception as e:
        st.error(f"Error generating ideas: {e}")


def add_selected_ideas_to_tournament(ideas_list: List[Dict[str, Any]], selected_indices: List[int]):
    """Add multiple selected ideas to the current tournament."""
    try:
        # Check if there's a current tournament
        tournament_file = Path("tournaments/current_imprint_tournament.json")
        
        if not tournament_file.exists():
            st.error("No active tournament found. Please create a tournament first.")
            return
        
        if not selected_indices:
            st.warning("No ideas selected. Please select at least one idea to add.")
            return
        
        # Load current tournament
        with open(tournament_file, 'r') as f:
            tournament = json.load(f)
        
        # Initialize ideas list if needed
        if "ideas" not in tournament:
            tournament["ideas"] = []
        
        added_ideas = []
        
        # Add selected ideas
        for i in selected_indices:
            if i < len(ideas_list):
                idea = ideas_list[i]
                
                # Convert idea to tournament format
                tournament_idea = {
                    "id": str(uuid.uuid4())[:8],
                    "name": idea.get('name', 'Unknown'),
                    "charter": idea.get('charter', 'No charter provided'),
                    "focus": idea.get('positioning', 'No focus specified'),
                    "tagline": idea.get('value_prop', 'No tagline'),
                    "target_audience": "Generated",
                    "competitive_advantage": idea.get('commercial_assessment', 'AI generated'),
                    "product_ideas": idea.get('product_ideas', 'No product ideas'),
                    "source": "AI Generated"
                }
                
                tournament["ideas"].append(tournament_idea)
                added_ideas.append(idea.get('name', 'Unknown'))
        
        # Save tournament
        with open(tournament_file, 'w') as f:
            json.dump(tournament, f, indent=2)
        
        if added_ideas:
            st.success(f"✅ Added {len(added_ideas)} idea(s) to tournament: {', '.join(added_ideas)}")
            # Clear selected ideas from session state
            if 'selected_ideas' in st.session_state:
                del st.session_state['selected_ideas']
            st.rerun()
        
    except Exception as e:
        st.error(f"Error adding ideas to tournament: {e}")


def add_idea_to_tournament(idea: Dict[str, Any]):
    """Add a single generated idea to the current tournament (legacy function)."""
    add_selected_ideas_to_tournament([idea], [0])


def create_tournament_brackets(tournament: Dict[str, Any]):
    """Create tournament bracket structure using proper tournament engine."""
    ideas = tournament['ideas']
    tournament_size = tournament.get('config', {}).get('tournament_size', 32)
    
    if len(ideas) != tournament_size:
        raise ValueError(f"Need exactly {tournament_size} ideas, have {len(ideas)}")
    
    try:
        if TOURNAMENT_ENGINE_AVAILABLE:
            # Use proper tournament engine with bye handling
            bracket_generator = BracketGenerator()
            
            # Convert ideas to mock CodexObjects for the bracket generator
            mock_participants = []
            for idea in ideas:
                # Create a simple mock object with required attributes
                mock_obj = type('MockCodexObject', (), {
                    'uuid': idea['id'],
                    'name': idea['name']
                })()
                mock_participants.append(mock_obj)
            
            # Generate proper bracket with automatic bye handling
            bracket = bracket_generator.generate_single_elimination_bracket(mock_participants)
            
            # Convert back to our tournament format
            tournament_brackets = {}
            for round_idx, round_matches in enumerate(bracket.rounds):
                round_matchups = []
                for match_idx, (participant1, participant2) in enumerate(round_matches):
                    matchup = {
                        "matchup_id": f"r{round_idx+1}_m{match_idx+1}",
                        "idea1_id": participant1 if participant1 != "BYE" else None,
                        "idea2_id": participant2 if participant2 != "BYE" else None,
                        "winner": None,
                        "votes": {"idea1": 0, "idea2": 0},
                        "has_bye": participant1 == "BYE" or participant2 == "BYE"
                    }
                    round_matchups.append(matchup)
                tournament_brackets[f"round_{round_idx+1}"] = round_matchups
            
            tournament['brackets'] = tournament_brackets
            tournament['bracket_metadata'] = {
                "total_rounds": len(bracket.rounds),
                "total_matches": bracket.metadata.get('total_matches', 0),
                "tournament_type": "single_elimination",
                "byes_used": len([m for round_matches in tournament_brackets.values() 
                                for m in round_matches if m.get('has_bye', False)])
            }
            
            logger.info(f"Created tournament bracket with {tournament_size} ideas using tournament engine")
        
        else:
            # Fallback to original logic if tournament engine unavailable
            create_tournament_brackets_fallback(tournament)
            
    except Exception as e:
        logger.error(f"Error creating tournament brackets: {e}")
        # Fallback to simple bracket creation
        create_tournament_brackets_fallback(tournament)


def create_tournament_brackets_fallback(tournament: Dict[str, Any]):
    """Fallback bracket creation with manual bye handling."""
    ideas = tournament['ideas']
    tournament_size = len(ideas)
    
    # Check if already a power of 2
    def is_power_of_2(n):
        return n > 0 and (n & (n - 1)) == 0
    
    if is_power_of_2(tournament_size):
        next_power_of_2 = tournament_size
    else:
        # Find next power of 2
        next_power_of_2 = 1
        while next_power_of_2 < tournament_size:
            next_power_of_2 *= 2
    
    # Shuffle ideas randomly
    import random
    shuffled_ideas = ideas.copy()
    random.shuffle(shuffled_ideas)
    
    # Add byes if needed
    current_participants = shuffled_ideas.copy()
    byes_needed = next_power_of_2 - tournament_size
    for i in range(byes_needed):
        current_participants.append({"id": f"BYE_{i}", "name": "BYE", "is_bye": True})
    
    # Create bracket rounds
    brackets = {}
    round_num = 1
    
    while len(current_participants) > 1:
        round_matchups = []
        next_round_participants = []
        
        for i in range(0, len(current_participants), 2):
            idea1 = current_participants[i]
            idea2 = current_participants[i + 1] if i + 1 < len(current_participants) else {"id": f"BYE_{i}", "name": "BYE", "is_bye": True}
            
            matchup = {
                "matchup_id": f"r{round_num}_m{i//2+1}",
                "idea1_id": idea1['id'] if not idea1.get('is_bye') else None,
                "idea2_id": idea2['id'] if not idea2.get('is_bye') else None,
                "winner": None,
                "votes": {"idea1": 0, "idea2": 0},
                "has_bye": idea1.get('is_bye', False) or idea2.get('is_bye', False)
            }
            round_matchups.append(matchup)
            
            # Winner advances (byes automatically advance the other participant)
            if idea1.get('is_bye', False):
                next_round_participants.append(idea2)
            elif idea2.get('is_bye', False):
                next_round_participants.append(idea1)
            else:
                # Real match - winner determined later, for now advance first
                next_round_participants.append(idea1)
        
        brackets[f"round_{round_num}"] = round_matchups
        current_participants = next_round_participants
        round_num += 1
    
    tournament['brackets'] = brackets
    tournament['bracket_metadata'] = {
        "total_rounds": round_num - 1,
        "tournament_type": "single_elimination",
        "original_size": tournament_size,
        "bracket_size": next_power_of_2,
        "byes_used": byes_needed
    }


def display_tournament_overview(tournament: Dict[str, Any]):
    """Display overview of current tournament."""
    st.markdown(f"### Tournament: {tournament['name']}")
    
    bracket_metadata = tournament.get('bracket_metadata', {})
    
    # Show bracket structure if we have bye information
    if bracket_metadata.get('byes_used', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Ideas", len(tournament.get('ideas', [])))
        
        with col2:
            st.metric("Bracket Size", bracket_metadata.get('bracket_size', 'N/A'))
            
        with col3:
            st.metric("Byes", bracket_metadata.get('byes_used', 0))
        
        with col4:
            st.metric("Status", tournament['status'])
            
        st.info(f"🏆 Structure: {len(tournament.get('ideas', []))} participants → {bracket_metadata.get('bracket_size', 'N/A')}-slot bracket with {bracket_metadata.get('byes_used', 0)} byes")
    
    else:
        # Standard display for power-of-2 tournaments
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Ideas", len(tournament.get('ideas', [])))
        
        with col2:
            st.metric("Status", tournament['status'])
        
        with col3:
            if tournament.get('started_at'):
                st.metric("Started", datetime.fromisoformat(tournament['started_at']).strftime('%m/%d'))


# Helper functions
def get_current_tournament_round(tournament: Dict[str, Any]) -> int:
    """Get the current tournament round."""
    brackets = tournament.get('brackets', {})
    if 'round_5' in brackets:
        return 5  # Finals
    elif 'round_4' in brackets:
        return 4  # Semi-finals
    elif 'round_3' in brackets:
        return 3  # Quarter-finals
    elif 'round_2' in brackets:
        return 2  # Round 2
    else:
        return 1  # Round 1


def get_idea_by_id(tournament: Dict[str, Any], idea_id: str) -> Dict[str, Any]:
    """Get idea by ID."""
    for idea in tournament.get('ideas', []):
        if idea['id'] == idea_id:
            return idea
    return None


def record_vote(tournament: Dict[str, Any], round_num: int, matchup_idx: int, winning_idea_id: str):
    """Record a vote for a matchup."""
    round_key = f"round_{round_num}"
    tournament['brackets'][round_key][matchup_idx]['winner'] = winning_idea_id
    tournament['voting_stats']['total_votes'] += 1
    save_tournament(tournament)
    st.success("Vote recorded!")
    st.rerun()


def is_round_complete(tournament: Dict[str, Any], round_num: int) -> bool:
    """Check if a round is complete."""
    round_key = f"round_{round_num}"
    if round_key not in tournament.get('brackets', {}):
        return False
    
    matchups = tournament['brackets'][round_key]
    return all(matchup.get('winner') for matchup in matchups)


def advance_tournament_round(tournament: Dict[str, Any]):
    """Advance tournament to next round."""
    # Implementation would create next round brackets
    st.success("Advanced to next round!")


def save_tournament(tournament: Dict[str, Any]):
    """Save tournament data."""
    tournament_file = Path("tournaments/current_imprint_tournament.json")
    tournament_file.parent.mkdir(exist_ok=True)
    
    with open(tournament_file, 'w') as f:
        json.dump(tournament, f, indent=2)


def create_winning_imprint(winner: Dict[str, Any]):
    """Create an imprint from the tournament winner."""
    try:
        from codexes.modules.imprints.services.imprint_manager import ImprintManager
        
        manager = ImprintManager()
        
        # Create the imprint
        imprint = manager.create_imprint(
            name=winner['name'],
            charter=winner['charter'],
            created_by="tournament_winner"
        )
        
        st.success(f"Created imprint: {winner['name']}")
        st.info("Visit Imprint Administration to configure further settings")
        
    except Exception as e:
        st.error(f"Failed to create winning imprint: {e}")


def display_bracket_tree(tournament: Dict[str, Any]):
    """Display tournament bracket visualization."""
    st.markdown("### 🌳 Tournament Bracket")
    # Simplified bracket display - full implementation would show visual bracket
    
    brackets = tournament.get('brackets', {})
    for round_name, matchups in brackets.items():
        st.markdown(f"#### {round_name.replace('_', ' ').title()}")
        
        for i, matchup in enumerate(matchups):
            idea1 = get_idea_by_id(tournament, matchup['idea1_id'])
            idea2 = get_idea_by_id(tournament, matchup['idea2_id'])
            winner_id = matchup.get('winner')
            
            if idea1 and idea2:
                winner_name = ""
                if winner_id:
                    winner_idea = get_idea_by_id(tournament, winner_id)
                    winner_name = f" → {winner_idea['name']}" if winner_idea else ""
                
                st.write(f"{i+1}. {idea1['name']} vs {idea2['name']}{winner_name}")


def display_tournament_stats(tournament: Dict[str, Any]):
    """Display tournament statistics."""
    st.markdown("### 📊 Tournament Statistics")
    
    stats = tournament.get('voting_stats', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Votes", stats.get('total_votes', 0))
    
    with col2:
        st.metric("Participants", stats.get('participants', 0))
    
    with col3:
        st.metric("Completion Rate", f"{stats.get('completion_rate', 0):.1%}")


def analyze_imprint_ideas_completeness(df: pd.DataFrame):
    """Analyze uploaded imprint ideas for completeness and provide recommendations."""
    st.markdown("### 🔍 Analysis of Uploaded Ideas")
    
    # Common expected columns for imprint ideas
    expected_columns = {
        'name': ['name', 'imprint_name', 'title', 'imprint'],
        'charter': ['charter', 'description', 'mission', 'purpose', 'charter_description'],
        'focus': ['focus', 'specialization', 'genre', 'subject', 'focus_area'],
        'tagline': ['tagline', 'slogan', 'motto', 'brand_tagline'],
        'target_audience': ['target_audience', 'audience', 'readers', 'demographic'],
        'competitive_advantage': ['competitive_advantage', 'advantage', 'differentiation', 'unique_selling_point']
    }
    
    # Analyze column mapping
    column_mapping = {}
    available_columns = df.columns.tolist()
    
    for concept, variations in expected_columns.items():
        for variation in variations:
            if variation.lower() in [col.lower() for col in available_columns]:
                # Find exact match (case insensitive)
                actual_col = next(col for col in available_columns if col.lower() == variation.lower())
                column_mapping[concept] = actual_col
                break
    
    # Display analysis results
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ Found Columns")
        for concept, column in column_mapping.items():
            st.write(f"• **{concept.title()}**: `{column}`")
        
        if not column_mapping:
            st.warning("No standard columns detected. Please check your column headers.")
    
    with col2:
        st.markdown("#### ❗ Missing Columns")
        missing = set(expected_columns.keys()) - set(column_mapping.keys())
        for concept in missing:
            st.write(f"• **{concept.title()}**")
            variations = expected_columns[concept]
            st.caption(f"  Expected: {', '.join(variations[:3])}")
    
    # Completeness analysis
    if column_mapping:
        st.markdown("#### 📊 Completeness Analysis")
        
        completeness_scores = []
        for idx, row in df.iterrows():
            score = 0
            filled_fields = 0
            
            for concept, column in column_mapping.items():
                if pd.notna(row[column]) and str(row[column]).strip():
                    filled_fields += 1
                score = filled_fields / len(column_mapping)
            
            completeness_scores.append({
                'index': idx,
                'name': row.get(column_mapping.get('name', df.columns[0]), f"Idea {idx+1}"),
                'completeness': score,
                'filled_fields': filled_fields,
                'total_fields': len(column_mapping)
            })
        
        # Summary metrics
        avg_completeness = sum(item['completeness'] for item in completeness_scores) / len(completeness_scores)
        complete_ideas = sum(1 for item in completeness_scores if item['completeness'] >= 0.8)
        incomplete_ideas = len(completeness_scores) - complete_ideas
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("Average Completeness", f"{avg_completeness:.1%}")
        
        with metric_col2:
            st.metric("Complete Ideas (≥80%)", complete_ideas)
        
        with metric_col3:
            st.metric("Need Enhancement", incomplete_ideas)
        
        # Recommendations
        st.markdown("#### 💡 Recommendations")
        
        if incomplete_ideas > 0:
            st.info(f"📝 {incomplete_ideas} ideas need enhancement before tournament")
            st.write("**Next Steps:**")
            st.write("1. Use the **Enhanced Imprint Creator** to flesh out incomplete ideas")
            st.write("2. Generate additional ideas in the **Generate Ideas** tab")
            st.write("3. Come back to create your tournament with N complete ideas")
        else:
            st.success("🎉 All ideas are sufficiently complete for tournament!")
        
        # Detail breakdown
        with st.expander("📋 Detailed Breakdown"):
            breakdown_df = pd.DataFrame(completeness_scores)
            breakdown_df['completeness_pct'] = (breakdown_df['completeness'] * 100).round(1)
            st.dataframe(breakdown_df[['name', 'completeness_pct', 'filled_fields', 'total_fields']])


if __name__ == "__main__":
    main()