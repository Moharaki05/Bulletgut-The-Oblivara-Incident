from weapons.hitscan_weapon import HitscanWeapon
import random
import math
import pygame as pg


class Shotgun(HitscanWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Shotgun"
        self.fire_rate = 1.0
        self.shot_cooldown = 1.0 / self.fire_rate
        self.spread = 0.12
        self.pellets = 8
        self.ammo_type = "shells"
        self.scale_factor = 1.7

        # Désactiver complètement le système d'animation de la classe parente
        self.is_firing = False  # Important: empêche l'animation auto de WeaponBase

        # Notre propre système d'animation
        self.animation_active = False
        self.animation_timer = 0
        self.animation_duration = 1.5  # Durée totale en secondes

        # Charger toutes les images d'animation
        self.load_sprites([
            "assets/weapons/shotgun/shotgun1.png",  # Image de base (repos)
            "assets/weapons/shotgun/shotgun2.png",  # Animation frame 1
            "assets/weapons/shotgun/shotgun3.png",  # Animation frame 2
            "assets/weapons/shotgun/shotgun4.png",  # Animation frame 3
            "assets/weapons/shotgun/shotgun5.png",  # Animation frame 4
            "assets/weapons/shotgun/shotgun6.png",  # Animation frame 5
            "assets/weapons/shotgun/shotgun7.png",  # Animation frame 6
            "assets/weapons/shotgun/shotgun8.png",  # Animation frame 7
            "assets/weapons/shotgun/shotgun9.png",  # Animation frame 8
            "assets/weapons/shotgun/shotgun10.png"  # Animation frame 9
        ])

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/shotgun/shotgun.wav")
        self.reload_sound = pg.mixer.Sound("assets/sounds/shotgun/shotgun_reload.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/shotgun/empty_shotgun_click.wav")

        self.position_offset = [10, 60]

        # Timing pour le son de rechargement
        self.reload_played = False

    def update(self, dt):
        # Vérification du rechargement (si nécessaire)
        current_time = pg.time.get_ticks() / 1000.0
        if self.is_reloading:
            if current_time - self.last_fire_time >= self.reload_time:
                self.is_reloading = False

        # Mise à jour du bobbing de l'arme
        if hasattr(self.game, 'player'):
            player = self.game.player
            if hasattr(player, 'is_moving') and player.is_moving:
                self.bobbing_counter += dt * self.bobbing_speed
                self.bobbing_x = math.sin(self.bobbing_counter) * self.bobbing_amount
                self.bobbing_y = abs(math.sin(self.bobbing_counter * 2)) * self.bobbing_amount
            else:
                self.bobbing_counter = 0
                self.bobbing_x = 0
                self.bobbing_y = 0

        super().update(dt)

        # Notre propre système d'animation
        if self.animation_active:
            self.animation_timer += dt

            # Calculer la progression (0.0 à 1.0)
            progress = min(self.animation_timer / self.animation_duration, 1.0)

            # Déterminer quelle frame afficher (0 à 9)
            frame_count = len(self.sprites) - 1  # Nombre de frames d'animation (hors image de repos)
            frame_index = min(int(progress * frame_count), frame_count)

            # Mettre à jour le sprite actuel
            self.current_sprite_index = frame_index
            self.current_sprite = self.sprites[frame_index]

            # Jouer le son de rechargement au milieu de l'animation
            if not self.reload_played and progress > 0.5:
                self.reload_sound.play()
                self.reload_played = True

            # Fin de l'animation
            if progress >= 1.0:
                self.animation_active = False
                self.animation_timer = 0
                self.current_sprite_index = 0
                self.current_sprite = self.sprites[0]
                self.reload_played = False

                # Si l'animation est terminée
                if self.animation_timer >= self.animation_duration:
                    # Réinitialiser l'état d'animation
                    self.animation_active = False
                    self.animation_timer = 0

                    # Si le shotgun était en train de se recharger, marquer comme rechargé
                    if self.is_reloading:
                        self.is_reloading = False
                        # S'assurer que l'arme est prête à tirer à nouveau
                        self.is_firing = False

    def fire(self):
        # Si l'arme est en train de se recharger ou si l'animation est active, ne pas tirer
        if self.is_reloading or self.animation_active:
            print("Le shotgun est en cours de rechargement, impossible de tirer")
            return

        # Vérifier si on peut tirer (cooldown)
        current_time = pg.time.get_ticks() / 1000.0
        if current_time - self.last_fire_time < self.shot_cooldown:
            return False

        # Vérifier les munitions
        if self.game.player.ammo[self.ammo_type] < 1:
            # Jouer le son "vide"
            self.empty_sound.set_volume(1.0)
            self.empty_sound.play()
            print("Son fusil vide joué - munitions épuisées")
            return False

        # Tout est OK pour tirer
        self._handle_fire()
        self.last_fire_time = current_time
        return True

    def _handle_fire(self):
        if self.is_reloading or self.animation_active:
            return None  # Ne pas tirer pendant le rechargement ou l'animation

        # Décrémenter les munitions
        self.game.player.ammo[self.ammo_type] -= 1

        # Jouer le son de tir
        self.fire_sound.play()

        # Démarrer l'animation
        self.animation_active = True
        self.animation_timer = 0
        self.reload_played = False

        # Définir immédiatement la première frame d'animation
        self.current_sprite_index = 1  # Start with the first animation frame
        self.current_sprite = self.sprites[1]

        # Obtenir la position et la direction du joueur
        player = self.game.player
        start_x, start_y = player.x, player.y
        direction = player.get_direction_vector()

        # Tirer plusieurs plombs avec dispersion
        for _ in range(self.pellets):
            # Calculer un angle aléatoire dans la limite du spread
            angle_offset = random.uniform(-self.spread, self.spread)
            # Appliquer la rotation à la direction
            cos_offset = math.cos(angle_offset)
            sin_offset = math.sin(angle_offset)
            dx, dy = direction
            pellet_direction = (
                dx * cos_offset - dy * sin_offset,
                dx * sin_offset + dy * cos_offset
            )

            # Calcul du point de fin (portée max)
            end_x = start_x + pellet_direction[0] * self.range
            end_y = start_y + pellet_direction[1] * self.range

            # Détection d'ennemis
            for enemy in self.game.level.enemies:
                if enemy.alive and self._line_intersects_enemy(start_x, start_y, end_x, end_y, enemy):
                    print(f"[HIT] Ennemi touché par un plomb : {enemy}")
                    enemy.health -= self.damage
                    if enemy.health <= 0:
                        enemy.die()
                    break  # un seul ennemi touché par plomb

        # TODO: Implémenter le raycast pour détecter les impacts
        print(f"Plomb de fusil tiré depuis ({start_x}, {start_y}) dans la direction {pellet_direction}")
        print(f"Munitions restantes: {self.game.player.ammo[self.ammo_type]}")

        # Recul du joueur
        if hasattr(player, 'apply_recoil'):
            player.apply_recoil(0.15)
