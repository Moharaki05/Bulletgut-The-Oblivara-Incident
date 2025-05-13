from weapons.melee_weapon import MeleeWeapon
import pygame as pg

class Chainsaw(MeleeWeapon):
    def __init__(self, game):
        super().__init__(game)
        self.name = "Chainsaw"
        self.damage = 5  # dégâts par tick
        self.fire_rate = 10  # taux de feu élevé
        self.shot_cooldown = 1.0 / self.fire_rate
        self.continuous_damage = True  # dégâts continus
        self.melee_range = 120  # portée légèrement supérieure aux poings

        # Charger les sprites
        self.load_sprites([
            "assets/weapons/chainsaw/idle.png",
            "assets/weapons/chainsaw/swing1.png",
            "assets/weapons/chainsaw/swing2.png",
            "assets/weapons/chainsaw/swing3.png"
        ])

        # Sons
        self.fire_sound = pg.mixer.Sound("assets/sounds/chainsaw_rev.wav")
        self.hit_sound = pg.mixer.Sound("assets/sounds/chainsaw_hit.wav")

    def _check_melee_hit(self):
        """Surcharge pour ajouter le son de contact"""
        hit = super()._check_melee_hit()
        if hit:
            self.hit_sound.play()
        return hit
