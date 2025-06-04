import pygame
import math
import random

from entities.enemy_base import EnemyBase
from entities.pickups.ammo_pickup import AmmoPickup
from utils.assets import load_sound

class Gunner(EnemyBase):
    def __init__(self, x, y, level):
        super().__init__(x, y, level, "assets/enemies/gunner")
        self.max_health = 60
        self.health = self.max_health
        self.damage = 5
        self.speed = 0.7
        self.attack_delay = 1500  # ms entre tirs
        self.sfx_gunshot = load_sound("assets/enemies/gunner/gunshot.wav")  # facultatif

    def attack(self):
        if self.target and self.attack_cooldown <= 0:
            # Hitscan = tir instantané si ligne dégagée
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)

            # Facultatif : vérifier ligne de vue avec raycaster
            self.target.take_damage(self.damage)

            if self.sfx_gunshot:
                self.sfx_gunshot.play()

            self.attack_cooldown = self.attack_delay
            self.state = "attack"

    def drop_loot(self):
        # Lâche des munitions (type à adapter à ton système)
        self.level.pickups.append(
            AmmoPickup(self.x, self.y, ammo_type="bullet", amount=10,
                       sprite_path="assets/pickups/ammo/ammo_bullet.png")
        )
