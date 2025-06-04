simport pygame as pg
from pytmx.util_pygame import load_pygame
from data.config import TILE_SIZE
from entities.door import Door
from entities.enemy_types import Gunner
# (Gunner, Shotgunner, Serpentipede, Plutonworm)
from entities.pickups.ammo_pickup import AmmoPickup
from entities.pickups.item_pickup import ItemPickup
from entities.pickups.weapon_pickup import WeaponPickup

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
        self.pickups = self.load_pickups()


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
        """Version améliorée de is_blocked inspirée de DUGA"""
        tx = int(x // TILE_SIZE)
        ty = int(y // TILE_SIZE)

        if not (0 <= tx < self.map_width and 0 <= ty < self.map_height):
            return True

        # Vérifier collision avec les murs
        if self.collision_map[ty][tx] == 1:
            return True

        # Vérifier collision avec les portes de manière plus précise
        for door in self.doors:
            if door.grid_x == tx and door.grid_y == ty:
                if door.is_blocking():
                    # Vérification plus fine basée sur les bounds réels
                    bounds = door.get_door_bounds()
                    if (bounds["min_x"] <= x <= bounds["max_x"] and
                            bounds["min_y"] <= y <= bounds["max_y"]):
                        return True

        return False

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
        """Version améliorée du rendu de porte inspirée de DUGA"""
        grid_x, grid_y = door.grid_x, door.grid_y

        # Si la porte est complètement fermée, utiliser la texture de mur
        if closed and door.progress == 0:
            return self._get_wall_texture_for_door(door)

        # Si la porte est en mouvement ou ouverte, utiliser la texture de porte
        tile = self.doors_layer.data[grid_y][grid_x]
        door_gid = tile.gid if hasattr(tile, 'gid') else tile

        # Fallback si pas de texture de porte
        if door_gid == 0:
            return self._get_wall_texture_for_door(door)

        return door_gid

    def _get_wall_texture_for_door(self, door):
        """Trouve une texture de mur appropriée pour une porte fermée"""
        grid_x, grid_y = door.grid_x, door.grid_y

        # Chercher dans les tuiles adjacentes (comme DUGA)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in directions:
            check_x, check_y = grid_x + dx, grid_y + dy

            if (0 <= check_x < self.map_width and 0 <= check_y < self.map_height):
                tile = self.walls_layer.data[check_y][check_x]
                gid = tile.gid if hasattr(tile, 'gid') else tile

                if gid != 0:
                    return gid

        # Fallback: première texture de mur trouvée
        for y in range(self.map_height):
            for x in range(self.map_width):
                tile = self.walls_layer.data[y][x]
                gid = tile.gid if hasattr(tile, 'gid') else tile
                if gid != 0:
                    return gid

        return 1  # Ultimate fallback

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
                enemy_type = obj.properties.get("enemy_type", "gunner").lower()
                x = obj.x
                y = obj.y

                if enemy_type == "gunner":
                    enemies.append(Gunner(x, y, self))
                # elif enemy_type == "shotgunner":
                #     enemies.append(Shotgunner(x, y, self))
                # elif enemy_type == "serpentipede":
                #     enemies.append(Serpentipede(x, y, self))
                # elif enemy_type == "plutonworm":
                #     enemies.append(Plutonworm(x, y, self))
                # else:
                    print(f"[Erreur] Type d'ennemi inconnu : {enemy_type}")
        return enemies

    def check_collision(self, position):
        x, y = int(position[0]), int(position[1])
        return self.is_blocked(x, y)

    def load_pickups(self):
        pickups = []
        for obj in self.tmx_data.objects:
            if obj.type == "Ammo":
                ammo_type = obj.properties["ammo_type"]
                amount = int(obj.properties["amount"])
                sprite_path = obj.properties.get("sprite", f"assets/pickups/ammo/ammo_{ammo_type}.png")
                x = obj.x
                y = obj.y
                pickups.append(AmmoPickup(x, y, ammo_type, amount, sprite_path))

            elif obj.type == "Weapon":
                weapon_name = obj.properties["weapon_name"]
                sprite = obj.properties.get("sprite", f"assets/pickups/weapons/{weapon_name}.png")
                ammo_type = obj.properties["ammo_type"]
                amount = int(obj.properties["amount"])
                x = obj.x
                y = obj.y
                pickups.append(WeaponPickup(x, y, weapon_name, sprite, ammo_type, amount))

            elif obj.type == "Item":
                item_type = obj.properties["item_type"]
                sprite = obj.properties.get("sprite", f"assets/pickups/items/{item_type}.png")
                amount = int(obj.properties["amount"])
                x = obj.x
                y = obj.y
                pickups.append(ItemPickup(x, y, item_type, amount, sprite))

        return pickups



