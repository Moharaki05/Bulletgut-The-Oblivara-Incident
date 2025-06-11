import pygame as pg
import time

class MessageManager:
    def __init__(self, font=None):
        self.messages = []
        self.font = font or pg.font.SysFont("DooM", 20, bold=False)
        self.duration = 3.0  # secondes
        self.has_death_message = False

    def add(self, text, color=(255, 255, 0)):
        self.messages.append({
            "text": text,
            "color": color,
            "start_time": time.time(),
            "duration": self.duration
        })

    def render(self, surface):
        now = time.time()
        y = 10
        for msg in self.messages:
            if now - msg["start_time"] <= msg["duration"]:
                rendered = self.font.render(msg["text"], True, msg["color"])
                surface.blit(rendered, (10, y))
                y += rendered.get_height() + 5
        # Supprimer les expirés
        self.messages = [msg for msg in self.messages if now - msg["start_time"] <= msg["duration"]]
