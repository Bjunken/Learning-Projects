"""
Reusable UI components with League of Legends styling
"""

import tkinter as tk
from config import Config

COLORS = Config.COLORS

class StyledButton(tk.Canvas):
    """Custom styled button with hover effect
    
    Visual:
    ┌────────────────┐
    │   BUTTON TEXT  │  ← Hover: changes color
    └────────────────┘
    """
    
    def __init__(self, parent, text, command=None, width=150, height=40, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=COLORS['bg_medium'], highlightthickness=0)
        
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.normal_color = COLORS['bg_light']
        self.hover_color = COLORS['accent_blue']
        self.text_color = COLORS['text_primary']
        
        # Draw button rectangle
        self.rect = self.create_rectangle(
            2, 2, width-2, height-2,
            fill=self.normal_color,
            outline=COLORS['accent_gold'],
            width=2
        )
        
        # Draw text
        self.text_id = self.create_text(
            width//2, height//2, 
            text=text,
            fill=self.text_color,
            font=('Arial', 10, 'bold')
        )
        
        # Bind events
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
        
        # Bind text too
        self.tag_bind(self.text_id, '<Enter>', self.on_enter)
        self.tag_bind(self.text_id, '<Leave>', self.on_leave)
        self.tag_bind(self.text_id, '<Button-1>', self.on_click)
    
    def on_enter(self, e):
        """Mouse enters button"""
        self.itemconfig(self.rect, fill=self.hover_color)
        self.config(cursor='hand2')
    
    def on_leave(self, e):
        """Mouse leaves button"""
        self.itemconfig(self.rect, fill=self.normal_color)
        self.config(cursor='')
    
    def on_click(self, e):
        """Button clicked"""
        if self.command:
            self.command()
    
    def disable(self):
        """Disable button"""
        self.itemconfig(self.rect, fill=COLORS['bg_medium'])
        self.itemconfig(self.text_id, fill=COLORS['text_secondary'])
        self.unbind('<Button-1>')
    
    def enable(self):
        """Enable button"""
        self.itemconfig(self.rect, fill=self.normal_color)
        self.itemconfig(self.text_id, fill=self.text_color)
        self.bind('<Button-1>', self.on_click)

class StyledEntry(tk.Entry):
    """Styled text entry field
    
    Visual:
    ┌─────────────────────┐
    │ [user input here]   │
    └─────────────────────┘
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            font=('Arial', 11),
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            borderwidth=2,
            **kwargs
        )
        self.config(highlightbackground=COLORS['accent_gold'],
                   highlightcolor=COLORS['accent_blue'],
                   highlightthickness=2)

class StyledLabel(tk.Label):
    """Styled label for text"""
    
    def __init__(self, parent, text='', fg=None, **kwargs):
        if fg is None:
            fg = COLORS['text_primary']
        
        super().__init__(
            parent,
            text=text,
            fg=fg,
            bg=COLORS['bg_medium'],
            font=('Arial', 11),
            **kwargs
        )

class ScrollableFrame(tk.Frame):
    """Scrollable frame for friends list, etc.
    
    Visual:
    ┌──────────────────┐ ▲
    │ Item 1           │ │
    │ Item 2           │ │ Scrollbar
    │ Item 3           │ │
    │ ...              │ ▼
    └──────────────────┘
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(
            self, 
            bg=COLORS['bg_medium'],
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(
            self, 
            orient='vertical',
            command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(
            self.canvas, 
            bg=COLORS['bg_medium']
        )
        
        # Configure canvas scrolling
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox('all')
            )
        )
        
        self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor='nw'
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
    
    def get_frame(self):
        """Get the scrollable frame to add widgets to"""
        return self.scrollable_frame

class LoadingSpinner(tk.Canvas):
    """Simple loading animation
    
    Visual:
    ⟳ Loading...
    """
    
    def __init__(self, parent, size=30):
        super().__init__(
            parent, 
            width=size, 
            height=size,
            bg=COLORS['bg_medium'],
            highlightthickness=0
        )
        
        self.size = size
        self.angle = 0
        self.is_spinning = False
        
        # Draw circle arc
        self.arc = self.create_arc(
            5, 5, size-5, size-5,
            start=0,
            extent=270,
            outline=COLORS['accent_blue'],
            width=3,
            style=tk.ARC
        )
    
    def start(self):
        """Start spinning"""
        self.is_spinning = True
        self._spin()
    
    def stop(self):
        """Stop spinning"""
        self.is_spinning = False
    
    def _spin(self):
        """Animation loop"""
        if self.is_spinning:
            self.angle = (self.angle + 10) % 360
            self.itemconfig(self.arc, start=self.angle)
            self.after(50, self._spin)