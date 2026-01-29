"""
Main server application
Handles HTTP API and WebSocket connections
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from database import Database
from auth import AuthManager, token_required
from social import SocialManager
from config import Config
import eventlet

# Monkey patch for eventlet (enables async support)
eventlet.monkey_patch()

# ==================== INITIALIZE FLASK APP ====================

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS (allows clients to connect from different computers)
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize SocketIO for real-time communication
socketio = SocketIO(
    app, 
    cors_allowed_origins=Config.SOCKETIO_CORS_ALLOWED_ORIGINS,
    async_mode=Config.SOCKETIO_ASYNC_MODE
)

# ==================== INITIALIZE MANAGERS ====================

# Database manager
db = Database(Config.DATABASE_PATH)
db.initialize_profile_icons()  # Create default profile icons

# Authentication manager
auth_manager = AuthManager(db)

# Social features manager
social_manager = SocialManager(db)

# Store active WebSocket connections
active_connections = {}  # Format: {user_id: socket_id}

# ==================== STARTUP MESSAGE ====================

print('='*60)
print('GAME SERVER INITIALIZATION')
print('='*60)
print(f'Server URL: http://{Config.HOST}:{Config.PORT}')
print(f'Database: {Config.DATABASE_PATH}')
print('='*60)

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if server is running"""
    return jsonify({
        'status': 'ok', 
        'message': 'Server is running',
        'version': '1.0.0'
    }), 200

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user account
    
    Request body:
        username: string (3-50 chars)
        email: string (valid email)
        password: string (6+ chars)
    
    Returns:
        success: boolean
        message: string
        token: string (if success)
        user: object (if success)
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Validate required fields
    if not all([username, email, password]):
        return jsonify({
            'success': False, 
            'message': 'Missing required fields'
        }), 400
    
    # Attempt registration
    result = auth_manager.register_user(username, email, password)
    
    if result['success']:
        print(f"[Auth] New user registered: {username}")
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login to existing account
    
    Request body:
        username: string
        password: string
    
    Returns:
        success: boolean
        message: string
        token: string (if success)
        user: object (if success)
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validate required fields
    if not all([username, password]):
        return jsonify({
            'success': False, 
            'message': 'Missing credentials'
        }), 400
    
    # Attempt login
    result = auth_manager.login_user(username, password)
    
    if result['success']:
        print(f"[Auth] User logged in: {username}")
        return jsonify(result), 200
    else:
        return jsonify(result), 401

    # ==================== PROFILE ENDPOINTS ====================

@app.route('/api/profile/icons', methods=['GET'])
@token_required
def get_profile_icons(current_user):
    """Get all available profile icons
    
    Requires: Valid JWT token in Authorization header
    
    Returns:
        success: boolean
        icons: array of icon objects
    """
    icons = db.get_profile_icons()
    
    return jsonify({
        'success': True,
        'icons': [
            {
                'id': icon.id,
                'filename': icon.filename,
                'name': icon.name,
                'description': icon.description
            }
            for icon in icons
        ]
    }), 200

@app.route('/api/profile/icon', methods=['PUT'])
@token_required
def update_profile_icon(current_user):
    """Update user's profile icon
    
    Request body:
        icon_id: integer (1-8)
    
    Returns:
        success: boolean
        message: string
    """
    data = request.get_json()
    icon_id = data.get('icon_id')
    
    if not icon_id:
        return jsonify({
            'success': False, 
            'message': 'Icon ID required'
        }), 400
    
    success = db.update_user_profile_icon(current_user['user_id'], icon_id)
    
    if success:
        print(f"[Profile] {current_user['username']} changed icon to {icon_id}")
        return jsonify({
            'success': True, 
            'message': 'Profile icon updated'
        }), 200
    else:
        return jsonify({
            'success': False, 
            'message': 'Update failed'
        }), 400

@app.route('/api/profile/<int:user_id>', methods=['GET'])
@token_required
def get_user_profile(current_user, user_id):
    """Get user profile information
    
    URL parameter:
        user_id: integer
    
    Returns:
        success: boolean
        profile: object with user info
    """
    user = db.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False, 
            'message': 'User not found'
        }), 404
    
    # Check if they are friends
    current_user_obj = db.get_user_by_id(current_user['user_id'])
    is_friend = user in current_user_obj.friends
    
    return jsonify({
        'success': True,
        'profile': {
            'id': user.id,
            'username': user.username,
            'profile_icon_id': user.profile_icon_id,
            'profile_icon': user.profile_icon.filename if user.profile_icon else None,
            'is_online': user.is_online,
            'is_friend': is_friend,
            'created_at': user.created_at.isoformat()
        }
    }), 200

