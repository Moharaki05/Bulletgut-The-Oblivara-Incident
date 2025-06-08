import pygame as pg
import math
from weapons.projectiles.projectile import Projectile
from effects.explosion import Explosion

class Plasma(Projectile):
    def __init__(self, game, x, y, angle, speed, damage, lifetime, splash_damage, splash_radius, sprite):
        super().__init__(game, x, y, angle, speed, damage, lifetime, splash_damage, splash_radius, sprite)

    def update(self, delta_time):
        for enemy in self.game.enemies:
            if enemy.alive and self._collides_with_entity(enemy):
                enemy.take_damage(self.damage)
                self._explode()
                return False

        # Vérification de collision
        if self._check_collision():
            self._explode()
            return False

        self.x += self.dx * delta_time
        self.y += self.dy * delta_time
        self.lifetime -= delta_time

        # Expiration du projectile
        if self.lifetime <= 0:
            return False

        return True

    def _explode(self):
        # Charger les frames de l'explosion plasma (une seule fois si possible)
        frames = [
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl1.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl2.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl3.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/plasma/plasma_expl4.png").convert_alpha(),
        ]

        self.game.effects.append(Explosion(self.x, self.y, frames, duration=0.3))

        # Dégâts directs
        for enemy in self.game.enemies:
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < enemy.size + self.size:
                enemy.take_damage(self.damage)
                break

    def render(self, screen, raycaster):
        player = self.game.player
        px, py = player.get_position()
        player_angle = player.get_angle()

        dx, dy = self.x - px, self.y - py
        dist = math.hypot(dx, dy)
        rel_angle = math.atan2(dy, dx) - player_angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(rel_angle) > raycaster.fov / 2:
            return

        corrected_dist = dist * math.cos(rel_angle)
        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())
        size = int((1000 / (corrected_dist + 0.0001)) * raycaster.wall_height_scale)

        if self.sprite:
            scaled = pg.transform.scale(self.sprite, (size, size))
            screen_y = screen.get_height() // 2 - size // 2
            screen.blit(scaled, (screen_x - size // 2, screen_y))

    def _collides_with_entity(self, entity):
        if hasattr(entity, 'position'):
            ex, ey = entity.position
        else:
            ex, ey = entity.x, entity.y
        dx, dy = self.x - ex, self.y - ey
        dist = math.hypot(dx, dy)
        return dist < (getattr(entity, 'size', 20) + getattr(self, 'size', 5))
