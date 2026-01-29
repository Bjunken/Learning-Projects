"""
Main entry point for the game client
Run this file to start the client!
"""

import tkinter as tk
from config import Config
from core.network_manager import NetworkManager
from core.session_manager import SessionManager
from ui.login_window import LoginWindow
import os

class GameClient:
    """Main game client application"""
    
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title(Config.WINDOW_TITLE)
        self.root.geometry(f'{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}')
        self.root.minsize(Config.WINDOW_MIN_WIDTH, Config.WINDOW_MIN_HEIGHT)
        self.root.configure(bg=Config.COLORS['bg_dark'])
        
        # Center window on screen
        self.center_window()
        
        # Initialize managers
        self.network = NetworkManager()
        self.session = SessionManager()
        
        self.current_user = None
        
        print('='*60)
        print('GAME CLIENT STARTED')
        print('='*60)
        print(f'Server: {Config.SERVER_URL}')
        print(f'Version: {Config.CLIENT_VERSION}')
        print('='*60)
        
        # Show login screen
        self.show_login()
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def show_login(self):
        """Show login window"""
        self.clear_window()
        LoginWindow(
            self.root, 
            self.network, 
            self.session, 
            self.on_login_success
        )
    
    def on_login_success(self, username):
        """Handle successful login"""
        self.current_user = username
        print(f'[Main] Login successful: {username}')
        
        # For now, just show a success message
        # We'll add the home screen in Part 7
        self.clear_window()
        
        success_frame = tk.Frame(self.root, bg=Config.COLORS['bg_dark'])
        success_frame.pack(fill='both', expand=True)
        
        tk.Label(
            success_frame,
            text=f'Welcome, {username}!',
            font=('Arial', 32, 'bold'),
            fg=Config.COLORS['accent_gold'],
            bg=Config.COLORS['bg_dark']
        ).pack(expand=True)
        
        tk.Label(
            success_frame,
            text='Home screen coming in Part 7!',
            font=('Arial', 16),
            fg=Config.COLORS['text_primary'],
            bg=Config.COLORS['bg_dark']
        ).pack(expand=True)
        
        from ui.components import StyledButton
        StyledButton(
            success_frame,
            'LOGOUT',
            self.on_logout,
            width=150
        ).pack(pady=20)
    
    def on_logout(self):
        """Handle logout"""
        self.network.disconnect()
        self.session.clear_session()
        self.current_user = None
        print('[Main] Logged out')
        self.show_login()
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        """Run the application"""
        # Handle window close
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        
        # Start main loop
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        print('[Main] Shutting down...')
        if self.network.is_connected:
            self.network.disconnect()
        self.root.quit()

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    # Create and run application
    app = GameClient()
    app.run()