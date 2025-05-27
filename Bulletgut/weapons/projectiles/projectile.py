import pygame as pg
import math
from data.config import TILE_SIZE

class Projectile:
    def __init__(self, game, x, y, angle, speed, damage, lifetime, splash_damage, splash_radius, sprite):
        self.game = game
        self.x = x
        self.y = y
        self.angle = angle
        self.direction_x = math.cos(self.angle)
        self.direction_y = math.sin(self.angle)
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.splash_damage = splash_damage
        self.splash_radius = splash_radius
        self.sprite = sprite
        self.creation_time = pg.time.get_ticks() / 1000
        self.dx = self.direction_x * self.speed
        self.dy = self.direction_y * self.speed
        self.size = 11  # Taille de collision du projectile

    def update(self, delta_time):
        # Calculer le déplacement
        movement_x = self.dx * delta_time
        movement_y = self.dy * delta_time

        self.x += movement_x
        self.y += movement_y

        # Log pour débogage
        print(f"Projectile at ({self.x:.2f}, {self.y:.2f}) - is_blocked: {self.game.level.is_blocked(self.x, self.y)}")

        # Temps de vie
        self.lifetime -= delta_time

        # Si collision détectée → suppression
        if self._check_collision():
            self.on_impact()
            print("💥 Collision détectée !")
            return False

        # Si temps écoulé → suppression
        if self.lifetime <= 0:
            print("⏱ Projectile expiré")
            return False

        return True  # Encore actif

    def _check_collision(self):
        if self.game.level.is_blocked(self.x, self.y):
            return True

        # Vérifier collision avec les portes fermées
        for door in self.game.level.doors:
            # Vérifier si la porte bloque
            if hasattr(door, 'is_blocking') and door.is_blocking():
                # Obtenir les limites de la porte
                bounds = door.get_door_bounds()

                if bounds:
                    # Créer un rectangle à partir des limites retournées
                    # Si bounds est un dictionnaire, accédons aux clés appropriées
                    try:
                        # Version dictionnaire avec clés 'x1', 'y1', 'x2', 'y2'
                        if 'x1' in bounds and 'y1' in bounds and 'x2' in bounds and 'y2' in bounds:
                            door_rect = pg.Rect(bounds['x1'], bounds['y1'],
                                                bounds['x2'] - bounds['x1'],
                                                bounds['y2'] - bounds['y1'])
                        # Version dictionnaire avec clés 'left', 'top', 'width', 'height'
                        elif 'left' in bounds and 'top' in bounds and 'width' in bounds and 'height' in bounds:
                            door_rect = pg.Rect(bounds['left'], bounds['top'],
                                                bounds['width'], bounds['height'])
                        # Version où bounds est le rectangle directement
                        elif hasattr(bounds, 'colliderect'):
                            door_rect = bounds
                        else:
                            # Format inconnu, passons à la porte suivante
                            continue

                        # Créer un rectangle pour le projectile
                        projectile_rect = pg.Rect(self.x - self.size / 2, self.y - self.size / 2,
                                                  self.size, self.size)

                        # Vérifier la collision
                        if door_rect.colliderect(projectile_rect):
                            return True
                    except (TypeError, KeyError) as e:
                        # Si une erreur se produit, passons simplement à la porte suivante
                        print(f"Erreur lors de la vérification de collision avec une porte: {e}")
                        continue

        return False

    def _explode(self):
        """Gère l'explosion du projectile"""
        if self.splash_damage:
            # Dégâts de zone
            for enemy in self.game.enemies:
                ex, ey = enemy.x, enemy.y
                distance = math.hypot(self.x - ex, self.y - ey)

                if distance < self.splash_radius:
                    # Dégâts inversement proportionnels à la distance
                    damage_factor = 1.0 - (distance / self.splash_radius)
                    enemy.take_damage(int(self.damage * damage_factor))
        else:
            # Dégâts directs seulement à la cible touchée
            for enemy in self.game.enemies:
                ex, ey = enemy.x, enemy.y
                distance = math.hypot(self.x - ex, self.y - ey)

                if distance < enemy.size + self.size:
                    enemy.take_damage(self.damage)
                    break

        # Créer un effet d'explosion
        self._create_explosion_effect()

    def _create_explosion_effect(self):
        """Crée un effet visuel d'explosion"""
        # Implémentez ici votre système de particules ou d'animations d'explosion
        pass

    def render(self, screen, raycaster):
        if not self.sprite:
            return

        player = self.game.player
        px, py = player.get_position()
        player_angle = player.get_angle()

        dx, dy = self.x - px, self.y - py
        dist = math.hypot(dx, dy)
        rel_angle = math.atan2(dy, dx) - player_angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        corrected_dist = dist * math.cos(rel_angle)
        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())


        if abs(rel_angle) > raycaster.fov / 2:
            return

        # NE PAS RENDRE si derrière un mur
        if 0 <= screen_x < len(raycaster.z_buffer):
            if corrected_dist > raycaster.z_buffer[screen_x] + 5:
                return

        size = int(1000 / (corrected_dist + 0.0001))
        scaled_sprite = pg.transform.scale(self.sprite, (size, size))
        screen_y = screen.get_height() // 2 - size // 2

        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))

    def on_impact(self):
        pass