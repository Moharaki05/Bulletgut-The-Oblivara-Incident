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
        # Set eye height to be the same as player's eye level
        self.eye_height = 0  # At same level as player (center of screen)

    def update(self, player, dt):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > 32:
            # Basic pathfinding - move toward player
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
            self.state = "chasing"
        else:
            self.state = "attacking"

    def get_sprite(self):
        return self.texture

    def get_position(self):
        return self.x, self.y