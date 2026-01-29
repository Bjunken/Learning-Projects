"""
Authentication and authorization
Handles user registration, login, and JWT tokens
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Secret key for JWT (CHANGE THIS IN PRODUCTION!)
SECRET_KEY = 'your-secret-key-change-this-in-production'
TOKEN_EXPIRATION_DAYS = 30

class AuthManager:
    """Handles authentication operations"""
    
    def __init__(self, database):
        self.db = database
    
    def hash_password(self, password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_token(self, user_id, username):
        """Generate JWT token for authenticated user"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(days=TOKEN_EXPIRATION_DAYS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, username, email, password):
        """Register a new user"""
        # Validation
        if len(username) < 3 or len(username) > 50:
            return {'success': False, 'message': 'Username must be 3-50 characters'}
        
        if len(password) < 6:
            return {'success': False, 'message': 'Password must be at least 6 characters'}
        
        if '@' not in email:
            return {'success': False, 'message': 'Invalid email address'}
        
        # Check if username already exists
        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            return {'success': False, 'message': 'Username already taken'}
        
        # Create user
        try:
            password_hash = self.hash_password(password)
            user = self.db.create_user(username, email, password_hash)
            token = self.generate_token(user.id, user.username)
            
            return {
                'success': True,
                'message': 'Registration successful',
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }
        except Exception as e:
            return {'success': False, 'message': f'Registration failed: {str(e)}'}
    
    def login_user(self, username, password):
        """Login a user"""
        user = self.db.get_user_by_username(username)
        
        if not user:
            return {'success': False, 'message': 'Invalid username or password'}
        
        if not self.verify_password(password, user.password_hash):
            return {'success': False, 'message': 'Invalid username or password'}
        
        # Update user status
        self.db.update_user_status(user.id, True)
        
        # Generate token
        token = self.generate_token(user.id, user.username)
        
        return {
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_icon_id': user.profile_icon_id
            }
        }

def token_required(f):
    """Decorator to require valid token for endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': 'Token required'}), 401
        
        # Verify token
        auth_manager = AuthManager(None)
        payload = auth_manager.verify_token(token)
        
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
        # Add user info to kwargs
        return f(payload, *args, **kwargs)
    
    return decorated