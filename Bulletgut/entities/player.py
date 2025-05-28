import math
import pygame as pg
from weapons.fists import Fists
from weapons.pistol import Pistol
from weapons.plasma_gun import PlasmaGun
from weapons.rocket_launcher import RocketLauncher
from weapons.shotgun import Shotgun
from weapons.chaingun import Chaingun
from weapons.chainsaw import Chainsaw
from weapons.bfg import BFG
from data.config import TILE_SIZE, PLAYER_SPEED, ROTATE_SPEED, FOV, PLAYER_COLLISION_RADIUS, SCREEN_WIDTH, SCREEN_HEIGHT

class Player:
    def __init__(self, x, y):
        self.weapon = None
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
            self.moving = True

            # Apply movement with improved collision detection
        if level:
            self.x, self.y = self.get_safe_position(level, original_x, original_y, new_x, new_y)
        else:
            self.x, self.y = new_x, new_y

        # Mouse rotation
        self.handle_mouse_movement(mouse_dx)
        self.angle %= 2 * math.pi # Keep an angle between 0 and 2pi


    def handle_mouse_movement(self, dx):
        # Style Doom/Wolf3D : sensibilité constante
        sensitivity = 0.025

        # Ignorer les micro-mouvements
        deadzone = 0.05
        if abs(dx) < deadzone:
            dx = 0

        # Appliquer la rotation
        self.angle += dx * sensitivity
        self.angle %= 2 * math.pi  # Garde l'angle entre 0 et 2pi

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
        return math.cos(self.angle), math.sin(self.angle)

    def is_moving(self):
        return self.moving

    def initialize_weapons(self, game):
        self.weapons.append(Fists(game))
        self.weapons.append(Chainsaw(game))
        self.weapons.append(Pistol(game))
        self.weapons.append(Shotgun(game))
        self.weapons.append(Chaingun(game))
        self.weapons.append(RocketLauncher(game))
        self.weapons.append(PlasmaGun(game))
        self.weapons.append(BFG(game))

        if hasattr(self.weapon, 'on_selected'):
            self.weapon.on_selected()

        # 🔧 Forcer un update visuel/sound immédiat à 0s (utile pour chainsaw)
        if hasattr(self.weapon, 'update'):
            self.weapon.update(0)

        if self.weapons:
            self.current_weapon_index = 0
            self.weapons[self.current_weapon_index].is_equipped = True
            self.weapon = self.weapons[self.current_weapon_index]

    def switch_weapon(self, direction):
        if not self.weapons:
            return

        # Stopper l'arme actuelle
        if hasattr(self.weapon, 'on_deselected'):
            self.weapon.on_deselected()

        # Passer à la nouvelle arme
        self.weapons[self.current_weapon_index].is_equipped = False
        self.current_weapon_index = (self.current_weapon_index + direction) % len(self.weapons)
        self.weapon = self.weapons[self.current_weapon_index]
        self.weapons[self.current_weapon_index].is_equipped = True

        # Activer la nouvelle arme
        if hasattr(self.weapon, 'on_selected'):
            self.weapon.on_selected()

        # Appliquer un update visuel immédiat (utile pour idle chainsaw)
        if hasattr(self.weapon, 'update'):
            self.weapon.update(0)

    def get_screen_position(self, world_position):
        # Calculer la position relative par rapport au joueur
        # Si world_position est un Vector2
        if hasattr(world_position, 'x') and hasattr(world_position, 'y'):
            dx = world_position.x - self.x
            dy = world_position.y - self.y
        # Si world_position est un tuple ou une liste
        elif isinstance(world_position, (tuple, list)) and len(world_position) >= 2:
            dx = world_position[0] - self.x
            dy = world_position[1] - self.y
        else:
            raise ValueError("world_position doit être un Vector2 ou un tuple/liste (x, y)")

        # Calculer l'angle relatif à la direction du joueur
        angle = math.atan2(dy, dx) - self.angle

        # Calculer la distance
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Direction du regard du joueur
        forward_x = math.cos(self.angle)
        forward_y = math.sin(self.angle)

        # Direction perpendiculaire (droite du joueur)
        right_x = math.sin(self.angle)
        right_y = -math.cos(self.angle)

        # Vecteur de la position du joueur à l'objet
        dir_x = dx
        dir_y = dy

        # Projection sur les axes forward et right
        proj_forward = dir_x * forward_x + dir_y * forward_y
        proj_right = dir_x * right_x + dir_y * right_y

        # Calcul des coordonnées à l'écran
        if proj_forward > 0:  # L'objet est devant le joueur
            screen_x = SCREEN_WIDTH / 2 + (proj_right / proj_forward) * (SCREEN_WIDTH / 2)
            # Plus l'objet est loin, plus il est petit/proche du centre
            scale_factor = 1 / proj_forward
            screen_y = SCREEN_HEIGHT / 2
        else:
            # L'objet est derrière le joueur, ne pas l'afficher
            return (-100, -100)  # Hors écran

        return int(screen_x), int(screen_y)









