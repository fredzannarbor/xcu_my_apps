"""
Shared Authentication System for xtuff.ai Applications

Provides cross-application authentication state management using a shared
SQLite database. Ensures user login, role, and subscription data persists
across all apps in the xcu_my_apps ecosystem.
"""

import streamlit as st
import sqlite3
import bcrypt
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import extra_streamlit_components as stx

logger = logging.getLogger(__name__)

# Shared database location - accessible by all apps
SHARED_AUTH_DB = Path("/Users/fred/xcu_my_apps/shared/auth/auth_sessions.db")
# Shared config location
SHARED_CONFIG_PATH = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/resources/yaml/config.yaml")


class SharedAuthSystem:
    """
    Shared authentication system that persists across all xtuff.ai applications.

    Uses a shared SQLite database to store active sessions, allowing users to
    log in once and access all applications with their credentials and entitlements.
    """

    def __init__(self):
        self.db_path = SHARED_AUTH_DB
        self.config_path = SHARED_CONFIG_PATH
        self._ensure_db_exists()
        self.config = self._load_config()

        # Initialize cookie manager for cross-app SSO
        self.cookie_manager = stx.CookieManager()

        # Initialize session state if needed
        if 'auth_checked' not in st.session_state:
            self._check_active_session()

    def _ensure_db_exists(self):
        """Create the shared auth database and tables if they don't exist."""
        # Create directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                user_name TEXT,
                user_email TEXT,
                user_role TEXT,
                subscription_tier TEXT,
                subscription_status TEXT,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

        logger.info(f"Shared auth database initialized at {self.db_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load authentication configuration from shared config file."""
        try:
            if self.config_path.exists():
                with self.config_path.open('r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return {"credentials": {"usernames": {}}}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"credentials": {"usernames": {}}}

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import secrets
        return secrets.token_urlsafe(32)

    def _check_active_session(self):
        """Check if there's an active session using session state or query params and load it into Streamlit session state."""
        st.session_state.auth_checked = True

        # Try to get session ID from multiple sources
        session_id = None

        # 1. First check if already in session state (persists across reruns in same browser tab)
        if 'shared_session_id' in st.session_state and st.session_state.shared_session_id:
            session_id = st.session_state.shared_session_id
            logger.debug(f"Session ID from session state: {session_id}")

            # Validate it's still valid in the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT expires_at FROM active_sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                expires_at = row[0]
                if datetime.fromisoformat(expires_at) >= datetime.now():
                    # Session still valid, nothing more to do
                    logger.debug(f"Existing session still valid")
                    return
                else:
                    # Session expired
                    logger.info(f"Session in state expired: {session_id}")
                    self._delete_session(session_id)
                    session_id = None
            else:
                # Session doesn't exist in database
                logger.warning(f"Session in state not found in database: {session_id}")
                session_id = None

        # 2. Check query params (for cross-app navigation)
        if not session_id:
            query_params = st.query_params
            if 'session_id' in query_params:
                session_id = query_params['session_id']
                logger.debug(f"Session ID from query params: {session_id}")
                # Remove from URL to clean it up
                del st.query_params['session_id']

        # 3. Check cookies as fallback (might not work reliably)
        if not session_id:
            try:
                cookies = self.cookie_manager.get_all()
                session_id = cookies.get('xtuff_session_id') if cookies else None
                if session_id:
                    logger.debug(f"Session ID from cookie: {session_id}")
            except Exception as e:
                logger.warning(f"Error reading cookies: {e}")

        if not session_id:
            logger.info("No session_id found in any source, initializing empty session")
            self._initialize_empty_session()
            return

        # Load session from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, user_name, user_email, user_role,
                   subscription_tier, subscription_status, expires_at
            FROM active_sessions
            WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            username, user_name, user_email, user_role, sub_tier, sub_status, expires_at = row

            # Check if session expired
            if datetime.fromisoformat(expires_at) < datetime.now():
                logger.info(f"Session expired: {session_id}")
                self._delete_session(session_id)
                self._initialize_empty_session()
                return

            # Load session data into Streamlit session state
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_name = user_name
            st.session_state.user_email = user_email
            st.session_state.user_role = user_role
            st.session_state.subscription_tier = sub_tier or 'free'
            st.session_state.subscription_status = sub_status or 'inactive'
            st.session_state.shared_session_id = session_id

            # Update last accessed time
            self._update_session_access(session_id)

            logger.info(f"Session restored for user: {username}")
        else:
            # Session ID in cookie but not in database (expired/deleted)
            self.cookie_manager.delete('xtuff_session_id')
            self._initialize_empty_session()

    def _initialize_empty_session(self):
        """Initialize an empty (unauthenticated) session state."""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_name = None
        st.session_state.user_email = None
        st.session_state.user_role = 'public'
        st.session_state.subscription_tier = 'free'
        st.session_state.subscription_status = 'inactive'
        st.session_state.shared_session_id = None

    def _update_session_access(self, session_id: str):
        """Update the last accessed time for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE active_sessions
            SET last_accessed = ?
            WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))

        conn.commit()
        conn.close()

    def _delete_session(self, session_id: str):
        """Delete a session from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM active_sessions WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate a user with username and password.

        Returns:
            (success: bool, message: str)
        """
        if not username or not password:
            return False, "Username and password are required"

        # Get user data from config
        user_data = self.config.get("credentials", {}).get("usernames", {}).get(username)
        if not user_data:
            return False, "Invalid username or password"

        # Check password
        stored_password = user_data.get("password", "")
        password_match = False

        if stored_password.startswith("$2b$"):
            # Bcrypt hashed password
            try:
                password_match = bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))
            except Exception as e:
                logger.error(f"Password check error: {e}")
                return False, "Authentication error"
        else:
            # Plain text password (development only)
            password_match = (password == stored_password)

        if not password_match:
            return False, "Invalid username or password"

        # Create session
        session_id = self._generate_session_id()
        now = datetime.now()
        expires = now + timedelta(days=30)

        user_name = user_data.get("name", username)
        user_email = user_data.get("email", "")
        user_role = user_data.get("role", "user")

        # Get subscription info (placeholder - integrate with Stripe later)
        subscription_tier = user_data.get("subscription_tier", "free")
        subscription_status = user_data.get("subscription_status", "inactive")

        # Store session in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO active_sessions
            (session_id, username, user_name, user_email, user_role,
             subscription_tier, subscription_status, created_at, last_accessed, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, username, user_name, user_email, user_role,
              subscription_tier, subscription_status,
              now.isoformat(), now.isoformat(), expires.isoformat()))

        conn.commit()
        conn.close()

        # Update Streamlit session state
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_name = user_name
        st.session_state.user_email = user_email
        st.session_state.user_role = user_role
        st.session_state.subscription_tier = subscription_tier
        st.session_state.subscription_status = subscription_status
        st.session_state.shared_session_id = session_id

        # Set browser cookie for cross-app SSO
        self.cookie_manager.set(
            'xtuff_session_id',
            session_id,
            max_age=30*24*60*60,  # 30 days in seconds
            key=f"set_cookie_{session_id[:8]}"  # Unique key for Streamlit
        )

        logger.info(f"User {username} authenticated successfully, cookie set")

        return True, f"Welcome back, {user_name}!"

    def logout(self):
        """Logout the current user and clear their session."""
        if 'shared_session_id' in st.session_state and st.session_state.shared_session_id:
            self._delete_session(st.session_state.shared_session_id)

        # Delete browser cookie
        self.cookie_manager.delete('xtuff_session_id')

        # Clear session state
        self._initialize_empty_session()

        logger.info("User logged out, cookie cleared")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('authenticated', False)

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        return {
            'username': st.session_state.get('username'),
            'user_name': st.session_state.get('user_name'),
            'user_email': st.session_state.get('user_email'),
            'user_role': st.session_state.get('user_role', 'public'),
            'subscription_tier': st.session_state.get('subscription_tier', 'free'),
            'subscription_status': st.session_state.get('subscription_status', 'inactive'),
        }

    def register_user(self, username: str, password: str, email: str, name: str, role: str = "user") -> bool:
        """
        Register a new user by adding them to the config file.

        Args:
            username: Unique username
            password: Plain text password (will be hashed with bcrypt)
            email: User email address
            name: User's full name
            role: User role (default: "user")

        Returns:
            bool: True if registration successful, False if username/email already exists
        """
        # Check if username already exists
        if username in self.config.get("credentials", {}).get("usernames", {}):
            logger.warning(f"Registration failed: username '{username}' already exists")
            return False

        # Check if email already exists
        for existing_user, user_data in self.config.get("credentials", {}).get("usernames", {}).items():
            if user_data.get("email") == email:
                logger.warning(f"Registration failed: email '{email}' already in use")
                return False

        # Hash password with bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Add user to config
        if "credentials" not in self.config:
            self.config["credentials"] = {}
        if "usernames" not in self.config["credentials"]:
            self.config["credentials"]["usernames"] = {}

        self.config["credentials"]["usernames"][username] = {
            "name": name,
            "email": email,
            "password": password_hash,
            "role": role,
            "subscription_tier": "free",
            "subscription_status": "inactive",
            "created_at": datetime.now().isoformat()
        }

        # Save config file
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with self.config_path.open('w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"New user registered: {username} ({email})")
            return True
        except Exception as e:
            logger.error(f"Failed to save config after registration: {e}")
            # Rollback config change
            del self.config["credentials"]["usernames"][username]
            return False

    def cleanup_expired_sessions(self):
        """Remove expired sessions from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM active_sessions
            WHERE expires_at < ?
        """, (datetime.now().isoformat(),))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired sessions")


# Global instance
_shared_auth = None


def get_shared_auth() -> SharedAuthSystem:
    """Get the global shared authentication instance."""
    global _shared_auth
    if _shared_auth is None:
        _shared_auth = SharedAuthSystem()
    return _shared_auth


# Convenience functions
def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return get_shared_auth().is_authenticated()


def get_user_info() -> Dict[str, Any]:
    """Get current user information."""
    return get_shared_auth().get_user_info()


def authenticate(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate a user."""
    return get_shared_auth().authenticate(username, password)


def logout():
    """Logout current user."""
    get_shared_auth().logout()
