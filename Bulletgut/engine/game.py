import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE
from engine.raycaster import Raycaster
from entities.player import Player
from engine.level import Level


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption('Bulletgut : The Oblivara Incident')
        self.clock = pg.time.Clock()
        self.running = True

        # Lock mouse inside the window and hide it
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)

        #TODO : Add player, levels, HUD, etc.
        self.level = Level("assets/maps/test_level.tmx")
        self.raycaster = Raycaster(self.level)
        spawn_x, spawn_y = self.level.spawn_point
        self.player = Player(spawn_x, spawn_y)
        self.enemies = []
        self.mouse_dx = 0

        # Système d'armes
        self.projectiles = []

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

        # Handle input
        keys = pg.key.get_pressed()
        self.player.handle_inputs(keys, dt, self.mouse_dx, self.level)

        for door in self.level.doors:
            door.update(dt)

        for enemy in self.level.enemies:
            enemy.update(self.player, dt)

        if self.player.weapon:
            self.player.weapon.update(dt)

        updated_projectiles = []
        for projectile in self.projectiles:
            if projectile.update(dt):
                updated_projectiles.append(projectile)
        self.projectiles = updated_projectiles


    def draw(self):
        self.screen.fill((0, 0, 0))
        self.raycaster.cast_rays(self.screen, self.player, self.level.floor_color)
        self.raycaster.render_enemies(self.screen, self.player, self.level.enemies)

        if self.player.weapon:
            self.player.weapon.render(self.screen)

        pg.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()