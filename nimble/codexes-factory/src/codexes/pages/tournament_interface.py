"""
Tournament creation and management interface.
Provides UI for creating tournaments, managing participants, and viewing results.
"""


import logging
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import sys

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()




logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)




from codexes.modules.ideation.core.codex_object import CodexObject
from codexes.modules.ideation.tournament.tournament_engine import TournamentEngine, TournamentConfiguration


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


def render_tournament_interface():
    """Render the tournament management interface."""
    st.title("🏆 Tournament Management")
    
    # Initialize tournament engine
    if 'tournament_engine' not in st.session_state:
        st.session_state.tournament_engine = TournamentEngine()
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["Create Tournament", "Active Tournaments", "Results"])
    
    with tab1:
        render_tournament_creation()
    
    with tab2:
        render_active_tournaments()
    
    with tab3:
        render_tournament_results()

def render_tournament_creation():
    """Render tournament creation interface."""
    st.subheader("Create New Tournament")
    
    with st.form("tournament_creation_form"):
        # Basic tournament settings
        tournament_name = st.text_input("Tournament Name", placeholder="Enter tournament name")
        
        col1, col2 = st.columns(2)
        with col1:
            tournament_type = st.selectbox(
                "Tournament Type",
                ["single_elimination", "double_elimination", "round_robin", "swiss"],
                help="Choose the tournament format"
            )
        
        with col2:
            evaluation_method = st.selectbox(
                "Evaluation Method",
                ["llm_comparison", "synthetic_readers", "hybrid"],
                help="How ideas will be evaluated"
            )
        
        # Participant selection
        st.subheader("Select Participants")
        
        # Option 1: Upload ideas
        uploaded_file = st.file_uploader(
            "Upload Ideas (JSON/CSV)",
            type=['json', 'csv'],
            help="Upload a file containing ideas to participate in the tournament"
        )
        
        # Option 2: Select from existing ideas
        if st.checkbox("Select from existing ideas"):
            # This would integrate with the idea storage system
            st.info("Feature coming soon: Select from your saved ideas")
        
        # Option 3: Generate ideas for tournament
        if st.checkbox("Generate ideas for tournament"):
            col1, col2 = st.columns(2)
            with col1:
                idea_count = st.number_input("Number of ideas to generate", min_value=4, max_value=32, value=8)
            with col2:
                generation_theme = st.text_input("Generation theme (optional)", placeholder="e.g., fantasy, sci-fi")
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                max_rounds = st.number_input("Maximum rounds", min_value=1, max_value=10, value=5)
                enable_detailed_feedback = st.checkbox("Enable detailed feedback", value=True)
            
            with col2:
                auto_advance = st.checkbox("Auto-advance rounds", value=False)
                save_all_evaluations = st.checkbox("Save all evaluations", value=True)
        
        # Submit button
        submitted = st.form_submit_button("Create Tournament")
        
        if submitted:
            if not tournament_name:
                st.error("Please enter a tournament name")
                return
            
            try:
                # Create tournament configuration
                config = TournamentConfiguration(
                    tournament_name=tournament_name,
                    tournament_type=tournament_type,
                    evaluation_method=evaluation_method,
                    max_rounds=max_rounds,
                    enable_detailed_feedback=enable_detailed_feedback,
                    auto_advance_rounds=auto_advance,
                    save_all_evaluations=save_all_evaluations
                )
                
                # Handle participant selection
                participants = []
                
                if uploaded_file:
                    participants = load_participants_from_file(uploaded_file)
                elif st.session_state.get('generate_ideas_for_tournament'):
                    participants = generate_tournament_participants(idea_count, generation_theme)
                
                if not participants:
                    st.error("Please provide participants for the tournament")
                    return
                
                # Create tournament
                tournament_engine = st.session_state.tournament_engine
                tournament_uuid = tournament_engine.create_tournament(participants, config)
                
                st.success(f"Tournament '{tournament_name}' created successfully!")
                st.info(f"Tournament ID: {tournament_uuid}")
                
                # Option to start tournament immediately
                if st.button("Start Tournament Now"):
                    result = tournament_engine.run_tournament(tournament_uuid)
                    if result:
                        st.success("Tournament started successfully!")
                        st.session_state.selected_tournament = tournament_uuid
                        st.rerun()
                    else:
                        st.error("Failed to start tournament")
                
            except Exception as e:
                st.error(f"Error creating tournament: {str(e)}")

