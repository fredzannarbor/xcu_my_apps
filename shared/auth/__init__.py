"""
Shared authentication module for xtuff.ai applications.
"""

from .shared_auth import (
    get_shared_auth,
    is_authenticated,
    get_user_info,
    authenticate,
    logout,
    SharedAuthSystem
)

__all__ = [
    'get_shared_auth',
    'is_authenticated',
    'get_user_info',
    'authenticate',
    'logout',
    'SharedAuthSystem'
]
