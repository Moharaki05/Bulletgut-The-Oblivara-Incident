import math

class Pickup:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.sprite = image
        self.picked_up = False

    def update(self, player, game):
        if self.picked_up:
            return

        dx = self.x - player.x
        dy = self.y - player.y
        distance = math.hypot(dx, dy)
        if distance < 20:
            self.on_pickup(player, game)

    def _is_near_player(self, player):
        dx = self.x - player.x
        dy = self.y - player.y
        return dx * dx + dy * dy < 0.25  # distance au carré < 0.5

    def on_pickup(self, player, game):
        pass
