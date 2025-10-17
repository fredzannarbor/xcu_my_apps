"""
Main ideation dashboard with navigation to all ideation features.
Provides overview of ideation activities and quick access to all workflows.
"""


import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
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
from codexes.modules.ideation.storage.database_manager import IdeationDatabase, DatabaseManager


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

# Import with graceful fallback for missing modules
try:
    from codexes.modules.ideation.tournament.tournament_engine import TournamentEngine
    TOURNAMENT_ENGINE_AVAILABLE = True
except ImportError:
    TournamentEngine = None
    TOURNAMENT_ENGINE_AVAILABLE = False

try:
    from codexes.modules.ideation.continuous.continuous_generator import ContinuousGenerationEngine
    CONTINUOUS_GENERATOR_AVAILABLE = True
except ImportError:
    ContinuousGenerationEngine = None 
    CONTINUOUS_GENERATOR_AVAILABLE = False

try:
    from codexes.modules.ideation.collaboration.session_manager import CollaborationSessionManager
    COLLABORATION_AVAILABLE = True
except ImportError:
    CollaborationSessionManager = None
    COLLABORATION_AVAILABLE = False
    
try:
    from codexes.modules.ideation.analytics.pattern_analyzer import PatternAnalyzer
    PATTERN_ANALYZER_AVAILABLE = True
except ImportError:
    PatternAnalyzer = None
    PATTERN_ANALYZER_AVAILABLE = False

