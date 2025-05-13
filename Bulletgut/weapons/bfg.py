from weapons.weapon_base import WeaponBase
import pygame as pg
import math


class BFG(WeaponBase):
    def __init__(self, game):
        super().__init__(game)
        self.name = "BFG 9000"
        self.damage = 200  # Dégâts massifs
        self.fire_rate = 0.2  # Très lente
        self.shot_cooldown = 1.0 / self.fire_rate
        self.ammo_type = "cells"
        self.ammo_per_shot = 40  # Consomme beaucoup de munitions
        self.max_ammo = 200
        self.current_ammo = self.max_ammo

        # Propriétés spécifiques au BFG
        self.charge_time = 2.5  # Temps de charge en secondes
        self.charge_level = 0  # Niveau de charge actuel
        self.is_charging = False
        self.projectile = None
        self.secondary_damage_radius = 400  # Rayon des arcs secondaires

        # Charger les sprites
        self.load_sprites([
            "assets/weapons/bfg/idle.png",
            "assets/weapons/bfg/charge1.png",
            "assets/weapons/bfg/charge2.png",
            "assets/weapons/bfg/charge3.png",
            "assets/weapons/bfg/fire.png"
        ])

        # Sprite du projectile
        self.projectile_sprite = pg.image.load("assets/weapons/bfg/bfg_ball.png").convert_alpha()

        # Sons
        self.charge_sound = pg.mixer.Sound("assets/sounds/bfg_charge.wav")
        self.fire_sound = pg.mixer.Sound("assets/sounds/bfg_fire.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/empty_click.wav")

    def start_firing(self):
        """Commence le processus de charge au lieu de tirer immédiatement"""
        if self.current_ammo >= self.ammo_per_shot and not self.is_cooling_down:
            self.is_charging = True
            self.charge_level = 0
            # Démarrer le son de charge en boucle
            self.charge_sound.play(-1)  # -1 pour boucle infinie
        else:
            self.empty_sound.play()

    def stop_firing(self):
        """Relâcher le tir après la charge"""
        if self.is_charging:
            # Arrêter le son de charge
            self.charge_sound.stop()

            # Tirer si suffisamment chargé
            if self.charge_level > 0.5:  # Au moins 50% chargé
                self._fire_effect()
                self.current_ammo -= self.ammo_per_shot
                self.last_shot_time = pg.time.get_ticks() / 1000.0

            self.is_charging = False
            self.charge_level = 0

    def _fire_effect(self):
        """Effet de tir du BFG - création d'un projectile massif"""
        # Jouer le son de tir
        self.fire_sound.play()

        # Créer le projectile du BFG
        self.create_bfg_projectile()

    def update(self, dt):
        """Mettre à jour l'arme, incluant la gestion de la charge"""
        super().update(dt)

        # Mettre à jour la charge
        if self.is_charging:
            self.charge_level += dt / self.charge_time
            self.charge_level = min(self.charge_level, 1.0)

            # Mettre à jour le sprite en fonction du niveau de charge
            if self.charge_level < 0.33:
                self.current_sprite_index = 1  # charge1
            elif self.charge_level < 0.66:
                self.current_sprite_index = 2  # charge2
            else:
                self.current_sprite_index = 3  # charge3

        # Mettre à jour le projectile du BFG s'il existe
        if self.projectile:
            self.update_bfg_projectile(dt)

    def create_bfg_projectile(self):
        """Crée le projectile principal du BFG"""
        # Position de départ (devant du joueur)
        player = self.game.player
        angle = player.angle
        dist = 30  # Distance devant le joueur

        start_x = player.x + math.cos(angle) * dist
        start_y = player.y + math.sin(angle) * dist

        # Créer le projectile
        self.projectile = {
            'x': start_x,
            'y': start_y,
            'dx': math.cos(angle) * 200,  # Vitesse plus lente que les autres projectiles
            'dy': math.sin(angle) * 200,
            'lifetime': 5.0,  # Durée de vie plus longue
            'damage': self.damage,
            'size': 40,  # Taille large
            'sprite': self.projectile_sprite
        }

    def update_bfg_projectile(self, dt):
        """Met à jour le projectile du BFG et génère les effets secondaires"""
        if not self.projectile:
            return

        # Mettre à jour la position
        self.projectile['x'] += self.projectile['dx'] * dt
        self.projectile['y'] += self.projectile['dy'] * dt
        self.projectile['lifetime'] -= dt

        # Vérifier les collisions avec les murs
        map_x, map_y = int(self.projectile['x']), int(self.projectile['y'])
        if map_x < 0 or map_x >= len(self.game.map[0]) or map_y < 0 or map_y >= len(self.game.map) or \
                self.game.map[map_y][map_x] != 0:
            self.bfg_explosion()
            return

        # Vérifier les collisions avec les ennemis
        for enemy in self.game.enemies:
            dx = enemy.x - self.projectile['x']
            dy = enemy.y - self.projectile['y']
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < enemy.size + self.projectile['size'] / 2:
                self.bfg_explosion()
                return

        # Génération d'arcs secondaires périodiques
        if pg.time.get_ticks() % 500 < 100:  # Tous les 0.5s, pendant 0.1s
            self.generate_secondary_arcs()

        # Fin de vie
        if self.projectile['lifetime'] <= 0:
            self.bfg_explosion()

    def generate_secondary_arcs(self):
        """Génère des arcs d'énergie secondaires qui touchent les ennemis à proximité"""
        if not self.projectile:
            return

        # Trouver tous les ennemis dans le rayon d'effet secondaire
        for enemy in self.game.enemies:
            dx = enemy.x - self.projectile['x']
            dy = enemy.y - self.projectile['y']
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < self.secondary_damage_radius:
                # Appliquer des dégâts
                enemy.take_damage(self.damage // 4)  # Dégâts réduits

                # Effet visuel: tracer de rayon entre le projectile et l'ennemi
                # À implémenter dans le système de rendu

    def bfg_explosion(self):
        """Gère l'explosion finale du projectile BFG"""
        if not self.projectile:
            return

        # Dégâts massifs dans la zone d'explosion
        explosion_radius = 250
        for enemy in self.game.enemies:
            dx = enemy.x - self.projectile['x']
            dy = enemy.y - self.projectile['y']
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < explosion_radius:
                # Dégâts diminuant avec la distance
                damage_factor = 1 - (distance / explosion_radius)
                final_damage = int(self.damage * damage_factor)
                enemy.take_damage(final_damage)

        # Effet d'explosion - à implémenter dans le système de particules
        # self.game.particle_system.add_explosion(self.projectile['x'], self.projectile['y'], explosion_radius)

        # Son d'explosion
        # self.explosion_sound.play()

        # Supprimer le projectile
        self.projectile = None
