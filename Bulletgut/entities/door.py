from data.config import TILE_SIZE


class Door:
    def __init__(self, x, y, auto_close_time=3.0, thickness=0.15):
        self.grid_x = x
        self.grid_y = y
        self.state = "closed"  # 'closed', 'opening', 'open', 'closing'
        self.timer = 0
        self.auto_close_time = auto_close_time
        self.progress = 0  # 0 = fully closed, 1 = fully open
        self.speed = 2.5  # seconds to fully open/close

        # Properties for sliding door in doorway
        self.thickness = thickness  # Door thickness as a fraction of tile size
        self.axis = "x"  # Default - will be set properly in level.py
        self.door_width = 1.0  # Door width as a fraction of tile size (default: full tile)

    def update(self, dt):
        if self.state == "opening":
            self.progress += dt / self.speed
            if self.progress >= 1:
                self.progress = 1
                self.state = "open"
                self.timer = 0

        elif self.state == "open":
            self.timer += dt
            if self.timer >= self.auto_close_time:
                self.state = "closing"

        elif self.state == "closing":
            self.progress -= dt / self.speed
            if self.progress <= 0:
                self.progress = 0
                self.state = "closed"

    def toggle(self):
        print(f"[TOGGLE] Door at {self.grid_x},{self.grid_y} toggled from {self.state}")
        if self.state in ("closed", "closing"):
            self.state = "opening"
        elif self.state in ("open", "opening"):
            self.state = "closing"

    def is_blocking(self):
        # A door blocks movement if it's not fully open
        return self.progress < 0.95  # Using 0.95 instead of 1 to give a little margin

    def is_visible(self):
        # A door is visible if it's not fully open
        # This is important - closed doors should be visible!
        return self.progress < 0.95  # Using 0.95 instead of 1 to give a little margin

    def get_door_thickness_px(self):
        """Returns the actual thickness of the door in pixels"""
        return TILE_SIZE * self.thickness

    def get_world_position(self):
        """Returns the world pixel position adjusted for sliding."""
        # Base position is the center of the tile
        base_x = self.grid_x * TILE_SIZE + TILE_SIZE / 2
        base_y = self.grid_y * TILE_SIZE + TILE_SIZE / 2

        # Calculate offset based on progress and axis
        offset = self.progress * TILE_SIZE

        if self.axis == "x":
            # Door slides horizontally (left-right)
            return (base_x + offset, base_y)
        else:
            # Door slides vertically (up-down)
            return (base_x, base_y - offset)  # Negative because we slide up

    def get_door_bounds(self):
        """Returns the physical bounds of the door in world space"""
        x, y = self.get_world_position()

        # Adjust for door in doorway
        half_thickness = self.get_door_thickness_px() / 2
        half_width = (TILE_SIZE * self.door_width) / 2

        if self.axis == "x":
            # Horizontal sliding door - thin in the X direction (door panel itself)
            return {
                "min_x": x - half_thickness,  # This is the door panel thickness
                "max_x": x + half_thickness,  # This is the door panel thickness
                "min_y": y - half_width,  # This is half the door height/width
                "max_y": y + half_width  # This is half the door height/width
            }
        else:
            # Vertical sliding door - thin in the Y direction (door panel itself)
            return {
                "min_x": x - half_width,  # This is half the door width
                "max_x": x + half_width,  # This is half the door width
                "min_y": y - half_thickness,  # This is the door panel thickness
                "max_y": y + half_thickness  # This is the door panel thickness
            }

    def is_open(self):
        return self.state == "open"