# ==================== FRIENDS ENDPOINTS ====================

@app.route('/api/friends', methods=['GET'])
@token_required
def get_friends(current_user):
    """Get user's friends list with online status"""
    result = social_manager.get_friends_list(current_user['user_id'])
    return jsonify(result), 200

@app.route('/api/friends/request', methods=['POST'])
@token_required
def send_friend_request(current_user):
    """Send a friend request
    
    Request body:
        username: string (target user's username)
    """
    data = request.get_json()
    receiver_username = data.get('username')
    
    if not receiver_username:
        return jsonify({
            'success': False, 
            'message': 'Username required'
        }), 400
    
    result = social_manager.send_friend_request(
        current_user['user_id'], 
        receiver_username
    )
    
    if result['success']:
        # Notify receiver via WebSocket if they're online
        receiver = db.get_user_by_username(receiver_username)
        if receiver and receiver.id in active_connections:
            socketio.emit('friend_request_received', {
                'from': current_user['username'],
                'request_id': result['request_id']
            }, room=active_connections[receiver.id])
        
        print(f"[Friends] {current_user['username']} sent request to {receiver_username}")
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/friends/accept/<int:request_id>', methods=['POST'])
@token_required
def accept_friend_request(current_user, request_id):
    """Accept a friend request
    
    URL parameter:
        request_id: integer
    """
    result = social_manager.accept_friend_request(request_id, current_user['user_id'])
    
    if result['success']:
        # Notify sender via WebSocket if they're online
        friend = result['friend']
        if friend['id'] in active_connections:
            socketio.emit('friend_request_accepted', {
                'from': current_user['username']
            }, room=active_connections[friend['id']])
        
        print(f"[Friends] {current_user['username']} accepted request from user {friend['id']}")
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/friends/remove/<int:friend_id>', methods=['DELETE'])
@token_required
def remove_friend(current_user, friend_id):
    """Remove a friend
    
    URL parameter:
        friend_id: integer
    """
    result = social_manager.remove_friend(current_user['user_id'], friend_id)
    
    if result['success']:
        print(f"[Friends] {current_user['username']} removed friend {friend_id}")
    
    return jsonify(result), 200

@app.route('/api/users/search', methods=['GET'])
@token_required
def search_users(current_user):
    """Search for users by username
    
    Query parameter:
        q: string (search query, min 2 chars)
    """
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({
            'success': False, 
            'message': 'Query too short (min 2 characters)'
        }), 400
    
    result = social_manager.search_users(query)
    return jsonify(result), 200

# ==================== MESSAGES ENDPOINT ====================

@app.route('/api/messages/<int:friend_id>', methods=['GET'])
@token_required
def get_messages(current_user, friend_id):
    """Get conversation history with a friend
    
    URL parameter:
        friend_id: integer
    
    Returns:
        success: boolean
        messages: array of message objects
    """
    result = social_manager.get_conversation(current_user['user_id'], friend_id)
    
    # Mark messages as read
    db.mark_messages_as_read(current_user['user_id'], friend_id)
    
    return jsonify(result), 200

# ==================== PARTY ENDPOINTS ====================

@app.route('/api/party/create', methods=['POST'])
@token_required
def create_party(current_user):
    """Create a new party
    
    Auto-creates party with current user as leader
    
    Returns:
        success: boolean
        party: object with party_id and leader_id
    """
    result = social_manager.create_party(current_user['user_id'])
    
    if result['success']:
        print(f"[Party] {current_user['username']} created party {result['party']['party_id']}")
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@app.route('/api/party/current', methods=['GET'])
@token_required
def get_current_party(current_user):
    """Get user's current party with all members
    
    Returns:
        success: boolean
        party: object (null if not in party)
            - party_id: string
            - leader_id: integer
            - members: array of member objects
    """
    result = social_manager.get_user_current_party(current_user['user_id'])
    return jsonify(result), 200

