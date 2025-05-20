import pygame as pg
import math
import time
from abc import ABC, abstractmethod

class WeaponBase(ABC):
    def __init__(self, game):
        self.game = game
        self.name = "Base weapon"
        self.damage = 10
        self.fire_rate = 1.0  # Tirs par seconde
        self.ammo_type = "default"
        self.ammo_per_shot = 1
        self.reload_time = 2.0  # Secondes
        self.max_ammo = 100
        self.current_ammo = self.max_ammo
        self.is_reloading = False
        self.last_fire_time = 0
        self.shot_cooldown = 1.0 / self.fire_rate

        # Animation
        self.sprites = []
        self.sprite_offsets = [] if not hasattr(self, 'sprite_offsets') \
            else self.sprite_offsets
        self.current_sprite_index = 0
        self.current_sprite = None
        self.animation_speed = 0.1
        self.animation_elapsed = 0
        self.last_animation_time = 0
        self.is_firing = False
        self.bobbing_x = 0
        self.bobbing_y = 0
        self.bobbing_amount = 10
        self.bobbing_speed = 0.2
        self.bobbing_counter = 0
        self.position_offset = [0, 0] if not hasattr(self, 'position_offset') \
            else self.position_offset
        self.scale_factor = 1.0

        # Son
        self.fire_sound = None
        self.reload_sound = None
        self.empty_sound = None
        self.swing_sound = None
        self.punch_sound = None

        # État
        self.is_equipped = False

    def load_sprites(self, sprite_paths):
        """Charge les sprites pour l'arme"""
        self.sprites = [pg.image.load(path).convert_alpha() for path in sprite_paths]

    def update(self, dt):
        """Met à jour l'état de l'arme"""
        # Mettre à jour le temps écoulé depuis le dernier tir
        current_time = pg.time.get_ticks() / 1000.0
        time_since_last_fire = current_time - self.last_fire_time

        # Vérifier si le temps de rechargement est écoulé
        if self.is_reloading:
            if time_since_last_fire >= self.reload_time:
                self.is_reloading = False
                self.current_ammo = self.max_ammo

        # Mettre à jour l'animation
        self._update_animation(dt)

        # Mettre à jour le bobbing
        self._update_weapon_bobbing(dt, self.game.player)

    def _update_animation(self, dt=None):
        """Met à jour l'animation de l'arme avec plusieurs frames"""
        if not self.sprites:
            return

        if not hasattr(self, 'animation_elapsed'):
            self.animation_elapsed = 0

        if self.is_firing:
            # Utiliser dt si fourni, sinon calculer le temps écoulé
            if dt is not None:
                # Accumuler delta time au lieu d'utiliser time.time()
                self.animation_elapsed += dt
            else:
                current_time = time.time()
                self.animation_elapsed = current_time - self.last_fire_time

            animation_duration = 0.5  # Durée totale de l'animation

            # Calculer l'index du sprite en fonction du temps écoulé
            if len(self.sprites) > 1:
                animation_frames = len(self.sprites) - 1

                animation_progress = self.animation_elapsed / animation_duration
                if animation_progress >= 1.0:
                    self.current_sprite_index = 0
                    self.is_firing = False
                    self.animation_elapsed = 0  # Réinitialiser le compteur
                else:
                    # Déterminer quelle frame afficher (pré-calculer ceci une fois)
                    frame_index = int(animation_progress * animation_frames)
                    self.current_sprite_index = min(frame_index + 1, animation_frames)

                # Utiliser directement l'offset sans vérifier hasattr à chaque frame
                if self.sprite_offsets and self.current_sprite_index < len(self.sprite_offsets):
                    # Éviter .copy() si possible en assignant directement les valeurs
                    self.position_offset[0] = self.sprite_offsets[self.current_sprite_index][0]
                    self.position_offset[1] = self.sprite_offsets[self.current_sprite_index][1]
        else:
            # En état de repos, utiliser la première image
            self.current_sprite_index = 0

            # Rétablir l'offset de l'image de repos (sans hasattr et sans copy)
            if self.sprite_offsets:
                self.position_offset[0] = self.sprite_offsets[0][0]
                self.position_offset[1] = self.sprite_offsets[0][1]

        if self.is_firing:
            current_time = time.time()
            elapsed_time = current_time - self.last_fire_time
            animation_duration = 0.5  # Durée totale de l'animation

            # Calculer l'index du sprite en fonction du temps écoulé
            if len(self.sprites) > 1:
                animation_frames = len(self.sprites) - 1

                animation_progress = elapsed_time / animation_duration
                if animation_progress >= 1.0:
                    self.current_sprite_index = 0
                    self.is_firing = False
                else:
                    # Déterminer quelle frame afficher
                    frame_index = int(animation_progress * animation_frames)
                    self.current_sprite_index = min(frame_index + 1, animation_frames)

                # Mettre à jour l'offset selon l'image actuelle
                if hasattr(self, 'sprite_offsets') and len(self.sprite_offsets) > self.current_sprite_index:
                    self.position_offset = self.sprite_offsets[self.current_sprite_index].copy()
        else:
            # En état de repos, utiliser la première image
            self.current_sprite_index = 0

            # Rétablir l'offset de l'image de repos
            if hasattr(self, 'sprite_offsets') and len(self.sprite_offsets) > 0:
                self.position_offset = self.sprite_offsets[0].copy()

    def _update_weapon_bobbing(self, dt, player):
        """Met à jour l'effet de balancement de l'arme en fonction du mouvement du joueur"""
        # Constantes pour le balancement
        bob_amount = 10  # Amplitude du balancement
        bob_speed = 4  # Vitesse du balancement

        # Vérifier si le joueur est en mouvement
        if player.is_moving():
            # Incrémenter le compteur de balancement
            self.bobbing_counter += dt * bob_speed

            # Calculer l'effet de balancement
            self.bobbing_x = math.sin(self.bobbing_counter) * bob_amount
            self.bobbing_y = math.cos(self.bobbing_counter * 2) * bob_amount
        else:
            # Réinitialiser progressivement le balancement quand le joueur est immobile
            self.bobbing_counter = 0
            self.bobbing_x = 0
            self.bobbing_y = 0

    def render(self, surface):
        if not self.is_equipped or not self.sprites:
            return

        # Obtenir l'image actuelle
        current_sprite = self.sprites[self.current_sprite_index]

        # Appliquer l'échelle si nécessaire
        if hasattr(self, 'scale_factor') and self.scale_factor != 1.0:
            orig_width = current_sprite.get_width()
            orig_height = current_sprite.get_height()
            new_width = int(orig_width * self.scale_factor)
            new_height = int(orig_height * self.scale_factor)
            current_sprite = pg.transform.scale(current_sprite, (new_width, new_height))

        # Centrer horizontalement en tenant compte de la largeur du sprite
        pos_x = (surface.get_width() - current_sprite.get_width()) // 2 + self.position_offset[0] + self.bobbing_x

        # Position verticale
        pos_y = surface.get_height() - current_sprite.get_height() + self.position_offset[1] + self.bobbing_y

        # Dessiner l'arme
        surface.blit(current_sprite, (pos_x, pos_y))

    def fire(self):
        """Déclenche le tir de l'arme si possible"""
        current_time = time.time()

        # Ne pas tirer si l'arme est déjà en train de tirer ou si le délai n'est pas écoulé
        if self.is_firing:
            return False

        # Vérifier le cooldown
        if current_time - self.last_fire_time >= 1.0 / self.fire_rate:
            self.is_firing = True
            self.last_fire_time = current_time

            # Jouer le son de tir
            if hasattr(self, 'fire_sound') and self.fire_sound:
                self.fire_sound.play()

            # Animation de tir - mettre à jour le sprite
            self.current_sprite_index = 1  # Premier sprite d'animation de tir

            # Logique spécifique du tir
            self._handle_fire()

            return True
        return False

    def release_trigger(self):
        pass

    def reload(self):
        """Recharge l'arme"""
        if self.is_reloading or self.current_ammo == self.max_ammo:
            return False

        self.is_reloading = True
        self.last_fire_time = time.time()

        if self.reload_sound:
            self.reload_sound.play()

        return True

    @abstractmethod
    def _fire_effect(self):
        """Effet spécifique lors du tir (hitscan, projectile, etc.)"""
        pass

    @abstractmethod
    def _handle_fire(self):
        pass