def render_active_tournaments():
    """Render active tournaments interface."""
    st.subheader("Active Tournaments")
    
    tournament_engine = st.session_state.tournament_engine
    active_tournaments = tournament_engine.get_active_tournaments()
    
    if not active_tournaments:
        st.info("No active tournaments found.")
        return
    
    for tournament in active_tournaments:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{tournament.tournament_name}**")
                st.caption(f"Type: {tournament.tournament_type}")
            
            with col2:
                st.write(f"Participants: {tournament.participant_count}")
                st.caption(f"Round: {tournament.current_round}/{tournament.total_rounds}")
            
            with col3:
                progress = (tournament.current_round / tournament.total_rounds) * 100
                st.progress(progress / 100)
                st.caption(f"Progress: {progress:.1f}%")
            
            with col4:
                if st.button("Manage", key=f"manage_{tournament.tournament_uuid}"):
                    st.session_state.selected_tournament = tournament.tournament_uuid
                    st.session_state.page = "tournament_management"
                    st.rerun()
            
            # Show current round details
            if st.expander(f"Round {tournament.current_round} Details"):
                current_round = tournament.rounds[tournament.current_round - 1] if tournament.rounds else None
                if current_round:
                    for match in current_round.matches:
                        col1, col2, col3 = st.columns([2, 1, 2])
                        
                        with col1:
                            st.write(match.participant_a.title if match.participant_a else "TBD")
                        
                        with col2:
                            st.write("vs")
                        
                        with col3:
                            st.write(match.participant_b.title if match.participant_b else "TBD")
                        
                        if match.winner:
                            st.success(f"Winner: {match.winner.title}")
                        elif match.status == "in_progress":
                            st.info("Match in progress...")
                        else:
                            if st.button(f"Evaluate Match", key=f"eval_{match.match_uuid}"):
                                # Trigger match evaluation
                                tournament_engine.evaluate_match(tournament.tournament_uuid, match.match_uuid)
                                st.rerun()

def render_tournament_results():
    """Render tournament results interface."""
    st.subheader("Tournament Results")
    
    tournament_engine = st.session_state.tournament_engine
    completed_tournaments = tournament_engine.get_completed_tournaments(limit=10)
    
    if not completed_tournaments:
        st.info("No completed tournaments found.")
        return
    
    # Tournament selector
    tournament_options = {
        f"{t.tournament_name} ({t.created_timestamp[:10])": t.tournament_uuid 
        for t in completed_tournaments
    }
    
    selected_tournament_name = st.selectbox("Select Tournament", list(tournament_options.keys()))
    
    if selected_tournament_name:
        tournament_uuid = tournament_options[selected_tournament_name]
        tournament = next(t for t in completed_tournaments if t.tournament_uuid == tournament_uuid)
        
        # Tournament summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Participants", tournament.participant_count)
        
        with col2:
            st.metric("Rounds", len(tournament.rounds))
        
        with col3:
            duration = "N/A"
            if tournament.started_timestamp and tournament.completed_timestamp:
                start = datetime.fromisoformat(tournament.started_timestamp)
                end = datetime.fromisoformat(tournament.completed_timestamp)
                duration = str(end - start)
            st.metric("Duration", duration)
        
        with col4:
            st.metric("Status", tournament.status.title())
        
        # Winner announcement
        if tournament.winner:
            st.success(f"🏆 **Winner: {tournament.winner.title}**")
            
            # Show winner details
            with st.expander("Winner Details"):
                st.write(f"**Premise:** {tournament.winner.premise}")
                st.write(f"**Genre:** {tournament.winner.genre}")
                if tournament.winner.themes:
                    st.write(f"**Themes:** {', '.join(tournament.winner.themes)}")
        
        # Bracket visualization
        st.subheader("Tournament Bracket")
        render_tournament_bracket(tournament)
        
        # Round-by-round results
        st.subheader("Round Results")
        
        for i, round_result in enumerate(tournament.rounds):
            with st.expander(f"Round {i + 1} - {round_result.round_name}"):
                for match in round_result.matches:
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        participant_a_name = match.participant_a.title if match.participant_a else "BYE"
                        if match.winner and match.winner.uuid == match.participant_a.uuid:
                            st.success(f"🏆 {participant_a_name}")
                        else:
                            st.write(participant_a_name)
                    
                    with col2:
                        st.write("vs")
                    
                    with col3:
                        participant_b_name = match.participant_b.title if match.participant_b else "BYE"
                        if match.winner and match.winner.uuid == match.participant_b.uuid:
                            st.success(f"🏆 {participant_b_name}")
                        else:
                            st.write(participant_b_name)
                    
                    # Show evaluation details
                    if match.evaluation_details:
                        st.caption(f"Evaluation: {match.evaluation_details.get('reasoning', 'No details available')}")

