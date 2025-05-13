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
            print(f"Sprites des poings chargés : {len(self.sprites)} images")
        except Exception as e:
            print(f"ERREUR lors du chargement des sprites des poings : {e}")
            self.sprites = []

    def _fire_effect(self):
        self.is_firing = True

    def _handle_fire(self):
        """Logique spécifique pour la frappe des poings"""
        # Vérifier si un ennemi est à portée (rayon de frappe)
        hit_range = 2.0  # Distance maximale de frappe en unités du jeu

        # Obtenir la position et la direction du joueur
        player_pos = self.game.player.get_position()
        player_dir = self.game.player.get_direction_vector()

        # Calculer le point d'impact potentiel
        target_x = player_pos[0] + player_dir[0] * hit_range
        target_y = player_pos[1] + player_dir[1] * hit_range

        # Vérifier si un ennemi est touché
        # for enemy in self.game.enemies:
        #     distance = ((enemy.position[0] - player_pos[0]) ** 2 +
        #                 (enemy.position[1] - player_pos[1]) ** 2) ** 0.5
        #
        #     if distance <= hit_range:
        #         # Vérifier si l'ennemi est dans le champ de vision
        #         angle_to_enemy = math.atan2(enemy.position[1] - player_pos[1],
        #                                     enemy.position[0] - player_pos[0])
        #         player_angle = math.atan2(player_dir[1], player_dir[0])
        #
        #         # Calculer la différence d'angle (normalisée entre -π et π)
        #         angle_diff = (angle_to_enemy - player_angle + math.pi) % (2 * math.pi) - math.pi
        #
        #         # Si l'ennemi est dans le champ de vision (±30 degrés)
        #         if abs(angle_diff) <= math.radians(30):
        #             # Infliger des dégâts
        #             enemy.take_damage(self.damage)
        #
        #             # Effet visuel ou sonore de l'impact (facultatif)
        #             if hasattr(self, 'hit_sound') and self.hit_sound:
        #                 self.hit_sound.play()

    def _update_weapon_bobbing(self, dt, player):
        super()._update_weapon_bobbing(dt, player)

        # Compensation pour le bobbing vertical
        # Si le bobbing est négatif (vers le haut), compenser dans l'offset
        if self.bobbing_y < 0:
            if not hasattr(self, '_base_position_y'):
                self._base_position_y = self.position_offset[1]

            self.position_offset[1] = self._base_position_y - self.bobbing_y



