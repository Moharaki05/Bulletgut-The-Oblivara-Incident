import pygame as pg
import math
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FOV, WALL_HEIGHT_SCALE, TILE_SIZE, PICKUP_SCALE


class Raycaster:
    def __init__(self, level, player):
        self.level = level
        self.player = player
        self.num_rays = SCREEN_WIDTH // 2
        self.wall_height_scale = 1.0
        self.fov = FOV
        self.max_depth = 800
        self.z_buffer = [float('inf')] * SCREEN_WIDTH  # Store depth for each screen column

    def cast_rays(self, screen, player, color):
        # Reset z-buffer for new frame
        self.z_buffer = [float('inf')] * SCREEN_WIDTH

        self.render_floor(screen, color)
        self.render_walls(screen, player)

    @staticmethod
    def render_floor(screen, color):
        height = screen.get_height()
        pg.draw.rect(screen, color, (0, height // 2, SCREEN_WIDTH, height // 2))

    def handle_door_intersection(self, ox, oy, angle):
        """FIXED: Door intersection that works for all door states"""
        closest_door = None
        closest_depth = float("inf")
        tex_x = 0
        side = None

        for door in self.level.doors:
            # CRITICAL FIX: Check doors in ALL states except completely invisible
            # Don't skip closed doors!
            if door.progress >= 0.95:  # Only skip when almost fully open
                continue

            # Use door's grid position directly for closed doors
            door_world_x = door.grid_x * TILE_SIZE
            door_world_y = door.grid_y * TILE_SIZE

            # For closed doors, use full tile bounds
            if door.progress <= 0.05:  # Fully closed
                bounds = {
                    "min_x": door_world_x,
                    "max_x": door_world_x + TILE_SIZE,
                    "min_y": door_world_y,
                    "max_y": door_world_y + TILE_SIZE
                }
            else:
                # Use calculated bounds for opening doors
                bounds = door.get_door_bounds()

            if not bounds:
                continue

            # Test intersection with door bounds
            if door.axis == "x":
                # Horizontal door
                if abs(math.cos(angle)) < 1e-6:
                    continue

                for face_x in [bounds["min_x"], bounds["max_x"]]:
                    t = (face_x - ox) / math.cos(angle)
                    if t <= 0:
                        continue

                    hit_y = oy + t * math.sin(angle)
                    if bounds["min_y"] <= hit_y <= bounds["max_y"] and t < closest_depth:
                        closest_door = door
                        closest_depth = t
                        side = "x"

                        # Simple texture calculation
                        rel_y = (hit_y - bounds["min_y"]) / max(1, bounds["max_y"] - bounds["min_y"])
                        tex_x = int(rel_y * TILE_SIZE) % TILE_SIZE

            else:  # Vertical door
                if abs(math.sin(angle)) < 1e-6:
                    continue

                for face_y in [bounds["min_y"], bounds["max_y"]]:
                    t = (face_y - oy) / math.sin(angle)
                    if t <= 0:
                        continue

                    hit_x = ox + t * math.cos(angle)
                    if bounds["min_x"] <= hit_x <= bounds["max_x"] and t < closest_depth:
                        closest_door = door
                        closest_depth = t
                        side = "y"

                        # Simple texture calculation
                        rel_x = (hit_x - bounds["min_x"]) / max(1, bounds["max_x"] - bounds["min_x"])
                        tex_x = int(rel_x * TILE_SIZE) % TILE_SIZE

        return closest_door, closest_depth, tex_x, side

    def render_walls(self, screen, player):
        """Simplified wall rendering that properly handles doors"""
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

            # Check for door intersection FIRST
            door_obj, door_depth, door_tex_x, door_side = self.handle_door_intersection(ox, oy, angle)

            # DDA for walls
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

            # Calculate wall distance and texture
            if side == 'x':
                wall_depth = abs((tile_x * TILE_SIZE - ox + (1 - dx) * TILE_SIZE / 2) / (cos_a + 1e-6))
                hit_x = oy + wall_depth * sin_a
                wall_tex_x = int(hit_x % TILE_SIZE)
            else:
                wall_depth = abs((tile_y * TILE_SIZE - oy + (1 - dy) * TILE_SIZE / 2) / (sin_a + 1e-6))
                hit_x = ox + wall_depth * cos_a
                wall_tex_x = int(hit_x % TILE_SIZE)

            # Decide what to render
            if door_obj and door_depth < wall_depth:
                # DOOR IS CLOSER - render door
                depth = door_depth
                tex_x = door_tex_x
                render_width = max(1, door_obj.get_door_thickness_px())

                # SIMPLE door texture lookup - no complex fallbacks
                door_wx = door_obj.grid_x * TILE_SIZE + TILE_SIZE // 2
                door_wy = door_obj.grid_y * TILE_SIZE + TILE_SIZE // 2
                gid = self.level.get_gid(door_wx, door_wy)

            else:
                # WALL IS CLOSER - render wall
                depth = wall_depth
                tex_x = wall_tex_x
                render_width = ray_width

                wall_wx = tile_x * TILE_SIZE + TILE_SIZE / 2
                wall_wy = tile_y * TILE_SIZE + TILE_SIZE / 2
                gid = self.level.get_gid(wall_wx, wall_wy)

                # Texture flipping
                if (side == 'x' and dx < 0) or (side == 'y' and dy > 0):
                    tex_x = TILE_SIZE - tex_x - 1

            # Fisheye correction
            depth *= math.cos(player.get_angle() - angle)
            wall_height = (40000 / (depth + 0.0001)) * WALL_HEIGHT_SCALE

            # Z-buffer
            screen_x = ray * ray_width
            for x in range(screen_x, min(screen_x + ray_width, SCREEN_WIDTH)):
                self.z_buffer[x] = depth

            # Render
            tile_img = self.level.tmx_data.get_tile_image_by_gid(gid)
            if tile_img:
                texture = pg.transform.scale(tile_img, (TILE_SIZE, TILE_SIZE))
                tex_x = max(0, min(tex_x, TILE_SIZE - 1))
                texture_column = texture.subsurface(tex_x, 0, 1, TILE_SIZE)

                height = screen.get_height()
                safe_height = max(1, min(int(wall_height), height * 2))
                column = pg.transform.scale(texture_column, (render_width, safe_height))

                column_y = (height - safe_height) // 2
                x = ray * ray_width
                screen.blit(column, (x, column_y))

            angle += delta_angle

    def get_door_at_position(self, wx, wy):
        """Get door object at world position"""
        grid_x = int(wx // TILE_SIZE)
        grid_y = int(wy // TILE_SIZE)

        for door in self.level.doors:
            if door.grid_x == grid_x and door.grid_y == grid_y:
                return door
        return None

    def get_door_texture_gid(self, door):
        """Get appropriate texture GID for door"""
        # Try to get door-specific texture
        is_closed = door.progress <= 0.1
        gid = self.level.get_door_gid(door, closed=is_closed)

        if gid and gid > 0:
            return gid

        # Fallback: use door's original tile texture
        door_wx = door.grid_x * TILE_SIZE + TILE_SIZE // 2
        door_wy = door.grid_y * TILE_SIZE + TILE_SIZE // 2
        base_gid = self.level.get_gid(door_wx, door_wy)

        if base_gid and base_gid > 0:
            return base_gid

        # Last fallback: use a default door texture (you may need to adjust this)
        return 1  # Replace with your default door texture GID

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

            enemy_img = enemy.get_sprite(player.x, player.y)
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
            height = screen.get_height()
            center_y = height // 2
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

    def get_center_ray_angle(self):
        return self.player.angle

    def render_pickups(self, screen, player, pickups):
        ox, oy = player.get_position()
        player_angle = player.get_angle()

        # Sort pickups by distance (farthest first for proper depth ordering)
        sorted_pickups = []
        for pickup in pickups:
            if pickup.picked_up:
                continue

            dx = pickup.x - ox
            dy = pickup.y - oy
            distance = math.hypot(dx, dy)
            sorted_pickups.append((pickup, distance))

        sorted_pickups.sort(key=lambda x: x[1], reverse=True)

        for pickup, distance in sorted_pickups:
            dx = pickup.x - ox
            dy = pickup.y - oy

            # Calculate angle to pickup relative to player's facing direction
            pickup_angle = math.atan2(dy, dx)
            angle_diff = pickup_angle - player_angle

            # Normalize angle difference to [-π, π]
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            # Check if pickup is within FOV
            if abs(angle_diff) > self.fov / 2:
                continue

            # Calculate screen X position
            screen_x = int(SCREEN_WIDTH / 2 + (angle_diff / (self.fov / 2)) * (SCREEN_WIDTH / 2))

            # Correct distance for fisheye effect (same as walls)
            corrected_distance = distance * math.cos(angle_diff)

            # Wolf3D-style scaling: pickups are much smaller than walls
            # Use a smaller base size for pickups (they're floor items, not wall-height)
            base_pickup_size = 8000  # Much smaller than wall's 40 000
            pickup_height = int((base_pickup_size / (corrected_distance + 0.0001)) * WALL_HEIGHT_SCALE * PICKUP_SCALE)

            # Get original sprite dimensions
            sprite = pickup.sprite
            original_width, original_height = sprite.get_size()

            # Maintain aspect ratio properly
            aspect_ratio = original_width / original_height
            pickup_width = int(pickup_height * aspect_ratio)

            # Clamp height but recalculate width to maintain aspect ratio
            max_pickup_height = SCREEN_HEIGHT // 6
            if pickup_height > max_pickup_height:
                pickup_height = max_pickup_height
                pickup_width = int(pickup_height * aspect_ratio)

            # Ensure minimum size
            pickup_height = max(12, pickup_height)
            pickup_width = max(int(12 * aspect_ratio), pickup_width)

            # Calculate drawing bounds
            left_x = screen_x - pickup_width // 2
            right_x = left_x + pickup_width

            # Skip if completely off-screen
            if right_x < 0 or left_x >= SCREEN_WIDTH:
                continue

            # Check z-buffer visibility
            visible = False
            for x in range(max(0, left_x), min(SCREEN_WIDTH, right_x)):
                if corrected_distance < self.z_buffer[x]:
                    visible = True
                    break

            if not visible:
                continue

            # Scale the sprite maintaining aspect ratio
            scaled_sprite = pg.transform.scale(sprite, (pickup_width, pickup_height))

            # Position pickup on the ground (Wolf3D style)
            # Ground level should be at the horizon line (screen center)
            surface_height = screen.get_height()
            horizon_y = surface_height // 2
            pickup_y = horizon_y + pickup_height + 35

            # Render pickup column by column with z-buffer checking
            for x in range(max(0, left_x), min(SCREEN_WIDTH, right_x)):
                if corrected_distance < self.z_buffer[x]:
                    # Calculate which column of the sprite to draw
                    local_x = x - left_x
                    if pickup_width > 0 and local_x < pickup_width:
                        # Extract single pixel column from scaled sprite
                        try:
                            column = scaled_sprite.subsurface(local_x, 0, 1, pickup_height)
                            screen.blit(column, (x, pickup_y))
                        except ValueError:
                            # Skip if subsurface is invalid
                            continue