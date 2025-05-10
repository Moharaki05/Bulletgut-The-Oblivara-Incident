import pygame as pg
from pytmx.util_pygame import load_pygame
from data.config import TILE_SIZE
from entities.door import Door

class Level:
    def __init__(self, filename):
        self.tmx_data = load_pygame(filename)
        self.map_width = self.tmx_data.width
        self.map_height = self.tmx_data.height
        self.walls_layer = self.tmx_data.get_layer_by_name("Walls")
        self.floor_layer = self.tmx_data.get_layer_by_name("Floor")
        self.doors_layer = self.tmx_data.get_layer_by_name("Doors")

        # self.floor_color = (30,30,30)

        if "floor_color" in self.tmx_data.properties:
            hex_color = self.tmx_data.properties["floor_color"].lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            self.floor_color = (r, g, b)

        self.collision_map = self.build_collision_map()
        self.spawn_point = self.get_player_spawn()
        self.doors = self.load_doors()


    def build_collision_map(self):
        grid=[]
        for y in range(self.map_height):
            row=[]
            for x in range(self.map_width):
                tile=self.walls_layer.data[y][x]
                gid = tile.gid if hasattr(tile, 'gid') else tile
                row.append(1 if gid != 0 else 0) #1 walls, #0 empty
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
                print(obj.x, obj.y)
                return obj.x, obj.y
        return TILE_SIZE * 2, TILE_SIZE * 2

    def get_gid(self, wx, wy):
        grid_x = int(wx // TILE_SIZE)
        grid_y = int(wy // TILE_SIZE)

        if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
            # Check for door first
            for door in self.doors:
                if door.grid_x == grid_x and door.grid_y == grid_y:
                    if not door.is_open():
                        tile = self.doors_layer.data[grid_y][grid_x]
                        return tile.gid if hasattr(tile, 'gid') else tile
                    else:
                        return 0  # Empty if open

            # If no door or door is open, check walls
            tile = self.walls_layer.data[grid_y][grid_x]
            return tile.gid if hasattr(tile, 'gid') else tile

        return 0

    def load_doors(self):
        doors = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                tile = self.doors_layer.data[y][x]
                gid = tile.gid if hasattr(tile, 'gid') else tile
                if gid != 0:
                    print(f"Loading door at {x},{y} with GID {gid}")
                    doors.append(Door(x, y, TILE_SIZE))
        return doors
