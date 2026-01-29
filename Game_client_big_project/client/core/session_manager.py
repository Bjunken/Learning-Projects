"""
Session Manager - Handles auto-login functionality
Saves and loads user sessions for "Keep me logged in" feature
"""

import json
import os
from config import Config

class SessionManager:
    """Manages user sessions and auto-login"""
    
    def __init__(self):
        self.session_file = Config.SESSION_FILE
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        print(f'[Session] Data directory ready: {Config.DATA_DIR}')
    
    def save_session(self, username, token, keep_logged_in=False):
        """Save session data to file
        
        Args:
            username: string
            token: string (JWT token)
            keep_logged_in: boolean (only auto-login if True)
        
        Returns:
            boolean (success/failure)
        """
        session_data = {
            'username': username,
            'token': token,
            'keep_logged_in': keep_logged_in
        }
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f'[Session] Session saved for {username} (auto-login: {keep_logged_in})')
            return True
        except Exception as e:
            print(f'[Session] Save error: {e}')
            return False
    
    def load_session(self):
        """Load session data from file
        
        Returns:
            dict with session data if "keep_logged_in" was True
            None if no session or keep_logged_in was False
        """
        if not os.path.exists(self.session_file):
            print('[Session] No saved session found')
            return None
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Only return session if keep_logged_in is True
            if session_data.get('keep_logged_in'):
                print(f'[Session] Loaded session for {session_data.get("username")}')
                return session_data
            else:
                print('[Session] Session found but auto-login not enabled')
                return None
        
        except Exception as e:
            print(f'[Session] Load error: {e}')
            return None
    
    def clear_session(self):
        """Clear session data (logout)
        
        Returns:
            boolean (success/failure)
        """
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
                print('[Session] Session cleared')
                return True
            except Exception as e:
                print(f'[Session] Clear error: {e}')
                return False
        return True
    
    def has_session(self):
        """Check if session file exists
        
        Returns:
            boolean
        """
        return os.path.exists(self.session_file)

    # In Python interpreter:
from core.session_manager import SessionManager

sm = SessionManager()

# Save session
sm.save_session('testuser', 'fake_token_123', True)

# Load session
session = sm.load_session()
print(session)  # Should print: {'username': 'testuser', 'token': 'fake_token_123', 'keep_logged_in': True}

# Clear session
sm.clear_session()