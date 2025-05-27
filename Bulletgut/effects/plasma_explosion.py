import pygame as pg
import math

class PlasmaExplosion:
    def __init__(self, game, x, y):
        self.game = game
        self.x = x
        self.y = y
        self.start_time = pg.time.get_ticks() / 1000
        self.duration = 0.3
        self.frames = [
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl1.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl2.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl3.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl4.png").convert_alpha()
        ]
        self.done = False

    def update(self):
        elapsed = pg.time.get_ticks() / 1000 - self.start_time
        if elapsed >= self.duration:
            self.done = True

    def render(self, screen, raycaster, player):
        if self.done:
            return

        elapsed = pg.time.get_ticks() / 1000 - self.start_time
        index = min(int((elapsed / self.duration) * len(self.frames)), len(self.frames) - 1)
        sprite = self.frames[index]

        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.hypot(dx, dy)
        rel_angle = math.atan2(dy, dx) - player.angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(rel_angle) > raycaster.fov / 2:
            return

        corrected_dist = dist * math.cos(rel_angle)
        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())

        # Empêche le rendu si explosion derrière un mur
        if 0 <= screen_x < len(raycaster.z_buffer):
            if corrected_dist > raycaster.z_buffer[screen_x] + 10:
                return

        size = max(60, int(800 / (corrected_dist + 0.0001)))
        screen_y = screen.get_height() // 2 - size // 2
        scaled_sprite = pg.transform.scale(sprite, (size, size))
        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))
