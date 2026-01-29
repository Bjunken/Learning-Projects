"""
Social features: friends, messages, lobby invites
"""

from datetime import datetime
from html import escape  # XSS protection

class SocialManager:
    """Handles social features"""
    
    def __init__(self, database):
        self.db = database
    
    def sanitize_message(self, content):
        """Sanitize message content to prevent XSS"""
        # Escape HTML characters
        sanitized = escape(content)
        # Limit length
        sanitized = sanitized[:2000]
        return sanitized
    
    def send_message(self, sender_id, receiver_id, content):
        """Send a message to another user"""
        # Sanitize content
        content = self.sanitize_message(content)
        
        if not content.strip():
            return {'success': False, 'message': 'Message cannot be empty'}
        
        # Verify users exist
        sender = self.db.get_user_by_id(sender_id)
        receiver = self.db.get_user_by_id(receiver_id)
        
        if not sender or not receiver:
            return {'success': False, 'message': 'User not found'}
        
        # Check if they are friends
        if receiver not in sender.friends:
            return {'success': False, 'message': 'You can only message friends'}
        
        # Save message
        message = self.db.save_message(sender_id, receiver_id, content)
        
        return {
            'success': True,
            'message': 'Message sent',
            'data': {
                'id': message.id,
                'sender_id': sender_id,
                'sender_username': sender.username,
                'content': content,
                'sent_at': message.sent_at.isoformat()
            }
        }
    
    def get_conversation(self, user_id, friend_id):
        """Get conversation history"""
        messages = self.db.get_conversation(user_id, friend_id)
        
        return {
            'success': True,
            'messages': [
                {
                    'id': msg.id,
                    'sender_id': msg.sender_id,
                    'sender_username': msg.sender.username,
                    'content': msg.content,
                    'sent_at': msg.sent_at.isoformat(),
                    'read': msg.read
                }
                for msg in messages
            ]
        }
    
    def send_friend_request(self, sender_id, receiver_username):
        """Send a friend request"""
        receiver = self.db.get_user_by_username(receiver_username)
        
        if not receiver:
            return {'success': False, 'message': 'User not found'}
        
        if receiver.id == sender_id:
            return {'success': False, 'message': 'Cannot add yourself'}
        
        sender = self.db.get_user_by_id(sender_id)
        
        # Check if already friends
        if receiver in sender.friends:
            return {'success': False, 'message': 'Already friends'}
        
        # Create friend request
        request = self.db.create_friend_request(sender_id, receiver.id)
        
        if not request:
            return {'success': False, 'message': 'Friend request already sent'}
        
        return {
            'success': True,
            'message': f'Friend request sent to {receiver_username}',
            'request_id': request.id
        }
    
    def accept_friend_request(self, request_id, user_id):
        """Accept a friend request"""
        # Get the request
        request = self.db.session.query(self.db.session.query(
            self.db.get_session().query(FriendRequest).filter_by(
                id=request_id,
                receiver_id=user_id
            ).first()
        ))
        
        if not request:
            return {'success': False, 'message': 'Friend request not found'}
        
        success = self.db.accept_friend_request(request_id)
        
        if success:
            sender = self.db.get_user_by_id(request.sender_id)
            return {
                'success': True,
                'message': f'You are now friends with {sender.username}',
                'friend': {
                    'id': sender.id,
                    'username': sender.username,
                    'is_online': sender.is_online,
                    'profile_icon_id': sender.profile_icon_id
                }
            }
        
        return {'success': False, 'message': 'Failed to accept friend request'}
    
    def get_friends_list(self, user_id):
        """Get user's friends with online status"""
        friends = self.db.get_friends(user_id)
        
        return {
            'success': True,
            'friends': [
                {
                    'id': friend.id,
                    'username': friend.username,
                    'is_online': friend.is_online,
                    'profile_icon_id': friend.profile_icon_id,
                    'profile_icon': friend.profile_icon.filename if friend.profile_icon else None,
                    'last_login': friend.last_login.isoformat() if friend.last_login else None
                }
                for friend in friends
            ]
        }
    
    def remove_friend(self, user_id, friend_id):
        """Remove a friend"""
        success = self.db.remove_friend(user_id, friend_id)
        
        if success:
            return {'success': True, 'message': 'Friend removed'}
        
        return {'success': False, 'message': 'Friend not found'}
    
    def search_users(self, query):
        """Search for users"""
        users = self.db.search_users(query)
        
        return {
            'success': True,
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'is_online': user.is_online,
                    'profile_icon_id': user.profile_icon_id,
                    'profile_icon': user.profile_icon.filename if user.profile_icon else None
                }
                for user in users
            ]
        }