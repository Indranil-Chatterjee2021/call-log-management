"""
Authentication Module for Call Log Application
Handles user registration, login, and password reset
"""
import hashlib
import streamlit as st
from typing import Optional, Tuple
from utils.data_models import User, get_now

def get_logged_in_user(user_data: dict | None = None) -> str:
    """Safely retrieves or updates the current username in session state."""
    
    # 1. If new user_data is provided, update the session state
    if user_data and isinstance(user_data, dict):
        # Use .get() to avoid KeyErrors if 'username' is missing
        st.session_state['current_user'] = user_data.get('username', 'System')
        return st.session_state['current_user']
    
    # 2. If no new data, try to retrieve from session state
    current = st.session_state.get('current_user')
    
    # 3. Handle cases where current_user is a dict or just a string
    if isinstance(current, dict):
        return current.get('username', 'System')
    elif isinstance(current, str):
        return current
        
    return "System"


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return _hash_password(password) == hashed_password


def register_user(repo, username: str, password: str) -> Tuple[bool, str]:
    """
    Register a new user
    Returns: (success: bool, message: str)
    """
    try:
        # Check if username already exists
        existing_user = repo.user_get_by_username(username)
        if existing_user:
            return False, "Username already exists"
        
        # Hash the password
        hashed_pw = _hash_password(password)
        
        # Create user record
        new_user = User(
            username=username,
            password=hashed_pw,
            created_at=get_now()
        )
        
        user_id = repo.user_create(new_user)

        if user_id:
            return True, "Registration successful! You can now log in."
        else:
            return False, "Failed to create user account"
    except Exception as e:
        return False, f"Registration error: {str(e)}"


def login_user(repo, username: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Authenticate a user
    Returns: (success: bool, message: str, user_data: dict or None)
    """
    try:
        # Get user by username
        user = repo.user_get_by_username(username)
        if not user:
            return False, "Invalid username or password", None
        
        # Verify password
        if _verify_password(password, user.password):
            return True, "Login successful!", user
        else:
            return False, "Invalid username or password", None
    except Exception as e:
        return False, f"Login error: {str(e)}", None


def reset_password(repo, username: str, new_password: str) -> Tuple[bool, str]:
    """
    Reset user password
    Returns: (success: bool, message: str)
    """
    try:
        # 1. Check if user exists first to provide a clear error message
        user = repo.user_get_by_username(username)
        if not user:
            return False, "Username not found"
        
        # 2. Hash the new password
        hashed_pw = _hash_password(new_password)
        
        # 3. Perform the update
        # update user record
        upd_user = User(
            username,
            password=hashed_pw,
            updated_by=username,
            updated_at=get_now()
        )
        success = repo.user_update(upd_user)
        
        if success:
            return True, "Password reset successful! You can now log in with your new password."
        else:
            # This handles cases where the new password is identical to the old one
            # or the document was locked.
            return False, "Password update failed. Please try a different password."
            
    except Exception as e:
        return False, f"Password reset error: {str(e)}"


def check_users_exist(repo) -> bool:
    """
    Check if any users exist in the system
    Returns: True if users exist, False otherwise
    """
    try:
        users = repo.user_list()
        return len(users) > 0
    except Exception as e:
        # If users table/collection doesn't exist yet, return False
        return False
