import pygame as pg
from pytmx.util_pygame import load_pygame
from data.config import TILE_SIZE
from entities.door import Door
from entities.enemy_base import Enemy

class Level:
    def __init__(self, filename):
        self.tmx_data = load_pygame(filename)
        self.map_width = self.tmx_data.width
        self.map_height = self.tmx_data.height
        self.walls_layer = self.tmx_data.get_layer_by_name("Walls")
        self.floor_layer = self.tmx_data.get_layer_by_name("Floor")
        self.doors_layer = self.tmx_data.get_layer_by_name("Doors")
        self.enemies_layer = self.tmx_data.get_layer_by_name("EnemyVisuals")

        if "floor_color" in self.tmx_data.properties:
            hex_color = self.tmx_data.properties["floor_color"].lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            self.floor_color = (r, g, b)
        else:
            self.floor_color = (30, 30, 30)

        self.enemies = self.load_enemies()
        self.collision_map = self.build_collision_map()
        self.spawn_point = self.get_player_spawn()
        self.doors = self.load_doors()


        # Store closed door GIDs for rendering
        self.closed_door_gids = self.find_closed_door_gids()

    def build_collision_map(self):
        grid = []
        for y in range(self.map_height):
            row = []
            for x in range(self.map_width):
                tile = self.walls_layer.data[y][x]
                gid = tile.gid if hasattr(tile, 'gid') else tile
                row.append(1 if gid != 0 else 0)  # 1 walls, #0 empty
            grid.append(row)
        return grid

    def is_blocked(self, x, y):
        tx = int(x // TILE_SIZE)
        ty = int(y // TILE_SIZE)

        if 0 <= tx < self.map_width and 0 <= ty < self.map_height:
            # Check wall collision
            if self.collision_map[ty][tx] == 1:
                return True

            # Check if there's a blocking door
            for door in self.doors:
                if door.grid_x == tx and door.grid_y == ty and door.is_blocking():
                    return True

            return False
        return True

    def get_player_spawn(self):
        for obj in self.tmx_data.objects:
            if obj.name == 'playerStart':
                return obj.x, obj.y
        return TILE_SIZE * 2, TILE_SIZE * 2

    def get_gid(self, wx, wy):
        grid_x = int(wx // TILE_SIZE)
        grid_y = int(wy // TILE_SIZE)

        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
            # Check for door first
            for door in self.doors:
                if door.grid_x == grid_x and door.grid_y == grid_y and door.is_blocking():
                    # Get the door tile GID from the doors layer
                    door_tile = self.doors_layer.data[grid_y][grid_x]
                    door_gid = door_tile.gid if hasattr(door_tile, 'gid') else door_tile
                    return door_gid

            # If no blocking door, check walls
            tile = self.walls_layer.data[grid_y][grid_x]
            return tile.gid if hasattr(tile, 'gid') else tile

        return 0

    def find_closed_door_gids(self):
        door_gids = {}

        # Scan through all doors to find adjacent wall tiles
        for door in self.doors:
            grid_x, grid_y = door.grid_x, door.grid_y

            # Find adjacent wall tiles based on door axis
            if door.axis == "x":  # Horizontal sliding door
                # Look for wall tiles to the left and right
                if 0 <= grid_x - 1 < self.map_width:
                    left_tile = self.walls_layer.data[grid_y][grid_x - 1]
                    left_gid = left_tile.gid if hasattr(left_tile, 'gid') else left_tile
                    if left_gid != 0:
                        door_gids[(grid_x, grid_y, "left")] = left_gid

                if 0 <= grid_x + 1 < self.map_width:
                    right_tile = self.walls_layer.data[grid_y][grid_x + 1]
                    right_gid = right_tile.gid if hasattr(right_tile, 'gid') else right_tile
                    if right_gid != 0:
                        door_gids[(grid_x, grid_y, "right")] = right_gid
            else:  # Vertical sliding door
                # Look for wall tiles above and below
                if 0 <= grid_y - 1 < self.map_height:
                    top_tile = self.walls_layer.data[grid_y - 1][grid_x]
                    top_gid = top_tile.gid if hasattr(top_tile, 'gid') else top_tile
                    if top_gid != 0:
                        door_gids[(grid_x, grid_y, "top")] = top_gid

                if 0 <= grid_y + 1 < self.map_height:
                    bottom_tile = self.walls_layer.data[grid_y + 1][grid_x]
                    bottom_gid = bottom_tile.gid if hasattr(bottom_tile, 'gid') else bottom_tile
                    if bottom_gid != 0:
                        door_gids[(grid_x, grid_y, "bottom")] = bottom_gid

        return door_gids

    def get_door_gid(self, door, closed=False):
        grid_x, grid_y = door.grid_x, door.grid_y

        if closed:
            # For closed doors, we need a wall texture
            # First check the cached door GIDs
            if door.axis == "x":  # Horizontal door
                left_key = (grid_x, grid_y, "left")
                right_key = (grid_x, grid_y, "right")

                if left_key in self.closed_door_gids:
                    return self.closed_door_gids[left_key]
                elif right_key in self.closed_door_gids:
                    return self.closed_door_gids[right_key]

                # If we don't have cached GIDs, check adjacent wall tiles
                if 0 <= grid_x - 1 < self.map_width:
                    left_tile = self.walls_layer.data[grid_y][grid_x - 1]
                    left_gid = left_tile.gid if hasattr(left_tile, 'gid') else left_tile
                    if left_gid != 0:
                        return left_gid

                if 0 <= grid_x + 1 < self.map_width:
                    right_tile = self.walls_layer.data[grid_y][grid_x + 1]
                    right_gid = right_tile.gid if hasattr(right_tile, 'gid') else right_tile
                    if right_gid != 0:
                        return right_gid
            else:  # Vertical door
                top_key = (grid_x, grid_y, "top")
                bottom_key = (grid_x, grid_y, "bottom")

                if top_key in self.closed_door_gids:
                    return self.closed_door_gids[top_key]
                elif bottom_key in self.closed_door_gids:
                    return self.closed_door_gids[bottom_key]

                # Check adjacent wall tiles
                if 0 <= grid_y - 1 < self.map_height:
                    top_tile = self.walls_layer.data[grid_y - 1][grid_x]
                    top_gid = top_tile.gid if hasattr(top_tile, 'gid') else top_tile
                    if top_gid != 0:
                        return top_gid

                if 0 <= grid_y + 1 < self.map_height:
                    bottom_tile = self.walls_layer.data[grid_y + 1][grid_x]
                    bottom_gid = bottom_tile.gid if hasattr(bottom_tile, 'gid') else bottom_tile
                    if bottom_gid != 0:
                        return bottom_gid

            # Fallback - find any valid wall texture
            for y in range(self.map_height):
                for x in range(self.map_width):
                    tile = self.walls_layer.data[y][x]
                    gid = tile.gid if hasattr(tile, 'gid') else tile
                    if gid != 0:
                        return gid

            # Last resort - just return 1 (usually the first wall texture)
            return 1

        # For open/opening/closing doors, use the door texture
        tile = self.doors_layer.data[grid_y][grid_x]
        door_gid = tile.gid if hasattr(tile, 'gid') else tile

        # Make sure we have a valid door GID
        if door_gid == 0:
            # If no door texture found, fall back to a wall texture (better than nothing)
            return self.get_door_gid(door, closed=True)

        return door_gid

    def load_doors(self):
        doors = []
        object_layer = [obj for obj in self.tmx_data.objects if obj.type == "door"]
        for obj in object_layer:
            grid_x = int(obj.x // TILE_SIZE)
            grid_y = int(obj.y // TILE_SIZE)

            axis = obj.properties.get("axis", "x")
            thickness = float(obj.properties.get("thickness", 0.2))
            auto_close_time = float(obj.properties.get("auto_close_time", 3.0))

            door = Door(grid_x, grid_y, auto_close_time, thickness)
            door.axis = axis
            doors.append(door)

        return doors

    def load_enemies(self):
        enemies = []
        for obj in self.tmx_data.objects:
            if obj.type == "enemy":
                enemy_type = obj.properties.get("enemy_type", "gunner")
                x = obj.x
                y = obj.y

                enemy_texture = pg.image.load("./assets/sprites/Enemy/Soldier/Movement/Walk1_Front.png").convert_alpha()
                frame_width = 41
                frame_height = 57
                first_frame = enemy_texture.subsurface(pg.Rect(0, 0, frame_width, frame_height))

                # enemy_texture.fill((255, 0, 0))  # bright red block

                enemy = Enemy(x, y, first_frame)
                enemies.append(enemy)
        return enemies