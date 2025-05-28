import math
import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE
from engine.raycaster import Raycaster
from entities.player import Player
from engine.level import Level


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True

        # Lock mouse inside the window and hide it
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        #TODO : Add player, levels, HUD, etc.
        self.level = Level("assets/maps/test_level.tmx")
        spawn_x, spawn_y = self.level.spawn_point
        self.player = Player(spawn_x, spawn_y)
        self.raycaster = Raycaster(self.level, self.player)
        self.enemies = []
        self.mouse_dx = 0

        self.crosshair_enabled = True
        self.crosshair_image = pg.image.load("assets/ui/crosshair.png").convert_alpha()
        self.crosshair_image = pg.transform.scale(self.crosshair_image, (20, 20))  # Ajuster la taille

        # Système d'armes
        self.projectiles = []
        self.effects=[]

        # Initialiser les armes
        self.player.initialize_weapons(self)

    def handle_events(self):
        self.mouse_dx = 0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEMOTION:
                self.mouse_dx = event.rel[0]
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if event.button == 1:
                        # Utiliser l'arme actuelle du joueur
                        if self.player.weapon:
                            self.player.weapon.fire()
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
                # Debug quit
                if event.key == pg.K_ESCAPE:
                    self.running = False

    def is_near_door(self, door):
        px, py = self.player.get_position()
        dx = px - (door.grid_x + 0.5) * TILE_SIZE
        dy = py - (door.grid_y + 0.5) * TILE_SIZE
        dist_squared = dx * dx + dy * dy
        return dist_squared <= (TILE_SIZE * 2.1) ** 2  # Adjust 1.1 as needed


    def update(self):
        #later: update player, enemies, projectiles, etc.
        dt = self.clock.tick(FPS) / 1000 # Delta time in seconds
        # print(f"FPS: {self.clock.get_fps()}")
        pg.display.set_caption(f"Bulletgut : The Oblivara Incident - FPS: {self.clock.get_fps():.2f}")

        # Handle input
        keys = pg.key.get_pressed()
        self.player.handle_inputs(keys, dt, self.mouse_dx, self.level)

        for door in self.level.doors:
            door.update(dt)

        for enemy in self.level.enemies:
            enemy.update(self.player, dt)

        if self.player.weapon:
            self.player.weapon.update(dt)

        self.projectiles = [p for p in self.projectiles if p.update(dt)]
        self.effects = [e for e in self.effects if e.update()]

    def render(self):
        self.screen.fill((0, 0, 0))
        self.raycaster.cast_rays(self.screen, self.player, self.level.floor_color)
        self.raycaster.render_enemies(self.screen, self.player, self.level.enemies)

        if self.player.weapon:
            self.player.weapon.render(self.screen)

        self._render_projectiles()

        for effect in self.effects:
            effect.render(self.screen, self.raycaster, self.player)

        if self.crosshair_enabled:
            center_x = SCREEN_WIDTH // 2 - self.crosshair_image.get_width() // 2
            center_y = SCREEN_HEIGHT // 2 - self.crosshair_image.get_height() // 2
            self.screen.blit(self.crosshair_image, (center_x, center_y))

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
            dist = math.hypot(dx, dy)

            # Calcule l'angle relatif entre projectile et direction du joueur
            rel_angle = math.atan2(dy, dx) - self.player.angle
            rel_angle = (rel_angle + math.pi) % (2 * math.pi) - math.pi  # Normalisation [-π, π]

            # Ne pas dessiner si hors champ de vision
            if abs(rel_angle) > self.raycaster.fov / 2:
                continue

            # Projette sur l'écran (même principe que dans Projectile.render)
            screen_x = int((0.5 + rel_angle / self.raycaster.fov) * self.screen.get_width())
            screen_y = self.screen.get_height() // 2  # centré verticalement

            # Dessin debug (point rouge)
            projectile.render(self.screen, self.raycaster)







