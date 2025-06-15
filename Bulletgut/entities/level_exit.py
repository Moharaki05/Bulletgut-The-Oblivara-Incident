from data.config import TILE_SIZE

class LevelExit:
    def __init__(self, x, y, next_level=None):
        self.x = x
        self.y = y
        self.next_level = next_level
        self.grid_x = int(x // TILE_SIZE)
        self.grid_y = int(y // TILE_SIZE)
        self.activated = False

    def is_player_near(self, player):
        """Vérifie si le joueur est proche de la sortie de niveau"""
        px, py = player.get_position()
        dx = px - (self.grid_x + 0.5) * TILE_SIZE
        dy = py - (self.grid_y + 0.5) * TILE_SIZE
        dist_squared = dx * dx + dy * dy
        return dist_squared <= (TILE_SIZE * 2.1) ** 2  # Même distance que les portes

    def activate(self):
        """Active la sortie de niveau"""
        if not self.activated:
            self.activated = True
            return True
        return False