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

        # States
        self.alive = True
        self.state = "idle"  # idle / move / attack / death
        self.attack_cooldown = 0
        self.attack_delay = 1000  # ms

        # Target (player)
        self.target = None

        # Animations and sounds
        self.animations = load_animation_set(asset_folder)
        self.animation_frame = 0
        self.animation_timer = 0
        self.frame_duration = 100  # ms between frames

        # AI behavior
        self.last_seen_player_pos = None
        self.patrol_timer = 0
        self.patrol_dir = pygame.Vector2(random.choice([-1, 1]), random.choice([-1, 1])).normalize()
        self.vision_range = 200
        self.vision_angle = 90  # in degrees
        self.ai_state = "patrol"  # "patrol", "alert", "search", "attack"

        # Wake up behavior (like Doom zombieman)
        self.is_awake = False
        self.wake_up_distance = 400  # Distance at which enemy wakes up
        self.wake_timer = 0
        self.is_attacking = False
        self.attack_pause_timer = 0

        # Sound loading with error handling
        try:
            self.sfx_attack = load_sound(f"{asset_folder}/attack.wav")
        except:
            self.sfx_attack = None

        try:
            self.sfx_death = load_sound(f"{asset_folder}/death.wav")
        except:
            self.sfx_death = None

        self.update_rect()

    def update(self, player, dt):
        """Main update method - implements Doom-like Zombieman AI"""
        if not self.alive:
            self.update_animation(dt)
            return

        print(f"[DEBUG] Enemy update: pos=({self.x:.1f}, {self.y:.1f}), state={self.state}, dt={dt}")

        self.target = player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        print(f"[DEBUG] Player distance: {dist:.1f}")

        # Simple AI: always move towards player if close enough
        if dist < 300:  # Detection range
            print(f"[DEBUG] Moving towards player")
            self.move_towards_player(player, dt)
            self.state = "move"

            # Attack if close enough
            if dist < 100 and self.attack_cooldown <= 0:
                self.attack()
        else:
            # Patrol when player is far
            print(f"[DEBUG] Patrolling")
            self.patrol(dt)

        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        self.update_animation(dt)

    def move_towards_player(self, player, dt):
        """Move towards the player"""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        print(f"[DEBUG] move_towards_player: dx={dx:.1f}, dy={dy:.1f}, dist={dist:.1f}")

        if dist == 0:
            return

        # Normalize direction
        dx /= dist
        dy /= dist

        # Move with collision checking
        move_x = dx * self.speed * dt * 60
        move_y = dy * self.speed * dt * 60

        print(f"[DEBUG] Attempting to move by: ({move_x:.2f}, {move_y:.2f})")

        old_x, old_y = self.x, self.y
        self.move(move_x, move_y)

        if self.x != old_x or self.y != old_y:
            print(f"[DEBUG] Successfully moved from ({old_x:.1f}, {old_y:.1f}) to ({self.x:.1f}, {self.y:.1f})")
        else:
            print(f"[DEBUG] Movement blocked!")

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

    def is_sprite_position_safe(self, sprite_x, sprite_y, sprite):
        """Simple collision check - sprite dimensions + buffer"""
        if not sprite:
            return True

        # Get sprite dimensions and add buffer
        sprite_width, sprite_height = sprite.get_size()
        buffer = 10  # Safety buffer

        # Check if the buffered sprite area would collide with walls
        left = sprite_x - buffer
        right = sprite_x + sprite_width + buffer
        top = sprite_y - buffer
        bottom = sprite_y + sprite_height + buffer

        # Convert screen coordinates to world coordinates for wall checking
        world_left = left + self.level.camera.x if hasattr(self.level, 'camera') else left
        world_right = right + self.level.camera.x if hasattr(self.level, 'camera') else right
        world_top = top + self.level.camera.y if hasattr(self.level, 'camera') else top
        world_bottom = bottom + self.level.camera.y if hasattr(self.level, 'camera') else bottom

        # Sample a few points around the buffered sprite area
        sample_points = [
            (world_left, world_top),  # Top-left
            (world_right, world_top),  # Top-right
            (world_left, world_bottom),  # Bottom-left
            (world_right, world_bottom),  # Bottom-right
            ((world_left + world_right) // 2, world_top),  # Top-center
            ((world_left + world_right) // 2, world_bottom),  # Bottom-center
        ]

        # Check if any sample point hits a wall
        for point_x, point_y in sample_points:
            if self.level.is_blocked(point_x, point_y):
                return False

        return True

    def get_safe_sprite_position(self, base_x, base_y, sprite, camera):
        """Find safe position for sprite using simple approach"""
        if not sprite:
            return base_x, base_y

        # First check if the base position is already safe
        if self.is_sprite_position_safe(base_x, base_y, sprite):
            return base_x, base_y

        # If not safe, try moving the sprite closer to the entity center
        sprite_width, sprite_height = sprite.get_size()

        # Calculate entity center in screen coordinates
        entity_screen_x = self.x - camera.x
        entity_screen_y = self.y - camera.y

        # Try different offsets around the entity center
        max_attempts = 20
        step_size = 4

        for attempt in range(max_attempts):
            # Calculate angle for this attempt (spiral outward)
            angle = (attempt * 0.5) % (2 * math.pi)
            offset_distance = (attempt + 1) * step_size

            # Calculate new sprite position
            offset_x = math.cos(angle) * offset_distance
            offset_y = math.sin(angle) * offset_distance

            test_x = entity_screen_x - sprite_width // 2 + offset_x
            test_y = entity_screen_y - sprite_height + offset_y

            if self.is_sprite_position_safe(test_x, test_y, sprite):
                return test_x, test_y

        # If all else fails, return the original position
        # Better to clip slightly than disappear completely
        return base_x, base_y

    def move(self, dx, dy):
        # """Move with collision detection"""
        # print(f"[DEBUG] move() called with dx={dx:.2f}, dy={dy:.2f}")
        # print(f"[DEBUG] Current position: ({self.x:.1f}, {self.y:.1f})")
        # print(f"[DEBUG] Current rect: {self.rect}")
        #
        # # Try moving horizontally first
        # new_rect = self.rect.move(dx, 0)
        # print(f"[DEBUG] Testing X movement to: {new_rect}")
        # blocked_x = self.level.is_blocked(new_rect.centerx, new_rect.centery)
        # print(f"[DEBUG] X movement blocked: {blocked_x}")
        #
        # if not blocked_x:
        #     self.rect = new_rect
        #     self.x = self.rect.centerx
        #     print(f"[DEBUG] X movement successful, new x: {self.x}")
        #
        # # Then try moving vertically
        # new_rect = self.rect.move(0, dy)
        # print(f"[DEBUG] Testing Y movement to: {new_rect}")
        # blocked_y = self.level.is_blocked(new_rect.centerx, new_rect.centery)
        # print(f"[DEBUG] Y movement blocked: {blocked_y}")
        #
        # if not blocked_y:
        #     self.rect = new_rect
        #     self.y = self.rect.centery
        #     print(f"[DEBUG] Y movement successful, new y: {self.y}")
        #
        # print(f"[DEBUG] Final position: ({self.x:.1f}, {self.y:.1f})")
        # print(f"[DEBUG] Final rect: {self.rect}")
        moved = False

        new_x = self.x + dx
        self.rect.topleft = (int(new_x) - self.rect.width // 2, int(self.y) - self.rect.height // 2)
        if not self.level.is_blocked(self.rect.x, self.rect.y):
            self.x = new_x
            moved = True

        new_y = self.y + dy
        self.rect.topleft = (int(self.x) - self.rect.width // 2, int(new_y) - self.rect.height // 2)
        if not self.level.is_blocked(self.rect.x, self.rect.y):
            self.y = new_y
            moved = True

        self.update_rect()
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

        self.health -= amount

        # Wake up when taking damage
        self.is_awake = True

        if self.health <= 0:
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
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            state_anims = self.animations.get(self.state, {})
            if state_anims:
                # Use direction 0 as fallback for simple animation
                frames = state_anims.get(0, [])
                if frames:
                    self.animation_frame = (self.animation_frame + 1) % len(frames)

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

            # DEBUG: Draw collision rect and sprite bounds for testing
            # Remove these in production

            # Entity collision rect (red)
            debug_rect = pygame.Rect(self.rect.x - camera.x, self.rect.y - camera.y,
                                     self.rect.width, self.rect.height)
            pygame.draw.rect(screen, (255, 0, 0), debug_rect, 1)

            # Sprite bounds (blue)
            sprite_debug_rect = pygame.Rect(safe_x, safe_y, sprite_width, sprite_height)
            pygame.draw.rect(screen, (0, 0, 255), sprite_debug_rect, 1)

            # Entity center point (green)
            center_screen_x = self.x - camera.x
            center_screen_y = self.y - camera.y
            pygame.draw.circle(screen, (0, 255, 0), (int(center_screen_x), int(center_screen_y)), 3)

    def get_facing_direction(self, viewer_x, viewer_y):
        dx = self.x - viewer_x
        dy = self.y - viewer_y
        angle = math.degrees(math.atan2(dy, dx)) % 360

        # Divide circle into 8 sectors of 45°
        direction = int(((angle + 22.5) % 360) // 45)
        return direction

    def get_sprite(self, viewer_x, viewer_y):
        if not self.alive and self.state != "death":
            return None

        direction = self.get_facing_direction(viewer_x, viewer_y)
        state = self.state.lower()
        frames_by_dir = self.animations.get(state)

        if not frames_by_dir:
            return None

        if direction not in frames_by_dir:
            direction = 0  # Fallback to direction 0

        frames = frames_by_dir.get(direction)
        if not frames:
            return None

        return frames[self.animation_frame % len(frames)]

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