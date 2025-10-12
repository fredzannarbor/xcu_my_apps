import streamlit as st
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Define the access level required for each page.
# The key is the path to the page file.
# The value is the minimum role required: 'public', 'user', 'subscriber', 'admin'.
PAGE_ACCESS_LEVELS: Dict[str, str] = {
    "pages/1_Home.py": "public",
    "pages/6_Bookstore.py": "public",
    "pages/2_Annotated_Bibliography.py": "public",
    "pages/13_Annotated_Bibliography.py": "public",
    "pages/22_AI_Social_Feed.py": "public",
    "pages/ideation_dashboard.py": "subscriber",
    "pages/15_Ideation_and_Development.py": "admin",
    "pages/3_Manuscript_Enhancement.py": "subscriber",
    "pages/4_Metadata_and_Distribution.py": "admin",
    "pages/5_Settings_and_Commerce.py": "admin",
    "pages/7_Admin_Dashboard.py": "admin",
    "pages/8_Login_Register.py": "public",
    "pages/10_Book_Pipeline.py": "admin",
    "pages/11_Backmatter_Manager.py": "admin",
    "pages/13_Bibliography_Shopping.py": "admin",
    "pages/15_Imprint_Display.py": "public",
    "pages/14_Annotated_Bibliography.py": "public",
    "pages/18_Imprint_Administration.py": "admin",
    "pages/20_Enhanced_Imprint_Creator.py": "admin",
    "pages/21_Imprint_Ideas_Tournament.py": "admin",
    "pages/Configuration_Management.py": "admin",
    # Finance Analysis Pages
    "pages/26_Rights_Analytics.py": "admin",
    "pages/27_Max_Bialystok_Financial.py": "admin",
    "pages/28_Leo_Bloom_Analytics.py": "admin",
    "pages/29_Imprint_Financial_Dashboard.py": "admin",
    "pages/30_Books_In_Print_Financial.py": "admin",
    "pages/30_Sales_Analysis.py": "admin",
    "pages/31_FRO_Diagnostics.py": "admin",
    "pages/32_PDF_Harvester.py": "admin"
}
# Define the hierarchy of roles. Higher numbers have more access.
ACCESS_HIERARCHY: Dict[str, int] = {
    "public": 0,
    "user": 1,
    "subscriber": 2,
    "admin": 3,
    "multi-organizational": 1,
    "personal": 1
}


def get_user_role(username: str, config: Dict[str, Any]) -> str:
    '''
    Retrieves the role for a given username from the authenticator config.

    Args:
        username (str): The username of the logged-in user.
        config (Dict[str, Any]): The loaded authenticator configuration.

    Returns:
        str: The user's role, or 'public' if not found.
    '''
    return config.get('credentials', {}).get('usernames', {}).get(username, {}).get('role', 'public')


def get_allowed_pages(user_role: str, all_pages: List[st.Page]) -> List[st.Page]:
    '''
    Filters the list of all pages to only those the user's role can access.

    Args:
        user_role (str): The role of the current user (e.g., 'public', 'user', 'admin').
        all_pages (List[st.Page]): The complete list of st.Page objects for the app.

    Returns:
        List[st.Page]: A filtered list of st.Page objects the user can access.
    '''
    user_access_level = ACCESS_HIERARCHY.get(user_role, 0)
    allowed_pages = []

    logger.info(f"Filtering pages for user role: {user_role} (level {user_access_level})")

    for page in all_pages:
        # Try multiple ways to get the page path
        page_path_str = None

        # Method 1: Try to get from _page attribute
        if hasattr(page, '_page') and page._page:
            full_page_path_str = str(page._page)
            pages_index = max(full_page_path_str.find("pages/"), full_page_path_str.find("pages\\"))
            if pages_index != -1:
                page_path_str = full_page_path_str[pages_index:]

        # Method 2: Try to get from page attribute
        if not page_path_str and hasattr(page, 'page') and page.page:
            full_page_path_str = str(page.page)
            pages_index = max(full_page_path_str.find("pages/"), full_page_path_str.find("pages\\"))
            if pages_index != -1:
                page_path_str = full_page_path_str[pages_index:]

        # Method 3: Try __dict__ inspection
        if not page_path_str:
            page_dict = page.__dict__
            logger.debug(f"Page dict keys: {list(page_dict.keys())}")
            for key, value in page_dict.items():
                if 'page' in key.lower() and value:
                    full_page_path_str = str(value)
                    pages_index = max(full_page_path_str.find("pages/"), full_page_path_str.find("pages\\"))
                    if pages_index != -1:
                        page_path_str = full_page_path_str[pages_index:]
                        break

        # If we still can't find the path, log the page object structure
        if not page_path_str:
            logger.warning(f"Could not extract page path from page object. Available attributes: {dir(page)}")
            logger.warning(f"Page dict: {page.__dict__}")
            continue

        # Normalize path separators
        page_path_str = page_path_str.replace("\\", "/")

        required_role = PAGE_ACCESS_LEVELS.get(page_path_str, 'public')
        required_level = ACCESS_HIERARCHY.get(required_role, 0)

        # Reduced per-page logging to prevent infinite reload loops
        # logger.debug(f"Page: {page_path_str}, Required role: {required_role} (level {required_level}), User level: {user_access_level}")

        if user_access_level >= required_level:
            allowed_pages.append(page)
            # Reduced logging to prevent infinite reload loops
            # logger.debug(f"✓ Added page: {page_path_str}")
        else:
            # logger.debug(f"✗ Blocked page: {page_path_str}")
            pass

    logger.info(f"Allowed {len(allowed_pages)} out of {len(all_pages)} pages for role {user_role}")
    return allowed_pages