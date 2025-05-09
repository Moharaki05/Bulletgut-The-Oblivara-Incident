import pygame as pg
import math
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FOV, WALL_HEIGHT_SCALE, TILE_SIZE


class Raycaster:
    def __init__(self, level):
        self.level = level
        self.num_rays = SCREEN_WIDTH // 4 #adjust resolution here
        self.fov = FOV
        self.max_depth = 800

    def cast_rays(self, screen, player):
        ox, oy = player.get_position()
        map_x = int(ox//TILE_SIZE)
        map_y = int(oy//TILE_SIZE)

        angle = player.get_angle() - self.fov /2
        angle = angle % (2 * math.pi)
        delta_angle = self.fov / self.num_rays
        ray_width = SCREEN_WIDTH / self.num_rays

        for ray in range(self.num_rays):
            sin_a = math.sin(angle)
            cos_a = math.cos(angle)

            # Which direction the ray steps
            dx = 1 if cos_a >= 0 else -1
            dy = 1 if sin_a >= 0 else -1

            # Distance to meet next vertical and horizontal gridlines
            delta_dist_x = abs(TILE_SIZE / (cos_a + 1e-6))
            delta_dist_y = abs(TILE_SIZE / (sin_a + 1e-6))

            # Initial step to grid boundary
            if dx > 0:
                next_x = (map_x + 1) * TILE_SIZE
                side_dist_x = (next_x - ox) / (cos_a + 1e-6)
            else :
                next_x = map_x * TILE_SIZE
                side_dist_x = (ox - next_x) / -cos_a

            if dy > 0:
                next_y = (map_y + 1) * TILE_SIZE
                side_dist_y = (next_y - oy) / (sin_a + 1e-6)
            else :
                next_y = map_y * TILE_SIZE
                side_dist_y = (oy - next_y) / -sin_a

            # DDA loop
            tile_x, tile_y = map_x, map_y
            hit = False
            side = None

            while not hit:
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    tile_x += dx
                    side = 'x'
                else :
                    side_dist_y += delta_dist_y
                    tile_y += dy
                    side = 'y'

                wx = tile_x * TILE_SIZE + TILE_SIZE / 2
                wy = tile_y * TILE_SIZE + TILE_SIZE / 2

                if self.level.is_blocked(wx, wy):
                    hit = True

            # Distance to wall
            if side == 'x':
                depth = abs((tile_x * TILE_SIZE - ox + (1 - dx) * TILE_SIZE / 2) / cos_a)
            else:
                depth = abs((tile_y * TILE_SIZE - oy + (1 - dy) * TILE_SIZE / 2) / sin_a)

            # Fish-eye fix
            corrected_depth = depth * math.cos(player.get_angle() - angle)

            # Wall height
            wall_height = min((40000 / (corrected_depth + 0.0001)) * WALL_HEIGHT_SCALE, SCREEN_HEIGHT)

            # Shading
            brightness = 255 / (1 + corrected_depth * 0.03)
            brightness = max(0, min(255, int(brightness)))
            color = (brightness, brightness, brightness)

            # Draw slice
            x = ray * ray_width
            y = (SCREEN_HEIGHT - wall_height) / 2
            pg.draw.rect(screen, color, (x, y, ray_width, wall_height))

            angle += delta_angle