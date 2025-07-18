import math
import random
import pygame as pg

from engine import game
from weapons.fists import Fists
from weapons.pistol import Pistol
from weapons.plasma_gun import PlasmaGun
from weapons.rocket_launcher import RocketLauncher
from weapons.shotgun import Shotgun
from weapons.chaingun import Chaingun
from weapons.chainsaw import Chainsaw
from weapons.bfg import BFG
from data.config import TILE_SIZE, PLAYER_SPEED, ROTATE_SPEED, FOV, PLAYER_COLLISION_RADIUS, \
    MOUSE_SENSITIVITY, WEAPON_SLOTS, MOUSE_SENSITIVITY_EXPONENT

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
        self.size = 32

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
        self.keys = set()
        self.rect = pg.Rect(self.x - 10, self.y - 10, 20, 20)

    def handle_inputs(self, keys, dt, mouse_dx=0, level=None, game=None):
        if not self.alive:
            return

        # ⭐ NOUVEAU : Vérifier si l'intermission est active
        if game and hasattr(game, 'show_intermission') and game.show_intermission:
            # Pendant l'intermission, ignorer TOUS les contrôles du joueur
            return

        # ⭐ NOUVEAU : Vérifier si le jeu est en pause
        if game and hasattr(game, 'game_paused') and game.game_paused:
            # Pendant la pause, ignorer TOUS les contrôles du joueur
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

        # NOUVELLE VERSION : Utiliser les méthodes améliorées du level
        if level:
            self.x, self.y = self.get_safe_position(level, original_x, original_y, new_x, new_y)
        else:
            self.x, self.y = new_x, new_y

        # Mouse rotation
        self.handle_mouse_movement(mouse_dx)
        self.angle %= 2 * math.pi
        self.rect.center = (self.x, self.y)

        if hasattr(game, "enemies"):
            self.check_enemy_collisions(game)

    def handle_mouse_movement(self, dx):
        dx = math.copysign(abs(dx) ** MOUSE_SENSITIVITY_EXPONENT, dx)
        self.angle += dx * MOUSE_SENSITIVITY
        self.angle %= 2 * math.pi

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
        """Version qui réduit le glissement contre les murs"""
        # Créer un rectangle de collision centré sur le joueur
        collision_rect = pg.Rect(0, 0, self.collision_radius * 2, self.collision_radius * 2)

        # Tester la nouvelle position
        collision_rect.center = (new_x, new_y)
        if not level.is_rect_blocked(collision_rect):
            return new_x, new_y

        # Calculer les deltas de mouvement
        dx = new_x - old_x
        dy = new_y - old_y

        # Facteur de réduction du glissement (ajustable)
        slide_factor = 0.75  # 75% du mouvement original pour le glissement

        # Tester mouvement horizontal réduit
        if abs(dx) > 0.1:
            reduced_x = old_x + (dx * slide_factor)
            collision_rect.center = (reduced_x, old_y)
            if not level.is_rect_blocked(collision_rect):
                return reduced_x, old_y

        # Tester mouvement vertical réduit
        if abs(dy) > 0.1:
            reduced_y = old_y + (dy * slide_factor)
            collision_rect.center = (old_x, reduced_y)
            if not level.is_rect_blocked(collision_rect):
                return old_x, reduced_y

        # Aucun mouvement possible
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
            if hasattr(game, "reset_player_state"):
                game.reset_player_state()

    def check_enemy_collisions(self, game):
        for enemy in game.enemies:
            if not enemy.alive:
                continue
            if self.rect.colliderect(enemy.rect):
                # Calcul d’un vecteur de séparation
                dx = self.x - enemy.x
                dy = self.y - enemy.y
                distance = math.hypot(dx, dy)
                if distance == 0:
                    continue
                overlap = (self.size + enemy.size) - distance
                push_x = (dx / distance) * overlap * 0.5
                push_y = (dy / distance) * overlap * 0.5

                self.x += push_x
                self.y += push_y
                self.rect.center = (self.x, self.y)