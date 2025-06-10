import math
import random
import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE, HUD_HEIGHT
from engine.raycaster import Raycaster
from entities.pickups.key_pickup import KeyPickup
from entities.pickups.weapon_pickup import WeaponPickup
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

        self.is_first_level = True
        self.player = None
        self.level = None
        self.level_name = ""
        self.raycaster = None
        self.enemies = []
        self.projectiles = []
        self.effects = []
        self.player_state = None
        self.enemies_killed = 0
        self.initial_item_count = 0
        self.initial_enemy_count = 0
        self.items_collected = 0

        self.mouse_dx = 0

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
        self.intermission_entry_started = False

        self.update_statistics()

    def load_level(self, path):
        # Sauvegarder l'état du joueur avant de charger le nouveau niveau (sauf si c'est le premier niveau)
        if not self.is_first_level and self.player and self.player.alive:
            self.save_player_state()

        self.level = Level(path)
        self.level_name = self.level.get_map_name_from_tmx(path)
        self.level.game = self
        spawn_x, spawn_y = self.level.spawn_point
        self.player = Player(spawn_x, spawn_y)
        self.player.initialize_weapons(self)

        # Restaurer l'état du joueur si ce n'est pas le premier niveau
        if not self.is_first_level:
            self.restore_player_state()
        else:
            self.is_first_level = False

        self.raycaster = Raycaster(self.level, self.player)
        self.enemies = self.level.enemies
        self.projectiles = []
        self.effects = []

    def save_player_state(self):
        """Sauvegarde l'état du joueur (armes, munitions, armure)"""
        if self.player:
            self.player_state = {
                'health': self.player.health,
                'armor': self.player.armor,
                'ammo': self.player.ammo.copy(),
                'weapons': self.player.weapons.copy(),
                'current_weapon_index': self.player.current_weapon_index,
            }

    def restore_player_state(self):
        """Restaure l'état du joueur sauvegardé"""
        if self.player_state and self.player:
            self.player.health = self.player_state['health']
            self.player.armor = self.player_state['armor']
            self.player.ammo = self.player_state['ammo'].copy()
            self.player.weapons = self.player_state['weapons'].copy()
            self.player.current_weapon_index = self.player_state['current_weapon_index']

            # Remettre l'arme courante
            if 0 <= self.player.current_weapon_index < len(self.player.weapons):
                self.player.weapon = self.player.weapons[self.player.current_weapon_index]
            else:
                for i, weapon in enumerate(self.player.weapons):
                    if weapon is not None:
                        self.player.current_weapon_index = i
                        self.player.weapon = weapon
                        break

    def reset_player_state(self):
        """Remet à zéro l'état du joueur (utilisé lors de la mort)"""
        self.player_state = None
        self.is_first_level = True
        print("[DEBUG] Player state reset due to death")

    def update_statistics(self):
        """Initialise les statistiques pour le niveau actuel"""
        self.enemies_killed = 0
        self.initial_enemy_count = len(
            [enemy for enemy in self.enemies if enemy.alive])  # Compter seulement les ennemis vivants
        self.items_collected = 0

        # Compter seulement les items de type "health", "armor", etc. (pas les clés, armes, munitions)
        self.initial_item_count = 0
        for pickup in self.level.pickups:
            if hasattr(pickup, 'pickup_type'):
                # Exclure les munitions, armes et clés du comptage
                if pickup.pickup_type not in ['weapon', 'key'] and not pickup.picked_up:
                    self.initial_item_count += 1
            # Pour les pickups sans pickup_type, vérifier le type de classe
            elif not isinstance(pickup, (WeaponPickup, KeyPickup)) and not pickup.picked_up:
                self.initial_item_count += 1

        print(f"[DEBUG] Level loaded - Enemies: {self.initial_enemy_count}, Items: {self.initial_item_count}")

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
                        print("[DEBUG] CLICK DETECTED - STARTING RESTART ANIMATION")
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
                    # Gérer ENTER seulement si l'intermission peut accepter l'input
                    if self.show_intermission and self.intermission_screen.can_accept_input():
                        self.start_level_transition()
                if event.key == pg.K_ESCAPE:
                    self.running = False

    def start_level_transition(self):
        """Démarre la transition vers le niveau suivant"""
        # Charger le niveau suivant en arrière-plan
        self.level_manager.advance()
        self.load_level(self.level_manager.get_current())
        self.update_statistics()

        # Rendre le nouveau niveau une fois pour capturer l'écran
        self.render_game_without_intermission()
        next_level_screen = self.screen.copy()

        # Démarrer la transition de sortie avec l'écran du nouveau niveau
        self.intermission_screen.start_exit_transition(next_level_screen)

    def is_near_door(self, door):
        px, py = self.player.get_position()
        dx = px - (door.grid_x + 0.5) * TILE_SIZE
        dy = py - (door.grid_y + 0.5) * TILE_SIZE
        return dx * dx + dy * dy <= (TILE_SIZE * 2.1) ** 2

    def update(self):
        dt = self.clock.tick(FPS) / 1000
        pg.display.set_caption(f"Bulletgut : The Oblivara Incident - FPS: {self.clock.get_fps():.2f}")

        if self.has_restarted:
            self.reload_level()
            self.pending_restart = False
            self.restart_anim_in_progress = False
            return

        if self.restart_anim_in_progress:
            self.update_restart_transition()
            return

        # Gérer le début de l'intermission
        if self.level_complete and not self.intermission_entry_started:
            self.render_game_without_intermission()
            self.intermission_screen.start_entry_transition(self.screen)
            self.intermission_entry_started = True
            self.show_intermission = True

        # Gérer la fin de l'intermission
        if self.show_intermission and self.intermission_screen.is_exit_transition_complete():
            # Transition terminée, retourner au jeu normal
            self.show_intermission = False
            self.intermission_entry_started = False
            self.level_complete = False
            self.intermission_screen.reset()
            return

        if self.show_intermission:
            self.intermission_screen.update(dt)
            return

        # Logique de jeu normale
        keys = pg.key.get_pressed()
        self.player.handle_inputs(keys, dt, self.mouse_dx, self.level, self)
        if self.player.damage_flash_timer > 0:
            self.player.damage_flash_timer = max(0.0, self.player.damage_flash_timer - dt)

        # Mettre à jour les pickups et compter les items SEULEMENT quand ils sont ramassés
        # Remplacer cette section dans la méthode update():
        for pickup in self.level.pickups:
            was_picked_up = pickup.picked_up
            pickup.update(self.player, self)
            # Compter l'item seulement au moment où il vient d'être ramassé
            # ET seulement si ce n'est pas une munition, arme ou clé
            if not was_picked_up and pickup.picked_up:
                if getattr(pickup, 'dropped_by_enemy', False):
                    continue
                if hasattr(pickup, 'pickup_type'):
                    if pickup.pickup_type not in ['weapon', 'key']:
                        self.items_collected += 1
                        print(f"[DEBUG] Item collected! Total: {self.items_collected}/{self.initial_item_count}")
                # Pour les pickups sans pickup_type, vérifier le type de classe
                elif not isinstance(pickup, (WeaponPickup, KeyPickup)):
                    self.items_collected += 1
                    print(f"[DEBUG] Item collected! Total: {self.items_collected}/{self.initial_item_count}")

        for door in self.level.doors:
            door.update(dt)

        # Mettre à jour les ennemis et compter les morts SEULEMENT quand ils meurent
        for enemy in self.level.enemies:
            enemy.update(self.player, dt)

            # ⭐ NOUVEAU : Vérifier si cet ennemi vient de mourir
            if hasattr(enemy, 'just_died') and enemy.just_died:
                self.enemies_killed += 1
                enemy.just_died = False  # Marquer comme traité pour éviter de compter plusieurs fois
                print(f"[DEBUG] Enemy killed! Total: {self.enemies_killed}/{self.initial_enemy_count}")

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
                                            self.items_collected, self.initial_item_count, self.level_name)
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
            print(f"[LEVEL] Level completed! Stats - Enemies: {self.enemies_killed}/{self.initial_enemy_count}, Items: {self.items_collected}/{self.initial_item_count}")

    def reload_level(self):
        self.reset_player_state()  # Remise à zéro pour éviter de restaurer un ancien état
        self.load_level(self.level_manager.get_current())
        self.update_statistics()

        self.restart_anim_col_width = 4
        num_cols = SCREEN_WIDTH // self.restart_anim_col_width
        self.restart_anim_columns = [0] * num_cols
        self.restart_anim_speeds = [random.randint(8, 20) for _ in range(num_cols)]
        self.restart_anim_done = False
        self.has_restarted = False
        self.restart_anim_in_progress = False

