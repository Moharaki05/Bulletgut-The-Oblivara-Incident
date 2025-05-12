import math
import pygame as pg

class Enemy:
    def __init__(self, x, y, texture):
        self.x = x
        self.y = y
        self.texture = texture
        self.health = 100
        self.speed = 30
        self.state = "idle"

    def update(self, player, dt):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > 32:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
            self.state = "chasing"
        else:
            self.state = "attacking"

    def get_sprite(self):
        return self.texture