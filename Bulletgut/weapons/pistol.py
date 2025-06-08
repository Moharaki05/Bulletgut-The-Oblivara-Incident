from weapons.hitscan_weapon import HitscanWeapon
import random
import math
import pygame as pg

class Pistol(HitscanWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Pistol"
        self.damage = 15
        self.fire_rate = 2.0
        self.shot_cooldown = 1.0 / self.fire_rate
        self.spread = 0.02
        self.pellets = 1
        self.ammo_type = "bullets"
        self.scale_factor = 1.5


        self.load_sprites([
            "assets/weapons/pistol/pistol1.png",
            "assets/weapons/pistol/pistol2.png",
            "assets/weapons/pistol/pistol3.png",
            "assets/weapons/pistol/pistol4.png",
            "assets/weapons/pistol/pistol5.png"
        ])

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/pistol/pistol.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/pistol/empty_pistol_click.wav")

        self.position_offset = [0, 50]

        # Initialiser le sprite actif
        self.current_sprite_index = 0
        self.current_sprite = self.sprites[0] if self.sprites else None
        self.is_firing = False

    def _handle_fire(self):
        # Vérifier si on a des munitions
        if self.game.player.ammo[self.ammo_type] <= 0:
            # Arrêter tout son en cours
            if hasattr(self, 'fire_sound'):
                self.fire_sound.stop()

            # Jouer le son "vide" avec un volume adéquat
            self.empty_sound.set_volume(1.0)
            self.empty_sound.play()
            print("Son pistolet vide joué - munitions épuisées")

            self.is_firing = False

            # Conserver le sprite de base (non-tir)
            self.current_sprite_index = 0
            if self.sprites and len(self.sprites) > 0:
                self.current_sprite = self.sprites[0]

            return

        # Décrémenter les munitions
        self.game.player.ammo[self.ammo_type] -= 1

        # Jouer le son de tir
        self.fire_sound.set_volume(0.65)
        self.fire_sound.play()

        # Animation de tir (passer aux sprites suivants)
        self.is_firing = True
        self.current_sprite_index = 1  # Commencer l'animation

        # Obtenir la position et la direction du joueur
        player = self.game.player
        start_x, start_y = player.x, player.y
        direction = player.get_direction_vector()

        # Calculer un angle aléatoire dans la limite du spread
        if hasattr(self, 'spread'):
            angle_offset = random.uniform(-self.spread, self.spread)
            # Appliquer la rotation à la direction
            cos_offset = math.cos(angle_offset)
            sin_offset = math.sin(angle_offset)
            dx, dy = direction
            direction = (
                dx * cos_offset - dy * sin_offset,
                dx * sin_offset + dy * cos_offset
            )

        super()._fire_effect()

        # TODO: Implémenter le raycast pour détecter les impacts
        # Pour l'instant, simplement afficher un message de débogage
        print(f"Tir du pistolet depuis ({start_x}, {start_y}) dans la direction {direction}")
        print(f"Munitions restantes: {self.game.player.ammo[self.ammo_type]}")


        # Si vous avez un système de particules ou d'effets visuels, vous pouvez l'utiliser ici
        # self.game.add_effect('muzzle_flash', start_x, start_y)




