"""
Database models and operations for the game server
Uses SQLAlchemy ORM with SQLite
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Create base class for models
Base = declarative_base()

# ==================== ASSOCIATION TABLES ====================

# Many-to-many relationship for friendships
friendships = Table('friendships', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# ==================== MODELS ====================

class ProfileIcon(Base):
    """Available profile icons that users can select"""
    __tablename__ = 'profile_icons'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(100), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    
    def __repr__(self):
        return f"<ProfileIcon {self.name}>"

class User(Base):
    """User account model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Boolean, default=False)
    
    # Profile customization
    profile_icon_id = Column(Integer, ForeignKey('profile_icons.id'), default=1)
    
    # Relationships
    profile_icon = relationship('ProfileIcon')
    
    friends = relationship(
        'User',
        secondary=friendships,
        primaryjoin=id==friendships.c.user_id,
        secondaryjoin=id==friendships.c.friend_id,
        backref='friend_of'
    )
    
    sent_messages = relationship('Message', foreign_keys='Message.sender_id', backref='sender')
    received_messages = relationship('Message', foreign_keys='Message.receiver_id', backref='receiver')
    
    def __repr__(self):
        return f"<User {self.username}>"

class Message(Base):
    """Chat message model"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(String(2000), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Message from {self.sender_id} to {self.receiver_id}>"

class FriendRequest(Base):
    """Friend request model"""
    __tablename__ = 'friend_requests'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending')  # pending, accepted, rejected
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship('User', foreign_keys=[sender_id])
    receiver = relationship('User', foreign_keys=[receiver_id])
    
    def __repr__(self):
        return f"<FriendRequest {self.sender_id} -> {self.receiver_id}: {self.status}>"

class Match(Base):
    """Match history for tracking recent players"""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default='completed')
    
    players = relationship('MatchPlayer', backref='match')
    
    def __repr__(self):
        return f"<Match {self.match_id}>"

class MatchPlayer(Base):
    """Players in a match (for recent players tracking)"""
    __tablename__ = 'match_players'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    team = Column(Integer, default=1)
    
    user = relationship('User', backref='match_participations')
    
    def __repr__(self):
        return f"<MatchPlayer match={self.match_id} user={self.user_id}>"

class Party(Base):
    """Active party/lobby"""
    __tablename__ = 'parties'
    
    id = Column(Integer, primary_key=True)
    party_id = Column(String(50), unique=True, nullable=False)
    leader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='open')  # open, in_game, disbanded
    
    leader = relationship('User', foreign_keys=[leader_id])
    members = relationship('PartyMember', backref='party')
    
    def __repr__(self):
        return f"<Party {self.party_id}>"

class PartyMember(Base):
    """Members of a party"""
    __tablename__ = 'party_members'
    
    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User')
    
    def __repr__(self):
        return f"<PartyMember party={self.party_id} user={self.user_id}>"

# ==================== DATABASE MANAGER ====================

class Database:
    """Database manager class - handles all database operations"""
    
    def __init__(self, db_path='game_server.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print(f'[Database] Initialized: {db_path}')
    
    def get_session(self):
        """Get database session"""
        return self.session
    
    def close(self):
        """Close database connection"""
        self.session.close()
    
    # ==================== INITIALIZATION ====================
    
    def initialize_profile_icons(self):
        """Create default profile icons"""
        default_icons = [
            {'filename': 'icon_1.png', 'name': 'Warrior', 'description': 'Brave warrior icon'},
            {'filename': 'icon_2.png', 'name': 'Mage', 'description': 'Mysterious mage icon'},
            {'filename': 'icon_3.png', 'name': 'Assassin', 'description': 'Stealthy assassin icon'},
            {'filename': 'icon_4.png', 'name': 'Tank', 'description': 'Sturdy tank icon'},
            {'filename': 'icon_5.png', 'name': 'Support', 'description': 'Helpful support icon'},
            {'filename': 'icon_6.png', 'name': 'Marksman', 'description': 'Precise marksman icon'},
            {'filename': 'icon_7.png', 'name': 'Fighter', 'description': 'Strong fighter icon'},
            {'filename': 'icon_8.png', 'name': 'Mage Knight', 'description': 'Magical knight icon'},
        ]
        
        for icon_data in default_icons:
            existing = self.session.query(ProfileIcon).filter_by(
                filename=icon_data['filename']).first()
            if not existing:
                icon = ProfileIcon(**icon_data)
                self.session.add(icon)
        
        self.session.commit()
        print('[Database] Profile icons initialized')
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, username, email, password_hash):
        """Create a new user"""
        try:
            user = User(username=username, email=email, password_hash=password_hash)
            self.session.add(user)
            self.session.commit()
            print(f'[Database] User created: {username}')
            return user
        except Exception as e:
            self.session.rollback()
            print(f'[Database] Error creating user: {e}')
            raise e
    
    def get_user_by_username(self, username):
        """Get user by username"""
        return self.session.query(User).filter_by(username=username).first()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return self.session.query(User).filter_by(id=user_id).first()
    
    def update_user_status(self, user_id, is_online):
        """Update user online status"""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_online = is_online
            if is_online:
                user.last_login = datetime.utcnow()
            self.session.commit()
    
    def get_profile_icons(self):
        """Get all available profile icons"""
        return self.session.query(ProfileIcon).all()
    
    def update_user_profile_icon(self, user_id, icon_id):
        """Update user's profile icon"""
        user = self.get_user_by_id(user_id)
        if user:
            user.profile_icon_id = icon_id
            self.session.commit()
            return True
        return False
    
    # ==================== FRIEND OPERATIONS ====================
    
    def add_friend(self, user_id, friend_id):
        """Add a friend relationship (bidirectional)"""
        user = self.get_user_by_id(user_id)
        friend = self.get_user_by_id(friend_id)
        
        if user and friend and friend not in user.friends:
            user.friends.append(friend)
            self.session.commit()
            print(f'[Database] {user.username} and {friend.username} are now friends')
            return True
        return False
    
    def remove_friend(self, user_id, friend_id):
        """Remove a friend relationship"""
        user = self.get_user_by_id(user_id)
        friend = self.get_user_by_id(friend_id)
        
        if user and friend and friend in user.friends:
            user.friends.remove(friend)
            self.session.commit()
            print(f'[Database] {user.username} removed {friend.username}')
            return True
        return False
    
    def get_friends(self, user_id):
        """Get user's friends"""
        user = self.get_user_by_id(user_id)
        if user:
            return user.friends
        return []
    
    # ==================== MESSAGE OPERATIONS ====================
    
    def save_message(self, sender_id, receiver_id, content):
        """Save a chat message"""
        message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
        self.session.add(message)
        self.session.commit()
        return message
    
    def get_conversation(self, user_id, friend_id, limit=50):
        """Get conversation history between two users"""
        messages = self.session.query(Message).filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
            ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
        ).order_by(Message.sent_at.desc()).limit(limit).all()
        
        return list(reversed(messages))
    
    def mark_messages_as_read(self, user_id, sender_id):
        """Mark messages as read"""
        self.session.query(Message).filter_by(
            receiver_id=user_id,
            sender_id=sender_id,
            read=False
        ).update({'read': True})
        self.session.commit()
    
    # ==================== FRIEND REQUEST OPERATIONS ====================
    
    def create_friend_request(self, sender_id, receiver_id):
        """Create a friend request"""
        # Check if request already exists
        existing = self.session.query(FriendRequest).filter_by(
            sender_id=sender_id,
            receiver_id=receiver_id,
            status='pending'
        ).first()
        
        if existing:
            return None
        
        request = FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
        self.session.add(request)
        self.session.commit()
        return request
    
    def get_pending_friend_requests(self, user_id):
        """Get pending friend requests for a user"""
        return self.session.query(FriendRequest).filter_by(
            receiver_id=user_id,
            status='pending'
        ).all()
    
    def accept_friend_request(self, request_id):
        """Accept a friend request"""
        request = self.session.query(FriendRequest).filter_by(id=request_id).first()
        if request and request.status == 'pending':
            request.status = 'accepted'
            # Add friend relationship
            self.add_friend(request.sender_id, request.receiver_id)
            self.session.commit()
            return True
        return False
    
    def search_users(self, query, limit=20):
        """Search users by username"""
        return self.session.query(User).filter(
            User.username.like(f'%{query}%')
        ).limit(limit).all()
    
    # ==================== PARTY OPERATIONS ====================
    
    def create_party(self, leader_id):
        """Create a new party"""
        import uuid
        party_id = f"party_{uuid.uuid4().hex[:8]}"
        
        party = Party(party_id=party_id, leader_id=leader_id)
        self.session.add(party)
        self.session.commit()
        
        # Add leader as first member
        member = PartyMember(party_id=party.id, user_id=leader_id)
        self.session.add(member)
        self.session.commit()
        
        print(f'[Database] Party created: {party_id}')
        return party
    
    def get_party_by_id(self, party_id):
        """Get party by ID"""
        return self.session.query(Party).filter_by(party_id=party_id).first()
    
    def get_user_party(self, user_id):
        """Get party that user is in"""
        member = self.session.query(PartyMember).filter_by(user_id=user_id).first()
        if member:
            return member.party
        return None
    
    def add_party_member(self, party_id, user_id):
        """Add member to party"""
        party = self.session.query(Party).filter_by(party_id=party_id).first()
        if not party or len(party.members) >= 5:
            return False
        
        # Check if already in party
        existing = self.session.query(PartyMember).filter_by(
            party_id=party.id, user_id=user_id).first()
        if existing:
            return False
        
        member = PartyMember(party_id=party.id, user_id=user_id)
        self.session.add(member)
        self.session.commit()
        return True
    
    def remove_party_member(self, party_id, user_id):
        """Remove member from party"""
        party = self.session.query(Party).filter_by(party_id=party_id).first()
        if not party:
            return False
        
        member = self.session.query(PartyMember).filter_by(
            party_id=party.id, user_id=user_id).first()
        
        if member:
            self.session.delete(member)
            
            # If leader leaves, disband or promote
            if party.leader_id == user_id:
                remaining = self.session.query(PartyMember).filter_by(
                    party_id=party.id).first()
                if remaining:
                    party.leader_id = remaining.user_id
                else:
                    party.status = 'disbanded'
            
            self.session.commit()
            return True
        return False
    
    def promote_party_leader(self, party_id, new_leader_id):
        """Promote new party leader"""
        party = self.session.query(Party).filter_by(party_id=party_id).first()
        if party:
            party.leader_id = new_leader_id
            self.session.commit()
            return True
        return False
    
    # ==================== MATCH OPERATIONS ====================
    
    def get_recent_players(self, user_id, limit=10):
        """Get recent players from last 2 matches"""
        # Get user's recent matches
        recent_matches = self.session.query(MatchPlayer).filter_by(
            user_id=user_id
        ).order_by(MatchPlayer.id.desc()).limit(2).all()
        
        if not recent_matches:
            return []
        
        match_ids = [mp.match_id for mp in recent_matches]
        
        # Get all players from these matches (except the user)
        teammates = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id.in_(match_ids),
            MatchPlayer.user_id != user_id
        ).all()
        
        # Get unique user IDs
        user_ids = list(set([tm.user_id for tm in teammates]))
        
        # Get user objects
        users = self.session.query(User).filter(User.id.in_(user_ids)).all()
        
        return users[:limit]
    
    def record_match(self, player_ids):
        """Record a match with players (for testing recent players)"""
        import uuid
        match_id = f"match_{uuid.uuid4().hex[:8]}"
        
        match = Match(match_id=match_id, status='completed')
        self.session.add(match)
        self.session.commit()
        
        for user_id in player_ids:
            player = MatchPlayer(match_id=match.id, user_id=user_id)
            self.session.add(player)
        
        self.session.commit()
        print(f'[Database] Match recorded: {match_id}')
        return match