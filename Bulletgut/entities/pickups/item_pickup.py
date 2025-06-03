from entities.pickups.pickup import Pickup
import pygame as pg

class ItemPickup(Pickup):
    def __init__(self, x, y, item_type, amount, sprite_path):
        image = pg.image.load(sprite_path).convert_alpha()
        super().__init__(x, y, image)
        self.item_type = item_type
        self.amount = amount

    def on_pickup(self, player, game):
        if self.item_type == "item_health":
            if player.health < player.max_health:
                player.health = min(player.health + self.amount, player.max_health)
                self.picked_up = True
                super().on_pickup(player, game)
                print(f"[PICKUP] +{self.amount} health")

        elif self.item_type == "item_armor":
            if player.armor < player.max_armor:
                player.armor = player.max_armor
                player.armor_absorption = 0.33
                self.picked_up = True
                super().on_pickup(player, game)
                print(f"[PICKUP] Armor set at {self.amount} %, absorption set to {player.armor_absorption}")

        elif self.item_type == "item_megaarmor":
            if player.armor < player.abs_max_armor:
                player.armor = player.abs_max_armor
                player.armor_absorption = 0.5
                self.picked_up = True
                super().on_pickup(player, game)
                print(f"[PICKUP] Armor set at {self.amount} %, absorption set to {player.armor_absorption}")



