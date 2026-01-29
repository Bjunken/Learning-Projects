"""
Server configuration
"""

class Config:
    # Server settings
    HOST = '0.0.0.0'  # Listen on all interfaces
    PORT = 5000
    DEBUG = True
    
    # Security
    SECRET_KEY = 'change-this-in-production'
    
    # Database
    DATABASE_PATH = 'game_server.db'
    
    # CORS (allow connections from clients)
    CORS_ORIGINS = '*'  # In production, specify exact origins
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'