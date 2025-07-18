import pygame as pg
import math
from effects.explosion import Explosion
from weapons.projectiles.projectile import Projectile

class BFGProjectile(Projectile):
    def __init__(self, game, x, y, angle, speed, damage, lifetime, splash_radius):
        super().__init__(
            game=game,
            x=x,
            y=y,
            angle=angle,
            speed=speed,
            damage=damage,
            lifetime=lifetime,
            splash_damage=True,
            splash_radius=splash_radius,
            sprite=None  # sera défini par l’animation
        )

        self.frames = [
            pg.image.load("assets/weapons/projectiles/bfg/BFGBEAM1.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/bfg/BFGBEAM2.png").convert_alpha()
        ]
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.1  # 100 ms par frame
        self.sprite = self.frames[0]
        self.scale = 17.0  # Agrandissement du sprite visuel

    def update(self, delta_time):
        # Collision ennemis ou murs
        if self._check_collision():
            self._explode()
            return False

        # Avance le projectile
        self.x += self.dx * delta_time
        self.y += self.dy * delta_time
        self.lifetime -= delta_time

        # Animation du projectile
        self.frame_timer += delta_time
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.sprite = self.frames[self.frame_index]

        # Durée de vie terminée
        if self.lifetime <= 0:
            return False

        return True

    def render(self, screen, raycaster):
        player = self.game.player
        px, py = player.get_position()
        player_angle = player.get_angle()

        dx, dy = self.x - px, self.y - py
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Raycast inline pour bloquer si un mur est entre le joueur et le projectile
        step = 2
        t = 0
        blocked = False
        while t < dist:
            x = px + dx / dist * t
            y = py + dy / dist * t
            if raycaster.level.is_blocked(x, y):
                blocked = True
                break
            t += step

        if blocked:
            return

        # Angle relatif au joueur
        rel_angle = math.atan2(dy, dx) - player_angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(rel_angle) > raycaster.fov / 2:
            return

        # Projection écran
        corrected_dist = dist * math.cos(rel_angle)
        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())
        size = int((1000 / (corrected_dist + 0.0001)) * raycaster.wall_height_scale * self.scale)

        if self.sprite:
            scaled = pg.transform.scale(self.sprite, (size, size))
            screen_y = screen.get_height() // 2 - size // 2
            screen.blit(scaled, (screen_x - size // 2, screen_y))

    def _explode(self):
        frames = [
            pg.image.load("assets/weapons/projectiles/bfg/BFG1.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/bfg/BFG2.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/bfg/BFG3.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/bfg/BFG4.png").convert_alpha(),
        ]

        self.game.effects.append(Explosion(self.x, self.y, frames, duration=0.3))

        # Dégâts directs
        hit_enemy = None
        for enemy in self.game.enemies:
            dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if dist < enemy.size + self.size:
                enemy.take_damage(self.damage)
                hit_enemy = enemy
                break

        for enemy in self.game.enemies:
            if enemy is not hit_enemy and enemy.alive:
                dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
                if dist < self.splash_radius:
                    factor = 1 - (dist / self.splash_radius)
                    splash_damage = self.damage * 0.5 * factor  # Exemple : 50% max
                    enemy.take_damage(splash_damage)

                    # Crée une explosion visuelle à la position de l'ennemi
                    self.game.effects.append(
                        Explosion(enemy.x, enemy.y, frames, duration=0.3)
                    )
