from entities.pickups.pickup import Pickup
import pygame as pg

pickup_messages = {
    "bullets": "A BOX OF BULLETS",
    "shells": "SOME SHELLS",
    "rockets": "A BOX OF ROCKETS",
    "cells": "A CELL CHARGE PACK"
}

class AmmoPickup(Pickup):
    def __init__(self, x, y, ammo_type, amount, sprite_path, label=None):
        image = pg.image.load(sprite_path).convert_alpha()
        super().__init__(x, y, image)
        self.ammo_type = ammo_type
        self.amount = amount
        self.label = label
        self.dropped_by_enemy = False
        self.pickup_type = "ammo"

    def on_pickup(self, player, game):
        current = player.ammo[self.ammo_type]
        max_amount = player.max_ammo[self.ammo_type]

        if current >= max_amount:
            print(f"[PICKUP] {self.ammo_type} full! ({current}/{max_amount})")
            return False

        new_amount = min(current + self.amount, max_amount)
        player.ammo[self.ammo_type] = new_amount
        print(f"[PICKUP] +{self.amount} {self.ammo_type} -> {new_amount}/{max_amount}")

        msg = self.label or pickup_messages.get(self.ammo_type, self.ammo_type.upper())
        game.hud.messages.add(f"PICKED UP {msg}.", (255, 0, 0))

        self.picked_up = True
        return super().on_pickup(player, game)
















