# File: backend/app/models/user.py
# Fixed user model with correct imports

import bcrypt
import uuid
from typing import Optional, Dict
from datetime import datetime
from app.neptune_client import run_query  # Remove get_neptune_client
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
        query = (
            f"g.V().hasLabel('User').has('user_id', '{user_id}').as('u')"
            f".V().hasLabel('Character').has('character_id', '{character_id}').as('c')"
            f".addE('owns').from('u').to('c')"
        )

        run_query(query)
        return True

    except Exception as e:
        print(f"Error linking character to user: {e}")
        return False


def get_user_characters(user_id: str) -> list:
    """Get all characters owned by a user"""
    try:
        query = (
            f"g.V().hasLabel('User').has('user_id', '{user_id}')"
            f".out('owns').hasLabel('Character').elementMap()"
        )

        result = run_query(query)
        characters = []

        for char_data in result:
            characters.append({
                "character_id": char_data.get('character_id'),
                "name": char_data.get('name'),
                "level": char_data.get('level', 1),
                "current_xp": char_data.get('current_xp', 0),
                "image_data": char_data.get('image_data')
            })

        return characters

    except Exception as e:
        print(f"Error fetching user characters: {e}")
        return []