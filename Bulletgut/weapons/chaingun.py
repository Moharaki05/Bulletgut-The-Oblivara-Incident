from weapons.hitscan_weapon import HitscanWeapon
import random
import math
import pygame as pg

class Chaingun(HitscanWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Chaingun"
        self.damage = 8
        self.fire_rate = 10.0  # Cadence de tir élevée
        self.shot_cooldown = 1.0 / self.fire_rate
        self.spread = 0.04
        self.pellets = 1
        self.ammo_type = "bullets"
        self.max_ammo = 200
        self.current_ammo = self.max_ammo
        self.scale_factor = 1.6

        # Charger les sprites (seulement 3 images)
        self.load_sprites([
            "assets/weapons/chaingun/chaingun1.png",  # Image 1: repos
            "assets/weapons/chaingun/chaingun2.png",  # Image 2: tir frame 1
            "assets/weapons/chaingun/chaingun3.png"  # Image 3: tir frame 2
        ])

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/chaingun/chaingun.wav")
        self.empty_sound = pg.mixer.Sound("assets/sounds/chaingun/empty_chaingun_click.wav")

        self.position_offset = [10, 50]

        # Initialiser le sprite actif
        self.current_sprite_index = 0  # Index 0 = image de repos
        self.current_sprite = self.sprites[0] if self.sprites else None

        # Variables pour gérer le tir et l'animation
        self.is_firing = False
        self.animation_timer = 0
        self.animation_speed = 0.05  # Temps entre chaque frame d'animation

        # Variables pour gérer le son et le tir continu
        self.sound_cooldown = 0
        self.sound_repeat_time = 0.1  # Intervalle entre les répétitions du son
        self.fire_cooldown = 0  # Cooldown entre chaque balle
        self.trigger_held = False  # Indique si le joueur maintient le bouton de tir

        # Pour gérer l'arrêt progressif du son
        self.current_sound_channel = None
        self.stopping_fire = False
        self.sound_fadeout_time = 100  # Temps de fadeout en millisecondes (0.1s)

    def update(self, delta_time):
        # Mettre à jour le cooldown de tir si nécessaire
        if self.fire_cooldown > 0:
            self.fire_cooldown -= delta_time

        # Vérifier si on est à court de munitions pendant le tir
        if self.is_firing and self.trigger_held and self.current_ammo <= 0:
            # Jouer le son empty une seule fois
            self.empty_sound.play()

            # Arrêter le tir immédiatement
            self.is_firing = False
            self.trigger_held = False

            # Arrêter tous les sons de tir en cours
            if self.current_sound_channel and self.current_sound_channel.get_busy():
                self.current_sound_channel.stop()
            self.current_sound_channel = None

            # Retour à l'image de repos
            self.current_sprite_index = 0
            self.current_sprite = self.sprites[0]

            return  # Sortir de la méthode pour éviter d'exécuter le reste

        # IMPORTANT: Ne gérer le son et l'animation que si on est en train de tirer
        # ET que la gâchette est maintenue ET qu'on a des munitions
        if self.is_firing and self.trigger_held and self.current_ammo > 0:
            # Mettre à jour le cooldown du son
            if self.sound_cooldown > 0:
                self.sound_cooldown -= delta_time
            else:
                # Ne jouer le son que s'il n'est pas déjà en cours de lecture
                if not self.current_sound_channel or not self.current_sound_channel.get_busy():
                    self.current_sound_channel = self.fire_sound.play()
                    self.sound_cooldown = self.sound_repeat_time

            # Animation de tir
            self.animation_timer += delta_time
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                # Alterner entre les images de tir
                if self.current_sprite_index == 1:
                    self.current_sprite_index = 2
                else:
                    self.current_sprite_index = 1
                self.current_sprite = self.sprites[self.current_sprite_index]

            # Gestion des tirs
            if self.fire_cooldown <= 0 and self.current_ammo > 0:
                self._handle_fire()
                self.fire_cooldown = self.shot_cooldown

        # Si on n'est plus en train de tirer, s'assurer que l'on est
        # sur l'image de repos et que le son ne sera pas rejoué
        elif not self.is_firing:
            self.current_sprite_index = 0
            self.current_sprite = self.sprites[0]
            # S'assurer que le son est arrêté
            if self.current_sound_channel and self.current_sound_channel.get_busy():
                self.current_sound_channel.stop()
                self.current_sound_channel = None

    def fire(self):
        self.pull_trigger()

    def pull_trigger(self):
        """Commence le tir de l'arme"""
        # Vérifier si on a des munitions
        if self.current_ammo <= 0:
            # Jouer le son empty une seule fois et sortir
            self.empty_sound.play()
            return

        # Si on a des munitions, commencer le tir
        self.is_firing = True
        self.trigger_held = True
        self.stopping_fire = False

        # Jouer le son une seule fois au début
        if not self.current_sound_channel or not self.current_sound_channel.get_busy():
            self.current_sound_channel = self.fire_sound.play()
            self.sound_cooldown = self.sound_repeat_time

        # Tirer immédiatement une première balle
        if self.current_ammo > 0:
            self._fire_bullet()
            self.fire_cooldown = self.shot_cooldown

        # Réinitialiser l'animation
        self.animation_timer = 0
        self.current_sprite_index = 1
        self.current_sprite = self.sprites[1]

    def release_trigger(self):
        """Arrête le tir de l'arme"""
        # Indiquer que l'arme n'est plus en train de tirer
        self.trigger_held = False
        self.is_firing = False
        self.stopping_fire = True

        # Arrêter définitivement tous les sons
        pg.mixer.stop()  # Arrête tous les canaux son en cours
        self.current_sound_channel = None  # Réinitialiser la référence

        # Réinitialiser le cooldown du son
        self.sound_cooldown = 0

        # Retour immédiat à l'image de repos
        self.current_sprite_index = 0
        self.current_sprite = self.sprites[0]

    def _fire_bullet(self):
        """Tire une seule balle (pour le tir automatique)"""
        # Vérifier les munitions
        if self.current_ammo <= 0:
            self.empty_sound.play()
            self.is_firing = False
            self.stopping_fire = False
            return False

        # Décrémenter les munitions
        self.current_ammo -= 1

        # Réinitialiser le cooldown pour la prochaine balle
        self.fire_cooldown = self.shot_cooldown

        # Jouer le son si nécessaire
        if self.sound_cooldown <= 0:
            self.current_sound_channel = self.fire_sound.play()
            self.sound_cooldown = self.sound_repeat_time

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

        # TODO: Implémenter le raycast pour détecter les impacts
        print(f"Tir de la mitrailleuse depuis ({start_x}, {start_y}) dans la direction {direction}")
        print(f"Munitions restantes: {self.current_ammo}")

        return True

    def _handle_fire(self):
        """Méthode appelée quand le joueur appuie sur le bouton de tir"""
        # Vérifier à nouveau les munitions pour être sûr
        if self.current_ammo <= 0:
            # Arrêter le tir et tous les sons en cours
            self.is_firing = False
            self.trigger_held = False

            if self.current_sound_channel and self.current_sound_channel.get_busy():
                self.current_sound_channel.stop()
            self.current_sound_channel = None

            # Jouer le son empty une seule fois
            self.empty_sound.play()
            return

        # Si on a des munitions, tirer normalement
        self._fire_bullet()