def render_ideation_dashboard():
    """Render the main ideation dashboard."""
    st.title("🧠 Ideation Dashboard")
    st.markdown("Welcome to the advanced ideation system. Explore ideas, run tournaments, and collaborate with others.")
    
    # Initialize session state with graceful fallbacks
    if 'tournament_engine' not in st.session_state:
        if TOURNAMENT_ENGINE_AVAILABLE:
            try:
                # Create database manager with default path
                db_manager = DatabaseManager("data/ideation_database.db")
                database = IdeationDatabase(db_manager)
                st.session_state.tournament_engine = TournamentEngine(database)
                logger.info("Tournament Engine initialized successfully")
            except Exception as e:
                st.session_state.tournament_engine = None
                st.error(f"Failed to initialize Tournament Engine: {str(e)}")
                logger.error(f"Tournament Engine initialization failed: {e}")
        else:
            st.session_state.tournament_engine = None
            
    if 'continuous_generator' not in st.session_state:
        if CONTINUOUS_GENERATOR_AVAILABLE:
            try:
                st.session_state.continuous_generator = ContinuousGenerationEngine()
            except Exception:
                st.session_state.continuous_generator = None
        else:
            st.session_state.continuous_generator = None
            
    if 'collaboration_manager' not in st.session_state:
        if COLLABORATION_AVAILABLE:
            try:
                st.session_state.collaboration_manager = CollaborationSessionManager()
            except Exception:
                st.session_state.collaboration_manager = None
        else:
            st.session_state.collaboration_manager = None
            
    if 'pattern_analyzer' not in st.session_state:
        if PATTERN_ANALYZER_AVAILABLE:
            try:
                st.session_state.pattern_analyzer = PatternAnalyzer()
            except Exception:
                st.session_state.pattern_analyzer = None
        else:
            st.session_state.pattern_analyzer = None
    
    # Main navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🏆 Tournaments")
        if st.session_state.tournament_engine:
            try:
                tournament_stats = st.session_state.tournament_engine.get_tournament_statistics()
                if tournament_stats and isinstance(tournament_stats, dict):
                    st.metric("Active Tournaments", tournament_stats.get("active_tournaments", 0))
                    st.metric("Completed Tournaments", tournament_stats.get("completed_tournaments", 0))
                else:
                    st.metric("Active Tournaments", "N/A")
                    st.metric("Completed Tournaments", "N/A")
                    st.info("Tournament statistics data unavailable")
            except (AttributeError, TypeError, Exception) as e:
                st.metric("Active Tournaments", "N/A")
                st.metric("Completed Tournaments", "N/A")
                st.info(f"Tournament statistics error: {type(e).__name__}")
                logger.warning(f"Tournament statistics error: {e}")
        else:
            st.metric("Active Tournaments", "N/A")
            st.metric("Completed Tournaments", "N/A")
            st.info("Tournament Engine not available")
        
        if st.button("Create Tournament", key="create_tournament_btn"):
            if st.session_state.tournament_engine:
                st.session_state.page = "tournament_creation"
                st.rerun()
            else:
                st.error("Tournament Engine not available")
        
        if st.button("View Tournaments", key="view_tournaments_btn"):
            if st.session_state.tournament_engine:
                st.session_state.page = "tournament_management"
                st.rerun()
            else:
                st.error("Tournament Engine not available")
    
    with col2:
        st.subheader("🔄 Continuous Generation")
        if st.session_state.continuous_generator:
            try:
                gen_stats = st.session_state.continuous_generator.get_generation_statistics()
                st.metric("Active Sessions", gen_stats.get("active_sessions", 0))
                st.metric("Total Ideas Generated", gen_stats.get("overall_statistics", {}).get("total_ideas_generated", 0))
            except AttributeError:
                st.metric("Active Sessions", "N/A")
                st.metric("Total Ideas Generated", "N/A")
                st.info("Generation statistics unavailable")
        else:
            st.metric("Active Sessions", "N/A")
            st.metric("Total Ideas Generated", "N/A")
            st.info("Continuous Generator not available")
        
        if st.button("Start Generation", key="start_generation_btn"):
            if st.session_state.continuous_generator:
                st.session_state.page = "continuous_generation"
                st.rerun()
            else:
                st.error("Continuous Generator not available")
        
        if st.button("Monitor Sessions", key="monitor_sessions_btn"):
            if st.session_state.continuous_generator:
                st.session_state.page = "generation_monitoring"
                st.rerun()
            else:
                st.error("Continuous Generator not available")
    
    with col3:
        st.subheader("👥 Collaboration")
        if st.session_state.collaboration_manager:
            try:
                collab_stats = st.session_state.collaboration_manager.get_session_statistics()
                st.metric("Active Sessions", collab_stats.get("active_sessions", 0))
                st.metric("Total Sessions", collab_stats.get("total_sessions", 0))
            except AttributeError:
                st.metric("Active Sessions", "N/A")
                st.metric("Total Sessions", "N/A")
                st.info("Collaboration statistics unavailable")
        else:
            st.metric("Active Sessions", "N/A")
            st.metric("Total Sessions", "N/A")
            st.info("Collaboration Manager not available")
        
        if st.button("Create Session", key="create_session_btn"):
            if st.session_state.collaboration_manager:
                st.session_state.page = "collaboration_session"
                st.rerun()
            else:
                st.error("Collaboration Manager not available")
        
        if st.button("Join Session", key="join_session_btn"):
            if st.session_state.collaboration_manager:
                st.session_state.page = "session_browser"
                st.rerun()
            else:
                st.error("Collaboration Manager not available")
    
    st.divider()
    
    # Quick actions row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Analytics", key="analytics_btn"):
            st.session_state.page = "analytics_dashboard"
            st.rerun()
    
    with col2:
        if st.button("🎭 Synthetic Readers", key="readers_btn"):
            st.session_state.page = "synthetic_readers"
            st.rerun()
    
    with col3:
        if st.button("📚 Series Generator", key="series_btn"):
            st.session_state.page = "series_generation"
            st.rerun()
    
    with col4:
        if st.button("🧩 Element Recombination", key="elements_btn"):
            st.session_state.page = "element_recombination"
            st.rerun()
    
    st.divider()
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    # Create tabs for different activity types
    tab1, tab2, tab3 = st.tabs(["Tournaments", "Generation", "Collaboration"])
    
    with tab1:
        render_recent_tournaments()
    
    with tab2:
        render_recent_generation()
    
    with tab3:
        render_recent_collaboration()

