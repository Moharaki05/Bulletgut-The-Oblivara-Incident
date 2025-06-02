import pygame as pg
from entities.pickups.pickup import Pickup

class WeaponPickup(Pickup):
    def __init__(self, x, y, weapon_name, sprite_path, ammo_type, amount):
        image = pg.image.load(sprite_path).convert_alpha()
        super().__init__(x, y, image)
        self.weapon_name = weapon_name
        self.ammo_type = ammo_type
        self.amount = amount

    def on_pickup(self, player, game):
        weapon_class = player.weapon_factory.get(self.weapon_name)

        if not weapon_class:
            print(f"[PICKUP] Unknown weapon: {self.weapon_name}")
            return

        # Vérifie si l'arme est déjà dans l'inventaire
        already_has_weapon = any(isinstance(w, weapon_class) for w in player.weapons)

        # Ajoute les munitions si possible
        if self.ammo_type in player.ammo:
            current = player.ammo[self.ammo_type]
            max_ammo = player.max_ammo.get(self.ammo_type, 0)
            if current < max_ammo:
                gained = min(self.amount, max_ammo - current)
                player.ammo[self.ammo_type] += gained
                print(f"[PICKUP] Gained {gained} {self.ammo_type} (now {player.ammo[self.ammo_type]})")

        # Ajoute l'arme si elle est nouvelle
        if not already_has_weapon:
            new_weapon = weapon_class(game)
            player.weapons.append(new_weapon)
            print(f"[PICKUP] Picked up new weapon: {self.weapon_name}")
        else:
            print(f"[PICKUP] Already has weapon: {self.weapon_name}")

        # Marquer comme ramassé
        self.picked_up = True
