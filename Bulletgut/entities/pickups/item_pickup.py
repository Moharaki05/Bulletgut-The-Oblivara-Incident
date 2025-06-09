from entities.pickups.pickup import Pickup
import pygame as pg

class ItemPickup(Pickup):
    def __init__(self, x, y, item_type, amount, sprite_path):
        image = pg.image.load(sprite_path).convert_alpha()
        super().__init__(x, y, image)
        self.item_type = item_type
        self.amount = amount
        self.pickup_type = "item"

    def on_pickup(self, player, game):
        pickup_messages = {
            "item_medikit": "A MEDIKIT",
            "item_armor": "ARMOR",
            "item_megaarmor": "A MEGA ARMOR"
        }

        if hasattr(self, 'suppress_message') and self.suppress_message:
            super().on_pickup(player, game)
            return

        if self.item_type == "item_medikit":
            if player.health < player.max_health:
                player.health = min(player.health + self.amount, player.max_health)
                self.picked_up = True
                print(f"[PICKUP] +{self.amount} health")

        elif self.item_type == "item_armor":
            if player.armor < player.max_armor:
                player.armor = player.max_armor
                player.armor_absorption = 0.33
                self.picked_up = True
                print(f"[PICKUP] Armor set at {self.amount} %, absorption set to {player.armor_absorption}")

        elif self.item_type == "item_megaarmor":
            if player.armor < player.abs_max_armor:
                player.armor = player.abs_max_armor
                player.armor_absorption = 0.5
                self.picked_up = True
                print(f"[PICKUP] Armor set at {self.amount} %, absorption set to {player.armor_absorption}")

        if self.picked_up:
            msg = pickup_messages.get(self.item_type, self.item_type.replace("_", " ").upper())
            game.hud.messages.add(f"PICKED UP {msg}.", (255, 0, 0))
            super().on_pickup(player, game)