def render_recent_tournaments():
    """Render recent tournament activity."""
    tournament_engine = st.session_state.get('tournament_engine')
    
    if not tournament_engine:
        st.info("Tournament Engine not available")
        return
    
    # Get recent tournaments
    try:
        recent_tournaments = tournament_engine.get_completed_tournaments(limit=5)
        if recent_tournaments is None:
            recent_tournaments = []
    except (AttributeError, TypeError, Exception) as e:
        st.info(f"Tournament data unavailable: {type(e).__name__}")
        logger.warning(f"Error getting recent tournaments: {e}")
        return
    
    if recent_tournaments:
        for tournament in recent_tournaments:
            try:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        tournament_name = getattr(tournament, 'name', 'Unnamed Tournament')
                        participant_count = getattr(tournament, 'participant_count', 0)
                        st.write(f"**{tournament_name}**")
                        st.caption(f"Participants: {participant_count}")
                    
                    with col2:
                        try:
                            winner_uuid = None
                            if tournament and hasattr(tournament, 'get_winner'):
                                winner_uuid = tournament.get_winner()
                            if winner_uuid:
                                st.write(f"🏆 Winner: {winner_uuid}")
                            else:
                                st.write("⏳ In Progress")
                        except Exception:
                            st.write("⏳ Status Unknown")
                    
                    with col3:
                        tournament_uuid = getattr(tournament, 'uuid', f"tournament_{id(tournament)}")
                        if st.button("View", key=f"view_tournament_{tournament_uuid}"):
                            st.session_state.selected_tournament = tournament_uuid
                            st.session_state.page = "tournament_results"
                            st.rerun()
            except Exception as e:
                st.error(f"Error displaying tournament: {type(e).__name__}")
                logger.warning(f"Error displaying tournament: {e}")
    else:
        st.info("No recent tournaments found. Create your first tournament!")

def render_recent_generation():
    """Render recent generation activity."""
    generator = st.session_state.get('continuous_generator')
    
    if not generator:
        st.info("Continuous Generator not available")
        return
    
    # Get recent sessions
    try:
        recent_sessions = generator.get_completed_sessions(limit=5)
        if recent_sessions is None:
            recent_sessions = []
    except (AttributeError, TypeError, Exception) as e:
        st.info(f"Generation data unavailable: {type(e).__name__}")
        logger.warning(f"Error getting recent generation sessions: {e}")
        return
    
    if recent_sessions:
        for session in recent_sessions:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{session.session_name}**")
                    st.caption(f"Ideas: {session.total_ideas_generated}")
                
                with col2:
                    success_rate = (session.successful_generations / max(session.total_generations, 1)) * 100
                    st.write(f"📊 Success: {success_rate:.1f}%")
                
                with col3:
                    if st.button("View", key=f"view_session_{session.session_uuid}"):
                        st.session_state.selected_session = session.session_uuid
                        st.session_state.page = "session_details"
                        st.rerun()
    else:
        st.info("No recent generation sessions found. Start continuous generation!")

def render_recent_collaboration():
    """Render recent collaboration activity."""
    collab_manager = st.session_state.get('collaboration_manager')
    
    if not collab_manager:
        st.info("Collaboration Manager not available")
        return
    
    # Get recent sessions
    try:
        completed_sessions = getattr(collab_manager, 'completed_sessions', [])
        recent_sessions = completed_sessions[-5:] if completed_sessions else []
        if recent_sessions is None:
            recent_sessions = []
    except (AttributeError, TypeError, Exception) as e:
        st.info(f"Collaboration data unavailable: {type(e).__name__}")
        logger.warning(f"Error getting recent collaboration sessions: {e}")
        return
    
    if recent_sessions:
        for session in recent_sessions:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{session.session_name}**")
                    st.caption(f"Participants: {len(session.participants)}")
                
                with col2:
                    st.write(f"💡 Ideas: {len(session.generated_ideas)}")
                
                with col3:
                    if st.button("View", key=f"view_collab_{session.session_uuid}"):
                        st.session_state.selected_collab_session = session.session_uuid
                        st.session_state.page = "collaboration_results"
                        st.rerun()
    else:
        st.info("No recent collaboration sessions found. Create a collaborative session!")

def main():
    """Main function for Streamlit page compatibility."""
    render_ideation_dashboard()

if __name__ == "__main__":
    main()