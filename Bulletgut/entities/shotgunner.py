import math
import random
import pygame as pg
from entities.enemy_base import EnemyBase
from entities.pickups.ammo_pickup import AmmoPickup
from entities.pickups.weapon_pickup import WeaponPickup
from utils.assets import load_sound

class Shotgunner(EnemyBase):
    def __init__(self, x, y, level):
        super().__init__(x, y, level, "assets/sprites/enemies/shotgunner")

        # Gunner-specific stats
        self.max_health = 30  # Zombieman has 20 HP
        self.health = self.max_health
        self.damage = random.randint(9, 45)  #
        self.speed = 1.0
        self.attack_delay = 3500
        self.attack_cooldown = 0

        # Vision and detection
        self.vision_range = 800  # Very long range like Doom
        self.wake_up_distance = 800  # Wake up when player is visible
        self.alert_distance = 64  # Close combat distance

        # Attack behavior
        self.min_attack_range = 0
        self.max_attack_range = 1024  # Can attack at any visible range

        # AI states
        self.is_alerted = False  # Whether enemy has seen player
        self.chase_timer = 0
        self.last_attack_time = 0

        # IMPORTANT: Randomize initial attack cooldown to prevent synchronized attacks
        self.attack_cooldown = random.randint(0, self.attack_delay)  # Random initial cooldown

        # Attack animation timing - like Doom Zombieman
        self.attack_animation_duration = 800  # Total attack animation time (ms)
        self.attack_frame_timer = 0
        self.attack_windup_time = 400  # Time before actually firing (ms)
        self.has_fired_shot = False  # Whether we've fired during this attack
        self.is_in_attack_sequence = False  # Whether we're in the middle of an attack animation

        # IMPROVED: Unique movement AI per enemy instance
        self.movement_timer = 0
        self.movement_duration = random.randint(500, 1500)  # How long to move in current direction
        self.current_movement_angle = 0  # Current movement direction
        self.strafe_direction = random.choice([-1, 1])  # -1 for left, 1 for right
        self.movement_mode = "direct"  # "direct", "strafe", "zigzag", "circle"
        self.preferred_distance = random.randint(150, 300)  # Preferred distance from player
        self.dodge_timer = 0
        self.last_player_pos = None

        # FIXED: Unique zigzag parameters per enemy to prevent clustering
        self.zigzag_amplitude = random.uniform(0.6, 1.0)  # How wide the zigzag is
        self.zigzag_frequency = random.uniform(1.5, 3.0)  # How fast to zigzag (Hz)
        self.zigzag_phase_offset = random.uniform(0, 2 * math.pi)  # Phase offset for desync
        self.zigzag_approach_bias = random.uniform(0.3, 0.7)  # How much to approach vs pure zigzag

        # FIXED: Unique circular movement parameters
        self.circle_radius_preference = random.uniform(0.8, 1.3)  # Preferred radius multiplier
        self.circle_rotation_speed = random.uniform(1.5, 2.5)  # Rotation speed (rad/s)
        self.circle_phase_offset = random.uniform(0, 2 * math.pi)  # Starting angle

        # FIXED: Individual positioning preferences to reduce clustering
        self.personal_space_radius = random.randint(80, 120)  # How close to allow other enemies
        self.formation_angle_preference = random.uniform(0, 2 * math.pi)  # Preferred angle around player
        self.spread_factor = random.uniform(0.8, 1.2)  # How much to spread out from others

        try:
            self.sfx_attack = load_sound("assets/sounds/enemies/shotgunner_shoot.wav")
        except:
            self.sfx_attack = None

    def update(self, player, dt):
        if not self.alive:
            self.update_animation(dt)
            return

        self.target = player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        # Update cooldowns and attack sequence timing
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt * 1000

        # Handle attack sequence timing
        if self.is_in_attack_sequence:
            self.attack_frame_timer += dt * 1000

            # Fire the shot at the right moment in the animation
            if not self.has_fired_shot and self.attack_frame_timer >= self.attack_windup_time:
                self.fire_shot()
                self.has_fired_shot = True

            # Check if attack animation is complete
            if self.attack_frame_timer >= self.attack_animation_duration:
                self.end_attack_sequence()

            # During attack sequence, don't move or change state
            self.update_animation(dt)
            return

        # IMPORTANT: Handle hit state FIRST and exit early if in hit state
        if self.state == "hit":
            self.hit_timer += dt
            if self.hit_timer >= self.hit_duration:
                print(f"[DEBUG] Hit state ended, returning to previous state: {self.previous_state}")
                self.hit_timer = 0.0
                self.state = self.previous_state or "idle"

            # Don't do any other logic while in hit state
            self.update_animation(dt)
            return

        # Rest of the normal AI logic only runs if NOT in hit state
        can_see_player = self.can_see_target() and dist <= self.vision_range

        # Wake up behavior - once alerted, stay alerted
        if can_see_player and not self.is_alerted:
            self.is_alerted = True
            spot_delay = random.randint(0, 500)
            self.attack_cooldown = max(self.attack_cooldown, spot_delay)

        # Normal AI behavior continues...
        if self.is_alerted and can_see_player:
            if not self.is_in_attack_sequence:
                self.facing_direction_override = self.get_facing_direction(player.x, player.y)
            if self.attack_cooldown <= 0:
                additional_delay = random.randint(0, 800)
                if additional_delay > 600:
                    self.start_attack_sequence()
                else:
                    self.attack_cooldown = additional_delay
                    if dist > self.alert_distance:
                        self.move_towards_player(player, dt)
                        self.state = "move"
                    else:
                        self.state = "idle"
            else:
                if dist > self.alert_distance:
                    self.move_towards_player(player, dt)
                    self.state = "move"
                else:
                    self.state = "idle"

            self.last_seen_player_pos = pg.Vector2(player.x, player.y)
            self.chase_timer = 5000

        elif self.is_alerted and self.last_seen_player_pos:
            chase_dist = math.hypot(self.last_seen_player_pos.x - self.x,
                                    self.last_seen_player_pos.y - self.y)
            if chase_dist > 32 and self.chase_timer > 0:
                self.facing_direction_override = self.get_facing_direction(player.x, player.y)
                self.move_towards(self.last_seen_player_pos.x, self.last_seen_player_pos.y, dt)
                self.state = "move"
                self.chase_timer -= dt
            else:
                self.last_seen_player_pos = None
                self.patrol(dt)
        elif not self.is_alerted:
            if can_see_player:
                self.is_alerted = True
            else:
                self.patrol(dt)
        else:
            self.patrol(dt)

        self.update_animation(dt)

    def start_attack_sequence(self):
        """Start the attack animation sequence - like Doom Zombieman"""

        if self.target:
            self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)

        self.is_in_attack_sequence = True
        self.attack_frame_timer = 0
        self.has_fired_shot = False
        self.state = "attack"

        # Set the attack cooldown for after this attack completes with more variation
        base_cooldown = self.attack_delay
        variation = random.randint(-400, 600)
        self.attack_cooldown = base_cooldown + variation
        self.attack_cooldown = max(self.attack_cooldown, 800)

        windup_variation = random.randint(-50, 100)
        self.attack_windup_time = max(350, 400 + windup_variation)

    def fire_shot(self):
        """Fire the actual shot during the attack animation"""
        if not self.target:
            return

        # Set facing direction towards target when firing
        self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        # Improved accuracy system - more forgiving but still distance-based
        base_accuracy = 0.85  # High base accuracy

        # More gradual distance penalty
        if dist <= 150:
            # Very close range - almost always hit
            distance_penalty = 0.0
        elif dist <= 300:
            # Close range - small penalty
            distance_penalty = 0.1
        elif dist <= 500:
            # Medium range - moderate penalty
            distance_penalty = 0.25
        else:
            # Long range - larger penalty but not too harsh
            distance_penalty = min((dist - 500) / 800.0, 0.4)  # Max 40% penalty

        accuracy = base_accuracy - distance_penalty

        # Player movement penalty - if player is moving fast, harder to hit
        if hasattr(self.target, 'velocity'):
            player_speed = math.hypot(getattr(self.target.velocity, 'x', 0),
                                      getattr(self.target.velocity, 'y', 0))
            if player_speed > 100:  # Player moving fast
                accuracy -= 0.15

        # Small random miss chance (reduced from 10% to 5%)
        if random.random() < 0.05:
            accuracy *= 0.3  # Reduce accuracy significantly but don't make it 0

        # Ensure minimum accuracy
        accuracy = max(accuracy, 0.25)  # At least 25% chance to hit even at worst

        if random.random() < accuracy:
            # Hit - calculate damage with slight variation
            base_damage = random.randint(8, 15)  # More consistent damage

            # Distance-based damage falloff (slight)
            if dist > 400:
                base_damage = int(base_damage * 0.85)  # 15% damage reduction at long range

            self.target.take_damage(base_damage)

        # Play attack sound
        if self.sfx_attack:
            self.sfx_attack.play()

    def end_attack_sequence(self):
        """End the attack sequence and return to normal behavior"""

        # IMMEDIATELY face the player when attack ends (if we still have a target)
        if self.target:
            self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)
        else:
            self.facing_direction_override = None

        self.is_in_attack_sequence = False
        self.attack_frame_timer = 0
        self.has_fired_shot = False
        self.state = "idle"

    def move_towards_player(self, player, dt):
        """Move towards player using Doom-style AI with strafing and tactical movement"""
        # Don't move if we're in an attack sequence
        if self.is_in_attack_sequence:
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Update movement timer
        self.movement_timer += dt * 1000

        # Detect if player has moved significantly (for dodging behavior)
        player_moved = False
        if self.last_player_pos:
            player_move_dist = math.hypot(player.x - self.last_player_pos[0],
                                          player.y - self.last_player_pos[1])
            if player_move_dist > 32:  # Player moved significantly
                player_moved = True
                self.dodge_timer = 500  # Start dodging for 500ms

        self.last_player_pos = (player.x, player.y)

        # Update dodge timer
        if self.dodge_timer > 0:
            self.dodge_timer -= dt * 1000

        # Change movement mode periodically or when reaching destination
        if (self.movement_timer >= self.movement_duration or
                (self.movement_mode == "direct" and dist < 80)):
            self.choose_new_movement_mode(dist)
            self.movement_timer = 0

        # Calculate base direction to player
        base_dx = dx / dist
        base_dy = dy / dist

        # Choose movement based on current mode
        move_dx, move_dy = self.calculate_movement_direction(base_dx, base_dy, dist, player_moved, dt)

        # Apply movement
        move_speed = self.speed * dt * 60

        # Vary speed based on movement mode
        if self.movement_mode == "strafe":
            move_speed *= 0.8  # Slightly slower when strafing
        elif self.movement_mode == "circle":
            move_speed *= 0.9
        elif self.dodge_timer > 0:
            move_speed *= 1.2  # Faster when dodging

        move_x = move_dx * move_speed
        move_y = move_dy * move_speed

        # Try movement with fallback if blocked
        old_x, old_y = self.x, self.y
        self.move(move_x, move_y)

        # If movement was blocked, try a different approach
        if self.x == old_x and self.y == old_y and move_speed > 0:
            # Try strafing instead
            self.movement_mode = "strafe"
            self.strafe_direction *= -1  # Change strafe direction
            self.movement_timer = 0

            # Try perpendicular movement
            perp_dx = -base_dy * self.strafe_direction
            perp_dy = base_dx * self.strafe_direction
            self.move(perp_dx * move_speed, perp_dy * move_speed)

    def choose_new_movement_mode(self, dist):
        """Choose a new movement mode based on distance and situation"""
        # Closer enemies tend to strafe more, distant ones approach more directly
        if dist > 400:
            # Far away - mostly direct approach with some variation
            modes = ["direct"] * 4 + ["strafe"] * 2 + ["zigzag"] * 1
        elif dist > 200:
            # Medium distance - mix of approaches
            modes = ["direct"] * 2 + ["strafe"] * 3 + ["zigzag"] * 2 + ["circle"] * 1
        else:
            # Close distance - mostly strafing and circling
            modes = ["direct"] * 1 + ["strafe"] * 4 + ["circle"] * 3 + ["zigzag"] * 2

        self.movement_mode = random.choice(modes)
        self.movement_duration = random.randint(500, 1500)

        # Update parameters for new mode
        if self.movement_mode == "strafe":
            self.strafe_direction = random.choice([-1, 1])
        elif self.movement_mode == "circle":
            self.current_movement_angle = random.uniform(0, 2 * math.pi)
        elif self.movement_mode == "zigzag":
            self.strafe_direction = random.choice([-1, 1])


    def calculate_movement_direction(self, base_dx, base_dy, dist, player_moved, dt):
        """Calculate movement direction based on current movement mode"""

        # If player just moved and we're close, try to dodge
        if player_moved and self.dodge_timer > 0 and dist < 200:
            # Dodge perpendicular to player movement
            dodge_dx = -base_dy * random.choice([-1, 1])
            dodge_dy = base_dx * random.choice([-1, 1])
            return dodge_dx, dodge_dy

        if self.movement_mode == "direct":
            # Direct approach but with some randomness
            noise_factor = 0.2
            noise_dx = (random.random() - 0.5) * noise_factor
            noise_dy = (random.random() - 0.5) * noise_factor

            # Maintain preferred distance
            if dist < self.preferred_distance * 0.8:
                # Too close, back away slightly while maintaining some forward pressure
                return (base_dx * 0.3 + noise_dx, base_dy * 0.3 + noise_dy)
            else:
                return (base_dx + noise_dx, base_dy + noise_dy)

        elif self.movement_mode == "strafe":
            # Move perpendicular to player while slowly approaching
            perp_dx = -base_dy * self.strafe_direction
            perp_dy = base_dx * self.strafe_direction

            # Mix strafe with slight approach
            approach_factor = 0.3 if dist > self.preferred_distance else -0.2
            final_dx = perp_dx * 0.8 + base_dx * approach_factor
            final_dy = perp_dy * 0.8 + base_dy * approach_factor

            # Normalize
            final_dist = math.hypot(final_dx, final_dy)
            if final_dist > 0:
                return (final_dx / final_dist, final_dy / final_dist)
            return (perp_dx, perp_dy)

        elif self.movement_mode == "zigzag":
            # FIXED: Improved zigzag pattern with unique parameters per enemy
            # Use a continuous sine wave based on time and unique frequency/phase
            time_seconds = self.movement_timer / 1000.0

            # Create a sine wave for the zigzag pattern
            zigzag_phase = (time_seconds * self.zigzag_frequency * 2 * math.pi +
                            self.zigzag_phase_offset)
            zigzag_intensity = math.sin(zigzag_phase) * self.zigzag_amplitude

            # Calculate perpendicular direction for zigzag
            perp_dx = -base_dy  # Perpendicular to player direction
            perp_dy = base_dx

            # Combine approach with zigzag movement
            final_dx = (base_dx * self.zigzag_approach_bias +
                        perp_dx * zigzag_intensity * (1 - self.zigzag_approach_bias))
            final_dy = (base_dy * self.zigzag_approach_bias +
                        perp_dy * zigzag_intensity * (1 - self.zigzag_approach_bias))

            # Add small random component to prevent perfect synchronization
            noise_factor = 0.1
            final_dx += (random.random() - 0.5) * noise_factor
            final_dy += (random.random() - 0.5) * noise_factor

            # Normalize the final direction
            final_dist = math.hypot(final_dx, final_dy)
            if final_dist > 0:
                return (final_dx / final_dist, final_dy / final_dist)
            return (base_dx, base_dy)

        elif self.movement_mode == "circle":
            # FIXED: Improved circular movement with unique parameters
            # Update angle based on individual rotation speed and phase offset
            angle_increment = self.circle_rotation_speed * dt
            self.current_movement_angle += angle_increment

            # Apply phase offset for desynchronization
            actual_angle = self.current_movement_angle + self.circle_phase_offset

            # Calculate circular movement
            circle_dx = math.cos(actual_angle)
            circle_dy = math.sin(actual_angle)

            # Dynamic radius based on distance and personal preference
            target_radius = self.preferred_distance * self.circle_radius_preference

            # Mix with approach/retreat based on distance to maintain preferred radius
            if dist > target_radius * 1.3:
                # Too far, approach while circling
                mix_factor = 0.6
                final_dx = circle_dx * (1 - mix_factor) + base_dx * mix_factor
                final_dy = circle_dy * (1 - mix_factor) + base_dy * mix_factor
            elif dist < target_radius * 0.7:
                # Too close, retreat while circling
                mix_factor = 0.4
                final_dx = circle_dx * (1 - mix_factor) - base_dx * mix_factor
                final_dy = circle_dy * (1 - mix_factor) - base_dy * mix_factor
            else:
                # Good distance, just circle with slight approach bias
                approach_bias = 0.1
                final_dx = circle_dx * (1 - approach_bias) + base_dx * approach_bias
                final_dy = circle_dy * (1 - approach_bias) + base_dy * approach_bias

            # Add formation spreading - try to avoid being at the same angle as other enemies
            # This creates natural spacing around the player
            spread_angle = self.formation_angle_preference
            spread_dx = math.cos(spread_angle) * 0.15
            spread_dy = math.sin(spread_angle) * 0.15

            final_dx += spread_dx
            final_dy += spread_dy

            # Normalize
            final_dist = math.hypot(final_dx, final_dy)
            if final_dist > 0:
                return (final_dx / final_dist, final_dy / final_dist)
            return (circle_dx, circle_dy)

        # Fallback to direct approach
        return (base_dx, base_dy)

    def attack(self):
        """Legacy attack method - now handled by attack sequence"""
        # This method is kept for compatibility but the new sequence system handles attacks
        if not self.is_in_attack_sequence:
            self.start_attack_sequence()

    def can_see_target(self):
        """Proper line of sight check - enemies can't see through walls"""
        if not self.target:
            return False

        # Check basic distance first
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.vision_range:
            return False

        # Use proper line of sight raycast - this should block vision through walls
        has_los = self.has_line_of_sight(self.target)
        return has_los

    def patrol(self, dt):
        """Patrol behavior when not alerted"""
        # Don't patrol if we're in an attack sequence
        if self.is_in_attack_sequence:
            return

        self.patrol_timer += dt

        # Change direction every 2-4 seconds randomly
        if self.patrol_timer > random.randint(2000, 4000):
            self.patrol_timer = 0
            # Choose a new random direction
            angle = random.uniform(0, 2 * math.pi)
            self.patrol_dir = pg.Vector2(math.cos(angle), math.sin(angle))

        # Move in patrol direction at slower speed
        move_speed = self.speed * 0.3 * dt * 60  # Much slower patrol
        move_x = self.patrol_dir.x * move_speed
        move_y = self.patrol_dir.y * move_speed

        # Check if we can move in this direction
        old_x, old_y = self.x, self.y
        self.move(move_x, move_y)

        if self.x != old_x or self.y != old_y:
            self.state = "move"
        else:
            # Hit a wall, choose new direction immediately
            self.patrol_timer = 4000
            self.state = "idle"

    def drop_loot(self):
        # loot = AmmoPickup(self.x, self.y, ammo_type="shells", amount=4,
        #                sprite_path="assets/pickups/ammo/ammo_fourshells.png", label="4 SHELLS")
        loot = WeaponPickup(self.x, self.y, "shotgun",
                          sprite_path="assets/pickups/weapons/shotgun.png", ammo_type = "shells" , amount = 8)
        loot.dropped_by_enemy = True
        self.level.pickups.append(loot)

    def take_damage(self, amount, splash=False, direct_hit=True):
        if not self.alive:
            print("hello")
            return

        # Taking damage always alerts the enemy (like Doom)
        self.is_alerted = True

        # Brief pain state - interrupt current action
        if self.is_in_attack_sequence:
            # Pain can interrupt attack sequence (like in Doom)
            self.end_attack_sequence()

        # Call the parent's take_damage method to handle hit state and animation
        super().take_damage(amount, splash, direct_hit)