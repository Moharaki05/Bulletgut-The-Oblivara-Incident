from data.config import TILE_SIZE


class Door:
    def __init__(self, x, y, auto_close_time=3.0, thickness=0.15):
        self.grid_x = x
        self.grid_y = y
        self.state = "closed"  # 'closed', 'opening', 'open', 'closing'
        self.timer = 0
        self.auto_close_time = auto_close_time
        self.progress = 0  # 0 = fully closed, 1 = fully open
        self.speed = 0.5  # seconds to fully open/close (faster like Wolf3D)

        # Properties for sliding door
        self.thickness = thickness  # Door thickness as a fraction of tile size
        self.axis = "x"  # Default - will be set properly in level.py

        # Door texture offset for rendering
        self.texture_offset = 0

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

        # Update texture offset for Wolf3D style door sliding visual
        if self.axis == "x":
            self.texture_offset = self.progress * TILE_SIZE
        else:  # y-axis
            self.texture_offset = self.progress * TILE_SIZE

    def toggle(self):
        if self.state in ("closed", "closing"):
            self.state = "opening"
        elif self.state in ("open", "opening"):
            self.state = "closing"

    def is_blocking(self):
        # Door blocks movement if it's not fully open
        # Using 0.95 to add some leeway so player doesn't get stuck
        return self.progress < 0.95

    def is_visible(self):
        # Door is visible unless it's fully open
        return self.progress < 0.95

    def get_door_thickness_px(self):
        return TILE_SIZE * self.thickness * (1.0 - self.progress)

    def get_world_position(self):
        # Base position at center of tile
        base_x = self.grid_x * TILE_SIZE + TILE_SIZE / 2
        base_y = self.grid_y * TILE_SIZE + TILE_SIZE / 2

        # Calculate sliding offset based on progress
        slide_distance = self.progress * TILE_SIZE

        # Apply offset based on axis
        if self.axis == "x":
            # Door slides horizontally (like Wolf3D)
            return (base_x, base_y)
        else:
            # Door slides vertically
            return (base_x, base_y)

    def get_door_bounds(self):
        x, y = self.get_world_position()

        # The visible part of the door gets smaller as it opens
        effective_size = (1.0 - self.progress) * TILE_SIZE

        # Center the remaining door in the opening
        offset = (TILE_SIZE - effective_size) / 2

        if self.axis == "x":
            # Horizontal sliding door (slides into left wall)
            return {
                "min_x": x - TILE_SIZE / 2 + offset,
                "max_x": x - TILE_SIZE / 2 + offset + effective_size,
                "min_y": y - TILE_SIZE / 2,
                "max_y": y + TILE_SIZE / 2
            }
        else:
            # Vertical sliding door (slides into ceiling)
            return {
                "min_x": x - TILE_SIZE / 2,
                "max_x": x + TILE_SIZE / 2,
                "min_y": y - TILE_SIZE / 2 + offset,
                "max_y": y - TILE_SIZE / 2 + offset + effective_size
            }

    def is_open(self):
        return self.state == "open"

    def get_texture_coordinates(self):
        if self.axis == "x":
            # For horizontal sliding doors, we need to offset the texture horizontally
            return self.texture_offset, 0
        else:
            # For vertical sliding doors, we need to offset the texture vertically
            return 0, self.texture_offset