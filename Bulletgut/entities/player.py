import math
import random
import pygame as pg
from weapons.fists import Fists
from weapons.pistol import Pistol
from weapons.plasma_gun import PlasmaGun
from weapons.rocket_launcher import RocketLauncher
from weapons.shotgun import Shotgun
from weapons.chaingun import Chaingun
from weapons.chainsaw import Chainsaw
from weapons.bfg import BFG
from data.config import TILE_SIZE, PLAYER_SPEED, ROTATE_SPEED, FOV, PLAYER_COLLISION_RADIUS, \
    MOUSE_SENSITIVITY, MOUSE_DEADZONE, WEAPON_SLOTS


class Player:
    def __init__(self, x, y):
        self.was_hit_until = 0
        self.got_weapon_until = 0
        self.weapon = None
        self.x = x
        self.y = y
        self.angle = 0 # Facing right
        self.fov = FOV
        self.move_speed = PLAYER_SPEED
        self.rotate_speed = ROTATE_SPEED
        self.collision_radius = PLAYER_COLLISION_RADIUS
        self.moving = False

        self.health = 100
        self.max_health = 100
        self.abs_max_health = 200

        self.armor = 0
        self.max_armor = 100
        self.abs_max_armor = 200
        self.armor_absorption = 0.33

        self.alive = True

        self.damage_flash_timer = 0

        self.hurt_sound = pg.mixer.Sound("assets/sounds/player/player_injured.wav")
        self.death_sounds = [
            pg.mixer.Sound("assets/sounds/player/player_death1.wav"),
            pg.mixer.Sound("assets/sounds/player/player_death2.wav")
        ]

        self.weapons = [None] * len(WEAPON_SLOTS)
        self.weapon_factory = {
            "fists": Fists,
            "pistol": Pistol,
            "shotgun": Shotgun,
            "chainsaw": Chainsaw,
            "chaingun": Chaingun,
            "plasmagun": PlasmaGun,
            "rocketlauncher": RocketLauncher,
            "bfg": BFG
        }

        self.ammo = {
            "bullets": 10,  # pistolet, chaingun
            "shells": 0,  # shotgun
            "cells": 0,  # plasma gun, BFG
            "rockets": 0  # lance-roquettes
        }
        self.max_ammo = {
            "bullets": 400,
            "shells": 100,
            "cells": 300,
            "rockets": 100
        }
        self.current_weapon_index = 0

    def handle_inputs(self, keys, dt, mouse_dx=0, level=None):
        if not self.alive:
            return

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
        # Ignorer les micro-mouvements
        if abs(dx) < MOUSE_DEADZONE:
            dx = 0

        # Appliquer la rotation
        self.angle += dx * MOUSE_SENSITIVITY
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
        # Créer une liste vide avec 8 slots
        self.weapons = [None] * 8

        # Donner les armes de départ (fists + pistol)
        self.weapons[WEAPON_SLOTS["fists"]] = self.weapon_factory["fists"](game)
        self.weapons[WEAPON_SLOTS["pistol"]] = self.weapon_factory["pistol"](game)

        # Définir l'arme active sur le pistolet
        self.current_weapon_index = WEAPON_SLOTS["pistol"]
        self.weapon = self.weapons[self.current_weapon_index]
        if self.weapon:
            self.weapon.is_equipped = True

    def switch_weapon(self, direction):
        num_slots = len(self.weapons)
        start_index = self.current_weapon_index

        for i in range(1, num_slots):
            new_index = (start_index + direction * i) % num_slots
            if self.weapons[new_index] is not None:
                # Unselect current weapon
                if self.weapon:
                    self.weapon.is_equipped = False
                    if hasattr(self.weapon, "on_deselected"):
                        self.weapon.on_deselected()

                # Switch to new weapon
                self.weapon = self.weapons[new_index]
                self.current_weapon_index = new_index
                self.weapon.is_equipped = True
                return

        print("[WEAPON] No other weapon to switch to.")

    def add_ammo(self, weapon_type, amount):
        if weapon_type in self.ammo:
            self.ammo[weapon_type] += amount
            print(f"+{amount} {weapon_type} ammo (total: {self.ammo[weapon_type]})")
        else:
            print(f"Unknown ammo type: {weapon_type}")

    def has_weapon(self, weapon_name):
        slot = WEAPON_SLOTS.get(weapon_name)
        return slot is not None and self.weapons[slot] is not None

    def take_damage(self, damage):
        if not self.alive:
            return

        self.damage_flash_timer = 0.25

        if self.armor > 0:
            absorbed = min(damage * self.armor_absorption, self.armor)
            self.armor -= absorbed
            damage -= absorbed

        self.health -= damage

        self.was_hit_until = pg.time.get_ticks() + 1000  # visible pendant 1 seconde

        if self.alive:
            self.hurt_sound.play()

        if self.health <= 0:
            self.health = 0
            self.alive = False
            random.choice(self.death_sounds).play()
            print("[PLAYER] You died!")

