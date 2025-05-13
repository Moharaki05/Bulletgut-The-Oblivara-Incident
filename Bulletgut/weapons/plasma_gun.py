from weapons.projectile_weapon import ProjectileWeapon
import pygame as pg


class PlasmaGun(ProjectileWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Plasma Gun"
        self.damage = 20
        self.fire_rate = 8.0  # Cadence de tir élevée
        self.shot_cooldown = 1.0 / self.fire_rate
        self.ammo_type = "cells"
        self.max_ammo = 200
        self.current_ammo = self.max_ammo
        self.projectile_speed = 500  # Projectiles rapides
        self.projectile_lifetime = 2.0
        self.splash_damage = False  # Pas de dégâts de zone

        # Propriétés spécifiques
        self.projectile_color = (0, 200, 255)  # Bleu clair pour le plasma
        self.projectile_size = 10
        self.glow_effect = True

        # Charger les sprites
        self.load_sprites([
            "assets/weapons/plasma/idle.png",
            "assets/weapons/plasma/fire1.png",
            "assets/weapons/plasma/fire2.png",
            "assets/weapons/plasma/reload.png"
        ])

        # Sprite du projectile
        self.projectile_sprite = pg.image.load("assets/weapons/plasma/plasma_bolt.png").convert_alpha()

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/plasma_fire.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/empty_click.wav")

    def create_projectile(self):
        """Crée et retourne un projectile de plasma avec effets spéciaux"""
        projectile = super().create_projectile()

        # Ajouter ici des propriétés spécifiques aux projectiles plasma
        projectile.light_intensity = 1.5  # Intensité lumineuse plus forte
        projectile.glow_radius = 30  # Rayon de l'effet de lueur

        return projectile
