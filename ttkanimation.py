import tkinter as tk
from tkinter import ttk
import time

class Animation:
    def __init__(self, widget, **kwargs):
        self.widget = widget
        self.properties = kwargs
        self.duration = kwargs.get('duration', 300)
        self.delay = kwargs.get('delay', 0)
        self.easing = kwargs.get('easing', 'linear')
        self.start_time = None
        self.original_values = {}

    def start(self):
        self.start_time = time.time() + (self.delay / 1000)
        self.save_original_values()
        self.animate()

    def save_original_values(self):
        for prop in self.properties:
            if hasattr(self.widget, prop):
                self.original_values[prop] = getattr(self.widget, prop)

    def animate(self):
        if not self.start_time:
            return
            
        current_time = time.time()
        if current_time < self.start_time:
            self.widget.after(16, self.animate)
            return
            
        progress = min(1, (current_time - self.start_time) / (self.duration / 1000))
        eased_progress = self.ease(progress)
        
        for prop, target in self.properties.items():
            if prop in ['duration', 'delay', 'easing']:
                continue
                
            current = self.original_values.get(prop, 0)
            value = current + (target - current) * eased_progress
            
            try:
                setattr(self.widget, prop, value)
            except:
                pass
        
        if progress < 1:
            self.widget.after(16, self.animate)

    def ease(self, t):
        if self.easing == 'ease_out':
            return 1 - (1 - t) * (1 - t)
        return t  # linear 