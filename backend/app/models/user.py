# File: backend/app/models/user.py
# Updated with debug logging and user creation in Neptune

import bcrypt
import uuid
from typing import Optional, Dict
from datetime import datetime
from app.neptune_client import run_query
import json


class User:
    def __init__(self, email: str, user_id: str = None, created_at: str = None):
        self.email = email
        self.user_id = user_id or str(uuid.uuid4())
        self.created_at = created_at

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_user_in_neptune(user_id: str, email: str) -> bool:
    """Create a user node in Neptune Graph"""
    try:
        print(f"Creating user in Neptune: {user_id}, {email}")

        # Check if user already exists
        check_query = f"g.V().hasLabel('User').has('user_id', '{user_id}').count()"
        existing_count = run_query(check_query)
        print(f"Existing user count: {existing_count}")

        if existing_count and existing_count[0] > 0:
            print(f"User {user_id} already exists in Neptune")
            return True

        query = (
            f"g.addV('User')"
            f".property('user_id', '{user_id}')"
            f".property('email', '{email}')"
            f".property('created_at', '{datetime.utcnow().isoformat()}')"
            f".property('is_active', true)"
            f".property('is_premium', false)"
            f".elementMap()"
        )

        result = run_query(query)
        print(f"User creation result: {result}")
        return True

    except Exception as e:
        print(f"Error creating user in Neptune: {e}")
        return False


def create_user(email: str, password: str) -> Optional[Dict]:
    """Create a new user in the database"""
    try:
        # Check if user already exists
        existing = get_user_by_email(email)
        if existing:
            return None

        user_id = str(uuid.uuid4())
        hashed_password = User.hash_password(password)

        query = (
            f"g.addV('User')"
            f".property('user_id', '{user_id}')"
            f".property('email', '{email}')"
            f".property('password_hash', '{hashed_password}')"
            f".property('created_at', '{datetime.utcnow().isoformat()}')"
            f".property('is_active', true)"
            f".property('is_premium', false)"
            f".elementMap()"
        )

        result = run_query(query)
        if result:
            return {
                "user_id": user_id,
                "email": email,
                "created_at": result[0].get('created_at')
            }
        return None

    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Retrieve user by email"""
    try:
        query = f"g.V().hasLabel('User').has('email', '{email}').elementMap()"
        result = run_query(query)

        if result:
            user_data = result[0]
            return {
                "user_id": user_data.get('user_id'),
                "email": user_data.get('email'),
                "password_hash": user_data.get('password_hash'),
                "is_active": user_data.get('is_active', True),
                "is_premium": user_data.get('is_premium', False),
                "created_at": user_data.get('created_at')
            }
        return None

    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Retrieve user by ID"""
    try:
        query = f"g.V().hasLabel('User').has('user_id', '{user_id}').elementMap()"
        result = run_query(query)

        if result:
            user_data = result[0]
            return {
                "user_id": user_data.get('user_id'),
                "email": user_data.get('email'),
                "is_active": user_data.get('is_active', True),
                "is_premium": user_data.get('is_premium', False),
                "created_at": user_data.get('created_at')
            }
        return None

    except Exception as e:
        print(f"Error fetching user by ID: {e}")
        return None


def link_character_to_user(user_id: str, character_id: str) -> bool:
    """Create ownership edge between user and character"""
    try:
        print(f"Linking character {character_id} to user {user_id}")

        # First ensure the user exists in Neptune
        user_exists = get_user_by_id(user_id)
        if not user_exists:
            print(f"User {user_id} doesn't exist in Neptune, creating...")
            # We need email, but we don't have it here. This is the problem!
            # For now, let's create a minimal user node
            create_query = (
                f"g.addV('User')"
                f".property('user_id', '{user_id}')"
                f".property('email', 'temp@example.com')"  # Temporary email
                f".property('created_at', '{datetime.utcnow().isoformat()}')"
                f".property('is_active', true)"
                f".property('is_premium', false)"
            )
            run_query(create_query)
            print(f"Created user node for {user_id}")

        # Now create the ownership edge
        query = (
            f"g.V().hasLabel('User').has('user_id', '{user_id}')"
            f".addE('owns')"
            f".to(V().hasLabel('Character').has('character_id', '{character_id}'))"
        )

        result = run_query(query)
        print(f"Link creation result: {result}")
        return True

    except Exception as e:
        print(f"Error linking character to user: {e}")
        return False


def get_user_characters(user_id: str) -> list:
    """Get all characters owned by a user"""
    try:
        print(f"Getting characters for user: {user_id}")

        # First check if user exists
        user_check_query = f"g.V().hasLabel('User').has('user_id', '{user_id}').count()"
        user_count = run_query(user_check_query)
        print(f"User count in Neptune: {user_count}")

        if not user_count or user_count[0] == 0:
            print(f"User {user_id} not found in Neptune!")
            return []

        # Debug: Check all User nodes
        all_users_query = "g.V().hasLabel('User').elementMap()"
        all_users = run_query(all_users_query)
        print(f"All users in Neptune: {[user.get('user_id') for user in all_users]}")

        # Debug: Check ownership edges from this user
        edges_query = f"g.V().hasLabel('User').has('user_id', '{user_id}').outE('owns').count()"
        edge_count = run_query(edges_query)
        print(f"Ownership edges from user {user_id}: {edge_count}")

        query = (
            f"g.V().hasLabel('User').has('user_id', '{user_id}')"
            f".out('owns').hasLabel('Character').elementMap()"
        )

        result = run_query(query)
        print(f"Characters query result: {result}")

        characters = []

        for char_data in result:
            print(f"Processing character data: {char_data}")
            characters.append({
                "character_id": char_data.get('character_id'),
                "name": char_data.get('name'),
                "level": char_data.get('level', 1),
                "current_xp": char_data.get('current_xp', 0),
                "image_data": char_data.get('image_data')
            })

        print(f"Returning {len(characters)} characters")
        return characters

    except Exception as e:
        print(f"Error fetching user characters: {e}")
        return []