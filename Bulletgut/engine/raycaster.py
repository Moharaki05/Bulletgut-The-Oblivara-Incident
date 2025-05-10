import pygame as pg
import math
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FOV, WALL_HEIGHT_SCALE, TILE_SIZE


class Raycaster:
    def __init__(self, level):
        self.level = level
        self.num_rays = SCREEN_WIDTH // 2  # adjust resolution here
        self.fov = FOV
        self.max_depth = 800


    def cast_rays(self, screen, player, color):
        self.render_floor(screen, color)
        self.render_walls(screen, player)

    def render_walls(self, screen, player):
        ox, oy = player.get_position()
        map_x = int(ox // TILE_SIZE)
        map_y = int(oy // TILE_SIZE)

        angle = player.get_angle() - self.fov / 2
        angle = angle % (2 * math.pi)
        delta_angle = self.fov / self.num_rays
        ray_width = SCREEN_WIDTH // self.num_rays

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
            else:
                next_x = map_x * TILE_SIZE
                side_dist_x = (ox - next_x) / (-cos_a + 1e-6)

            if dy > 0:
                next_y = (map_y + 1) * TILE_SIZE
                side_dist_y = (next_y - oy) / (sin_a + 1e-6)
            else:
                next_y = map_y * TILE_SIZE
                side_dist_y = (oy - next_y) / (-sin_a + 1e-6)

            # DDA loop
            tile_x, tile_y = map_x, map_y
            side = None

            while True:
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    tile_x += dx
                    side = 'x'
                else:
                    side_dist_y += delta_dist_y
                    tile_y += dy
                    side = 'y'

                wx = tile_x * TILE_SIZE + TILE_SIZE / 2
                wy = tile_y * TILE_SIZE + TILE_SIZE / 2

                if self.level.is_blocked(wx, wy):
                    break

            # Calculate distance
            if side == 'x':
                depth = abs((tile_x * TILE_SIZE - ox + (1 - dx) * TILE_SIZE / 2) / (cos_a + 1e-6))
                hit_x = oy + depth * sin_a
            else:
                depth = abs((tile_y * TILE_SIZE - oy + (1 - dy) * TILE_SIZE / 2) / (sin_a + 1e-6))
                hit_x = ox + depth * cos_a

            # Fish-eye fix
            depth *= math.cos(player.get_angle() - angle)

            # Calculate wall height - use your original formula
            wall_height = (40000 / (depth + 0.0001)) * WALL_HEIGHT_SCALE

            # Calculate texture x-coordinate
            hit_x = hit_x % TILE_SIZE
            tex_x = int(hit_x)

            # Flip texture for correct sides
            if (side == 'x' and dx < 0) or (side == 'y' and dy > 0):
                tex_x = TILE_SIZE - tex_x - 1

            # Get the tile and draw the column
            gid = self.level.get_gid(wx, wy)
            tile_img = self.level.tmx_data.get_tile_image_by_gid(gid)
            if gid and not tile_img:
                print(f"Missing tile image for gid: {gid}")

            if tile_img:
                # Prepare texture
                texture = pg.transform.scale(tile_img, (TILE_SIZE, TILE_SIZE))
                texture_column = texture.subsurface(tex_x, 0, 1, TILE_SIZE)

                # Make sure height is reasonable
                safe_height = max(1, min(int(wall_height), SCREEN_HEIGHT * 2))
                column = pg.transform.scale(texture_column, (1, safe_height))

                # Calculate vertical position
                column_y = (SCREEN_HEIGHT - safe_height) // 2

                # Draw the column
                x = ray * ray_width
                for i in range(ray_width):
                    screen.blit(column, (x + i, column_y))

            angle += delta_angle

    def render_floor(self, screen, color):
        pg.draw.rect(screen, color, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))