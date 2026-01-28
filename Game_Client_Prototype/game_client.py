"""
League of Legends Inspired Game Client
A prototype game client with authentication, profile management, and social features
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import hashlib
import os
from datetime import datetime
from PIL import Image, ImageTk
import threading
import time

# Configuration
DATA_DIR = "client_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
SLIDESHOW_DIR = os.path.join(DATA_DIR, "slideshow")

# Color scheme inspired by League of Legends
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
    'offline': '#808080'
}

class DataManager:
    """Handles all data persistence for the client"""
    
    def __init__(self):
        self.ensure_data_structure()
        
    def ensure_data_structure(self):
        """Create necessary directories and files"""
        # Create main data directory
        os.makedirs(DATA_DIR, exist_ok=True)
        # Create slideshow directory
        os.makedirs(SLIDESHOW_DIR, exist_ok=True)
        
        # Create empty users file if it doesn't exist
        if not os.path.exists(USERS_FILE):
            self.save_users({})
        
        # Create config file if it doesn't exist
        if not os.path.exists(CONFIG_FILE):
            self.save_config({
                'version': '1.0.0',
                'slideshow_interval': 5000,
                'last_update': datetime.now().isoformat()
            })
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self, users):
        """Save users to JSON file"""
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    
    def load_config(self):
        """Load configuration"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_config(self, config):
        """Save configuration"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, email):
        """Create a new user account"""
        users = self.load_users()
        
        # Check if username already exists
        if username in users:
            return False, "Username already exists"
        
        # Create new user
        users[username] = {
            'password': self.hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'friends': [],
            'billing_info': {},
            'status': 'offline'
        }
        
        self.save_users(users)
        return True, "Account created successfully"
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        users = self.load_users()
        
        if username not in users:
            return False, "User not found"
        
        if users[username]['password'] != self.hash_password(password):
            return False, "Incorrect password"
        
        return True, "Login successful"
    
    def get_user(self, username):
        """Get user data"""
        users = self.load_users()
        return users.get(username, None)
    
    def update_user(self, username, updates):
        """Update user data"""
        users = self.load_users()
        if username in users:
            users[username].update(updates)
            self.save_users(users)
            return True
        return False

class StyledButton(tk.Canvas):
    """Custom styled button widget"""
    
    def __init__(self, parent, text, command=None, width=150, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS['bg_medium'], highlightthickness=0)
        
        self.command = command
        self.text = text
        self.normal_color = COLORS['bg_light']
        self.hover_color = COLORS['accent_blue']
        self.text_color = COLORS['text_primary']
        
        # Draw button rectangle
        self.rect = self.create_rectangle(2, 2, width-2, height-2, 
                                         fill=self.normal_color, 
                                         outline=COLORS['accent_gold'])
        
        # Draw button text
        self.text_id = self.create_text(width//2, height//2, text=text, 
                                       fill=self.text_color, 
                                       font=('Arial', 10, 'bold'))
        
        # Bind hover events
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
    
    def on_enter(self, e):
        """When mouse hovers over button"""
        self.itemconfig(self.rect, fill=self.hover_color)
    
    def on_leave(self, e):
        """When mouse leaves button"""
        self.itemconfig(self.rect, fill=self.normal_color)
    
    def on_click(self, e):
        """When button is clicked"""
        if self.command:
            self.command()

class LoginWindow:
    """Login window for the game client"""
    
    def __init__(self, parent, data_manager, on_login_success):
        self.parent = parent
        self.data_manager = data_manager
        self.on_login_success = on_login_success
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill='both', expand=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title = tk.Label(self.frame, text="GAME CLIENT", 
                        font=('Arial', 32, 'bold'),
                        fg=COLORS['accent_gold'], bg=COLORS['bg_dark'])
        title.pack(pady=50)
        
        # Login form container
        form_frame = tk.Frame(self.frame, bg=COLORS['bg_medium'], 
                             highlightbackground=COLORS['accent_gold'], 
                             highlightthickness=2)
        form_frame.pack(pady=20, padx=50)
        
        # Username field
        tk.Label(form_frame, text="Username:", fg=COLORS['text_primary'], 
                bg=COLORS['bg_medium'], font=('Arial', 12)).pack(pady=(20, 5))
        self.username_entry = tk.Entry(form_frame, font=('Arial', 12), width=30,
                                       bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                       insertbackground=COLORS['text_primary'])
        self.username_entry.pack(pady=5)
        
        # Password field
        tk.Label(form_frame, text="Password:", fg=COLORS['text_primary'], 
                bg=COLORS['bg_medium'], font=('Arial', 12)).pack(pady=(10, 5))
        self.password_entry = tk.Entry(form_frame, font=('Arial', 12), width=30, show='*',
                                       bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                       insertbackground=COLORS['text_primary'])
        self.password_entry.pack(pady=5)
        
        # Press Enter to login
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg=COLORS['bg_medium'])
        button_frame.pack(pady=20)
        
        StyledButton(button_frame, "LOGIN", self.login, width=120).pack(side='left', padx=5)
        StyledButton(button_frame, "SIGN UP", self.show_signup, width=120).pack(side='left', padx=5)
        
        # Status label for messages
        self.status_label = tk.Label(self.frame, text="", fg=COLORS['accent_blue'], 
                                    bg=COLORS['bg_dark'], font=('Arial', 10))
        self.status_label.pack(pady=10)
    
    def login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Validate input
        if not username or not password:
            self.status_label.config(text="Please enter username and password", 
                                    fg='#FF0000')
            return
        
        # Check credentials
        success, message = self.data_manager.authenticate_user(username, password)
        
        if success:
            self.status_label.config(text=message, fg=COLORS['online'])
            # Wait 500ms then go to home screen
            self.frame.after(500, lambda: self.on_login_success(username))
        else:
            self.status_label.config(text=message, fg='#FF0000')
            self.password_entry.delete(0, 'end')  # Clear password
    
    def show_signup(self):
        """Navigate to signup window"""
        SignupWindow(self.parent, self.data_manager, self.on_signup_success)
        self.frame.pack_forget()  # Hide login window
    
    def on_signup_success(self):
        """Return from signup to login"""
        self.frame.pack(fill='both', expand=True)

class SignupWindow:
    """Signup window for creating new accounts"""
    
    def __init__(self, parent, data_manager, on_back):
        self.parent = parent
        self.data_manager = data_manager
        self.on_back = on_back
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill='both', expand=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title = tk.Label(self.frame, text="CREATE ACCOUNT", 
                        font=('Arial', 28, 'bold'),
                        fg=COLORS['accent_gold'], bg=COLORS['bg_dark'])
        title.pack(pady=30)
        
        # Signup form
        form_frame = tk.Frame(self.frame, bg=COLORS['bg_medium'], 
                             highlightbackground=COLORS['accent_gold'], 
                             highlightthickness=2)
        form_frame.pack(pady=20, padx=50)
        
        # Username
        tk.Label(form_frame, text="Username:", fg=COLORS['text_primary'], 
                bg=COLORS['bg_medium'], font=('Arial', 12)).pack(pady=(20, 5))
        self.username_entry = tk.Entry(form_frame, font=('Arial', 12), width=30,
                                       bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                       insertbackground=COLORS['text_primary'])
        self.username_entry.pack(pady=5)
        
        # Email
        tk.Label(form_frame, text="Email:", fg=COLORS['text_primary'], 
                bg=COLORS['bg_medium'], font=('Arial', 12)).pack(pady=(10, 5))
        self.email_entry = tk.Entry(form_frame, font=('Arial', 12), width=30,
                                    bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                    insertbackground=COLORS['text_primary'])
        self.email_entry.pack(pady=5)
        
        # Password
        tk.Label(form_frame, text="Password:", fg=COLORS['text_primary'], 
                bg=COLORS['bg_medium'], font=('Arial', 12)).pack(pady=(10, 5))
        self.password_entry = tk.Entry(form_frame, font=('Arial', 12), width=30, show='*',
                                       bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                       insertbackground=COLORS['text_primary'])
        self.password_entry.pack(pady=5)
        
        # Confirm Password
        tk.Label(form_frame, text="Confirm Password:", fg=COLORS['text_primary'], 
                bg=COLORS['bg_medium'], font=('Arial', 12)).pack(pady=(10, 5))
        self.confirm_entry = tk.Entry(form_frame, font=('Arial', 12), width=30, show='*',
                                      bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                      insertbackground=COLORS['text_primary'])
        self.confirm_entry.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg=COLORS['bg_medium'])
        button_frame.pack(pady=20)
        
        StyledButton(button_frame, "CREATE", self.signup, width=120).pack(side='left', padx=5)
        StyledButton(button_frame, "BACK", self.back, width=120).pack(side='left', padx=5)
        
        # Status label
        self.status_label = tk.Label(self.frame, text="", fg=COLORS['accent_blue'], 
                                    bg=COLORS['bg_dark'], font=('Arial', 10))
        self.status_label.pack(pady=10)
    
    def signup(self):
        """Handle signup button click"""
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        
        # Validation
        if not username or not email or not password:
            self.status_label.config(text="All fields are required", fg='#FF0000')
            return
        
        if password != confirm:
            self.status_label.config(text="Passwords do not match", fg='#FF0000')
            return
        
        if len(password) < 6:
            self.status_label.config(text="Password must be at least 6 characters", fg='#FF0000')
            return
        
        # Create account
        success, message = self.data_manager.create_user(username, password, email)
        
        if success:
            self.status_label.config(text=message, fg=COLORS['online'])
            self.frame.after(1000, self.back)  # Return to login after 1 second
        else:
            self.status_label.config(text=message, fg='#FF0000')
    
    def back(self):
        """Return to login window"""
        self.frame.destroy()
        self.on_back()

class HomeScreen:
    """Main home screen after login"""
    
    def __init__(self, parent, data_manager, username, on_logout):
        self.parent = parent
        self.data_manager = data_manager
        self.username = username
        self.on_logout = on_logout
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill='both', expand=True)
        
        self.current_slide = 0
        self.slideshow_images = []
        self.slideshow_running = False
        
        self.setup_ui()
        self.load_slideshow_images()
        self.start_slideshow()
        
        # Demo friends for prototype
        self.demo_friends = [
            {'name': 'ShadowBlade', 'status': 'online'},
            {'name': 'IronWarrior', 'status': 'online'},
            {'name': 'MysticMage', 'status': 'offline'},
            {'name': 'DragonSlayer', 'status': 'online'},
            {'name': 'NightHunter', 'status': 'offline'},
        ]
        self.populate_friends()

    def setup_ui(self):
        # Top navigation bar
        nav_frame = tk.Frame(self.frame, bg=COLORS['bg_light'], height=60)
        nav_frame.pack(fill='x', side='top')
        nav_frame.pack_propagate(False)
        
        # Navigation buttons
        nav_buttons = ['PLAY', 'PROFILE', 'SOCIAL', 'SETTINGS', 'QUIT GAME']
        button_container = tk.Frame(nav_frame, bg=COLORS['bg_light'])
        button_container.pack(side='left', padx=20, pady=10)
        
        for btn_text in nav_buttons:
            if btn_text == 'PROFILE':
                cmd = self.show_profile
            elif btn_text == 'QUIT GAME':
                cmd = self.quit_game
            else:
                cmd = lambda t=btn_text: self.placeholder_action(t)
            
            StyledButton(button_container, btn_text, cmd, width=130, height=35).pack(
                side='left', padx=5)
        
        # Username display
        user_label = tk.Label(nav_frame, text=f"Welcome, {self.username}", 
                             fg=COLORS['accent_gold'], bg=COLORS['bg_light'],
                             font=('Arial', 12, 'bold'))
        user_label.pack(side='right', padx=20)
        
        # Main content area
        content_frame = tk.Frame(self.frame, bg=COLORS['bg_dark'])
        content_frame.pack(fill='both', expand=True)
        
        # Left side - Slideshow
        slideshow_frame = tk.Frame(content_frame, bg=COLORS['bg_medium'], 
                                   highlightbackground=COLORS['accent_gold'],
                                   highlightthickness=2)
        slideshow_frame.pack(side='left', fill='both', expand=True, padx=(20, 10), pady=20)
        
        self.slideshow_canvas = tk.Canvas(slideshow_frame, bg=COLORS['bg_dark'], 
                                         highlightthickness=0)
        self.slideshow_canvas.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Right side - Friends list
        friends_frame = tk.Frame(content_frame, bg=COLORS['bg_medium'], width=300,
                                highlightbackground=COLORS['accent_gold'],
                                highlightthickness=2)
        friends_frame.pack(side='right', fill='y', padx=(10, 20), pady=20)
        friends_frame.pack_propagate(False)
        
        # Friends list title
        tk.Label(friends_frame, text="FRIENDS LIST", fg=COLORS['accent_gold'],
                bg=COLORS['bg_medium'], font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Scrollable friends list
        friends_canvas = tk.Canvas(friends_frame, bg=COLORS['bg_medium'], 
                                  highlightthickness=0)
        scrollbar = tk.Scrollbar(friends_frame, orient='vertical', 
                                command=friends_canvas.yview)
        
        self.friends_list_frame = tk.Frame(friends_canvas, bg=COLORS['bg_medium'])
        
        friends_canvas.create_window((0, 0), window=self.friends_list_frame, anchor='nw')
        friends_canvas.configure(yscrollcommand=scrollbar.set)
        
        friends_canvas.pack(side='left', fill='both', expand=True, padx=5)
        scrollbar.pack(side='right', fill='y')
        
        self.friends_list_frame.bind('<Configure>', 
                                     lambda e: friends_canvas.configure(
                                         scrollregion=friends_canvas.bbox('all')))

    def load_slideshow_images(self):
        """Load slideshow images or create placeholder images"""
        # Create placeholder slides if none exist
        for i in range(3):
            img_path = os.path.join(SLIDESHOW_DIR, f'slide_{i+1}.png')
            if not os.path.exists(img_path):
                self.create_placeholder_slide(img_path, i+1)
        
        # Load all slide images
        for filename in sorted(os.listdir(SLIDESHOW_DIR)):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(SLIDESHOW_DIR, filename)
                try:
                    img = Image.open(img_path)
                    self.slideshow_images.append(img)
                except:
                    pass
    
    def create_placeholder_slide(self, path, number):
        """Create a placeholder slide image"""
        img = Image.new('RGB', (800, 450), color=COLORS['bg_light'])
        img.save(path)
    
    def start_slideshow(self):
        """Start the slideshow rotation"""
        self.slideshow_running = True
        self.update_slideshow()
    
    def update_slideshow(self):
        """Update slideshow to next image"""
        if not self.slideshow_running or not self.slideshow_images:
            return
        
        # Get canvas dimensions
        canvas_width = self.slideshow_canvas.winfo_width()
        canvas_height = self.slideshow_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Resize image to fit canvas
            img = self.slideshow_images[self.current_slide].copy()
            img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.slideshow_canvas.delete('all')
            self.slideshow_canvas.create_image(canvas_width//2, canvas_height//2, 
                                              image=photo)
            self.slideshow_canvas.image = photo  # Keep reference
            
            # Add slide indicator
            self.slideshow_canvas.create_text(20, canvas_height - 20, 
                                             text=f"Slide {self.current_slide + 1}/{len(self.slideshow_images)}",
                                             fill=COLORS['text_secondary'], anchor='w',
                                             font=('Arial', 10))
        
        self.current_slide = (self.current_slide + 1) % len(self.slideshow_images)
        
        # Schedule next update (5 seconds)
        self.frame.after(5000, self.update_slideshow)

    def populate_friends(self):
        """Populate friends list"""
        for friend in self.demo_friends:
            self.create_friend_widget(friend)
    
    def create_friend_widget(self, friend):
        """Create a friend list item widget"""
        friend_frame = tk.Frame(self.friends_list_frame, bg=COLORS['bg_light'],
                               highlightbackground=COLORS['accent_gold'],
                               highlightthickness=1)
        friend_frame.pack(fill='x', padx=5, pady=3)
        
        # Status indicator (green dot = online, gray = offline)
        status_color = COLORS['online'] if friend['status'] == 'online' else COLORS['offline']
        status_canvas = tk.Canvas(friend_frame, width=10, height=10, bg=COLORS['bg_light'],
                                 highlightthickness=0)
        status_canvas.create_oval(2, 2, 8, 8, fill=status_color, outline='')
        status_canvas.pack(side='left', padx=5, pady=5)
        
        # Friend name
        name_label = tk.Label(friend_frame, text=friend['name'], fg=COLORS['text_primary'],
                             bg=COLORS['bg_light'], font=('Arial', 11))
        name_label.pack(side='left', padx=5, pady=5)
        
        # Bind click event
        for widget in [friend_frame, name_label]:
            widget.bind('<Button-1>', lambda e, f=friend: self.show_friend_menu(e, f))
    
    def show_friend_menu(self, event, friend):
        """Show context menu for friend"""
        menu = tk.Menu(self.frame, tearoff=0, bg=COLORS['bg_light'], 
                      fg=COLORS['text_primary'], activebackground=COLORS['accent_blue'])
        
        menu.add_command(label="Message Friend", 
                        command=lambda: self.friend_action('message', friend['name']))
        menu.add_command(label="Invite to Lobby", 
                        command=lambda: self.friend_action('invite', friend['name']))
        menu.add_separator()
        menu.add_command(label="Remove Friend", 
                        command=lambda: self.friend_action('remove', friend['name']))
        
        menu.post(event.x_root, event.y_root)
    
    def friend_action(self, action, friend_name):
        """Handle friend actions"""
        messages = {
            'message': f"Messaging {friend_name}... (Feature coming soon)",
            'invite': f"Inviting {friend_name} to lobby... (Feature coming soon)",
            'remove': f"Remove {friend_name}? (Feature coming soon)"
        }
        messagebox.showinfo("Friend Action", messages.get(action, "Action"))

    def show_profile(self):
        """Show profile settings"""
        ProfileWindow(self.parent, self.data_manager, self.username, self.on_profile_close)
        self.frame.pack_forget()
        self.slideshow_running = False
    
    def on_profile_close(self):
        """Return from profile window"""
        self.frame.pack(fill='both', expand=True)
        self.slideshow_running = True
        self.update_slideshow()
    
    def placeholder_action(self, button_name):
        """Placeholder for unimplemented features"""
        messagebox.showinfo("Coming Soon", 
                          f"{button_name} feature will be implemented in future updates!")
    
    def quit_game(self):
        """Quit the game"""
        if messagebox.askyesno("Quit Game", "Are you sure you want to quit?"):
            self.slideshow_running = False
            self.on_logout()

class ProfileWindow:
    """Profile settings and information window"""
    
    def __init__(self, parent, data_manager, username, on_close):
        self.parent = parent
        self.data_manager = data_manager
        self.username = username
        self.on_close = on_close
        
        self.user_data = data_manager.get_user(username)
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill='both', expand=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title bar
        title_frame = tk.Frame(self.frame, bg=COLORS['bg_light'], height=60)
        title_frame.pack(fill='x', side='top')
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="PROFILE SETTINGS", fg=COLORS['accent_gold'],
                bg=COLORS['bg_light'], font=('Arial', 18, 'bold')).pack(side='left', padx=20, pady=15)
        
        StyledButton(title_frame, "BACK", self.back, width=100, height=35).pack(
            side='right', padx=20, pady=12)
        
        # Content area
        content = tk.Frame(self.frame, bg=COLORS['bg_dark'])
        content.pack(fill='both', expand=True, padx=50, pady=30)
        
        # Account Information Section
        info_frame = tk.Frame(content, bg=COLORS['bg_medium'],
                             highlightbackground=COLORS['accent_gold'],
                             highlightthickness=2)
        info_frame.pack(fill='x', pady=10)
        
        tk.Label(info_frame, text="Account Information", fg=COLORS['accent_gold'],
                bg=COLORS['bg_medium'], font=('Arial', 14, 'bold')).pack(anchor='w', padx=20, pady=10)
        
        info_text = f"""
        Username: {self.username}
        Email: {self.user_data.get('email', 'N/A')}
        Account Created: {self.user_data.get('created_at', 'N/A')[:10]}
        """
        
        tk.Label(info_frame, text=info_text, fg=COLORS['text_primary'],
                bg=COLORS['bg_medium'], font=('Arial', 11), justify='left').pack(
                    anchor='w', padx=20, pady=10)
        
        # Change Password Section
        password_frame = tk.Frame(content, bg=COLORS['bg_medium'],
                                 highlightbackground=COLORS['accent_gold'],
                                 highlightthickness=2)
        password_frame.pack(fill='x', pady=10)
        
        tk.Label(password_frame, text="Change Password", fg=COLORS['accent_gold'],
                bg=COLORS['bg_medium'], font=('Arial', 14, 'bold')).pack(anchor='w', padx=20, pady=10)
        
        # Current password
        tk.Label(password_frame, text="Current Password:", fg=COLORS['text_primary'],
                bg=COLORS['bg_medium']).pack(anchor='w', padx=20, pady=(5, 0))
        self.current_pass = tk.Entry(password_frame, font=('Arial', 11), show='*',
                                     bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                     insertbackground=COLORS['text_primary'])
        # Fixed: removed duplicate 'padx' argument
        self.current_pass.pack(anchor='w', padx=20, pady=5, fill='x')
        
        # New password
        tk.Label(password_frame, text="New Password:", fg=COLORS['text_primary'],
                bg=COLORS['bg_medium']).pack(anchor='w', padx=20, pady=(10, 0))
        self.new_pass = tk.Entry(password_frame, font=('Arial', 11), show='*',
                                bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                insertbackground=COLORS['text_primary'])
        # Fixed: removed duplicate 'padx' argument
        self.new_pass.pack(anchor='w', padx=20, pady=5, fill='x')
        
        StyledButton(password_frame, "UPDATE PASSWORD", self.change_password,
                    width=180, height=35).pack(anchor='w', padx=20, pady=15)
        
        # Billing Section
        billing_frame = tk.Frame(content, bg=COLORS['bg_medium'],
                                highlightbackground=COLORS['accent_gold'],
                                highlightthickness=2)
        billing_frame.pack(fill='x', pady=10)
        
        tk.Label(billing_frame, text="Billing Information", fg=COLORS['accent_gold'],
                bg=COLORS['bg_medium'], font=('Arial', 14, 'bold')).pack(anchor='w', padx=20, pady=10)
        
        billing_info = self.user_data.get('billing_info', {})
        if billing_info:
            billing_text = f"Card: **** **** **** {billing_info.get('last4', 'N/A')}"
        else:
            billing_text = "No billing information added"
        
        tk.Label(billing_frame, text=billing_text, fg=COLORS['text_primary'],
                bg=COLORS['bg_medium'], font=('Arial', 11)).pack(anchor='w', padx=20, pady=5)
        
        btn_frame = tk.Frame(billing_frame, bg=COLORS['bg_medium'])
        btn_frame.pack(anchor='w', padx=20, pady=15)
        
        StyledButton(btn_frame, "ADD/UPDATE", self.add_billing, width=150, height=35).pack(
            side='left', padx=5)
        
        if billing_info:
            StyledButton(btn_frame, "REMOVE", self.remove_billing, width=150, height=35).pack(
                side='left', padx=5)
    
    def change_password(self):
        """Change user password"""
        current = self.current_pass.get()
        new = self.new_pass.get()
        
        if not current or not new:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        # Verify current password
        if self.data_manager.hash_password(current) != self.user_data['password']:
            messagebox.showerror("Error", "Current password is incorrect")
            return
        
        if len(new) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        # Update password
        self.data_manager.update_user(self.username, {
            'password': self.data_manager.hash_password(new)
        })
        
        messagebox.showinfo("Success", "Password updated successfully")
        self.current_pass.delete(0, 'end')
        self.new_pass.delete(0, 'end')
    
    def add_billing(self):
        """Add/update billing information"""
        BillingWindow(self.parent, self.data_manager, self.username, self.refresh)
    
    def remove_billing(self):
        """Remove billing information"""
        if messagebox.askyesno("Confirm", "Remove billing information?"):
            self.data_manager.update_user(self.username, {'billing_info': {}})
            messagebox.showinfo("Success", "Billing information removed")
            self.refresh()
    
    def refresh(self):
        """Refresh the profile window"""
        self.frame.destroy()
        self.__init__(self.parent, self.data_manager, self.username, self.on_close)
    
    def back(self):
        """Return to home screen"""
        self.frame.destroy()
        self.on_close()

class BillingWindow:
    """Window for adding/updating billing information"""
    
    def __init__(self, parent, data_manager, username, on_close):
        self.data_manager = data_manager
        self.username = username
        self.on_close = on_close
        
        self.window = tk.Toplevel(parent)
        self.window.title("Billing Information")
        self.window.geometry("400x400")
        self.window.configure(bg=COLORS['bg_dark'])
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        tk.Label(self.window, text="Add Billing Information", 
                fg=COLORS['accent_gold'], bg=COLORS['bg_dark'],
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        form = tk.Frame(self.window, bg=COLORS['bg_medium'],
                       highlightbackground=COLORS['accent_gold'],
                       highlightthickness=2)
        form.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Card number
        tk.Label(form, text="Card Number:", fg=COLORS['text_primary'],
                bg=COLORS['bg_medium']).pack(anchor='w', padx=20, pady=(20, 5))
        self.card_entry = tk.Entry(form, font=('Arial', 11),
                                   bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.card_entry.pack(fill='x', padx=20, pady=5)
        
        # Expiry
        tk.Label(form, text="Expiry (MM/YY):", fg=COLORS['text_primary'],
                bg=COLORS['bg_medium']).pack(anchor='w', padx=20, pady=(10, 5))
        self.expiry_entry = tk.Entry(form, font=('Arial', 11),
                                     bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.expiry_entry.pack(fill='x', padx=20, pady=5)
        
        # CVV
        tk.Label(form, text="CVV:", fg=COLORS['text_primary'],
                bg=COLORS['bg_medium']).pack(anchor='w', padx=20, pady=(10, 5))
        self.cvv_entry = tk.Entry(form, font=('Arial', 11), show='*',
                                 bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.cvv_entry.pack(fill='x', padx=20, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(form, bg=COLORS['bg_medium'])
        btn_frame.pack(pady=20)
        
        StyledButton(btn_frame, "SAVE", self.save, width=120).pack(side='left', padx=5)
        StyledButton(btn_frame, "CANCEL", self.window.destroy, width=120).pack(side='left', padx=5)
    
    def save(self):
        """Save billing information"""
        card = self.card_entry.get().strip()
        expiry = self.expiry_entry.get().strip()
        cvv = self.cvv_entry.get().strip()
        
        if not card or not expiry or not cvv:
            messagebox.showerror("Error", "All fields are required")
            return
        
        # Basic validation
        if len(card) < 13:
            messagebox.showerror("Error", "Invalid card number")
            return
        
        # Store last 4 digits only (simulated - NOT FOR REAL PAYMENTS)
        billing_info = {
            'last4': card[-4:],
            'expiry': expiry,
            'added_at': datetime.now().isoformat()
        }
        
        self.data_manager.update_user(self.username, {'billing_info': billing_info})
        messagebox.showinfo("Success", "Billing information added successfully")
        self.window.destroy()
        self.on_close()

class GameClient:
    """Main game client application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Client")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.minsize(1000, 600)
        
        self.data_manager = DataManager()
        self.current_user = None
        
        self.show_login()
    
    def show_login(self):
        """Show login window"""
        self.clear_window()
        LoginWindow(self.root, self.data_manager, self.on_login_success)
    
    def on_login_success(self, username):
        """Handle successful login"""
        self.current_user = username
        self.show_home()
    
    def show_home(self):
        """Show home screen"""
        self.clear_window()
        HomeScreen(self.root, self.data_manager, self.current_user, self.show_login)
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = GameClient()
    app.run()