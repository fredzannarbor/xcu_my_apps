"""
Simple Authentication System for Codexes Factory
Provides basic login/logout functionality with session state management
"""

import streamlit as st
import bcrypt
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SimpleAuth:
    """Simple authentication system with session state management"""
    
    def __init__(self, config_path: str = "resources/yaml/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.persistent_auth_file = Path(".claude/persistent_auth.json")
        
        # Initialize session state
        if 'auth_initialized' not in st.session_state:
            self._initialize_session_state()
            
        # Check for persistent login
        if not st.session_state.get('authenticated', False):
            self._check_persistent_login()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load authentication configuration"""
        try:
            with self.config_path.open('r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            return {"credentials": {"usernames": {}}}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"credentials": {"usernames": {}}}
    
    def _initialize_session_state(self):
        """Initialize authentication session state"""
        st.session_state.auth_initialized = True
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_role = 'public'
        st.session_state.user_name = None
        st.session_state.user_email = None
    
    def _check_persistent_login(self):
        """Check for persistent login credentials and auto-login if valid"""
        try:
            if not self.persistent_auth_file.exists():
                return
                
            with open(self.persistent_auth_file, 'r') as f:
                persistent_data = json.load(f)
            
            # Check if credentials are still valid (30 days max)
            saved_time = datetime.fromisoformat(persistent_data.get('saved_at', '2000-01-01'))
            if datetime.now() - saved_time > timedelta(days=30):
                # Expired, remove file
                self.persistent_auth_file.unlink()
                return
            
            # Auto-login with saved credentials
            username = persistent_data.get('username')
            password = persistent_data.get('password')  # This would be securely stored in production
            
            if username and password and self._authenticate_direct(username, password):
                logger.info(f"Auto-logged in user {username} from persistent credentials")
                # Trigger UI update to show logged-in state
                st.rerun()
                
        except Exception as e:
            logger.debug(f"Error checking persistent login: {e}")
            # Clean up corrupted file
            if self.persistent_auth_file.exists():
                self.persistent_auth_file.unlink()
    
    def _save_persistent_credentials(self, username: str, password: str, remember_duration_days: int = 30):
        """Save credentials for persistent login"""
        try:
            # Ensure directory exists
            self.persistent_auth_file.parent.mkdir(parents=True, exist_ok=True)
            
            # In production, this should be encrypted/hashed properly
            persistent_data = {
                'username': username,
                'password': password,  # WARNING: In production, use secure token instead
                'saved_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=remember_duration_days)).isoformat()
            }
            
            with open(self.persistent_auth_file, 'w') as f:
                json.dump(persistent_data, f, indent=2)
                
            logger.info(f"Saved persistent credentials for {username}")
            
        except Exception as e:
            logger.error(f"Error saving persistent credentials: {e}")
    
    def _clear_persistent_credentials(self):
        """Clear saved persistent credentials"""
        try:
            if self.persistent_auth_file.exists():
                self.persistent_auth_file.unlink()
                logger.info("Cleared persistent credentials")
        except Exception as e:
            logger.error(f"Error clearing persistent credentials: {e}")
    
    def _authenticate_direct(self, username: str, password: str) -> bool:
        """Direct authentication without UI interaction"""
        try:
            user_data = self.config.get("credentials", {}).get("usernames", {}).get(username)
            if not user_data:
                return False
            
            # Check password
            stored_password = user_data.get("password", "")
            if stored_password.startswith("$2b$"):
                # Bcrypt hashed password
                if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
                    self._set_user_session(username, user_data)
                    return True
            else:
                # Plain text password (for development only)
                if password == stored_password:
                    self._set_user_session(username, user_data)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Direct authentication error: {e}")
            return False

    def authenticate(self, username: str, password: str, remember_me: bool = False) -> bool:
        """Authenticate user with username and password"""
        if not username or not password:
            return False
        
        # Use direct authentication
        success = self._authenticate_direct(username, password)
        
        # Save persistent credentials if requested and authentication successful
        if success and remember_me:
            self._save_persistent_credentials(username, password)
            
        return success
    
    def _set_user_session(self, username: str, user_data: Dict[str, Any]):
        """Set user session data after successful authentication"""
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_role = user_data.get("role", "user")
        st.session_state.user_name = user_data.get("name", username)
        st.session_state.user_email = user_data.get("email", "")
        
        logger.info(f"User {username} authenticated successfully with role {st.session_state.user_role}")
    
    def is_registration_enabled(self) -> bool:
        """Check if registration is enabled in configuration"""
        return self.config.get("registration", {}).get("enabled", True)
    
    def get_default_role(self) -> str:
        """Get the default role for new registrations"""
        return self.config.get("registration", {}).get("default_role", "user")

    def register_user(self, username: str, password: str, name: str, email: str, role: str = None) -> bool:
        """Register a new user"""
        try:
            # Check if registration is enabled
            if not self.is_registration_enabled():
                logger.warning("Registration attempt when registration is disabled")
                return False
            
            # Use default role if none specified
            if role is None:
                role = self.get_default_role()
            
            # Check if user already exists
            if username in self.config.get("credentials", {}).get("usernames", {}):
                logger.warning(f"Registration failed: Username {username} already exists")
                return False
            
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            # Add user to config
            if "credentials" not in self.config:
                self.config["credentials"] = {}
            if "usernames" not in self.config["credentials"]:
                self.config["credentials"]["usernames"] = {}
            
            self.config["credentials"]["usernames"][username] = {
                "name": name,
                "email": email,
                "password": hashed_password,
                "role": role
            }
            
            # Save updated config
            try:
                # Ensure directory exists
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with self.config_path.open('w') as file:
                    yaml.dump(self.config, file, default_flow_style=False, sort_keys=False)
                
                logger.info(f"Successfully registered new user: {username}")
                return True
                
            except Exception as e:
                logger.error(f"Error saving config after registration: {e}")
                # Remove user from memory config since save failed
                del self.config["credentials"]["usernames"][username]
                return False
                
        except Exception as e:
            logger.error(f"Registration error for user {username}: {e}")
            return False

    def logout(self, clear_persistent: bool = False):
        """Logout current user"""
        username = st.session_state.get('username', 'unknown')
        logger.info(f"User {username} logged out")
        
        # Clear persistent credentials if requested
        if clear_persistent:
            self._clear_persistent_credentials()
        
        # Clear authentication session state
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_role = 'public'
        st.session_state.user_name = None
        st.session_state.user_email = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.get('username')
    
    def get_user_role(self) -> str:
        """Get current user role"""
        return st.session_state.get('user_role', 'public')
    
    def get_user_name(self) -> str:
        """Get current user display name"""
        return st.session_state.get('user_name', 'Guest')
    
    def render_registration_form(self) -> bool:
        """Render registration form and return True if registration was attempted"""
        st.subheader("📝 Register for Codexes Factory")
        
        # Check if registration is enabled
        if not self.is_registration_enabled():
            st.warning("Registration is currently disabled. Please contact an administrator for account creation.")
            return False
        
        with st.form("registration_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            name = st.text_input("Full Name", placeholder="Enter your full name")
            email = st.text_input("Email", placeholder="Enter your email address")
            password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            st.info(f"New users will be assigned '{self.get_default_role()}' role by default.")
            
            submitted = st.form_submit_button("Register")
            
            if submitted:
                # Validation
                if not all([username, name, email, password, confirm_password]):
                    st.error("All fields are required.")
                    return True
                
                if password != confirm_password:
                    st.error("Passwords do not match.")
                    return True
                
                if len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                    return True
                
                if "@" not in email:
                    st.error("Please enter a valid email address.")
                    return True
                
                # Attempt registration
                if self.register_user(username, password, name, email):
                    st.success(f"Registration successful! Welcome, {name}!")
                    st.info("You can now log in with your new credentials.")
                    st.rerun()
                else:
                    st.error("Registration failed. Username may already exist.")
                return True
        
        return False

    def render_login_form(self) -> bool:
        """Render login form and return True if login was attempted"""
        st.subheader("🔐 Login to Codexes Factory")

        # Check if there are saved credentials
        if self.persistent_auth_file.exists():
            st.info("🔑 You have saved login credentials. They will be used automatically.")

            if st.button("🗑️ Clear Saved Credentials"):
                self._clear_persistent_credentials()
                st.success("Saved credentials cleared!")
                st.rerun()

        # Show default credentials for convenience (commented out for security)
        #st.info("💡 **Default Login Credentials:**\n\n**Username:** admin\n\n**Password:** hotdogtoy")
        
        with st.form("simple_login_form"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
            
            with col2:
                st.markdown("") # spacing
                st.markdown("") # spacing
                remember_me = st.checkbox("Remember me for 30 days", 
                                        help="Save login credentials for automatic login")
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if self.authenticate(username, password, remember_me):
                    if remember_me:
                        st.success("Login successful! Credentials saved for future visits.")
                    else:
                        st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                return True
        
        return False
    
    def render_user_info(self):
        """Render current user information"""
        if self.is_authenticated():
            st.success(f"Welcome, **{self.get_user_name()}**!")
            st.caption(f"Role: {self.get_user_role().capitalize()}")
            
            if st.button("Logout", key="logout_button"):
                self.logout()
                st.rerun()
        else:
            st.info("Not logged in")
    
    def require_authentication(self, required_role: str = None) -> bool:
        """Require authentication and optionally a specific role"""
        if not self.is_authenticated():
            st.warning("Please log in to access this page.")
            self.render_login_form()
            return False
        
        if required_role:
            user_role = self.get_user_role()
            role_hierarchy = {'public': 0, 'user': 1, 'subscriber': 2, 'admin': 3}
            
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                st.error(f"Access denied. This page requires {required_role} role or higher.")
                return False
        
        return True

# Global authentication instance
_auth_instance = None

def get_auth() -> SimpleAuth:
    """Get global authentication instance"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = SimpleAuth()
    return _auth_instance

# Convenience functions
def is_authenticated() -> bool:
    return get_auth().is_authenticated()

def get_current_user() -> Optional[str]:
    return get_auth().get_current_user()

def get_user_role() -> str:
    return get_auth().get_user_role()

def require_auth(required_role: str = None) -> bool:
    return get_auth().require_authentication(required_role)

def logout():
    get_auth().logout()