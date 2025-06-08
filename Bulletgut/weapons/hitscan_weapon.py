from abc import ABC
import math
import random
from weapons.weapon_base import WeaponBase

class HitscanWeapon(WeaponBase, ABC):
    def __init__(self, game):
        super().__init__(game)
        self.spread = 0.05  # Dispersion des tirs en radians
        self.range = 1000.0  # Portée maximale
        self.pellets = 1  # Nombre de projectiles par tir (1 pour pistolet, plus pour fusil à pompe)
        self.hit_effect = None  # Effet visuel quand le tir touche quelque chose

    def _fire_effect(self):
        """Effet de tir hitscan (instantané)"""
        player = self.game.player
        enemies = self.game.level.enemies  # Supposons que vous avez une liste d'ennemis dans game
        walls = self.game.level.walls  # Et une liste de murs

        # Position et angle du joueur
        px, py = player.get_position()
        angle = player.get_angle()

        # Tire plusieurs pellets (pour fusil à pompe) ou un seul (pour pistolet/mitraillette)
        for _ in range(self.pellets):
            # Applique une dispersion aléatoire
            shot_angle = angle
            if self.spread > 0:
                shot_angle += random.uniform(-self.spread, self.spread)

            # Direction du tir
            dx = math.cos(shot_angle)
            dy = math.sin(shot_angle)

            # Distance parcourue
            distance = 0
            hit_enemy = None

            # Avance par petits pas jusqu'à toucher quelque chose ou atteindre la portée maximale
            step_size = 1.0

            while distance < self.range:
                distance += step_size
                x = px + dx * distance
                y = py + dy * distance

                # Vérification de collision avec les murs
                if self._check_wall_collision(x, y, walls):
                    # Créer un effet d'impact sur le mur
                    self._create_hit_effect(x, y)
                    break

                # Vérification de collision avec les ennemis
                hit_enemy = self._check_enemy_collision(x, y, enemies)
                if hit_enemy:
                    print(f"[HIT] Ennemi touché à {distance:.1f} px")
                    hit_enemy.take_damage(self.damage)
                    # Effet de sang ou autre
                    self._create_hit_effect(x, y, is_enemy=True)
                    break


            # Créer un effet de tracer temporaire si désiré
            self._create_tracer_effect(px, py, px + dx * distance, py + dy * distance)

    def _check_wall_collision(self, x, y, walls):
        """Vérifie si la position (x, y) est dans un mur"""
        # À adapter selon votre implémentation des murs
        grid_x, grid_y = int(x // 64), int(y // 64)  # Supposant des cases de 64x64
        return (grid_x, grid_y) in walls

    @staticmethod
    def _check_enemy_collision(x, y, enemies):
        for enemy in enemies:
            ex, ey = enemy.x, enemy.y
            distance = math.hypot(x - ex, y - ey)
            print(
                f"[DEBUG COLLISION] Tir à ({x:.1f}, {y:.1f}), Ennemi à ({ex:.1f}, {ey:.1f}) → dist: {distance:.1f}, hitbox: {enemy.size}")
            if distance < max(enemy.size, 32):
                return enemy
        return None

    def _create_hit_effect(self, x, y, is_enemy=False):
        """Crée un effet visuel d'impact"""
        # Vous pouvez implémenter ici un système de particules ou d'autres effets visuels
        pass

    def _create_tracer_effect(self, start_x, start_y, end_x, end_y):
        """Crée un effet de traçante pour visualiser le tir"""
        # Pour une mitrailleuse par exemple
        pass
