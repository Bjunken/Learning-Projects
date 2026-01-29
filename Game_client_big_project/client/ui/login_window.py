"""
Login window with auto-login support
"""

import tkinter as tk
from tkinter import messagebox
from ui.components import StyledButton, StyledEntry, StyledLabel, LoadingSpinner
from config import Config

COLORS = Config.COLORS

class LoginWindow:
    """Login/Register screen"""
    
    def __init__(self, parent, network_manager, session_manager, on_login_success):
        self.parent = parent
        self.network = network_manager
        self.session = session_manager
        self.on_login_success = on_login_success
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill='both', expand=True)
        
        self.keep_logged_in = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
        # Try auto-login after UI is ready
        self.frame.after(100, self.try_auto_login)
    
    def setup_ui(self):
        """Setup login UI"""
        # Title
        title = tk.Label(
            self.frame, 
            text='GAME CLIENT',
            font=('Arial', 32, 'bold'),
            fg=COLORS['accent_gold'], 
            bg=COLORS['bg_dark']
        )
        title.pack(pady=50)
        
        # Login form container
        form_frame = tk.Frame(
            self.frame, 
            bg=COLORS['bg_medium'],
            highlightbackground=COLORS['accent_gold'],
            highlightthickness=2
        )
        form_frame.pack(pady=20, padx=50)
        
        # Username
        StyledLabel(
            form_frame, 
            text='Username:', 
            font=('Arial', 12)
        ).pack(pady=(20, 5))
        
        self.username_entry = StyledEntry(form_frame, width=30)
        self.username_entry.pack(pady=5, padx=20)
        
        # Password
        StyledLabel(
            form_frame, 
            text='Password:', 
            font=('Arial', 12)
        ).pack(pady=(10, 5))
        
        self.password_entry = StyledEntry(form_frame, width=30, show='*')
        self.password_entry.pack(pady=5, padx=20)
        
        # Keep me logged in checkbox
        keep_logged_in_frame = tk.Frame(form_frame, bg=COLORS['bg_medium'])
        keep_logged_in_frame.pack(pady=10)
        
        tk.Checkbutton(
            keep_logged_in_frame,
            text='Keep me logged in',
            variable=self.keep_logged_in,
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light'],
            activebackground=COLORS['bg_medium'],
            activeforeground=COLORS['text_primary'],
            font=('Arial', 10)
        ).pack()
        
        # Bind Enter key to login
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg=COLORS['bg_medium'])
        button_frame.pack(pady=20)
        
        self.login_btn = StyledButton(
            button_frame, 
            'LOGIN', 
            self.login, 
            width=120
        )
        self.login_btn.pack(side='left', padx=5)
        
        StyledButton(
            button_frame, 
            'REGISTER', 
            self.show_register, 
            width=120
        ).pack(side='left', padx=5)
        
        StyledButton(
            button_frame, 
            'QUIT', 
            self.quit_app, 
            width=120
        ).pack(side='left', padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.frame, 
            text='Ready to connect', 
            fg=COLORS['text_secondary'],
            bg=COLORS['bg_dark'], 
            font=('Arial', 10)
        )
        self.status_label.pack(pady=10)
        
        # Loading spinner (hidden initially)
        self.spinner = LoadingSpinner(self.frame)
        # Don't pack it yet
    
    def try_auto_login(self):
        """Try to auto-login with saved session"""
        print('[Login] Checking for saved session...')
        session_data = self.session.load_session()
        
        if session_data:
            print(f'[Login] Found session for {session_data["username"]}')
            self.status_label.config(
                text='Auto-logging in...', 
                fg=COLORS['accent_blue']
            )
            
            # Set token in network manager
            self.network.token = session_data['token']
            self.network.username = session_data['username']
            
            # Show spinner
            self.spinner.pack(pady=5)
            self.spinner.start()
            
            # Try to connect
            if self.network.connect():
                # Wait a moment for authentication
                self.frame.after(1000, lambda: self._check_auto_login_success(session_data['username']))
            else:
                self.spinner.stop()
                self.spinner.pack_forget()
                self.status_label.config(
                    text='Auto-login failed. Please login manually.',
                    fg=COLORS['error']
                )
                self.session.clear_session()
        else:
            print('[Login] No saved session found')
    
    def _check_auto_login_success(self, username):
        """Check if auto-login was successful"""
        if self.network.is_connected and self.network.user_id:
            print('[Login] Auto-login successful!')
            self.spinner.stop()
            self.status_label.config(
                text='Login successful!', 
                fg=COLORS['online']
            )
            self.frame.after(500, lambda: self.on_login_success(username))
        else:
            print('[Login] Auto-login failed')
            self.spinner.stop()
            self.spinner.pack_forget()
            self.status_label.config(
                text='Auto-login failed. Please login manually.',
                fg=COLORS['error']
            )
            self.session.clear_session()
    
    def login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Validate inputs
        if not username or not password:
            self.status_label.config(
                text='Please enter username and password',
                fg=COLORS['error']
            )
            return
        
        # Disable button
        self.login_btn.disable()
        
        # Show status
        self.status_label.config(
            text='Logging in...', 
            fg=COLORS['accent_blue']
        )
        self.spinner.pack(pady=5)
        self.spinner.start()
        
        # Login to server (HTTP)
        result = self.network.login(username, password)
        
        if result['success']:
            # Save session if "keep logged in" is checked
            if self.keep_logged_in.get():
                self.session.save_session(
                    username, 
                    result['token'], 
                    True
                )
            else:
                self.session.save_session(
                    username, 
                    result['token'], 
                    False
                )
            
            # Connect to WebSocket
            if self.network.connect():
                # Wait for authentication
                self.frame.after(1000, lambda: self._check_login_success(username))
            else:
                self.spinner.stop()
                self.spinner.pack_forget()
                self.status_label.config(
                    text='Connected but WebSocket failed',
                    fg=COLORS['error']
                )
                self.login_btn.enable()
        else:
            self.spinner.stop()
            self.spinner.pack_forget()
            self.status_label.config(
                text=result['message'], 
                fg=COLORS['error']
            )
            self.password_entry.delete(0, 'end')
            self.login_btn.enable()
    
    def _check_login_success(self, username):
        """Check if login and WebSocket connection succeeded"""
        if self.network.is_connected and self.network.user_id:
            self.spinner.stop()
            self.status_label.config(
                text='Login successful!', 
                fg=COLORS['online']
            )
            self.frame.after(500, lambda: self.on_login_success(username))
        else:
            self.spinner.stop()
            self.spinner.pack_forget()
            self.status_label.config(
                text='Login succeeded but WebSocket failed',
                fg=COLORS['error']
            )
            self.login_btn.enable()
    
    def show_register(self):
        """Show registration form"""
        RegisterWindow(
            self.parent, 
            self.network, 
            self.on_register_success
        )
        self.frame.pack_forget()
    
    def on_register_success(self):
        """Called after successful registration"""
        self.frame.pack(fill='both', expand=True)
        self.status_label.config(
            text='Registration successful! Please login.',
            fg=COLORS['online']
        )
    
    def quit_app(self):
        """Quit the application"""
        if messagebox.askyesno('Quit', 'Are you sure you want to quit?'):
            self.parent.quit()


