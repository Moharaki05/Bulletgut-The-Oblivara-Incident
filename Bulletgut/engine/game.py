import math
import random
import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE, HUD_HEIGHT
from engine.raycaster import Raycaster
from entities.player import Player
from engine.level import Level
from ui.hud import HUD
from engine.level_manager import LevelManager
from ui.intermission import IntermissionScreen

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.render_surface = self.screen.subsurface((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True

        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        self.level_manager = LevelManager([
            "assets/maps/test_level.tmx",
            "assets/maps/test_level2.tmx"
        ])
        self.load_level(self.level_manager.get_current())

        self.crosshair_enabled = True
        self.crosshair_image = pg.image.load("assets/ui/crosshair.png").convert_alpha()
        self.crosshair_image = pg.transform.scale(self.crosshair_image, (20, 20))

        self.restart_anim_col_width = 4
        num_cols = SCREEN_WIDTH // self.restart_anim_col_width
        self.restart_anim_columns = [0] * num_cols
        self.restart_anim_speeds = [random.randint(16, 32) for _ in range(num_cols)]
        self.restart_anim_surface = None
        self.restart_anim_in_progress = False
        self.restart_anim_done = False

        self.pending_restart = False
        self.has_restarted = False
        self.pending_level_change = False
        self.ready_to_load_level = False

        self.hud = HUD(self.screen)
        self.intermission_screen = IntermissionScreen()
        self.level_complete = False
        self.show_intermission = False
        self.intermission_transition_started = False

        self.update_statistics()

    def load_level(self, path):
        self.level = Level(path)
        self.level.game = self
        spawn_x, spawn_y = self.level.spawn_point
        self.player = Player(spawn_x, spawn_y)
        self.player.initialize_weapons(self)
        self.raycaster = Raycaster(self.level, self.player)
        self.enemies = self.level.enemies
        self.projectiles = []
        self.effects = []

    def update_statistics(self):
        self.enemies_killed = 0
        self.initial_enemy_count = len(self.enemies)
        self.items_collected = 0
        self.initial_item_count = len([pickup for pickup in self.level.pickups
                                       if hasattr(pickup, 'pickup_type') and pickup.pickup_type != 'ammo'])

    def handle_events(self):
        self.mouse_dx = 0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEMOTION:
                self.mouse_dx = event.rel[0]
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.player.alive:
                        if self.player.weapon:
                            self.player.weapon.fire()
                    elif not self.restart_anim_in_progress:
                        self.hud.render(self.player, self)
                        self.restart_anim_surface = self.screen.copy()
                        self.restart_anim_in_progress = True
                        self.restart_anim_done = False
                        self.has_restarted = False
                if event.button == 4:
                    self.player.switch_weapon(-1)
                elif event.button == 5:
                    self.player.switch_weapon(1)
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.player.weapon:
                        self.player.weapon.release_trigger()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_e:
                    for door in self.level.doors:
                        if self.is_near_door(door):
                            door.toggle(self)
                            break
                    else:
                        for level_exit in self.level.level_exits:
                            if level_exit.is_player_near(self.player):
                                if level_exit.activate():
                                    self.trigger_level_complete()
                                break
                if event.key == pg.K_RETURN:
                    if self.show_intermission and self.intermission_screen.is_transition_complete():
                        self.pending_level_change = True
                        self.level_manager.advance()
                        self.load_level(self.level_manager.get_current())
                        self.update_statistics()
                        self.render_game_without_intermission()
                        self.restart_anim_surface = self.screen.copy()
                        self.restart_anim_columns = [0] * len(self.restart_anim_columns)
                        self.restart_anim_speeds = [random.randint(16, 32) for _ in self.restart_anim_speeds]
                        self.restart_anim_in_progress = True
                        self.restart_anim_done = False
                        self.has_restarted = False
                        self.show_intermission = False
                        self.intermission_transition_started = False
                        self.level_complete = False
                if event.key == pg.K_ESCAPE:
                    self.running = False

    def is_near_door(self, door):
        px, py = self.player.get_position()
        dx = px - (door.grid_x + 0.5) * TILE_SIZE
        dy = py - (door.grid_y + 0.5) * TILE_SIZE
        return dx * dx + dy * dy <= (TILE_SIZE * 2.1) ** 2

    def update(self):
        dt = self.clock.tick(FPS) / 1000
        pg.display.set_caption(f"Bulletgut : The Oblivara Incident - FPS: {self.clock.get_fps():.2f}")

        if self.restart_anim_in_progress:
            self.update_restart_transition()

        if self.level_complete and not self.intermission_transition_started:
            self.render_game_without_intermission()
            self.intermission_screen.start_transition(self.screen)
            self.intermission_transition_started = True
            self.show_intermission = True

        if self.show_intermission:
            self.intermission_screen.update(dt)
            return

        keys = pg.key.get_pressed()
        self.player.handle_inputs(keys, dt, self.mouse_dx, self.level, self)
        if self.player.damage_flash_timer > 0:
            self.player.damage_flash_timer = max(0.0, self.player.damage_flash_timer - dt)

        for pickup in self.level.pickups:
            pickup.update(self.player, self)
            if pickup.picked_up and hasattr(pickup, 'pickup_type') and pickup.pickup_type != 'ammo':
                self.items_collected += 1

        for door in self.level.doors:
            door.update(dt)

        for enemy in self.level.enemies:
            was_alive = enemy.alive
            enemy.update(self.player, dt)
            if was_alive and not enemy.alive:
                self.enemies_killed += 1

        if not self.player.alive and not self.hud.messages.has_death_message:
            self.hud.messages.add("YOU DIED. CLICK TO RESTART.", (255, 0, 0))
            self.hud.messages.has_death_message = True

        if self.player.weapon:
            self.player.weapon.update(dt)
            if hasattr(self.player.weapon, 'update_line_detection'):
                self.player.weapon.update_line_detection()

        self.projectiles = [p for p in self.projectiles if p.update(dt)]
        self.effects = [e for e in self.effects if e.update()]

    def render(self):
        if self.show_intermission:
            self.intermission_screen.render(self.screen, self.enemies_killed, self.initial_enemy_count,
                                            self.items_collected, self.initial_item_count)
        else:
            self.render_game_without_intermission()

        self.draw_restart_transition()
        pg.display.flip()

    def render_game_without_intermission(self):
        self.screen.fill((0, 0, 0))
        self.raycaster.cast_rays(self.render_surface, self.player, self.level.floor_color)
        self.raycaster.render_pickups(self.render_surface, self.player, self.level.pickups)
        self.raycaster.render_enemies(self.render_surface, self.player, self.level.enemies)

        if self.player.weapon:
            self.player.weapon.render(self.render_surface)
            if hasattr(self.player.weapon, 'render_detection_line'):
                self.player.weapon.render_detection_line(self.render_surface)

        self._render_projectiles()

        for effect in self.effects:
            effect.render(self.render_surface, self.raycaster, self.player)

        if self.crosshair_enabled:
            center_x = SCREEN_WIDTH // 2 - self.crosshair_image.get_width() // 2
            center_y = (SCREEN_HEIGHT - HUD_HEIGHT) // 2 - self.crosshair_image.get_height() // 2
            self.screen.blit(self.crosshair_image, (center_x, center_y))

        if self.player.damage_flash_timer > 0:
            alpha = int(255 * (self.player.damage_flash_timer / 0.2))
            flash_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.set_alpha(alpha)
            flash_surface.fill((255, 0, 0))
            self.screen.blit(flash_surface, (0, 0))

        self.hud.render(self.player, self)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()

    def _render_projectiles(self):
        for projectile in self.projectiles:
            dx = projectile.x - self.player.x
            dy = projectile.y - self.player.y
            rel_angle = math.atan2(dy, dx) - self.player.angle
            rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi
            if abs(rel_angle) > self.raycaster.fov / 2:
                continue
            projectile.render(self.render_surface, self.raycaster)

    def draw_restart_transition(self):
        if not self.restart_anim_surface:
            return

        all_done = True
        col_width = self.restart_anim_col_width
        for x in range(0, SCREEN_WIDTH, col_width):
            col_index = x // col_width
            if self.restart_anim_columns[col_index] < SCREEN_HEIGHT:
                self.restart_anim_columns[col_index] += self.restart_anim_speeds[col_index]
                all_done = False

            remaining_height = SCREEN_HEIGHT - self.restart_anim_columns[col_index]
            if remaining_height > 0:
                source_rect = pg.Rect(x, self.restart_anim_columns[col_index], col_width, remaining_height)
                dest_pos = (x, self.restart_anim_columns[col_index])
                column = self.restart_anim_surface.subsurface(source_rect)
                self.screen.blit(column, dest_pos)

        if all_done and not self.restart_anim_done:
            self.restart_anim_done = True

    def update_restart_transition(self):
        self.draw_restart_transition()
        if self.restart_anim_done and not self.has_restarted:
            self.has_restarted = True

    def trigger_level_complete(self):
        if not self.level_complete:
            self.level_complete = True
            print("[LEVEL] Level completed!")
