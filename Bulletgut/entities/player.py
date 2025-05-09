import math
import pygame as pg
from data.config import TILE_SIZE, PLAYER_SPEED, ROTATE_SPEED, FOV

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0 # Facing right
        self.fov = FOV

        self.move_speed = PLAYER_SPEED
        self.rotate_speed = ROTATE_SPEED

    def handle_inputs(self, keys, dt, mouse_dx=0, level=None):
        # Direction vector
        speed = self.move_speed * dt
        dx = math.cos(self.angle) * speed
        dy = math.sin(self.angle) * speed


        def try_move(nx, ny):
            if level and not level.is_blocked(nx, ny):
                self.x = nx
                self.y = ny

        # Movements
        ## Forward/Backward
        if keys[pg.K_w]:
            try_move(self.x + dx * speed, self.y + dy * speed)
        if keys[pg.K_s]:
            try_move(self.x - dx * speed, self.y - dy * speed)

        ## Strafe
        if keys[pg.K_a]:
            try_move(self.x + dy * speed, self.y - dx * speed)
        if keys[pg.K_d]:
            try_move(self.x - dy * speed, self.y + dx * speed)

        # Mouse rotation
        self.angle += mouse_dx * self.rotate_speed * dt
        self.angle %= 2 * math.pi # Keep an angle between 0 and 2pi

    def get_position(self):
        return self.x, self.y

    def get_angle(self):
        return self.angle

    def get_direction_vector(self):
        return (math.cos(self.angle), math.sin(self.angle))

    def draw_debug(self, screen):
        # FOR DEBUG PURPOSES ONLY
        px, py = int(self.x), int(self.y)
        pg.draw.circle(screen, (0, 255, 0), (px, py), 5)
        dx = math.cos(self.angle) * 20
        dy = math.sin(self.angle) * 20
        pg.draw.line(screen, (255, 255, 0), (px, py), (px + dx, py + dy), 2)
        tx = int(self.x // TILE_SIZE)
        ty = int(self.y // TILE_SIZE)
        pg.draw.rect(screen, (255, 0, 0), (tx * 4, ty * 4, 4, 4))
