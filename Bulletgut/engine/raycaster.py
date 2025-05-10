import pygame as pg
import math
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FOV, WALL_HEIGHT_SCALE, TILE_SIZE


class Raycaster:
    def __init__(self, level):
        self.level = level
        self.num_rays = SCREEN_WIDTH // 2
        self.fov = FOV
        self.max_depth = 800

    def cast_rays(self, screen, player, color):
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
            # Check both visible and invisible doors
            # This is critical - closed doors should still be checked for intersection

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

            # Handle door intersection before wall intersection
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

            # Check if door is closer than the wall
            if door_obj and door_depth < wall_depth:
                depth = door_depth
                tex_x = door_tex_x
                side = door_side

                # Get door position
                wx, wy = door_obj.get_world_position()

                # Get the appropriate texture GID - either door or wall
                # For closed doors, we should show a wall texture
                if door_obj.is_visible():
                    # Door is visible/partially visible - use door texture
                    gid = self.level.get_door_gid(door_obj, closed=False)

                    # Calculate direction from door to player for texture orientation
                    door_to_player_x = ox - wx
                    door_to_player_y = oy - wy

                    # Calculate the dot product to determine which side of the door the player is on
                    if door_obj.axis == "x":
                        # For horizontal doors, check if player is to the left or right
                        if (door_to_player_x < 0 and cos_a > 0) or (door_to_player_x > 0 and cos_a < 0):
                            tex_x = TILE_SIZE - tex_x - 1  # Flip texture if viewing from "back"
                    else:
                        # For vertical doors, check if player is above or below
                        if (door_to_player_y < 0 and sin_a > 0) or (door_to_player_y > 0 and sin_a < 0):
                            tex_x = TILE_SIZE - tex_x - 1  # Flip texture if viewing from "back"
                else:
                    # Door is fully closed - use wall texture
                    gid = self.level.get_door_gid(door_obj, closed=True)
            else:
                depth = wall_depth
                wx = tile_x * TILE_SIZE + TILE_SIZE / 2
                wy = tile_y * TILE_SIZE + TILE_SIZE / 2
                gid = self.level.get_gid(wx, wy)

                # Standard wall texture flipping based on view angle
                if (side == 'x' and dx < 0) or (side == 'y' and dy > 0):
                    tex_x = TILE_SIZE - tex_x - 1

            # Adjust for fish-eye effect
            depth *= math.cos(player.get_angle() - angle)
            wall_height = (40000 / (depth + 0.0001)) * WALL_HEIGHT_SCALE

            # Get and render the texture
            tile_img = self.level.tmx_data.get_tile_image_by_gid(gid)
            if gid and not tile_img:
                # Fallback for missing textures - use a default GID
                default_gid = 1  # Usually the first texture
                tile_img = self.level.tmx_data.get_tile_image_by_gid(default_gid)

            if tile_img:
                texture = pg.transform.scale(tile_img, (TILE_SIZE, TILE_SIZE))
                texture_column = texture.subsurface(tex_x, 0, 1, TILE_SIZE)
                safe_height = max(1, min(int(wall_height), SCREEN_HEIGHT * 2))

                # Adjust width for doors based on their thickness
                if door_obj and door_depth < wall_depth:
                    # If the door is visible, adjust width based on thickness
                    if door_obj.is_visible():
                        door_width_px = max(1, int(door_obj.get_door_thickness_px()))
                        column = pg.transform.scale(texture_column, (door_width_px, safe_height))
                    else:
                        # For closed doors, use standard ray width
                        column = pg.transform.scale(texture_column, (ray_width, safe_height))
                else:
                    column = pg.transform.scale(texture_column, (ray_width, safe_height))

                column_y = (SCREEN_HEIGHT - safe_height) // 2
                x = ray * ray_width
                screen.blit(column, (x, column_y))

            angle += delta_angle