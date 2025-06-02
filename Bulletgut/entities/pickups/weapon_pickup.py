import pygame as pg

from data.config import WEAPON_SLOTS
from entities.pickups.pickup import Pickup

class WeaponPickup(Pickup):
    def __init__(self, x, y, weapon_name, sprite_path, ammo_type, amount):
        image = pg.image.load(sprite_path).convert_alpha()
        super().__init__(x, y, image)
        self.weapon_name = weapon_name
        self.ammo_type = ammo_type
        self.amount = amount

    def on_pickup(self, player, game):
        slot = WEAPON_SLOTS.get(self.weapon_name)

        if slot is None:
            print(f"[PICKUP] Unknown weapon slot for: {self.weapon_name}")
            return

        has_weapon = player.weapons[slot] is not None

        # ✅ Ajouter des munitions SEULEMENT si ammo_type est défini
        if self.ammo_type is not None:
            if self.ammo_type in player.ammo:
                if player.ammo[self.ammo_type] < player.max_ammo[self.ammo_type]:
                    before = player.ammo[self.ammo_type]
                    player.ammo[self.ammo_type] = min(
                        player.ammo[self.ammo_type] + self.amount,
                        player.max_ammo[self.ammo_type]
                    )
                    gained = player.ammo[self.ammo_type] - before
                    print(f"[PICKUP] Gained {gained} {self.ammo_type} (from weapon pickup)")
            else:
                print(f"[PICKUP] Unknown ammo type: {self.ammo_type}")

        # ✅ Ajouter l'arme même si elle n'utilise pas de munitions
        if not has_weapon:
            weapon_class = player.weapon_factory.get(self.weapon_name)
            if weapon_class:
                new_weapon = weapon_class(game)
                player.weapons[slot] = new_weapon
                print(f"[PICKUP] Picked up new weapon: {self.weapon_name}")
            else:
                print(f"[PICKUP] Unknown weapon class: {self.weapon_name}")
        else:
            print(f"[PICKUP] Already has weapon: {self.weapon_name}")

        self.picked_up = True