@app.route('/api/party/invite', methods=['POST'])
@token_required
def invite_to_party(current_user):
    """Invite user to party (leader only)
    
    Request body:
        user_id: integer (user to invite)
    
    Returns:
        success: boolean
        message: string
    """
    data = request.get_json()
    invited_user_id = data.get('user_id')
    
    if not invited_user_id:
        return jsonify({
            'success': False, 
            'message': 'User ID required'
        }), 400
    
    # Check if can invite
    result = social_manager.invite_to_party(current_user['user_id'], invited_user_id)
    
    if result['success']:
        # Send WebSocket invitation if user is online
        if invited_user_id in active_connections:
            invited_user = db.get_user_by_id(invited_user_id)
            inviter = db.get_user_by_id(current_user['user_id'])
            
            socketio.emit('party_invite', {
                'party_id': result['party_id'],
                'inviter_id': inviter.id,
                'inviter_username': inviter.username,
                'inviter_icon': inviter.profile_icon.filename if inviter.profile_icon else None
            }, room=active_connections[invited_user_id])
            
            print(f"[Party] {inviter.username} invited {invited_user.username}")
            return jsonify({'success': True, 'message': 'Invite sent'}), 200
        else:
            return jsonify({
                'success': False, 
                'message': 'User is offline'
            }), 400
    else:
        return jsonify(result), 400

@app.route('/api/party/join/<party_id>', methods=['POST'])
@token_required
def join_party(current_user, party_id):
    """Join a party
    
    URL parameter:
        party_id: string
    
    Returns:
        success: boolean
        message: string
    """
    result = social_manager.join_party(current_user['user_id'], party_id)
    
    if result['success']:
        # Notify all party members
        party = db.get_party_by_id(party_id)
        user_data = result['user']
        
        for member in party.members:
            if member.user_id in active_connections:
                socketio.emit('party_member_joined', {
                    'party_id': party_id,
                    'user_id': user_data['user_id'],
                    'username': user_data['username'],
                    'profile_icon_id': user_data['profile_icon_id']
                }, room=active_connections[member.user_id])
        
        print(f"[Party] {current_user['username']} joined party {party_id}")
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/party/leave', methods=['POST'])
@token_required
def leave_party(current_user):
    """Leave current party
    
    Returns:
        success: boolean
        message: string
    """
    result = social_manager.leave_party(current_user['user_id'])
    
    if result['success']:
        # Notify remaining members
        party = db.get_party_by_id(result['party_id'])
        if party:
            for member in party.members:
                if member.user_id in active_connections:
                    socketio.emit('party_member_left', {
                        'party_id': result['party_id'],
                        'user_id': current_user['user_id']
                    }, room=active_connections[member.user_id])
        
        print(f"[Party] {current_user['username']} left party")
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/party/kick/<int:user_id>', methods=['POST'])
@token_required
def kick_from_party(current_user, user_id):
    """Kick user from party (leader only)
    
    URL parameter:
        user_id: integer
    
    Returns:
        success: boolean
        message: string
    """
    result = social_manager.kick_from_party(current_user['user_id'], user_id)
    
    if result['success']:
        # Notify kicked user
        if user_id in active_connections:
            socketio.emit('party_kicked', {
                'party_id': result['party_id']
            }, room=active_connections[user_id])
        
        # Notify remaining members
        party = db.get_party_by_id(result['party_id'])
        if party:
            for member in party.members:
                if member.user_id in active_connections:
                    socketio.emit('party_member_left', {
                        'party_id': result['party_id'],
                        'user_id': user_id
                    }, room=active_connections[member.user_id])
        
        print(f"[Party] {current_user['username']} kicked user {user_id}")
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/party/promote/<int:user_id>', methods=['POST'])
@token_required
def promote_leader(current_user, user_id):
    """Promote member to party leader
    
    URL parameter:
        user_id: integer (new leader)
    
    Returns:
        success: boolean
        message: string
    """
    result = social_manager.promote_to_leader(current_user['user_id'], user_id)
    
    if result['success']:
        # Notify all members
        party = db.get_party_by_id(result['party_id'])
        if party:
            for member in party.members:
                if member.user_id in active_connections:
                    socketio.emit('party_leader_changed', {
                        'party_id': result['party_id'],
                        'new_leader_id': user_id
                    }, room=active_connections[member.user_id])
        
        print(f"[Party] {current_user['username']} promoted user {user_id} to leader")
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/api/players/recent', methods=['GET'])
@token_required
def get_recent_players(current_user):
    """Get recent players from last 2 matches
    
    Returns:
        success: boolean
        players: array of player objects
    """
    players = db.get_recent_players(current_user['user_id'])
    
    return jsonify({
        'success': True,
        'players': [
            {
                'id': player.id,
                'username': player.username,
                'profile_icon_id': player.profile_icon_id,
                'is_online': player.is_online
            }
            for player in players
        ]
    }), 200

# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Client connected via WebSocket
    
    This happens when client calls: network.connect()
    """
    print(f'[WebSocket] Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('authenticate')
def handle_authenticate(data):
    """Client authenticating WebSocket connection
    
    Data:
        token: string (JWT token from login)
    
    Emits:
        authenticated: on success
        auth_failed: on failure
    """
    token = data.get('token')
    
    if not token:
        emit('auth_failed', {'message': 'Token required'})
        return
    
    # Verify JWT token
    payload = auth_manager.verify_token(token)
    
    if not payload:
        emit('auth_failed', {'message': 'Invalid or expired token'})
        return
    
    user_id = payload['user_id']
    username = payload['username']
    
    # Store active connection
    active_connections[user_id] = request.sid
    join_room(request.sid)
    
    # Update user online status
    db.update_user_status(user_id, True)
    
    # Notify all friends that this user is online
    user = db.get_user_by_id(user_id)
    for friend in user.friends:
        if friend.id in active_connections:
            socketio.emit('friend_online', {
                'user_id': user_id,
                'username': username
            }, room=active_connections[friend.id])
    
    # Send success confirmation
    emit('authenticated', {
        'message': 'Authentication successful',
        'user_id': user_id,
        'username': username
    })
    
    print(f'[WebSocket] Authenticated: {username} (ID: {user_id})')

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected
    
    This happens when:
    - Client closes/quits
    - Connection lost
    - Client calls: network.disconnect()
    """
    # Find user by socket ID
    user_id = None
    for uid, sid in list(active_connections.items()):
        if sid == request.sid:
            user_id = uid
            break
    
    if user_id:
        # Remove from active connections
        del active_connections[user_id]
        
        # Update database status
        db.update_user_status(user_id, False)
        
        # Notify all friends that user is offline
        user = db.get_user_by_id(user_id)
        if user:
            for friend in user.friends:
                if friend.id in active_connections:
                    socketio.emit('friend_offline', {
                        'user_id': user_id,
                        'username': user.username
                    }, room=active_connections[friend.id])
        
        print(f'[WebSocket] Disconnected: {user.username if user else user_id}')

@socketio.on('send_message')
def handle_send_message(data):
    """Client sending a chat message
    
    Data:
        receiver_id: integer
        content: string
    
    Emits:
        message_sent: to sender (confirmation)
        message_received: to receiver (if online)
        message_error: on failure
    """
    # Find sender from active connections
    sender_id = None
    for uid, sid in active_connections.items():
        if sid == request.sid:
            sender_id = uid
            break
    
    if not sender_id:
        emit('message_error', {'message': 'Not authenticated'})
        return
    
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not receiver_id or not content:
        emit('message_error', {'message': 'Missing receiver_id or content'})
        return
    
    # Send message via social manager
    result = social_manager.send_message(sender_id, receiver_id, content)
    
    if result['success']:
        # Confirm to sender
        emit('message_sent', result['data'])
        
        # Deliver to receiver if online
        if receiver_id in active_connections:
            socketio.emit('message_received', result['data'], 
                         room=active_connections[receiver_id])
        
        print(f"[Message] {result['data']['sender_username']} -> User {receiver_id}")
    else:
        emit('message_error', {'message': result['message']})

@socketio.on('typing')
def handle_typing(data):
    """Client typing indicator
    
    Data:
        receiver_id: integer
        is_typing: boolean
    
    Emits:
        friend_typing: to receiver
    """
    # Find sender
    sender_id = None
    for uid, sid in active_connections.items():
        if sid == request.sid:
            sender_id = uid
            break
    
    if not sender_id:
        return
    
    receiver_id = data.get('receiver_id')
    is_typing = data.get('is_typing', False)
    
    # Send to receiver if online
    if receiver_id and receiver_id in active_connections:
        sender = db.get_user_by_id(sender_id)
        socketio.emit('friend_typing', {
            'user_id': sender_id,
            'username': sender.username,
            'is_typing': is_typing
        }, room=active_connections[receiver_id])

# ==================== START SERVER ====================

if __name__ == '__main__':
    print('\n')
    print('='*60)
    print('           GAME SERVER READY')
    print('='*60)
    print(f'  Listening on: http://{Config.HOST}:{Config.PORT}')
    print(f'  Database: {Config.DATABASE_PATH}')
    print('='*60)
    print('\n  Waiting for connections...\n')
    
    # Start the server
    socketio.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT, 
        debug=Config.DEBUG
    )