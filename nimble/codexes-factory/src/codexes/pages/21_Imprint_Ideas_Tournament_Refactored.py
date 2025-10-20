"""
Tournament of Imprint Ideas (Refactored with OO Architecture)

A competitive tournament system for evaluating and selecting the best
new imprint concepts using AI-assisted evaluation and user input.

This is the refactored version using Rich Domain Models and Repository Pattern.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Optional
import logging
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add paths for imports
sys.path.insert(0, '/Users/fred/my-apps')
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import shared authentication system (optional for testing)
try:
    from shared.auth import is_authenticated, get_user_info
    AUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Shared authentication not available: {e}")
    AUTH_AVAILABLE = False
    # Mock functions for testing
    def is_authenticated():
        return True
    def get_user_info():
        return {'username': 'test_user', 'user_name': 'Test User', 'user_email': 'test@example.com'}

# Import with fallback pattern
try:
    from codexes.core.llm_caller import call_model_with_prompt
except ImportError:
    from src.codexes.core.llm_caller import call_model_with_prompt

# Import new OO architecture components
try:
    from codexes.domain.models.tournament import Tournament, ImprintIdea, TournamentStatus
    from codexes.infrastructure.repositories.tournament_repository import TournamentRepository
    from codexes.infrastructure.repositories.imprint_repository import ImprintRepository
    from codexes.application.services.tournament_service import TournamentService
    from codexes.application.services.imprint_creation_service import ImprintCreationService
except ImportError:
    from src.codexes.domain.models.tournament import Tournament, ImprintIdea, TournamentStatus
    from src.codexes.infrastructure.repositories.tournament_repository import TournamentRepository
    from src.codexes.infrastructure.repositories.imprint_repository import ImprintRepository
    from src.codexes.application.services.tournament_service import TournamentService
    from src.codexes.application.services.imprint_creation_service import ImprintCreationService


# Dependency Injection - Create services once
@st.cache_resource
def get_tournament_service() -> TournamentService:
    """Get tournament service with all dependencies."""
    base_path = Path(__file__).parent.parent.parent.parent
    tournament_repo = TournamentRepository(base_path)
    imprint_repo = ImprintRepository(base_path)

    # Create imprint service
    imprint_service = ImprintCreationService(imprint_repo)

    # Create tournament service
    return TournamentService(
        repository=tournament_repo,
        idea_generator=None,  # Will use LLM directly
        imprint_service=imprint_service
    )


def main():
    """Main tournament interface using OO architecture."""
    # Sync session state from shared auth
    if is_authenticated():
        user_info = get_user_info()
        st.session_state.username = user_info.get('username')
        st.session_state.user_name = user_info.get('user_name')
        st.session_state.user_email = user_info.get('user_email')
        logger.info(f"User authenticated: {st.session_state.username}")
    else:
        st.session_state.username = st.session_state.get('username')

    # Get tournament service
    service = get_tournament_service()

    # Get tournament size from session state or default
    tournament_size = st.session_state.get('tournament_size', 32)

    st.title(f"🏆 Tournament of {tournament_size} Imprint Ideas")
    st.markdown("*Discover the next great publishing imprint through competitive evaluation*")

    # Tournament tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Setup Tournament",
        "⚔️ Run Tournament",
        "🏅 Results",
        "💡 Generate Ideas"
    ])

    with tab1:
        render_tournament_setup(service)

    with tab2:
        render_tournament_runner(service)

    with tab3:
        render_tournament_results(service)

    with tab4:
        render_idea_generator(service)


def render_tournament_setup(service: TournamentService):
    """Set up a new tournament using OO service."""
    st.subheader("🎯 Tournament Setup")

    # Check for existing tournament
    current_tournament = service.get_active_tournament()

    if current_tournament:
        st.info(f"Current tournament: **{current_tournament.name}** ({current_tournament.status.value})")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Current Tournament"):
                st.session_state.view_current = True
                st.rerun()

        with col2:
            if st.button("🗑️ Clear & Start New"):
                # Archive current by creating new tournament
                st.session_state.clear_tournament = True
                st.rerun()

        if st.session_state.get("view_current"):
            display_tournament_overview(current_tournament)
            return

    # Upload existing ideas section
    st.markdown("### 📊 Upload Existing Imprint Ideas")

    uploaded_file = st.file_uploader(
        "Upload your imprint ideas spreadsheet",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a CSV or Excel file with your partial imprint ideas"
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

            # Store in session state
            st.session_state['uploaded_imprint_ideas'] = df.to_dict('records')

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    st.markdown("---")

    # Create new tournament
    st.markdown("### Create New Tournament")

    uploaded_ideas_count = len(st.session_state.get('uploaded_imprint_ideas', []))
    if uploaded_ideas_count > 0:
        st.info(f"📊 You have {uploaded_ideas_count} uploaded ideas ready to use")

    with st.form("tournament_setup"):
        col1, col2 = st.columns(2)

        with col1:
            tournament_name = st.text_input(
                "Tournament Name",
                value=f"Imprint Ideas Tournament {pd.Timestamp.now().strftime('%B %Y')}"
            )

            tournament_size = st.number_input(
                "Tournament Size",
                min_value=2,
                max_value=256,
                value=uploaded_ideas_count if uploaded_ideas_count >= 2 else 16,
                help="Number of imprint ideas (any number 2-256). Non-power-of-2 will use byes."
            )

            st.session_state.tournament_size = tournament_size

            # Show tournament structure info
            if _is_power_of_2(tournament_size):
                st.success(f"✅ Perfect bracket: {tournament_size} participants, no byes needed")
            else:
                next_power = _next_power_of_2(tournament_size)
                byes_needed = next_power - tournament_size
                st.info(f"📋 {tournament_size} participants + {byes_needed} byes → {next_power}-slot bracket")

            user_ideas_count = st.number_input(
                "Your Ideas",
                min_value=0,
                max_value=tournament_size,
                value=min(uploaded_ideas_count, tournament_size) if uploaded_ideas_count > 0 else max(1, tournament_size // 4),
                help="Number of ideas you'll provide (including uploaded)"
            )

            llm_ideas_count = st.number_input(
                "AI Generated Ideas",
                min_value=0,
                max_value=tournament_size,
                value=tournament_size - user_ideas_count,
                help="Number of ideas for AI to generate"
            )

            total_ideas = user_ideas_count + llm_ideas_count
            if total_ideas != tournament_size:
                st.warning(f"Total ideas must equal {tournament_size} (currently {total_ideas})")

        with col2:
            evaluation_criteria = st.multiselect(
                "Evaluation Criteria",
                ["Commercial Viability", "Editorial Innovation", "Market Gap",
                 "Brand Potential", "Audience Appeal", "Production Feasibility",
                 "Competitive Advantage", "Cultural Relevance"],
                default=["Commercial Viability", "Editorial Innovation", "Market Gap"]
            )

            tournament_duration = st.selectbox(
                "Tournament Duration",
                ["1 Week", "2 Weeks", "1 Month"],
                index=1
            )

            allow_public_voting = st.checkbox(
                "Allow Public Voting",
                value=True,
                help="Let website visitors vote on imprint ideas"
            )

        if st.form_submit_button("🚀 Create Tournament"):
            if total_ideas == tournament_size and tournament_name:
                try:
                    # Create tournament using service
                    tournament = service.create_tournament(
                        name=tournament_name,
                        size=tournament_size,
                        evaluation_criteria=evaluation_criteria,
                        allow_public_voting=allow_public_voting
                    )

                    st.success(f"✅ Tournament '{tournament_name}' created!")
                    st.info("Next: Add your imprint ideas and generate AI ideas")
                    st.session_state.tournament_created = True
                    st.rerun()

                except Exception as e:
                    st.error(f"Failed to create tournament: {e}")
                    logger.error(f"Tournament creation failed: {e}")
            else:
                st.error(f"Please ensure {tournament_size} total ideas and provide a tournament name")


def render_tournament_runner(service: TournamentService):
    """Run the active tournament using OO service."""
    st.subheader("⚔️ Tournament Runner")

    tournament = service.get_active_tournament()

    if not tournament:
        st.warning("No active tournament. Create one in the Setup tab.")
        return

    st.markdown(f"### {tournament.name}")
    st.write(f"**Status**: {tournament.status.value}")
    st.write(f"**Ideas**: {len(tournament.ideas)}/{tournament.tournament_size}")

    # Tournament status and actions
    if tournament.status == TournamentStatus.SETUP:
        render_idea_collection(service, tournament)
    elif tournament.status == TournamentStatus.RUNNING:
        render_bracket_voting(service, tournament)
    elif tournament.status == TournamentStatus.COMPLETED:
        render_tournament_completion(service, tournament)


def render_idea_collection(service: TournamentService, tournament: Tournament):
    """Collect imprint ideas for the tournament using OO models."""
    st.markdown("### 💡 Collect Imprint Ideas")

    user_ideas = [idea for idea in tournament.ideas if idea.source == 'user']
    ai_ideas = [idea for idea in tournament.ideas if idea.source == 'ai']

    # Note: config is stored in tournament but not exposed directly
    # We'll use tournament size directly
    user_target = tournament.tournament_size // 4  # Example: 25% user ideas
    ai_target = tournament.tournament_size - user_target

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### Your Ideas ({len(user_ideas)}/{user_target})")

        if len(user_ideas) < user_target:
            with st.form("add_user_idea"):
                idea_name = st.text_input("Imprint Name")
                idea_charter = st.text_area("Editorial Charter", height=100)
                idea_focus = st.text_input("Market Focus")

                if st.form_submit_button("Add Your Idea"):
                    if idea_name and idea_charter:
                        # Create ImprintIdea domain object
                        user_idea = ImprintIdea(
                            name=idea_name,
                            charter=idea_charter,
                            focus=idea_focus,
                            source="user"
                        )

                        # Add via service
                        service.add_user_idea(tournament, user_idea)
                        st.success(f"Added idea: {idea_name}")
                        st.rerun()
                    else:
                        st.error("Please provide name and charter")

        # Display user ideas
        for idea in user_ideas:
            with st.expander(f"💡 {idea.name}"):
                st.write(f"**Charter**: {idea.charter}")
                st.write(f"**Focus**: {idea.focus}")

    with col2:
        st.markdown(f"#### AI Generated Ideas ({len(ai_ideas)}/{ai_target})")

        if len(ai_ideas) < ai_target:
            needed_ideas = ai_target - len(ai_ideas)

            if st.button(f"🤖 Generate {min(5, needed_ideas)} AI Ideas"):
                with st.spinner("Generating AI ideas..."):
                    try:
                        # Generate using service
                        new_ideas = _generate_ai_ideas_inline(
                            tournament,
                            min(5, needed_ideas)
                        )

                        # Add to tournament
                        for idea in new_ideas:
                            service.add_user_idea(tournament, idea)

                        st.success(f"Generated {len(new_ideas)} AI ideas!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to generate AI ideas: {e}")
                        logger.error(f"AI idea generation failed: {e}")

        # Display AI ideas
        for idea in ai_ideas[-5:]:  # Show last 5
            with st.expander(f"🤖 {idea.name}"):
                st.write(f"**Charter**: {idea.charter}")
                st.write(f"**Focus**: {idea.focus}")

    # Start tournament when ready
    if tournament.can_start():
        st.success(f"🎉 All {tournament.tournament_size} ideas collected!")
        if st.button("🏁 Start Tournament"):
            try:
                service.start_tournament(tournament)
                st.success("Tournament started!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to start tournament: {e}")
    else:
        needed = tournament.tournament_size - len(tournament.ideas)
        st.info(f"Collect {needed} more ideas to start the tournament")


def render_bracket_voting(service: TournamentService, tournament: Tournament):
    """Render tournament bracket voting interface using OO models."""
    st.markdown("### ⚔️ Tournament Brackets")

    current_round = tournament.get_current_round()

    if not current_round:
        st.info("Tournament brackets not yet created")
        return

    st.write(f"**Current Round**: {current_round.round_number}")

    # Display matchups for current round
    st.markdown(f"#### Round {current_round.round_number} Matchups")

    for i, matchup in enumerate(current_round.matchups):
        if not matchup.is_complete:
            render_matchup_voting(service, tournament, matchup, i)

    # Check if round is complete
    if current_round.is_complete:
        if st.button("Advance to Next Round"):
            tournament.advance_round()
            service.repository.save(tournament)
            st.rerun()


def render_matchup_voting(
    service: TournamentService,
    tournament: Tournament,
    matchup,
    matchup_idx: int
):
    """Render individual matchup voting using OO models."""
    idea1 = matchup.idea1
    idea2 = matchup.idea2

    if not idea1 or not idea2:
        st.error("Invalid matchup - missing ideas")
        return

    st.markdown(f"#### Matchup {matchup_idx + 1}")

    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        st.markdown(f"**{idea1.name}**")
        st.write(idea1.charter)
        st.write(f"*Focus: {idea1.focus}*")

        if st.button(f"Vote for {idea1.name}", key=f"vote_1_{matchup.id}"):
            try:
                service.record_vote(tournament, matchup.id, idea1.id)
                st.success("Vote recorded!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to record vote: {e}")

    with col2:
        st.markdown("**VS**")
        st.markdown("---")
        st.write("🏆")

    with col3:
        st.markdown(f"**{idea2.name}**")
        st.write(idea2.charter)
        st.write(f"*Focus: {idea2.focus}*")

        if st.button(f"Vote for {idea2.name}", key=f"vote_2_{matchup.id}"):
            try:
                service.record_vote(tournament, matchup.id, idea2.id)
                st.success("Vote recorded!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to record vote: {e}")


def render_tournament_completion(service: TournamentService, tournament: Tournament):
    """Display tournament completion status."""
    st.markdown("### 🏆 Tournament Complete!")

    if tournament.winner:
        st.balloons()
        st.markdown(f"## 🎉 Winner: {tournament.winner.name}")
        st.markdown(f"**Charter**: {tournament.winner.charter}")
        st.markdown(f"**Focus**: {tournament.winner.focus}")

        if st.button("🚀 Create This Imprint"):
            try:
                imprint = service.create_imprint_from_winner(tournament)
                st.success(f"Created imprint: {imprint.name}")
                st.info("Visit Imprint Administration to configure further settings")
            except Exception as e:
                st.error(f"Failed to create imprint: {e}")


def render_tournament_results(service: TournamentService):
    """Display tournament results using OO models."""
    st.subheader("🏅 Tournament Results")

    tournament = service.get_active_tournament()

    if not tournament:
        st.info("No tournament results available")
        return

    if tournament.status == TournamentStatus.COMPLETED:
        render_tournament_completion(service, tournament)
    else:
        st.info(f"Tournament status: {tournament.status.value}")
        st.write(f"Current ideas: {len(tournament.ideas)}")

        if tournament.rounds:
            st.write(f"Current round: {tournament.get_current_round().round_number if tournament.get_current_round() else 'N/A'}")


def render_idea_generator(service: TournamentService):
    """Generate additional imprint ideas for inspiration."""
    st.subheader("💡 Imprint Idea Generator")

    st.markdown("Generate inspiration for new imprint concepts")

    with st.form("idea_generation"):
        col1, col2 = st.columns(2)

        with col1:
            focus_areas = st.multiselect(
                "Focus Areas",
                ["Nonfiction", "Business", "Self-Help", "Science", "Technology",
                 "History", "Biography", "Pop Culture", "Movies and TV",
                 "Philosophy", "Art & Design", "Random", "Emerging Trends"],
                default=["Emerging Trends", "Nonfiction"]
            )

            additional_focus = st.text_area(
                "Additional Focus Areas",
                help="Enter additional focus areas separated by semicolons"
            )
            if additional_focus:
                focus_areas += additional_focus.split(";")

            target_market = st.selectbox(
                "Target Market",
                ["General Readers", "Young Adults", "Seniors", "8-12 years old",
                 "Infrequent Readers", "Industry Specialists", "International Audiences",
                 "Niche Communities"]
            )

        with col2:
            innovation_level = st.slider(
                "Innovation Level",
                0.0, 1.0, 0.7,
                help="0.0 = Traditional, 1.0 = Highly Experimental"
            )

            num_ideas = st.number_input("Number of Ideas", min_value=1, max_value=10, value=5)

        if st.form_submit_button("Generate Ideas"):
            if focus_areas:
                with st.spinner("Generating ideas..."):
                    ideas = _generate_inspiration_ideas(
                        focus_areas, target_market, innovation_level, num_ideas
                    )

                    st.markdown("### Generated Imprint Ideas")

                    for i, idea in enumerate(ideas):
                        with st.expander(f"💡 {idea.get('name', 'Unknown')}", expanded=True):
                            st.write(f"**Charter**: {idea.get('charter', 'No charter')}")
                            st.write(f"**Positioning**: {idea.get('positioning', 'No positioning')}")
                            st.write(f"**Value Proposition**: {idea.get('value_prop', 'No value prop')}")
                            st.write(f"**Commercial Assessment**: {idea.get('commercial_assessment', 'No assessment')}")
            else:
                st.error("Please select at least one focus area")


def display_tournament_overview(tournament: Tournament):
    """Display overview of current tournament using OO model."""
    st.markdown(f"### Tournament: {tournament.name}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Ideas", len(tournament.ideas))

    with col2:
        st.metric("Status", tournament.status.value)

    with col3:
        if tournament.started_at:
            st.metric("Started", tournament.started_at.strftime('%m/%d'))


# Helper functions

def _is_power_of_2(n: int) -> bool:
    """Check if number is power of 2."""
    return n > 0 and (n & (n - 1)) == 0


def _next_power_of_2(n: int) -> int:
    """Get next power of 2."""
    power = 1
    while power < n:
        power *= 2
    return power


def _generate_ai_ideas_inline(tournament: Tournament, count: int) -> List[ImprintIdea]:
    """Generate AI imprint ideas using LLM (inline implementation)."""
    prompt_config = {
        "messages": [{
            "role": "user",
            "content": f"""Generate {count} innovative publishing imprint concepts. Each imprint should have:

