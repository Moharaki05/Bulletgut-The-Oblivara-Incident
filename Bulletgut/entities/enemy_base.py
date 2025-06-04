import pygame
import math
import random
from entities.pickups.ammo_pickup import AmmoPickup
from entities.pickups.weapon_pickup import WeaponPickup
from utils.assets import load_animation_set, load_sound

class EnemyBase:
    def __init__(self, x: object, y: object, level: object, asset_folder: str) -> None:
        self.x = x
        self.y = y
        self.level = level
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)

        # Stats
        self.max_health = 100
        self.health = self.max_health
        self.speed = 0.6
        self.damage = 10

        # États
        self.alive = True
        self.state = "idle"  # idle / move / attack / death
        self.attack_cooldown = 0
        self.attack_delay = 1000  # ms

        # Cible (le joueur)
        self.target = None

        # Animations et sons
        self.animations = load_animation_set(asset_folder)
        self.animation_frame = 0
        self.animation_timer = 0
        self.frame_duration = 100  # ms entre chaque frame

        self.sfx_attack = load_sound(f"{asset_folder}/attack.wav")
        self.sfx_death = load_sound(f"{asset_folder}/death.wav")

    def update(self, player, dt):
        if not self.alive:
            return

        self.target = player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist < 200:
            self.state = "move"
            dir_x = dx / dist
            dir_y = dy / dist
            self.move(dir_x * self.speed * dt, dir_y * self.speed * dt)
            if dist < 50 and self.attack_cooldown <= 0:
                self.attack()
        else:
            self.state = "idle"

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        self.update_animation(dt)

    def move(self, dx, dy):
        new_rect = self.rect.move(dx, 0)
        if not self.level.is_blocked(new_rect.centerx, new_rect.centery):
            self.rect = new_rect
            self.x = self.rect.centerx

        new_rect = self.rect.move(0, dy)
        if not self.level.is_blocked(new_rect.centerx, new_rect.centery):
            self.rect = new_rect
            self.y = self.rect.centery

    def attack(self):
        if self.target:
            self.target.take_damage(self.damage)
            if self.sfx_attack:
                self.sfx_attack.play()
            self.attack_cooldown = self.attack_delay
            self.state = "attack"

    def take_damage(self, amount, splash=False, direct_hit=True):
        if not self.alive:
            return

        if splash and not direct_hit:
            amount *= 0.5

        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        self.alive = False
        self.state = "death"
        self.animation_frame = 0  # recommence l'animation de mort au début
        if self.sfx_death:
            self.sfx_death.play()
        self.drop_loot()

    def drop_loot(self):
        # À overrider dans les sous-classes (ex : Shotgunner → WeaponPickup)
        pass

    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            frames = self.animations.get(self.state, [])
            if frames:
                self.animation_frame = (self.animation_frame + 1) % len(frames)

    def draw(self, screen, camera):
        if not self.alive and self.state != "death":
            return
        frames = self.animations.get(self.state)
        if frames:
            frame = frames[self.animation_frame % len(frames)]
            screen.blit(frame, (self.rect.x - camera.x, self.rect.y - camera.y))

    def get_sprite(self):
        """Utilisé par le raycaster pour obtenir le sprite à dessiner"""
        if not self.alive and self.state != "death":
            return None
        frames = self.animations.get(self.state)
        if frames:
            return frames[self.animation_frame % len(frames)]
        return None

