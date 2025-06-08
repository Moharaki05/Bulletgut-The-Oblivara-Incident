from abc import ABC
import math
import random
import pygame as pg
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
        end_x = px + dx * self.range
        end_y = py + dy * self.range

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

    def render_detection_line(self, surface):
        """Render the detection line for debugging purposes"""
        if not hasattr(self, 'debug_render') or not self.debug_render:
            return

        player = self.game.player
        px, py = player.get_position()
        angle = player.get_angle()

        # Calculate line direction
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Get actual end point considering walls
        end_x, end_y = self._get_line_end_point(px, py, dx, dy)

        # Convert world coordinates to screen coordinates
        # The render_surface is already offset, so we need to calculate relative to player position
        screen_width = surface.get_width()
        screen_height = surface.get_height()

        # Player should be at center of screen
        player_screen_x = screen_width // 2
        player_screen_y = screen_height // 2

        # Calculate end position relative to player
        world_dx = end_x - px
        world_dy = end_y - py

        end_screen_x = player_screen_x + world_dx
        end_screen_y = player_screen_y + world_dy

        # Only draw if end point is reasonable (within a reasonable distance from center)
        max_screen_distance = max(screen_width, screen_height)
        if abs(end_screen_x - player_screen_x) > max_screen_distance or abs(
                end_screen_y - player_screen_y) > max_screen_distance:
            # Clamp to screen bounds
            line_length = math.hypot(world_dx, world_dy)
            if line_length > 0:
                # Normalize and scale to fit screen
                scale = min(max_screen_distance * 0.8, line_length) / line_length
                end_screen_x = player_screen_x + world_dx * scale
                end_screen_y = player_screen_y + world_dy * scale

        start_screen = (int(player_screen_x), int(player_screen_y))
        end_screen = (int(end_screen_x), int(end_screen_y))

        # Draw the line (red if detecting enemy, green otherwise)
        color = (255, 0, 0) if self.last_detected_enemies else (0, 255, 0)

        # Only draw if both points are within reasonable bounds
        if (0 <= end_screen[0] <= screen_width * 2 and
                0 <= end_screen[1] <= screen_height * 2):
            try:
                pg.draw.line(surface, color, start_screen, end_screen, 2)
            except:
                pass  # Skip if coordinates cause issues

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

    def _line_intersects_enemy(self, line_start_x, line_start_y, line_end_x, line_end_y, enemy):
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

    def _get_enemy_by_id(self, enemy_id, enemies):
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
        angle = player.get_angle()

        print(f"[SHOT] Firing weapon from ({px:.1f}, {py:.1f}) at angle {math.degrees(angle):.1f}°")
        print(f"[WEAPON] Damage per hit: {self.damage}, Pellets: {self.pellets}")

        # Find all alive enemies for debugging
        alive_enemies = [e for e in enemies if e.alive]
        print(f"[DEBUG] {len(alive_enemies)} alive enemies in level")

        # Tire plusieurs pellets (pour fusil à pompe) ou un seul (pour pistolet/mitraillette)
        hits_this_shot = 0
        enemies_hit = set()  # Track unique enemies hit this shot

        for pellet_num in range(self.pellets):
            # Applique une dispersion aléatoire
            shot_angle = angle
            if self.spread > 0:
                shot_angle += random.uniform(-self.spread, self.spread)

            # Direction du tir
            dx = math.cos(shot_angle)
            dy = math.sin(shot_angle)

            # Get line end point considering walls
            end_x, end_y = self._get_line_end_point(px, py, dx, dy)
            print(f"[TRACE] Pellet {pellet_num + 1}: Line from ({px:.1f}, {py:.1f}) to ({end_x:.1f}, {end_y:.1f})")

            # Check for enemy hits along the line
            hit_enemy = None
            closest_distance = float('inf')

            # Check each enemy
            for enemy in enemies:
                if not enemy.alive:
                    continue

                enemy_distance = math.hypot(enemy.x - px, enemy.y - py)
                print(f"[CHECK] Checking enemy at ({enemy.x:.1f}, {enemy.y:.1f}), distance: {enemy_distance:.1f}")

                if self._line_intersects_enemy(px, py, end_x, end_y, enemy):
                    print(f"[INTERSECT] Line intersects with enemy at {enemy_distance:.1f}px")
                    if enemy_distance < closest_distance:
                        closest_distance = enemy_distance
                        hit_enemy = enemy
                else:
                    print(f"[NO_INTERSECT] Line does not intersect enemy")

            # Damage the closest enemy hit
            if hit_enemy:
                hits_this_shot += 1
                enemies_hit.add(id(hit_enemy))
                print(
                    f"[HIT] Pellet {pellet_num + 1} hit {type(hit_enemy).__name__} at {closest_distance:.1f}px distance")

                # Actually deal the damage
                damage_to_deal = self.damage
                print(f"[DAMAGE] Dealing {damage_to_deal} damage to enemy")
                hit_enemy.take_damage(damage_to_deal)

                self._create_hit_effect(hit_enemy.x, hit_enemy.y, is_enemy=True)
            else:
                # Hit wall or nothing
                print(f"[MISS] Pellet {pellet_num + 1} hit wall/nothing at ({end_x:.1f}, {end_y:.1f})")
                self._create_hit_effect(end_x, end_y)

            # Create tracer effect
            self._create_tracer_effect(px, py, end_x, end_y)

        if hits_this_shot > 0:
            print(f"[SHOT RESULT] {hits_this_shot}/{self.pellets} pellets hit {len(enemies_hit)} unique enemies")
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