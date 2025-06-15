import math
import random
import pygame as pg
from entities.enemy_base import EnemyBase
from utils.assets import load_sound
from weapons.projectiles.serpentipede_fireball import SerpentipedeFireball


class Serpentipede(EnemyBase):
    def __init__(self, x, y, level):
        super().__init__(x, y, level, "assets/sprites/enemies/serpentipede")

        # Health and damage - similar to Doom Imp
        self.max_health = 60
        self.health = self.max_health
        self.damage = random.randint(3, 24)  # Doom Imp damage range (3 * 1-8)
        self.speed = 1.2  # Slightly faster than base
        self.attack_delay = 1800  # Base attack delay (1.8 seconds)
        self.attack_cooldown = 0

        # Vision and detection - like Doom Imp
        self.vision_range = 1024  # Long range vision
        self.wake_up_distance = 1024  # Wake up when player is visible
        self.alert_distance = 80  # Close combat distance

        # Attack behavior
        self.min_attack_range = 64  # Minimum range for ranged attacks
        self.max_attack_range = 1024  # Maximum attack range
        self.melee_range = 48  # Melee attack range
        self.melee_damage = 12  # Melee damage
        self.melee_cooldown = 1200  # Melee attack cooldown

        # AI states
        self.is_alerted = False
        self.chase_timer = 0
        self.last_attack_time = 0
        self.last_melee_time = 0

        # Attack animation system (like Doom)
        self.attack_animation_duration = 1000  # 1 second total attack animation
        self.attack_frame_timer = 0
        self.attack_windup_time = 600  # Time before firing (wind-up)
        self.has_fired_shot = False
        self.is_in_attack_sequence = False

        # Randomize initial attack cooldown to prevent sync
        self.attack_cooldown = random.randint(0, self.attack_delay)

        # Improved movement AI
        self.movement_timer = 0
        self.movement_duration = random.randint(800, 2000)
        self.current_movement_angle = 0
        self.strafe_direction = random.choice([-1, 1])
        self.movement_mode = "direct"  # "direct", "strafe", "circle", "zigzag"
        self.preferred_distance = random.randint(180, 320)
        self.dodge_timer = 0
        self.last_player_pos = None

        # Unique movement parameters per enemy
        self.zigzag_amplitude = random.uniform(0.7, 1.2)
        self.zigzag_frequency = random.uniform(1.8, 2.8)
        self.zigzag_phase_offset = random.uniform(0, 2 * math.pi)
        self.zigzag_approach_bias = random.uniform(0.4, 0.8)

        self.circle_radius_preference = random.uniform(0.9, 1.4)
        self.circle_rotation_speed = random.uniform(1.8, 2.8)
        self.circle_phase_offset = random.uniform(0, 2 * math.pi)

        # Formation and spacing
        self.personal_space_radius = random.randint(90, 140)
        self.formation_angle_preference = random.uniform(0, 2 * math.pi)
        self.spread_factor = random.uniform(0.9, 1.3)

        # Sound effects
        try:
            self.sfx_attack_melee = load_sound("assets/sounds/enemies/serpentipede_attack_near.wav")
            self.sfx_attack_ranged = load_sound("assets/sounds/enemies/serpentipede_shoot.wav")
        except FileNotFoundError:
            self.sfx_attack_melee = None
            self.sfx_attack_ranged = None

    def update(self, player, dt):
        if not self.alive:
            self.update_animation(dt)
            return

        self.target = player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        # Update cooldowns and timers
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt * 1000

        # Handle attack sequence timing
        if self.is_in_attack_sequence:
            self.attack_frame_timer += dt * 1000

            # Fire the shot at the right moment in the animation
            if not self.has_fired_shot and self.attack_frame_timer >= self.attack_windup_time:
                self.fire_projectile()
                self.has_fired_shot = True

            # Check if attack animation is complete
            if self.attack_frame_timer >= self.attack_animation_duration:
                self.end_attack_sequence()

            # During attack sequence, maintain facing direction but don't move
            self.update_animation(dt)
            return

        # Handle hit state FIRST
        if self.state == "hit":
            self.hit_timer += dt
            if self.hit_timer >= self.hit_duration:
                self.hit_timer = 0.0
                self.state = self.previous_state or "idle"
            self.update_animation(dt)
            return

        # AI Logic
        can_see_player = self.can_see_target() and dist <= self.vision_range

        # Alert behavior - once seen, stay alerted
        if can_see_player and not self.is_alerted:
            self.is_alerted = True
            # Add some delay before first attack
            spot_delay = random.randint(200, 800)
            self.attack_cooldown = max(self.attack_cooldown, spot_delay)

        # Main AI behavior
        if self.is_alerted and can_see_player:
            # Always face the player when we can see them
            if not self.is_in_attack_sequence:
                self.facing_direction_override = self.get_facing_direction(player.x, player.y)

            current_time = pg.time.get_ticks()

            # Melee attack if very close
            if dist <= self.melee_range and (current_time - self.last_melee_time >= self.melee_cooldown):
                self.perform_melee_attack(player, current_time)
                return

            # Ranged attack logic
            if (self.min_attack_range <= dist <= self.max_attack_range and
                    self.attack_cooldown <= 0):

                # Random chance to attack vs move (like Doom AI)
                attack_chance = self.calculate_attack_chance(dist)
                if random.random() < attack_chance:
                    self.start_ranged_attack()
                else:
                    # Decide to move instead
                    self.set_next_attack_delay()
                    self.move_towards_player(player, dt)
                    self.state = "move"
            else:
                # Move towards or around player
                if dist > self.alert_distance:
                    self.move_towards_player(player, dt)
                    self.state = "move"
                else:
                    self.state = "idle"

            # Update last seen position
            self.last_seen_player_pos = pg.Vector2(player.x, player.y)
            self.chase_timer = 6000  # Chase for 6 seconds after losing sight

        elif self.is_alerted and self.last_seen_player_pos:
            # Chase last known position
            chase_dist = math.hypot(self.last_seen_player_pos.x - self.x,
                                    self.last_seen_player_pos.y - self.y)
            if chase_dist > 48 and self.chase_timer > 0:
                self.facing_direction_override = self.get_facing_direction(
                    self.last_seen_player_pos.x, self.last_seen_player_pos.y)
                self.move_towards(self.last_seen_player_pos.x, self.last_seen_player_pos.y, dt)
                self.state = "move"
                self.chase_timer -= dt * 1000
            else:
                # Lost the trail, return to patrol
                self.last_seen_player_pos = None
                self.patrol(dt)
        else:
            # Not alerted, patrol normally
            if can_see_player:
                self.is_alerted = True
            else:
                self.patrol(dt)

        self.update_animation(dt)

    @staticmethod
    def calculate_attack_chance(distance):
        """Calculate probability of attacking based on distance (like Doom AI)"""
        if distance < 150:
            return 0.8  # High chance at close range
        elif distance < 300:
            return 0.6  # Medium chance at medium range
        elif distance < 500:
            return 0.4  # Lower chance at long range
        else:
            return 0.2  # Very low chance at extreme range

    def perform_melee_attack(self, player, current_time):
        """Perform melee attack when very close to player"""
        self.facing_direction_override = self.get_facing_direction(player.x, player.y)
        self.state = "attack"
        self.last_melee_time = current_time

        # Deal damage to player
        player.take_damage(self.melee_damage)

        # Play melee attack sound
        if self.sfx_attack_melee:
            self.sfx_attack_melee.play()

    def start_ranged_attack(self):
        """Start the ranged attack sequence (like Doom Imp)"""
        if self.target:
            self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)

        self.is_in_attack_sequence = True
        self.attack_frame_timer = 0
        self.has_fired_shot = False
        self.state = "attack"

        # Set next attack cooldown with variation
        self.set_next_attack_delay()

        # Vary wind-up time slightly
        windup_variation = random.randint(-100, 150)
        self.attack_windup_time = max(400, 600 + windup_variation)

    def set_next_attack_delay(self):
        """Set the next attack delay with random variation"""
        base_cooldown = self.attack_delay
        variation = random.randint(-400, 800)
        self.attack_cooldown = base_cooldown + variation
        self.attack_cooldown = max(self.attack_cooldown, 1000)  # Minimum 1 second

    def fire_projectile(self):
        self.sfx_attack_ranged.play()
        player = self.level.game.player
        dx, dy = player.x - self.x, player.y - self.y
        angle = math.atan2(dy, dx)

        # Décalage pour éviter que le projectile naisse dans l'ennemi
        offset = 0.5
        start_x = self.x + math.cos(angle) * offset
        start_y = self.y + math.sin(angle) * offset

        projectile = SerpentipedeFireball(
            game=self.level.game,
            x=start_x,
            y=start_y,
            angle=angle,
            owner=self
        )

        self.level.game.projectiles.append(projectile)

    def end_attack_sequence(self):
        """End the attack sequence and return to normal behavior"""
        # Face the player when attack ends (if we still have a target)
        if self.target:
            self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)
        else:
            self.facing_direction_override = None

        self.is_in_attack_sequence = False
        self.attack_frame_timer = 0
        self.has_fired_shot = False
        self.state = "idle"

    def move_towards_player(self, player, dt):
        """Improved movement AI with tactical behavior"""
        if self.is_in_attack_sequence:
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Update movement timer
        self.movement_timer += dt * 1000

        # Detect player movement for dodging
        player_moved = False
        if self.last_player_pos:
            player_move_dist = math.hypot(player.x - self.last_player_pos[0],
                                          player.y - self.last_player_pos[1])
            if player_move_dist > 40:
                player_moved = True
                self.dodge_timer = 600

        self.last_player_pos = (player.x, player.y)

        # Update dodge timer
        if self.dodge_timer > 0:
            self.dodge_timer -= dt * 1000

        # Change movement mode periodically
        if (self.movement_timer >= self.movement_duration or
                (self.movement_mode == "direct" and dist < 100)):
            self.choose_movement_mode(dist)
            self.movement_timer = 0

        # Calculate movement direction
        base_dx = dx / dist
        base_dy = dy / dist
        move_dx, move_dy = self.calculate_movement_vector(base_dx, base_dy, dist, player_moved, dt)

        # Apply movement with speed scaling
        move_speed = self.speed * dt * 60

        # Adjust speed based on mode and situation
        if self.movement_mode == "strafe":
            move_speed *= 0.85
        elif self.movement_mode == "circle":
            move_speed *= 0.9
        elif self.dodge_timer > 0:
            move_speed *= 1.3  # Faster when dodging

        move_x = move_dx * move_speed
        move_y = move_dy * move_speed

        # Attempt movement with fallback
        old_pos = (self.x, self.y)
        self.move(move_x, move_y)

        # If blocked, try alternative movement
        if (self.x, self.y) == old_pos and move_speed > 0:
            self.handle_movement_blocked(base_dx, base_dy, move_speed)

    def choose_movement_mode(self, distance):
        """Choose movement mode based on distance and situation"""
        if distance > 400:
            # Long range - mostly direct approach
            modes = ["direct"] * 5 + ["strafe"] * 2 + ["zigzag"] * 1
        elif distance > 200:
            # Medium range - mixed tactics
            modes = ["direct"] * 2 + ["strafe"] * 4 + ["zigzag"] * 2 + ["circle"] * 1
        else:
            # Close range - more evasive
            modes = ["direct"] * 1 + ["strafe"] * 4 + ["circle"] * 3 + ["zigzag"] * 2

        self.movement_mode = random.choice(modes)
        self.movement_duration = random.randint(700, 1800)

        # Initialize mode-specific parameters
        if self.movement_mode == "strafe":
            self.strafe_direction = random.choice([-1, 1])
        elif self.movement_mode == "circle":
            self.current_movement_angle = random.uniform(0, 2 * math.pi)

    def calculate_movement_vector(self, base_dx, base_dy, distance, player_moved, dt):
        """Calculate movement direction based on current mode"""
        # Priority: dodge if player moved and we're close
        if player_moved and self.dodge_timer > 0 and distance < 250:
            dodge_dx = -base_dy * random.choice([-1, 1])
            dodge_dy = base_dx * random.choice([-1, 1])
            return dodge_dx, dodge_dy

        if self.movement_mode == "direct":
            return self.calculate_direct_movement(base_dx, base_dy, distance)
        elif self.movement_mode == "strafe":
            return self.calculate_strafe_movement(base_dx, base_dy, distance)
        elif self.movement_mode == "zigzag":
            return self.calculate_zigzag_movement(base_dx, base_dy)
        elif self.movement_mode == "circle":
            return self.calculate_circle_movement(base_dx, base_dy, distance, dt)

        return base_dx, base_dy

    def calculate_direct_movement(self, base_dx, base_dy, distance):
        """Direct movement with noise and distance management"""
        noise_factor = 0.15
        noise_dx = (random.random() - 0.5) * noise_factor
        noise_dy = (random.random() - 0.5) * noise_factor

        if distance < self.preferred_distance * 0.7:
            # Too close, back away while maintaining some approach
            return base_dx * 0.2 + noise_dx, base_dy * 0.2 + noise_dy
        elif distance > self.preferred_distance * 1.3:
            # Too far, approach more aggressively
            return base_dx * 1.2 + noise_dx, base_dy * 1.2 + noise_dy
        else:
            return base_dx * 0.8 + noise_dx, base_dy * 0.8 + noise_dy

    def calculate_strafe_movement(self, base_dx, base_dy, distance):
        """Strafing movement perpendicular to player"""
        perp_dx = -base_dy * self.strafe_direction
        perp_dy = base_dx * self.strafe_direction

        # Mix strafe with approach/retreat
        if distance > self.preferred_distance:
            approach_factor = 0.4
        else:
            approach_factor = -0.3

        final_dx = perp_dx * 0.8 + base_dx * approach_factor
        final_dy = perp_dy * 0.8 + base_dy * approach_factor

        # Normalize
        final_dist = math.hypot(final_dx, final_dy)
        if final_dist > 0:
            return final_dx / final_dist, final_dy / final_dist
        return perp_dx, perp_dy

    def calculate_zigzag_movement(self, base_dx, base_dy):
        """Zigzag movement pattern"""
        time_seconds = self.movement_timer / 1000.0
        zigzag_phase = (time_seconds * self.zigzag_frequency * 2 * math.pi +
                        self.zigzag_phase_offset)
        zigzag_intensity = math.sin(zigzag_phase) * self.zigzag_amplitude

        perp_dx = -base_dy
        perp_dy = base_dx

        final_dx = (base_dx * self.zigzag_approach_bias +
                    perp_dx * zigzag_intensity * (1 - self.zigzag_approach_bias))
        final_dy = (base_dy * self.zigzag_approach_bias +
                    perp_dy * zigzag_intensity * (1 - self.zigzag_approach_bias))

        # Add randomness
        noise_factor = 0.1
        final_dx += (random.random() - 0.5) * noise_factor
        final_dy += (random.random() - 0.5) * noise_factor

        # Normalize
        final_dist = math.hypot(final_dx, final_dy)
        if final_dist > 0:
            return final_dx / final_dist, final_dy / final_dist
        return base_dx, base_dy

    def calculate_circle_movement(self, base_dx, base_dy, distance, dt):
        """Circular movement around player"""
        angle_increment = self.circle_rotation_speed * dt
        self.current_movement_angle += angle_increment
        actual_angle = self.current_movement_angle + self.circle_phase_offset

        circle_dx = math.cos(actual_angle)
        circle_dy = math.sin(actual_angle)

        target_radius = self.preferred_distance * self.circle_radius_preference

        # Adjust based on distance to preferred radius
        if distance > target_radius * 1.4:
            # Too far, approach while circling
            mix_factor = 0.7
            final_dx = circle_dx * (1 - mix_factor) + base_dx * mix_factor
            final_dy = circle_dy * (1 - mix_factor) + base_dy * mix_factor
        elif distance < target_radius * 0.6:
            # Too close, retreat while circling
            mix_factor = 0.5
            final_dx = circle_dx * (1 - mix_factor) - base_dx * mix_factor
            final_dy = circle_dy * (1 - mix_factor) - base_dy * mix_factor
        else:
            # Good distance, pure circle with slight approach
            approach_bias = 0.15
            final_dx = circle_dx * (1 - approach_bias) + base_dx * approach_bias
            final_dy = circle_dy * (1 - approach_bias) + base_dy * approach_bias

        # Formation spreading
        spread_dx = math.cos(self.formation_angle_preference) * 0.2
        spread_dy = math.sin(self.formation_angle_preference) * 0.2
        final_dx += spread_dx
        final_dy += spread_dy

        # Normalize
        final_dist = math.hypot(final_dx, final_dy)
        if final_dist > 0:
            return final_dx / final_dist, final_dy / final_dist
        return circle_dx, circle_dy

    def handle_movement_blocked(self, base_dx, base_dy, move_speed):
        """Handle when walls block movement"""
        self.movement_mode = "strafe"
        self.strafe_direction *= -1
        self.movement_timer = 0

        # Try perpendicular movement
        perp_dx = -base_dy * self.strafe_direction
        perp_dy = base_dx * self.strafe_direction
        self.move(perp_dx * move_speed, perp_dy * move_speed)

    def patrol(self, dt):
        """Patrol when not alerted"""
        if self.is_in_attack_sequence:
            return

        self.patrol_timer += dt

        # Change direction every 2-4 seconds
        if self.patrol_timer > random.randint(2000, 4500):
            self.patrol_timer = 0
            angle = random.uniform(0, 2 * math.pi)
            self.patrol_dir = pg.Vector2(math.cos(angle), math.sin(angle))

        # Move slowly during patrol
        move_speed = self.speed * 0.25 * dt * 60
        move_x = self.patrol_dir.x * move_speed
        move_y = self.patrol_dir.y * move_speed

        old_pos = (self.x, self.y)
        self.move(move_x, move_y)

        if (self.x, self.y) != old_pos:
            self.state = "move"
        else:
            # Hit obstacle, change direction
            self.patrol_timer = 4000
            self.state = "idle"

    def take_damage(self, amount, splash=False, direct_hit=True):
        """Handle taking damage with Doom-style pain behavior"""
        if not self.alive:
            return

        # Always become alerted when taking damage
        self.is_alerted = True

        # Pain can interrupt attack sequence (like Doom)
        if self.is_in_attack_sequence:
            # Small chance to interrupt attack (pain chance)
            if random.random() < 0.25:  # 25% chance like Doom
                self.end_attack_sequence()

        # Call parent damage handling for hit state and animation
        super().take_damage(amount, splash, direct_hit)

    def attack(self):
        """Legacy method for compatibility"""
        if not self.is_in_attack_sequence:
            self.start_ranged_attack()

    def drop_loot(self):
        """Override to drop appropriate loot"""
        # Could drop ammo, health, etc.
        pass