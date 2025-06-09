import pygame as pg
import math
from weapons.melee_weapon import MeleeWeapon

class Chainsaw(MeleeWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Chainsaw"
        self.damage = 15
        self.range = 60  # Portée courte
        self.fire_rate = 10
        self.shot_cooldown = 1.0 / self.fire_rate
        self.hold_to_attack = True
        self.last_fire_time = 0
        self.scale_factor = 0.4

        self.is_attacking = False
        self.animation_timer = 0
        self.animation_speed = 0.05
        self.frame_index = 0

        self.bobbing_timer = 0
        self.bobbing_x = 0
        self.bobbing_y = 0
        self.bobbing_intensity = 10
        self.bobbing_speed = 5

        # Sprites
        self.idle_frames = [
            pg.image.load("assets/weapons/chainsaw/csaw_idle1.png").convert_alpha(),
            pg.image.load("assets/weapons/chainsaw/csaw_idle2.png").convert_alpha(),
        ]
        self.attack_frames = [
            pg.image.load("assets/weapons/chainsaw/csaw_attack1.png").convert_alpha(),
            pg.image.load("assets/weapons/chainsaw/csaw_attack2.png").convert_alpha(),
        ]
        self.current_sprite = self.idle_frames[0]

        # Sons
        self.idle_sound = pg.mixer.Sound("assets/sounds/chainsaw/chainsaw_idle.wav")
        self.attack_sound = pg.mixer.Sound("assets/sounds/chainsaw/chainsaw_attack.wav")
        self.idle_sound.set_volume(0.5)
        self.attack_sound.set_volume(0.7)

    def update(self, dt):
        if self.game.player.moving:
            self.bobbing_timer += dt * self.bobbing_speed
            self.bobbing_x = math.sin(self.bobbing_timer) * self.bobbing_intensity
            self.bobbing_y = abs(math.cos(self.bobbing_timer)) * self.bobbing_intensity
        else:
            self.bobbing_x = 0
            self.bobbing_y = 0

        # Animation
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            frames = self.get_current_frames()
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.current_sprite = frames[self.frame_index]

        # Attaque en boucle
        if self.is_attacking:
            self.try_attack()
            if not self.attack_sound.get_num_channels():
                self.attack_sound.play(-1)
        else:
            if not self.idle_sound.get_num_channels():
                self.idle_sound.play(-1)

    def get_current_frames(self):
        return self.attack_frames if self.is_attacking else self.idle_frames

    def start_attack(self):
        self.is_attacking = True
        self.idle_sound.stop()

    def stop_attack(self):
        self.is_attacking = False
        self.attack_sound.stop()

    def try_attack(self):
        hit_range = self.range  # portée en pixels
        angle_range = math.radians(60)  # cône frontal ±30°

        player_x, player_y = self.game.player.get_position()
        player_angle = self.game.player.get_angle()
        enemy_hit = False

        for enemy in self.game.enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - player_x
            dy = enemy.y - player_y
            distance = math.hypot(dx, dy)

            if distance <= hit_range:
                angle_to_enemy = math.atan2(dy, dx)
                angle_diff = abs((angle_to_enemy - player_angle + math.pi) % (2 * math.pi) - math.pi)

                if angle_diff <= angle_range:
                    enemy.take_damage(self.damage, splash=False, direct_hit=True)
                    enemy_hit = True

        # Gestion du son (ta version, conservée)
        if enemy_hit:
            if not self.attack_sound.get_num_channels():
                self.attack_sound.play(-1)
        else:
            self.attack_sound.stop()

    def render(self, screen):
        if not self.current_sprite:
            return

        screen_w, screen_h = screen.get_size()
        target_width = int(screen_w * 0.25)  # même largeur que les autres armes
        ratio = target_width / self.current_sprite.get_width()
        target_height = int(self.current_sprite.get_height() * ratio)

        weapon_sprite = pg.transform.scale(self.current_sprite, (target_width, target_height))
        x = screen_w // 2 - weapon_sprite.get_width() // 2 + self.bobbing_x + 30
        y = screen_h - weapon_sprite.get_height() + self.bobbing_y

        screen.blit(weapon_sprite, (x, y))

    def _handle_fire(self):
        return False

    def on_deselected(self):
        if self.idle_sound:
            self.idle_sound.stop()
        if self.attack_sound:
            self.attack_sound.stop()

    def on_selected(self):
        if self.is_attacking:
            if not self.attack_sound.get_num_channels():
                self.attack_sound.play(-1)
        else:
            if not self.idle_sound.get_num_channels():
                self.idle_sound.play(-1)

    def fire(self):
        self.start_attack()
        return True

    def release_trigger(self):
        self.stop_attack()
