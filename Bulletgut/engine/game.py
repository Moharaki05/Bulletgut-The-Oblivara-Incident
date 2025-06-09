import math
import random
import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE, HUD_HEIGHT
from engine.raycaster import Raycaster
from entities.player import Player
from engine.level import Level
from ui.hud import HUD


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.render_surface = self.screen.subsurface((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True

        # Lock mouse inside the window and hide it
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        #TODO : Add player, levels, HUD, etc.
        self.level = Level("assets/maps/test_level.tmx")
        self.level.game = self
        spawn_x, spawn_y = self.level.spawn_point
        self.player = Player(spawn_x, spawn_y)
        self.raycaster = Raycaster(self.level, self.player)
        self.enemies = self.level.enemies
        self.mouse_dx = 0

        self.crosshair_enabled = True
        self.crosshair_image = pg.image.load("assets/ui/crosshair.png").convert_alpha()
        self.crosshair_image = pg.transform.scale(self.crosshair_image, (20, 20))  # Ajuster la taille

        # Système d'armes
        self.projectiles = []
        self.effects=[]

        # Initialiser les armes
        self.player.initialize_weapons(self)

        self.restart_anim_col_width = 4
        num_cols = SCREEN_WIDTH // self.restart_anim_col_width
        self.restart_anim_columns = [0] * num_cols
        self.restart_anim_speeds = [random.randint(16, 32) for _ in range(num_cols)]
        self.restart_anim_surface = None
        self.restart_anim_in_progress = False
        self.restart_anim_done = False

        self.take_restart_screenshot = False
        self.pending_restart = False
        self.has_restarted = False

        # UI
        self.hud = HUD(self.screen)

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
                        # self.restart_anim_columns = [0] * (SCREEN_WIDTH // self.restart_anim_col_width)
                        # self.restart_anim_speeds = [random.randint(8, 20) for _ in self.restart_anim_columns]
                if event.button == 4:  # Molette vers le haut
                    self.player.switch_weapon(-1)
                elif event.button == 5:  # Molette vers le bas
                    self.player.switch_weapon(1)
            elif event.type == pg.MOUSEBUTTONUP:  # Ajout de cette condition
                if event.button == 1:
                    # Arrêter le tir quand le bouton est relâché
                    if self.player.weapon:
                        self.player.weapon.release_trigger()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_e:
                    for door in self.level.doors:
                        if self.is_near_door(door):
                            door.toggle()
                # Debug events
                if event.key == pg.K_ESCAPE:
                    self.running = False
                # if event.key == pg.K_p:
                #     self.player.take_damage(10)


    def is_near_door(self, door):
        px, py = self.player.get_position()
        dx = px - (door.grid_x + 0.5) * TILE_SIZE
        dy = py - (door.grid_y + 0.5) * TILE_SIZE
        dist_squared = dx * dx + dy * dy
        return dist_squared <= (TILE_SIZE * 2.1) ** 2  # Adjust 1.1 as needed

    def update(self):
        #later: update player, enemies, projectiles, etc.
        dt = self.clock.tick(FPS) / 1000 # Delta time in seconds
        pg.display.set_caption(f"Bulletgut : The Oblivara Incident - FPS: {self.clock.get_fps():.2f}")

        if self.restart_anim_in_progress:
            self.update_restart_transition()

        if self.has_restarted:
            self.reload_level()
            self.pending_restart = False
            self.restart_anim_in_progress = False
            return

        # Handle input
        keys = pg.key.get_pressed()
        self.player.handle_inputs(keys, dt, self.mouse_dx, self.level, self)
        if self.player.damage_flash_timer > 0:
            self.player.damage_flash_timer = max(0.0, self.player.damage_flash_timer - dt)

        for pickup in self.level.pickups:
            pickup.update(self.player, self)

        for door in self.level.doors:
            door.update(dt)

        for enemy in self.level.enemies:
            enemy.update(self.player, dt)

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
        self.draw_restart_transition()

        pg.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()

    def _render_projectiles(self):
        for projectile in self.projectiles:
            # Calcule position relative au joueur
            dx = projectile.x - self.player.x
            dy = projectile.y - self.player.y

            # Calcule l'angle relatif entre projectile et direction du joueur
            rel_angle = math.atan2(dy, dx) - self.player.angle
            rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi  # Normalisation [-π, π]

            # Ne pas dessiner si hors champ de vision
            if abs(rel_angle) > self.raycaster.fov / 2:
                continue

            projectile.render(self.render_surface, self.raycaster)

    def reload_level(self):
        self.level = Level("assets/maps/test_level.tmx")
        spawn_x, spawn_y = self.level.spawn_point
        self.player = Player(spawn_x, spawn_y)
        self.player.initialize_weapons(self)
        self.raycaster = Raycaster(self.level, self.player)
        self.projectiles.clear()
        self.effects.clear()
        self.enemies.clear()
        self.hud.messages.has_death_message = False

        self.restart_anim_col_width = 4
        num_cols = SCREEN_WIDTH // self.restart_anim_col_width
        self.restart_anim_columns = [0] * num_cols
        self.restart_anim_speeds = [random.randint(8, 20) for _ in range(num_cols)]
        self.restart_anim_done = False
        self.has_restarted = False
        self.restart_anim_in_progress = False

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