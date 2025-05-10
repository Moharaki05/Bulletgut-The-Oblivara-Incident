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
        self.axis = self.determine_door_axis()  # 'x' or 'y' - which axis door slides along
        self.door_width = 1.0  # Door width as a fraction of tile size (default: full tile)

    def determine_door_axis(self):
        # This would ideally be determined by your map data
        # For now, we'll default to x-axis (horizontal sliding doors)
        # You could extend this by checking adjacent tiles or adding properties in your TMX
        return "x"  # or "y" for vertical sliding doors

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
        return self.state in ("closed", "closing", "opening") and self.progress < 1

    def is_visible(self):
        return self.progress < 1

    def get_door_thickness_px(self):
        """Returns the actual thickness of the door in pixels"""
        return TILE_SIZE * self.thickness

    def get_world_position(self):
        """Returns the world pixel position adjusted for sliding."""
        offset = self.progress * TILE_SIZE

        # Calculate the center position of the door based on sliding axis
        if self.axis == "x":
            # Door slides horizontally (left-right)
            # Calculate door starting position at the edge of the doorway
            door_x = self.grid_x * TILE_SIZE + TILE_SIZE / 2  # Center of the tile
            if self.progress == 0:  # If door is closed
                return (door_x, self.grid_y * TILE_SIZE + TILE_SIZE / 2)
            else:
                # Slide to the right when opening
                return (door_x + offset, self.grid_y * TILE_SIZE + TILE_SIZE / 2)
        else:
            # Door slides vertically (up-down)
            door_y = self.grid_y * TILE_SIZE + TILE_SIZE / 2  # Center of the tile
            if self.progress == 0:  # If door is closed
                return (self.grid_x * TILE_SIZE + TILE_SIZE / 2, door_y)
            else:
                # Slide up when opening
                return (self.grid_x * TILE_SIZE + TILE_SIZE / 2, door_y - offset)

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

    def is_ray_hitting(self, ox, oy, ray_x, ray_y):
        """Check if a ray intersects with this door"""
        if not self.is_visible():
            return False

        bounds = self.get_door_bounds()

        # For simplicity, we'll use a line segment intersection test
        # This is a simplified version - for production you'd want a more robust approach

        # Line segments: (ox,oy)->(ray_x,ray_y) and door bounds
        if self.axis == "x":
            # Check intersection with horizontal door (thin in Y)
            # We only need to check Y intersection since door spans full X of tile
            if (oy < bounds["min_y"] and ray_y > bounds["min_y"]) or (oy > bounds["max_y"] and ray_y < bounds["max_y"]):
                # Ray crosses y bounds of door, now check if it's within x bounds
                t = (bounds["min_y"] - oy) / (ray_y - oy) if ray_y != oy else 0
                intersect_x = ox + t * (ray_x - ox)
                return bounds["min_x"] <= intersect_x <= bounds["max_x"]
        else:
            # Check intersection with vertical door (thin in X)
            if (ox < bounds["min_x"] and ray_x > bounds["min_x"]) or (ox > bounds["max_x"] and ray_x < bounds["max_x"]):
                # Ray crosses x bounds of door, now check if it's within y bounds
                t = (bounds["min_x"] - ox) / (ray_x - ox) if ray_x != ox else 0
                intersect_y = oy + t * (ray_y - oy)
                return bounds["min_y"] <= intersect_y <= bounds["max_y"]

        return False

    def is_open(self):
        return self.state == "open"