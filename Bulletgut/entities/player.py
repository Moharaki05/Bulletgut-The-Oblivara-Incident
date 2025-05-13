import math
import pygame as pg
from data.config import TILE_SIZE, PLAYER_SPEED, ROTATE_SPEED, FOV, MOUSE_SENSITIVITY_MULTIPLIER, PLAYER_COLLISION_RADIUS


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0 # Facing right
        self.fov = FOV
        self.move_speed = PLAYER_SPEED
        self.rotate_speed = ROTATE_SPEED
        self.collision_radius = PLAYER_COLLISION_RADIUS
        self.moving = False

        self.weapons = []
        self.current_weapon_index = 0

    def handle_inputs(self, keys, dt, mouse_dx=0, level=None):
        # Direction vector
        speed = self.move_speed * dt
        dx = math.cos(self.angle)
        dy = math.sin(self.angle)

        # Save original position for collision detection
        original_x, original_y = self.x, self.y
        new_x, new_y = original_x, original_y

        self.moving = False

        if keys[pg.K_w]:
            new_x += dx * speed
            new_y += dy * speed
        if keys[pg.K_s]:
            new_x -= dx * speed
            new_y -= dy * speed
        if keys[pg.K_a]:
            new_x += dy * speed
            new_y -= dx * speed
        if keys[pg.K_d]:
            new_x -= dy * speed
            new_y += dx * speed

        if keys[pg.K_w] or keys[pg.K_s] or keys[pg.K_a] or keys[pg.K_d]:
            # Une touche de mouvement est enfoncée
            self.moving = True

            # Apply movement with improved collision detection
        if level:
            self.x, self.y = self.get_safe_position(level, original_x, original_y, new_x, new_y)
        else:
            self.x, self.y = new_x, new_y

        # Mouse rotation
        self.angle += mouse_dx * self.rotate_speed * dt * MOUSE_SENSITIVITY_MULTIPLIER
        self.angle %= 2 * math.pi # Keep an angle between 0 and 2pi

    def check_collision(self, level, x, y):
        # Check surrounding tiles
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_x = grid_x + dx
                check_y = grid_y + dy

                # Get the center of the tile
                tile_center_x = check_x * TILE_SIZE + TILE_SIZE / 2
                tile_center_y = check_y * TILE_SIZE + TILE_SIZE / 2

                # If this is a wall tile, check distance
                if level.is_blocked(tile_center_x, tile_center_y):
                    # Find the closest point on the tile to the player
                    tile_x = check_x * TILE_SIZE
                    tile_y = check_y * TILE_SIZE

                    closest_x = max(tile_x, min(x, tile_x + TILE_SIZE))
                    closest_y = max(tile_y, min(y, tile_y + TILE_SIZE))

                    # Calculate distance
                    dist_x = x - closest_x
                    dist_y = y - closest_y
                    distance = math.sqrt(dist_x * dist_x + dist_y * dist_y)

                    if distance < self.collision_radius:
                        return True

        return False

    def get_safe_position(self, level, old_x, old_y, new_x, new_y):
        # If no collision, return the new position
        if not self.check_collision(level, new_x, new_y):
            return new_x, new_y

        # Try moving along x-axis only
        if not self.check_collision(level, new_x, old_y):
            return new_x, old_y

        # Try moving along y-axis only
        if not self.check_collision(level, old_x, new_y):
            return old_x, new_y

        # Can't move, return original position
        return old_x, old_y

    def get_position(self):
        return self.x, self.y

    def get_angle(self):
        return self.angle

    def get_direction_vector(self):
        return (math.cos(self.angle), math.sin(self.angle))

    def is_moving(self):
        print(self.moving)
        return self.moving

    def initialize_weapons(self, game):
        """Crée toutes les armes disponibles pour le joueur"""
        from weapons.fists import Fists
        from weapons.pistol import Pistol

        # Ajouter les armes au joueur
        self.weapons.append(Fists(game))
        self.weapons.append(Pistol(game))

        # Définir l'arme active initiale
        if self.weapons:
            self.current_weapon_index = 0
            self.weapons[self.current_weapon_index].is_equipped = True
            self.weapon = self.weapons[self.current_weapon_index]  # Référence à l'arme actuelle

    def switch_weapon(self, direction):
        if not self.weapons:
            return

        # Désactiver l'arme actuelle
        self.weapons[self.current_weapon_index].is_equipped = False

        # Calculer le nouvel index
        self.current_weapon_index = (self.current_weapon_index + direction) % len(self.weapons)

        # Activer la nouvelle arme
        self.weapons[self.current_weapon_index].is_equipped = True

        # Mettre à jour la référence à l'arme actuelle
        self.weapon = self.weapons[self.current_weapon_index]