1. A compelling, unique name
2. A clear editorial charter (50-100 words)
3. A specific market focus or niche
4. Commercial viability potential

Return as JSON with this structure:
{{
  "imprints": [
    {{
      "name": "Imprint Name",
      "charter": "Editorial mission and philosophy",
      "focus": "Target market and positioning"
    }}
  ]
}}"""
        }],
        "params": {
            "temperature": 0.8,
            "max_tokens": 2000
        }
    }

    response = call_model_with_prompt(
        model_name="gemini/gemini-2.5-flash",
        prompt_config=prompt_config,
        response_format_type="json_object",
        prompt_name="imprint_tournament_generation"
    )

    ideas = []
    if response.get("parsed_content"):
        imprints_data = response["parsed_content"]

        for imprint_data in imprints_data.get("imprints", [])[:count]:
            idea = ImprintIdea(
                name=imprint_data.get("name", "AI Generated Imprint"),
                charter=imprint_data.get("charter", "AI generated charter"),
                focus=imprint_data.get("focus", "AI generated focus"),
                source="ai"
            )
            ideas.append(idea)

    return ideas


def _generate_inspiration_ideas(
    focus_areas: List[str],
    target_market: str,
    innovation_level: float,
    count: int
) -> List[dict]:
    """Generate inspiration ideas based on parameters."""
    focus_areas_text = ", ".join(focus_areas)

    prompt_config = {
        "messages": [{
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
5. Commercial potential assessment

Format as JSON:
{{
  "ideas": [
    {{
      "name": "Imprint Name",
      "charter": "Editorial mission",
      "positioning": "Market position",
      "value_prop": "Unique advantage",
      "commercial_assessment": "Viability analysis"
    }}
  ]
}}"""
        }]
    }

    try:
        response = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name="imprint_inspiration_generation"
        )

        if response.get("parsed_content"):
            return response["parsed_content"].get("ideas", [])
    except Exception as e:
        logger.error(f"Failed to generate inspiration ideas: {e}")
        st.error(f"Failed to generate ideas: {e}")

    return []


if __name__ == "__main__":
    main()
