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
        self.hit_enemy = None  # Pour tracker l'ennemi touché directement

    def update(self, dt):
        if not super().update(dt):
            return False

        self.position.update(self.x, self.y)

        # Collision avec les ennemis
        for enemy in self.game.enemies:
            if enemy.alive and self._collides_with_entity(enemy):
                self.hit_enemy = enemy  # Stocker l'ennemi touché directement
                self.on_impact()
                return False

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
        """Appelé quand la roquette entre en collision"""
        if self.exploded:
            return

        # Appliquer les dégâts directs à l'ennemi touché
        if self.hit_enemy and self.hit_enemy.alive:
            print(f"🎯 Dégâts directs à {type(self.hit_enemy).__name__}: {self.damage}")
            # Forcer les dégâts directs en passant par une méthode spéciale
            self._apply_direct_damage(self.hit_enemy, self.damage)

        # Jouer le son et créer l'explosion visuelle
        self.explosion_sound.play()
        self.game.effects.append(
            Explosion(self.x, self.y, self.explosion_sprites)
        )

        # Appliquer l'explosion (splash damage)
        self._explode()

    def _explode(self):
        """Gère l'explosion et les dégâts de zone"""
        if not self.exploded:
            self.exploded = True
            print(f"💥 Explosion à ({self.x:.1f}, {self.y:.1f})")
            self._apply_splash_damage()
            # Détruire le projectile
            self.destroy()

    def _apply_splash_damage(self):
        """Applique les dégâts de zone à toutes les entités dans le rayon"""
        # Dégâts au joueur
        player_pos = pg.Vector2(self.game.player.get_position())
        player_dist = (player_pos - self.position).length()
        if player_dist < self.splash_radius:
            damage_factor = 1 - (player_dist / self.splash_radius)
            damage_to_player = int(self.damage * damage_factor)
            print(f"💥 Splash damage au joueur: {damage_to_player} (distance: {player_dist:.1f})")
            # Utiliser la méthode normale pour le joueur car il n'a pas les mêmes problèmes d'état
            self.game.player.take_damage(damage_to_player)

        # Dégâts aux ennemis
        for enemy in self.game.enemies:
            if enemy.alive:
                # Ne pas appliquer de splash damage à l'ennemi déjà touché directement
                if enemy == self.hit_enemy:
                    print(f"⚠️ Ennemi {type(enemy).__name__} déjà touché directement, skip splash")
                    continue

                # Récupérer la position de l'ennemi de manière cohérente
                if hasattr(enemy, 'x') and hasattr(enemy, 'y'):
                    enemy_pos = pg.Vector2(enemy.x, enemy.y)
                elif hasattr(enemy, 'rect'):
                    enemy_pos = pg.Vector2(enemy.rect.centerx, enemy.rect.centery)
                elif hasattr(enemy, 'position'):
                    if isinstance(enemy.position, pg.Vector2):
                        enemy_pos = enemy.position
                    else:
                        enemy_pos = pg.Vector2(enemy.position[0], enemy.position[1])
                else:
                    print(f"⚠️ Impossible de récupérer la position de {type(enemy).__name__}")
                    continue

                enemy_dist = (enemy_pos - self.position).length()
                if enemy_dist < self.splash_radius:
                    damage_factor = 1 - (enemy_dist / self.splash_radius)
                    damage_to_enemy = int(self.damage * damage_factor)
                    print(f"💥 Splash damage à {type(enemy).__name__}: {damage_to_enemy} (distance: {enemy_dist:.1f})")
                    self._apply_direct_damage(enemy, damage_to_enemy)

    @staticmethod
    def _apply_direct_damage(enemy, damage):
        """Applique les dégâts directement en contournant les vérifications d'état"""
        if not enemy.alive:
            return

        old_health = enemy.health
        enemy.health -= damage
        print(f"[ROCKET DAMAGE] {type(enemy).__name__} lost {damage} HP ({old_health} -> {enemy.health})")

        # Réveiller l'ennemi
        enemy.is_awake = True
        enemy.is_alerted = True

        # Vérifier si l'ennemi est mort
        if enemy.health <= 0:
            print(f"[ROCKET KILL] {type(enemy).__name__} killed by rocket!")
            enemy.die()
            return

        # Déclencher l'animation de hit seulement si l'ennemi n'est pas déjà dans cet état
        if enemy.state != "hit" and 'hit' in enemy.animations and enemy.animations['hit']:
            # Préserver la direction actuelle
            if enemy.facing_direction_override is None and enemy.target:
                enemy.facing_direction_override = enemy.get_facing_direction(enemy.target.x, enemy.target.y)

            # Sauvegarder l'état actuel et déclencher l'état hit
            enemy.previous_state = enemy.state
            enemy.state = "hit"
            enemy.hit_timer = 0.0

            # Réinitialiser l'animation pour l'état hit
            enemy.frame_index = 0
            enemy.frame_timer = 0

    def _collides_with_entity(self, entity):
        """Vérifie si la roquette entre en collision avec une entité"""
        # Récupérer la position de l'entité de manière cohérente
        # Priorité à x,y car c'est ce qui est mis à jour dans enemy_base
        if hasattr(entity, 'x') and hasattr(entity, 'y'):
            entity_pos = (entity.x, entity.y)
        elif hasattr(entity, 'rect'):
            entity_pos = (entity.rect.centerx, entity.rect.centery)
        elif hasattr(entity, 'position') and isinstance(entity.position, (tuple, list)):
            entity_pos = entity.position
        else:
            print(f"⚠️ Impossible de récupérer la position de {type(entity).__name__}")
            return False

        # Calculer la distance entre la roquette et l'entité
        dx = self.position.x - entity_pos[0]
        dy = self.position.y - entity_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)

        # Définir un rayon de collision plus cohérent
        rocket_radius = getattr(self, 'size', 11) / 2  # Utilise self.size de Projectile

        # Pour les ennemis, utiliser rect.width/2 ou size/2
        if hasattr(entity, 'rect'):
            entity_radius = max(entity.rect.width, entity.rect.height) / 2
        else:
            entity_radius = getattr(entity, 'size', 16) / 2

        collision = distance < (rocket_radius + entity_radius)

        if collision:
            print(f"🎯 Collision détectée avec {type(entity).__name__}")
            print(f"   Roquette: pos=({self.position.x:.1f}, {self.position.y:.1f}), rayon={rocket_radius}")
            print(f"   Ennemi: pos=({entity_pos[0]:.1f}, {entity_pos[1]:.1f}), rayon={entity_radius}")
            print(f"   Distance: {distance:.1f} < seuil: {rocket_radius + entity_radius:.1f}")

        return collision

    def _collides_with_door(self, door):
        """Vérifie si la roquette entre en collision avec une porte"""
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