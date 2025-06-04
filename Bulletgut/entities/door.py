from data.config import TILE_SIZE


class Door:
    def __init__(self, x, y, auto_close_time=3.0, thickness=0.15):
        self.grid_x = x
        self.grid_y = y
        self.state = "closed"  # 'closed', 'opening', 'open', 'closing'
        self.timer = 0
        self.auto_close_time = auto_close_time
        self.progress = 0  # 0 = fully closed, 1 = fully open
        self.speed = 0.5  # seconds to fully open/close

        # Properties for sliding door
        self.thickness = thickness
        self.axis = "x"  # Will be set in level.py

        # NOUVEAU: Offset pour le rendu de texture coulissante
        self.texture_offset = 0
        self.open_distance = 0  # Distance d'ouverture (comme dans DUGA)

        # NOUVEAU: Bounds précis pour la collision
        self.collision_bounds = None
        self.update_bounds()

    def update(self, dt):
        old_progress = self.progress

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

        # NOUVEAU: Mettre à jour les bounds seulement si le progrès a changé
        if old_progress != self.progress:
            self.update_bounds()
            self.update_texture_offset()

    def update_bounds(self):
        """Met à jour les bounds de collision de la porte"""
        base_x = self.grid_x * TILE_SIZE
        base_y = self.grid_y * TILE_SIZE

        # Inspiré de DUGA: calcul précis des bounds selon l'axe
        if self.axis == "x":
            # Porte horizontale - glisse vers la gauche/droite
            slide_distance = self.progress * (TILE_SIZE * 0.5)
            self.collision_bounds = {
                "min_x": base_x + slide_distance,
                "max_x": base_x + TILE_SIZE - slide_distance,
                "min_y": base_y,
                "max_y": base_y + TILE_SIZE
            }
        else:
            # Porte verticale - glisse vers le haut/bas
            slide_distance = self.progress * (TILE_SIZE * 0.5)
            self.collision_bounds = {
                "min_x": base_x,
                "max_x": base_x + TILE_SIZE,
                "min_y": base_y + slide_distance,
                "max_y": base_y + TILE_SIZE - slide_distance
            }

    def update_texture_offset(self):
        """Met à jour l'offset de texture pour l'effet de glissement"""
        # Inspiré de DUGA: offset basé sur le progrès
        self.texture_offset = int(self.progress * TILE_SIZE * 0.8)
        self.open_distance = int(self.progress * (TILE_SIZE // 2))

    def is_blocking(self):
        """Vérifie si la porte bloque le mouvement"""
        # Plus strict que l'original pour éviter les glitches
        return self.progress < 0.98

    def is_visible(self):
        """Vérifie si la porte doit être rendue"""
        # La porte reste visible tant qu'elle n'est pas complètement ouverte
        return self.progress < 1.0

    def get_door_bounds(self):
        """Retourne les bounds actuels de la porte"""
        return self.collision_bounds

    def get_texture_offset(self):
        """Retourne l'offset de texture pour le rendu"""
        return self.texture_offset