from weapons.weapon_base import WeaponBase
from weapons.projectiles.projectile import Projectile
from abc import ABC

class ProjectileWeapon(WeaponBase, ABC):
    def __init__(self, game):
        super().__init__(game)
        self.projectile_speed = 40  # Unités par seconde
        self.projectile_lifetime = 5.0  # Secondes avant disparition
        self.splash_damage = False
        self.splash_radius = 0
        self.projectile_sprite = None

    def update(self, dt):
        super().update(dt)

    # Dans projectile_weapon.py
    def _fire_effect(self, player=None):
        """Tire un projectile physique"""
        if player is None:
            player = self.game.player

        # Position et angle du joueur
        px, py = player.get_position()
        angle = self.game.raycaster.get_center_ray_angle()

        # Crée un nouveau projectile
        projectile = Projectile(
            self.game,
            px, py,
            angle,
            self.projectile_speed,
            self.damage,
            self.projectile_lifetime,
            self.splash_damage,
            self.splash_radius,
            self.projectile_sprite
        )


    # Dans weapon_base.py ou projectile_weapon.py
    def fire(self):
        """
        Méthode appelée quand le joueur déclenche un tir.
        À surcharger dans les classes dérivées si nécessaire.
        """
        print(f"{type(self).__name__}.fire() appelée")

        # Par défaut, déléguer à _handle_fire si elle existe
        if hasattr(self, '_handle_fire'):
            self.is_firing = True
            return self._handle_fire()  # dt approximatif
        else:
            print("AVERTISSEMENT: Aucune méthode _handle_fire trouvée")
            return False

