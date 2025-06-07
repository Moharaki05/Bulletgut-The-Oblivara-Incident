import math

import pygame as pg
from weapons.melee_weapon import MeleeWeapon
import os

class Fists(MeleeWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Fists"
        self.damage = 5
        self.fire_rate = 2.0  # Coups par seconde
        self.sprite_offsets = []

        # Par défaut, initialiser avec des offsets standard
        for i in range(len(self.sprites)):
            if i == 0:
                # Première image (repos)
                self.sprite_offsets.append([0, 170])
            else:
                # Images d'animation
                self.sprite_offsets.append([0, 100])

        # Position initiale
            if self.sprite_offsets:  # Vérifier que la liste n'est pas vide
                self.position_offset = self.sprite_offsets[0].copy()
            else:
                # Valeur par défaut si aucun sprite n'est chargé
                self.position_offset = [0, 170]

        self.scale_factor = 2.5

        # Chargement des sprites
        self.load_sprites()

        # Chargement des sons
        self.swing_sound = pg.mixer.Sound("assets/sounds/fists/fist_swing.wav")
        self.punch_sound = pg.mixer.Sound("assets/sounds/fists/punch.wav")

        # Initialiser le sprite actif
        self.current_sprite_index = 0
        self.current_sprite = self.sprites[0] if self.sprites else None

    def load_sprites(self):
        # Chemin vers les sprites
        base_path = "assets/weapons/fists"

        # Vérifier si le dossier existe
        if not os.path.exists(base_path):
            print(f"ERREUR: Le dossier {base_path} n'existe pas!")
            return

        # Charger les sprites
        try:
            self.sprites = [
                pg.image.load(f"{base_path}/punch_idle.png").convert_alpha(),
                pg.image.load(f"{base_path}/punch1.png").convert_alpha(),
                pg.image.load(f"{base_path}/punch2.png").convert_alpha(),
                pg.image.load(f"{base_path}/punch3.png").convert_alpha()
            ]
        except Exception as e:
            print(f"ERREUR lors du chargement des sprites des poings : {e}")
            self.sprites = []

    def _fire_effect(self):
        self.is_firing = True

    def _handle_fire(self):
        if hasattr(self, 'swing_sound') and self.swing_sound:
            self.swing_sound.stop()
            self.swing_sound.play()

        hit_range = 2.0  # Distance maximale de frappe en unités du jeu

        # Obtenir la position et la direction du joueur
        player_pos = self.game.player.get_position()
        player_dir = self.game.player.get_direction_vector()

        # Flag pour détecter un impact
        enemy_hit = False

        # Vérifier si un ennemi est touché
        for enemy in self.game.enemies:
            distance = ((enemy.position[0] - player_pos[0]) ** 2 +
                        (enemy.position[1] - player_pos[1]) ** 2) ** 0.5

            if distance <= hit_range:
                # Vérifier si l'ennemi est dans le champ de vision (±30°)
                angle_to_enemy = math.atan2(enemy.position[1] - player_pos[1],
                                            enemy.position[0] - player_pos[0])
                player_angle = math.atan2(player_dir[1], player_dir[0])
                angle_diff = (angle_to_enemy - player_angle + math.pi) % (2 * math.pi) - math.pi

                if abs(angle_diff) <= math.radians(30):
                    enemy.take_damage(self.damage)
                    enemy_hit = True

        # Jouer le son d'impact uniquement si un ennemi a été touché
        if enemy_hit and hasattr(self, 'punch_sound') and self.punch_sound:
            self.punch_sound.play()

    def _update_weapon_bobbing(self, dt, player):
        super()._update_weapon_bobbing(dt, player)

        # Compensation pour le bobbing vertical
        # Si le bobbing est négatif (vers le haut), compenser dans l'offset
        if self.bobbing_y < 0:
            if not hasattr(self, '_base_position_y'):
                self._base_position_y = self.position_offset[1]

            self.position_offset[1] = self._base_position_y - self.bobbing_y



