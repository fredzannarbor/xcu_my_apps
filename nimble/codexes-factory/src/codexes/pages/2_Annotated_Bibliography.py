import sys
import os
import logging
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv


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

load_dotenv()



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# Add xcu_my_apps to path for shared modules
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



# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))
print(project_root)

try:
    from codexes.modules.bibliography_managers.zotero2json import get_AI_bibliography, process_zotero_results
except ModuleNotFoundError:
    try:
        from src.codexes.modules.bibliography_managers.zotero2json import get_AI_bibliography, process_zotero_results
    except ImportError:
        st.error("Zotero integration not available. Please ensure zotero2json.py is in the project root.")
        get_AI_bibliography = None
        process_zotero_results = None
        st.stop()

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




@st.cache_data()
def show_bibliography_info():
    st.markdown(
        """*This bibliography is selective in that it covers only those journal articles, books, and news articles that I have found relevant to my work on the AI Lab for Book-Lovers.  It is not an exhaustive review of the entire literature, but it is a good starting point.*

*As far as I can tell, there is no single coherent community of people working on AI for books.  There are many different individuals or small isolated groups, and each has its own unique set of interests. Perhaps an expansion of this list could be a useful tool for building that community.*

**If you know of items about AI & books that should be added to this list, please send them to me via the link in the sidebar!**

*My comments are appended below each entry.  While CMOS17 section 14.10 recommends block indenting annotations, this produces an unbalanced grid, so I have opted to keep comments in standard margins.*

*Default display is in reverse date of publication. Note that there are quite a few non-dated items that are all at the bottom.* 

*Changing sort mode to 'dateModified' sorts by the date that my bibliographic metadata was last modified, so this is a good way to see what I have added recently.*

*Changing sort mode to 'creator' produces an alphabetical list by author. Note there are some missing author names that appear at the bottom.*
***"""

    )
    return

@st.cache_data()
def show_bibliography_sorted(sort="date"):
    with st.spinner("Retrieving bibliography..."):
        try:
            results = get_AI_bibliography(sort=sort)
            t1 = process_zotero_results(results)
            st.markdown(t1, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error retrieving bibliography: {str(e)}")
            raise

with st.expander("About this Bibliography", expanded=False):
    show_bibliography_info()

with st.expander("Questions and Suggestions", expanded=False):
    st.markdown(
        """Please send any questions or suggestions to [me](mailto:wfz@nimblebooks.com). I am always looking for new developments and new collaborators in the books & AI space!""")

with st.expander("Annotated Bibliography", expanded=True):
    with st.form(key="bib_form"):
        a, b = st.columns([5, 1])
        status_string = f"Currently sorted by date of publication. Change sort to: "
        sort_option = a.selectbox(status_string, ("dateModified", "creator", "date"))
        # sort_option = "creator"
        # b = st.markdown(""" """)
        b.markdown("""
    ` `
    ` `
                       """)
        submitted = b.form_submit_button("Go")
        if submitted:
            show_bibliography_sorted(sort=sort_option)
            status_string = f"Currently sorted by {sort_option}. Change sort to: "
        else:
            show_bibliography_sorted(sort="date")

