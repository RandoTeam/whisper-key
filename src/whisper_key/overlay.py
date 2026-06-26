import tkinter as tk
import customtkinter as ctk
import queue
import logging

logger = logging.getLogger(__name__)

class OverlayWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Make the window frameless and floating
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Transparent background for the main window
        self.transparent_color = "#000001"
        self.config(bg=self.transparent_color)
        
        # Attempt to set transparent color (works on Windows)
        try:
            self.attributes("-transparentcolor", self.transparent_color)
        except Exception as e:
            logger.warning(f"Could not set transparent color: {e}")
        
        # Size and position
        self.width = 400
        self.height = 100
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - self.width) // 2
        y = screen_height - self.height - 150  # Bottom center
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Main rounded container
        self.container = ctk.CTkFrame(
            self, 
            fg_color="#1e1e1e", # Dark gray semi-transparent style
            bg_color=self.transparent_color,
            corner_radius=20,
            border_width=1,
            border_color="#3a3a3a"
        )
        self.container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.top_bar = ctk.CTkFrame(self.container, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=15, pady=(10, 0))
        
        # Red pulsing dot (Canvas for drawing circle)
        self.dot_canvas = tk.Canvas(self.top_bar, width=20, height=20, bg="#1e1e1e", highlightthickness=0)
        self.dot_canvas.pack(side="left")
        self.dot_id = self.dot_canvas.create_oval(5, 5, 15, 15, fill="#ff3b30", outline="#ff3b30")
        
        self.status_label = ctk.CTkLabel(
            self.top_bar, 
            text="Слушаю...", 
            font=("Segoe UI", 12, "bold"),
            text_color="#a0a0a0"
        )
        self.status_label.pack(side="left", padx=10)
        
        self.text_label = ctk.CTkLabel(
            self.container, 
            text="Говорите...", 
            font=("Segoe UI", 14),
            text_color="white",
            justify="left",
            wraplength=350
        )
        self.text_label.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Animation and thread sync state
        self.pulse_growing = True
        self.pulse_size = 5
        self.is_recording = False
        self.update_queue = queue.Queue()
        
        # Hide initially
        self.withdraw()
        
        self.after(50, self._process_queue)
        self.after(50, self._animate_pulse)

    def _process_queue(self):
        while not self.update_queue.empty():
            msg_type, data = self.update_queue.get()
            if msg_type == 'text':
                self.text_label.configure(text=data)
            elif msg_type == 'show':
                self.deiconify()
                self.is_recording = True
                self.text_label.configure(text="Говорите...")
            elif msg_type == 'hide':
                self.withdraw()
                self.is_recording = False
        self.after(50, self._process_queue)
        
    def _animate_pulse(self):
        if self.is_recording:
            if self.pulse_growing:
                self.pulse_size += 0.5
                if self.pulse_size >= 7:
                    self.pulse_growing = False
            else:
                self.pulse_size -= 0.5
                if self.pulse_size <= 4:
                    self.pulse_growing = True
            
            # Redraw oval
            self.dot_canvas.coords(self.dot_id, 10 - self.pulse_size, 10 - self.pulse_size, 10 + self.pulse_size, 10 + self.pulse_size)
            
        self.after(50, self._animate_pulse)
        
    def show_overlay(self):
        self.update_queue.put(('show', None))
        
    def hide_overlay(self):
        self.update_queue.put(('hide', None))
        
    def update_transcription(self, text):
        self.update_queue.put(('text', text))
