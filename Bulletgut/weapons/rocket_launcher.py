import math

import pygame as pg
from weapons.projectile_weapon import ProjectileWeapon


class RocketLauncher(ProjectileWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Rocket Launcher"
        self.damage = 100
        self.fire_rate = 1.2
        self.shot_cooldown = 1.0 / self.fire_rate
        self.ammo_type = "rockets"
        self.projectile_speed = 700
        self.projectile_lifetime = 5.0
        self.splash_damage = True
        self.splash_radius = 200

        # Paramètres de bobbing
        self.bobbing_intensity = 0.05
        self.bobbing_horizontal = 0.025
        self.bobbing_speed = 5.0

        self.animation_active = False
        self.animation_timer = 0
        self.animation_duration = 0.3  # par ex. 0.3s pour rocket

        self.pending_projectile = False
        self.projectile_delay = 0.12  # en secondes (ajuste selon le feeling)
        self.projectile_timer = 0

        # Paramètres de recul
        self.recoil_amount = 0.15
        self.recoil_recovery = 0.8
        self.current_recoil = 0

        # Ajuster la position verticale du lance-roquettes
        self.position_offset = (0, 30)  # Décalage vertical pour abaisser l'arme

        # Augmenter la taille du lance-roquettes
        self.scale_factor = 1.3  # Augmentez cette valeur pour agrandir l'arme (1.0 est la taille normale)

        # Charger les sprites
        self.load_sprites([
            "assets/weapons/rocketlauncher/RPG1.png",
            "assets/weapons/rocketlauncher/RPG2.png",
            "assets/weapons/rocketlauncher/RPG3.png",
            "assets/weapons/rocketlauncher/RPG4.png"
        ])

        self.current_sprite_index = 0
        self.current_sprite = self.sprites[0] if self.sprites else None
        self.is_firing = False

        self.projectile_front = pg.image.load("assets/weapons/projectiles/rocket/rocket_front.png").convert_alpha()
        self.projectile_back = pg.image.load("assets/weapons/projectiles/rocket/rocket_back.png").convert_alpha()

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/rocketlauncher/rocket_fire.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/rocketlauncher/empty_rpg_click.wav")
        self.explosion_sound = pg.mixer.Sound("assets/sounds/rocketlauncher/rocket_hit.wav")

    def fire(self, player=None):
        return self._handle_fire()

    def _fire_effect(self, player=None):
        if player is None:
            player = self.game.player

        super()._fire_effect(player)

        self.current_recoil = self.recoil_amount

        # Démarrer l'animation
        self.animation_active = True
        self.animation_timer = 0
        self.current_sprite_index = 1
        if self.sprites:
            self.current_sprite = self.sprites[1]

        self.pending_projectile = True
        self.projectile_timer = 0  # commence à compter

        self.fire_sound.play()

    def _handle_fire(self):
        # Vérifier si on peut tirer (pas en rechargement, assez de munitions)
        current_time = pg.time.get_ticks() / 1000
        if (self.is_reloading or
                current_time - self.last_fire_time < self.shot_cooldown):
            return False

        # Vérifier les munitions
        if self.game.player.ammo[self.ammo_type] <= 0:
            # Plus de munitions, jouer le son "clic"
            if self.empty_sound:
                self.empty_sound.play()
            return False

        # Décrémenter les munitions
        self.game.player.ammo[self.ammo_type] -= 1

        # Mettre à jour le temps de tir
        self.last_fire_time = current_time

        # Appeler l'effet de tir
        self._fire_effect()

        return True

    def update(self, dt):
        super().update(dt)

        if self.animation_active:
            self.animation_timer += dt
            progress = min(self.animation_timer / self.animation_duration, 1.0)

            frame_count = len(self.sprites) - 1
            frame_index = min(int(progress * frame_count), frame_count)

            self.current_sprite_index = frame_index
            self.current_sprite = self.sprites[frame_index]

            if progress >= 1.0:
                self.animation_active = False
                self.animation_timer = 0
                self.current_sprite_index = 0
                self.current_sprite = self.sprites[0]

            if self.pending_projectile:
                self.projectile_timer += dt
                if self.projectile_timer >= self.projectile_delay:
                    self._create_projectile()
                    self.pending_projectile = False

    def _create_projectile(self):
        # Utiliser les attributs x et y directement ou la méthode get_position
        if hasattr(self.game.player, 'get_position'):
            player_pos = self.game.player.get_position()
            player_x, player_y = player_pos  # Supposant que get_position retourne un tuple (x, y)
        else:
            player_x = self.game.player.x
            player_y = self.game.player.y

        # Obtenir l'angle du joueur
        player_angle = self.game.raycaster.get_center_ray_angle()

        offset = 0.5  # Distance devant le joueur
        start_x = player_x + math.cos(player_angle) * offset
        start_y = player_y + math.sin(player_angle) * offset

        print(f"Création d'une roquette à la position ({player_x}, {player_y}), angle {player_angle}")

        # Créer la roquette avec les coordonnées
        from weapons.projectiles.rocket import Rocket

        try:
            rocket = Rocket(
                self.game,
                start_x, start_y,
                player_angle,
                self.projectile_speed,
                self.damage,
                self.projectile_lifetime,
                self.splash_damage,
                self.splash_radius,
                self.projectile_front,  # front_sprite
                back_sprite=self.projectile_back  # Utiliser le paramètre nommé pour être sûr
            )

            # Ajouter à la liste des projectiles
            self.game.projectiles.append(rocket)
            print(f"Roquette ajoutée! Total projectiles: {len(self.game.projectiles)}")

        except TypeError as e:
            print(f"ERREUR lors de la création de la roquette: {e}")
            # Afficher des informations de débogage
            print(f"Arguments: game={type(self.game)}, x={player_x}, y={player_y}, angle={player_angle}")
            print(f"front_sprite={type(self.projectile_front)}, back_sprite={type(self.projectile_back)}")

