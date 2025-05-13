# projectile_weapon.py
import pygame as pg
import math
from weapon_base import WeaponBase


class ProjectileWeapon(WeaponBase):
    def __init__(self, game):
        super().__init__(game)
        self.projectile_speed = 200  # Unités par seconde
        self.projectile_lifetime = 5.0  # Secondes avant disparition
        self.splash_damage = False
        self.splash_radius = 0
        self.projectile_sprite = None

    def _fire_effect(self):
        """Tire un projectile physique"""
        player = self.game.player

        # Position et angle du joueur
        px, py = player.get_position()
        angle = player.get_angle()

        # Crée un nouveau projectile
        projectile = Projectile(
            self.game,
            px, py,
            angle,
            self.projectile_speed,
            self.damage,
            self.projectile_lifetime,
            self.splash_damage,
            self.splash_radius,
            self.projectile_sprite
        )

        # Ajoute à la liste des projectiles actifs
        self.game.projectiles.append(projectile)


class Projectile:
    def __init__(self, game, x, y, angle, speed, damage, lifetime, splash_damage, splash_radius, sprite):
        self.game = game
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.splash_damage = splash_damage
        self.splash_radius = splash_radius
        self.sprite = sprite
        self.creation_time = pg.time.get_ticks() / 1000
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.size = 8  # Taille de collision du projectile

    def update(self, dt):
        """Met à jour la position du projectile"""
        current_time = pg.time.get_ticks() / 1000

        # Vérifie si le projectile a expiré
        if current_time - self.creation_time > self.lifetime:
            return False  # Le projectile doit être supprimé

        # Déplace le projectile
        self.x += self.dx * dt
        self.y += self.dy * dt

        # Vérifie les collisions
        if self._check_collision():
            return False  # Le projectile a heurté quelque chose

        return True  # Le projectile reste actif

    def _check_collision(self):
        """Vérifie si le projectile a touché quelque chose"""
        # Collision avec les murs
        walls = self.game.level.walls
        grid_x, grid_y = int(self.x // 64), int(self.y // 64)

        if (grid_x, grid_y) in walls:
            self._explode()
            return True

        # Collision avec les ennemis
        for enemy in self.game.enemies:
            ex, ey = enemy.x, enemy.y
            distance = math.hypot(self.x - ex, self.y - ey)

            if distance < enemy.size + self.size:
                self._explode()
                return True

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
        """Affiche le projectile à l'écran"""
        if not self.sprite:
            return

        # Convertir les coordonnées du monde en coordonnées d'écran
        player = self.game.player
        px, py = player.get_position()
        player_angle = player.get_angle()

        # Calcul de la position relative au joueur
        dx, dy = self.x - px, self.y - py

        # Distance et angle relatif au joueur
        dist = math.hypot(dx, dy)
        rel_angle = math.atan2(dy, dx) - player_angle

        # Normaliser l'angle
        rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi

        # Vérifier si le projectile est dans le champ de vision
        if abs(rel_angle) > raycaster.fov / 2:
            return

        # Projection à l'écran
        screen_x = int((0.5 + rel_angle / raycaster.fov) * screen.get_width())
        size = int((1000 / (dist + 0.0001)) * raycaster.wall_height_scale)

        # Redimensionner et dessiner le sprite
        scaled_sprite = pg.transform.scale(self.sprite, (size, size))
        screen_y = screen.get_height() // 2 - size // 2

        screen.blit(scaled_sprite, (screen_x - size // 2, screen_y))
