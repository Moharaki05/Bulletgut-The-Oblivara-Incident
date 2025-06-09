import math
import pygame as pg

from utils.assets import load_image
from weapons.projectiles.projectile import Projectile
from effects.explosion import Explosion

class SerpentipedeFireball(Projectile):
    def __init__(self, game, x, y, angle, owner=None):
        self.game = game

        # Sprite de test visible : cercle rouge
        sprite = load_image("assets/weapons/projectiles/fireball.png")

        super().__init__(
            game,
            x, y,
            angle,
            speed=220,
            damage=12,
            lifetime=2.5,
            splash_damage=False,
            splash_radius=0,
            sprite=sprite
        )

        self.owner = owner
        self.explosion_sound = pg.mixer.Sound("assets/sounds/rocketlauncher/rocket_hit.wav")
        self.explosion_sprites = [
            pg.image.load("assets/weapons/projectiles/rocket/expl_01.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_02.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_03.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_04.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_05.png").convert_alpha()
        ]

        self.exploded = False
        self.collision_delay = 0.05
        self.prev_x = self.x
        self.prev_y = self.y

    def update(self, dt):
        if self not in self.game.projectiles:
            return False

        self.prev_x = self.x
        self.prev_y = self.y

        self.x += self.dx * dt
        self.y += self.dy * dt

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.on_impact()
            return False

        if self.collision_delay <= 0:
            if self._check_collision():
                self.on_impact()
                return False
        else:
            self.collision_delay -= dt

        if self._collides_with_entity(self.game.player):
            self.game.player.take_damage(self.damage)
            self.on_impact()
            return False


        return not self.exploded

    def render(self, screen, raycaster):
        if self.exploded:
            return

        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        rel_angle = math.atan2(dy, dx) - self.game.player.angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(rel_angle) > raycaster.fov / 2:
            return

        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())
        corrected_dist = dist * math.cos(rel_angle)

        if 0 <= screen_x < len(raycaster.z_buffer):
            if corrected_dist > raycaster.z_buffer[screen_x] + 5:
                return

        size = int(1.5 * 4000 / (corrected_dist + 0.0001))
        size = min(size, 200)  # Optionnel : éviter les tailles trop grandes

        screen_y = screen.get_height() // 2 - size // 2

        scaled_sprite = pg.transform.scale(self.sprite, (size, size))
        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))

    def on_impact(self):
        if not self.exploded:
            self.exploded = True
            self.explosion_sound.play()
            self.game.effects.append(
                Explosion(self.prev_x, self.prev_y, self.explosion_sprites)
            )

    def _explode(self):
        self.exploded = True

    def _collides_with_entity(self, entity):
        if entity == self.owner:
            return False
        if hasattr(entity, 'position'):
            ex, ey = entity.position
        else:
            ex, ey = entity.x, entity.y
        dx, dy = self.x - ex, self.y - ey
        dist = math.hypot(dx, dy)
        return dist < (getattr(entity, 'size', 20) + self.size)
