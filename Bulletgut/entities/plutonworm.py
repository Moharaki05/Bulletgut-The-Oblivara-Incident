import math
import random
import pygame as pg
from entities.enemy_base import EnemyBase
from utils.assets import load_sound

class PlutonWorm(EnemyBase):
    def __init__(self, x, y, level):
        super().__init__(x, y, level, "assets/sprites/enemies/plutonworm")

        # PlutonWorm-specific stats (like Doom Pinky Demon)
        self.speed_backup = 0.0
        self.max_health = 150  # Pinky has 150 HP in Doom
        self.health = self.max_health
        self.damage = random.randint(4, 40)  # 4-10 * 4 damage range like Doom Pinky
        self.speed = 1.5  # Fast like Pinky Demon
        self.attack_delay = 1200  # Quick melee attacks
        self.attack_cooldown = 0

        # Vision and detection - shorter range than gunner but still decent
        self.vision_range = 600  # Medium range vision
        self.wake_up_distance = 700  # Wake up when close
        self.alert_distance = 80  # Melee range

        # Melee attack specific
        self.min_attack_range = 0
        self.max_attack_range = 80  # Close combat only
        self.melee_hitbox = self.rect.inflate(60, 60)  # Larger melee range

        # AI states
        self.is_alerted = False
        self.charge_mode = False  # Special charging behavior
        self.charge_timer = 0
        self.charge_duration = 2000  # How long to charge for
        self.charge_cooldown = 0
        self.charge_delay = 3000  # Time between charges

        # Pack behavior - PlutonWorms are more dangerous in groups
        self.pack_behavior = True
        self.nearby_worms = []  # Other worms nearby
        self.pack_bonus_damage = 1.0  # Damage multiplier when in pack
        self.pack_radius = 200  # Distance to consider "pack"

        # Movement AI - more aggressive than gunner
        self.movement_timer = 0
        self.movement_duration = random.randint(300, 800)  # Shorter, more erratic
        self.current_movement_angle = 0
        self.preferred_distance = random.randint(40, 80)  # Prefers close combat
        self.dodge_timer = 0
        self.last_player_pos = None
        self.movement_mode = "direct"

        # Unique movement parameters for pack spreading
        self.formation_angle_preference = random.uniform(0, 2 * math.pi)
        self.spread_factor = random.uniform(0.9, 1.3)
        self.aggression_level = random.uniform(0.7, 1.0)  # How aggressive this worm is

        # Attack animation timing
        self.attack_animation_duration = 600  # Faster than gunner
        self.attack_frame_timer = 0
        self.attack_windup_time = 200  # Quick windup
        self.has_performed_attack = False
        self.is_in_attack_sequence = False

        # Randomize initial cooldowns to prevent synchronization
        self.attack_cooldown = random.randint(0, self.attack_delay)
        self.charge_cooldown = random.randint(0, self.charge_delay)

        # Sound effects
        try:
            self.sfx_attack = load_sound("assets/sounds/enemies/worm_bite.wav")
        except:
            self.sfx_attack = None

        try:
            self.sfx_charge = load_sound("assets/sounds/enemies/worm_charge.wav")
        except:
            self.sfx_charge = None

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
        if self.charge_cooldown > 0:
            self.charge_cooldown -= dt * 1000

        # Handle attack sequence timing
        if self.is_in_attack_sequence:
            self.attack_frame_timer += dt * 1000

            # Perform melee attack at the right moment
            if not self.has_performed_attack and self.attack_frame_timer >= self.attack_windup_time:
                self.perform_melee_attack()
                self.has_performed_attack = True

            # Check if attack animation is complete
            if self.attack_frame_timer >= self.attack_animation_duration:
                self.end_attack_sequence()

            self.update_animation(dt)
            return

        # Handle hit state FIRST
        if self.state == "hit":
            self.hit_timer += dt
            if self.hit_timer >= self.hit_duration:
                self.hit_timer = 0.0
                self.state = self.previous_state or "idle"
                # Being hit interrupts charge mode
                if self.charge_mode:
                    self.end_charge()

            self.update_animation(dt)
            return

        # Handle charge mode
        if self.charge_mode:
            self.charge_timer += dt * 1000
            if self.charge_timer >= self.charge_duration:
                self.end_charge()
            else:
                # Charge directly at player at high speed
                self.charge_towards_player(player, dt)
                self.state = "move"
                self.update_animation(dt)
                return

        # Normal AI behavior
        can_see_player = self.can_see_target() and dist <= self.vision_range

        # Wake up behavior - very aggressive once alerted
        if can_see_player and not self.is_alerted:
            self.is_alerted = True
            # Slight delay before reacting
            reaction_delay = random.randint(100, 400)
            self.attack_cooldown = max(self.attack_cooldown, reaction_delay)

        # Update pack behavior
        self.update_pack_behavior()

        if self.is_alerted and can_see_player:
            # Always face the player when alerted and can see them
            if not self.is_in_attack_sequence:
                self.facing_direction_override = self.get_facing_direction(player.x, player.y)

            # Check for charge opportunity (medium range)
            if (not self.charge_mode and self.charge_cooldown <= 0 and
                    120 < dist < 400 and random.random() < 0.3):
                self.start_charge()
                return

            # Check for melee attack (close range)
            if dist <= self.max_attack_range and self.attack_cooldown <= 0:
                self.start_attack_sequence()
            else:
                # Move towards player aggressively
                if dist > self.alert_distance:
                    self.move_towards_player_aggressively(player, dt)
                    self.state = "move"
                else:
                    self.state = "idle"

        elif self.is_alerted:
            # Lost sight but still alerted - move to last known position
            if hasattr(self, 'last_seen_player_pos') and self.last_seen_player_pos:
                chase_dist = math.hypot(self.last_seen_player_pos.x - self.x,
                                        self.last_seen_player_pos.y - self.y)
                if chase_dist > 32:
                    self.facing_direction_override = self.get_facing_direction(
                        self.last_seen_player_pos.x, self.last_seen_player_pos.y)
                    self.move_towards(self.last_seen_player_pos.x, self.last_seen_player_pos.y, dt)
                    self.state = "move"
                else:
                    self.last_seen_player_pos = None
                    self.patrol(dt)
            else:
                self.patrol(dt)
        else:
            # Not alerted - patrol
            if can_see_player:
                self.is_alerted = True
            else:
                self.patrol(dt)

        # Remember last seen player position
        if can_see_player:
            self.last_seen_player_pos = pg.Vector2(player.x, player.y)

        self.update_animation(dt)

    def start_charge(self):
        """Start charging towards the player"""
        if not self.target:
            return

        self.charge_mode = True
        self.charge_timer = 0
        self.speed_backup = self.speed
        self.speed *= 2.5  # Much faster during charge

        # Set charge cooldown for after charge ends
        self.charge_cooldown = self.charge_delay + random.randint(-500, 1000)

        # Face the player
        self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)

        if self.sfx_charge:
            self.sfx_charge.play()

    def end_charge(self):
        """End the charge sequence"""
        self.charge_mode = False
        self.charge_timer = 0
        if hasattr(self, 'speed_backup'):
            self.speed = self.speed_backup

    def charge_towards_player(self, player, dt):
        """Charge directly at player during charge mode"""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Normalize and move
        dx /= dist
        dy /= dist

        move_speed = self.speed * dt * 60
        move_x = dx * move_speed
        move_y = dy * move_speed

        self.move(move_x, move_y)

        # Check for collision with player during charge
        if dist <= self.max_attack_range and self.attack_cooldown <= 0:
            self.start_attack_sequence()
            self.end_charge()

    def move_towards_player_aggressively(self, player, dt):
        """Aggressive movement towards player - more direct than gunner"""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        # Update movement timer
        self.movement_timer += dt * 1000

        # Change behavior less frequently than gunner - more persistent
        if self.movement_timer >= self.movement_duration:
            self.choose_aggressive_movement_mode(dist)
            self.movement_timer = 0

        # Calculate base direction
        base_dx = dx / dist
        base_dy = dy / dist

        # More direct approach with some pack behavior
        move_dx, move_dy = self.calculate_aggressive_movement(base_dx, base_dy, dist, dt)

        # Apply movement
        move_speed = self.speed * dt * 60

        # Speed boost when close to target
        if dist < 200:
            move_speed *= 1.2

        # Pack speed bonus
        if len(self.nearby_worms) > 0:
            move_speed *= (1.0 + len(self.nearby_worms) * 0.1)

        move_x = move_dx * move_speed
        move_y = move_dy * move_speed

        # Try movement
        old_x, old_y = self.x, self.y
        self.move(move_x, move_y)

        # If blocked, try to go around obstacle
        if self.x == old_x and self.y == old_y:
            # Try perpendicular movement
            perp_dx = -base_dy
            perp_dy = base_dx
            direction = random.choice([-1, 1])
            self.move(perp_dx * direction * move_speed, perp_dy * direction * move_speed)

    def choose_aggressive_movement_mode(self, dist):
        """Choose movement mode - more aggressive than gunner"""
        if dist > 300:
            # Far away - direct approach mostly
            self.movement_mode = random.choice(["direct"] * 6 + ["zigzag"] * 2)
        elif dist > 150:
            # Medium distance - mix of direct and flanking
            self.movement_mode = random.choice(["direct"] * 4 + ["flank"] * 3 + ["zigzag"] * 1)
        else:
            # Close - direct assault
            self.movement_mode = random.choice(["direct"] * 7 + ["flank"] * 1)

        self.movement_duration = random.randint(200, 600)  # Shorter than gunner

    def calculate_aggressive_movement(self, base_dx, base_dy, dist, dt):
        """Calculate movement direction - more direct than gunner"""

        if self.movement_mode == "direct":
            # Direct approach with minimal randomness
            noise_factor = 0.1  # Less noise than gunner
            noise_dx = (random.random() - 0.5) * noise_factor
            noise_dy = (random.random() - 0.5) * noise_factor
            return (base_dx + noise_dx, base_dy + noise_dy)

        elif self.movement_mode == "flank":
            # Try to approach from the side
            perp_dx = -base_dy * random.choice([-1, 1])
            perp_dy = base_dx * random.choice([-1, 1])

            # Mix flanking with approach
            approach_factor = 0.6
            final_dx = perp_dx * (1 - approach_factor) + base_dx * approach_factor
            final_dy = perp_dy * (1 - approach_factor) + base_dy * approach_factor

            # Normalize
            final_dist = math.hypot(final_dx, final_dy)
            if final_dist > 0:
                return (final_dx / final_dist, final_dy / final_dist)
            return (base_dx, base_dy)

        elif self.movement_mode == "zigzag":
            # Simple zigzag pattern
            time_seconds = self.movement_timer / 1000.0
            zigzag_intensity = math.sin(time_seconds * 3.0) * 0.5

            perp_dx = -base_dy
            perp_dy = base_dx

            final_dx = base_dx * 0.8 + perp_dx * zigzag_intensity
            final_dy = base_dy * 0.8 + perp_dy * zigzag_intensity

            # Normalize
            final_dist = math.hypot(final_dx, final_dy)
            if final_dist > 0:
                return (final_dx / final_dist, final_dy / final_dist)
            return (base_dx, base_dy)

        # Fallback
        return (base_dx, base_dy)

    def update_pack_behavior(self):
        """Update pack behavior - worms are stronger in groups"""
        # This would be called by the game to pass nearby worms
        # For now, we'll simulate pack behavior
        pack_size = len(self.nearby_worms)

        # Damage bonus for being in a pack
        if pack_size > 0:
            self.pack_bonus_damage = 1.0 + (pack_size * 0.15)  # 15% more damage per nearby worm
        else:
            self.pack_bonus_damage = 1.0

    def start_attack_sequence(self):
        """Start melee attack sequence"""
        if self.target:
            self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)

        self.is_in_attack_sequence = True
        self.attack_frame_timer = 0
        self.has_performed_attack = False
        self.state = "attack"

        # Set attack cooldown with less variation than gunner
        base_cooldown = self.attack_delay
        variation = random.randint(-200, 300)
        self.attack_cooldown = max(800, base_cooldown + variation)

    def perform_melee_attack(self):
        """Perform the actual melee attack"""
        if not self.target:
            return

        # Check if target is in melee range
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist <= self.max_attack_range:
            # Calculate damage with pack bonus
            base_damage = random.randint(15, 25)  # Higher than gunner
            final_damage = int(base_damage * self.pack_bonus_damage * self.aggression_level)

            # Melee attacks always hit if in range
            self.target.take_damage(final_damage)

            if self.sfx_attack:
                self.sfx_attack.play()

    def end_attack_sequence(self):
        """End attack sequence"""
        if self.target:
            self.facing_direction_override = self.get_facing_direction(self.target.x, self.target.y)
        else:
            self.facing_direction_override = None

        self.is_in_attack_sequence = False
        self.attack_frame_timer = 0
        self.has_performed_attack = False
        self.state = "idle"

    def attack(self):
        """Legacy attack method for compatibility"""
        if not self.is_in_attack_sequence:
            self.start_attack_sequence()

    def patrol(self, dt):
        """Patrol behavior - more restless than gunner"""
        if self.is_in_attack_sequence or self.charge_mode:
            return

        self.patrol_timer += dt

        # Change direction more frequently than gunner
        if self.patrol_timer > random.randint(1000, 2500):
            self.patrol_timer = 0
            angle = random.uniform(0, 2 * math.pi)
            self.patrol_dir = pg.Vector2(math.cos(angle), math.sin(angle))

        # Move faster during patrol than gunner
        move_speed = self.speed * 0.4 * dt * 60
        move_x = self.patrol_dir.x * move_speed
        move_y = self.patrol_dir.y * move_speed

        old_x, old_y = self.x, self.y
        self.move(move_x, move_y)

        if self.x != old_x or self.y != old_y:
            self.state = "move"
        else:
            # Hit wall, change direction
            self.patrol_timer = 2500
            self.state = "idle"

    def can_see_target(self):
        """Line of sight check"""
        if not self.target:
            return False

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.vision_range:
            return False

        return self.has_line_of_sight(self.target)

    def drop_loot(self):
        pass

    def take_damage(self, amount, splash=False, direct_hit=True):
        """Override to handle pack behavior and aggression"""
        if not self.alive:
            return

        # Taking damage always alerts and angers the worm
        self.is_alerted = True
        self.aggression_level = min(1.0, self.aggression_level + 0.1)  # Become more aggressive

        # Interrupt charge if hit
        if self.charge_mode:
            self.end_charge()

        # Interrupt attack sequence if hit (chance based)
        if self.is_in_attack_sequence and random.random() < 0.7:
            self.end_attack_sequence()

        # Call parent's damage handling
        super().take_damage(amount, splash, direct_hit)