import pygame as pg
import math

from data.config import SCREEN_HEIGHT
from weapons.projectile_weapon import ProjectileWeapon
from weapons.projectiles.plasma import Plasma # à créer

class PlasmaGun(ProjectileWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Plasma Gun"
        self.damage = 25
        self.fire_rate = 10.0
        self.shot_cooldown = 1.0 / self.fire_rate
        self.projectile_speed = 650
        self.projectile_lifetime = 3.0
        self.splash_damage = False
        self.splash_radius = 0
        self.ammo_type = "cells"
        self.scale_factor = 2.25
        self.projectile_sprite = pg.image.load("assets/weapons/projectiles/plasma/plasma.png").convert_alpha()
        self.position_offset = [0, SCREEN_HEIGHT * 0.05]  # 5% du bas

        # Animation
        self.load_sprites([
            "assets/weapons/plasmagun/PlasmaGun1.png",
            "assets/weapons/plasmagun/PlasmaGun2.png",
            "assets/weapons/plasmagun/PlasmaGun3.png",
        ])
        self.current_sprite_index = 0
        self.current_sprite = self.sprites[0]
        self.animation_timer = 0
        self.animation_speed = 0.05
        self.is_firing = False
        self.trigger_held = False
        self.fire_cooldown = 0

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/plasmagun/plasmagun.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/plasmagun/empty_plasmagun_click.wav")

    def update(self, dt):
        super().update(dt)

        if self.trigger_held:
            if self.fire_cooldown <= 0 < self.game.player.ammo[self.ammo_type]:
                self._fire_effect()
                self.fire_cooldown = self.shot_cooldown
                print(f"Munitions restantes: {self.game.player.ammo[self.ammo_type]}")
            self.fire_cooldown = max(0, self.fire_cooldown - dt)

            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_sprite_index = (self.current_sprite_index + 1) % len(self.sprites)
                self.current_sprite = self.sprites[self.current_sprite_index]
        else:
            self.current_sprite_index = 0
            self.current_sprite = self.sprites[0]


    def fire(self):
        self.pull_trigger()

    def pull_trigger(self):
        if self.game.player.ammo[self.ammo_type] <= 0:
            self.empty_sound.play()
            return
        self.trigger_held = True
        self.is_firing = True

    def release_trigger(self):
        self.trigger_held = False
        self.is_firing = False
        self.animation_timer = 0
        self.current_sprite_index = 0
        self.current_sprite = self.sprites[0]

    def _fire_effect(self, player=None):
        if player is None:
            player = self.game.player

        px, py = player.get_position()
        angle = self.game.raycaster.get_center_ray_angle()

        # Décalage pour ne pas spawn dans le joueur
        offset = 0.5
        start_x = px + math.cos(angle) * offset
        start_y = py + math.sin(angle) * offset

        projectile = Plasma(
            self.game,
            start_x, start_y,
            angle,
            self.projectile_speed,
            self.damage,
            self.projectile_lifetime,
            splash_damage=False,
            splash_radius=0,
            sprite=self.projectile_sprite
        )

        self.game.projectiles.append(projectile)
        self.fire_sound.play()
        self.game.player.ammo[self.ammo_type] -= 1

    def _handle_fire(self):
        # Appelé par fire(), vérifie si tir possible
        current_time = pg.time.get_ticks() / 1000
        if self.game.player.ammo[self.ammo_type] <= 0 or (current_time - self.last_fire_time < self.shot_cooldown):
            return False

        self._fire_effect()
        self.last_fire_time = current_time
        self.game.player.ammo[self.ammo_type] -= 1
        return True
