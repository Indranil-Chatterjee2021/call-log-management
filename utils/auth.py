"""
Authentication Module for Call Log Application
Handles user registration, login, and password reset
"""
import hashlib
import secrets
from typing import Optional, Tuple


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password


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
        hashed_pw = hash_password(password)
        
        # Create user record
        user_id = repo.user_create({
            "username": username,
            "password": hashed_pw
        })
        
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
        if verify_password(password, user.get("password", "")):
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
        # Check if user exists
        user = repo.user_get_by_username(username)
        if not user:
            return False, "Username not found"
        
        # Hash the new password
        hashed_pw = hash_password(new_password)
        
        # Update user password
        user_id = user.get("id")
        repo.user_update(user_id, {"password": hashed_pw})
        
        return True, "Password reset successful! You can now log in with your new password."
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
