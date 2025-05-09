import pygame as pg
from pytmx.util_pygame import load_pygame
from data.config import TILE_SIZE

class Level:
    def __init__(self, filename):
        self.tmx_data = load_pygame(filename)
        self.map_width = self.tmx_data.width
        self.map_height = self.tmx_data.height
        self.collision_map = self.build_collision_map()
        self.spawn_point = self.get_player_spawn()

    def build_collision_map(self):
        grid=[]
        walls_layer = self.tmx_data.get_layer_by_name("Walls")

        for y in range(self.map_height):
            row=[]
            for x in range(self.map_width):
                tile=walls_layer.data[y][x]
                gid = tile.gid if hasattr(tile, 'gid') else tile
                row.append(1 if gid != 0 else 0) #1 walls, #0 empty
            grid.append(row)
        return grid

    def is_blocked(self, x, y):
        # x, y in pixels -> tile coords
        tx = int(x // TILE_SIZE)
        ty = int(y // TILE_SIZE)

        if 0 <= tx < self.map_width and 0 <= ty < self.map_height:
            blocked = self.collision_map[ty][tx] == 1
            return blocked
        else:
            return True

    def get_player_spawn(self):
        for obj in self.tmx_data.objects:
            if obj.name == 'playerStart':
                print(obj.x, obj.y)
                return obj.x, obj.y
        return TILE_SIZE * 2, TILE_SIZE * 2

    def draw_minimap(self, screen):
        for y in range(self.map_height):
            for x in range(self.map_width):
                color = (255, 255, 255) if self.collision_map[y][x] else (50, 50, 50)
                pg.draw.rect(screen, color, (x*4, y*4, 4, 4))