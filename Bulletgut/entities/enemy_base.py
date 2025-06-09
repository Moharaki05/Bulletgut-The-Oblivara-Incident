import pygame
import math
import random
from utils.assets import load_animation_set, load_sound

class EnemyBase:
    def __init__(self, x, y, level, asset_folder):
        self.x = x
        self.y = y
        self.position = (self.x, self.y)
        self.level = level
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        self.melee_hitbox = self.rect.inflate(40, 40)

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
        self.frame_duration = 0.25  # Durée entre chaque frame (à ajuster si besoin)
        self.hit_timer = 0.0
        self.hit_duration = 0.25

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
        self.size = 16

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
            print(f"[DEBUG] In hit state - Timer: {self.hit_timer:.2f}/{self.hit_duration}")

        if self.state == "hit":
            self.hit_timer += dt
            if self.hit_timer >= self.hit_duration:
                print(f"[DEBUG] Hit state ended, returning to previous state: {self.previous_state}")
                self.hit_timer = 0.0
                self.state = self.previous_state or "idle"  # Fallback to idle if no previous state

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        self.update_animation(dt)
        self.melee_hitbox.center = self.rect.center

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

    # Updated move() method in enemy_base.py
    def move(self, dx, dy):
        old_x, old_y = self.x, self.y
        new_x = old_x + dx
        new_y = old_y + dy
        safe_x, safe_y = self.get_safe_position(self.level, old_x, old_y, new_x, new_y, radius=self.rect.width // 2)

        self.x = safe_x
        self.y = safe_y
        self.rect.center = (self.x, self.y)
        if self.x != old_x or self.y != old_y:
            self.state = "move"

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
            print("hello")
            return

        if splash and not direct_hit:
            amount *= 0.5

        old_health = self.health
        self.health -= amount
        print(f"[DAMAGE] {type(self).__name__} lost {amount} HP ({old_health} -> {self.health})")

        self.is_awake = True
        self.is_alerted = True

        # ⚠️ Vérifie si l'ennemi est mort AVANT de faire quoi que ce soit d'autre
        if self.health <= 0:
            print(f"[DEATH] {type(self).__name__} died!")
            self.die()
            return  # ⬅️ TRÈS IMPORTANT pour éviter que l'état "hit" ne s'active après la mort

        if self.state == "hit":
            return

        print("[DEBUG] Checking hit animation:", self.animations.get('hit'))

        # Only enter hit state if we have hit animations
        if 'hit' in self.animations and self.animations['hit']:
            print(f"[DEBUG] Entering hit state - has hit animations")

            # Preserve current facing direction when hit
            if self.facing_direction_override is None and self.target:
                self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)

            # Save the current state and trigger hit state
            self.previous_state = self.state
            self.state = "hit"
            self.hit_timer = 0.0

            # Reset animation for hit state
            self.frame_index = 0
            self.frame_timer = 0
        else:
            print(f"[DEBUG] No hit animations available, skipping hit state")

    def die(self):
        self.alive = False
        self.state = "death"

        # IMPORTANT: Reset animation properly for death
        self.frame_index = 0
        self.frame_timer = 0

        # Set facing direction for death animation (usually front-facing)
        self.facing_direction_override = 0  # Face front when dying

        if self.sfx_death:
            self.sfx_death.play()
        self.drop_loot()

        print(f"[DEATH] {type(self).__name__} died - starting death animation")

    def drop_loot(self):
        """Override in subclasses"""
        pass

    def update_animation(self, dt):
        if self.state == "death":
            if not hasattr(self, 'death_timer'):
                self.death_timer = 0
            self.death_timer += dt

    def get_direction_index_towards_player(self):
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            angle = (math.degrees(math.atan2(-dy, dx)) + 360) % 360
            return int((angle + 22.5) // 45) % 8  # Découpe en 8 directions (0=Front, etc.)

    def get_facing_direction(self, viewer_x, viewer_y):
        """Retourne la direction du sprite à afficher selon l'état d'éveil de l'ennemi."""
        if self.is_alerted:
            return 0  # Toujours montrer la face (front)

        dx = self.x - viewer_x
        dy = self.y - viewer_y
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        return int((angle + 22.5) // 45) % 8

    # Fixed sections of enemy_base.py to prevent death sprite scaling

    def draw(self, screen, camera):
        if not self.alive and self.state != "death":
            return

        sprite = self.get_sprite(camera.x + screen.get_width() // 2, camera.y + screen.get_height() // 2)
        if sprite:
            # Get original sprite dimensions - NEVER scale sprites
            original_sprite = sprite
            sprite_width, sprite_height = original_sprite.get_size()

            # Calculate base sprite position (centered on entity with bottom alignment)
            # Use the entity's collision rect for positioning
            base_sprite_x = self.rect.centerx - sprite_width // 2 - camera.x
            base_sprite_y = self.rect.bottom - sprite_height - camera.y

            # FIXED: For death state, use simple positioning without collision checks
            if self.state == "death":
                # Death sprites should always render at the basic position without modification
                # This prevents any scaling or distortion that might occur in safe positioning
                screen.blit(original_sprite, (base_sprite_x, base_sprite_y))
            elif self.state == "hit":
                # Hit state also uses simple positioning to avoid visual glitches
                screen.blit(original_sprite, (base_sprite_x, base_sprite_y))
            else:
                # For other states, use the safe position system only if needed
                # But first try the simple position
                screen.blit(original_sprite, (base_sprite_x, base_sprite_y))

    # def get_safe_sprite_position(self, base_x, base_y, sprite, camera):
    #     """Find safe position for sprite rendering that doesn't clip through walls"""
    #     if not sprite:
    #         return base_x, base_y
    #
    #     # FIXED: Skip safe positioning for death and hit states to prevent scaling issues
    #     if self.state in ["death", "hit"]:
    #         return base_x, base_y
    #
    #     sprite_width, sprite_height = sprite.get_size()
    #
    #     # Create a test rectangle for the sprite bounds
    #     sprite_rect = pygame.Rect(base_x, base_y, sprite_width, sprite_height)
    #
    #     # Convert screen coordinates to world coordinates
    #     world_rect = pygame.Rect(
    #         sprite_rect.x + camera.x,
    #         sprite_rect.y + camera.y,
    #         sprite_rect.width,
    #         sprite_rect.height
    #     )
    #
    #     # If sprite doesn't clip through walls, use original position
    #     if not self.level.is_rect_blocked_improved(world_rect):
    #         return base_x, base_y
    #
    #     # For non-death/hit states, try to find a better position
    #     entity_screen_x = self.x - camera.x
    #     entity_screen_y = self.y - camera.y
    #
    #     # Try positions closer to the entity center (pulling sprite away from walls)
    #     search_offsets = [
    #         (0, 0),
    #         (8, 0), (-8, 0), (0, 8), (0, -8),
    #         (16, 0), (-16, 0), (0, 16), (0, -16),
    #         (8, 8), (-8, 8), (8, -8), (-8, -8),
    #         (16, 16), (-16, 16), (16, -16), (-16, -16)
    #     ]
    #
    #     for offset_x, offset_y in search_offsets:
    #         test_x = entity_screen_x - sprite_width // 2 + offset_x
    #         test_y = entity_screen_y - sprite_height + offset_y
    #
    #         test_sprite_rect = pygame.Rect(test_x, test_y, sprite_width, sprite_height)
    #         test_world_rect = pygame.Rect(
    #             test_sprite_rect.x + camera.x,
    #             test_sprite_rect.y + camera.y,
    #             test_sprite_rect.width,
    #             test_sprite_rect.height
    #         )
    #
    #         if not self.level.is_rect_blocked_improved(test_world_rect):
    #             return test_x, test_y
    #
    #     # Fallback: position sprite centered on entity (might still clip but better than scaling)
    #     return (entity_screen_x - sprite_width // 2,
    #             entity_screen_y - sprite_height // 2)

    def get_sprite(self, viewer_x, viewer_y):
        if not self.alive and self.state != "death":
            return None

        # Use facing direction override if set, otherwise calculate direction
        if self.facing_direction_override is not None:
            direction = self.facing_direction_override
        else:
            direction = self.get_facing_direction(viewer_x, viewer_y)

        state = self.state.lower()

        # Get frames for the current state and direction
        frames_by_dir = self.animations.get(state)
        if not frames_by_dir:
            print(f"[DEBUG] No animations found for state '{state}'")
            return None

        # FIXED: Special handling for death animations
        if state == "death":
            # Death animations use direction -1
            direction = -1
            if direction not in frames_by_dir:
                print(f"[ERROR] No death animation frames found!")
                return None

            frames = frames_by_dir[direction]
            if not frames:
                print(f"[ERROR] Death frames list is empty!")
                return None

            # CRITICAL FIX: Ensure frame index is valid and doesn't cause issues
            if self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1  # Stay on last frame

            # FIXED: Slower death animation with proper frame advancement
            frame_advance_speed = 15  # Slower animation
            self.frame_timer += 1

            if self.frame_timer >= frame_advance_speed:
                self.frame_timer = 0
                # Only advance if not on last frame
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1
                    print(f"[DEATH ANIM] Advanced to frame {self.frame_index}/{len(frames)}")

            current_frame = frames[self.frame_index]
            if current_frame:
                # CRITICAL: Return the frame WITHOUT any modifications
                print(f"[DEATH SPRITE] Returning frame {self.frame_index}, size: {current_frame.get_size()}")
                return current_frame
            else:
                print(f"[ERROR] Death frame {self.frame_index} is None!")
                return None

        if state == "hit":
            if direction not in frames_by_dir:
                direction = 0 if 0 in frames_by_dir else list(frames_by_dir.keys())[0]

            frames = frames_by_dir[direction]
            if not frames:
                print("[ERROR] No frames found for hit animation!")
                return None

            # Timing pour hit
            frame_advance_speed = 12
            self.frame_timer += 1
            if self.frame_timer >= frame_advance_speed:
                self.frame_timer = 0
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1

            current_frame = frames[self.frame_index]
            if current_frame:
                print(f"[HIT SPRITE] Returning frame {self.frame_index}, size: {current_frame.get_size()}")
                return current_frame
            else:
                print(f"[ERROR] Hit frame {self.frame_index} is None!")
                return None

        # Handle other states normally...
        if direction not in frames_by_dir:
            if 0 in frames_by_dir:
                direction = 0
            elif frames_by_dir:
                direction = list(frames_by_dir.keys())[0]
            else:
                return None

        frames = frames_by_dir[direction]
        if not frames:
            return None

        # Ensure frame index is valid
        if self.frame_index >= len(frames):
            self.frame_index = 0 if state != "death" else len(frames) - 1

        # Animation timing for non-death states
        if state != "death":
            frame_advance_speed = 8
            if state == "hit":
                frame_advance_speed = 12
            elif state == "attack":
                frame_advance_speed = 5

            self.frame_timer += 1
            if self.frame_timer >= frame_advance_speed:
                self.frame_timer = 0
                if state == "hit":
                    if self.frame_index < len(frames) - 1:
                        self.frame_index += 1
                else:
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

    def get_safe_position(self, level, old_x, old_y, new_x, new_y, radius=10):
        collision_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        collision_rect.center = (new_x, new_y)
        if not level.is_rect_blocked(collision_rect):
            return new_x, new_y

        dx = new_x - old_x
        dy = new_y - old_y
        slide_factor = 0.25

        if abs(dx) > 0.1:
            reduced_x = old_x + dx * slide_factor
            collision_rect.center = (reduced_x, old_y)
            if not level.is_rect_blocked(collision_rect):
                return reduced_x, old_y

        if abs(dy) > 0.1:
            reduced_y = old_y + dy * slide_factor
            collision_rect.center = (old_x, reduced_y)
            if not level.is_rect_blocked(collision_rect):
                return old_x, reduced_y

        return old_x, old_y
