"""
Network Manager - Handles ALL server communication
Both HTTP (REST API) and WebSocket (real-time)
"""

import requests
import socketio
from config import Config

class NetworkManager:
    """Manages connection to game server"""
    
    def __init__(self):
        self.server_url = Config.SERVER_URL
        self.token = None
        self.user_id = None
        self.username = None
        self.is_connected = False
        
        # SocketIO client for real-time communication
        self.sio = socketio.Client(
            reconnection=True, 
            reconnection_attempts=5,
            reconnection_delay=1
        )
        
        # Setup WebSocket event handlers
        self._setup_socketio_handlers()
        
        # Callbacks for UI updates (set by UI components)
        self.on_authenticated = None
        self.on_message_received = None
        self.on_friend_online = None
        self.on_friend_offline = None
        self.on_friend_typing = None
        self.on_party_invite_received = None
        self.on_party_member_joined = None
        self.on_party_member_left = None
        self.on_party_kicked = None
        self.on_party_leader_changed = None
        self.on_friend_request_received = None
        
        print('[Network] Network manager initialized')
    
    # ==================== WEBSOCKET SETUP ====================
    
    def _setup_socketio_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.on('connect')
        def on_connect():
            print('[WebSocket] Connected to server')
            self.is_connected = True
            
            # Authenticate if we have a token
            if self.token:
                print('[WebSocket] Sending authentication...')
                self.sio.emit('authenticate', {'token': self.token})
        
        @self.sio.on('disconnect')
        def on_disconnect():
            print('[WebSocket] Disconnected from server')
            self.is_connected = False
        
        @self.sio.on('authenticated')
        def on_authenticated(data):
            print(f'[WebSocket] Authenticated as {data["username"]}')
            self.user_id = data['user_id']
            self.username = data['username']
            
            if self.on_authenticated:
                self.on_authenticated(data)
        
        @self.sio.on('auth_failed')
        def on_auth_failed(data):
            print(f'[WebSocket] Authentication failed: {data.get("message")}')
        
        @self.sio.on('message_received')
        def on_message_received(data):
            print(f'[WebSocket] Message from {data["sender_username"]}: {data["content"][:50]}...')
            if self.on_message_received:
                self.on_message_received(data)
        
        @self.sio.on('friend_online')
        def on_friend_online(data):
            print(f'[WebSocket] Friend online: {data["username"]}')
            if self.on_friend_online:
                self.on_friend_online(data)
        
        @self.sio.on('friend_offline')
        def on_friend_offline(data):
            print(f'[WebSocket] Friend offline: {data["username"]}')
            if self.on_friend_offline:
                self.on_friend_offline(data)
        
        @self.sio.on('friend_typing')
        def on_friend_typing(data):
            if self.on_friend_typing:
                self.on_friend_typing(data)
        
        @self.sio.on('party_invite')
        def on_party_invite(data):
            print(f'[WebSocket] Party invite from {data["inviter_username"]}')
            if self.on_party_invite_received:
                self.on_party_invite_received(data)
        
        @self.sio.on('party_member_joined')
        def on_party_member_joined(data):
            print(f'[WebSocket] {data.get("username")} joined party')
            if self.on_party_member_joined:
                self.on_party_member_joined(data)
        
        @self.sio.on('party_member_left')
        def on_party_member_left(data):
            print('[WebSocket] Member left party')
            if self.on_party_member_left:
                self.on_party_member_left(data)
        
        @self.sio.on('party_kicked')
        def on_party_kicked(data):
            print('[WebSocket] You were kicked from party')
            if self.on_party_kicked:
                self.on_party_kicked(data)
        
        @self.sio.on('party_leader_changed')
        def on_party_leader_changed(data):
            print('[WebSocket] Party leader changed')
            if self.on_party_leader_changed:
                self.on_party_leader_changed(data)
        
        @self.sio.on('friend_request_received')
        def on_friend_request(data):
            print(f'[WebSocket] Friend request from {data["from"]}')
            if self.on_friend_request_received:
                self.on_friend_request_received(data)
    
    # ==================== CONNECTION ====================
    
    def connect(self):
        """Connect to server via WebSocket
        
        Returns:
            boolean (success/failure)
        """
        try:
            print(f'[Network] Connecting to {self.server_url}...')
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            print(f'[Network] Connection failed: {e}')
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        if self.is_connected:
            print('[Network] Disconnecting...')
            self.sio.disconnect()
    
    # ==================== HTTP API: AUTHENTICATION ====================
    
    def register(self, username, email, password):
        """Register a new account
        
        Args:
            username: string
            email: string
            password: string
        
        Returns:
            dict with 'success', 'message', and 'token' (if success)
        """
        try:
            print(f'[HTTP] Registering user: {username}')
            response = requests.post(
                f'{self.server_url}/api/auth/register',
                json={
                    'username': username,
                    'email': email,
                    'password': password
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                self.token = data['token']
                print(f'[HTTP] Registration successful')
            else:
                print(f'[HTTP] Registration failed: {data.get("message")}')
            
            return data
        
        except requests.exceptions.ConnectionError:
            print('[HTTP] Cannot connect to server')
            return {'success': False, 'message': 'Cannot connect to server. Is it running?'}
        except Exception as e:
            print(f'[HTTP] Registration error: {e}')
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def login(self, username, password):
        """Login to account
        
        Args:
            username: string
            password: string
        
        Returns:
            dict with 'success', 'message', and 'token' (if success)
        """
        try:
            print(f'[HTTP] Logging in: {username}')
            response = requests.post(
                f'{self.server_url}/api/auth/login',
                json={
                    'username': username,
                    'password': password
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                self.token = data['token']
                self.username = username
                print('[HTTP] Login successful')
            else:
                print(f'[HTTP] Login failed: {data.get("message")}')
            
            return data
        
        except requests.exceptions.ConnectionError:
            print('[HTTP] Cannot connect to server')
            return {'success': False, 'message': 'Cannot connect to server. Is it running?'}
        except Exception as e:
            print(f'[HTTP] Login error: {e}')
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    # ==================== HTTP API: PROFILE ====================
    
    def get_profile_icons(self):
        """Get all available profile icons"""
        try:
            response = requests.get(
                f'{self.server_url}/api/profile/icons',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Get icons error: {e}')
            return {'success': False, 'icons': []}
    
    def update_profile_icon(self, icon_id):
        """Update user's profile icon"""
        try:
            response = requests.put(
                f'{self.server_url}/api/profile/icon',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'icon_id': icon_id},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Update icon error: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_user_profile(self, user_id):
        """Get user profile"""
        try:
            response = requests.get(
                f'{self.server_url}/api/profile/{user_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Get profile error: {e}')
            return {'success': False}
    
    # ==================== HTTP API: FRIENDS ====================
    
    def get_friends(self):
        """Get friends list"""
        try:
            response = requests.get(
                f'{self.server_url}/api/friends',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Get friends error: {e}')
            return {'success': False, 'friends': []}
    
    def send_friend_request(self, username):
        """Send friend request"""
        try:
            response = requests.post(
                f'{self.server_url}/api/friends/request',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'username': username},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Send friend request error: {e}')
            return {'success': False, 'message': str(e)}
    
    def accept_friend_request(self, request_id):
        """Accept friend request"""
        try:
            response = requests.post(
                f'{self.server_url}/api/friends/accept/{request_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Accept friend request error: {e}')
            return {'success': False}
    
    def remove_friend(self, friend_id):
        """Remove a friend"""
        try:
            response = requests.delete(
                f'{self.server_url}/api/friends/remove/{friend_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Remove friend error: {e}')
            return {'success': False, 'message': str(e)}
    
    def search_users(self, query):
        """Search for users"""
        try:
            response = requests.get(
                f'{self.server_url}/api/users/search',
                headers={'Authorization': f'Bearer {self.token}'},
                params={'q': query},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Search users error: {e}')
            return {'success': False, 'users': []}
    
    # ==================== HTTP API: MESSAGES ====================
    
    def get_conversation(self, friend_id):
        """Get conversation history"""
        try:
            response = requests.get(
                f'{self.server_url}/api/messages/{friend_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Get conversation error: {e}')
            return {'success': False, 'messages': []}
    
    # ==================== HTTP API: PARTY ====================
    
    def create_party(self):
        """Create a new party"""
        try:
            response = requests.post(
                f'{self.server_url}/api/party/create',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Create party error: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_current_party(self):
        """Get current party"""
        try:
            response = requests.get(
                f'{self.server_url}/api/party/current',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Get party error: {e}')
            return {'success': False, 'party': None}
    
    def invite_to_party(self, user_id):
        """Invite user to party"""
        try:
            response = requests.post(
                f'{self.server_url}/api/party/invite',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'user_id': user_id},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Invite to party error: {e}')
            return {'success': False, 'message': str(e)}
    
    def join_party(self, party_id):
        """Join a party"""
        try:
            response = requests.post(
                f'{self.server_url}/api/party/join/{party_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Join party error: {e}')
            return {'success': False, 'message': str(e)}
    
    def leave_party(self):
        """Leave current party"""
        try:
            response = requests.post(
                f'{self.server_url}/api/party/leave',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Leave party error: {e}')
            return {'success': False, 'message': str(e)}
    
    def kick_from_party(self, user_id):
        """Kick user from party"""
        try:
            response = requests.post(
                f'{self.server_url}/api/party/kick/{user_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Kick from party error: {e}')
            return {'success': False, 'message': str(e)}
    
    def promote_to_leader(self, user_id):
        """Promote user to party leader"""
        try:
            response = requests.post(
                f'{self.server_url}/api/party/promote/{user_id}',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Promote leader error: {e}')
            return {'success': False, 'message': str(e)}
    
    def get_recent_players(self):
        """Get recent players"""
        try:
            response = requests.get(
                f'{self.server_url}/api/players/recent',
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f'[HTTP] Get recent players error: {e}')
            return {'success': False, 'players': []}
    
    # ==================== WEBSOCKET: REAL-TIME ====================
    
    def send_message(self, receiver_id, content):
        """Send a message via WebSocket"""
        if self.is_connected:
            self.sio.emit('send_message', {
                'receiver_id': receiver_id,
                'content': content
            })
        else:
            print('[WebSocket] Not connected - cannot send message')
    
    def send_typing_indicator(self, receiver_id, is_typing):
        """Send typing indicator"""
        if self.is_connected:
            self.sio.emit('typing', {
                'receiver_id': receiver_id,
                'is_typing': is_typing
            })