class RegisterWindow:
    """Registration screen"""
    
    def __init__(self, parent, network_manager, on_back):
        self.parent = parent
        self.network = network_manager
        self.on_back = on_back
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill='both', expand=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup registration UI"""
        # Title
        title = tk.Label(
            self.frame, 
            text='CREATE ACCOUNT',
            font=('Arial', 28, 'bold'),
            fg=COLORS['accent_gold'], 
            bg=COLORS['bg_dark']
        )
        title.pack(pady=30)
        
        # Form
        form_frame = tk.Frame(
            self.frame, 
            bg=COLORS['bg_medium'],
            highlightbackground=COLORS['accent_gold'],
            highlightthickness=2
        )
        form_frame.pack(pady=20, padx=50)
        
        # Username
        StyledLabel(
            form_frame, 
            text='Username:', 
            font=('Arial', 12)
        ).pack(pady=(20, 5))
        self.username_entry = StyledEntry(form_frame, width=30)
        self.username_entry.pack(pady=5, padx=20)
        
        # Email
        StyledLabel(
            form_frame, 
            text='Email:', 
            font=('Arial', 12)
        ).pack(pady=(10, 5))
        self.email_entry = StyledEntry(form_frame, width=30)
        self.email_entry.pack(pady=5, padx=20)
        
        # Password
        StyledLabel(
            form_frame, 
            text='Password:', 
            font=('Arial', 12)
        ).pack(pady=(10, 5))
        self.password_entry = StyledEntry(form_frame, width=30, show='*')
        self.password_entry.pack(pady=5, padx=20)
        
        # Confirm password
        StyledLabel(
            form_frame, 
            text='Confirm Password:', 
            font=('Arial', 12)
        ).pack(pady=(10, 5))
        self.confirm_entry = StyledEntry(form_frame, width=30, show='*')
        self.confirm_entry.pack(pady=5, padx=20)
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg=COLORS['bg_medium'])
        button_frame.pack(pady=20)
        
        self.create_btn = StyledButton(
            button_frame, 
            'CREATE', 
            self.register, 
            width=120
        )
        self.create_btn.pack(side='left', padx=5)
        
        StyledButton(
            button_frame, 
            'BACK', 
            self.back, 
            width=120
        ).pack(side='left', padx=5)
        
        # Status
        self.status_label = tk.Label(
            self.frame, 
            text='', 
            fg=COLORS['accent_blue'],
            bg=COLORS['bg_dark'], 
            font=('Arial', 10)
        )
        self.status_label.pack(pady=10)
        
        # Loading spinner
        self.spinner = LoadingSpinner(self.frame)
    
    def register(self):
        """Handle registration"""
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        
        # Validation
        if not all([username, email, password]):
            self.status_label.config(
                text='All fields are required', 
                fg=COLORS['error']
            )
            return
        
        if password != confirm:
            self.status_label.config(
                text='Passwords do not match', 
                fg=COLORS['error']
            )
            return
        
        if len(password) < 6:
            self.status_label.config(
                text='Password must be at least 6 characters',
                fg=COLORS['error']
            )
            return
        
        if '@' not in email:
            self.status_label.config(
                text='Invalid email address',
                fg=COLORS['error']
            )
            return
        
        # Disable button
        self.create_btn.disable()
        
        # Show status
        self.status_label.config(
            text='Creating account...', 
            fg=COLORS['accent_blue']
        )
        self.spinner.pack(pady=5)
        self.spinner.start()
        
        # Register
        result = self.network.register(username, email, password)
        
        self.spinner.stop()
        self.spinner.pack_forget()
        
        if result['success']:
            self.status_label.config(
                text='Account created! Returning to login...',
                fg=COLORS['online']
            )
            self.frame.after(1500, self.back)
        else:
            self.status_label.config(
                text=result['message'], 
                fg=COLORS['error']
            )
            self.create_btn.enable()
    
    def back(self):
        """Go back to login"""
        self.frame.destroy()
        self.on_back()