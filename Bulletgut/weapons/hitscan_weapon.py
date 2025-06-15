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

        # Detection state tracking
        self.last_detected_enemies = set()  # Track previously detected enemies
        self.detection_active = False  # Whether line detection is active

    def update_line_detection(self):
        """Update continuous line detection for aiming"""
        player = self.game.player
        enemies = self.game.level.enemies

        # Get player position and angle
        px, py = player.get_position()
        angle = player.get_angle()

        # Calculate line end point
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Find actual end point (considering walls)
        actual_end_x, actual_end_y = self._get_line_end_point(px, py, dx, dy)

        # Check which enemies are hit by the line
        currently_detected = set()
        for enemy in enemies:
            if enemy.alive and self._line_intersects_enemy(px, py, actual_end_x, actual_end_y, enemy):
                currently_detected.add(id(enemy))

        # Print messages for newly detected enemies
        newly_detected = currently_detected - self.last_detected_enemies
        for enemy_id in newly_detected:
            enemy = self._get_enemy_by_id(enemy_id, enemies)
            if enemy:
                print(f"[DETECTION] Enemy detected: {type(enemy).__name__} at ({enemy.x:.1f}, {enemy.y:.1f})")

        # Print messages for enemies no longer detected
        no_longer_detected = self.last_detected_enemies - currently_detected
        for enemy_id in no_longer_detected:
            enemy = self._get_enemy_by_id(enemy_id, enemies)
            if enemy:
                print(f"[DETECTION] Enemy lost: {type(enemy).__name__}")

        # Update tracking
        self.last_detected_enemies = currently_detected

        return currently_detected


    def _get_line_end_point(self, start_x, start_y, dx, dy):
        """Get the actual end point of the line, considering wall collisions"""
        step_size = 4.0  # Small steps for accurate collision detection
        distance = 0
        max_distance = min(self.range, 500)  # Cap the maximum distance for debug rendering

        while distance < max_distance:
            distance += step_size
            x = start_x + dx * distance
            y = start_y + dy * distance

            # Check wall collision
            if self.game.level.is_blocked(x, y):
                # Step back to last valid position
                return start_x + dx * (distance - step_size), start_y + dy * (distance - step_size)

        # No wall hit within range, return max distance point
        return start_x + dx * max_distance, start_y + dy * max_distance

    @staticmethod
    def _line_intersects_enemy(line_start_x, line_start_y, line_end_x, line_end_y, enemy):
        """Check if a line intersects with an enemy's hitbox using closest point method"""
        # Enemy position and size
        ex, ey = enemy.x, enemy.y
        enemy_radius = getattr(enemy, 'size', 32) / 2

        # Vector from line start to line end
        line_dx = line_end_x - line_start_x
        line_dy = line_end_y - line_start_y
        line_length_sq = line_dx * line_dx + line_dy * line_dy

        if line_length_sq == 0:
            # Line has no length, check distance to start point
            dist_sq = (ex - line_start_x) ** 2 + (ey - line_start_y) ** 2
            return dist_sq <= enemy_radius ** 2

        # Vector from line start to enemy
        to_enemy_x = ex - line_start_x
        to_enemy_y = ey - line_start_y

        # Project enemy position onto line
        projection = (to_enemy_x * line_dx + to_enemy_y * line_dy) / line_length_sq

        # Clamp projection to line segment
        projection = max(0, min(1, projection))

        # Find closest point on line to enemy
        closest_x = line_start_x + projection * line_dx
        closest_y = line_start_y + projection * line_dy

        # Check distance from enemy to closest point
        dist_sq = (ex - closest_x) ** 2 + (ey - closest_y) ** 2
        return dist_sq <= enemy_radius ** 2

    @staticmethod
    def _get_enemy_by_id(enemy_id, enemies):
        """Helper to get enemy object by its id"""
        for enemy in enemies:
            if id(enemy) == enemy_id:
                return enemy
        return None

    def _fire_effect(self):
        """Enhanced fire effect that deals damage to enemies when shooting"""
        player = self.game.player
        enemies = self.game.level.enemies

        # Position and angle du joueur
        px, py = player.get_position()
        base_angle = player.get_angle()

        print(f"[SHOT] Firing weapon from ({px:.1f}, {py:.1f}) at angle {math.degrees(base_angle):.1f}°")
        print(f"[WEAPON] Damage per hit: {self.damage}, Pellets: {self.pellets}")

        # Find all alive enemies for debugging
        alive_enemies = [e for e in enemies if e.alive]
        print(f"[DEBUG] {len(alive_enemies)} alive enemies in level")

        # Tire plusieurs pellets (pour fusil à pompe) ou un seul (pour pistolet/mitraillette)
        hits_this_shot = 0
        enemies_hit = set()  # Track unique enemies hit this shot

        for pellet_num in range(self.pellets):
            # Applique une dispersion aléatoire pour CHAQUE pellet
            shot_angle = base_angle
            if self.spread > 0:
                if self.pellets > 1:
                    # For shotguns, use Gaussian distribution for more realistic pellet clustering
                    # Most pellets cluster near center, fewer at the edges
                    spread_factor = random.gauss(0, 0.3)  # Standard deviation of 0.3
                    spread_factor = max(-1.0, min(1.0, spread_factor))  # Clamp to [-1, 1]
                    shot_angle += spread_factor * self.spread
                else:
                    # For single-shot weapons, use uniform distribution
                    shot_angle += random.uniform(-self.spread, self.spread)

            # Direction du tir pour CE pellet spécifique
            dx = math.cos(shot_angle)
            dy = math.sin(shot_angle)

            # Get line end point considering walls for THIS pellet
            end_x, end_y = self._get_line_end_point(px, py, dx, dy)
            spread_degrees = math.degrees(shot_angle - base_angle)
            print(
                f"[TRACE] Pellet {pellet_num + 1}: Line from ({px:.1f}, {py:.1f}) to ({end_x:.1f}, {end_y:.1f}) at angle {math.degrees(shot_angle):.1f}° (spread: {spread_degrees:+.1f}°)")

            # Check for enemy hits along THIS pellet's line
            hit_enemy = None
            closest_distance = float('inf')

            # Check each enemy for THIS specific pellet
            for enemy in enemies:
                if not enemy.alive:
                    continue

                enemy_distance = math.hypot(enemy.x - px, enemy.y - py)

                if self._line_intersects_enemy(px, py, end_x, end_y, enemy):
                    print(f"[INTERSECT] Pellet {pellet_num + 1} intersects with enemy at {enemy_distance:.1f}px")
                    if enemy_distance < closest_distance:
                        closest_distance = enemy_distance
                        hit_enemy = enemy

            # Damage the closest enemy hit by THIS pellet
            if hit_enemy:
                hits_this_shot += 1
                enemies_hit.add(id(hit_enemy))  # Track for statistics only
                print(
                    f"[HIT] Pellet {pellet_num + 1} hit {type(hit_enemy).__name__} at {closest_distance:.1f}px distance")

                # Each pellet deals its own damage - this is what makes shotguns powerful!
                damage_to_deal = self.damage
                print(f"[DAMAGE] Dealing {damage_to_deal} damage to enemy (pellet {pellet_num + 1})")
                hit_enemy.take_damage(damage_to_deal)

                self._create_hit_effect(hit_enemy.x, hit_enemy.y, is_enemy=True)
            else:
                # Hit wall or nothing
                print(f"[MISS] Pellet {pellet_num + 1} hit wall/nothing at ({end_x:.1f}, {end_y:.1f})")
                self._create_hit_effect(end_x, end_y)

            # Create tracer effect for this pellet
            self._create_tracer_effect(px, py, end_x, end_y)

        if hits_this_shot > 0:
            print(f"[SHOT RESULT] {hits_this_shot}/{self.pellets} pellets hit {len(enemies_hit)} unique enemies")
            print(f"[TOTAL DAMAGE] {hits_this_shot * self.damage} total damage dealt this shot")
        else:
            print(f"[SHOT RESULT] No hits - all {self.pellets} pellets missed")

        # Extra debug: Show all enemy states after shot
        print("[POST_SHOT] Enemy health status:")
        for i, enemy in enumerate(enemies):
            if enemy.alive:
                print(f"  Enemy {i}: {type(enemy).__name__} - {enemy.health}/{enemy.max_health} HP")
            else:
                print(f"  Enemy {i}: {type(enemy).__name__} - DEAD")

    def _create_hit_effect(self, x, y, is_enemy=False):
        """Crée un effet visuel d'impact"""
        # You can implement particle systems or other visual effects here
        pass

    def _create_tracer_effect(self, start_x, start_y, end_x, end_y):
        """Crée un effet de traçante pour visualiser le tir"""
        # For machine guns for example
        pass