def render_tournament_bracket(tournament):
    """Render a visual tournament bracket."""
    # This is a simplified bracket visualization
    # In a full implementation, you might use a more sophisticated visualization library
    
    if not tournament.rounds:
        st.info("No bracket data available")
        return
    
    # Create a simple bracket display
    bracket_data = []
    
    for round_idx, round_result in enumerate(tournament.rounds):
        round_name = f"Round {round_idx + 1}"
        
        for match in round_result.matches:
            bracket_data.append({
                "Round": round_name,
                "Participant A": match.participant_a.title if match.participant_a else "BYE",
                "Participant B": match.participant_b.title if match.participant_b else "BYE",
                "Winner": match.winner.title if match.winner else "TBD",
                "Status": match.status
            })
    
    if bracket_data:
        df = pd.DataFrame(bracket_data)
        st.dataframe(df, use_container_width=True)

def load_participants_from_file(uploaded_file) -> List[CodexObject]:
    """Load tournament participants from uploaded file."""
    try:
        if uploaded_file.type == "application/json":
            import json
            data = json.load(uploaded_file)
            
            participants = []
            for item in data:
                if isinstance(item, dict):
                    participant = CodexObject(
                        title=item.get("title", "Untitled"),
                        premise=item.get("premise", ""),
                        genre=item.get("genre", ""),
                        themes=item.get("themes", []),
                        setting=item.get("setting", ""),
                        main_character=item.get("main_character", ""),
                        conflict=item.get("conflict", ""),
                        tone=item.get("tone", ""),
                        length=item.get("length", "novel")
                    )
                    participants.append(participant)
            
            return participants
            
        elif uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            
            participants = []
            for _, row in df.iterrows():
                participant = CodexObject(
                    title=row.get("title", "Untitled"),
                    premise=row.get("premise", ""),
                    genre=row.get("genre", ""),
                    themes=row.get("themes", "").split(",") if row.get("themes") else [],
                    setting=row.get("setting", ""),
                    main_character=row.get("main_character", ""),
                    conflict=row.get("conflict", ""),
                    tone=row.get("tone", ""),
                    length=row.get("length", "novel")
                )
                participants.append(participant)
            
            return participants
    
    except Exception as e:
        st.error(f"Error loading participants from file: {str(e)}")
        return []

def generate_tournament_participants(count: int, theme: str = "") -> List[CodexObject]:
    """Generate participants for tournament using the ideation system."""
    # This would integrate with the idea generation system
    # For now, return placeholder participants
    
    participants = []
    
    for i in range(count):
        participant = CodexObject(
            title=f"Generated Idea {i + 1}",
            premise=f"This is a generated premise for idea {i + 1} with theme: {theme}",
            genre="Fantasy" if not theme else theme.title(),
            themes=["adventure", "magic"] if not theme else [theme],
            setting="A mystical realm",
            main_character="A young hero",
            conflict="Must overcome great challenges",
            tone="Epic and adventurous",
            length="novel"
        )
        participants.append(participant)
    
    return participants

if __name__ == "__main__":
    render_tournament_interface()