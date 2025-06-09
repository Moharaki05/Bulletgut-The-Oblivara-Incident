import pygame as pg
from data.config import SCREEN_HEIGHT
from weapons.projectile_weapon import ProjectileWeapon
from weapons.projectiles.bfg_projectile import BFGProjectile

class BFG(ProjectileWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "BFG 9000"
        self.damage = 500
        self.fire_rate = 0.1
        self.shot_cooldown = 1 / self.fire_rate
        self.ammo_type = "cells"
        self.ammo_per_shot = 40

        self.projectile_speed = 775
        self.projectile_lifetime = 10.0
        self.splash_damage = True
        self.splash_radius = 300

        # Chargement des sprites d'animation (idle -> charge -> tir)
        self.load_sprites([
            "assets/weapons/bfg/BFG1.png",  # idle
            "assets/weapons/bfg/BFG2.png",  # charge 1
            "assets/weapons/bfg/BFG3.png",  # charge 2
            "assets/weapons/bfg/BFG4.png",  # charge 3
            "assets/weapons/bfg/BFG5.png",  # tir
        ])
        self.sprite_index = 0
        self.current_sprite = self.sprites[0]

        # Affichage HUD
        self.scale_factor = 2.5
        self.position_offset = [0, SCREEN_HEIGHT * 0.05]

        # Animation
        self.is_animating = False
        self.animation_timer = 0.0
        self.animation_frame_duration = 0.2  # 80 ms par frame
        self.has_fired_projectile = False

        # Cooldown
        self.shot_timer = 0.0

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/bfg/bfg_fire.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/bfg/empty_bfg_click.wav")

    def fire(self):
        if not self.is_animating and self.game.player.ammo[self.ammo_type] >= self.ammo_per_shot:
            self.game.player.ammo[self.ammo_type] -= self.ammo_per_shot
            self.is_animating = True
            self.animation_timer = 0.0
            self.sprite_index = 0
            self.has_fired_projectile = False
            self.fire_sound.play()
            print(f"Munitions restantes: {self.game.player.ammo[self.ammo_type]}")
        elif self.game.player.ammo[self.ammo_type] < self.ammo_per_shot:
            self.empty_sound.play()
            print("Munitions épuisées")

    def update(self, dt):
        super().update(dt)

        if self.is_animating:
            self.animation_timer += dt
            frame = int(self.animation_timer / self.animation_frame_duration)

            if frame < len(self.sprites):
                self.sprite_index = frame
                if frame == 4 and not self.has_fired_projectile:
                    self._fire_effect()
                    self.has_fired_projectile = True
            else:
                self.sprite_index = 0
                self.is_animating = False
                self.has_fired_projectile = False
                self.shot_timer = self.shot_cooldown  # ✅ cooldown démarre ici

        else:
            self.shot_timer = max(0, self.shot_timer - dt)

        self.current_sprite = self.sprites[self.sprite_index]

    def _fire_effect(self, player=None):
        if player is None:
            player = self.game.player

        px, py = player.get_position()
        angle = self.game.raycaster.get_center_ray_angle()

        projectile = BFGProjectile(
            game=self.game,
            x=px,
            y=py,
            angle=angle,
            speed=self.projectile_speed,
            damage=self.damage,
            lifetime=self.projectile_lifetime,
            splash_radius=self.splash_radius
        )

        self.game.projectiles.append(projectile)

    def _handle_fire(self):
        self.fire()
