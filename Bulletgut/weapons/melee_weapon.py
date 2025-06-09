from weapons.weapon_base import WeaponBase
from abc import ABC
import math

class MeleeWeapon(WeaponBase, ABC):
    def __init__(self, game):
        super().__init__(game)
        # Propriétés spécifiques aux armes de mêlée
        self.melee_range = 100  # portée en pixels
        self.swing_duration = 0.3  # durée en secondes de l'animation
        self.swing_timer = 0
        self.is_swinging = False
        self.continuous_damage = False  # True pour tronçonneuse, False pour poings
        self.damage_interval = 0.1  # pour les armes à dégâts continus
        self.damage_timer = 0

    def _fire_effect(self):
        """Effet de tir spécifique pour les armes de mêlée"""
        self.is_swinging = True
        self.swing_timer = self.swing_duration

        # Vérification des ennemis à portée
        self._check_melee_hit()

        # Jouer le son si disponible
        if hasattr(self, 'fire_sound') and self.fire_sound:
            self.fire_sound.play()

    def update(self, dt):
        super().update(dt)

        # Gestion de l'animation et des dégâts continus
        if self.is_swinging:
            self.swing_timer -= dt

            # Pour les armes à dégâts continus (tronçonneuse)
            if self.continuous_damage:
                self.damage_timer -= dt
                if self.damage_timer <= 0:
                    self._check_melee_hit()
                    self.damage_timer = self.damage_interval

            # IMPORTANT: Réinitialiser is_swinging quand le timer est écoulé
            if self.swing_timer <= 0:
                self.is_swinging = False

    def _check_melee_hit(self):
        """Vérifie si un ennemi est touché par l'attaque de mêlée"""
        player_rect = self.game.player.rect

        for enemy in self.game.enemies:
            if not enemy.alive:
                continue

            if hasattr(enemy, "melee_hitbox") and player_rect.colliderect(enemy.melee_hitbox):
                enemy.take_damage(self.damage, splash=False, direct_hit=True)




