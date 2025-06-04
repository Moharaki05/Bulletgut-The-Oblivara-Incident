from data.config import TILE_SIZE


class Door:
    def __init__(self, x, y, auto_close_time=3.0, thickness=0.2):
        self.grid_x = x
        self.grid_y = y
        self.state = "closed"  # 'closed', 'opening', 'open', 'closing'
        self.timer = 0
        self.auto_close_time = auto_close_time
        self.progress = 0.0  # 0 = fully closed, 1 = fully open
        self.speed = 2.0  # Speed multiplier for opening/closing

        # Door properties matching DUGA's system
        self.thickness = thickness
        self.axis = "x"  # Will be set in level.py ('x' for horizontal, 'y' for vertical)

        # DUGA-style door opening mechanism
        self.open = 0  # How much the door has slid open (0 to TILE_SIZE//2)
        self.max_open = TILE_SIZE // 2  # Maximum opening distance

        # Collision and rendering bounds
        self.collision_bounds = None
        self.update_bounds()

    def update(self, dt):
        old_progress = self.progress

        if self.state == "opening":
            self.progress += dt * self.speed
            if self.progress >= 1.0:
                self.progress = 1.0
                self.state = "open"
                self.timer = 0

        elif self.state == "open":
            self.timer += dt
            if self.timer >= self.auto_close_time:
                self.state = "closing"

        elif self.state == "closing":
            self.progress -= dt * self.speed
            if self.progress <= 0.0:
                self.progress = 0.0
                self.state = "closed"

        # Update door opening distance (DUGA style)
        if old_progress != self.progress:
            self.open = int(self.progress * self.max_open)
            self.update_bounds()

    def update_bounds(self):
        """Update collision bounds based on door opening progress (DUGA style)"""
        base_x = self.grid_x * TILE_SIZE
        base_y = self.grid_y * TILE_SIZE

        if self.axis == "x":
            # Horizontal door - slides horizontally
            # As door opens, the collision area shrinks from both sides
            shrink = self.open
            self.collision_bounds = {
                "min_x": base_x + shrink,
                "max_x": base_x + TILE_SIZE - shrink,
                "min_y": base_y,
                "max_y": base_y + TILE_SIZE
            }
        else:
            # Vertical door - slides vertically
            # As door opens, the collision area shrinks from top and bottom
            shrink = self.open
            self.collision_bounds = {
                "min_x": base_x,
                "max_x": base_x + TILE_SIZE,
                "min_y": base_y + shrink,
                "max_y": base_y + TILE_SIZE - shrink
            }

    def is_blocking(self):
        """Check if door blocks movement (DUGA style)"""
        # Door stops blocking when it's almost fully open (like DUGA)
        return self.progress < 0.9

    def is_visible(self):
        """Check if door should be rendered"""
        # Door is visible until almost fully open
        return self.progress < 0.95

    def get_door_bounds(self):
        """Get current collision bounds"""
        return self.collision_bounds

    def get_texture_offset(self):
        """Get texture offset for sliding effect (DUGA style)"""
        # This creates the sliding texture effect
        return self.open

    def get_door_thickness_px(self):
        """Get door thickness in pixels"""
        # Thickness affects rendering width
        base_thickness = max(1, int(self.thickness * TILE_SIZE))
        # As door opens, it gets visually thinner
        return max(1, int(base_thickness * (1.0 - self.progress * 0.7)))

    def get_world_position(self):
        """Get world position of door center"""
        return (
            self.grid_x * TILE_SIZE + TILE_SIZE // 2,
            self.grid_y * TILE_SIZE + TILE_SIZE // 2
        )

    # Door control methods
    def toggle(self):
        """Toggle door state"""
        if self.state == "closed":
            self.state = "opening"
            self.timer = 0
        elif self.state == "open":
            self.state = "closing"
            self.timer = 0
        elif self.state == "opening":
            self.state = "closing"
            self.timer = 0
        elif self.state == "closing":
            self.state = "opening"
            self.timer = 0

    def open_door(self):
        """Force door to open"""
        if self.state != "open" and self.state != "opening":
            self.state = "opening"
            self.timer = 0

    def close_door(self):
        """Force door to close"""
        if self.state != "closed" and self.state != "closing":
            self.state = "closing"
            self.timer = 0

    def is_open(self):
        """Check if door is fully open"""
        return self.state == "open" and self.progress >= 1.0

    def is_closed(self):
        """Check if door is fully closed"""
        return self.state == "closed" and self.progress <= 0.0

    def is_moving(self):
        """Check if door is currently moving"""
        return self.state in ["opening", "closing"]

    # DUGA compatibility methods
    def get_open_amount(self):
        """Get how much the door is open (0 to max_open)"""
        return self.open

    def get_collision_rect(self):
        """Get collision rectangle for the door"""
        bounds = self.collision_bounds
        if bounds:
            return {
                'x': bounds['min_x'],
                'y': bounds['min_y'],
                'width': bounds['max_x'] - bounds['min_x'],
                'height': bounds['max_y'] - bounds['min_y']
            }
        return None