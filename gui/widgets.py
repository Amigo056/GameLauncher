import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class ConsoleButton(tk.Frame):
    """Botão de consola com ícone e texto."""
    def __init__(self, parent, name: str, icon_path: str, command, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(bg='#2b2b2b', padx=20, pady=20)
        
        # Try to load icon
        try:
            img = Image.open(icon_path)
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            self.icon = ImageTk.PhotoImage(img)
        except:
            # Fallback: colored square
            self.icon = None
        
        if self.icon:
            self.lbl_icon = tk.Label(self, image=self.icon, bg='#2b2b2b')
            self.lbl_icon.pack()
        
        self.lbl_name = tk.Label(
            self, 
            text=name, 
            bg='#2b2b2b', 
            fg='white',
            font=('Segoe UI', 12, 'bold')
        )
        self.lbl_name.pack(pady=(10, 0))
        
        # Bind click
        self.bind('<Button-1>', lambda e: command())
        self.lbl_name.bind('<Button-1>', lambda e: command())
        if self.icon:
            self.lbl_icon.bind('<Button-1>', lambda e: command())
        
        # Hover effect
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, event):
        self.configure(bg='#3b3b3b')
        for child in self.winfo_children():
            child.configure(bg='#3b3b3b')
    
    def on_leave(self, event):
        self.configure(bg='#2b2b2b')
        for child in self.winfo_children():
            child.configure(bg='#2b2b2b')

class GameCard(tk.Frame):
    """Card de jogo com cover e título."""
    def __init__(self, parent, game_data: dict, command, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.game_data = game_data
        self.command = command
        
        self.configure(bg='#1e1e1e', relief='flat', bd=2)
        
        # Cover image
        try:
            img = Image.open(game_data['cover'])
            img = img.resize((120, 120), Image.Resampling.LANCZOS)
            self.cover_img = ImageTk.PhotoImage(img)
            self.lbl_cover = tk.Label(self, image=self.cover_img, bg='#1e1e1e')
        except:
            self.lbl_cover = tk.Label(
                self, 
                text="No Image", 
                bg='#333333', 
                fg='white',
                width=15, 
                height=10
            )
        
        self.lbl_cover.pack()
        
        # Title (truncated)
        title = game_data['name'][:25] + "..." if len(game_data['name']) > 25 else game_data['name']
        self.lbl_title = tk.Label(
            self,
            text=title,
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 9),
            wraplength=120
        )
        self.lbl_title.pack(pady=(5, 0))
        
        # Click binding
        self.bind('<Button-1>', self.on_click)
        self.lbl_cover.bind('<Button-1>', self.on_click)
        self.lbl_title.bind('<Button-1>', self.on_click)
        
        # Hover
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_click(self, event):
        self.command(self.game_data)
    
    def on_enter(self, event):
        self.configure(bg='#2e2e2e')
        self.lbl_title.configure(bg='#2e2e2e')
        self.lbl_cover.configure(bg='#2e2e2e')
    
    def on_leave(self, event):
        self.configure(bg='#1e1e1e')
        self.lbl_title.configure(bg='#1e1e1e')
        self.lbl_cover.configure(bg='#1e1e1e')