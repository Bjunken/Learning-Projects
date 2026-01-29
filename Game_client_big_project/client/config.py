import os

class Config:
    # Server connection
    SERVER_HOST = 'localhost'
    SERVER_PORT = 5000
    SERVER_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    PROFILE_ICONS_DIR = os.path.join(ASSETS_DIR, 'profile_icons')
    SESSION_FILE = os.path.join(DATA_DIR, 'session.json')
    
    # UI Settings
    WINDOW_TITLE = 'Game Client'
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 800
    WINDOW_MIN_WIDTH = 1200
    WINDOW_MIN_HEIGHT = 700
    
    # Colors
    COLORS = {
        'bg_dark': '#010A13',
        'bg_medium': '#0A1428',
        'bg_light': '#1E2328',
        'accent_gold': '#C89B3C',
        'accent_blue': '#0AC8B9',
        'text_primary': '#F0E6D2',
        'text_secondary': '#A09B8C',
        'button_hover': '#0E141B',
        'online': '#00FF00',
        'offline': '#808080',
        'error': '#FF4444'
    }
    
    # Chat settings
    CHAT_HEIGHT = 300
    CHAT_WIDTH = 400
    
    # Version
    CLIENT_VERSION = '1.0.0'