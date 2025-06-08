import pygame
import math
import random
from entities.pickups.ammo_pickup import AmmoPickup
from entities.pickups.weapon_pickup import WeaponPickup
from utils.assets import load_animation_set, load_sound

class EnemyBase:
    def __init__(self, x, y, level, asset_folder):
        self.x = x
        self.y = y
        self.level = level
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)

        # Stats
        self.max_health = 100
        self.health = self.max_health
        self.speed = 0.6
        self.damage = 10

        # States
        self.alive = True
        self.state = "idle"
        self.attack_cooldown = 0
        self.attack_delay = 1000

        # Target
        self.target = None

        # Animation
        self.animations = load_animation_set(asset_folder)
        self.animation_frame = 0
        self.animation_timer = 0
        self.frame_duration = 100

        # Direction fixée (ex: après attaque)
        self.facing_direction_override = None

        # AI
        self.last_seen_player_pos = None
        self.previous_state = "idle"
        self.patrol_timer = 0
        self.patrol_dir = pygame.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.vision_range = 200
        self.vision_angle = 90
        self.ai_state = "patrol"
        self.is_awake = False
        self.is_alerted = False
        self.wake_up_distance = 1400
        self.wake_timer = 0
        self.is_attacking = False
        self.attack_pause_timer = 0

        self.image = None  # Pour que self.image soit bien défini
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_duration = 0.15  # Durée entre chaque frame (à ajuster si besoin)
        self.hit_timer = 0.0
        self.hit_duration = 0.75

        # Sons
        try:
            self.sfx_attack = load_sound(f"{asset_folder}/attack.wav")
        except:
            self.sfx_attack = None
        try:
            self.sfx_death = load_sound(f"{asset_folder}/death.wav")
        except:
            self.sfx_death = None

        self.update_rect()
        self.size = 32

    def update(self, player, dt):
        if not self.alive:
            self.update_animation(dt)
            return

        self.target = player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        # Réveil si joueur est proche
        if dist < self.wake_up_distance:
            self.is_awake = True

        if not self.is_awake:
            self.patrol(dt)
            self.update_animation(dt)
            return

        if dist < 300:
            self.facing_direction_override = self.get_facing_direction(player.x, player.y)
            self.move_towards_player(player, dt)
            self.state = "move"

            if dist < 100 and self.attack_cooldown <= 0:
                self.facing_direction_override = self.get_facing_direction(player.x, player.y)
                self.attack()

            elif self.can_see_target():
                # Toujours se tourner vers le joueur si on le voit
                self.facing_direction_override = self.get_facing_direction(player.x, player.y)

        else:
            if not self.can_see_target():
                self.facing_direction_override = None

            self.patrol(dt)

        if self.state == "hit":
            self.hit_timer += dt
            if self.hit_timer >= self.hit_duration:
                self.hit_timer = 0.0
                self.state = "idle"  # ou "chase", "search", etc. selon logique IA

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        self.update_animation(dt)

    def move_towards_player(self, player, dt):
        """Move towards the player"""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Normalize direction
        dx /= dist
        dy /= dist

        # Move with collision checking
        move_x = dx * self.speed * dt * 60
        move_y = dy * self.speed * dt * 60

        old_x, old_y = self.x, self.y
        self.move(move_x, move_y)

    def move_towards(self, target_x, target_y, dt):
        """Move towards a specific target position"""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Normalize direction
        dx /= dist
        dy /= dist

        # Move with collision checking
        move_x = dx * self.speed * dt * 60
        move_y = dy * self.speed * dt * 60
        self.move(move_x, move_y)

    def is_sprite_position_safe(self, sprite_x, sprite_y, sprite, camera):
        """Check if sprite position would clip through walls"""
        if not sprite:
            return True

        # Get sprite dimensions
        sprite_width, sprite_height = sprite.get_size()

        # Convert screen coordinates back to world coordinates for collision checking
        world_left = sprite_x + camera.x
        world_right = sprite_x + sprite_width + camera.x
        world_top = sprite_y + camera.y
        world_bottom = sprite_y + sprite_height + camera.y

        # Sample points around the sprite bounds to check for wall collisions
        sample_points = [
            (world_left, world_top),  # Top-left
            (world_right, world_top),  # Top-right
            (world_left, world_bottom),  # Bottom-left
            (world_right, world_bottom),  # Bottom-right
            (world_left + sprite_width // 2, world_top),  # Top-center
            (world_left + sprite_width // 2, world_bottom),  # Bottom-center
            (world_left, world_top + sprite_height // 2),  # Left-center
            (world_right, world_top + sprite_height // 2),  # Right-center
        ]

        # Check if any sample point hits a wall
        for point_x, point_y in sample_points:
            if self.level.is_blocked(point_x, point_y):
                return False

        return True

    def get_safe_sprite_position(self, base_x, base_y, sprite, camera):
        """Find safe position for sprite rendering that doesn't clip through walls"""
        if not sprite:
            return base_x, base_y

        sprite_width, sprite_height = sprite.get_size()

        # Create a test rectangle for the sprite bounds
        sprite_rect = pygame.Rect(base_x, base_y, sprite_width, sprite_height)

        # Convert screen coordinates to world coordinates
        world_rect = pygame.Rect(
            sprite_rect.x + camera.x,
            sprite_rect.y + camera.y,
            sprite_rect.width,
            sprite_rect.height
        )

        # If sprite doesn't clip through walls, use original position
        if not self.level.is_rect_blocked_improved(world_rect):
            return base_x, base_y

        # Try to find a better position by moving the sprite away from walls
        entity_screen_x = self.x - camera.x
        entity_screen_y = self.y - camera.y

        # Try positions closer to the entity center (pulling sprite away from walls)
        search_offsets = [
            (0, 0),
            (8, 0), (-8, 0), (0, 8), (0, -8),
            (16, 0), (-16, 0), (0, 16), (0, -16),
            (8, 8), (-8, 8), (8, -8), (-8, -8),
            (16, 16), (-16, 16), (16, -16), (-16, -16)
        ]

        for offset_x, offset_y in search_offsets:
            test_x = entity_screen_x - sprite_width // 2 + offset_x
            test_y = entity_screen_y - sprite_height + offset_y

            test_sprite_rect = pygame.Rect(test_x, test_y, sprite_width, sprite_height)
            test_world_rect = pygame.Rect(
                test_sprite_rect.x + camera.x,
                test_sprite_rect.y + camera.y,
                test_sprite_rect.width,
                test_sprite_rect.height
            )

            if not self.level.is_rect_blocked_improved(test_world_rect):
                return test_x, test_y

        # Fallback: position sprite centered on entity (might still clip but better than original)
        return (entity_screen_x - sprite_width // 2,
                entity_screen_y - sprite_height // 2)

    # Updated move() method in enemy_base.py
    def move(self, dx, dy):
        old_x, old_y = self.x, self.y
        self.x += dx
        self.y += dy
        if (self.x != old_x or self.y != old_y):
            self.state = "move"
        # Try horizontal movement first
        test_rect = self.rect.copy()
        test_rect.x += dx

        # Check multiple points along the rectangle edges for horizontal movement
        collision_points = [
            (test_rect.left, test_rect.top),
            (test_rect.left, test_rect.bottom - 1),
            (test_rect.right - 1, test_rect.top),
            (test_rect.right - 1, test_rect.bottom - 1),
            (test_rect.centerx, test_rect.top),
            (test_rect.centerx, test_rect.bottom - 1)
        ]

        can_move_x = True
        for point in collision_points:
            if self.level.is_blocked(point[0], point[1]):
                can_move_x = False
                break

        if can_move_x:
            self.rect.x += dx
            self.x = self.rect.centerx
            moved = True

        # Try vertical movement
        test_rect = self.rect.copy()
        test_rect.y += dy

        # Check multiple points along the rectangle edges for vertical movement
        collision_points = [
            (test_rect.left, test_rect.top),
            (test_rect.left, test_rect.bottom - 1),
            (test_rect.right - 1, test_rect.top),
            (test_rect.right - 1, test_rect.bottom - 1),
            (test_rect.left, test_rect.centery),
            (test_rect.right - 1, test_rect.centery)
        ]

        can_move_y = True
        for point in collision_points:
            if self.level.is_blocked(point[0], point[1]):
                can_move_y = False
                break

        if can_move_y:
            self.rect.y += dy
            self.y = self.rect.centery
            moved = True

        return moved


    def patrol(self, dt):
        """Patrol behavior - wander around randomly"""
        self.patrol_timer += dt

        # Change direction every 3 seconds
        if self.patrol_timer > 3000:
            self.patrol_timer = 0
            # Choose a new random direction
            angle = random.uniform(0, 2 * math.pi)
            self.patrol_dir = pygame.Vector2(math.cos(angle), math.sin(angle))

        # Move in patrol direction
        move_x = self.patrol_dir.x * self.speed * 0.5 * dt  # Slower patrol speed
        move_y = self.patrol_dir.y * self.speed * 0.5 * dt

        # Check if we can move in this direction
        test_rect = self.rect.move(move_x, move_y)
        if not self.level.is_blocked(test_rect.centerx, test_rect.centery):
            self.move(move_x, move_y)
            self.state = "move"
        else:
            # Hit a wall, choose new direction immediately
            self.patrol_timer = 3000
            self.state = "idle"

    def attack(self):
        """Override in subclasses"""
        pass

    def take_damage(self, amount, splash=False, direct_hit=True):
        if not self.alive:
            return

        if splash and not direct_hit:
            amount *= 0.5

        old_health = self.health
        self.health -= amount
        print(f"[DAMAGE] {type(self).__name__} lost {amount} HP ({old_health} -> {self.health})")

        # Sauvegarder l'état actuel et déclencher l'état de hit
        self.previous_state = self.state
        self.state = "hit"
        self.hit_timer = 0.0

        self.is_awake = True
        self.is_alerted = True

        if self.health <= 0:
            print(f"[DEATH] {type(self).__name__} died!")
            self.die()

    def die(self):
        self.alive = False
        self.state = "death"
        self.animation_frame = 0
        if self.sfx_death:
            self.sfx_death.play()
        self.drop_loot()

    def drop_loot(self):
        """Override in subclasses"""
        pass

    def update_animation(self, dt):
        self.frame_timer += dt

    def get_direction_index_towards_player(self):
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            angle = (math.degrees(math.atan2(-dy, dx)) + 360) % 360
            return int((angle + 22.5) // 45) % 8  # Découpe en 8 directions (0=Front, etc.)

    def draw(self, screen, camera):
        if not self.alive and self.state != "death":
            return

        sprite = self.get_sprite(camera.x + screen.get_width() // 2, camera.y + screen.get_height() // 2)
        if sprite:
            # Calculate base sprite position (centered on entity with bottom alignment)
            sprite_width, sprite_height = sprite.get_size()

            # Center horizontally on the entity, align bottom with entity's collision rect bottom
            base_sprite_x = self.rect.centerx - sprite_width // 2 - camera.x
            base_sprite_y = self.rect.bottom - sprite_height - camera.y

            # Get safe position that won't clip through walls
            safe_x, safe_y = self.get_safe_sprite_position(base_sprite_x, base_sprite_y, sprite, camera)

            screen.blit(sprite, (safe_x, safe_y))

    def get_facing_direction(self, viewer_x, viewer_y):
        """Retourne la direction du sprite à afficher selon l'état d'éveil de l'ennemi."""
        if self.is_alerted:
            return 0  # Toujours montrer la face (front)

        dx = self.x - viewer_x
        dy = self.y - viewer_y
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        return int((angle + 22.5) // 45) % 8

    def get_sprite(self, viewer_x, viewer_y):
        if not self.alive and self.state != "death":
            return None

        # 🔄 Toujours recalculer la direction vers le joueur
        direction = self.get_facing_direction(viewer_x, viewer_y)
        state = self.state.lower()

        frames_by_dir = self.animations.get(state)
        if not frames_by_dir:
            return None

        if direction not in frames_by_dir:
            direction = 0

        frames = frames_by_dir[direction]
        if not frames:
            return None

        if self.frame_index >= len(frames):
            self.frame_index = 0

        self.frame_timer += 1
        if self.frame_timer >= 10:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames)

        return frames[self.frame_index]

    def can_see_target(self):
        """Check if enemy has clear line of sight to target"""
        if not self.target:
            return False

        return self.has_line_of_sight(self.target)

    def has_line_of_sight(self, player):
        """Raycast to check line of sight"""
        x0, y0 = int(self.x // 64), int(self.y // 64)
        x1, y1 = int(player.x // 64), int(player.y // 64)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while x0 != x1 or y0 != y1:
            wx = x0 * 64 + 32
            wy = y0 * 64 + 32
            if self.level.is_blocked(wx, wy):
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return True

    def update_rect(self):
        self.rect.topleft = (int(self.x) - self.rect.width // 2, int(self.y) - self.rect.height // 2)