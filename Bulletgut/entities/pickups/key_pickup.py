from entities.pickups.item_pickup import ItemPickup

class KeyPickup(ItemPickup):
    def __init__(self, x, y, color):
        self.color = color
        self.suppress_message = True
        self.pickup_type = "key"
        item_type = f"key_{color}"
        amount = 0
        sprite_path = f"assets/pickups/keys/key_{color}.png"
        super().__init__(x, y, item_type, amount, sprite_path)

    def on_pickup(self, player, game):
        if self.color not in player.keys:
            player.keys.add(self.color)
            game.hud.messages.add(f"YOU GOT THE {self.color.upper()} KEY!", (255, 0, 0))
            self.picked_up = True

        if self.picked_up:
            super().on_pickup(player, game)