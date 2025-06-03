import pygame as pg
import math

from effects.explosion import Explosion
from weapons.projectiles.projectile import Projectile

class Rocket(Projectile):
    def __init__(self, game, x, y, angle, speed, damage, lifetime, splash_damage, splash_radius, front_sprite,
                 back_sprite):
        super().__init__(game, x, y, angle, speed, damage, lifetime, splash_damage, splash_radius, front_sprite)

        self.front_sprite = front_sprite
        self.back_sprite = back_sprite
        self.explosion_sound = pg.mixer.Sound("assets/sounds/rocketlauncher/rocket_hit.wav")
        self.explosion_sprites = [
            pg.image.load("assets/weapons/projectiles/rocket/expl_01.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_02.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_03.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_04.png").convert_alpha(),
            pg.image.load("assets/weapons/projectiles/rocket/expl_05.png").convert_alpha()
        ]

        self.position = pg.Vector2(x, y)

        self.exploded = False

    def update(self, dt):
        if not super().update(dt):
            return False

        self.position.update(self.x, self.y)
        return True  # Toujours en vie

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

        size = int(1000 / (corrected_dist + 0.0001))
        screen_y = screen.get_height() // 2 - size // 2


        sprite = self.front_sprite
        scaled_sprite = pg.transform.scale(sprite, (size, size))
        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))


    def on_impact(self):
        self.explosion_sound.play()
        self.game.effects.append(
            Explosion(self.x, self.y, self.explosion_sprites)
        )
        self._explode()

    def _explode(self):
        if not self.exploded:
            self.exploded = True

            if self.explosion_sound:
                self.explosion_sound.play()

            self._apply_splash_damage()

    def _apply_splash_damage(self):
        player_pos = pg.Vector2(self.game.player.get_position())
        player_dist = (player_pos - self.position).length()
        if player_dist < self.splash_radius:
            damage_factor = 1 - (player_dist / self.splash_radius)
            damage_to_player = self.damage * damage_factor
            self.game.player.take_damage(damage_to_player)
    #
    #     for enemy in self.game.enemies:
    #         if enemy.is_alive:
    #             enemy_dist = (enemy.position - self.position).length()
    #             if enemy_dist < self.splash_radius:
    #                 damage_factor = 1 - (enemy_dist / self.splash_radius)
    #                 damage_to_enemy = self.damage * damage_factor
    #                 enemy.take_damage(damage_to_enemy)

    def _collides_with_entity(self, entity):
        # Récupérer la position de l'entité
        if hasattr(entity, 'position'):
            entity_pos = entity.position
        elif hasattr(entity, 'rect'):
            entity_pos = (entity.rect.centerx, entity.rect.centery)
        elif hasattr(entity, 'x') and hasattr(entity, 'y'):
            entity_pos = (entity.x, entity.y)
        else:
            return False

        # Calculer la distance entre la roquette et l'entité
        dx = self.position[0] - entity_pos[0]
        dy = self.position[1] - entity_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5

        # Définir un rayon de collision (ajuster selon votre jeu)
        rocket_radius = self.size / 2 if hasattr(self, 'size') else 5
        entity_radius = 20  # Ajuster selon la taille de vos entités

        return distance < (rocket_radius + entity_radius)

    def _collides_with_door(self, door):
        # Créer un rectangle pour la porte
        if hasattr(door, 'rect'):
            door_rect = door.rect
        else:
            door_rect = pg.Rect(door.x, door.y, door.width, door.height)

        # Créer un rectangle pour la roquette
        rocket_radius = self.size / 2 if hasattr(self, 'size') else 5
        rocket_rect = pg.Rect(
            self.position[0] - rocket_radius,
            self.position[1] - rocket_radius,
            rocket_radius * 2,
            rocket_radius * 2
        )

        return door_rect.colliderect(rocket_rect)
