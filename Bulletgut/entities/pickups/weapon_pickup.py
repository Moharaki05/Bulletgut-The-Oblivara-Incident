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
        gained_ammo = 0

        if self.ammo_type is not None and self.ammo_type in player.ammo:
            before = player.ammo[self.ammo_type]
            player.ammo[self.ammo_type] = min(
                player.ammo[self.ammo_type] + self.amount,
                player.max_ammo[self.ammo_type]
            )
            gained_ammo = player.ammo[self.ammo_type] - before
            if gained_ammo > 0:
                print(f"[PICKUP] Gained {gained_ammo} {self.ammo_type} (from weapon pickup)")
        elif self.ammo_type:
            print(f"[PICKUP] Unknown ammo type: {self.ammo_type}")

        if not has_weapon:
            weapon_class = player.weapon_factory.get(self.weapon_name)
            if weapon_class:
                new_weapon = weapon_class(game)
                player.weapons[slot] = new_weapon
                print(f"[PICKUP] Picked up new weapon: {self.weapon_name}")

                player.got_weapon_until = pg.time.get_ticks() + 1000

                if player.weapon:
                    player.weapon.is_equipped = False
                    if hasattr(player.weapon, "on_deselected"):
                        player.weapon.on_deselected()

                player.weapon = new_weapon
                player.current_weapon_index = slot
                player.weapon.is_equipped = True

                nice_names = {
                    "pistol": "PISTOL",
                    "shotgun": "SHOTGUN",
                    "chaingun": "CHAINGUN",
                    "rocketlauncher": "ROCKET LAUNCHER",
                    "plasmagun": "PLASMA GUN",
                    "bfg": "BFG9000"
                }
                fallback_name = self.weapon_name.replace("_", " ").upper()
                display_name = nice_names.get(self.weapon_name, fallback_name)
                game.hud.messages.add(f"YOU GOT THE {display_name}!", (255, 0, 0))
        else:
            if gained_ammo > 0:
                ammo_names = {
                    "bullets": "BULLETS",
                    "shells": "SHELLS",
                    "rockets": "ROCKETS",
                    "cells": "CELLS"
                }
                ammo_display = ammo_names.get(self.ammo_type, self.ammo_type.upper())
                game.hud.messages.add(f"PICKED UP {ammo_display}.", (255, 0, 0))
            else:
                print(f"[PICKUP] Already has weapon: {self.weapon_name}, no ammo gained.")

        if not pg.mixer.get_init():
            pg.mixer.init()

        pickup_sound = pg.mixer.Sound("assets/sounds/pickups/weapon_pickup.wav")
        pickup_sound.play()

        self.picked_up = True
