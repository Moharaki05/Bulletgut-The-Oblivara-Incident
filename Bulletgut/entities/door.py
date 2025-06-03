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
        # CHANGEMENT PRINCIPAL: La porte reste toujours visible pendant l'animation
        # Elle ne disparaît que quand elle est complètement ouverte
        return self.progress < 1.0  # Changé de 0.95 à 1.0

    def get_door_thickness_px(self):
        # La largeur diminue progressivement selon le progrès d'ouverture
        return TILE_SIZE * self.thickness * (1.0 - self.progress)

    def get_world_position(self):
        # Base position at center of tile
        base_x = self.grid_x * TILE_SIZE + TILE_SIZE / 2
        base_y = self.grid_y * TILE_SIZE + TILE_SIZE / 2

        # AMÉLIORATION: Position de glissement plus progressive
        slide_distance = self.progress * (TILE_SIZE * 0.5)  # Glisse sur la moitié de la tile

        if self.axis == "x":
            # Door slides horizontally (into the wall)
            return (base_x - slide_distance, base_y)
        else:
            # Door slides vertically (into ceiling/floor)
            return (base_x, base_y - slide_distance)

    def get_door_bounds(self):
        x, y = self.get_world_position()

        # AMÉLIORATION: Calcul plus précis des bounds pour le glissement
        # La partie visible de la porte rétrécit progressivement
        visible_ratio = 1.0 - self.progress

        if self.axis == "x":
            # Horizontal sliding door
            door_width = TILE_SIZE * visible_ratio
            return {
                "min_x": x - door_width / 2,
                "max_x": x + door_width / 2,
                "min_y": y - TILE_SIZE / 2,
                "max_y": y + TILE_SIZE / 2
            }
        else:
            # Vertical sliding door
            door_height = TILE_SIZE * visible_ratio
            return {
                "min_x": x - TILE_SIZE / 2,
                "max_x": x + TILE_SIZE / 2,
                "min_y": y - door_height / 2,
                "max_y": y + door_height / 2
            }

    def is_open(self):
        return self.state == "open"

    def get_texture_coordinates(self):
        # AMÉLIORATION: Offset de texture plus fluide
        offset = self.progress * TILE_SIZE * 0.8  # 80% pour un meilleur effet visuel

        if self.axis == "x":
            return offset, 0
        else:
            return 0, offset

    def _check_collision(self):
        # Vérifier collision avec les murs/obstacles
        x, y = int(self.x), int(self.y)

        # Utiliser la méthode is_blocked du niveau
        if self.game.level.is_blocked(x, y):
            return True

        # Vérifier collision avec les portes
        for door in self.game.level.doors:
            if hasattr(door, 'is_blocking') and callable(getattr(door, 'is_blocking')):
                if door.is_blocking(self.x, self.y):
                    return True

        return False