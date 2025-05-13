import pygame as pg
import math
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FOV, WALL_HEIGHT_SCALE, TILE_SIZE


class Raycaster:
    def __init__(self, level):
        self.level = level
        self.num_rays = SCREEN_WIDTH // 2
        self.fov = FOV
        self.max_depth = 800
        self.z_buffer = [float('inf')] * SCREEN_WIDTH  # Store depth for each screen column

    def cast_rays(self, screen, player, color):
        # Reset z-buffer for new frame
        self.z_buffer = [float('inf')] * SCREEN_WIDTH

        self.render_floor(screen, color)
        self.render_walls(screen, player)

    def render_floor(self, screen, color):
        pg.draw.rect(screen, color, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

    def handle_door_intersection(self, ox, oy, angle):
        closest_door = None
        closest_depth = float("inf")
        tex_x = 0
        side = None

        for door in self.level.doors:
            if not door.is_visible():
                continue

            bounds = door.get_door_bounds()

            if door.axis == "x":
                if abs(math.cos(angle)) < 1e-6:
                    continue
                t = (bounds["min_x"] - ox) / math.cos(angle)
                if t <= 0:
                    continue
                hit_y = oy + t * math.sin(angle)
                if bounds["min_y"] <= hit_y <= bounds["max_y"] and t < closest_depth:
                    closest_door = door
                    closest_depth = t
                    rel_y = (hit_y - bounds["min_y"]) / (bounds["max_y"] - bounds["min_y"])
                    tex_x = int(rel_y * TILE_SIZE)
                    side = "x"
            else:
                if abs(math.sin(angle)) < 1e-6:
                    continue
                t = (bounds["min_y"] - oy) / math.sin(angle)
                if t <= 0:
                    continue
                hit_x = ox + t * math.cos(angle)
                if bounds["min_x"] <= hit_x <= bounds["max_x"] and t < closest_depth:
                    closest_door = door
                    closest_depth = t
                    rel_x = (hit_x - bounds["min_x"]) / (bounds["max_x"] - bounds["min_x"])
                    tex_x = int(rel_x * TILE_SIZE)
                    side = "y"

        return closest_door, closest_depth, tex_x, side

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
            dx = 1 if cos_a >= 0 else -1
            dy = 1 if sin_a >= 0 else -1

            delta_dist_x = abs(TILE_SIZE / (cos_a + 1e-6))
            delta_dist_y = abs(TILE_SIZE / (sin_a + 1e-6))

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

            tile_x, tile_y = map_x, map_y
            side = None

            door_obj, door_depth, door_tex_x, door_side = self.handle_door_intersection(ox, oy, angle)

            wall_hit = False
            while not wall_hit:
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
                    wall_hit = True

            if side == 'x':
                wall_depth = abs((tile_x * TILE_SIZE - ox + (1 - dx) * TILE_SIZE / 2) / (cos_a + 1e-6))
                hit_x = oy + wall_depth * sin_a
                tex_x = int(hit_x % TILE_SIZE)
            else:
                wall_depth = abs((tile_y * TILE_SIZE - oy + (1 - dy) * TILE_SIZE / 2) / (sin_a + 1e-6))
                hit_x = ox + wall_depth * cos_a
                tex_x = int(hit_x % TILE_SIZE)

            if door_obj and door_depth < wall_depth:
                depth = door_depth
                tex_x = door_tex_x
                side = door_side
                wx, wy = door_obj.get_world_position()
                gid = self.level.get_door_gid(door_obj, closed=not door_obj.is_visible())

                # Flip door texture if player is behind the door
                vec_to_player_x = ox - wx
                vec_to_player_y = oy - wy
                dot = vec_to_player_x * math.cos(angle) + vec_to_player_y * math.sin(angle)

                if dot < 0:
                    tex_x = TILE_SIZE - tex_x - 1  # Flip texture X

            else:
                depth = wall_depth
                wx = tile_x * TILE_SIZE + TILE_SIZE / 2
                wy = tile_y * TILE_SIZE + TILE_SIZE / 2
                gid = self.level.get_gid(wx, wy)

                if (side == 'x' and dx < 0) or (side == 'y' and dy > 0):
                    tex_x = TILE_SIZE - tex_x - 1

            depth *= math.cos(player.get_angle() - angle)
            wall_height = (40000 / (depth + 0.0001)) * WALL_HEIGHT_SCALE

            # Store depth information in z-buffer for sprite rendering
            screen_x = ray * ray_width
            for x in range(screen_x, min(screen_x + ray_width, SCREEN_WIDTH)):
                self.z_buffer[x] = depth

            tile_img = self.level.tmx_data.get_tile_image_by_gid(gid)
            if gid and not tile_img:
                print(f"Missing tile image for gid: {gid}")

            if tile_img:
                texture = pg.transform.scale(tile_img, (TILE_SIZE, TILE_SIZE))
                texture_column = texture.subsurface(tex_x, 0, 1, TILE_SIZE)
                safe_height = max(1, min(int(wall_height), SCREEN_HEIGHT * 2))

                # Adjust door thickness if it's a door
                if door_obj and door_depth < wall_depth:
                    door_width_px = max(1, int(door_obj.get_door_thickness_px()))
                    column = pg.transform.scale(texture_column, (door_width_px, safe_height))
                else:
                    column = pg.transform.scale(texture_column, (ray_width, safe_height))

                column_y = (SCREEN_HEIGHT - safe_height) // 2
                x = ray * ray_width
                screen.blit(column, (x, column_y))

            angle += delta_angle

    def render_enemies(self, screen, player, enemies):
        ox, oy = player.get_position()
        angle = player.get_angle()

        size_reduction_factor = 0.55

        sorted_enemies = []
        for enemy in enemies:
            ex, ey = enemy.x, enemy.y
            dx, dy = ex - ox, ey - oy
            dist = math.hypot(dx, dy)
            sorted_enemies.append((enemy, dist))

        sorted_enemies.sort(key=lambda x: x[1], reverse=True)

        for enemy, dist in sorted_enemies:
            ex, ey = enemy.x, enemy.y
            dx, dy = ex - ox, ey - oy

            dir_angle = math.atan2(dy, dx)
            delta = (dir_angle - angle + math.pi) % (2 * math.pi) - math.pi
            if abs(delta) > self.fov / 2:
                continue

            screen_x = int((0.5 + delta / self.fov) * SCREEN_WIDTH)
            corrected_dist = dist * math.cos(delta)

            enemy_img = enemy.get_sprite()
            if not enemy_img:
                continue

            wall_height = (40000 / (corrected_dist + 0.0001)) * WALL_HEIGHT_SCALE

            wall_height *= size_reduction_factor

            original_width, original_height = enemy_img.get_size()
            aspect_ratio = original_width / original_height

            img_height = int(wall_height)
            img_width = int(img_height * aspect_ratio)

            max_size = SCREEN_WIDTH // 3
            if img_width > max_size or img_height > max_size:
                scale_factor = max_size / max(img_width, img_height)
                img_width = int(img_width * scale_factor)
                img_height = int(img_height * scale_factor)

            left_x = max(0, screen_x - img_width // 2)
            right_x = min(SCREEN_WIDTH - 1, screen_x + img_width // 2)

            visible = False
            for x in range(left_x, right_x + 1):
                if 0 <= x < SCREEN_WIDTH and corrected_dist < self.z_buffer[x]:
                    visible = True
                    break

            if not visible:
                continue

            sprite = pg.transform.scale(enemy_img, (img_width, img_height))
            center_y = SCREEN_HEIGHT // 2
            floor_offset = img_height * 0.3
            screen_y = center_y - (img_height // 2) + floor_offset

            for x in range(left_x, right_x + 1):
                if x < 0 or x >= SCREEN_WIDTH:
                    continue

                if corrected_dist < self.z_buffer[x]:
                    if right_x != left_x:
                        col_ratio = (x - left_x) / (right_x - left_x)
                        sprite_x = min(img_width - 1, max(0, int(col_ratio * img_width)))
                    else:
                        sprite_x = 0

                    if sprite_x < img_width:
                        column = sprite.subsurface(sprite_x, 0, 1, img_height)
                        screen.blit(column, (x, screen_y))
