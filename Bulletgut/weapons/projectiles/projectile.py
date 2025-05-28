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
        self.size = 11

    def update(self, delta_time):
        self.x += self.dx * delta_time
        self.y += self.dy * delta_time

        print(f"Projectile at ({self.x:.2f}, {self.y:.2f}) - is_blocked: {self.game.level.is_blocked(self.x, self.y)}")

        self.lifetime -= delta_time

        if self._check_collision():
            self.on_impact()
            print("💥 Collision détectée !")
            return False

        if self.lifetime <= 0:
            print("⏱ Projectile expiré")
            self.destroy()
            return False

        return True

    def _check_collision(self):
        if self.game.level.is_blocked(self.x, self.y):
            return True

        for door in self.game.level.doors:
            if hasattr(door, 'is_blocking') and door.is_blocking():
                bounds = door.get_door_bounds()
                try:
                    if 'x1' in bounds:
                        door_rect = pg.Rect(bounds['x1'], bounds['y1'], bounds['x2'] - bounds['x1'], bounds['y2'] - bounds['y1'])
                    elif 'left' in bounds:
                        door_rect = pg.Rect(bounds['left'], bounds['top'], bounds['width'], bounds['height'])
                    elif hasattr(bounds, 'colliderect'):
                        door_rect = bounds
                    else:
                        continue
                    projectile_rect = pg.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)
                    if door_rect.colliderect(projectile_rect):
                        return True
                except Exception as e:
                    print(f"Erreur collision porte : {e}")
                    continue

        for entity in self.game.enemies:
            if hasattr(entity, "take_damage"):
                dx, dy = entity.x - self.x, entity.y - self.y
                if math.hypot(dx, dy) <= self.size:
                    return True
        return False

    def on_impact(self):
        hit_enemy = self._get_hit_enemy()
        if hit_enemy:
            hit_enemy.take_damage(self.damage)

        if self.splash_damage:
            for enemy in self.game.enemies:
                if enemy is hit_enemy:
                    continue
                if hasattr(enemy, "take_damage"):
                    dx = enemy.x - self.x
                    dy = enemy.y - self.y
                    distance = math.hypot(dx, dy)
                    if distance <= self.splash_radius and self._has_line_of_sight(enemy):
                        enemy.take_damage(self.damage // 2)

        self._create_explosion_effect()
        self.destroy()

    def _get_hit_enemy(self):
        for enemy in self.game.enemies:
            if hasattr(enemy, "take_damage"):
                dx, dy = enemy.x - self.x, enemy.y - self.y
                if math.hypot(dx, dy) <= self.size:
                    return enemy
        return None

    def _has_line_of_sight(self, target):
        return not self.game.raycaster.raycast_hits_wall(self.x, self.y, target.x, target.y)

    def _explode(self):
        if self.splash_damage:
            for enemy in self.game.enemies:
                ex, ey = enemy.x, enemy.y
                distance = math.hypot(self.x - ex, self.y - ey)
                if distance < self.splash_radius:
                    factor = 1.0 - (distance / self.splash_radius)
                    enemy.take_damage(int(self.damage * factor))
        else:
            for enemy in self.game.enemies:
                ex, ey = enemy.x, enemy.y
                distance = math.hypot(self.x - ex, self.y - ey)
                if distance < enemy.size + self.size:
                    enemy.take_damage(self.damage)
                    break
        self._create_explosion_effect()

    def _create_explosion_effect(self):
        # Implémentez ici votre système de particules ou effet d'explosion
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

        if 0 <= screen_x < len(raycaster.z_buffer):
            if corrected_dist > raycaster.z_buffer[screen_x] + 5:
                return

        size = int(1000 / (corrected_dist + 0.0001))
        scaled_sprite = pg.transform.scale(self.sprite, (size, size))
        screen_y = screen.get_height() // 2 - size // 2
        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))

    def destroy(self):
        if self in self.game.projectiles:
            self.game.projectiles.remove(self)
