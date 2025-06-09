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
        self.swing_sound.stop()
        self.swing_sound.play()

        hit_range = 100.0  # portée de coup en pixels
        angle_range = math.radians(60)  # cône de 60° (±30°)

        player_pos = self.game.player.get_position()
        player_dir = self.game.player.get_direction_vector()
        player_angle = math.atan2(player_dir[1], player_dir[0])

        enemy_hit = False

        for enemy in self.game.enemies:
            if not enemy.alive:
                continue

            # Position de l'ennemi
            ex = getattr(enemy, 'x', getattr(enemy, 'position', (0, 0))[0])
            ey = getattr(enemy, 'y', getattr(enemy, 'position', (0, 0))[1])

            dx = ex - player_pos[0]
            dy = ey - player_pos[1]
            distance = math.hypot(dx, dy)

            if distance <= hit_range:
                angle_to_enemy = math.atan2(dy, dx)
                angle_diff = abs((angle_to_enemy - player_angle + math.pi) % (2 * math.pi) - math.pi)

                if angle_diff <= angle_range:
                    enemy.take_damage(self.damage, splash=False, direct_hit=True)
                    enemy_hit = True

        if enemy_hit:
            self.punch_sound.play()

    def _update_weapon_bobbing(self, dt, player):
        super()._update_weapon_bobbing(dt, player)

        # Compensation pour le bobbing vertical
        # Si le bobbing est négatif (vers le haut), compenser dans l'offset
        if self.bobbing_y < 0:
            if not hasattr(self, '_base_position_y'):
                self._base_position_y = self.position_offset[1]

            self.position_offset[1] = self._base_position_y - self.bobbing_y



