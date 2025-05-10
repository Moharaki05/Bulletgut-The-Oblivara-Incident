from data.config import TILE_SIZE

class Door:
    def __init__(self, x, y, auto_close_time = 3.0):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * TILE_SIZE
        self.pixel_y = y * TILE_SIZE
        self.state = "closed"
        self.timer = 0
        self.auto_close_time = auto_close_time

    def update(self, dt):
        if self.state == "opening":
            self.state = "open"
            self.timer = 0
        elif self.state == "open":
            self.timer += dt
            if self.timer >= self.auto_close_time:
                self.state = "closed"

    def toggle(self):
        if self.state in ["closed", "closing"]:
            print(f"Toggling door at ({self.grid_x}, {self.grid_y})")
            self.state = "opening"
            self.timer = 0

    def is_blocking(self):
        return self.state in ("closed", "closing")

    def is_open(self):
        return self.state == "open"