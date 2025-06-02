from entities.pickups.pickup import Pickup
import pygame as pg

class AmmoPickup(Pickup):
    def __init__(self, x, y, ammo_type, amount, sprite_path):
        image = pg.image.load(sprite_path).convert_alpha()
        super().__init__(x, y, image)
        self.ammo_type = ammo_type
        self.amount = amount

    def on_pickup(self, player, game):
        current = player.ammo.get(self.ammo_type, 0)
        max_ammo = player.max_ammo.get(self.ammo_type, 0)

        if current < max_ammo:
            added = min(self.amount, max_ammo - current)
            player.ammo[self.ammo_type] += added
            print(f"[PICKUP] +{added} {self.ammo_type} (total: {player.ammo[self.ammo_type]})")
            self.picked_up = True
        else:
            print(f"[PICKUP] {self.ammo_type} full! ({current}/{max_ammo})")

        super().on_pickup(player, game)














